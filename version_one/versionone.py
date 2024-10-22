from v1pysdk import V1Meta
from HtmlClipboard import put_html
from charts.donut import Donut
from config import config
from datetime import datetime
from helpers.string_helper import r, str_file
from html import escape
import yaml
import json
from yaml.loader import SafeLoader

DEFAULT_FIELDS = (
    "Number",
    "Name",
    "Status.Name",
    "Estimate",
    "Timebox.Name",
    "TaggedWith",
)

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
    "PlannedBusinessValue": "Business Value",
    "Workitems.SubsAndDown:PrimaryWorkItem.@Sum": "Ticket Count",
    "Dependencies": "Upstream dependencies",
    "Dependants": "Downstream dependencies",
}


def version_one_conf() -> (
    dict[str, dict[str, dict[str, dict[str, str | int | list[str] | dict[str, str]]]]]
):
    c = config()
    with open(c.Version_one.conf, "r", encoding="utf-8") as f:
        data_conf = yaml.load(f, Loader=SafeLoader)
    return data_conf


def extract_tree(
    conf: dict[
        str, dict[str, dict[str, dict[str, str | int | list[str] | dict[str, str]]]]
    ],
    title: str,
    filters: list[str],
    asof: str | None,
    fields: list[str],
    limit: int = None,
):
    tickets = {}
    name_extract = str_file(f"{title}_{asof if asof else ''}")
    if extract_exist(
        conf=conf, asof=asof, name_extract=name_extract, name_file="date_extract"
    ):
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
        ) as ver1:
            for s_filter in filters:
                for type_vone in [ver1.Story, ver1.Defect]:
                    for idref, ticket in extract_datas(
                        s_filter=s_filter,
                        fields=fields,
                        asof=asof,
                        type_vone=type_vone,
                    ):
                        tickets[idref] = ticket
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
            save_extract(
                conf=conf,
                datas=features,
                name_extract=name_extract,
                name_file="date_extract",
                prefix="result_extract_",
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


def save_extract(
    conf: dict, datas: dict, name_extract: str, name_file: str, prefix: str
):
    with open(
        f"{conf['path_data']}{prefix}{name_extract}.json",
        "w",
        encoding="utf-8",
    ) as fp:
        json.dump(datas, fp)
    with open(f'{conf["path_data"]}{name_file}.txt', "a") as date_export:
        date_export.write(
            f"{name_extract}: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )


def extract_exist(conf: dict, asof: str, name_extract: str, name_file: str):
    try:
        with open(f'{conf["path_data"]}{name_file}.txt', "r") as date_extract:
            lines = date_extract.readlines()
        for line in lines:
            line = line.replace("\n", "")
            if asof and line.split(":")[0] == name_extract and line[-19:-9] >= asof:
                return True
    except FileNotFoundError:
        pass
    return False


def epic_html(
    conf,
    ver1: V1Meta,
    filters: list[str] = ("",),
    fields: list[str] = DEFAULT_FIELDS,
    fields_epic: list[str] = ("Name", "Number", "ID"),
    image: bool = False,
):
    tab = "<style>table.sm, .sm th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
    for s_filter in filters:
        datas = []
        for e in ver1.Epic.filter(s_filter).select(*fields_epic):
            vals = {status: 0 for status in conf["colors"].keys()}
            tab += "<style>table.sam, .sam th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
            epic_url = f"https://{conf['url_server']}/{conf['instance']}/Epic.mvc/Summary?oidToken={e.idref}"
            tab += f'<h1><a href="{epic_url}">{e.Number}:  {escape(e.Name)}</a></h1>'
            tab += "<style>.sam tr:nth-child(even){background-color: #F2F3F4}</style>"
            tab += '\n<table class="sam"><thead><tr><th>'
            tab += "</th><th>".join([naming[f] for f in fields])
            tab += "</th></tr></thead>\n"
            for type_vone in [ver1.Story, ver1.Defect]:
                for tr, data in tr_html(
                    conf=conf,
                    tickets=extract(
                        s_filter="Super='" + e.idref + "'",
                        fields=fields,
                        type_vone=type_vone,
                    ),
                    fields=fields,
                ):
                    tab += tr
                    datas.append(data)
            tab += "</table>"
            if image:
                for s in datas:
                    status = r(s.Status.Name)
                    vals[status] = vals[status] + 1
                tab += Donut(values=[vals]).build().chart_html()
    put_html(tab, source=conf["url_server"])
    return tab


def epic(
    filters: list[str] = ("",),
    ver1=None,
    fields=DEFAULT_FIELDS,
    fields_epic: list[str] = ("Name", "Number", "ID"),
    children: bool = True,
):
    ticketsjson = {}
    for s_filter in filters:
        for e in ver1.Epic.filter(s_filter).select(*fields_epic):
            if children:
                for type_vone in [ver1.Story, ver1.Defect]:
                    for idref, ticket in extract_datas(
                        s_filter="Super='" + e.idref + "'",
                        fields=fields,
                        type_vone=type_vone,
                    ):
                        ticketsjson[idref] = ticket
            else:
                datas = ticketsjson[e.idref] = {}
                for field in fields_epic:
                    extract_fields(field=field, datas=datas, ticket=e, todo_sum=None)
    return ticketsjson


def epic_story_defect_txt(
    conf,
    filters: list[str] = ("",),
    ver1=None,
    fields=DEFAULT_FIELDS,
    fields_epic: list[str] = ("Name", "Number", "ID"),
    children: bool = True,
):
    for s_filter in filters:
        for e in ver1.Epic.filter(s_filter).select(*fields_epic):
            if children:
                yield e.idref
                print("\t", " | ".join([naming[f] for f in fields]), sep="")
                for type_vone in [ver1.Story, ver1.Defect]:
                    for idref, ticket in extract_datas(
                        s_filter="Super='" + e.idref + "'",
                        fields=fields,
                        type_vone=type_vone,
                    ):
                        yield " | ".join(ticket)
            else:
                epic_url = f"https://{conf['url_server']}/{conf['instance']}/Epic.mvc/Summary?oidToken={e.idref}"
                yield epic_url
                yield "\t", " | ".join([naming[f] for f in fields])
                yield "\t" + "\t".join([r(eval("d." + f, {"d": e})) for f in fields])


def data_field(field, ticket):
    if isinstance(dict, ticket):
        return ticket[field]
    else:
        # return getattr(ticket, field)
        return eval("ticket." + field, {"ticket": ticket})


def b_html(conf, c, ticket):
    if c == "Number":
        st = (
            "story"
            if ticket["Number"][0] == "S"
            else "goal" if ticket["Number"][0] == "G" else "defect"
        )
        idref = data_field("idref", ticket)
        # try:
        #     idref = ticket["idref"]
        # except KeyError:
        #     idref = ticket.idref
        ticket_url = f"https://{conf['url_server']}/{conf['instance']}/{st}.mvc/Summary?oidToken={idref}"
        number = f'<a href="{ticket_url}">{ticket["Number"]}</a>'
        return number
    elif c == "Super.Name":
        super_idref = data_field("idref", ticket)
        if super_idref:
            sup_url = f"https://{conf['url_server']}/{conf['instance']}/Epic.mvc/Summary?oidToken={super_idref}"
            return f'<a href="{sup_url}">{escape(ticket.Super.Name)}</a>'
        return ""
    elif c == "Timebox.Name":
        iteration_idref = data_field("Timebox.idref", ticket)
        iteration_url = f"https://{conf['url_server']}/{conf['instance']}/Iteration.mvc/Summary?oidToken={iteration_idref}"
        return f'<a href="{iteration_url}">{data_field("Timebox.Name", ticket)}</a>'
    elif c in ("Depencies", "Dependants"):
        deps = data_field(c, ticket)
        deps_datas = []
        if deps:
            for dep in deps:
                deps_datas += b_html(conf, "Number", dep)
        return " ".join(deps_datas)
    elif c == "TaggedWith" and ticket.TaggedWith:
        tagged = []
        for ta in ticket.TaggedWith:
            if ta is not None:
                tag_url = f"https://{conf['url_server']}/{conf['instance']}/Search.mvc/Tagged?tag={ta}"
                tagged.append('<a href="' + tag_url + '">' + escape(str(ta)) + "</a>")
        return " ".join(tagged)
    else:
        return escape(r(eval("ticket." + c, {"ticket": ticket})))


def extract_fields(
    field, datas, ticket, todo_sum, exclude_status: list[str] | None = None
):
    if field in (
        "ChildrenAndDown.ToDo.@Sum",
        "ToDo",
        "ChildrenAndDown[AssetState!='Dead'].ToDo.@Sum",
    ):
        todo = r(ticket[field])
        if todo != "":
            todo_sum += float(todo)
            datas["ToDo"] = todo_sum
    elif field in (
        "BlockingIssues.Name",
        "BlockingIssues.AssetState",
        "BlockingIssues.Number",
    ):
        field_blocking = field[15:]
        for blocking_issue in ticket.BlockingIssues:
            if "BlockingIssues" in datas:
                if blocking_issue.idref in datas["BlockingIssues"]:
                    datas["BlockingIssues"][blocking_issue.idref][field_blocking] = r(
                        blocking_issue[field_blocking]
                    )
                else:
                    datas["BlockingIssues"][blocking_issue.idref] = {
                        field_blocking: r(blocking_issue[field_blocking])
                    }
            else:
                datas["BlockingIssues"] = {
                    blocking_issue.idref: {
                        field_blocking: r(blocking_issue[field_blocking])
                    }
                }
    elif "Goals" in field:
        extract_goals_recursive(datas, field, ticket, exclude_status=exclude_status)
    elif "Dependencies" in field:
        extract_field_recursive(datas, field, ticket, field_family="Dependencies")
    elif "Dependants" in field:
        extract_field_recursive(datas, field, ticket, field_family="Dependencies")
    else:
        datas[field] = r(eval("ticket." + field, {"ticket": ticket}))


def extract_field_recursive(datas, field: str, ticket, field_family: str):
    field_recursive = field.split(f"{field_family}.")[1]
    if f".{field_family}" in field:
        if ticket.idref in datas[field_family]:
            level_super_field = field.split(f".{field_family}")[0]
            level_field = f"{level_super_field}.{field_family}"
            tickets = data_field(level_field, ticket)
        else:
            tickets = data_field(field_family, ticket)
        if tickets:
            for ticket in tickets:
                if field_family in datas:
                    if ticket.idref in datas[field_family]:
                        datas[field_family][ticket.idref][field_recursive] = r(
                            eval("ticket." + field_recursive, {"ticket": ticket})
                        )
                    else:
                        datas[field_family][ticket.idref] = {
                            field: r(eval("ticket." + field, {"ticket": ticket}))
                        }
                else:
                    datas[field_family] = {
                        ticket.idref: {
                            field_recursive: {
                                field: r(
                                    eval(
                                        "ticket." + field_recursive, {"ticket": ticket}
                                    )
                                )
                            }
                        }
                    }


def extract_goals_recursive(
    datas, field, ticket, exclude_status: list[str] | None = None
):
    if exclude_status or ticket.Status.Name in exclude_status:
        return None
    field_goal = field.split("Goals.")[1]
    if "SuperAndUp" in field:
        goals = [father.Goals for father in ticket.SuperAndUp]
    elif "SuperAndMe" in field:
        goals = [father.Goals for father in ticket.SuperAndMe]
    elif ".Goals" in field:
        level_super_field = field.split(".Goals")[0]
        level_field = f"{level_super_field}.Goals"
        goals = data_field(level_field, ticket)
    else:
        goals = data_field("Goals", ticket)
    if goals:
        for goal in goals:
            if "Goals" in datas:
                if goal.idref in datas["Goals"]:
                    datas["Goals"][goal.idref][field_goal] = r(
                        eval("goal." + field_goal, {"goal": goal})
                    )
                else:
                    datas["Goals"][goal.idref] = {
                        field_goal: r(eval("goal." + field_goal, {"goal": goal}))
                    }
            else:
                datas["Goals"] = {
                    goal.idref: {
                        field_goal: r(eval("goal." + field_goal, {"goal": goal}))
                    }
                }


def extract_datas(
    s_filter: str,
    type_vone,
    fields: list[str],
    order: list[str] = ("Super", "-Status", "Order"),
    asof: str | None = None,
    exclude_status: list[str] | None = None,
) -> tuple[str, dict]:
    for ticket in extract(
        s_filter=s_filter, type_vone=type_vone, fields=fields, order=order, asof=asof
    ):
        datas = {}
        todo_sum = 0.0
        for field in fields:
            extract_fields(field, datas, ticket, todo_sum, exclude_status)
        datas["idref"] = r(ticket.idref)
        if "Super.Number" in fields:
            datas["Super.idref"] = r(ticket.Super.idref)
        yield ticket.idref, datas


def extract(
    s_filter: str,
    type_vone,
    fields: list[str],
    order: list[str] = ("Super", "-Status", "Order"),
    asof: str | None = None,
):
    for ticket in (
        type_vone.select(*fields)
        .filter(s_filter)
        .sort(*order)
        .asof([] if asof is None else asof)
    ):
        yield ticket


def extracts_story_defect(
    ver1: V1Meta,
    filters: list[str] = [""],
    fields: list[str] = DEFAULT_FIELDS,
    order: list[str] = ("Super", "-Status", "Order"),
    asof: str = None,
    exclude_status: list[str] | None = None,
):
    tickets = {}
    for s_filter in filters:
        for type_vone in [ver1.Story, ver1.Defect]:
            for idref, s in extract_datas(
                s_filter=s_filter,
                fields=fields,
                order=order,
                asof=asof,
                type_vone=type_vone,
                exclude_status=exclude_status,
            ):
                tickets[idref] = s
    return tickets


def extract_goals(conf, filters, fields):
    goals = {}
    with V1Meta(
        address=conf["url_server"],
        instance=conf["instance"],
        password=conf["token"],
        use_password_as_token=True,
    ) as ver1:
        for filtre in filters:
            for g in (
                ver1.Goal.select(*fields)
                .filter(filtre)
                .sort("-PlannedBusinessValue", "-Scope.Name")
            ):
                goal = goals[g.idref] = {"idref": g.idref, "Workitems": []}
                for field in fields:
                    if ".@" in field:
                        goal[field] = r(eval("g." + field))
                    elif "Workitems." in field:
                        for work_item in g.Workitems:
                            if work_item.idref in goal["Workitems"]:
                                goal["Workitems"][work_item.idref][field[10:]] = r(
                                    data_field(field[10:], work_item)
                                )
                            else:
                                goal["Workitems"][work_item.idref] = {
                                    field[10:]: data_field(field[10:], work_item)
                                }
                    else:
                        goal[field] = r(data_field(field, g))
    return goals


def tr_html(conf, tickets, fields, link: bool = True):

    for ticket in tickets:
        tab = "<tr><td>"
        if link:
            tab += "</td><td>".join([b_html(conf, c, ticket) for c in fields])
        else:
            tab += "</td><td>".join(
                [escape(r(eval("ticket." + c, {"ticket": ticket}))) for c in fields]
            )
        tab += "</td></tr>\n"
        yield tab, ticket


def test_versionone():
    conf = version_one_conf()["projects"]["testV1"]
    with V1Meta(
        address=conf["url_server"],
        instance=conf["instance"],
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


def test_epic_html():
    conf_test = version_one_conf()["projects"]["testV1"]
    with V1Meta(
        address=conf_test["url_server"],
        instance=conf_test["instance"],
        password=conf_test["token"],
        use_password_as_token=True,
    ) as v_one_test:
        val = "".join(
            epic_html(
                conf=conf_test,
                ver1=v_one_test,
                filters=['Number="E-01345"'],
                # image=True,
            )
        )
        assert (
            "<style>table.sm, .sm th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
            "<style>table.sam, .sam th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}"
            '</style><h1><a href="https://www14.v1host.com/v1sdktesting/Epic.mvc/Summary?oidToken=Epic:43560">E-01345:'
            '  a</a></h1><style>.sam tr:nth-child(even){background-color: #F2F3F4}</style>\n<table class="sam"><thead>'
            "<tr><th>Id</th><th>Title</th><th>Status</th><th>Estimate</th><th>Iteration</th><th>Tags</th></tr></thead>"
            '\n<tr><td><a href="https://www14.v1host.com/v1sdktesting/story.mvc/Summary?oidToken=Story:43561">S-11248'
            '</a></td><td>test story with epic</td><td></td><td></td><td><a href="https://www14.v1host.com/v1sdktesting'
            '/Iteration.mvc/Summary?oidToken=Timebox:42438">Sprint 1</a></td><td></td></tr>\n</table>'
            == val
        )


def test_epic_json():
    conf_test = version_one_conf()["projects"]["testV1"]
    with V1Meta(
        address=conf_test["url_server"],
        instance=conf_test["instance"],
        password=conf_test["token"],
        use_password_as_token=True,
    ) as v_one_test:
        val = epic(
            ver1=v_one_test,
            filters=['Number="E-01345"'],
        )
        assert val == {
            "Story:43561": {
                "Estimate": "",
                "Name": "test story with epic",
                "Number": "S-11248",
                "Status.Name": "",
                "TaggedWith": "[None]",
                "Timebox.Name": "Sprint 1",
                "idref": "Story:43561",
            }
        }
