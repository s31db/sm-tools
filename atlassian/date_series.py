def field_changelog(
    asof: str | None,
    changelog_date: str,
    changelog_item_from_string: str,
    created: str,
    dates: list[str],
    field: str,
    ticket_key: str,
    us_date: dict[str, dict[str, dict[str, str | dict[str, str]]]],
):
    for date in dates:
        if asof and asof > date:
            break
        else:
            if created <= date < changelog_date and (
                changelog_date < us_date[date][ticket_key]["update"][field]
                or changelog_date
                <= us_date[date][ticket_key]["update"][field]
                == dates[-1]
            ):
                us_date[date][ticket_key][field] = changelog_item_from_string
                us_date[date][ticket_key]["update"][field] = changelog_date


def test_field_changelog():
    dates = [
        "2025-03-22",
        "2025-03-23",
        "2025-03-24",
        "2025-03-25",
        "2025-03-26",
        "2025-03-27",
    ]
    us_date = {}
    for date in dates:
        us_date[date] = {
            "1": {"update": {"status": dates[-1]}, "status": "status_date"}
        }
    field_changelog(
        asof=None,
        changelog_date="2025-03-25",
        changelog_item_from_string="val_2025-03-25_bis",
        created="2024-05-11",
        dates=dates,
        field="status",
        ticket_key="1",
        us_date=us_date,
    )
    assert us_date == {
        "2025-03-22": {
            "1": {"update": {"status": "2025-03-25"}, "status": "val_2025-03-25_bis"}
        },
        "2025-03-23": {
            "1": {"update": {"status": "2025-03-25"}, "status": "val_2025-03-25_bis"}
        },
        "2025-03-24": {
            "1": {"update": {"status": "2025-03-25"}, "status": "val_2025-03-25_bis"}
        },
        "2025-03-25": {
            "1": {"update": {"status": "2025-03-27"}, "status": "status_date"}
        },
        "2025-03-26": {
            "1": {"update": {"status": "2025-03-27"}, "status": "status_date"}
        },
        "2025-03-27": {
            "1": {"update": {"status": "2025-03-27"}, "status": "status_date"}
        },
    }
    second_change(dates, us_date)
    third_change(dates, us_date)


def second_change(dates, us_date):
    field_changelog(
        asof=None,
        changelog_date="2025-03-25",
        changelog_item_from_string="val_2025-03-25",
        created="2024-05-11",
        dates=dates,
        field="status",
        ticket_key="1",
        us_date=us_date,
    )
    assert us_date == {
        "2025-03-22": {
            "1": {"update": {"status": "2025-03-25"}, "status": "val_2025-03-25_bis"}
        },
        "2025-03-23": {
            "1": {"update": {"status": "2025-03-25"}, "status": "val_2025-03-25_bis"}
        },
        "2025-03-24": {
            "1": {"update": {"status": "2025-03-25"}, "status": "val_2025-03-25_bis"}
        },
        "2025-03-25": {
            "1": {"update": {"status": "2025-03-27"}, "status": "status_date"}
        },
        "2025-03-26": {
            "1": {"update": {"status": "2025-03-27"}, "status": "status_date"}
        },
        "2025-03-27": {
            "1": {"update": {"status": "2025-03-27"}, "status": "status_date"}
        },
    }


def third_change(dates, us_date):
    field_changelog(
        asof=None,
        changelog_date="2025-03-27",
        changelog_item_from_string="val_2025-03-27",
        created="2024-05-11",
        dates=dates,
        field="status",
        ticket_key="1",
        us_date=us_date,
    )
    assert us_date == {
        "2025-03-22": {
            "1": {
                "update": {"status": "2025-03-25"},
                "status": "val_2025-03-25_bis",
            }
        },
        "2025-03-23": {
            "1": {
                "update": {"status": "2025-03-25"},
                "status": "val_2025-03-25_bis",
            }
        },
        "2025-03-24": {
            "1": {
                "update": {"status": "2025-03-25"},
                "status": "val_2025-03-25_bis",
            }
        },
        "2025-03-25": {
            "1": {"update": {"status": "2025-03-27"}, "status": "val_2025-03-27"}
        },
        "2025-03-26": {
            "1": {"update": {"status": "2025-03-27"}, "status": "val_2025-03-27"}
        },
        "2025-03-27": {
            "1": {"update": {"status": "2025-03-27"}, "status": "status_date"}
        },
    }
