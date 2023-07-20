from datetime import timedelta, date
# https://github.com/etalab/jours-feries-france
from jours_feries_france import JoursFeries
from datetime import datetime


def sprint_dates(start_date: str, weeks: int = 1, frm: str = '%Y-%m-%d', now: bool = False, limit: str = None):
    d = date.fromisoformat(start_date)
    for i in range((7 * weeks) + 1):
        if d.weekday() < 5 and not JoursFeries.is_bank_holiday(d):
            yield d.strftime(frm)
        d += timedelta(days=1)
    if now:
        n = datetime.now().date()
        limit_date = date.fromisoformat(limit) if limit else None
        while d <= n:
            if limit is None or d <= limit_date:
                if d.weekday() < 5 and not JoursFeries.is_bank_holiday(d):
                    yield d.strftime(frm)
                d += timedelta(days=1)


def test_sprint_dates():
    assert [*sprint_dates('2022-11-04', 3)] == ['2022-11-04', '2022-11-07', '2022-11-08', '2022-11-09', '2022-11-10',
                                                '2022-11-14', '2022-11-15', '2022-11-16', '2022-11-17',
                                                '2022-11-18', '2022-11-21', '2022-11-22', '2022-11-23', '2022-11-24',
                                                '2022-11-25']

