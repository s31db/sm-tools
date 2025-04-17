import pandas as pd
import json
from charts.radar import Radar
from helpers.clipboard import send_to_clipboard_image
from charts.barcompare import Barcompare
from charts.barcomparecumul import BarcompareCumul
from charts.line import Line

criterias = [
    "Mission",
    "Pawns or players",
    "Teamwork",
    "Suitable process",
    "Delivering value",
    "Easy to release",
    "Speed",
    "Health of codebase",
    "Support",
    "Learning",
    "Fun!",
]
values_critere = ["green", "orange", "red"]


def test_local():

    date_shc = "202501"
    with open("squadhelathcheck.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)
    data[date_shc]["data"].pop("dates")
    df = pd.DataFrame(data[date_shc]["data"])
    file_path = f"tmp/radar_health_check_{date_shc}.png"
    Radar(title=data[date_shc]["title"]).build(df).save(file_path).show()

    send_to_clipboard_image(file_path)


def test_local_team():
    with open("squadhelathcheck.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)
    from time import sleep

    for team in ("TeamA",):
        team_data = {"title": team, "data": {"group": [], "color": []}}
        for key, values in data.items():
            if team in values["data"]["group"]:
                team_data["data"]["group"].append(key)
                team_data["data"]["color"].append("b")
                n = values["data"]["group"].index(team)
                for data_key, data_values in values["data"].items():
                    if data_key not in ("group", "color"):
                        if data_key in team_data["data"]:
                            team_data["data"][data_key].append(data_values[n])
                        else:
                            team_data["data"][data_key] = [data_values[n]]
        # print(team_data)
        df = pd.DataFrame(team_data["data"])
        file_path = "tmp/radar_health_check_{team}.png"
        # Radar(title=team_data["title"]).build(df).show()
        Radar(title=team_data["title"]).build(df).save(file_path)

        send_to_clipboard_image(file_path)
        print("ready", team, file_path)


def prepare_values(values, pos):

    for criteria in criterias:
        res = {
            "green": values[criteria][pos][0],
            "orange": values[criteria][pos][1],
            "red": values[criteria][pos][2],
        }
        # if criteria not in values:
        #     exit(-1)
        # if pos > len(values[criteria]):
        #     exit(-2)
        # val = (
        #     values[criteria][pos][0] * 4
        #     + values[criteria][pos][1] * 2
        #     + values[criteria][pos][2] * 1
        # )
        # yield criteria, (
        #     "vert"
        #     if val == 4
        #     else "orange" if val == 2 else "red" if val == 1 else "NOP"
        # )
        yield criteria, res


def test_dates_teams():
    with open("squadhelathcheck.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)
    teams = {}
    teams_sqh = {}
    titles = []
    for key, values in data.items():
        title = key
        titles.append(key)
        for i, group in enumerate(values["data"]["group"]):
            if group not in teams:
                teams[group] = [values["data"]["dates"][i]]
                teams_sqh[group] = {title: {}}
            else:
                teams[group].append(values["data"]["dates"][i])
                teams_sqh[group][title] = {}
            # print(title, i)
            for criteria, value in prepare_values(values["data"], i):
                # print(criteria, value)
                teams_sqh[group][title][criteria] = value
            # print(group, values["data"]["dates"][i])
    # print(teams)
    # titles
    print()
    # tab_sqh(teams_sqh, titles)

    # tab_sqh_critere_period(teams_sqh, titles)

    # by_periods(teams_sqh, titles)

    # by_criterias(teams_sqh, titles)

    # by_teams(teams_sqh, titles)

    # by_criterias_periods(teams_sqh, titles)

    # by_evolution(teams_sqh, titles)

    last_values(teams_sqh, titles)

    # for team in teams_sqh:


def tab_sqh(teams_sqh, titles):
    print("SQH", "Criterias", *titles, sep="\t")
    for team, values in teams_sqh.items():
        for criteria in criterias:
            print(team, criteria, sep="\t", end="\t")
            for title in titles:
                print(values[title][criteria] if title in values else "", end="\t")
            print()


def tab_sqh_critere_period(teams_sqh, titles):
    # sep = "\t"
    sep = " | "
    print("| ", end="")
    print("Criterias", *titles, "", sep=sep)
    print("| --------|---------|-------|--------|---------|-------|-------|")
    for criteria in criterias:
        print("| ", end="")
        print(criteria, sep=sep, end=sep)
        for title in titles:
            critere_period = {value_critere: 0 for value_critere in values_critere}
            for team, values in teams_sqh.items():
                if title in values:
                    for value_critere in values_critere:
                        critere_period[value_critere] += values[title][criteria][
                            value_critere
                        ]
            # https://emojipedia.org
            print(
                "🟢" * critere_period[values_critere[0]]
                + "🟠" * critere_period[values_critere[1]]
                + "🔴" * critere_period[values_critere[2]],
                # critere_period,
                end=sep,
            )
        print()


def by_periods(teams_sqh, titles):
    # group par period
    periods = {}
    for title in titles:
        periods[title] = {v: 0 for v in values_critere}
        for team, values in teams_sqh.items():
            if title in values:
                for v in values_critere:
                    for criteria in criterias:
                        periods[title][v] += values[title][criteria][v]
    print(periods)
    file_path = f"radar_health_check_periods.png"
    Barcompare(
        "SQH group par period", colors={v: v for v in values_critere}, legend=False
    ).nodes(periods).width_bar(0.25).build().save(file_path).show()
    send_to_clipboard_image(file_path)


def last_values(teams_sqh, titles):
    # last_values
    teams = {}
    for team, values in teams_sqh.items():
        # for value in values.values():
        #     teams[team] = value
        teams[team] = list(values.values())[-1]
    # print(teams)

    group = list(teams.keys())
    color = ["b", "c", "r", "g", "o", "p", "v", "y", "violet", "pink"][: len(group)]
    datas = {"group": group, "color": color}
    for criteria in criterias:
        datas[criteria] = [list(team[criteria].values()) for team in teams.values()]
    datas["group"] = list(teams.keys())
    # print(datas)
    df = pd.DataFrame(datas)
    file_path = f"tmp/radar_health_check_last_values.png"
    Radar(title="SQH last_values", figsize=(10, 11)).build(df).save(file_path)
    # send_to_clipboard_image(file_path)


def by_criterias(teams_sqh, titles):
    # group par critere
    criteres = {}
    for criteria in criterias:
        criteres[criteria] = {v: 0 for v in values_critere}
        for title in titles:
            for team, values in teams_sqh.items():
                if title in values:
                    for v in values_critere:
                        criteres[criteria][v] += values[title][criteria][v]
    print(criteres)
    file_path = f"tmp/radar_health_check_criteres.png"
    Barcompare(
        "SQH group par critères",
        colors={v: v for v in values_critere},
        legend=False,
        figsize=(18, 7),
    ).nodes(criteres).width_bar(0.25).build().save(file_path).show()
    send_to_clipboard_image(file_path)


def by_criterias_periods(teams_sqh, titles):
    # group par period
    criteria_periods = {}
    for criteria in criterias:
        criteria_periods[criteria] = {v: {} for v in values_critere}
        for title in titles:
            for team, values in teams_sqh.items():
                if title in values:
                    for v in values_critere:
                        if title in criteria_periods[criteria][v]:
                            criteria_periods[criteria][v][title] += values[title][
                                criteria
                            ][v]
                        else:
                            criteria_periods[criteria][v][title] = values[title][
                                criteria
                            ][v]
    # print(criteria_periods)
    criteria_periods_nodes = {}
    for key, criteria_period in criteria_periods.items():
        criteria_periods_nodes[key] = {}
        for k, value in criteria_period.items():
            criteria_periods_nodes[key][k] = [n for n in value.values()]
            # criteria_periods_nodes[key][k] = [n for n in value.values() if n != 0]
            # criteria_periods_nodes[key].append(value)
            # criteria_periods_nodes[key] += value
    print(criteria_periods_nodes)
    file_path = f"tmp/radar_health_check_criteria_periods.png"
    BarcompareCumul(
        "SQH group par criteria period",
        colors={f"{v}_{i}": v for v in values_critere for i in range(7)},
        legend=False,
        figsize=(18, 7),
    ).nodes(criteria_periods_nodes).width_bar(0.25).build().save(file_path).show()
    send_to_clipboard_image(file_path)


def by_teams(teams_sqh, titles):
    # group par equipe
    equipes = {}
    for team, values in teams_sqh.items():
        equipes[team] = {v: 0 for v in values_critere}
        for criteria in criterias:
            for title in titles:
                if title in values:
                    for v in values_critere:
                        equipes[team][v] += values[title][criteria][v]
    print(equipes)
    file_path = f"tmp/radar_health_check_teams.png"
    Barcompare(
        "SQH group par teams",
        colors={v: v for v in values_critere},
        legend=False,
        figsize=(18, 7),
    ).nodes(equipes).width_bar(0.25).build().save(file_path).show()
    send_to_clipboard_image(file_path)


def by_evolution(teams_sqh, titles):
    # group par equipe
    equipes = {}
    evolutions = {}
    for team, values in teams_sqh.items():
        equipes[team] = {v: None for v in criterias}
        # equipes[team] = {v: 10 * i for i, v in enumerate(criterias)}
        # for criteria in criterias:
        for i, criteria in enumerate(criterias):
            for title in titles:
                if title in values:
                    if title not in evolutions:
                        evolutions[title] = {}
                    val = (
                        values[title][criteria]["green"] * 4
                        + values[title][criteria]["orange"] * 2
                        + values[title][criteria]["red"] * 1
                    )
                    if equipes[team][criteria] is not None:
                        if criteria not in evolutions[title]:
                            evolutions[title][criteria] = (
                                1
                                if equipes[team][criteria] < val
                                else 1 if equipes[team][criteria] > val else 0
                            )
                        else:
                            evolutions[title][criteria] += (
                                1
                                if equipes[team][criteria] < val
                                else 1 if equipes[team][criteria] > val else 0
                            )
                    equipes[team][criteria] = val
    print(evolutions)
    evolutions_criteria = {criteria: [] for criteria in criterias}
    for key, ev in evolutions.items():
        for criteria in criterias:
            if criteria in ev:
                evolutions_criteria[criteria].append(ev[criteria])
    file_path = f"tmp/radar_health_check_evolution.png"
    Line(
        "SQH group par evolution",
        datas=evolutions_criteria,
        legend=True,
        xlabel="Quarter",
        ylabel_width=20,
        bar_label=True,
        figsize=(18, 7),
    ).build().save(file_path).show()
    send_to_clipboard_image(file_path)


# Example

# {
#   "202501": {
#     "title": "Squad Health Check 2025 01",
#     "link": "",
#     "data": {
#       "group": ["TeamA", "TeamB", "TeamC", "TeamD", "TeamE"],
#       "dates": ["05 Jan 2025", "07 Jan 2025", "09 Jan 2025", "11 Jan 2025", "10 Jan 2025"],
#       "dates_int": ["2025-01-05", "2025-01-07", "2025-02-09", "2025-01-11", "2025-01-10"],
#       "color": ["b", "r", "g", "p", "v"],
#       "Mission": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Pawns or players": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Teamwork": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Suitable process": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Delivering value": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Easy to release": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Speed": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Health of codebase": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Support": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Learning": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#       "Fun!": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]],
#     }
#   },
