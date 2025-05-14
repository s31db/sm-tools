from atlassian.jiraSM import JiraSM
import statistics
from decimal import Decimal
import math


def to_hour(second: int | None, minus: int | None = None):
    if second and minus:
        return second - minus / 3600
    elif second:
        return second / 3600
    elif minus:
        return minus / -3600
    return None


def assign(jira: JiraSM):
    tasks = {}
    for task in jira.search(
        jira._filter_project() + 'AND status in ("To Do", "In Progress") '
        # 'AND issuetype in (Bug, Sub-task) '
        # 'AND assignee = currentUser() ' +
        "AND resolution = Unresolved ORDER BY updated DESC",
        fields="summary, status, assignee, aggregatetimeoriginalestimate, aggregatetimespent",
    ):
        tasks[task.key] = {
            "summary": task.fields.summary,
            "link": jira.link_browse(task.key),
            "status": task.fields.status.name,
            "assignee": str(task.fields.assignee),
            "restant": to_hour(
                task.fields.aggregatetimeoriginalestimate,
                task.fields.aggregatetimespent,
            ),
        }
        print(task.self, jira.link_browse(task.key))
        print(
            task.fields.summary,
            task.fields.status,
            task.fields.assignee,
            to_hour(task.fields.aggregatetimespent),
            "/",
            to_hour(task.fields.aggregatetimeoriginalestimate),
            to_hour(
                task.fields.aggregatetimeoriginalestimate,
                task.fields.aggregatetimespent,
            ),
        )
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(tasks)
    # print(tasks)


def analyse(jira: JiraSM):
    # issue = jira.issue('XX-Number')
    # print(issue.fields.project.key)
    # print(issue.fields.issuetype.name)
    # print(issue.fields.reporter.displayName)

    # jql_str = self._filter_project() + 'AND sprint = "XXX" AND issuetype =  Sub-task ORDER BY Rank ASC'
    jql_str = (
        jira._filter_project()
        + 'AND sprint = "XXX" AND issuetype =  Story ORDER BY Rank ASC'
    )
    sousestimer = 0
    sousestimerl = []
    parfait = 0
    surestimer = 0
    autre = 0
    for task in jira.search(jql_str=jql_str, max_results=10000):
        if (
            task.fields.aggregatetimespent
            and task.fields.aggregatetimeoriginalestimate
            and task.fields.aggregatetimespent
            > task.fields.aggregatetimeoriginalestimate
        ):
            print(task.self, jira.link_browse(task.key))
            print(
                task.fields.summary,
                task.fields.status,
                task.fields.assignee,
                to_hour(task.fields.aggregatetimespent),
                "/",
                to_hour(task.fields.aggregatetimeoriginalestimate),
            )
            sousestimer += 1
            sousestimerl.append(
                to_hour(
                    task.fields.aggregatetimespent
                    - task.fields.aggregatetimeoriginalestimate
                )
            )
        elif (
            task.fields.aggregatetimespent
            and task.fields.aggregatetimeoriginalestimate
            and task.fields.aggregatetimespent
            == task.fields.aggregatetimeoriginalestimate
        ):
            parfait += 1
        elif (
            task.fields.aggregatetimespent
            and task.fields.aggregatetimeoriginalestimate
            and task.fields.aggregatetimespent
            < task.fields.aggregatetimeoriginalestimate
        ):
            surestimer += 1
        else:
            # print(task.self, self.link_browse(task.key))
            # print(task.fields.summary, task.fields.status, task.fields.assignee,
            #       to_hour(task.fields.aggregatetimespent),
            #       '/', to_hour(task.fields.aggregatetimeoriginalestimate))
            autre += 1

    print(
        "Total",
        math.fsum(sousestimerl),
        "Median",
        statistics.median(map(Decimal, sousestimerl)),
        "Mean",
        statistics.mean(map(Decimal, sousestimerl)),
    )
    print(
        "sousestimer",
        sousestimer,
        "parfait",
        parfait,
        "surestimer",
        surestimer,
        "autre",
        autre,
    )
