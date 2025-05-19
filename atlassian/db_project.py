import duckdb
from duckdb.duckdb import DuckDBPyConnection

from sm import jiraconf
from helpers.prepare_date_sprint import add_dates
from atlassian.jiraSM import JiraSM
from datetime import date, timedelta
from charts.barcompare import Barcompare

SERIAL_TICKET_KEY = "day, ticket"

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


def project_fields(project: str, path: str) -> list[str]:
    dataconf = jiraconf(path=path)
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


def epic_fields(project: str, path: str) -> list[str]:
    dataconf = jiraconf(path=path)
    conf_fields = dataconf["projects"][project]["epic_fields"]
    fields = [f for f in conf_fields.keys()]
    return fields


def status_done(project: str, path: str) -> list[str]:
    dataconf = jiraconf(path=path)
    return dataconf["projects"][project]["status_done"]


def status_started(project: str, path: str) -> list[str]:
    dataconf = jiraconf(path=path)
    return dataconf["projects"][project]["status_started"]


def prepare_values(fields, vals, values):
    for f in fields:
        if f in values:
            vals.append(values[f])
        else:
            vals.append(None)


def jira(project: str, start_date: str, path: str):

    data_conf = jiraconf(path=path)
    d = add_dates(
        date.fromisoformat(start_date[:10]),
        frm="%Y-%m-%d",
        limit_date=None,
        end_date=date.today(),
    )
    jirasm = JiraSM(project=project, **data_conf["projects"][project]).conn()
    return data_conf, d, jirasm


def re_update(projects: list[str], start_date: str):
    for project in projects:
        db_project = DBProject(project=project)
        db_project.execute(
            query=f'delete from {project}_epic where "day" >= ?',
            parameters=[start_date],
        )
        db_project.execute(
            query=f'delete from {project} where "day" >= ?',
            parameters=[start_date],
        )
        db_project.update_project(start_date=start_date)


class DBProject:
    _con: DuckDBPyConnection
    project: str
    path: str
    path_conf: str | None

    def __init__(
        self, project: str, path: str | None = None, path_conf: str | None = None
    ) -> None:
        self.project = project
        if project and path is None:
            data_conf = jiraconf(path=path_conf)["projects"][project]
            path = data_conf["path_data"] + project + ".db"
        self.path = path
        self._con = duckdb.connect(path)
        self.path_conf = path_conf

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._con is not None:
            self._con.close()

    def create_tempo(self):
        if self.path != ":memory:":
            self._con.sql(f"SET temp_directory = ?", params=[self.path])
        table = self.project + "_tempo"
        self._con.sql(f"Drop TABLE IF EXISTS {table}")
        req = (
            f"CREATE TEMP TABLE IF NOT EXISTS {table} (day string, ticket string, "
            f'"{'" string, "'.join(project_fields(project=self.project, path=self.path_conf))}" string, '
            f"PRIMARY KEY ({SERIAL_TICKET_KEY}))"
        )
        req = req.replace('"estimate" string', '"estimate" float')
        self._con.sql(req)

    def prepare(self):
        # with duckdb.connect(path) as con:
        table = self.project
        self._con.sql(f"Drop TABLE IF EXISTS {table}")
        req = (
            f"CREATE TABLE IF NOT EXISTS {table} (day string, ticket string, "
            f'"{'" string, "'.join(project_fields(project=self.project, path=self.path_conf))}" string, '
            f"PRIMARY KEY ({SERIAL_TICKET_KEY}))"
        )
        req = req.replace('"estimate" string', '"estimate" float')
        self._con.sql(req)
        # con.table(project).show()

        table = self.project + "_epic"
        self._con.sql(f"Drop TABLE IF EXISTS {table}")
        req = (
            f"CREATE TABLE IF NOT EXISTS {table} (day string, ticket string, "
            f'"{'" string, "'.join(epic_fields(project=self.project, path=self.path_conf))}" string, PRIMARY KEY ({SERIAL_TICKET_KEY}))'
        )
        self._con.sql(req)
        # con.table(f"{table}").show()

        table = self.project + "_sprint"
        self._con.sql(f"Drop TABLE IF EXISTS {table}")
        req = (
            f"CREATE TABLE IF NOT EXISTS {table} (sprint int, "
            f"{", ".join([f"{key} {typ}" for key, typ in CONF_TABLES["sprint"]["fields"].items()])}, "
            f"PRIMARY KEY (sprint))"
        )
        self._con.sql(req)

        table = self.project + "_suivi"
        self._con.sql(f"Drop TABLE IF EXISTS {table}")
        req = f"CREATE TABLE IF NOT EXISTS {table} (typ string, day string, PRIMARY KEY (typ, day))"
        self._con.sql(req)

        self._con.sql("Drop TABLE IF EXISTS days")
        req = "CREATE TABLE IF NOT EXISTS days (day string primary key, id int);"
        self._con.sql(req)

    def insert_from_file(
        self, export_date: str | None = None, path_file: str | None = None
    ):
        self.create_tempo()
        data_conf = jiraconf(self.path_conf)
        if not path_file:
            path_file = f"{data_conf['projects'][self.project]['path_data']}{export_date}{self.project}_.json"
        fields = project_fields(project=self.project, path=self.path_conf)
        import json

        self._con.sql(f"truncate {self.project}_tempo")
        with open(path_file, "r", encoding="utf-8") as fp:
            # dict de date de ticket avec update ou fields
            datas_sm: dict[
                str, dict[str, dict[str, None | str | int | dict[str, str]]]
            ] = json.load(fp)
        prepare_insert = f"VALUES ($values)"
        for day, tickets in datas_sm.items():
            for ticket, values in tickets.items():
                vals = [day, ticket]
                vals += [
                    str(values[f]).replace("'", "''") if f in values else ""
                    for f in fields
                ]
                # FIXME prepare_statement
                p = prepare_insert.replace("$values", f"'{"', '".join(vals)}'")
                self._con.sql(f"INSERT INTO {self.project} {p} ON CONFLICT DO NOTHING")

    def verify(self, table_name: str):
        self._con.table(table_name).order(SERIAL_TICKET_KEY).show()
        print(self._con.table(table_name).count("day").fetchdf())

    def validate_project_data(self, table_name: str):
        self._con.table(table_name).order(SERIAL_TICKET_KEY).show()
        print(self._con.table(table_name).count("day").fetchdf())
        # check consistency

    def insert_or_update(
        self,
        start_date: str | None = None,
        updated: bool = False,
        filtre: str = "",
    ):
        # TODO séparer les épics et les sprints / regarder les changements de nom de sprint et les changements dans les epics du projet et du projet connexe
        fields = project_fields(project=self.project, path=self.path_conf)
        data_conf, d, jirasm, start_date = self.prepare_conf(
            start_date=start_date, typ="ticket"
        )
        self.create_tempo()
        days = list(d)
        datas_sm, file = jirasm.epic_ticket(
            days,
            filtre=f"{filtre} " + (f"and updated >= '{start_date}'" if updated else ""),
            asof=None,
            file=False,
        )
        prepare_insert = f"VALUES ({",".join(["?" for _ in range(len(fields)+2)])})"
        for day, day_tickets in datas_sm.items():
            for ticket, values in day_tickets.items():
                vals = [day, ticket]
                prepare_values(fields, vals, values)
                self._con.execute(
                    f"INSERT INTO {self.project}_tempo {prepare_insert} ON CONFLICT DO NOTHING",
                    vals,
                )
        if updated:
            for day in days:
                self._con.execute(
                    f"INSERT INTO {self.project}_tempo select ?, ticket,"
                    f"{", ".join([f'"{field}"' for field in fields if field != "day"])} "
                    f'from {self.project} where "day" = (select max("day") from {self.project})  and created[0:10] < "day" ON CONFLICT DO NOTHING',
                    [day],
                )
        update_fields = [f'"{field}" = EXCLUDED."{field}"' for field in fields]
        self._con.execute(
            f"INSERT INTO {self.project} select * from {self.project}_tempo ON CONFLICT ({SERIAL_TICKET_KEY}) DO UPDATE set {", ".join(update_fields)}"
        )
        self._con.execute(
            f"INSERT INTO {self.project}_suivi (typ, day) values ('ticket', ?) ON CONFLICT DO NOTHING",
            [date.today().strftime("%Y-%m-%d")],
        )
        self._con.sql('truncate "days"')
        self._con.sql(
            f'insert into "days" select "day", row_number() OVER () from (select "day" from {self.project} group by 1 order by 1)'
        )

    def prepare_conf(self, start_date, typ):
        if start_date is None:
            start_date = (
                self._con.table(f"{self.project}_suivi")
                .filter(f"typ = '{typ}'")
                .last("day")
                .fetchone()[0]
            )
        if start_date is None:
            start_date = (
                f'{(date.today() - timedelta(weeks=2 * 52)).strftime("%Y-%m-%d")}'
            )
        data_conf, d, jirasm = jira(
            project=self.project, start_date=start_date, path=self.path_conf
        )
        print(self.project, typ, start_date)
        return data_conf, d, jirasm, start_date

    def epic(
        self,
        start_date: str | None = None,
        updated: bool = False,
    ):
        fields = epic_fields(self.project, path=self.path_conf)

        data_conf, d, jirasm, start_date = self.prepare_conf(
            start_date=start_date, typ="epic"
        )
        days = list(d)
        datas_sm = jirasm.epics(
            dates=days,
            filtre=f"and updated >= '{start_date}'" if updated else "",
            now=date.today().strftime("%Y-%m-%d"),
        )
        prepare_insert = f"VALUES ({",".join(["?" for _ in range(len(fields) + 2)])})"
        update_fields = [f'"{field}" = EXCLUDED."{field}"' for field in fields]

        if updated:
            last_date = self._con.table(f"{self.project}_epic").max("day").fetchone()[0]
            for day in days:
                self._con.execute(
                    f"INSERT INTO {self.project}_epic select ?, ticket,"
                    f"{", ".join([f'"{field}"' for field in fields if field != "day"])} "
                    f'from {self.project}_epic where "day" = ? and created[0:10] < "day" ON CONFLICT DO NOTHING',
                    [day, last_date],
                )
        for day, tickets in datas_sm.items():
            for ticket, values in tickets.items():
                vals = [day, ticket]
                prepare_values(fields, vals, values)
                self._con.execute(
                    f"INSERT INTO {self.project}_epic {prepare_insert} ON CONFLICT ({SERIAL_TICKET_KEY}) "
                    f"DO UPDATE set {", ".join(update_fields)}",
                    vals,
                )
        self._con.execute(
            f"INSERT INTO {self.project}_suivi (typ, day) values ('epic', ?) ON CONFLICT DO NOTHING",
            [date.today().strftime("%Y-%m-%d")],
        )

    def sprint(self, start_date: str | None = None):
        fields = CONF_TABLES["sprint"]["fields"].keys()

        data_conf, d, jirasm, start_date = self.prepare_conf(
            start_date=start_date, typ="sprint"
        )
        datas_sm = jirasm.sprints(asof=None, file=False)

        prepare_insert = f"VALUES ({",".join(["?" for _ in range(len(fields) + 1)])})"
        update_fields = [f'"{field}" = EXCLUDED."{field}"' for field in fields]
        for ticket, values in datas_sm.items():
            vals = [str(ticket)]
            prepare_values(fields, vals, values)
            self._con.execute(
                f"INSERT INTO {self.project}_sprint {prepare_insert} ON CONFLICT (sprint) DO UPDATE set {", ".join(update_fields)}",
                vals,
            )
        self._con.execute(
            f"INSERT INTO {self.project}_suivi (typ, day) values ('sprint', ?) ON CONFLICT DO NOTHING",
            [date.today().strftime("%Y-%m-%d")],
        )

    def new_project(self, filtre: str = ""):
        data_conf = jiraconf()["projects"][self.project]
        start_date = data_conf["start"]
        print(self.project, start_date)

        self.prepare()
        self.insert_or_update(
            start_date=start_date,
            updated=False,
            filtre=filtre,
        )
        self.sprint(start_date=start_date)
        self.epic(start_date=start_date, updated=False)

    def update_project(self, start_date: str | None = None, filtre: str = ""):
        self.insert_or_update(
            updated=True,
            start_date=start_date,
            filtre=filtre,
        )
        self.sprint()
        self.epic(updated=True, start_date=start_date)
        # self.verify(table_name=project)

    def verify_project(self):
        print("Ticket")
        self._con.table(self.project).order(SERIAL_TICKET_KEY).show()
        print(self._con.table(self.project).count("day").fetchdf())
        print(
            self._con.sql(
                f'select "type", count(distinct ticket) as nb_ticket from {self.project} group by 1 order by 1'
            ).fetchdf()
        )
        # print(
        #     self.con.sql(
        #         f"select day, count(1) from {project} group by day order by day"
        #     ).fetchdf()
        # )
        print("Epic")
        # self.con.table(project + "_epic").order(DAY_TICKET).show()
        print(self._con.table(self.project + "_epic").count("day").fetchdf())
        print(
            self._con.sql(
                f"select count(distinct ticket) as nb_epics from {self.project}_epic"
            ).fetchdf()
        )
        print("Sprint")
        # self.con.table(project + "_sprint").order("start_date, state").show()
        print(self._con.table(self.project + "_sprint").count("name").fetchdf())
        print("Suivi")
        self._con.table(self.project + "_suivi").order("day, typ").show()
        # print(self.con.table(project + "_suivi").count("day").fetchdf())

    def tickets(self, project: str, filtre_db: str | None = None):
        t = {}
        req = (
            f"select * from {project} a where (status is null or status <> 'Canceled')"
        )
        if filtre_db:
            req += f" and {filtre_db}"
        # print(req)
        result = self._con.sql(req)
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

    def execute(self, query: str, parameters=None):
        res = self._con.execute(query, parameters)
        print(res.fetchdf())

    def analyse_estimate(self, day: str):
        status_done_project = status_done(self.project, self.path_conf)
        status_started_project = status_started(self.project, self.path_conf)
        sql = (
            "select assignee, estimate, quantile_cont(lead_time, 0.7), avg(lead_time) as avg_lead_time, min(lead_time) "
            "as min_lead_time, max(lead_time) as max_lead_time, quantile_cont(cycle_time, 0.7), avg(cycle_time) as avg_cycle_time, count(1) as nb from ("
            'select assignee, estimate, (select id from "days" where "day" = done) - (select id from "days" '
            'where "day" = created) as lead_time, (select id from "days" '
            'where "day" = done) - (select id from "days" where "day" = start_date) as cycle_time from ('
            f'select assignee, estimate, created[0:10] created, (select "day" from {self.project} B where a.ticket = b.ticket and '
            f"b.status in ('{status_started_project}') "
            f' order by b."day" limit 1) as start_date, (select "day" from {self.project} B where a.ticket = b.ticket and '
            f"b.status in ('{status_done_project}') order by b.\"day\" limit 1) as done, "
            f"from {self.project} a where \"day\" = '2025-03-14' and "
            f"status in ('{status_done_project}))) group by 1,2 order by 1,2 desc;"
        )
        self._con.sql(sql, params=[day]).show(
            max_width=500000, null_value="", max_rows=10000
        )

    def sprints(self):
        d = []
        datas_sprint = (
            self._con.table(f"{self.project}_sprint")
            .filter(f"state in ('closed', 'active')")
            .select("name", "start_date", "end_date")
            .order("start_date desc")
        )
        for s in datas_sprint.fetchall():
            d.append(
                {
                    "name": s[0],
                    "start_date": s[1],
                    "end_date": s[2],
                }
            )
        return d

    def cycle_time(self, day, min_ticket) -> Barcompare:
        # strftime(done, '%Y-%m') by_month
        # done - created as lead_time
        status_done_project = "','".join(status_done(self.project, self.path_conf))
        status_started_project = "','".join(
            status_started(self.project, self.path_conf)
        )
        sql_data = (
            "select year(done) year_done, quarter(done) quarter_done, "
            f'(select estimate from {self.project} c where c.ticket=i.ticket and c."day" = start_date) estimate, '
            # "estimate, "
            "done - start_date as cycle_time, ticket "
            "from (select  estimate, CAST(created as DATE) created, ticket, "
            f'CAST((select "day" from {self.project} B where a.ticket = b.ticket '
            f"and b.status in ('{status_started_project}') "
            f'order by b."day" limit 1) as DATE) as start_date, '
            f'CAST((select "day" from {self.project} B where a.ticket = b.ticket '
            f"and b.status in ('{status_done_project}') "
            'order by b."day" limit 1) as DATE) as done '
            f'from {self.project} a where "day" = ? and '
            f"a.status != 'Canceled' and status in ('{status_done_project}') "
            "and \"super.name\" != 'Backlog') as i"
        )
        sql = (
            "select "
            "year_done, quarter_done, estimate, min(cycle_time) as min_cycle_time, avg(cycle_time) as avg_cycle_time, "
            f"quantile_cont(cycle_time, 0.7), max(cycle_time) as max_cycle_time, count(1) as nb from ({sql_data}) "
            f"where estimate is not null group by 1,2,3 having count(1) > {min_ticket} order by 3 desc, 1, 2;"
        )
        d = {}
        print(
            "\t".join(("year_done", "quarter_done", "estimate", "cycle_time", "ticket"))
        )
        for s in self._con.sql(
            sql_data + " order by 3 desc, 1, 2;", params=[day]
        ).fetchall():
            print("\t".join([str(d) for d in s]))
        for s in self._con.sql(sql, params=[day]).fetchall():
            estimate = 0 if s[2] is None else s[2]
            key = f"{str(s[0])[2:]}-{s[1]}#{estimate}"
            d[key] = {
                # "min_cycle_time": s[3],
                "avg_cycle_time": s[4],
                "70 per centile": s[5],
                # "max_cycle_time": s[6],
                "nb": s[7],
            }
        print(d)
        barcompare = (
            Barcompare(f"Cycle times {self.project}", figsize=(16, 5))
            .nodes(d)
            .width_bar(0.20)
            .build()
        )
        return barcompare


def test_init():
    with DBProject(
        path=":memory:", project="Example", path_conf="../example/config_example.ini"
    ) as db_project:
        db_project.prepare()
        db_project.insert_from_file(path_file="../example/example.json")
        db_project.verify_project()
        assert len(db_project.cycle_time("2022-09-04", 0).img64()[0]) == 23200
    pass
