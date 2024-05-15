# https://pypi.org/project/v1pysdk/
# https://github.com/mtalexan/VersionOne.SDK.Python
# https://pypi.org/project/ntlm-auth/
# https://XXXXX/VersionOne/meta.v1/Story
# https://XXXXX/VersionOne/rest-1.v1/Data/Story/2881576

from v1pysdk import V1Meta
from HtmlClipboard import put_html
from charts.donut import Donut
from config import config
from collections import OrderedDict
from datetime import datetime
from html import escape
from string import ascii_letters, digits
from typing import List
import yaml
import json
from yaml.loader import SafeLoader

fields_html = (
    "Number",
    "Name",
    "Status.Name",
    "Estimate",
    "Timebox.Name",
    "TaggedWith",
)
fields_tab = ("Number", "Name", "Estimate", "Status.Name")
naming = {
    "Number": "Id",
    "Name": "Title",
    "Status.Name": "Status",
    "Estimate": "Estimate",
    "Timebox.Name": "Iteration",
    "Super.Name": "Portfolio",
    "TaggedWith": "Tags",
    "Super.Number": "Portfolio Id",
    "ChildrenAndDown.ToDo.@Sum": "Total To Do Effort",
    "ChildrenAndDown[AssetState!='Dead'].ToDo.@Sum": "Total To Do Effort",
    "ToDo": "Total To Do Effort",
    "Scope.Name": "Planning Level",
}

# https://versionone.github.io/api-docs
# Asset States
# Asset states represent system-known life-cycle stage of an asset. The UI typically only show assets that are not "Dead".
# State 	Name 	            Meaning
# 0 	    Future
# 64 	    Active 	            The asset has been assigned to a user-defined workflow status.
# 128 	    Closed 	            The asset has been closed or quick-closed.
# 200 	    Template (Dead) 	The asset is only used to create new copies as part of creating from Templates or Quick Add.
# 208 	    Broken Down (Dead) 	The asset was converted to an Epic for further break-down.
# 255 	    Deleted (Dead) 	    The asset has been deleted.


def r(s):
    return "" if s is None or str(s) == "None" else str(s)


def version_one_conf() -> (
    dict[str, dict[str, dict[str, dict[str, str | int | list[str] | dict[str, str]]]]]
):
    data_conf: dict[
        str, dict[str, dict[str, dict[str, str | int | list[str] | dict[str, str]]]]
    ]
    # common str ou projets de projet avec fields, list, dict
    c = config()
    with open(c.Version_one.conf, "r", encoding="utf-8") as f:
        data_conf = yaml.load(f, Loader=SafeLoader)
    return data_conf


def str_file(title):
    valid_chars = "-_.() %s%s" % (ascii_letters, digits)
    filename = "".join(c for c in title if c in valid_chars)
    return filename.replace(" ", "_")


def extracts(conf, title, filters, asof, fields, limit: int = None):
    tickets = {}
    name_extract = str_file(f"{title}_{asof if asof else ''}")
    try:
        with open(conf["path_data"] + "date_extract.txt", "r") as date_extract:
            lines = date_extract.readlines()
    except FileNotFoundError:
        lines = []
    present = False
    for line in lines:
        line = line.replace("\n", "")
        if asof and line.split(":")[0] == name_extract and line[-19:-9] >= asof:
            present = True
            break
    if present:
        with open(
            f"{conf['path_data']}result_extract_{name_extract}.json",
            "r",
            encoding="utf-8",
        ) as fp:
            features = json.load(fp)
    else:
        with V1Meta(
            address=conf["url_server"],
            instance=conf["instance"],
            password=conf["token"],
            use_password_as_token=True,
        ) as v1:
            for apppend_filter in filters:
                for idref, s in stories(
                    conf=conf,
                    ver1=v1,
                    fields=fields,
                    s_filter=apppend_filter,
                    json=True,
                    asof=asof,
                ):
                    tickets[idref] = s
                for idref, s in defect(
                    conf=conf,
                    ver1=v1,
                    fields=fields,
                    s_filter=apppend_filter,
                    json=True,
                    asof=asof,
                ):
                    tickets[idref] = s
        features = {}
        for ticket in tickets.values():
            if ticket["Super.Number"] in features:
                features[ticket["Super.Number"]]["story"][ticket["Number"]] = ticket
            else:
                features[ticket["Super.Number"]] = {
                    "Name": ticket["Super.Name"],
                    "story": {ticket["Number"]: ticket},
                    "status": ticket["Super.Status.Name"],
                }
        if asof:
            with open(
                f"{conf['path_data']}result_extract_{name_extract}.json",
                "w",
                encoding="utf-8",
            ) as fp:
                json.dump(features, fp)
        with open(conf["path_data"] + "date_extract.txt", "a") as date_export:
            date_export.write(
                f"{name_extract}: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
    if limit:
        fs = {}
        for k, v in features.items():
            if limit == 0:
                break
            fs[k] = v
            limit -= 1
    else:
        fs = features
    return fs


def get_fields(max_super):
    fields = ["Estimate", "Timebox.Name", "AssetState", "Team.Name"]
    for i in range(max_super):
        for field in ("Number", "Name", "Status.Name"):
            fields.append("Super." * i + field)
    return fields


def iteration(
    conf,
    timebox,
    append_filters: List[str] = [""],
    html=False,
    dic=False,
    ver1=None,
    image=False,
    json=False,
    fields=("Number", "Name", "Status.Name", "Estimate", "Timebox.Name", "TaggedWith"),
    order=None,
    link=True,
    asof=None,
):
    tab = "<style>table.sm, .sm th, .sm td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
    tickets = []
    ticketsjson = {}
    if html:
        vals = OrderedDict(
            [
                ("", 0),
                ("ToDo", 0),
                ("In Progress", 0),
                ("Blocked", 0),
                ("In Test", 0),
                ("To Integrate", 0),
                ("To Test PO", 0),
                ("Done", 0),
            ]
        )
        datas = []
        t = (
            ver1.Timebox.filter("Name='" + timebox + "'")
            .select("ID")
            .asof([] if asof is None else asof)[0]
        )
        iteration_url = f"https://{conf['url_server']}/{conf['instance']}/Iteration.mvc/Summary?oidToken={t.idref}"
        tab += '<h1><a href="' + iteration_url + '">' + timebox + "</a></h1>"
        tab += '<table class="sm"><thead><tr><th>'
        tab += "</th><th>".join([naming[f] for f in fields])
        tab += "</th></tr></thead>\n"
        for append_filter in append_filters:
            #  + "';AssetState!='Closed'" si on enleve les clos
            for s, data in stories(
                conf=conf,
                s_filter=append_filter,
                html=html,
                dic=dic,
                ver1=ver1,
                fields=fields,
                order=order,
                link=link,
                asof=asof,
            ):
                tab += s
                datas.append(data)
        for append_filter in append_filters:
            for d, data in defect(
                conf=conf,
                s_filter=append_filter,
                html=html,
                dic=dic,
                ver1=ver1,
                fields=fields,
                order=order,
                link=link,
                asof=asof,
            ):
                tab += d
                datas.append(data)
        tab += "</table>"
        if image:
            for s in datas:
                status = r(s.Status.Name)
                vals[status] = vals[status] + 1
            tab += Donut(vals).build().chart_html()
        put_html(tab, source=conf["url_server"])
        return tab
    elif dic:
        for append_filter in append_filters:
            for s in stories(
                conf=conf,
                s_filter=append_filter,
                html=html,
                dic=dic,
                ver1=ver1,
                fields=fields,
                order=order,
                link=link,
            ):
                tickets.append((*s,))
        for append_filter in append_filters:
            for d in defect(
                conf=conf,
                s_filter=append_filter,
                html=html,
                dic=dic,
                ver1=ver1,
                fields=fields,
                order=order,
                link=link,
            ):
                tickets.append((*d,))
        return tickets
    elif json:
        for append_filter in append_filters:
            for idref, s in stories(
                conf=conf,
                s_filter=append_filter,
                html=html,
                dic=dic,
                ver1=ver1,
                fields=fields,
                order=order,
                link=link,
                json=json,
                asof=asof,
            ):
                ticketsjson[idref] = s
        for append_filter in append_filters:
            for idref, d in defect(
                conf=conf,
                s_filter=append_filter,
                html=html,
                dic=dic,
                ver1=ver1,
                fields=fields,
                order=order,
                link=link,
                json=json,
                asof=asof,
            ):
                ticketsjson[idref] = d
        return ticketsjson
    else:
        print(timebox)
        print("\t", " | ".join([naming[f] for f in fields]), sep="")
        for append_filter in append_filters:
            for s in stories(
                conf=conf,
                s_filter=append_filter,
                html=html,
                dic=dic,
                ver1=ver1,
                fields=fields,
                order=order,
                link=link,
            ):
                print(*s, sep=" | ")
        for append_filter in append_filters:
            for d in defect(
                conf=conf,
                s_filter=append_filter,
                html=html,
                dic=dic,
                ver1=ver1,
                fields=fields,
                order=order,
                link=link,
            ):
                print(*d, sep=" | ")


def feature(
    conf,
    append_filters: list[str] = ("",),
    html: bool = False,
    dic=False,
    ver1=None,
    fields=("Number", "Name", "Status.Name", "Estimate", "Timebox.Name", "TaggedWith"),
    fields_epic: list[str] = ("Name", "Number", "ID"),
    image: bool = False,
    json: bool = False,
    children: bool = True,
):
    tab = "<style>table.sm, .sm th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
    ticketsjson = {}
    for append_filter in append_filters:
        datas = []
        datas_defect = []
        for e in ver1.Epic.filter(append_filter).select(*fields_epic):
            # TODO reprendre list status in config
            vals = OrderedDict(
                [
                    ("", 0),
                    ("To Do", 0),
                    ("In Progress", 0),
                    ("Blocked", 0),
                    ("In Test", 0),
                    ("To Integrate", 0),
                    ("To Test PO", 0),
                    ("Accepted", 0),
                    ("Done", 0),
                ]
            )
            if html:
                epic_url = f"https://{conf['url_server']}/{conf['instance']}/Epic.mvc/Summary?oidToken={e.idref}"
                tab += (
                    f'<h1><a href="{epic_url}">{e.Number}:  {escape(e.Name)}</a></h1>'
                )
                tab += '<table class="sm"><thead><tr><th>'
                tab += "</th><th>".join([naming[f] for f in fields])
                tab += "</th></tr></thead>\n"
                for s, data in stories(
                    conf=conf,
                    s_filter="Super='" + e.idref + "'",
                    html=html,
                    dic=dic,
                    ver1=ver1,
                    fields=fields,
                ):
                    tab += s
                    datas.append(data)
                for s, data in defect(
                    conf=conf,
                    s_filter="Super='" + e.idref + "'",
                    html=html,
                    dic=dic,
                    ver1=ver1,
                    fields=fields,
                ):
                    tab += s
                    datas_defect.append(data)
                tab += "</table>"
                if image:
                    for s in datas:
                        status = r(s.Status.Name)
                        vals[status] = vals[status] + 1
                    tab += Donut(vals).build().chart_html()
            elif json:
                if children:
                    for idref, s in stories(
                        conf=conf,
                        s_filter="Super='" + e.idref + "'",
                        html=html,
                        dic=dic,
                        ver1=ver1,
                        fields=fields,
                        json=True,
                    ):
                        ticketsjson[idref] = s
                    for idref, d in defect(
                        conf=conf,
                        s_filter="Super='" + e.idref + "'",
                        html=html,
                        dic=dic,
                        ver1=ver1,
                        fields=fields,
                        json=True,
                    ):
                        ticketsjson[idref] = d
                else:
                    ticketsjson[e.idref] = {}
                    for c in fields_epic:
                        ticketsjson[e.idref][c] = r(eval("s." + c, {"s": e}))
            else:
                if children:
                    print(e.idref)
                    print("\t", " | ".join([naming[f] for f in fields]), sep="")
                    for s in stories(
                        conf=conf,
                        s_filter="Super='" + e.idref + "'",
                        html=html,
                        dic=dic,
                        ver1=ver1,
                        fields=fields,
                    ):
                        print(*s, sep=" | ")
                    for s in defect(
                        conf=conf,
                        s_filter="Super='" + e.idref + "'",
                        html=html,
                        dic=dic,
                        ver1=ver1,
                        fields=fields,
                    ):
                        print(*s, sep=" | ")
                else:
                    epic_url = f"https://{conf['url_server']}/{conf['instance']}/Epic.mvc/Summary?oidToken={e.idref}"
                    print(epic_url)
                    print("\t", " | ".join([naming[f] for f in fields]), sep="")
                    print(
                        "\t",
                        "\t".join([r(eval("d." + f, {"d": e})) for f in fields]),
                        sep="",
                    )
    if html:
        put_html(tab, source=conf["url_server"])
        return tab
    if json:
        return ticketsjson


def b_html(conf, c, s, number):
    if c == "Number":
        return number
    elif c == "Super.Name" and s.Super:
        sup_url = (
            f"https://{conf['url_server']}/{conf['instance']}/Epic.mvc/Summary?oidToken="
            + s.Super.idref
        )
        return '<a href="' + sup_url + '">' + escape(s.Super.Name) + "</a>"
    elif c == "Timebox.Name" and s.Timebox:
        iteration_url = (
            f"https://{conf['url_server']}/{conf['instance']}/Iteration.mvc/Summary?oidToken="
            + s.Timebox.idref
        )
        return '<a href="' + iteration_url + '">' + s.Timebox.Name + "</a>"
    elif c == "TaggedWith" and s.TaggedWith:
        tagged = []
        for ta in s.TaggedWith:
            if ta is not None:
                tag_url = (
                    f"https:///{conf['url_server']}/{conf['instance']}/Search.mvc/Tagged?tag="
                    + str(ta)
                )
                tagged.append('<a href="' + tag_url + '">' + escape(str(ta)) + "</a>")
        return " ".join(tagged)
    else:
        return escape(r(eval("s." + c, {"s": s})))


def stories(
    conf,
    s_filter,
    html=False,
    dic=False,
    ver1=None,
    fields=None,
    order=("Super", "-Status", "Order"),
    link=True,
    json=False,
    asof=None,
):
    if order is None:
        order = ("Super", "-Status", "Order")
    for s in (
        ver1.Story.select(*fields)
        .filter(s_filter)
        .sort(*order)
        .asof([] if asof is None else asof)
    ):
        if html:
            story_url = (
                f"https://{conf['url_server']}/{conf['instance']}/story.mvc/Summary?oidToken="
                + s.idref
            )
            number = '<a href="' + story_url + '">' + s.Number + "</a>"
            yield "<tr><td>" + "</td><td>".join(
                [b_html(conf, c, s, number) for c in fields]
            ) + "</td></tr>\n", s
        elif dic:
            if link:
                story_url = (
                    f"https://{conf['url_server']}/{conf['instance']}/story.mvc/Summary?oidToken="
                    + s.idref
                )
                number = (
                    '<a href="'
                    + story_url
                    + '" style="text-decoration:none;">'
                    + s.Number
                    + "</a>"
                )
                yield [b_html(conf, c, s, number) for c in fields]
            else:
                yield [r(eval("s." + c, {"s": s})) for c in fields]
        elif json:
            d = {}
            todo_sum = 0.0
            for c in fields:
                if c in (
                    "ChildrenAndDown.ToDo.@Sum",
                    "ToDo",
                    "ChildrenAndDown[AssetState!='Dead'].ToDo.@Sum",
                ):
                    todo = r(s[c])
                    if todo != "":
                        todo_sum += float(todo)
                        d["ToDo"] = todo_sum
                elif c in (
                    "BlockingIssues.Name",
                    "BlockingIssues.AssetState",
                    "BlockingIssues.Number",
                ):
                    field_blocking = c[15:]
                    for blocking_issue in s.BlockingIssues:
                        if "BlockingIssues" in d:
                            if blocking_issue.idref in d["BlockingIssues"]:
                                d["BlockingIssues"][blocking_issue.idref][
                                    field_blocking
                                ] = r(blocking_issue[field_blocking])
                            else:
                                d["BlockingIssues"][blocking_issue.idref] = {
                                    field_blocking: r(blocking_issue[field_blocking])
                                }
                        else:
                            d["BlockingIssues"] = {
                                blocking_issue.idref: {
                                    field_blocking: r(blocking_issue[field_blocking])
                                }
                            }
                elif "Goals" in c:
                    field_goal = c.split("Goals.")[1]
                    field_level_goal = c.split(".Goals")[0].split("Goals")[0] + ".Goals"
                    for goal in s.Goals:
                        if "Goals" in d:
                            if goal.idref in d["Goals"]:
                                d["Goals"][goal.idref][field_goal] = r(goal[field_goal])
                            else:
                                d["Goals"][goal.idref] = {
                                    field_goal: r(goal[field_goal])
                                }
                                d["Goals"][goal.idref][field_level_goal] = r(
                                    goal[field_level_goal]
                                )
                        else:
                            d["Goals"] = {goal.idref: {field_goal: r(goal[field_goal])}}
                else:
                    d[c] = r(eval("s." + c, {"s": s}))
            d["idref"] = r(s.idref)
            if "Super.Number" in fields:
                d["Super.idref"] = r(s.Super.idref)
            yield s.idref, d
        else:
            yield "\t" + s.Number, s.Name, r(s.Status.Name), r(s.Estimate), r(
                s.Timebox.Name
            )


def defect(
    conf,
    s_filter,
    html=False,
    dic=False,
    ver1=None,
    fields=None,
    order=("Super", "-Status", "Order"),
    link=True,
    json=False,
    asof=None,
):
    if order is None:
        order = ("Super", "-Status", "Order")
    for d in (
        ver1.Defect.select(*fields)
        .filter(s_filter)
        .sort(*order)
        .asof([] if asof is None else asof)
    ):
        if html:
            story_url = (
                f"https://{conf['url_server']}/{conf['instance']}/defect.mvc/Summary?oidToken="
                + d.idref
            )
            number = '<a href="' + story_url + '">' + d.Number + "</a>"
            yield "<tr><td>" + "</td><td>".join(
                [b_html(conf, c, d, number) for c in fields]
            ) + "</td></tr>\n", d
        elif dic:
            if link:
                story_url = (
                    f"https://{conf['url_server']}/{conf['instance']}/defect.mvc/Summary?oidToken="
                    + d.idref
                )
                number = (
                    '<a href="'
                    + story_url
                    + '" style="text-decoration:none;">'
                    + d.Number
                    + "</a>"
                )
                yield [b_html(conf, c, d, number) for c in fields]
            else:
                yield [r(eval("d." + c, {"d": d})) for c in fields]
        elif json:
            di = {}
            todo_sum = 0.0
            for c in fields:
                if c in (
                    "ChildrenAndDown.ToDo.@Sum",
                    "ToDo",
                    "ChildrenAndDown[AssetState!='Dead'].ToDo.@Sum",
                ):
                    todo = r(d[c])
                    if todo != "":
                        todo_sum += float(todo)
                        di["ToDo"] = todo_sum

                elif c in (
                    "BlockingIssues.Name",
                    "BlockingIssues.AssetState",
                    "BlockingIssues.Number",
                ):
                    field_blocking: c[15:]
                    for blocking_issue in d.BlockingIssues:
                        if "BlockingIssues" in di:
                            if blocking_issue.idref in di["BlockingIssues"]:
                                di["BlockingIssues"][blocking_issue.idref][
                                    field_blocking
                                ] = r(blocking_issue[field_blocking])
                            else:
                                di["BlockingIssues"][blocking_issue.idref] = {
                                    field_blocking: r(blocking_issue[field_blocking])
                                }
                        else:
                            di["BlockingIssues"] = {
                                blocking_issue.idref: {
                                    field_blocking: r(blocking_issue[field_blocking])
                                }
                            }
                elif "Goals" in c:
                    field_goal = c.split("Goals.")[1]
                    field_level_goal = c.split(".Goals")[0].split("Goals")[0] + ".Goals"
                    for goal in d.Goals:
                        if "Goals" in di:
                            if goal.idref in di["Goals"]:
                                di["Goals"][goal.idref][field_goal] = r(
                                    goal[field_goal]
                                )
                            else:
                                di["Goals"][goal.idref] = {
                                    field_goal: r(goal[field_goal])
                                }
                                di["Goals"][goal.idref][field_level_goal] = r(
                                    goal[field_level_goal]
                                )
                        else:
                            di["Goals"] = {
                                goal.idref: {field_goal: r(goal[field_goal])}
                            }
                else:
                    di[c] = r(eval("d." + c, {"d": d}))
            di["idref"] = r(d.idref)
            if "Super.Number" in fields:
                di["Super.idref"] = r(d.Super.idref)
            yield d.idref, di
        else:
            yield "\t" + d.Number, d.Name, r(d.Status.Name), r(d.Estimate), r(
                d.Timebox.Name
            )


def test_versionone():
    conf = version_one_conf()["projects"]["testV1"]
    with V1Meta(
        address=conf["url_server"],
        instance=conf["instance"],
        # scheme='https',  # optional, defaults to https
        # username='',
        password=conf["token"],
        use_password_as_token=True,
    ) as v1:
        # Example:
        # user = v1.Member(20)  # internal numeric ID
        # print(user.CreateDate, user.Name)
        # s = v1.asset_from_oid('Story:XXXXXXX')
        # print(s.ID)
        # print(s.TaggedWith)
        # print(s.ChildrenAndDown.To Do)
        # for s in (v1.Story.select('ChildrenAndDown.To Do.@Sum').filter('Number="S-XXXXXXX"')):
        for s1 in v1.Story.select(
            "ChildrenAndDown:Task",
            "ChildrenAndDown:Test",
            "Owners",
            "ChildrenAndDown.ToDo.@Sum",
        ).filter('Number="S-XXXXXXX"'):
            # for s in (v1.Story.select('Number').filter('Number="S-XXXXXX"')):
            for t in s1["ChildrenAndDown:Task"]:
                print(t.idref, t.Name)
            for t in s1["Owners"]:
                print(t.idref, t.Name, t.Nickname)
            print(s1)
        # Filter by tags: "TaggedWith='MIP0.0.9.0'"
