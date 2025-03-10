import json
from sm import jiraconf


def conf_boards(project):
    from atlassian.jiraSM import JiraSM

    data_conf = jiraconf()
    jira = JiraSM(project=project, **data_conf["projects"][project]).conn()._jira
    boards = jira.boards(projectKeyOrID=project)
    statuses = jira.statuses()
    status_jira = {s.id: s.name for s in statuses}
    for board in boards:
        print(board.id, board.name)
        c = jira._get_json(
            f"board/{board.id}/configuration",
            base=data_conf["projects"][project]["url_server"] + "rest/agile/1.0/{path}",
        )
        for column in c["columnConfig"]["columns"]:
            print(column["name"])
            for status in column["statuses"]:
                print("\t", status_jira[status["id"]])


def nb_status_overall(code):
    dataconf = jiraconf()
    with open(
        f"{dataconf["projects"][code]["path_data"]}YYYYMMDD{code}_.json",
        "r",
        encoding="utf-8",
    ) as fp:
        data = json.load(fp)
    # print(data)
    status_id = {}
    for d in data.values():
        for id, tickets in d.items():
            if tickets["status"] in status_id:
                if id not in status_id[tickets["status"]]:
                    status_id[tickets["status"]].append(id)
            else:
                status_id[tickets["status"]] = [id]
    for k, s in status_id.items():
        print(k, len(s))


if __name__ == "__main__":
    nb_status_overall("XXX")
    # TODO link board with analyse status used.
