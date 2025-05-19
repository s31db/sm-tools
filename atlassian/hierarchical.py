from jira import Issue
import logging

SUPER = "super"
SUPER_NAME = "super.name"
SUPER_STATUS = "super.status"
SUPER_TYPE = "super.type"
SUPER_SUPER = "super.super"
SUPER_SUPER_NAME = "super.super.name"
SUPER_SUPER_STATUS = "super.super.status"


def add_super(
    date: str,
    ticket_super_super: str | None,
    epics_date: dict,
    epics_no_rights: dict,
    ticket_super: str | None,
    ticket: Issue,
    us_date: dict,
    _super: dict,
    epic_fields: dict,
):
    # if 'type' in _super['super'] and _super['super']['type'] == 'Epic' and
    # ticket_super_super is not None and ticket_super_super not in epics_date[date]:
    if (
        ticket_super_super is not None
        and ("type" not in _super["super"] or _super["super"]["type"] == "Epic")
        and ticket_super_super not in epics_date[date]
    ):
        epics_no_rights[ticket_super_super] = ticket.key
    if SUPER in _super:
        if ticket_super_super is None or (
            ("type" not in _super["super"] or _super["super"]["type"] == "Epic")
            and ticket_super_super not in epics_date[date]
        ):
            super_super_id = "-2"
            us_date[date][ticket.key][SUPER_SUPER_STATUS] = ""
            us_date[date][ticket.key][SUPER_SUPER_NAME] = _super[SUPER]["default_name"]
        elif "type" in _super["super"] and _super["super"]["type"] == "Sprint":
            super_super_id = (
                ticket_super_super[-1].split("[id=")[-1].split(",rapidViewId=")[0]
            )
            # if 'type' in _super['super'] and _super['super']['type'] == 'Sprint':
            # us_date[date][ticket.key][SUPER_SUPER_NAME] = us_date[date][ticket.key]['sprints'][-1]
            us_date[date][ticket.key][SUPER_SUPER_STATUS] = (
                ticket_super_super[-1].split(",state=")[-1].split(",name=")[0]
            )
            us_date[date][ticket.key][SUPER_SUPER_NAME] = (
                ticket_super_super[-1].split(",name=")[-1].split(",startDate=")[0]
            )
        elif (
            "type" in _super["super"]
            and _super["super"]["type"] == "Epic"
            and epic_fields
        ):
            super_super_id = ticket_super_super
            for epic_field in epic_fields.keys():
                us_date[date][ticket.key]["super.super." + epic_field] = epics_date[
                    date
                ][ticket_super_super][epic_field]
        else:
            super_super_id = ticket_super_super
            # if 'type' in _super['super'] and _super['super']['type'] == 'Epic':
            us_date[date][ticket.key][SUPER_SUPER_STATUS] = epics_date[date][
                ticket_super_super
            ]["status"]
            us_date[date][ticket.key][SUPER_SUPER_NAME] = epics_date[date][
                ticket_super_super
            ]["name"]

        us_date[date][ticket.key][SUPER_SUPER] = super_super_id
    if ticket_super is None or (
        "type" in _super and _super["type"] == "Sprint" and not ticket_super
    ):
        if SUPER in _super:
            us_date[date][ticket.key][SUPER] = "-1" + "_" + super_super_id
        else:
            us_date[date][ticket.key][SUPER] = "-1"
        us_date[date][ticket.key][SUPER_NAME] = _super["default_name"]
        us_date[date][ticket.key][SUPER_STATUS] = ""
        us_date[date][ticket.key][SUPER_TYPE] = ""
    else:
        if "type" in _super and _super["type"] == "Sprint":
            try:
                us_date[date][ticket.key][SUPER] = (
                    ticket_super[-1].split("[id=")[-1].split(",rapidViewId=")[0]
                    + "_"
                    + super_super_id
                )
                us_date[date][ticket.key][SUPER_NAME] = (
                    ticket_super[-1].split(",name=")[-1].split(",startDate=")[0]
                )
                us_date[date][ticket.key][SUPER_STATUS] = (
                    ticket_super[-1].split(",state=")[-1].split(",name=")[0]
                )
                us_date[date][ticket.key][SUPER_TYPE] = "Sprint"
            except IndexError as ie:
                logging.error(ie)
        else:
            us_date[date][ticket.key][SUPER] = ticket_super
            if ticket_super in epics_date[date]:
                us_date[date][ticket.key][SUPER_STATUS] = epics_date[date][
                    ticket_super
                ]["status"]
                us_date[date][ticket.key][SUPER_NAME] = epics_date[date][ticket_super][
                    "name"
                ]
                us_date[date][ticket.key][SUPER_TYPE] = epics_date[date][ticket_super][
                    "type"
                ]
        if (
            "super" in _super
            and "type" in _super["super"]
            and _super["super"]["type"] == "Sprint"
        ):
            us_date[date][ticket.key][SUPER] = f"{ticket_super}_{super_super_id}"


def change_super(
    changelog_date,
    changelog_item,
    created,
    dates,
    epics_date: dict,
    ticket,
    us_date,
    _super,
):
    if changelog_item.field == _super["field_changelog"]:
        changelog_item_from = getattr(changelog_item, "from")
        if changelog_item_from is not None:
            name = changelog_item.fromString
            if ", " in changelog_item_from:
                changelog_item_from = changelog_item_from.split(", ")[-1]
                # XXX not perfect for name
                name = name.split(", ")[-1]
        field = SUPER
        for date in dates:
            if (
                created
                <= date
                < changelog_date
                <= us_date[date][ticket.key]["update"][SUPER]
            ):
                if SUPER_SUPER in us_date[date][ticket.key]:
                    super_super_id = us_date[date][ticket.key][SUPER_SUPER]
                else:
                    super_super_id = ""
                if changelog_item_from is None:
                    us_date[date][ticket.key][SUPER] = "-1" + "_" + super_super_id
                    us_date[date][ticket.key][SUPER_NAME] = "Backlog"
                    us_date[date][ticket.key][SUPER_STATUS] = ""
                else:
                    us_date[date][ticket.key][SUPER] = (
                        changelog_item_from + "_" + super_super_id
                    )
                    us_date[date][ticket.key][SUPER_NAME] = name
                    # TODO improve name and status with list sprints by date.
                    us_date[date][ticket.key][SUPER_STATUS] = ""
                us_date[date][ticket.key]["update"][field] = changelog_date
    elif changelog_item.field == _super[SUPER]["field_changelog"]:
        super_super_id = getattr(changelog_item, "from")
        field = SUPER_SUPER
        for date in dates:
            if (
                created
                <= date
                < changelog_date
                <= us_date[date][ticket.key]["update"][SUPER_SUPER]
            ):
                if super_super_id is None or super_super_id not in epics_date[date]:
                    us_date[date][ticket.key][SUPER_SUPER] = "-2"
                    us_date[date][ticket.key][SUPER] = (
                        us_date[date][ticket.key][SUPER].split("_")[0] + "_-2"
                    )
                    us_date[date][ticket.key][SUPER_SUPER_STATUS] = ""
                    us_date[date][ticket.key][SUPER_SUPER_STATUS] = "No Epic"
                else:
                    us_date[date][ticket.key][SUPER_SUPER] = super_super_id
                    us_date[date][ticket.key][SUPER] = (
                        us_date[date][ticket.key][SUPER].split("_")[0]
                        + "_"
                        + super_super_id
                    )
                    us_date[date][ticket.key][SUPER_SUPER_STATUS] = epics_date[date][
                        super_super_id
                    ]["status"]
                    us_date[date][ticket.key][SUPER_SUPER_STATUS] = epics_date[date][
                        super_super_id
                    ]["name"]
                us_date[date][ticket.key]["update"][field] = changelog_date
