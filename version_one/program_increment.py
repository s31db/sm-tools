from v1pysdk import V1Meta
from version_one.versionone import (
    extracts_story_defect,
    version_one_conf,
    extract_goals,
    b_html,
    epic_html,
    extract_datas,
)
import json
from datetime import datetime
from html import escape
from helpers.string_helper import r
from charts.barhorizontal import  BarHorizontal


def stories_pi(
    conf,
    its: iter,
    fields,
    asof: str | None = None,
    append_filters: list[str] = [""],
    title: str = "",
) -> iter:
    features = {}
    with V1Meta(
        address=conf["url_server"],
        instance=conf["instance"],
        password=conf["token"],
        use_password_as_token=True,
    ) as v1:
        for it in its:
            present = False
            name_extract = f"{it}_{title}_{asof if asof else ''}"
            with open(conf["path_data"] + "date_export_pi.txt", "r") as date_export:
                lines = date_export.readlines()
            for line in lines:
                line = line.replace("\n", "")
                if asof and line.split(":")[0] == name_extract and line[-19:-9] >= asof:
                    present = True
                    break
            if present:
                with open(
                    f"{conf['path_data']}result_pi_{name_extract}.json",
                    "r",
                    encoding="utf-8",
                ) as fp:
                    ite = json.load(fp)
            else:
                ite = extracts_story_defect(
                    ver1=v1,
                    filters=[
                        f'Timebox.Name="{it}"{append_filter}'
                        for append_filter in append_filters
                    ],
                    fields=fields,
                    asof=asof,
                )
                if asof:
                    with open(
                        f"{conf['path_data']}result_pi_{name_extract}.json",
                        "w",
                        encoding="utf-8",
                    ) as fp:
                        json.dump(ite, fp)
                with open(conf["path_data"] + "date_export_pi.txt", "a") as date_export:
                    date_export.write(
                        f"{name_extract}: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
            if ite:
                for us in ite.values():
                    if us["Super.Number"] in features:
                        features[us["Super.Number"]]["story"][us["Number"]] = us
                    else:
                        features[us["Super.Number"]] = {
                            "Name": us["Super.Name"],
                            "story": {us["Number"]: us},
                            "status": us["Super.Status.Name"],
                        }
    return features


def analyse_goals_pi(conf, filter_goal):
    # pi répartition des tickets par itération avec leur objectif le lien vers la feature

    goals = extract_goals(
        conf=conf,
        filters=(filter_goal,),
        fields=[
            "Number",
            "Name",
            "PlannedBusinessValue",
            "Team.Name",
            "Workitems.SubsAndDown:PrimaryWorkitem.@Count",
            "Workitems.SubsAndDown.@Count",
        ],
    )
    return goals


def print_goals_html(project, goals_v1):
    conf = version_one_conf()["projects"][project]
    from version_one.versionone import tr_html, naming

    print(goals_v1)
    fields = [
        "Name",
        "PlannedBusinessValue",
        "Workitems.SubsAndDown:PrimaryWorkitem.@Count",
    ]
    tab = "<style>table.sam, .sam th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
    tab += "<style>.sam tr:nth-child(even){background-color: #F2F3F4}</style>"
    goals_page = (
        f"https://{conf['url_server']}/{conf['instance']}/Default.aspx?menu=GoalsPage"
    )
    tab += f'\n<h1><a href="{goals_page}">Goals</a></h1>'
    tab += '\n<table class="sam"><thead><tr><th>'
    tab += "</th><th>".join([naming[f] for f in fields])
    tab += "</th></tr></thead>\n"
    for line in tr_html(
        conf=conf,
        tickets=goals_v1.values(),
        fields=fields,
        link=True,
    ):
        tab += line[0]
    tab += "</table>"
    print(tab)


def goals_iterations(project, goals_v1, filter_team, exclude_goals_status):

    conf = version_one_conf()["projects"][project]
    filters = [f'Timebox.Name="{pi}"{filter_team}' for pi in conf["pi"].keys()]
    filters.append(
        # f'Timebox=""{filter_team};Scope.AssetState!="Closed";AssetState!="Closed";Status.Name!="Done";Status.Name!="Accepted"'
        f'Timebox=""{filter_team};Scope.AssetState!="Closed"'
    )
    goals_v1, goals = analyse_tickets_goals(
        conf=conf,
        goals_v1=goals_v1,
        filters=filters,
        exclude_goals_status=exclude_goals_status,
        fields=[
            "Number",
            "Name",
            "Status.Name",
            "AssetState",
            "Super.Number",
            "Super.Name",
            "SuperAndUp.Goals.Number",
            # "SuperAndUp.Dependancies.Number",
            "Dependencies.Number",
            "Dependencies.Name",
            "Dependants.Number",
            "Dependants.Name",
            "Timebox.Name",
            "Super.Dependencies.Number",
            "Super.Dependencies.Name",
            "Super.Dependants.Number",
            "Super.Dependants.Name",
            "Super.Super.Dependencies.Number",
            "Super.Super.Dependencies.Name",
            "Super.Super.Dependants.Number",
            "Super.Super.Dependants.Name",
        ],
    )
    return goals


def print_goals_pi_html(project, goals, goals_v1):
    conf = version_one_conf()["projects"][project]
    from version_one.versionone import naming

    fields = [
        "Number",
        "Name",
        "Super.Name",
        "Timebox.Name",
        # "PlannedBusinessValue",
        # "Workitems.SubsAndDown:PrimaryWorkitem.@Count",
    ]
    tab = "<style>table.sam, .sam th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
    tab += "<style>.sam tr:nth-child(even){background-color: #F2F3F4}</style>"
    goals_page = (
        f"https://{conf['url_server']}/{conf['instance']}/Default.aspx?menu=GoalsPage"
    )
    tab += f'\n<h1><a href="{goals_page}">Goals</a></h1>'
    tab += '\n<table class="sam"><thead><tr><th>'
    tab += "</th><th>".join([naming[f] for f in fields])
    tab += "</th></tr><thead>\n"
    for line in tr_goal_html(
        conf=conf,
        goals=goals,
        goals_v1=goals_v1,
        fields=fields,
        link=True,
    ):
        tab += line
    tab += "</table>"
    print(tab)
    return tab


def print_goals_pi_iteration_html(project, goals, goals_v1):
    conf = version_one_conf()["projects"][project]
    from version_one.versionone import tr_html, naming

    print(goals)
    fields = [
        "Number",
        "Name",
        "Super.Name",
        # "Timebox.Name",
        # "PlannedBusinessValue",
        # "Workitems.SubsAndDown:PrimaryWorkitem.@Count",
        "Dependencies",
        "Dependants",
    ]
    tab = "<style>table.sam, .sam th, .sam td{border: 1px solid black; border-collapse: collapse;padding: 3px;}</style>"
    tab += "<style>.sam tr:nth-child(even){background-color: #F2F3F4}</style>"
    goals_page = (
        f"https://{conf['url_server']}/{conf['instance']}/Default.aspx?menu=GoalsPage"
    )
    tab += f'\n<h1><a href="{goals_page}">Goals</a></h1>'
    for goal_id, goal in goals.items():
        tab += f'<details open><summary><b>{goals_v1[goal_id]["Name"] if goal_id in goals_v1 else goal_id}</b></summary>'
        for it_filter, it in goal["it"].items():
            timebox = (
                it_filter.split('Timebox.Name="')[-1].split('"')[0]
                if "Timebox.Name" in it_filter
                else "Backlog"
            )
            tab += f"\n<h3>{timebox}</h3>"
            tab += '\n<table class="sam"><thead><tr><th>'
            tab += "</th><th>".join([naming[f] for f in fields])
            tab += "</th></tr><thead>\n"
            for line in tr_html(
                conf=conf,
                # goals=it,
                # goals_v1=goals_v1,
                tickets=it["st"],
                fields=fields,
                link=True,
            ):
                tab += line[0]
            tab += "</table>"
        tab += "</details><br/>"
    print(tab)

    from HtmlClipboard import put_html

    put_html(tab, source=conf["url_server"])
    return tab


def tr_goal_html(conf, goals, goals_v1, fields, link: bool = True):
    for goal_id, goal in goals.items():
        nb_tickets = len(goal["st"])
        goal_url = f"https://{conf['url_server']}/{conf['instance']}/Goal.mvc/Summary?oidToken={goal_id}"
        tab = "<tr>"
        for i, ticket in enumerate(goal["st"]):
            tab += "<td"
            if i == 0:
                tab += f' rowspan="{nb_tickets}"><a href="{goal_url}">{goals_v1[goal_id]["Name"]}</td><td'
            tab += ">"
            if link:
                tab += "</td><td>".join([b_html(conf, c, ticket) for c in fields])
            else:
                tab += "</td><td>".join(
                    [escape(r(eval("ticket." + c, {"ticket": ticket}))) for c in fields]
                )
            tab += "</td></tr>\n"
        yield tab


def analyse_pi(project: str):
    goals_v1 = analyse_goals_pi(
        conf=version_one_conf()["projects"][project],
        filter_goal='Scope.Name="XXX";Team.Name="XXX"',
    )
    goals = goals_iterations(
        project="XXX",
        goals_v1=goals_v1,
        # filter_team=';Team.Name="XXX";Status.Name!="Cancelled / Descope"',
        filter_team=';Team.Name="XXX"',
        # exclude_goals_status=["Cancelled / Descope"],
        exclude_goals_status=None,
    )

    return print_goals_pi_iteration_html(project=project, goals=goals, goals_v1=goals_v1)


def features_pi(project: str):
    conf = version_one_conf()["projects"][project]
    filter_goal = ('Scope.Name="XXX";Team.Name="XXX"',)
    with V1Meta(
        address=conf["url_server"],
        instance=conf["instance"],
        password=conf["token"],
        use_password_as_token=True,
        # loglevel=logging.INFO,
    ) as v1:

        html_epic_pi = epic_html(
            conf=conf,
            filters=(filter_goal,),
            ver1=v1,
            # fields_epic=[
            #     "Number",
            #     "Name",
            #     # "PlannedBusinessValue",
            #     # "Team.Name",
            #     # "Workitems.SubsAndDown:PrimaryWorkitem.@Count",
            #     # "Workitems.SubsAndDown.@Count",
            # ],
        )
    # print(html_epic_pi)
    from HtmlClipboard import put_html

    put_html(html_epic_pi, source=conf["url_server"])
    return html_epic_pi


def analyse_tickets_goals(
    conf,
    goals_v1,
    filters,
    exclude_goals_status,
    fields=[
        "Status.Name",
        "AssetState",
        "SuperAndUp.Goals.Number",
        "SuperAndUp.Goals.Name",
    ],
):
    goals = {}
    import logging

    logger_analyse = logging.getLogger(__name__)
    logging.basicConfig(
        format="%(asctime)s %(message)s",
        encoding="utf-8",
        level=logging.INFO,
    )
    logger_analyse.setLevel(logging.INFO)
    with V1Meta(
        address=conf["url_server"],
        instance=conf["instance"],
        password=conf["token"],
        use_password_as_token=True,
        loglevel=logging.INFO,
    ) as v1:
        for filter_pi in filters:
            nb = 0
            logger_analyse.info("Filter %s", filter_pi)
            for key, st in extract_datas(
                s_filter=filter_pi,
                type_vone=v1.Story,
                fields=fields,
                exclude_status=exclude_goals_status,
            ):
                nb += 1
                # logger_analyse.info("Story %s", key)
                # break
                status = st["Status.Name"]
                if status in conf["status_done"] or (
                    st["AssetState"] == "128" and conf["closed_is_done"]
                ):
                    status = "Done"
                # elif status == "":
                else:
                    status = "To Do"
                if "Goals" not in st:
                    st["Goals"] = {
                        "None_Goal": {
                            "Name": "Without goal",
                            "Number": None,
                            "PlannedBusinessValue": 0,
                        }
                    }

                for key, goal in st["Goals"].items():
                    if key in goals_v1:
                        if key in goals:
                            goals[key]["st"].append(st)
                            goals[key]["total"] += 1
                            if status in goals[key]["status"]:
                                goals[key]["status"][status] += 1
                            else:
                                goals[key]["status"][status] = 1
                            if filter_pi in goals[key]["it"]:
                                if status in goals[key]["it"][filter_pi]["status"]:
                                    goals[key]["it"][filter_pi]["status"][status] += 1
                                else:
                                    goals[key]["it"][filter_pi]["status"][status] = 1
                            else:
                                goals[key]["it"][filter_pi] = {
                                    "status": {status: 1},
                                    "st": [],
                                }
                            if "total" not in goals[key]["it"][filter_pi]["status"]:
                                goals[key]["it"][filter_pi]["status"]["total"] = 1
                            else:
                                goals[key]["it"][filter_pi]["status"]["total"] += 1
                            goals[key]["it"][filter_pi]["st"].append(st)
                        else:
                            goals[key] = {
                                # "Number": goal["Number"],
                                # "Name": goal["Name"],
                                # "BV": goal["PlannedBusinessValue"],
                                # "Name": goals_v1[key]["Name"],
                                # "BV": goals_v1[key]["PlannedBusinessValue"],
                                "st": [st],
                                "it": {
                                    filter_pi: {
                                        "status": {status: 1, "total": 1},
                                        "st": [st],
                                    },
                                },
                                "status": {status: 1},
                                "total": 1,
                            }
                # logger_analyse.info("End Story %s", key)
            print(filter_pi, nb)
        remove_goals = []
        for goal_id, goal_v1 in goals_v1.items():
            if goal_id not in goals:
                remove_goals.append(goal_id)
        for remove_goal in remove_goals:
            goals_v1.pop(remove_goal)
    logger_analyse.info("End filter")
    print("--------------------")
    for goal_id, goal_v1 in goals_v1.items():
        goal = goals[goal_id]
        print(goal_v1["Name"], goal["status"])
        if goal_id == "None_Goal":
            print(goal["st"])
    print("--------------------")
    for goal_id, goal_v1 in goals_v1.items():
        goal = goals[goal_id]
        print(
            f'{goal_v1["Name"]} - {goal_v1["PlannedBusinessValue"]}BV',
            *[
                (
                    goal["it"][it]["status"]["Done"]
                    if it in goal["it"] and "Done" in goal["it"][it]["status"]
                    else 0
                )
                for it in filters
            ],
            goal["status"]["To Do"] if "To Do" in goal["status"] else 0,
            sep="\t",
        )
    print("****************************")
    for goal_id, goal_v1 in goals_v1.items():
        if goal_id in goals:
            goal = goals[goal_id]
            print(
                f'{goal_v1["Name"]} - {goal_v1["PlannedBusinessValue"]}BV',
                *[
                    (
                        goal["it"][it]["status"]["total"]
                        if it in goal["it"] and "total" in goal["it"][it]["status"]
                        else 0
                    )
                    for it in filters
                ],
                goal["status"]["To Do"] if "To Do" in goal["status"] else 0,
                sep="\t",
            )
    print("goals =", goals)

    logger_analyse.info("End")
    return goals_v1, goals


def graph_goals(
    project: str, filter_team: str, filter_goal: str, title: str, exclude_goals_status
):
    conf = version_one_conf()["projects"][project]
    # path_data = conf["path_data"]
    real = True

    filters = [f'Timebox.Name="{pi}"{filter_team}' for pi in conf["pi"].keys()]
    filters.append(
        f'Timebox=""{filter_team};Scope.AssetState!="Closed";AssetState!="Closed";Status.Name!="Done";Status.Name!="Accepted"'
    )
    if real:
        goals_v1 = extract_goals(
            conf=conf,
            filter_goal=filter_goal,
        )
        goals_v1, goals = analyse_tickets_goals(
            conf=conf,
            goals_v1=goals_v1,
            filters=filters,
            exclude_goals_status=exclude_goals_status,
        )
        # trouver les features sans tickets.
    else:
        goals = {}
        goals_v1 = {}

    # filters_label = {f'Timebox.Name="{pi}"{append_filter}': f"It {i}" for i, pi in enumerate(conf["pi"].keys())}
    # print(filters_label)
    datas = {}
    datas_todo = {}
    # for goal_id in list_goals:
    #     goal = goals[goal_id]
    for goal_id, goal_v1 in goals_v1.items():
        goal = goals[goal_id]
        label = f'{goal_v1["Name"]} - {goal_v1["PlannedBusinessValue"]}BV'
        datas[label] = [
            (
                goal["it"][it]["status"]["total"]
                if it in goal["it"] and "total" in goal["it"][it]["status"]
                else 0
            )
            for it in filters
        ]
        datas_todo[label] = [
            (
                goal["it"][it]["status"]["Done"]
                if it in goal["it"] and "Done" in goal["it"][it]["status"]
                else 0
            )
            for it in filters
        ]
        datas_todo[label].append(
            goal["status"]["To Do"] if "To Do" in goal["status"] else 0
        )
    colors = {
        "It 1": "#e8e7ed",
        "It 2": "#bcb7c9",
        "It 3": "#8f88a6",
        "It 4": "#625982",
        "It 5": "#4d4171",
        # "It 6": "#36295e",
        # "Backlog": "#999898",
        # "Todo": "#ff9900",
    }
    print(colors),
    print(datas)
    if len(conf["pi"].keys()) > 5:
        colors["It 6"] = "#36295e"
    colors["Backlog"] = "#999898"
    # BarHorizontal(title,
    #               datas=datas, labels=list(colors.keys()), colors=colors,
    #               ylabel_width=100,
    #               xlabel="Goal Repartition").build().copy_html().show()
    colors["Remaining"] = "#ff9900"
    BarHorizontal(
        title,
        datas=datas_todo,
        labels=list(colors.keys()),
        colors=colors,
        xlabel="Goal Progress - Complete & Remaining",
    ).build().copy_html().show()


if __name__ == "__main__":
    # Stretch: "0" -> false, Stretch: "1" -> true
    # graph_goals(
    #     project="XXX",
    #     filter_team=';Team.Name="XXX";Status.Name!="Cancelled / Descope"',
    #     filter_goal='Scope.Name="XXX";Team.Name="XXX";Stretch="0"',
    #     title="XXX goals",
    #     exclude_goals_status=["Cancelled / Descope"],
    # )

    graph_goals(
        project="XXX",
        filter_team=';Team.ID="Team:XXX"',
        filter_goal='Scope.Name="XXX";Team.ID="Team:XXX"',
        title="XXX goals",
        exclude_goals_status=None,
    )
