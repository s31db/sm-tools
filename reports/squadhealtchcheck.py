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


def sqh(file, date_shc) -> Radar:

    with open(file, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    data[date_shc]["data"].pop("dates")
    data[date_shc]["data"].pop("dates_int")
    df = pd.DataFrame(data[date_shc]["data"])
    radar = Radar(title=data[date_shc]["title"]).build(df)
    return radar


def sqh_team(file, teams) -> dict[str, Radar]:
    with open(file, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    radars: dict[str, Radar] = {}
    for team in teams:
        team_data = {"title": team, "data": {"group": [], "color": []}}
        for key, values in data.items():
            if team in values["data"]["group"]:
                team_data["data"]["group"].append(key)
                team_data["data"]["color"].append("b")
                n = values["data"]["group"].index(team)
                for data_key, data_values in values["data"].items():
                    if data_key not in ("group", "color", "dates", "dates_int"):
                        if data_key in team_data["data"]:
                            team_data["data"][data_key].append(data_values[n])
                        else:
                            team_data["data"][data_key] = [data_values[n]]
        df = pd.DataFrame(team_data["data"])
        radar = Radar(title=team_data["title"]).build(df)
        radars[team] = radar
    return radars


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


def prepare_dates_teams(file):
    with open(file, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    teams = {}
    teams_sqh = {}
    titles = []
    for key, values in data.items():
        title = key
        titles.append(key)
        for i, group in enumerate(values["data"]["group"]):
            # if group not in ("TeamA",):  # filter Teams
            #     continue
            if group not in teams:
                teams[group] = [values["data"]["dates"][i]]
                teams_sqh[group] = {title: {}}
            else:
                teams[group].append(values["data"]["dates"][i])
                teams_sqh[group][title] = {}
            for criteria, value in prepare_values(values["data"], i):
                teams_sqh[group][title][criteria] = value
    return teams_sqh, titles


def tab_sqh(file):
    teams_sqh, titles = prepare_dates_teams(file)
    print("SQH", "Criterias", *titles, sep="\t")
    for team, values in teams_sqh.items():
        for criteria in criterias:
            print(team, criteria, sep="\t", end="\t")
            for title in titles:
                print(values[title][criteria] if title in values else "", end="\t")
            print()


def tab_sqh_critere_period(file):
    teams_sqh, titles = prepare_dates_teams(file)
    # sep = "\t"
    sep = "|"
    print(sep * 2, end="")
    print("Criterias", *titles, "", sep=sep * 2)
    # print("| --------|---------|-------|--------|---------|-------|-------|")
    for criteria in criterias:
        print("||", end="")
        print(criteria, end=sep)
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
                + "🔴" * critere_period[values_critere[2]]
                + " ",
                # critere_period,
                end=sep,
            )
        print()


def by_periods(file) -> Barcompare:
    teams_sqh, titles = prepare_dates_teams(file)
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
    barcompare = (
        Barcompare(
            "SQH group par period", colors={v: v for v in values_critere}, legend=False
        )
        .nodes(periods)
        .width_bar(0.25)
        .build()
    )
    return barcompare


def last_values(file) -> Radar:
    teams_sqh, titles = prepare_dates_teams(file)
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
    df = pd.DataFrame(datas)
    radar = Radar(title="SQH last_values", figsize=(10, 11)).build(df)
    return radar


def by_criterias(file) -> Barcompare:
    teams_sqh, titles = prepare_dates_teams(file)
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
    barcompare = (
        Barcompare(
            "SQH group par critères",
            colors={v: v for v in values_critere},
            legend=False,
            figsize=(18, 7),
        )
        .nodes(criteres)
        .width_bar(0.25)
        .build()
    )
    return barcompare


def by_criterias_periods(file) -> BarcompareCumul:
    teams_sqh, titles = prepare_dates_teams(file)
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
    barcompare_cumul = (
        BarcompareCumul(
            "SQH group par criteria period",
            colors={f"{v}_{i}": v for v in values_critere for i in range(7)},
            legend=False,
            figsize=(18, 7),
        )
        .nodes(criteria_periods_nodes)
        .width_bar(0.25)
        .build()
    )
    return barcompare_cumul


def by_teams(file) -> Barcompare:
    teams_sqh, titles = prepare_dates_teams(file)
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
    barcompare = (
        Barcompare(
            "SQH group par teams",
            colors={v: v for v in values_critere},
            legend=False,
            figsize=(18, 7),
        )
        .nodes(equipes)
        .width_bar(0.25)
        .build()
    )


def by_evolution(file) -> Line:
    teams_sqh, titles = prepare_dates_teams(file)
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
    # print(evolutions)
    evolutions_criteria = {criteria: [] for criteria in criterias}
    for key, ev in evolutions.items():
        for criteria in criterias:
            if criteria in ev:
                evolutions_criteria[criteria].append(ev[criteria])
    line = Line(
        "SQH group par evolution",
        datas=evolutions_criteria,
        legend=True,
        xlabel="Quarter",
        ylabel_width=20,
        bar_label=True,
        figsize=(18, 7),
    ).build()
    return line


FILE_TEST = "../example/squadhealthcheck.json"


def test_sqh():
    date_shc = "202501"
    file_path = f"tmp/radar_health_check_{date_shc}.png"
    radar = sqh(FILE_TEST, date_shc=date_shc)
    # radar.save(file_path).show()
    # send_to_clipboard_image(file_path)


def test_sqh_team():
    radars = sqh_team(FILE_TEST, teams=("TeamA",))
    for team, radar in radars.items():
        file_path = f"tmp/radar_health_check_{team}.png"
        # radar.save(file_path)
        # send_to_clipboard_image(file_path)
        # print("ready", team, file_path)


def test_tab_sqh():
    tab_sqh(FILE_TEST)


def test_tab_sqh_critere_period():
    tab_sqh_critere_period(FILE_TEST)


def test_by_periods():
    barcompare = by_periods(FILE_TEST)
    # file_path = f"radar_health_check_periods.png"
    # barcompare.save(file_path).show()
    # send_to_clipboard_image(file_path)


def test_by_criterias():
    barcompare = by_criterias(FILE_TEST)
    # file_path = f"tmp/radar_health_check_criteres.png"
    # barcompare.save(file_path).show()
    # send_to_clipboard_image(file_path)


def test_by_teams():
    barcompare = by_teams(FILE_TEST)
    # file_path = f"tmp/radar_health_check_teams.png"
    # barcompare.save(file_path).show()
    # send_to_clipboard_image(file_path)


def test_by_criterias_periods():
    barcompare_cumul = by_criterias_periods(FILE_TEST)
    # file_path = f"tmp/radar_health_check_criteria_periods.png"
    # barcompare_cumul.save(file_path).show()
    # send_to_clipboard_image(file_path)


def test_by_evolution():
    line = by_evolution(FILE_TEST)
    # file_path = f"tmp/radar_health_check_evolution.png"
    # line.save(file_path).show()
    # send_to_clipboard_image(file_path)


def test_last_values():
    radar = last_values(FILE_TEST)
    # file_path = f"tmp/radar_health_check_last_values.png"
    # radar.save(file_path)
    # send_to_clipboard_image(file_path)
