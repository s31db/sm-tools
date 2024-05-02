from jira import JIRA, Issue
import logging
import statistics
from decimal import Decimal
import math
import json
from datetime import datetime
from operator import attrgetter
from jira.client import ResultList

Y_M_D = "%Y-%m-%d"
SUPER = "super"
SUPER_NAME = "super.name"
SUPER_STATUS = "super.status"
SUPER_SUPER = "super.super"
SUPER_SUPER_NAME = "super.super.name"
SUPER_SUPER_STATUS = "super.super.status"


def to_hour(second: int, minus: int | None = None):
    if second and minus:
        return second - minus / 3600
    elif second:
        return second / 3600
    elif minus:
        return minus / -3600


def add_super(
    date: str,
    ticket_super_super: str | None,
    epics_date: dict,
    epics_no_rights: dict,
    ticket_super: str | None,
    ticket: Issue,
    us_date: dict,
    _super: dict,
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
    if ticket_super is None:
        if SUPER in _super:
            us_date[date][ticket.key][SUPER] = "-1" + "_" + super_super_id
        else:
            us_date[date][ticket.key][SUPER] = "-1"
        us_date[date][ticket.key][SUPER_NAME] = _super["default_name"]
        us_date[date][ticket.key][SUPER_STATUS] = ""
        us_date[date][ticket.key]["super.type"] = ""
    else:
        if "type" in _super and _super["type"] == "Sprint":
            us_date[date][ticket.key][SUPER] = (
                ticket_super[-1].split("[id=")[-1].split(",rapidViewId=")[0]
                + "_"
                + super_super_id
            )
            us_date[date][ticket.key][SUPER_NAME] = (
                ticket_super[-1].split(",name=")[-1].split(",startDate=")[0]
            )
            us_date[date][ticket.key][SUPER_STATUS] = ""
            us_date[date][ticket.key]["super.type"] = "Sprint"
        else:
            us_date[date][ticket.key][SUPER] = ticket_super
            if ticket_super in epics_date[date]:
                us_date[date][ticket.key][SUPER_STATUS] = epics_date[date][
                    ticket_super
                ]["status"]
                us_date[date][ticket.key][SUPER_NAME] = epics_date[date][ticket_super][
                    "name"
                ]
                us_date[date][ticket.key]["super.type"] = epics_date[date][
                    ticket_super
                ]["type"]
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


class JiraSM:
    _jira: JIRA
    _project: str
    _url_server: str
    _fields_change_ignored: list[str]
    _type_base: list[str]
    _path_data: str
    _epic_fields: dict
    _fields: dict
    _super: dict
    _board_id: int
    _trc: bool = False
    _user: str
    _token_auth: str
    _verify_ssl: bool = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, "_" + key, value)

    def conn(self):
        if "atlassian.net" in self._url_server:
            self._jira = JIRA(
                server=self._url_server, basic_auth=(self._user, self._token_auth)
            )
        else:
            self._jira = JIRA(
                server=self._url_server,
                options={"verify": self._verify_ssl},
                token_auth=self._token_auth,
            )
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._jira is not None:
            self._jira.close()

    def search(
        self,
        jql_str: str,
        max_results: int = 10000,
        fields: str | list[str] | None = None,
        expand: str | None = None,
        trc: bool = False,
    ) -> ResultList[Issue]:
        if trc or self._trc:
            print(jql_str)
            from urllib.parse import quote_plus

            print(self._url_server + "/issues/?jql=" + quote_plus(jql_str))
        return ResultList[Issue](
            self._jira.search_issues(
                jql_str=jql_str, maxResults=max_results, fields=fields, expand=expand
            )
        )
        # results = self._jira.search_issues(jql_str=jql_str, maxResults=maxResults, fields=fields, expand=expand)
        # for result in results:
        #     yield result
        # Limit by Server Jira the maxResults
        # start_at = results.maxResults
        # while results.total > start_at:
        #     for result in self._jira.search_issues(jql_str=jql_str, maxResults=results.maxResults,
        #                                            fields=fields, expand=expand,  startAt=start_at):
        #         yield result
        #     start_at += results.maxResults

    def analyse(self):
        # issue = jira.issue('XX-Number')
        # print(issue.fields.project.key)
        # print(issue.fields.issuetype.name)
        # print(issue.fields.reporter.displayName)

        # jql_str = self._filter_project() + 'AND sprint = "XXX" AND issuetype =  Sub-task ORDER BY Rank ASC'
        jql_str = (
            self._filter_project()
            + 'AND sprint = "XXX" AND issuetype =  Story ORDER BY Rank ASC'
        )
        sousestimer = 0
        sousestimerl = []
        parfait = 0
        surestimer = 0
        autre = 0
        for task in self.search(jql_str=jql_str, max_results=10000):
            if (
                task.fields.aggregatetimespent
                and task.fields.aggregatetimeoriginalestimate
                and task.fields.aggregatetimespent
                > task.fields.aggregatetimeoriginalestimate
            ):
                print(task.self, self.link_browse(task.key))
                print(
                    task.fields.summary,
                    task.fields.status,
                    task.fields.assignee,
                    to_hour(task.fields.aggregatetimespent),
                    "/",
                    to_hour(task.fields.aggregatetimeoriginalestimate),
                )
                sousestimer += 1
                sousestimerl.append(
                    to_hour(
                        task.fields.aggregatetimespent
                        - task.fields.aggregatetimeoriginalestimate
                    )
                )
            elif (
                task.fields.aggregatetimespent
                and task.fields.aggregatetimeoriginalestimate
                and task.fields.aggregatetimespent
                == task.fields.aggregatetimeoriginalestimate
            ):
                parfait += 1
            elif (
                task.fields.aggregatetimespent
                and task.fields.aggregatetimeoriginalestimate
                and task.fields.aggregatetimespent
                < task.fields.aggregatetimeoriginalestimate
            ):
                surestimer += 1
            else:
                # print(task.self, self.link_browse(task.key))
                # print(task.fields.summary, task.fields.status, task.fields.assignee,
                #       to_hour(task.fields.aggregatetimespent),
                #       '/', to_hour(task.fields.aggregatetimeoriginalestimate))
                autre += 1

        print(
            "Total",
            math.fsum(sousestimerl),
            "Median",
            statistics.median(map(Decimal, sousestimerl)),
            "Mean",
            statistics.mean(map(Decimal, sousestimerl)),
        )
        print(
            "sousestimer",
            sousestimer,
            "parfait",
            parfait,
            "surestimer",
            surestimer,
            "autre",
            autre,
        )

    def _filter_project(self):
        return "project = " + self._project + " "

    def assign(self):
        tasks = {}
        for task in self.search(
            self._filter_project() + 'AND status in ("To Do", "In Progress") '
            # 'AND issuetype in (Bug, Sub-task) '
            # 'AND assignee = currentUser() ' +
            "AND resolution = Unresolved ORDER BY updated DESC",
            fields="summary, status, assignee, aggregatetimeoriginalestimate, aggregatetimespent",
        ):
            tasks[task.key] = {
                "summary": task.fields.summary,
                "link": self.link_browse(task.key),
                "status": task.fields.status.name,
                "assignee": str(task.fields.assignee),
                "restant": to_hour(
                    task.fields.aggregatetimeoriginalestimate,
                    task.fields.aggregatetimespent,
                ),
            }
            print(task.self, self.link_browse(task.key))
            print(
                task.fields.summary,
                task.fields.status,
                task.fields.assignee,
                to_hour(task.fields.aggregatetimespent),
                "/",
                to_hour(task.fields.aggregatetimeoriginalestimate),
                to_hour(
                    task.fields.aggregatetimeoriginalestimate,
                    task.fields.aggregatetimespent,
                ),
            )
        import pprint

        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(tasks)
        # print(tasks)

    def remaining(self, cleaner: bool = False):
        fields: str = "summary, assignee, aggregatetimeestimate, status"
        orders: str = "ORDER BY assignee ASC, remainingEstimate DESC"
        filters: dict[str, str] = {
            "remaining": "and remainingEstimate > 0",
            "doneOrCancel": "and (status = DONE or status = CANCELED)",
            "subtaskdone": "and status in (Done, Closed) and issuetype in (ST-Dev, ST-Doc, ST-Tst)",
            # 'subtaskdone': 'and status in (Closed) and issuetype in (ST-Dev, ST-Doc, ST-Tst)',
            "doneOrValidate": 'and (status = DONE or status = "To Validate")',
            "canceled": "and status = CANCELED",
            "doneAndNotAssignee": "and status = Done and assignee is EMPTY",
        }
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path_file = (
            self._path_data
            + now.replace("-", "")
            + self._project
            + "_"
            + "remaining"
            + ".txt"
        )
        with open(path_file, "w", encoding="utf-8") as f:
            for task in self.search(
                jql_str=f"{self._filter_project()}{filters['subtaskdone']}{filters['remaining']} {orders}",
                max_results=False,
                fields=fields,
                trc=True,
            ):
                # print(task.key)
                if task.fields.aggregatetimeestimate is not None:
                    print(
                        task,
                        (
                            task.fields.assignee
                            if task.fields.assignee
                            else "Non assignée"
                        ),
                        task.fields.summary,
                        self.link_browse(task.key),
                        task.fields.status,
                        task.fields.aggregatetimeestimate / 3600,
                        "h",
                    )
                    f.write(
                        " ".join(
                            (
                                str(task),
                                (
                                    str(task.fields.assignee)
                                    if task.fields.assignee
                                    else "Not assigned"
                                ),
                                task.fields.summary,
                                self.link_browse(task.key),
                                str(task.fields.status),
                                str(task.fields.aggregatetimeestimate / 3600) + "h",
                            )
                        )
                        + "\n"
                    )
                if cleaner:
                    task.update(
                        update={"timetracking": [{"edit": {"remainingEstimate": "0h"}}]}
                    )
            # task.update(update={"timetracking_remainingestimate": "0h"})

    def link_browse(self, key: str):
        return self._url_server + "/browse/" + key

    def false_status(self):
        # sprint_field = self._fields['sprints']['field']
        # fields = 'summary, assignee, ' + sprint_field + ', status'
        fields = "summary, assignee, status"
        # filtre = ' AND Sprint in closedSprints() AND Sprint not in openSprints() AND ' \
        filtre = (
            "AND "
            "status not in (Closed, Cancelled, Done, Closed, Validated) ORDER BY status ASC"
        )
        for task in self.search(
            self._filter_project() + filtre, 50000, fields=fields, trc=True
        ):
            # print(task.key)
            print(
                task,
                task.fields.assignee if task.fields.assignee else "Non assignée",
                task.fields.summary,
                self.link_browse(task.key),
                # attrgetter(sprint_field)(task.fields)[-1].split(',name=')[-1].split(',startDate=')[0],
                task.fields.status,
            )

    def out_person(self):
        fields = "summary, assignee, aggregatetimeestimate, status"
        filters = {
            "remaining": "and remainingEstimate > 0",
            "doneOrCancel": "and (status = DONE or status = CANCELED)",
            "subtaskdone": "and status in (Done, Closed) and issuetype in (ST-Dev, ST-Doc, ST-Tst)",
            "doneOrValidate": 'and (status = DONE or status = "To Validate")',
            "progress": 'and status = "In Progress"',
            "canceled": "and status = CANCELED",
            "doneAndNotAssignee": "and status = Done and assignee is EMPTY",
            "out_team": 'AND assignee not in ("XXX", "YYY")',
        }
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path_file = (
            self._path_data
            + now.replace("-", "")
            + self._project
            + "_"
            + "out_team"
            + ".txt"
        )
        with open(path_file, "w", encoding="utf-8") as f:
            for task in self.search(
                "project = "
                + self._project
                + " "
                + filters["progress"]
                + " "
                + filters["out_team"]
                + " ORDER BY assignee ASC, remainingEstimate DESC",
                max_results=False,
                fields=fields,
                trc=True,
            ):
                # print(task.key)
                if task.fields.aggregatetimeestimate is not None:
                    print(
                        task,
                        (
                            task.fields.assignee
                            if task.fields.assignee
                            else "Non assignée"
                        ),
                        task.fields.summary,
                        self._url_server + "/browse/" + task.key,
                        task.fields.status,
                        task.fields.aggregatetimeestimate / 3600,
                        "h",
                    )
                    f.write(
                        " ".join(
                            (
                                str(task),
                                (
                                    str(task.fields.assignee)
                                    if task.fields.assignee
                                    else "Not assigned"
                                ),
                                task.fields.summary,
                                self._url_server + "browse/" + task.key,
                                str(task.fields.status),
                                str(task.fields.aggregatetimeestimate / 3600) + "h",
                            )
                        )
                        + "\n"
                    )

    def epic_ticket(
        self,
        dates: list,
        filtre: str = "",
        suffix: str = "",
        file: bool = True,
        asof: str | None = None,
    ) -> tuple[dict, str]:
        epics_date: dict = {}
        us_date: dict = {}
        if asof:
            now = asof
        else:
            now = datetime.now().strftime(Y_M_D)
        (
            epics_changelogs,
            epics_fields,
            tickets_changelogs,
            tickets_fields,
        ) = self._prepare_epic_ticket(dates, epics_date, now, us_date)

        self._prepare_epics(dates, epics_changelogs, epics_date, epics_fields, now)

        epics_no_rights: dict = {}
        type_tickets = (
            'AND type in ("' + '", "'.join(self._type_base) + '") '
            if self._type_base
            else ""
        )
        for ticket in self.search(
            jql_str=f"{self._filter_project()}{type_tickets}{filtre} ORDER BY key asc",
            max_results=False,
            expand="changelog",
            trc=False,
            fields=", ".join(tickets_fields),
        ):
            created = ticket.fields.created[:10]
            ticket_super: str = attrgetter(self._super["field"])(ticket.fields)
            if SUPER in self._super:
                ticket_super_super: str | None = attrgetter(
                    self._super[SUPER]["field"]
                )(ticket.fields)
            else:
                ticket_super_super = None
            # if 'type' in self._super and self._super['type'] == 'Epic':
            self._epic_tickets_by_date(
                created,
                dates,
                epics_date,
                epics_no_rights,
                now,
                ticket,
                ticket_super,
                ticket_super_super,
                us_date,
            )

            self._epic_ticket_changelog(
                created,
                dates,
                epics_date,
                ticket,
                tickets_changelogs,
                us_date,
                asof=asof,
            )

        if epics_no_rights:
            logging.warning(
                "Right to see {} ?".format(" ".join(epics_no_rights.keys()))
            )
            logging.warning("Exemple ticket from epic: {}".format(epics_no_rights))
        if asof:
            now = asof
        else:
            now = datetime.now().strftime(Y_M_D)
        path_file = (
            self._path_data
            + now.replace("-", "")
            + self._project
            + "_"
            + suffix
            + ".json"
        )
        if file:
            with open(path_file, "w", encoding="utf-8") as f:
                json.dump(us_date, f, indent=2)
        return us_date, path_file

    def _epic_tickets_by_date(
        self,
        created,
        dates,
        epics_date: dict,
        epics_no_rights: dict,
        now,
        ticket,
        ticket_super: str | None,
        ticket_super_super: str | None,
        us_date: dict,
    ):
        for date in dates:
            if created <= date <= now:
                us_date[date][ticket.key] = {"update": {SUPER: now, SUPER_SUPER: now}}
                for us_field, us_field_conf in self._fields.items():
                    try:
                        us_date[date][ticket.key][us_field] = attrgetter(
                            us_field_conf["field"]
                        )(ticket.fields)
                    except AttributeError:
                        logging.info("AttributeError :" + us_field_conf["field"])
                    us_date[date][ticket.key]["update"][us_field] = now
                add_super(
                    date,
                    ticket_super_super,
                    epics_date,
                    epics_no_rights,
                    ticket_super,
                    ticket,
                    us_date,
                    self._super,
                )

    def _epic_ticket_changelog(
        self,
        created,
        dates,
        epics_date,
        ticket,
        tickets_changelogs,
        us_date,
        asof: str | None = None,
    ):
        for changelog in ticket.changelog.histories:
            changelog_date = changelog.created[:10]
            for changelog_item in changelog.items:
                if changelog_item.field in tickets_changelogs:
                    field = (
                        "name"
                        if changelog_item.field == "summary"
                        else tickets_changelogs[changelog_item.field]
                    )
                    for date in dates:
                        if asof and asof > date:
                            break
                        else:
                            if (
                                created
                                <= date
                                < changelog_date
                                <= us_date[date][ticket.key]["update"][field]
                            ):
                                us_date[date][ticket.key][
                                    field
                                ] = changelog_item.fromString
                                us_date[date][ticket.key]["update"][
                                    field
                                ] = changelog_date
                elif changelog_item.field in (self._super["field_changelog"],):
                    change_super(
                        changelog_date,
                        changelog_item,
                        created,
                        dates,
                        epics_date,
                        ticket,
                        us_date,
                        self._super,
                    )
                elif SUPER in self._super and changelog_item.field in (
                    self._super[SUPER]["field_changelog"],
                ):
                    change_super(
                        changelog_date,
                        changelog_item,
                        created,
                        dates,
                        epics_date,
                        ticket,
                        us_date,
                        self._super,
                    )
                elif changelog_item.field not in self._fields_change_ignored:
                    logging.debug(
                        "Field not ignored {} {} {} ".format(
                            changelog_item.field,
                            changelog_item.fieldtype,
                            getattr(changelog_item, "from"),
                        )
                    )
                    # changelog_item.fromString, changelog_item.to, changelog_item.toString

    def _prepare_epics(
        self, dates, epics_changelogs, epics_date: dict, epics_fields, now
    ):
        for epic in self.search(
            jql_str=self._filter_project() + " AND type = Epic ORDER BY key asc",
            max_results=False,
            fields=", ".join(epics_fields),
            expand="changelog",
        ):
            created = epic.fields.created[:10]
            for date in dates:
                if created <= date <= now:
                    epics_date[date][epic.key] = {"update": {}}
                    for epic_field, epic_field_conf in self._epic_fields.items():
                        epics_date[date][epic.key][epic_field] = attrgetter(
                            epic_field_conf["field"]
                        )(epic.fields)
                        epics_date[date][epic.key]["update"][epic_field] = now

            for changelog in epic.changelog.histories:
                changelog_date = changelog.created[:10]
                for changelog_item in changelog.items:
                    field = changelog_item.field
                    if field in epics_changelogs:
                        for date in dates:
                            if (
                                created
                                <= date
                                < changelog_date
                                <= epics_date[date][epic.key]["update"][
                                    epics_changelogs[field]
                                ]
                            ):
                                epics_date[date][epic.key][
                                    epics_changelogs[field]
                                ] = changelog_item.fromString
                                epics_date[date][epic.key]["update"][
                                    epics_changelogs[field]
                                ] = changelog_date

    def _prepare_epic_ticket(
        self, dates: list[str], epics_date: dict, now: str, us_date: dict
    ):
        for date in dates:
            if date <= now:
                epics_date[date] = {}
                us_date[date] = {}
        epics_changelogs = {}
        epics_fields = []
        for key, value in self._epic_fields.items():
            if "field_changelog" in value:
                epics_changelogs[value["field_changelog"]] = key
            if "field" in value:
                epics_fields.append(value["field"].split(".")[0])
        tickets_changelogs = {}
        if SUPER in self._super:
            tickets_fields = [self._super["field"], self._super[SUPER]["field"]]
        else:
            tickets_fields = [self._super["field"]]
        for key, value in self._fields.items():
            if "field_changelog" in value:
                tickets_changelogs[value["field_changelog"]] = key
            if "field" in value:
                tickets_fields.append(value["field"].split(".")[0])
        return epics_changelogs, epics_fields, tickets_changelogs, tickets_fields

    def sprints(self, file: bool = True, asof: str | None = None):
        s = {}
        for sprint in self._jira.sprints(self._board_id):
            if sprint.state == "future":
                s[sprint.id] = {"name": sprint.name, "state": sprint.state}
            else:
                # s[sprint.id] = {'start_date': sprint.activatedDate[:10], 'end_date': sprint.completeDate[:10],
                s[sprint.id] = {
                    "start_date": sprint.activatedDate[:10],
                    "end_date": sprint.endDate[:10],
                    "name": sprint.name,
                    "state": sprint.state,
                }
        if asof:
            now = asof
        else:
            now = datetime.now().strftime("%Y-%m-%d")
        if file:
            path_file = (
                self._path_data
                + now.replace("-", "")
                + self._project
                + "_"
                + "infos_sprints"
                + ".json"
            )
            with open(path_file, "w", encoding="utf-8") as f:
                json.dump(s, f, indent=2)
        return s

    def sprint_actif(self) -> tuple[str, dict[str, str | None]]:
        for sprint in self._jira.sprints(self._board_id, state="active"):
            sprint_id = sprint.id
            sprint_infos = {
                "start_date": sprint.activatedDate,
                "end_date": sprint.endDate,
                "name": sprint.name,
                "state": sprint.state,
                "goal": sprint.goal,
            }
            return sprint_id, sprint_infos

    def previous_sprint(self) -> tuple[str | None, dict[str, str | None] | None]:
        closed: dict[str, dict[str, str | None]] = {}
        for sprint in self._jira.sprints(self._board_id, state="closed"):
            sprint_infos = {
                "sprint_id": sprint.id,
                "start_date": sprint.activatedDate,
                "end_date": sprint.endDate,
                "name": sprint.name,
                "state": sprint.state,
                "goal": sprint.goal,
            }
            closed[sprint.endDate] = sprint_infos
        last_closed = max(closed.keys())
        return closed[last_closed]["sprint_id"], closed[last_closed]

    def workload(self, start_date: str, date_to: str, file: bool = True):
        workloads = []
        # jql_str = f"project={self._project} and ..."
        jql_str = (
            f"worklogDate>={start_date} and worklogDate <={date_to} ORDER BY Rank ASC"
        )

        for task in self.search(
            jql_str=jql_str, max_results=False, fields="worklog, summary"
        ):
            if task.fields.worklog.total > task.fields.worklog.maxResults:
                worklogs = self._jira.worklogs(task.key)
            else:
                worklogs = task.fields.worklog.worklogs
            for work in worklogs:
                # workloads.append({'author': str(work.author).strip(), 'day': work.started[:10],
                workloads.append(
                    {
                        "author": str(work.author).strip().replace(" ", ".").lower(),
                        "day": work.started[:10],
                        "timeSpentSecond": work.timeSpentSeconds,
                        "key": task.key,
                        "project": task.key.split("-")[0],
                    }
                )
        # print(workloads)
        now = datetime.now().strftime("%Y%m%d")
        path_file = (
            f"{self._path_data}workloads_{self._project}_"
            f"{start_date.replace('-', '')}_{date_to.replace('-', '')}_{now}.json"
        )
        if file:
            with open(path_file, "w", encoding="utf-8") as f:
                json.dump(workloads, f, indent=2)
        return workloads

    def tree_jira(self, dates: list, filtre: str = "", suffix: str = ""):
        # us_date = self.epic_ticket(
        #     dates=dates, filtre=filtre, suffix=suffix, file=False
        # )[0]
        tickets_fields = ["parent", "created"]
        for ticket in self.search(
            jql_str=self._filter_project() + filtre + " ORDER BY key asc",
            max_results=False,
            expand="changelog",
            trc=False,
            fields=", ".join(tickets_fields),
        ):
            created = ticket.fields.created[:10]
            ticket_super = attrgetter("parent")(ticket.fields)
            print(created, ticket_super)
