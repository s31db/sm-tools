from datetime import timedelta, date
from typing import Generator, List

from holidays import country_holidays
from datetime import datetime


def all_holiday(d: str, countries: List[str] = ("FR",)) -> bool:
    for country in countries:
        if d not in country_holidays(country):
            return False
    return True


def sprint_dates(
    start_date: str,
    weeks: int = 1,
    frm: str = "%Y-%m-%d",
    now: bool = False,
    limit: str | None = None,
    end_date: str | None = None,
    countries: List[str] = ("FR",),
) -> Generator[str, None, None]:
    d = date.fromisoformat(start_date)
    for i in range((7 * weeks) + 1):
        if d.weekday() < 5 and not all_holiday(d, countries=countries):
            yield d.strftime(frm)
        d += timedelta(days=1)
    limit_date = date.fromisoformat(limit) if limit else None
    if now:
        n = datetime.now().date()
        yield from add_dates(d, frm, limit_date, end_date=n)
    if end_date:
        yield from add_dates(d, frm, limit_date, end_date=date.fromisoformat(end_date))


def previous_sprint_date(
    start_date: str,
    frm: str = "%Y-%m-%d",
    countries: List[str] = ("FR",),
) -> str:
    open_date = date.fromisoformat(start_date) - timedelta(days=1)
    while open_date.weekday() >= 5 or all_holiday(open_date, countries=countries):
        open_date -= timedelta(days=1)
    return open_date.strftime(frm)


def tomorrow_sprint_date(
    start_date: str,
    frm: str = "%Y-%m-%d",
    countries: List[str] = ("FR",),
) -> str:
    open_date = date.fromisoformat(start_date) + timedelta(days=1)
    while open_date.weekday() >= 5 or all_holiday(open_date, countries=countries):
        open_date += timedelta(days=1)
    return open_date.strftime(frm)


def add_dates(
    d,
    frm: str,
    limit_date: date | None,
    end_date: date,
    countries: List[str] = ("FR",),
) -> Generator[str, None, None]:
    while d <= end_date:
        if limit_date is None or d <= limit_date:
            if d.weekday() < 5 and not all_holiday(d, countries=countries):
                yield d.strftime(frm)
        d += timedelta(days=1)


def test_sprint_dates():
    assert [*sprint_dates("2022-11-04", 3)] == [
        "2022-11-04",
        "2022-11-07",
        "2022-11-08",
        "2022-11-09",
        "2022-11-10",
        "2022-11-14",
        "2022-11-15",
        "2022-11-16",
        "2022-11-17",
        "2022-11-18",
        "2022-11-21",
        "2022-11-22",
        "2022-11-23",
        "2022-11-24",
        "2022-11-25",
    ]


def test_sprint_dates_futur():
    assert [*sprint_dates("5022-11-04", 3)] == [
        "5022-11-04",
        "5022-11-05",
        "5022-11-06",
        "5022-11-07",
        "5022-11-08",
        "5022-11-12",
        "5022-11-13",
        "5022-11-14",
        "5022-11-15",
        "5022-11-18",
        "5022-11-19",
        "5022-11-20",
        "5022-11-21",
        "5022-11-22",
        "5022-11-25",
    ]


def test_sprint_dates_futur_added():
    assert [*sprint_dates("5022-11-04", 3, end_date="5022-11-30")] == [
        "5022-11-04",
        "5022-11-05",
        "5022-11-06",
        "5022-11-07",
        "5022-11-08",
        "5022-11-12",
        "5022-11-13",
        "5022-11-14",
        "5022-11-15",
        "5022-11-18",
        "5022-11-19",
        "5022-11-20",
        "5022-11-21",
        "5022-11-22",
        "5022-11-25",
        "5022-11-26",
        "5022-11-27",
        "5022-11-28",
        "5022-11-29",
    ]
