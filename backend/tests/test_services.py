"""비즈니스 로직 단위 테스트."""
import pytest
from datetime import date
from app.services.holiday_service import (
    get_korean_holidays,
    is_holiday,
    is_business_day,
    next_business_day,
    prev_business_day,
    add_business_days,
    last_business_day_of_month,
)
from app.services.template_engine import (
    generate_reminders_from_template,
    SYSTEM_TEMPLATES,
)
from app.utils.security import hash_password, verify_password


class TestHolidayService:
    """공휴일 서비스 테스트."""

    def test_new_year_is_holiday(self):
        holidays = get_korean_holidays(2026)
        assert date(2026, 1, 1) in holidays

    def test_christmas_is_holiday(self):
        holidays = get_korean_holidays(2026)
        assert date(2026, 12, 25) in holidays

    def test_independence_day_is_holiday(self):
        holidays = get_korean_holidays(2026)
        assert date(2026, 3, 1) in holidays  # 삼일절

    def test_memorial_day_is_holiday(self):
        holidays = get_korean_holidays(2026)
        assert date(2026, 6, 6) in holidays  # 현충일

    def test_liberation_day_is_holiday(self):
        holidays = get_korean_holidays(2026)
        assert date(2026, 8, 15) in holidays  # 광복절

    def test_national_foundation_day(self):
        holidays = get_korean_holidays(2026)
        assert date(2026, 10, 3) in holidays  # 개천절

    def test_hangul_day(self):
        holidays = get_korean_holidays(2026)
        assert date(2026, 10, 9) in holidays  # 한글날

    def test_children_day(self):
        holidays = get_korean_holidays(2026)
        assert date(2026, 5, 5) in holidays  # 어린이날

    def test_weekend_is_not_business_day(self):
        # 2026-01-03 is Saturday
        assert not is_business_day(date(2026, 1, 3))
        # 2026-01-04 is Sunday
        assert not is_business_day(date(2026, 1, 4))

    def test_weekday_is_business_day(self):
        # 2026-01-05 is Monday
        assert is_business_day(date(2026, 1, 5))

    def test_holiday_is_not_business_day(self):
        # 2026-01-01 is Thursday (New Year)
        assert not is_business_day(date(2026, 1, 1))

    def test_next_business_day_from_weekend(self):
        # 2026-01-03 (Saturday) → 2026-01-05 (Monday)
        assert next_business_day(date(2026, 1, 3)) == date(2026, 1, 5)

    def test_next_business_day_from_weekday(self):
        # 2026-01-05 (Monday) → same day
        assert next_business_day(date(2026, 1, 5)) == date(2026, 1, 5)

    def test_prev_business_day_from_weekend(self):
        # 2026-01-03 (Saturday) → 2026-01-02 (Friday)
        assert prev_business_day(date(2026, 1, 3)) == date(2026, 1, 2)

    def test_add_business_days(self):
        # 2026-01-05 (Monday) + 5 business days
        result = add_business_days(date(2026, 1, 5), 5)
        assert result == date(2026, 1, 12)  # Monday

    def test_last_business_day_of_month(self):
        # January 2026: 31st is Saturday → 30th is Friday
        result = last_business_day_of_month(2026, 1)
        assert result == date(2026, 1, 30)

    def test_holidays_have_seollal(self):
        """설날 연휴가 포함되어 있는지 확인."""
        holidays = get_korean_holidays(2026)
        # 음력 1/1 기준 설날이 있어야 함
        seollal_dates = [d for d, name in holidays.items() if "설날" in name]
        assert len(seollal_dates) >= 3  # 전날, 당일, 다음날

    def test_holidays_have_chuseok(self):
        """추석 연휴가 포함되어 있는지 확인."""
        holidays = get_korean_holidays(2026)
        chuseok_dates = [d for d, name in holidays.items() if "추석" in name]
        assert len(chuseok_dates) >= 3


class TestTemplateEngine:
    """템플릿 엔진 테스트."""

    def test_tax_template_generates_reminders(self):
        """법정신고일 템플릿이 올바르게 리마인더를 생성하는지 확인."""
        tax_template = SYSTEM_TEMPLATES[0]
        reminders = generate_reminders_from_template(tax_template, 2026)

        assert len(reminders) > 0
        # 원천세 12개 + 4대보험 12개 + 부가세 4개 + 법인세 1개 + 종소세 1개 + 지방소득세 2개 + 연말정산 1개
        assert len(reminders) >= 30

    def test_tax_deadlines_are_business_days(self):
        """모든 마감일이 영업일인지 확인."""
        tax_template = SYSTEM_TEMPLATES[0]
        reminders = generate_reminders_from_template(tax_template, 2026)

        for r in reminders:
            assert is_business_day(r["deadline"]), (
                f"{r['title']}: {r['deadline']} is not a business day"
            )

    def test_payroll_template(self):
        """급여 처리 템플릿 테스트."""
        payroll_template = SYSTEM_TEMPLATES[1]
        reminders = generate_reminders_from_template(payroll_template, 2026)

        # 급여 지급 12개 + 급여 확정 12개
        assert len(reminders) == 24

    def test_payroll_last_business_day(self):
        """급여 지급일이 매월 마지막 영업일인지 확인."""
        payroll_template = SYSTEM_TEMPLATES[1]
        reminders = generate_reminders_from_template(payroll_template, 2026)

        payment_reminders = [r for r in reminders if "급여 지급" in r["title"]]
        assert len(payment_reminders) == 12

        for r in payment_reminders:
            assert is_business_day(r["deadline"])

    def test_hr_template(self):
        """HR 템플릿 테스트."""
        hr_template = SYSTEM_TEMPLATES[2]
        reminders = generate_reminders_from_template(hr_template, 2026)

        assert len(reminders) > 0

    def test_reminders_sorted_by_deadline(self):
        """리마인더가 마감일 순으로 정렬되는지 확인."""
        tax_template = SYSTEM_TEMPLATES[0]
        reminders = generate_reminders_from_template(tax_template, 2026)

        for i in range(len(reminders) - 1):
            assert reminders[i]["deadline"] <= reminders[i + 1]["deadline"]

    def test_holiday_adjusted_deadline(self):
        """공휴일인 마감일이 자동 조정되는지 확인."""
        # 2026-01-01 (신정, 목요일) - 원천세 마감일은 1월 10일
        tax_template = SYSTEM_TEMPLATES[0]
        reminders = generate_reminders_from_template(tax_template, 2026)

        for r in reminders:
            if r.get("original_deadline") is not None:
                # 원래 마감일이 공휴일/주말이었다면 조정된 것
                assert r["deadline"] != r["original_deadline"]
                assert is_business_day(r["deadline"])


class TestSecurity:
    """보안 유틸리티 테스트."""

    def test_password_hashing(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert not verify_password("wrong_password", hashed)
