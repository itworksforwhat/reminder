"""한국 공휴일 및 영업일 계산 서비스.

korean_lunar_calendar를 활용하여 음력 기반 공휴일과 대체공휴일을 계산합니다.
"""
from datetime import date, timedelta
from functools import lru_cache
from korean_lunar_calendar import KoreanLunarCalendar


def _lunar_to_solar(year: int, month: int, day: int) -> date:
    """음력 날짜를 양력으로 변환합니다."""
    cal = KoreanLunarCalendar()
    cal.setLunarDate(year, month, day, False)
    return date(cal.solarYear, cal.solarMonth, cal.solarDay)


@lru_cache(maxsize=32)
def get_korean_holidays(year: int) -> dict[date, str]:
    """해당 연도의 한국 공휴일 목록을 반환합니다."""
    holidays: dict[date, str] = {}

    # 양력 공휴일
    fixed_holidays = [
        (1, 1, "신정"),
        (3, 1, "삼일절"),
        (5, 5, "어린이날"),
        (6, 6, "현충일"),
        (8, 15, "광복절"),
        (10, 3, "개천절"),
        (10, 9, "한글날"),
        (12, 25, "크리스마스"),
    ]

    for month, day, name in fixed_holidays:
        holidays[date(year, month, day)] = name

    # 음력 공휴일
    try:
        # 설날 (음력 1/1) 전날, 당일, 다음날
        seollal = _lunar_to_solar(year, 1, 1)
        holidays[seollal - timedelta(days=1)] = "설날 연휴"
        holidays[seollal] = "설날"
        holidays[seollal + timedelta(days=1)] = "설날 연휴"

        # 부처님오신날 (음력 4/8)
        buddha = _lunar_to_solar(year, 4, 8)
        holidays[buddha] = "부처님오신날"

        # 추석 (음력 8/15) 전날, 당일, 다음날
        chuseok = _lunar_to_solar(year, 8, 15)
        holidays[chuseok - timedelta(days=1)] = "추석 연휴"
        holidays[chuseok] = "추석"
        holidays[chuseok + timedelta(days=1)] = "추석 연휴"
    except Exception:
        pass

    # 대체공휴일 적용
    substitute_holidays = _calculate_substitute_holidays(year, holidays)
    holidays.update(substitute_holidays)

    return holidays


def _calculate_substitute_holidays(year: int, holidays: dict[date, str]) -> dict[date, str]:
    """대체공휴일을 계산합니다.

    - 설날/추석 연휴가 일요일과 겹치면 대체공휴일
    - 어린이날이 토/일/공휴일과 겹치면 대체공휴일
    - 삼일절, 광복절, 개천절, 한글날이 토/일과 겹치면 대체공휴일 (2021년~)
    """
    substitutes: dict[date, str] = {}

    # 설날 대체공휴일
    try:
        seollal = _lunar_to_solar(year, 1, 1)
        seollal_range = [seollal + timedelta(days=i) for i in range(-1, 2)]
        for d in seollal_range:
            if d.weekday() == 6:  # 일요일
                next_day = seollal_range[-1] + timedelta(days=1)
                while next_day in holidays or next_day in substitutes or next_day.weekday() >= 5:
                    next_day += timedelta(days=1)
                substitutes[next_day] = "대체공휴일 (설날)"
    except Exception:
        pass

    # 추석 대체공휴일
    try:
        chuseok = _lunar_to_solar(year, 8, 15)
        chuseok_range = [chuseok + timedelta(days=i) for i in range(-1, 2)]
        for d in chuseok_range:
            if d.weekday() == 6:  # 일요일
                next_day = chuseok_range[-1] + timedelta(days=1)
                while next_day in holidays or next_day in substitutes or next_day.weekday() >= 5:
                    next_day += timedelta(days=1)
                substitutes[next_day] = "대체공휴일 (추석)"
    except Exception:
        pass

    # 어린이날 대체공휴일
    children_day = date(year, 5, 5)
    if children_day.weekday() >= 5 or children_day in holidays:
        next_day = children_day + timedelta(days=1)
        while next_day in holidays or next_day in substitutes or next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        if next_day != children_day:
            substitutes[next_day] = "대체공휴일 (어린이날)"

    # 2021년부터 적용되는 대체공휴일 확대
    if year >= 2021:
        expanded = [
            (3, 1, "삼일절"),
            (8, 15, "광복절"),
            (10, 3, "개천절"),
            (10, 9, "한글날"),
        ]
        for month, day, name in expanded:
            d = date(year, month, day)
            if d.weekday() == 5:  # 토요일 → 월요일
                sub = d + timedelta(days=2)
                while sub in holidays or sub in substitutes:
                    sub += timedelta(days=1)
                substitutes[sub] = f"대체공휴일 ({name})"
            elif d.weekday() == 6:  # 일요일 → 월요일
                sub = d + timedelta(days=1)
                while sub in holidays or sub in substitutes:
                    sub += timedelta(days=1)
                substitutes[sub] = f"대체공휴일 ({name})"

    return substitutes


def is_holiday(d: date) -> bool:
    """해당 날짜가 공휴일인지 확인합니다."""
    holidays = get_korean_holidays(d.year)
    return d in holidays


def is_business_day(d: date) -> bool:
    """해당 날짜가 영업일(평일이면서 공휴일이 아닌 날)인지 확인합니다."""
    if d.weekday() >= 5:  # 토, 일
        return False
    return not is_holiday(d)


def next_business_day(d: date) -> date:
    """주어진 날짜가 영업일이 아니면 다음 영업일을 반환합니다."""
    while not is_business_day(d):
        d += timedelta(days=1)
    return d


def prev_business_day(d: date) -> date:
    """주어진 날짜가 영업일이 아니면 이전 영업일을 반환합니다."""
    while not is_business_day(d):
        d -= timedelta(days=1)
    return d


def add_business_days(d: date, days: int) -> date:
    """영업일 기준으로 일수를 더합니다."""
    direction = 1 if days >= 0 else -1
    remaining = abs(days)

    while remaining > 0:
        d += timedelta(days=direction)
        if is_business_day(d):
            remaining -= 1

    return d


def last_business_day_of_month(year: int, month: int) -> date:
    """해당 월의 마지막 영업일을 반환합니다."""
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    return prev_business_day(last_day)
