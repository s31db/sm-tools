import json

from helpers.prepare_date_sprint import sprint_dates
from sm import jiraconf
from charts.barhorizontal import BarHorizontal
from datetime import datetime
from helpers.string_helper import r


def dates(start_date, weeks, end_date=None, exclude_dates=None):
    return [
        i
        for i in sprint_dates(start_date, weeks, end_date=end_date)
        if not (exclude_dates and i in exclude_dates)
    ]


def sprint_run(code, sprints, with_name, date, html=True):
    dataconf = jiraconf()
    colors = dataconf["projects"][code]["colors"]
    url_server = dataconf["projects"][code]["url_server"]
    path_export = dataconf["projects"][code]["path_export"]
    with open(
        f"{dataconf["projects"][code]["path_data"]}{date}{code}_.json",
        "r",
        encoding="utf-8",
    ) as fp:
        data = json.load(fp)
    if html:
        sprint_run_html(url_server, colors, code, data, sprints, with_name, path_export)
    else:
        sprint_run_chart(colors, data, sprints, with_name)


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
    yield "<table style='border: 1px solid'><tr><th>id</th>"
    ticket_sprint = calcul_tickets_sprint(
        data=data, html=True, name_sprint=name_sprint, sds=sds, with_name=with_name
    )
    for sd in sds:
        yield f"<th>{sd}</th>"
    yield "</tr>"
    for k, s in ticket_sprint.items():
        if not (
            s["name"].startswith("RUN / PROD Sprint")
            or s["name"].startswith("RUN/PROD Sprint")
        ):
            link = f"<a href='{url_server}browse/{k}'>{k}</a>"
            if with_name:
                yield f"<tr><td>{link} {s["name"]}</td>"
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
                                "name": ticket["name"],
                                "estimate": {sd: ticket["estimate"]},
                            }
                            last_estimate = ticket["estimate"]
                        else:
                            ticket_sprint[id] = [(status, sd)]
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
