import json

from helpers.prepare_date_sprint import sprint_dates
from sm import jiraconf
from charts.barhorizontal import BarHorizontal
from datetime import datetime
from helpers.string_helper import r
from atlassian.jiraSM import JiraSM


def dates(start_date, weeks, end_date=None, exclude_dates=None):
    return [
        i
        for i in sprint_dates(
            start_date[:10], weeks, end_date=end_date[:10] if end_date else None
        )
        if not (exclude_dates and i in exclude_dates)
    ]


def sprint_actif(project: str, conf: dict, previous: bool = False):
    with JiraSM(project=project, **conf).conn() as conn:
        if previous:
            sprint_id, sprint_infos = conn.previous_sprint()
        else:
            sprint_id, sprint_infos = conn.sprint_actif()
        return sprint_infos


def sprint_run(
    project: str,
    sprints: list | None,
    with_name: bool,
    date: str | None,
    html: bool = True,
    previous: bool = False,
    file: bool = True,
    db: bool = False,
):
    conf = jiraconf()["projects"][project]
    if sprints is None:
        sprints = (sprint_actif(project=project, conf=conf, previous=previous),)
    if date is None:
        date = datetime.today().strftime("%Y%m%d")
    colors = conf["colors"]
    url_server = conf["url_server"]
    path_export = conf["path_export"]
    if db:
        from db.db_project import tickets

        data = tickets(project=project)
    else:
        with open(
            f"{conf["path_data"]}{date}{project}_.json",
            "r",
            encoding="utf-8",
        ) as fp:
            data = json.load(fp)

    if html and not file:
        tab = ""
        for sprint in sprints:
            tab += "".join(
                by_sprint_html(
                    url_server=url_server,
                    colors=colors,
                    data=data,
                    name_sprint=sprint["name"],
                    start_date=sprint["start_date"],
                    weeks=sprint.get("weeks", 3),
                    end_date=sprint.get("end_date", None),
                    exclude_dates=sprint.get("exclude_dates", None),
                    with_name=with_name,
                )
            )
    elif html:
        tab = sprint_run_html(
            url_server,
            colors,
            project,
            data,
            sprints,
            with_name,
            path_export,
        )
    else:
        sprint_run_chart(colors, data, sprints, with_name)
    return tab


def sprint_run_chart(colors, data, sprints, with_name):
    for sprint in sprints:
        by_sprint_chart(
            colors=colors,
            data=data,
            name_sprint=sprint["name"],
            start_date=sprint["start_date"],
            weeks=3,
            end_date=sprint.get("end_date", None),
            with_name=with_name,
        )


def sprint_run_html(url_server, colors, code, data, sprints, with_name, path_export):
    tab = (
        "<!DOCTYPE html><html><head><style>"
        "th, td {padding: 15px; min-height: 25px;} "
        "tr:nth-child(even) {background-color: #f2f2f2;} "
        "th:nth-child(even) {background-color: #f2f2f2;} "
        "td:nth-child(even) {background-color: #f2f2f2;} "
        "table, td, th { border: 1px solid;} table {width: 100%; border-collapse: collapse;} td {text-align: center;}"
        "</style></head><body>"
    )
    for sprint in sprints:
        tab += "".join(
            by_sprint_html(
                url_server=url_server,
                colors=colors,
                data=data,
                name_sprint=sprint["name"],
                start_date=sprint["start_date"],
                weeks=sprint.get("weeks", 3),
                end_date=sprint.get("end_date", None),
                exclude_dates=sprint.get("exclude_dates", None),
                with_name=with_name,
            )
        )
        tab += "<br/>"
    tab += "</body>"
    with open(
        f"{path_export}/sprint_run_{code}.html",
        "w",
        encoding="utf-8",
    ) as fp:
        fp.write(tab)
    import webbrowser

    webbrowser.open(f"{path_export}/sprint_run_{code}.html")
    return tab


def by_sprint_html(
    url_server,
    colors,
    data,
    name_sprint,
    start_date,
    weeks,
    end_date,
    exclude_dates=None,
    with_name=False,
):
    sds = dates(
        start_date=start_date,
        weeks=weeks,
        end_date=end_date,
        exclude_dates=exclude_dates,
    )
    yield f"<p>{name_sprint}</p>"
    yield "<table style='border: 1px solid; font-size: 14px'><tr><th>id</th>"
    ticket_sprint = calcul_tickets_sprint(
        data=data, html=True, name_sprint=name_sprint, sds=sds, with_name=with_name
    )
    for sd in sds:
        yield f"<th>{sd}</th>"
    yield "</tr>"
    for k, s in ticket_sprint.items():
        link = f"<a href='{url_server}browse/{k}'>{k}</a>"
        if with_name:
            yield f"<tr><td>{link} {s["name"]}"
            if "assignee" in s and s["assignee"]:
                yield f" - {s["assignee"].split("@")[0]}"
            yield "</td>"
        else:
            yield f"<tr><td>{link}</td>"
        n = 1
        status = None
        for sd in sds:
            if sd <= datetime.today().strftime("%Y-%m-%d"):
                if sd in s:
                    if status:
                        yield f"<td colspan={n} style='background-color: {colors[status]}'>{status} {r(s["estimate"][sd])}</td>"
                        n = 1
                    status = s[sd]
                    last_sd = sd
                else:
                    if status:
                        n += 1
                    else:
                        yield f"<td id='{k}_{sd}'></td>"
        yield f"<td colspan={n} style='background-color: {colors[status]}'>{status} {r(s["estimate"][last_sd])}</td>"
        for sd in sds:
            if sd > datetime.today().strftime("%Y-%m-%d"):
                yield "<td style='background-color: white'/>"
        yield "</tr>"
    yield "</table>"


def by_sprint_chart(
    colors,
    data,
    name_sprint,
    start_date,
    weeks,
    end_date,
    exclude_dates=None,
    with_name=False,
):

    sds = dates(
        start_date=start_date,
        weeks=weeks,
        end_date=end_date,
        exclude_dates=exclude_dates,
    )

    ticket_sprint = calcul_tickets_sprint(
        data=data, html=False, name_sprint=name_sprint, sds=sds, with_name=with_name
    )

    BarHorizontal(
        name_sprint,
        end_date=sds[-1],
        datas_dates=ticket_sprint,
        colors=colors,
        legend=False,
        figsize=(15, 10),
    ).build().show()


def calcul_tickets_sprint(data, html, name_sprint, sds, with_name):
    ticket_sprint = {}
    ticket_sprint_last = {}
    for sd in sds:
        if sd in data:
            d = data[sd]
            for id, ticket in d.items():
                if in_sprint(name_sprint, ticket):
                    status = ticket["status"]
                    if with_name and not html:
                        id = f"{id} {ticket["name"]}"
                    if id in ticket_sprint:
                        if ticket_sprint_last[id] != status:
                            if html:
                                ticket_sprint[id][sd] = status
                                ticket_sprint[id]["estimate"][sd] = ticket["estimate"]
                                if last_estimate and (
                                    ticket["estimate"] is None
                                    or float(last_estimate) != float(ticket["estimate"])
                                ):
                                    last_estimate = ticket["estimate"]
                            else:
                                ticket_sprint[id].append((status, sd))
                    else:
                        if html:
                            ticket_sprint[id] = {
                                sd: status,
                                # "name": ticket["name"],
                                "estimate": {sd: ticket["estimate"]},
                            }
                            last_estimate = ticket["estimate"]
                        else:
                            ticket_sprint[id] = [(status, sd)]
                    if "assignee" in ticket:
                        ticket_sprint[id]["assignee"] = ticket["assignee"]
                    ticket_sprint[id]["name"] = ticket["name"]
                    ticket_sprint_last[id] = status
    return ticket_sprint


def in_sprint(name_sprint, ticket):
    # if ticket["sprints"]:
    #     for sprint in ticket["sprints"]:
    #         if (
    #             sprint.split(",name=")[-1]
    #             .split(",startDate=")[0]
    #             .startswith(name_sprint)
    #         ):
    #             return True
    #     return False
    return ticket["super.name"].startswith(name_sprint)
