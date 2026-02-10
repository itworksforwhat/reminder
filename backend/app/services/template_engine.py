"""법정신고일 및 기타 일정 템플릿 자동 생성 엔진.

템플릿을 기반으로 연간 리마인더 일정을 자동으로 생성합니다.
공휴일/대체공휴일/주말에 해당하는 마감일은 자동으로 다음 영업일로 조정됩니다.
"""
from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.template import Template, TemplateItem
from app.models.reminder import Reminder
from app.models.company import CompanyMember
from app.services.holiday_service import (
    next_business_day, last_business_day_of_month, add_business_days,
)


# 시스템 기본 템플릿 정의
SYSTEM_TEMPLATES = [
    {
        "name": "법정신고일",
        "description": "원천세, 4대보험, 부가세, 법인세 등 법정 신고 일정",
        "category": "tax",
        "items": [
            # 매월 원천세 신고 (매월 10일)
            *[
                {
                    "title": f"{m}월분 원천세 신고·납부",
                    "month": m + 1 if m < 12 else 1,
                    "day": 10,
                    "recurrence": "once",
                    "adjust_for_holiday": True,
                    "priority": 2,
                    "category": "원천세",
                    "description": f"{m}월분 원천징수세액 신고·납부 기한",
                }
                for m in range(1, 13)
            ],
            # 매월 4대보험 신고 (매월 15일)
            *[
                {
                    "title": f"{m}월분 4대보험 신고",
                    "month": m + 1 if m < 12 else 1,
                    "day": 15,
                    "recurrence": "once",
                    "adjust_for_holiday": True,
                    "priority": 2,
                    "category": "4대보험",
                    "description": f"{m}월분 국민연금·건강보험·고용보험·산재보험 신고 기한",
                }
                for m in range(1, 13)
            ],
            # 부가세 확정신고 (1월 25일, 7월 25일)
            {
                "title": "2기 부가가치세 확정신고·납부",
                "month": 1,
                "day": 25,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 3,
                "category": "부가세",
                "description": "전년도 하반기 부가가치세 확정신고·납부 기한",
            },
            {
                "title": "1기 부가가치세 확정신고·납부",
                "month": 7,
                "day": 25,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 3,
                "category": "부가세",
                "description": "상반기 부가가치세 확정신고·납부 기한",
            },
            # 부가세 예정신고 (4월 25일, 10월 25일)
            {
                "title": "1기 부가가치세 예정신고·납부",
                "month": 4,
                "day": 25,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 2,
                "category": "부가세",
                "description": "1분기 부가가치세 예정신고·납부 기한",
            },
            {
                "title": "2기 부가가치세 예정신고·납부",
                "month": 10,
                "day": 25,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 2,
                "category": "부가세",
                "description": "3분기 부가가치세 예정신고·납부 기한",
            },
            # 법인세 (3월 31일)
            {
                "title": "법인세 확정신고·납부",
                "month": 3,
                "day": 31,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 3,
                "category": "법인세",
                "description": "12월 결산법인 법인세 확정신고·납부 기한",
            },
            # 종합소득세 (5월 31일)
            {
                "title": "종합소득세 확정신고·납부",
                "month": 5,
                "day": 31,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 3,
                "category": "종합소득세",
                "description": "종합소득세 확정신고·납부 기한",
            },
            # 지방소득세 (종합소득세와 동일)
            {
                "title": "지방소득세(종합소득) 신고·납부",
                "month": 5,
                "day": 31,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 2,
                "category": "지방소득세",
                "description": "개인 지방소득세 확정신고·납부 기한",
            },
            # 지방소득세 (법인세와 동일 - 4월)
            {
                "title": "지방소득세(법인) 신고·납부",
                "month": 4,
                "day": 30,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 2,
                "category": "지방소득세",
                "description": "법인 지방소득세 확정신고·납부 기한",
            },
            # 연말정산 (3월 10일)
            {
                "title": "연말정산 환급신청",
                "month": 3,
                "day": 10,
                "recurrence": "once",
                "adjust_for_holiday": True,
                "priority": 3,
                "category": "연말정산",
                "description": "전년도 근로소득 연말정산 환급신청 기한",
            },
        ],
    },
    {
        "name": "급여 처리",
        "description": "급여 지급 및 관련 업무 일정",
        "category": "payroll",
        "items": [
            *[
                {
                    "title": f"{m}월 급여 지급",
                    "month": m,
                    "day": -1,  # -1은 마지막 영업일을 의미
                    "recurrence": "once",
                    "adjust_for_holiday": True,
                    "priority": 3,
                    "category": "급여",
                    "description": f"{m}월분 급여 지급일",
                    "extra_config": {"type": "last_business_day"},
                }
                for m in range(1, 13)
            ],
            *[
                {
                    "title": f"{m}월 급여 확정",
                    "month": m,
                    "day": -1,
                    "recurrence": "once",
                    "adjust_for_holiday": True,
                    "priority": 2,
                    "category": "급여",
                    "description": f"{m}월분 급여 확정 (지급 3영업일 전)",
                    "extra_config": {"type": "before_last_business_day", "offset": -3},
                }
                for m in range(1, 13)
            ],
        ],
    },
    {
        "name": "HR 업무",
        "description": "인사/노무 관련 정기 업무 일정",
        "category": "hr",
        "items": [
            {
                "title": "4대보험 취득/상실 신고",
                "month": None,
                "day": 15,
                "recurrence": "monthly",
                "adjust_for_holiday": True,
                "priority": 2,
                "category": "HR",
                "description": "매월 입퇴사자 4대보험 취득/상실 신고 기한",
            },
            {
                "title": "연차 사용 현황 점검",
                "month": None,
                "day": 1,
                "recurrence": "quarterly",
                "adjust_for_holiday": False,
                "priority": 1,
                "category": "HR",
                "description": "분기별 연차 사용 현황 점검",
                "extra_config": {"quarters": [1, 4, 7, 10]},
            },
            {
                "title": "근로계약서 갱신 점검",
                "month": 12,
                "day": 15,
                "recurrence": "once",
                "adjust_for_holiday": False,
                "priority": 2,
                "category": "HR",
                "description": "연간 근로계약 갱신 대상자 확인",
            },
        ],
    },
]


def generate_reminders_from_template(
    template_data: dict, year: int
) -> list[dict]:
    """템플릿 데이터를 기반으로 해당 연도의 리마인더 목록을 생성합니다."""
    reminders = []

    for item in template_data["items"]:
        generated = _generate_item_reminders(item, year)
        reminders.extend(generated)

    reminders.sort(key=lambda r: r["deadline"])
    return reminders


def _generate_item_reminders(item: dict, year: int) -> list[dict]:
    """단일 템플릿 항목에서 리마인더를 생성합니다."""
    recurrence = item.get("recurrence", "once")
    extra = item.get("extra_config") or {}

    if recurrence == "monthly":
        return _generate_monthly(item, year)
    elif recurrence == "quarterly":
        return _generate_quarterly(item, year, extra)
    else:
        return _generate_once(item, year, extra)


def _generate_once(item: dict, year: int, extra: dict) -> list[dict]:
    """단발성 일정을 생성합니다."""
    month = item.get("month")
    day = item.get("day")

    if month is None:
        return []

    deadline_type = extra.get("type", "fixed")

    if deadline_type == "last_business_day":
        deadline = last_business_day_of_month(year, month)
    elif deadline_type == "before_last_business_day":
        offset = extra.get("offset", 0)
        last_bd = last_business_day_of_month(year, month)
        deadline = add_business_days(last_bd, offset)
    else:
        # 일반 고정일
        try:
            deadline = date(year, month, day)
        except ValueError:
            # 2월 29일 같은 경우 해당 월의 마지막날
            if month == 2 and day > 28:
                deadline = date(year, 3, 1)
            else:
                return []

    original_deadline = deadline

    if item.get("adjust_for_holiday", True) and deadline_type == "fixed":
        deadline = next_business_day(deadline)

    return [
        {
            "title": item["title"],
            "description": item.get("description"),
            "category": item["category"],
            "deadline": deadline,
            "original_deadline": original_deadline if original_deadline != deadline else None,
            "priority": item.get("priority", 0),
        }
    ]


def _generate_monthly(item: dict, year: int) -> list[dict]:
    """매월 반복 일정을 생성합니다."""
    reminders = []
    day = item.get("day", 1)

    for month in range(1, 13):
        try:
            deadline = date(year, month, day)
        except ValueError:
            continue

        original_deadline = deadline

        if item.get("adjust_for_holiday", True):
            deadline = next_business_day(deadline)

        reminders.append({
            "title": f"{month}월 {item['title']}",
            "description": item.get("description"),
            "category": item["category"],
            "deadline": deadline,
            "original_deadline": original_deadline if original_deadline != deadline else None,
            "priority": item.get("priority", 0),
        })

    return reminders


def _generate_quarterly(item: dict, year: int, extra: dict) -> list[dict]:
    """분기별 반복 일정을 생성합니다."""
    reminders = []
    quarters = extra.get("quarters", [1, 4, 7, 10])
    day = item.get("day", 1)

    for month in quarters:
        try:
            deadline = date(year, month, day)
        except ValueError:
            continue

        original_deadline = deadline

        if item.get("adjust_for_holiday", True):
            deadline = next_business_day(deadline)

        quarter_num = (month - 1) // 3 + 1
        reminders.append({
            "title": f"{quarter_num}분기 {item['title']}",
            "description": item.get("description"),
            "category": item["category"],
            "deadline": deadline,
            "original_deadline": original_deadline if original_deadline != deadline else None,
            "priority": item.get("priority", 0),
        })

    return reminders


async def seed_system_templates(db: AsyncSession) -> None:
    """시스템 기본 템플릿을 데이터베이스에 시드합니다."""
    for tmpl_data in SYSTEM_TEMPLATES:
        existing = await db.execute(
            select(Template).where(
                Template.name == tmpl_data["name"],
                Template.is_system == True,
            )
        )
        if existing.scalar_one_or_none():
            continue

        template = Template(
            name=tmpl_data["name"],
            description=tmpl_data["description"],
            category=tmpl_data["category"],
            is_system=True,
        )
        db.add(template)
        await db.flush()

        for item_data in tmpl_data["items"]:
            item = TemplateItem(
                template_id=template.id,
                title=item_data["title"],
                description=item_data.get("description"),
                month=item_data.get("month"),
                day=item_data.get("day"),
                recurrence=item_data.get("recurrence", "once"),
                adjust_for_holiday=item_data.get("adjust_for_holiday", True),
                priority=item_data.get("priority", 0),
                category=item_data["category"],
                extra_config=item_data.get("extra_config"),
            )
            db.add(item)

    await db.flush()


async def apply_template(
    db: AsyncSession,
    template_id: UUID,
    company_id: UUID,
    user_id: UUID,
    year: int,
) -> list[Reminder]:
    """DB에 저장된 템플릿을 적용하여 리마인더를 생성합니다."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # 접근 권한 확인
    member_result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.user_id == user_id,
            CompanyMember.company_id == company_id,
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this company",
        )

    # 템플릿 항목을 dict로 변환
    template_data = {
        "name": template.name,
        "items": [],
    }
    for item in template.items:
        template_data["items"].append({
            "title": item.title,
            "description": item.description,
            "month": item.month,
            "day": item.day,
            "recurrence": item.recurrence,
            "adjust_for_holiday": item.adjust_for_holiday,
            "priority": item.priority,
            "category": item.category,
            "extra_config": item.extra_config,
        })

    # 리마인더 생성
    reminder_dicts = generate_reminders_from_template(template_data, year)

    reminders = []
    for rd in reminder_dicts:
        reminder = Reminder(
            company_id=company_id,
            title=rd["title"],
            description=rd.get("description"),
            category=rd["category"],
            deadline=rd["deadline"],
            original_deadline=rd.get("original_deadline"),
            priority=rd.get("priority", 0),
            template_id=template_id,
            created_by=user_id,
        )
        db.add(reminder)
        reminders.append(reminder)

    await db.flush()
    return reminders
