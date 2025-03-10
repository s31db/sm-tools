import duckdb
from sm import jiraconf
from helpers.prepare_date_sprint import add_dates
from atlassian.jiraSM import JiraSM
from datetime import date, timedelta

CONF_TABLES = {
    "sprint": {
        "primary_keys": {"fields": {"sprint": "int"}},
        "fields": {
            "start_date": "string",
            "end_date": "string",
            "name": "string",
            "state": "string",
            "goal": "string",
        },
    }
}


def get_super(v, i: int) -> list[str]:
    fields = ["super." * i + "super."]
    if "super" in v:
        fields += get_super(v["super"], i + 1)
    return fields


def project_fields(project: str) -> list[str]:
    dataconf = jiraconf()
    conf = dataconf["projects"][project]
    conf_fields = conf["fields"]
    super_fields = get_super(conf["super"], 0)
    fields = [f for f in conf_fields.keys()] + [
        field + n
        for field in super_fields
        for n in (
            "name",
            "status",
        )
    ]
    fields += ["super", "super.super"]
    return fields


def epic_fields(project: str) -> list[str]:
    dataconf = jiraconf()
    conf_fields = dataconf["projects"][project]["epic_fields"]
    fields = [f for f in conf_fields.keys()]
    return fields


def prepare(path: str, project: str):
    with duckdb.connect(path) as con:
        for table in (project, project + "_tempo"):
            con.sql(f"Drop TABLE IF EXISTS {table}")
            req = f'CREATE TABLE IF NOT EXISTS {table} (day string, ticket string, "{'" string, "'.join(project_fields(project=project))}" string, PRIMARY KEY (day, ticket))'
            req = req.replace('"estimate" string', '"estimate" float')
            con.sql(req)
        # con.table(project).show()

        table = project + "_epic"
        con.sql(f"Drop TABLE IF EXISTS {table}")
        req = f'CREATE TABLE IF NOT EXISTS {table} (day string, ticket string, "{'" string, "'.join(epic_fields(project=project))}" string, PRIMARY KEY (day, ticket))'
        con.sql(req)
        # con.table(f"{table}").show()

        table = project + "_sprint"
        con.sql(f"Drop TABLE IF EXISTS {table}")
        req = f"CREATE TABLE IF NOT EXISTS {table} (sprint int, {", ".join([f"{key} {typ}" for key, typ in CONF_TABLES["sprint"]["fields"].items()])}, PRIMARY KEY (sprint))"
        con.sql(req)

        table = project + "_suivi"
        con.sql(f"Drop TABLE IF EXISTS {table}")
        req = f"CREATE TABLE IF NOT EXISTS {table} (typ string, day string, PRIMARY KEY (typ, day))"
        con.sql(req)
        pass


def insert_from_file(path: str, project: str):
    data_conf = jiraconf()
    path_file = f"{data_conf['projects'][project]['path_data']}20250213{project}_.json"
    fields = project_fields(project)
    import json

    with duckdb.connect(path) as con:
        con.sql(f"truncate {project}_tempo")
        with open(path_file, "r", encoding="utf-8") as fp:
            # dict de date de ticket avec update ou fields
            datas_sm: dict[
                str, dict[str, dict[str, None | str | int | dict[str, str]]]
            ] = json.load(fp)
        prepare_insert = f"VALUES ($values)"
        for day, tickets in datas_sm.items():
            for ticket, values in tickets.items():
                vals = [day, ticket]
                vals += [str(values[f]).replace("'", "''") for f in fields]
                # FIXME prepare_statement
                p = prepare_insert.replace("$values", f"'{"', '".join(vals)}'")
                con.sql(f"INSERT INTO {project} {p} ON CONFLICT DO NOTHING")


def verify(path: str, table_name: str):
    with duckdb.connect(path) as con:
        con.table(table_name).order("day, ticket").show()
        print(con.table(table_name).count("day").fetchdf())


def jira(
    project: str,
    start_date: str,
):

    data_conf = jiraconf()
    d = add_dates(
        date.fromisoformat(start_date),
        frm="%Y-%m-%d",
        limit_date=None,
        end_date=date.today(),
    )
    jirasm = JiraSM(project=project, **data_conf["projects"][project]).conn()
    return data_conf, d, jirasm


def insert_or_update(
    path: str, project: str, start_date: str | None = None, updated: bool = False
):
    fields = project_fields(project)
    with duckdb.connect(path) as con:
        data_conf, d, jirasm, start_date = prepare_conf(
            con=con, project=project, start_date=start_date, typ="ticket"
        )
        datas_sm, file = jirasm.epic_ticket(
            list(d),
            filtre=f"and updated >= '{start_date}'" if updated else "",
            asof=None,
            file=False,
        )
        con.sql(f"truncate {project}_tempo")
        prepare_insert = f"VALUES ($values)"
        for day, tickets in datas_sm.items():
            for ticket, values in tickets.items():
                vals = [day, ticket]
                vals += [str(values[f]).replace("'", "''") for f in fields]
                # FIXME prepare_statement
                p = prepare_insert.replace("$values", f"'{"', '".join(vals)}'")
                con.sql(f"INSERT INTO {project}_tempo {p} ON CONFLICT DO NOTHING")
        update_fields = [f'"{field}" = "{field}"' for field in fields]
        con.sql(
            f"INSERT INTO {project} select * from {project}_tempo ON CONFLICT (day, ticket) DO UPDATE set {", ".join(update_fields)}"
        )
        con.sql(
            f"INSERT INTO {project}_suivi (typ, day) values ('ticket', '{date.today().strftime("%Y-%m-%d hh:mm:ss")}') ON CONFLICT DO NOTHING"
        )


def prepare_conf(con, project, start_date, typ):
    if start_date is None:
        start_date = (
            con.table(f"{project}_suivi")
            .filter(f"typ = '{typ}'")
            .last("day")
            .fetchone()[0]
        )
    if start_date is None:
        start_date = f'{(date.today() - timedelta(weeks=2 * 52)).strftime("%Y-%m-%d")}'
    data_conf, d, jirasm = jira(project=project, start_date=start_date)
    print(typ, start_date)
    return data_conf, d, jirasm, start_date


def epic(path: str, project: str, start_date: str | None = None, updated: bool = False):
    fields = epic_fields(project)

    with duckdb.connect(path) as con:
        data_conf, d, jirasm, start_date = prepare_conf(
            con=con, project=project, start_date=start_date, typ="epic"
        )
        datas_sm = jirasm.epics(
            dates=list(d),
            filtre=f"and updated >= '{start_date}'" if updated else "",
            now=date.today().strftime("%Y-%m-%d"),
        )
        prepare_insert = f"VALUES ($values)"
        update_fields = [f'"{field}" = "{field}"' for field in fields]
        for day, tickets in datas_sm.items():
            for ticket, values in tickets.items():
                vals = [day, ticket]
                vals += [str(values[f]).replace("'", "''") for f in fields]
                # FIXME prepare_statement
                p = prepare_insert.replace("$values", f"'{"', '".join(vals)}'")
                con.sql(
                    f"INSERT INTO {project}_epic {p} ON CONFLICT (day, ticket) DO UPDATE set {", ".join(update_fields)}"
                )
        con.sql(
            f"INSERT INTO {project}_suivi (typ, day) values ('epic', '{date.today().strftime("%Y-%m-%d hh:mm:ss")}') ON CONFLICT DO NOTHING"
        )


def sprint(path: str, project: str, start_date: str | None = None):
    fields = CONF_TABLES["sprint"]["fields"].keys()

    with duckdb.connect(path) as con:
        data_conf, d, jirasm, start_date = prepare_conf(
            con=con, project=project, start_date=start_date, typ="sprint"
        )
        datas_sm = jirasm.sprints(asof=None, file=False)

        prepare_insert = f"VALUES ($values)"
        update_fields = [f'"{field}" = "{field}"' for field in fields]
        for ticket, values in datas_sm.items():
            vals = [
                str(values[f]).replace("'", "''") if f in values else "" for f in fields
            ]
            # FIXME prepare_statement
            p = prepare_insert.replace("$values", f"{ticket}, '{"', '".join(vals)}'")
            con.sql(
                f"INSERT INTO {project}_sprint {p} ON CONFLICT (sprint) DO UPDATE set {", ".join(update_fields)}"
            )
        con.sql(
            f"INSERT INTO {project}_suivi (typ, day) values ('sprint', '{date.today().strftime("%Y-%m-%d hh:mm:ss")}') ON CONFLICT DO NOTHING"
        )
        con.table(f"{project}_sprint").show()


def new_project(project: str):
    data_conf = jiraconf()["projects"][project]
    start_date = data_conf["start"]
    print(start_date)
    db_path = data_conf["path_data"] + project + ".db"

    prepare(path=db_path, project=project)
    insert_or_update(
        path=db_path, project=project, start_date=start_date, updated=False
    )
    sprint(path=db_path, project=project, start_date=start_date)
    epic(path=db_path, project=project, start_date=start_date, updated=False)
    # verify(path=db_path, table_name=project)


def update_project(project: str):
    data_conf = jiraconf()["projects"][project]
    db_path = data_conf["path_data"] + project + ".db"
    insert_or_update(path=db_path, project=project)
    sprint(path=db_path, project=project)
    epic(path=db_path, project=project, updated=True)
    # verify(path=db_path, table_name=project)


def verify_project(project: str):
    data_conf = jiraconf()["projects"][project]
    db_path = data_conf["path_data"] + project + ".db"
    # print(db_path)
    with duckdb.connect(db_path) as con:
        print("Ticket")
        con.table(project).order("day, ticket").show()
        print(con.table(project).count("day").fetchdf())
        print(
            con.sql(
                f'select "type", count(distinct ticket) as nb_ticket from {project} group by 1 order by 1'
            ).fetchdf()
        )
        # print(
        #     con.sql(
        #         f"select day, count(1) from {project} group by day order by day"
        #     ).fetchdf()
        # )

        print("Epic")
        # con.table(project + "_epic").order("day, ticket").show()
        print(con.table(project + "_epic").count("day").fetchdf())
        print(
            con.sql(
                f"select count(distinct ticket) as nb_epics from {project}_epic"
            ).fetchdf()
        )

        print("Sprint")
        # con.table(project + "_sprint").order("start_date, state").show()
        print(con.table(project + "_sprint").count("name").fetchdf())

        print("Suivi")
        con.table(project + "_suivi").order("day, typ").show()
        # print(con.table(project + "_suivi").count("day").fetchdf())


def tickets(project: str):
    data_conf = jiraconf()["projects"][project]
    db_path = data_conf["path_data"] + project + ".db"
    t = {}
    with duckdb.connect(db_path) as con:
        result = con.sql(f"select * from {project}")
        columns = result.columns[2:]
        for day_ticket in result.fetchall():
            # print(day_ticket)
            if day_ticket[0] not in t:
                t[day_ticket[0]] = {}
            t[day_ticket[0]][day_ticket[1]] = {
                c: (
                    float(day_ticket[i + 2])
                    if c == "estimate"
                    and day_ticket[i + 2]
                    and day_ticket[i + 2] != "None"
                    else day_ticket[i + 2] if day_ticket[i + 2] != "None" else None
                )
                for i, c in enumerate(columns)
            }
            t[day_ticket[0]][day_ticket[1]]["super.type"] = "Sprint"
    return t


if __name__ == "__main__":
    # new_project(project="XXX")  # Be careful re-create tables
    # update_project(project="XXX")
    # verify_project(project="XXX")
    tickets(project="XXX")
    pass
# TODO séparer les épics et les sprints
# ou regarder les changements de nom de sprint
# et les changements dans les epics du projet et du projet connexe
