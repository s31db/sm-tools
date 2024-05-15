from typing import List, Tuple
import matplotlib.pyplot as plt
from version_one.program_increment import stories_pi
from version_one.versionone import extracts, get_fields
from helpers.prepare_date_sprint import sprint_dates
from datetime import datetime, timedelta
from charts.treemap import Treemap

DEFAULT_ESTIMATE = 1.11


def not_present(a, nivxs, i, max_super: int) -> bool:
    for j in range(i, max_super):
        if a in nivxs[j]:
            return False
    return True


def build_super(v, title, i, max_super: int) -> str:
    value = ""
    for j in range(max_super - i - 1, -1, -1):
        if "super." * j + "super" in v:
            value += v["super." * j + "super"]
            if j > 0:
                value += "/"
    if value == "":
        value = title
    return value


def build_id(v, i, a, max_super: int) -> str:
    value = ""
    for j in range(max_super - i - 1, -1, -1):
        if "super." * j + "super" in v:
            value += v["super." * j + "super"] + "/"
    return value + a


def prepare_pi_portfolio(
    conf,
    title: str,
    i_pi: iter = None,
    asof: str = None,
    append_filters: List[str] = None,
) -> List:
    max_super = conf["max_super"]
    if asof:
        title = f"{title} {asof}"
    fields = get_fields(max_super)
    closed_is_done = conf["closed_is_done"]

    fs_now = {}
    if i_pi:
        fields_now = ["AssetState", "Number", "Status.Name"]
        if asof:
            for epic_detail in stories_pi(
                conf=conf,
                its=i_pi,
                fields=fields_now,
                asof=asof,
                append_filters=append_filters,
                title="now " + title,
            ).values():
                for key, value in epic_detail["story"].items():
                    fs_now[key] = value
            for epic_detail in stories_pi(
                conf=conf,
                its=i_pi,
                fields=fields_now,
                asof=asof,
                append_filters=[a + ';IsDeleted="True"' for a in append_filters],
                title="now_deleted " + title,
            ).values():
                for key, value in epic_detail["story"].items():
                    fs_now[key] = value
        present = {}
        for it in i_pi:
            present[it] = False
        with open(conf["path_data"] + "date_export_pi.txt", "r") as date_export:
            lines = date_export.readlines()
        for line in lines:
            line = line.replace("\n", "")
            for it in i_pi:
                if (
                    asof
                    and line.split(":")[0] == it + "_" + title + asof
                    and line[-19:-9] >= asof
                ):
                    present[it] = True
                    break
        fs = stories_pi(
            conf=conf,
            its=i_pi,
            fields=fields,
            asof=asof,
            append_filters=append_filters,
            title=title,
        )
    else:
        fs = extracts(
            conf=conf,
            fields=fields,
            asof=asof,
            filters=append_filters,
            title=title,
        )

    to_delete = []
    if asof:
        for epic_detail in fs.values():
            for key, value in epic_detail["story"].items():
                if key in fs_now:
                    value["Status.Name"] = fs_now[key]["Status.Name"]
                    if fs_now[key]["AssetState"] == "255":
                        to_delete.append([epic_detail, key])
        for key, value in to_delete:
            epic_detail["story"].pop(key)
    sum_total = 0
    sum_total_done = 0
    no_estimate = conf["no_estimate"]
    for key, epic_detail in fs.items():
        if key == "":
            continue
        epic_detail["total"] = sum(
            (
                [
                    (
                        1
                        if no_estimate
                        else (
                            float(story["Estimate"])
                            if "Estimate" in story
                            and story["Estimate"] != ""
                            and story["Estimate"] != 0
                            else DEFAULT_ESTIMATE
                        )
                    )
                    for story in epic_detail["story"].values()
                ]
            )
        )
    sum_total += epic_detail["total"]
    if epic_detail["total"] > 0:
        epic_detail["total_done"] = sum(
            [
                (
                    0
                    if not story["Status.Name"] == "Done"
                    or (closed_is_done and story["AssetState"] == "128")
                    else (
                        1
                        if no_estimate
                        else (
                            float(story["Estimate"])
                            if "Estimate" in story
                            and story["Estimate"] != ""
                            and story["Estimate"] != "0"
                            else DEFAULT_ESTIMATE
                        )
                    )
                )
                for story in epic_detail["story"].values()
            ]
        )
        sum_total_done += epic_detail["total_done"]
    if sum_total != 0:
        print(asof, sum_total_done, sum_total, sum_total_done * 100 / sum_total)

    nivxs = {"id": {}}
    for i in range(max_super):
        nivxs[i] = {}

    for key, epic_detail in fs.items():
        for story in epic_detail["story"].values():
            for i in range(2, max_super):
                label_super = "Super." * i
                if label_super + "Number" in story:
                    niv_id = story[label_super + "Number"]
                    nivxs["id"][i] = niv_id
                    if niv_id:
                        if niv_id not in nivxs[i]:
                            nivxs[i][niv_id] = {
                                "total": 0,
                                "total_done": 0,
                                "Name": story[label_super + "Name"],
                            }
                        nivxs[i][niv_id]["total"] += epic_detail["total"]
                        if "total_done" in epic_detail:
                            nivxs[i][niv_id]["total_done"] += epic_detail["total_done"]
                        epic_detail["super." * (i - 2) + "super"] = niv_id
                        for j in range(2, i):
                            # Add super.super inverse of actual level to build tree ids
                            nivxs[j][nivxs["id"][j]][
                                "super." * (i - j - 1) + "super"
                            ] = niv_id
            # First is sufficient to take parent
            break
    for key, values in nivxs[2].items():
        if key in fs:
            values["total"] += fs[key]["total"]
            values["total_done"] += fs[key]["total_done"]
    for i in range(3, max_super):
        for key, values in nivxs[i].items():
            if key in nivxs[i - 1]:
                values["total"] += nivxs[i - 1][key]["total"]
                values["total_done"] += nivxs[i - 1][key]["total_done"]

    conf_colors = conf["colors"]
    status_pos = {}
    for i, status in enumerate(conf_colors):
        status_pos[status] = i

    names = [title]
    for i in range(max_super - 1, 1, -1):
        names += [
            niv["Name"]
            + " "
            + (
                (str(int(niv["total_done"] * 100 / niv["total"])) + "%")
                if niv["total"] > 0
                else ""
            )
            for a, niv in nivxs[i].items()
            if not_present(a, nivxs, i + 1, max_super)
        ]

    names += [
        v["Name"]
        + (
            " " + str(int(v["total_done"] * 100 / v["total"])) + "%"
            if "total_done" in v
            else ""
        )
        for a, v in fs.items()
        if v["Name"] != "" and not_present(a, nivxs, 1, max_super)
    ]

    parents = [""]
    for i in range(max_super - 1, 1, -1):
        parents += [
            build_super(v, title, i, max_super)
            for a, v in nivxs[i].items()
            if not_present(a, nivxs, i + 1, max_super)
        ]
    parents += [
        build_super(v, title, 1, max_super)
        for a, v in fs.items()
        if v["Name"] != "" and not_present(a, nivxs, 1, max_super)
    ]

    custom_data = [""]
    for i in range(max_super - 1, 1, -1):
        custom_data += [
            "" for a in nivxs[i].keys() if not_present(a, nivxs, i + 1, max_super)
        ]
    custom_data += [
        ""
        for a, v in fs.items()
        if v["Name"] != "" and not_present(a, nivxs, 1, max_super)
    ]
    custom_link = [a for a in custom_data]
    custom_team = [a for a in custom_data]
    custom_data_statues = [a for a in custom_data]
    custom_data_ite = [a for a in custom_data]

    values = [0]
    for i in range(max_super - 1, 1, -1):
        values += [
            0 for a in nivxs[i].keys() if not_present(a, nivxs, i + 1, max_super)
        ]
    values += [
        0
        for a, v in fs.items()
        if v["Name"] != "" and not_present(a, nivxs, 1, max_super)
    ]

    colors = {"": "Grey"}

    ids = [""]
    for i in range(max_super - 1, 1, -1):
        ids += [
            build_id(v, i, a, max_super)
            for a, v in nivxs[i].items()
            if not_present(a, nivxs, i + 1, max_super)
        ]
    ids += [
        build_id(v, 1, a, max_super)
        for a, v in fs.items()
        if v["Name"] != "" and not_present(a, nivxs, 1, max_super)
    ]
    for i in range(max_super - 1, 1, -1):
        colorize(colors, nivxs[i], i, max_super)
    colorize(colors, fs, 0, max_super)

    for key, epic_detail in fs.items():
        if key == "":
            key = title
        epics = epic_detail["story"]
        epics_sorted = {
            k: v
            for k, v in sorted(
                epics.items(), key=lambda item: status_pos[item[1]["Status.Name"]]
            )
        }
        for s, story in epics_sorted.items():
            names.append(story["Number"])
            parents_story = key
            id_story = key + "/" + s
            for i in range(2, max_super):
                super_number = "Super." * i + "Number"
                if super_number in story and story[super_number]:
                    parents_story = story[super_number] + "/" + parents_story
                    id_story = story[super_number] + "/" + id_story
            parents.append(parents_story)
            value = (
                1
                if no_estimate
                else (
                    float(story["Estimate"])
                    if "Estimate" in story and story["Estimate"] != ""
                    else DEFAULT_ESTIMATE
                )
            )
            values.append(value)
            custom_data.append(story["Name"].strip())
            if "idref" in story:
                st = "story" if s[0] == "S" else "defect"
                custom_linked = f"{st}.mvc/Summary?oidToken={story['idref']}"
            else:
                custom_linked = ""
            custom_link.append(custom_linked)
            custom_data_statues.append(story["Status.Name"])
            custom_data_ite.append(story["Timebox.Name"])
            custom_team.append(story["Team.Name"])
            ids.append(id_story)
            colors[id_story] = (
                conf_colors["Asset_Closed"]
                if closed_is_done
                and story["AssetState"] == "128"
                and story["Status.Name"] != "Done"
                else conf_colors[story["Status.Name"]]
            )

    return (
        names,
        values,
        parents,
        ids,
        colors,
        custom_data,
        custom_data_statues,
        custom_data_ite,
        custom_link,
        custom_team,
    )


def treemap_pi_portfolio(
    conf,
    title: str,
    i_pi: iter = None,
    show: bool = True,
    sav: bool = False,
    img: bool = False,
    asof: str | None = None,
    append_filters: List[str] = [""],
) -> Tuple[Treemap, str]:
    (
        names,
        values,
        parents,
        ids,
        colors,
        custom_data,
        custom_data_statues,
        custom_data_ite,
        custom_link,
        custom_team,
    ) = prepare_pi_portfolio(
        conf=conf, title=title, i_pi=i_pi, asof=asof, append_filters=append_filters
    )

    treemap = Treemap(title=title, global_parent="Portfolio", **conf)
    treemap._text_template = (
        f'<a href="https://{conf["url_server"]}/{conf["instance"]}/'
    )
    treemap._text_template += (
        '%{customdata[0]}" style="color:inherit">%{label}</a><br>%{customdata[1]}<br>'
    )
    treemap._text_template += (
        "%{customdata[2]}<br>%{customdata[3]}<br>%{customdata[4]}<br>"
    )

    treemap.figure(
        colors=colors,
        custom_data=[
            custom_link,
            custom_data,
            custom_data_statues,
            custom_data_ite,
            custom_team,
        ],
        ids=ids,
        names=names,
        parents=parents,
        values=values,
    )

    return treemap, export(asof, treemap, img, sav, show, title)


def export(asof, treemap, img, sav, show, title):
    if show:
        treemap.show()
    if asof:
        now = asof
    else:
        now = datetime.today().strftime("%Y%m%d%H%M")
    title_date = title + "_" + now
    treemap._title = title_date
    if sav:
        treemap.html()
    if img:
        treemap.png()
    return title_date


def colorize(colors, niv, i, max_super: int):
    total = {}
    for k, v in niv.items():
        if k == "":
            continue
        key = build_id(v, i, k, max_super)
        total[key] = v["total"]
    total_sorted = {k: v for k, v in sorted(total.items(), key=lambda item: item[1])}
    n = 0
    nb_prec = -1
    sm = plt.cm.ScalarMappable(cmap=plt.cm.cool)
    vmax = len(set(total_sorted.values()))
    sm.set_clim(vmin=0, vmax=vmax)
    for key, nb in total_sorted.items():
        if key == "":
            continue
        c = sm.to_rgba(vmax - n)
        colors[key] = "#%02x%02x%02x" % (
            int(c[0] * 100),
            int(c[1] * 100),
            int(c[2] * 100),
        )
        if nb_prec != nb:
            n += 1
        nb_prec = nb


def anime(conf, title, filters):
    filenames = []
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y%m%d")
    treemap = None
    for sprint_id, sprint_val in conf["sprints"].items():
        for asof_d in sprint_dates(
            start_date=sprint_val["start_date"], weeks=sprint_val["weeks"]
        ):
            if asof_d <= tomorrow:
                treemap, filename = treemap_pi_portfolio(
                    conf=conf,
                    title=title,
                    asof=asof_d,
                    append_filters=filters,
                    i_pi=conf["pi"].keys(),
                    show=False,
                    sav=False,
                    img=True,
                )
                filenames.append(conf["path_export"] + filename + ".png")
    if treemap:
        treemap.title(title + "_animation")
        treemap.sequence(filenames=filenames, duration=1000, loop=None)
