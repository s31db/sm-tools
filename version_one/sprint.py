from v1pysdk import V1Meta
from version_one.versionone import iteration, naming, r, str_file
import json
from datetime import datetime, timedelta
from collections import OrderedDict
from charts.cumulative import Cumulative, previous_date
from helpers.prepare_date_sprint import (
    sprint_dates,
    previous_sprint_date,
    tomorrow_sprint_date,
)
from HtmlClipboard import put_html
from typing import List


def extract(conf, asofs, timebox: str, append_filters: List[str], id_filter: str):
    with V1Meta(
        address=conf["url_server"],
        instance=conf["instance"],
        password=conf["token"],
        use_password_as_token=True,
    ) as v1:
        # Start day as midnight.
        for asof in asofs:
            present = False
            date_len = len(asof)
            with open(conf["path_data"] + "date_export.txt", "r") as date_export:
                lines = date_export.readlines()
            for line in lines:
                if (
                    line[0:date_len] == asof
                    and line[date_len + 2 : date_len + 12] >= asof
                    and (
                        len(line) < date_len + 24
                        or line[date_len + 23 : -1] == id_filter
                    )
                ):
                    present = True
            if not present:
                it = iteration(
                    conf=conf,
                    timebox=timebox,
                    json=True,
                    ver1=v1,
                    link=False,
                    fields=(
                        "Number",
                        "Name",
                        "Status.Name",
                        "Estimate",
                        "Super.Number",
                        "Super.Name",
                        # 'ChildrenAndDown.ToDo.@Sum',
                        "ChildrenAndDown[AssetState!='Dead'].ToDo.@Sum",
                        "ToDo",
                        "Timebox.Name",
                    ),
                    asof=asof,
                    append_filters=append_filters,
                )
                with open(
                    f"{conf['path_data']}result{str_file(asof)}_{id_filter}.json",
                    "w",
                    encoding="utf-8",
                ) as fp:
                    json.dump(it, fp)
                with open(conf["path_data"] + "date_export.txt", "a") as date_export:
                    date_export.write(
                        f"{asof}: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}: {id_filter}\n"
                    )
    # print(it)


def read(
    conf,
    timebox: str,
    extr: bool = False,
    table: bool = True,
    graph: bool = True,
    append_filters: List[str] = [
        "",
    ],
    asof: str | None = None,
    start_date: str | None = None,
    weeks: int | None = None,
    end_date: str | None = None,
    now: bool = False,
):
    id_filter = str_file("¤".join(append_filters))
    if asof:
        tomorrow = asof
    else:
        d = datetime.today().strftime("%Y-%m-%d")
        # tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = tomorrow_sprint_date(d)
    asofs_all = [
        *sprint_dates(start_date=start_date, weeks=weeks, end_date=end_date, now=now)
    ]
    asofs = [d for d in asofs_all if d <= tomorrow]
    print(asofs)
    if extr:
        extract(
            conf=conf,
            asofs=asofs,
            timebox=timebox,
            append_filters=append_filters,
            id_filter=id_filter,
        )
    tab = ""
    if table:
        datas = {}
        new_story = {}
        remove_story = {}
        todos = {}
        todos_prec = {}
        last_status = {}
        data_prec = None
        asof_prec = None
        stories = OrderedDict()
        ord_item = 0
        # ord_portfolio = []
        ord_portfolio = {}
        for asof in asofs:
            with open(
                conf["path_data"] + "result" + asof + ".json", "r", encoding="utf-8"
            ) as fp:
                data = json.load(fp)
            datas[asof] = data
            for key, values in data.items():
                if key not in stories:
                    if values["Super.Name"] not in ord_portfolio:
                        # ord_portfolio.append(values['Super.Name'])
                        ord_portfolio[values["Super.Name"]] = {"pos": ord_item, "nb": 1}
                        values["ord_item"] = 1000 * ord_item + ord_item
                    else:
                        ord_portfolio[values["Super.Name"]]["nb"] += 1
                        values["ord_item"] = (
                            1000 * ord_portfolio[values["Super.Name"]]["pos"] + ord_item
                        )
                    # values['ord_item'] = 1000 * ord_portfolio.index(values['Super.Name']) + ord_item
                    # values['ord_item'] = 1000 * ord_portfolio[values['Super.Name']]['pos'] + ord_item
                    stories[key] = values
                    ord_item += 1
                else:
                    # update estimate
                    stories[key]["Estimate"] = values["Estimate"]
                date_status = asof_prec if asof_prec else asof
                time_in = 0
                if key in last_status:
                    if last_status[key]["name"] == values["Status.Name"]:
                        date_status = last_status[key]["date_status"]
                        time_in = last_status[key]["time_in"] + 1
                last_status[key] = {
                    "name": values["Status.Name"],
                    "date_status": date_status,
                    "time_in": time_in,
                }
            if data_prec and asof_prec:
                for key, values in data.items():
                    if key not in data_prec:
                        if key in new_story:
                            # new_story[key]['asof'].append(asof)
                            new_story[key].append(previous_date(asof))
                        else:
                            # new_story[key] = {'asof': [asof], 'values': values}
                            new_story[key] = [previous_date(asof)]
                        # print(asof, key, data[key])
                    # Attention si le To Do est mis à nul et pas à 0...
                    if "ToDo" in values and not (
                        key in todos_prec and todos_prec[key] == values["ToDo"]
                    ):
                        if key in todos:
                            todos[key][asof] = values["ToDo"]
                        else:
                            todos[key] = {asof: values["ToDo"]}
                        todos_prec[key] = values["ToDo"]

                for key in data_prec.keys():
                    if key not in data_prec:
                        if key in remove_story:
                            remove_story[key].append(previous_date(asof))
                        else:
                            remove_story[key] = [previous_date(asof)]
                        # print(asof, key, data[key])
            data_prec = data
            asof_prec = asof
        # print(new_story, remove_story, todos, sep='\n\n\n')

        tab += "<style>table.sam, .sam th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
        tab += "<style>.sam tr:nth-child(even){background-color: #F2F3F4}</style>"
        tab += '\n<table class="sam"><thead><tr><th>'
        fields = ("Super.Name", "Number", "Name", "Estimate", "ToDo", "Status.Name")
        tab += "</th><th>".join([naming[f] for f in fields])
        tab = tab.replace("Status", "First Status")
        tab += "</th><th>" + "</th><th>".join(
            ["Last Status", "RAE", "New", "Remove", "Date Status", "Day in Status"]
        )
        tab += "</th></tr></thead>\n"
        stories = OrderedDict(
            sorted(
                stories.items(),
                key=lambda key_value_pair: key_value_pair[1]["ord_item"],
            )
        )
        for key, values in stories.items():
            st = "story" if key[0] == "S" else "defect"
            story_url = f"https://{conf['url_server']}/{conf['instance']}/{st}.mvc/Summary?oidToken={key}"
            number = '<a href="' + story_url + '">' + values["Number"] + "</a>"
            # tab += '<tr><td>' + '</td><td>'.join([v1_html(c, values, number, ord_portfolio) for c in fields])
            # tab += '<tr><td>' + ''.join([v1_html(c, values, number, ord_portfolio) for c in fields])
            match last_status[key]:
                case "Done":
                    tab += '<tr style="background-color:#82E0AA">'
                case "Blocked":
                    tab += '<tr style="background-color:#E74C3C">'
                case _:
                    tab += "<tr>"
            tab += "".join(
                [
                    v1_html(conf, c, values, number, ord_portfolio, i)
                    for i, c in enumerate(fields)
                ]
            )
            tab += "<td"
            if last_status[key]["name"] not in ("Done", "Blocked"):
                tab += f' style="background-color: {conf["colors"][last_status[key]["name"]]}"'
            tab += ">" + last_status[key]["name"] + "</td>"
            # Tout les restes à faire
            # tab += '<td>' + (', '.join([d + ': ' + str(v) for d, v in todos[key].items()]) if key in todos else '') + '</td>'
            # last_rae = [d + ': ' + str(v) for d, v in todos[key].items()][-1] if key in todos else ''
            last_rae = (
                [[d, str(v)] for d, v in todos[key].items()][-1] if key in todos else ""
            )
            # tab += '<td>' + ('' if not last_rae or last_rae[-1] == '0.0' else ': '.join(last_rae)) + '</td>'
            tab += (
                "<td>"
                + (
                    ""
                    if not last_rae or last_rae[-1] == "0.0"
                    else
                    # ((datetime.strptime(last_rae[0], '%Y-%m-%d') - timedelta(days=1)).strftime(
                    #     '%Y-%m-%d') + ': ' + last_rae[1])) + '</td>'
                    (previous_date(last_rae[0]) + ": " + last_rae[1])
                )
                + "</td>"
            )
            tab += (
                "<td>"
                + (", ".join(new_story[key]) if key in new_story else "")
                + "</td>"
            )
            tab += (
                "<td>"
                + (", ".join(remove_story[key]) if key in remove_story else "")
                + "</td>"
            )
            tab += f"<td>{last_status[key]['date_status']}</td>"
            tab += f"<td"
            if last_status[key]["name"] in ("In Progress",):
                if last_status[key]["time_in"] > 5:
                    tab += f' style="background-color: red"'
                elif last_status[key]["time_in"] > 2:
                    tab += f' style="background-color: orange"'
            tab += f">{last_status[key]['time_in']}</td>"
            tab += "</tr>\n"
        # for s, data in stories(tags[self.path[1:]], html=True, ver1=v1, fields=fields):
        #     tab += s
        tab += "</table>"
        # print(tab)
        # print(datas)
    if graph:
        datas = {}
        for asof in asofs:
            with open(
                f"{conf['path_data']}result{str_file(asof)}_{id_filter}.json",
                "r",
                encoding="utf-8",
            ) as fp:
                datas[previous_sprint_date(asof)] = json.load(fp)
        tab += '<p style="text-align: center;">'
        # tab += burndown(asofs, asofs_all, title="Burn Down Sprint ") + '" alt="" />'
        asofs_all = [previous_sprint_date(d) for d in asofs_all]
        if len(asofs) > 1:
            tab += (
                Cumulative(
                    datas=datas,
                    asofs_all=asofs_all,
                    title="Workitem Cumulative Flow " + timebox,
                    **conf,
                )
                .build()
                .chart_html()
            )
        put_html(tab, source=conf["url_server"])
    return tab


def v1_html(conf, c, s, number, ord_portfolio, i):
    td = "</td>" if i > 0 else ""
    td += "<td"
    if c == "Number":
        return td + ">" + number
    elif c == "Super.Name" and "Super.Number" in s and s["Super.Number"] != "":
        if (
            s["ord_item"]
            == 1000 * ord_portfolio[s["Super.Name"]]["pos"]
            + ord_portfolio[s["Super.Name"]]["pos"]
        ):
            sup_url = f'https://{conf["url_server"]}/{conf["instance"]}/Epic.mvc/Summary?oidToken={s["Super.idref"]}'
            rowspan = ord_portfolio[s["Super.Name"]]["nb"]
            if rowspan > 1:
                td += f' style="background-color: white" rowspan="{str(rowspan)}">'
                td += f'<a href="{sup_url}">{s[c]}</a>'
                return td
            else:
                return td + 'd><a href="' + sup_url + '">' + s[c] + "</a>"
        else:
            return ""
    elif c == "Timebox.Name" and "Timebox" in s:
        iteration_url = f"https://{conf['url_server']}/{conf['instance']}/Iteration.mvc/Summary?oidToken={s['Timebox']}"
        return td + '><a href="' + iteration_url + '">' + s[c] + "</a>"
    elif c == "Status.Name":
        status = r(s[c] if c in s else None)
        if status == "Done":
            return td + ' style="background-color:green">' + status
        return td + ">" + status
    elif c == "TaggedWith" and s.TaggedWith:
        tagged = []
        for t in s.TaggedWith:
            if t is not None:
                tag_url = f"https://{conf['url_server']}/{conf['instance']}/Search.mvc/Tagged?tag={t}"
                tagged.append('<a href="' + tag_url + '">' + str(t) + "</a>")
        return " ".join(tagged)
    else:
        return "</td><td>" + r(s[c] if c in s else None)


if __name__ == "__main__":
    # extract()
    # extract(('2022-09-24', '2022-09-27'))
    # read()
    pass
