from jira import JIRA
import logging
import statistics
from decimal import Decimal
import math
from config import config
import json
from datetime import datetime
from configparser import ConfigParser
from operator import attrgetter

SUPER = 'super'
SUPER_NAME = 'super.name'
SUPER_STATUS = 'super.status'
SUPER_SUPER = 'super.super'
SUPER_SUPER_NAME = 'super.super.name'
SUPER_SUPER_STATUS = 'super.super.status'


def to_hour(second: int, minus: int = None):
    if second and minus:
        return second - minus / 3600
    elif second:
        return second / 3600
    elif minus:
        return minus / -3600


def add_super(date: str, ticket_super_super: str, epics_date: str, epics_no_rights: list[str],
              ticket_super: str, ticket: str, us_date: str, _super: dict):
    if ticket_super_super is not None and ticket_super_super not in epics_date[date]:
        epics_no_rights[ticket_super_super] = ticket.key
    if SUPER in _super:
        if ticket_super_super is None or ticket_super_super not in epics_date[date]:
            super_super_id = '-2'
            us_date[date][ticket.key][SUPER_SUPER_STATUS] = ''
            us_date[date][ticket.key][SUPER_SUPER_NAME] = _super[SUPER]['default_name']
        else:
            super_super_id = ticket_super_super
            us_date[date][ticket.key][SUPER_SUPER_STATUS] = epics_date[date][ticket_super_super]['status']
            us_date[date][ticket.key][SUPER_SUPER_NAME] = epics_date[date][ticket_super_super]['name']
        us_date[date][ticket.key][SUPER_SUPER] = super_super_id
    if ticket_super is None:
        if SUPER in _super:
            us_date[date][ticket.key][SUPER] = '-1' + '_' + super_super_id
        else:
            us_date[date][ticket.key][SUPER] = '-1'
        us_date[date][ticket.key][SUPER_NAME] = _super['default_name']
        us_date[date][ticket.key][SUPER_STATUS] = ''
        us_date[date][ticket.key]['super.type'] = ''
    else:
        # us_date[date][ticket.key][SUPER] = ticket_super[-1].split('[id=')[-1].split(',rapidViewId=')[0] + \
        #                                      '_' + super_super_id
        # us_date[date][ticket.key][SUPER_NAME] = ticket_super[-1].split(',name=')[-1].split(',startDate=')[0]
        # us_date[date][ticket.key][SUPER_STATUS] = ''
        us_date[date][ticket.key][SUPER] = ticket_super
        if ticket_super in epics_date[date]:
            us_date[date][ticket.key][SUPER_STATUS] = epics_date[date][ticket_super]['status']
            us_date[date][ticket.key][SUPER_NAME] = epics_date[date][ticket_super]['name']
            us_date[date][ticket.key]['super.type'] = epics_date[date][ticket_super]['type']


def change_super(changelog_date, changelog_item, created, dates, epics_date, ticket, us_date, _super):
    if changelog_item.field == _super['field_changelog']:
        changelog_item_from = getattr(changelog_item, 'from')
        if changelog_item_from is not None:
            name = changelog_item.fromString
            if ', ' in changelog_item_from:
                changelog_item_from = changelog_item_from.split(', ')[-1]
                # XXX not perfect for name
                name = name.split(', ')[-1]
        field = SUPER
        for date in dates:
            if created <= date < changelog_date <= us_date[date][ticket.key]['update'][SUPER]:
                if SUPER_SUPER in us_date[date][ticket.key]:
                    super_super_id = us_date[date][ticket.key][SUPER_SUPER]
                else:
                    super_super_id = ''
                if changelog_item_from is None:
                    us_date[date][ticket.key][SUPER] = '-1' + '_' + super_super_id
                    us_date[date][ticket.key][SUPER_NAME] = 'Backlog'
                    us_date[date][ticket.key][SUPER_STATUS] = ''
                else:
                    us_date[date][ticket.key][SUPER] = changelog_item_from + '_' + super_super_id
                    us_date[date][ticket.key][SUPER_NAME] = name
                    # TODO improve name and status with list sprints by date.
                    us_date[date][ticket.key][SUPER_STATUS] = ''
                us_date[date][ticket.key]['update'][field] = changelog_date
    elif changelog_item.field == _super[SUPER]['field_changelog']:
        super_super_id = getattr(changelog_item, 'from')
        field = SUPER_SUPER
        for date in dates:
            if created <= date < changelog_date <= us_date[date][ticket.key]['update'][SUPER_SUPER]:
                if super_super_id is None or super_super_id not in epics_date[date]:
                    us_date[date][ticket.key][SUPER_SUPER] = '-2'
                    us_date[date][ticket.key][SUPER] = us_date[date][ticket.key][SUPER].split(
                        '_')[0] + '_-2'
                    us_date[date][ticket.key][SUPER_SUPER_STATUS] = ''
                    us_date[date][ticket.key][SUPER_SUPER_STATUS] = 'No Epic'
                else:
                    us_date[date][ticket.key][SUPER_SUPER] = super_super_id
                    us_date[date][ticket.key][SUPER] = us_date[date][ticket.key][SUPER].split(
                        '_')[0] + '_' + super_super_id
                    us_date[date][ticket.key][SUPER_SUPER_STATUS] = epics_date[date][super_super_id]['status']
                    us_date[date][ticket.key][SUPER_SUPER_STATUS] = epics_date[date][super_super_id]['name']
                us_date[date][ticket.key]['update'][field] = changelog_date


class JiraSM:
    conf: ConfigParser = config()
    _jira: JIRA
    _project: str
    _url_server: str
    _fields_change_ignored: list[str]
    _type_base: list[str]
    _path_data: str
    _epic_fields: dict
    _fields: dict
    _super: dict
    _board_id: int

    def __init__(self, **kwargs):
        # self._project = self.conf.JIRA.project
        # self._fields_change_ignored = self.conf.JIRA.fields_change_ignored.split(', ')
        # self._url_server = self.conf.JIRA.url_server
        for key, value in kwargs.items():
            setattr(self, '_' + key, value)

    def conn(self):
        if 'atlassian.net' in self._url_server:
            self._jira = JIRA(server=self._url_server, basic_auth=(self._user, self._token_auth))
        else:
            self._jira = JIRA(server=self._url_server, token_auth=self._token_auth)
        return self

    def search(self, jql_str: str, maxResults: int = 10000, fields: str = None, expand: str = None, trc: bool = False):
        if trc:
            print(jql_str)
        return self._jira.search_issues(jql_str=jql_str, maxResults=maxResults, fields=fields, expand=expand)
        # results = self._jira.search_issues(jql_str=jql_str, maxResults=maxResults, fields=fields, expand=expand)
        # for result in results:
        #     yield result
        # Limit by Server Jira the maxResults
        # start_at = results.maxResults
        # while results.total > start_at:
        #     for result in self._jira.search_issues(jql_str=jql_str, maxResults=results.maxResults,
        #                                            fields=fields, expand=expand,  startAt=start_at):
        #         yield result
        #     start_at += results.maxResults

    def analyse(self):
        # issue = jira.issue('XX-Number')
        # print(issue.fields.project.key)
        # print(issue.fields.issuetype.name)
        # print(issue.fields.reporter.displayName)

        # jql_str = 'project = ' + self._project + ' AND sprint = "XXX" AND issuetype =  Sub-task ORDER BY Rank ASC'
        jql_str = 'project = ' + self._project + ' AND sprint = "XXX" AND issuetype =  Story ORDER BY Rank ASC'
        sousestimer = 0
        sousestimerl = []
        parfait = 0
        surestimer = 0
        autre = 0
        for task in self.search(jql_str=jql_str, maxResults=10000):
            if task.fields.aggregatetimespent and task.fields.aggregatetimeoriginalestimate \
                    and task.fields.aggregatetimespent > task.fields.aggregatetimeoriginalestimate:
                print(task.self, self._url_server + "/browse/"+task.key)
                print(task.fields.summary, task.fields.status, task.fields.assignee,
                      to_hour(task.fields.aggregatetimespent),
                      '/', to_hour(task.fields.aggregatetimeoriginalestimate))
                sousestimer += 1
                sousestimerl.append(to_hour(task.fields.aggregatetimespent - task.fields.aggregatetimeoriginalestimate))
            elif task.fields.aggregatetimespent and task.fields.aggregatetimeoriginalestimate \
                    and task.fields.aggregatetimespent == task.fields.aggregatetimeoriginalestimate:
                parfait += 1
            elif task.fields.aggregatetimespent and task.fields.aggregatetimeoriginalestimate \
                    and task.fields.aggregatetimespent < task.fields.aggregatetimeoriginalestimate:
                surestimer += 1
            else:
                # print(task.self, url_server + "/browse/" + task.key)
                # print(task.fields.summary, task.fields.status, task.fields.assignee,
                #       to_hour(task.fields.aggregatetimespent),
                #       '/', to_hour(task.fields.aggregatetimeoriginalestimate))
                autre += 1

        print('Total', math.fsum(sousestimerl), 'Median', statistics.median(map(Decimal, sousestimerl)),
              'Mean', statistics.mean(map(Decimal, sousestimerl)))
        print('sousestimer', sousestimer, 'parfait', parfait, 'surestimer', surestimer, 'autre', autre)

    def assign(self):
        tasks = {}
        for task in self.search(
                           'project = ' + self._project + '  '
                           'AND status in ("To Do", "In Progress") '
                           # 'AND issuetype in (Bug, Sub-task) '
                           # 'AND assignee = currentUser() ' +
                           'AND resolution = Unresolved ORDER BY updated DESC',
                           fields='summary, status, assignee, aggregatetimeoriginalestimate, aggregatetimespent'):
            tasks[task.key] = {'summary': task.fields.summary,
                               'link': self._url_server + "/browse/" + task.key,
                               'status': task.fields.status.name,
                               'assignee': str(task.fields.assignee),
                               'restant': to_hour(task.fields.aggregatetimeoriginalestimate,
                                                  task.fields.aggregatetimespent)}
            print(task.self, self._url_server + "/browse/" + task.key)
            print(task.fields.summary, task.fields.status, task.fields.assignee,
                  to_hour(task.fields.aggregatetimespent), '/', to_hour(task.fields.aggregatetimeoriginalestimate),
                  to_hour(task.fields.aggregatetimeoriginalestimate, task.fields.aggregatetimespent))
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(tasks)
        # print(tasks)

    def remaining(self):
        fields = 'summary, assignee, aggregatetimeestimate, status'
        filters = {'remaining': '',
                   'doneOrCancel': 'and (status = DONE or status = CANCELED)',
                   'subtaskdone': 'and status in (Done, Closed) and issuetype in (ST-Dev, ST-Doc, ST-Tst)',
                   'doneOrValidate': 'and (status = DONE or status = "To Validate")',
                   'canceled': 'and status = CANCELED',
                   'doneAndNotAssignee': 'and status = Done and assignee is EMPTY'
                   }
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        path_file = self._path_data + now.replace('-', '') + self._project + '_' + 'remaining' + '.txt'
        with open(path_file, 'w', encoding='utf-8') as f:
            for task in self.search('project = ' + self._project + ' ' + filters['subtaskdone'] +
                                    ' and remainingEstimate > 0 ORDER BY assignee ASC, remainingEstimate DESC',
                                    maxResults=False, fields=fields, trc=True):
                # print(task.key)
                if task.fields.aggregatetimeestimate is not None:
                    print(task, task.fields.assignee if task.fields.assignee else 'Non assignée', task.fields.summary,
                          self._url_server + "browse/" + task.key, task.fields.status,
                          task.fields.aggregatetimeestimate / 3600, 'h')
                    f.write(' '.join((str(task), str(task.fields.assignee) if task.fields.assignee else 'Not assigned', task.fields.summary,
                          self._url_server + "browse/" + task.key, str(task.fields.status),
                          str(task.fields.aggregatetimeestimate / 3600) + 'h')) + '\n')
                if False:
                    task.update(update={"timetracking": [{"edit": {"remainingEstimate": "0h"}}]})
            # task.update(update={"timetracking_remainingestimate": "0h"})

    def false_status(self):
        # sprint_field = self._fields['sprints']['field']
        # fields = 'summary, assignee, ' + sprint_field + ', status'
        fields = 'summary, assignee, status'
        # filtre = ' AND Sprint in closedSprints() AND Sprint not in openSprints() AND ' \
        filtre = ' AND ' \
                 'status not in (Closed, Cancelled, Done, Closed, Validated) ORDER BY status ASC'
        for task in self.search('project = ' + self._project + filtre,
                                50000, fields=fields, trc=True):
            # print(task.key)
            print(task, task.fields.assignee if task.fields.assignee else 'Non assignée', task.fields.summary,
                  self._url_server + "browse/" + task.key,
                  # attrgetter(sprint_field)(task.fields)[-1].split(',name=')[-1].split(',startDate=')[0],
                  task.fields.status)

    def epic_ticket(self, dates: list, filtre: str = '', suffix: str = ''):
        epics_date = {}
        us_date = {}
        now = datetime.now().strftime('%Y-%m-%d')
        for date in dates:
            if date <= now:
                epics_date[date] = {}
                us_date[date] = {}
        epics_changelogs = {}
        epics_fields = []
        for key, value in self._epic_fields.items():
            if 'field_changelog' in value:
                epics_changelogs[value['field_changelog']] = key
            if 'field' in value:
                epics_fields.append(value['field'].split('.')[0])
        tickets_changelogs = {}
        if SUPER in self._super:
            tickets_fields = [self._super['field'], self._super[SUPER]['field']]
        else:
            tickets_fields = [self._super['field']]
        for key, value in self._fields.items():
            if 'field_changelog' in value:
                tickets_changelogs[value['field_changelog']] = key
            if 'field' in value:
                tickets_fields.append(value['field'].split('.')[0])

        for epic in self.search(jql_str='project = ' + self._project + ' AND type = Epic ORDER BY key asc',
                                maxResults=3000, fields=', '.join(epics_fields), expand='changelog'):

            created = epic.fields.created[:10]
            for date in dates:
                if created <= date <= now:
                    epics_date[date][epic.key] = {'update': {}}
                    for epic_field, epic_field_conf in self._epic_fields.items():
                        epics_date[date][epic.key][epic_field] = attrgetter(epic_field_conf['field'])(epic.fields)
                        epics_date[date][epic.key]['update'][epic_field] = now

            for changelog in epic.changelog.histories:
                changelog_date = changelog.created[:10]
                for changelog_item in changelog.items:
                    field = changelog_item.field
                    if field in epics_changelogs:
                        for date in dates:
                            if created <= date < changelog_date <= epics_date[date][epic.key]['update'][epics_changelogs[field]]:
                                epics_date[date][epic.key][epics_changelogs[field]] = changelog_item.fromString
                                epics_date[date][epic.key]['update'][epics_changelogs[field]] = changelog_date

        epics_no_rights = {}
        for ticket in self.search(jql_str='project = ' + self._project +
                                          ' AND type in ("' + '", "'.join(self._type_base) + '") ' + filtre +
                                          ' ORDER BY key asc',
                                  maxResults=False, expand='changelog', trc=False,
                                  fields=', '.join(tickets_fields)):

            created = ticket.fields.created[:10]
            ticket_super = attrgetter(self._super['field'])(ticket.fields)
            if SUPER in self._super:
                ticket_super_super = attrgetter(self._super[SUPER]['field'])(ticket.fields)
            else:
                ticket_super_super = None
            for date in dates:
                if created <= date <= now:
                    us_date[date][ticket.key] = {'update': {SUPER: now, SUPER_SUPER: now}}
                    for us_field, us_field_conf in self._fields.items():
                        try:
                            us_date[date][ticket.key][us_field] = attrgetter(us_field_conf['field'])(ticket.fields)
                        except AttributeError:
                            logging.info('AttributeError :' + us_field_conf['field'])
                        us_date[date][ticket.key]['update'][us_field] = now
                    add_super(date, ticket_super_super, epics_date, epics_no_rights,
                              ticket_super, ticket, us_date, self._super)

            for changelog in ticket.changelog.histories:
                changelog_date = changelog.created[:10]
                for changelog_item in changelog.items:
                    if changelog_item.field in tickets_changelogs:
                        field = 'name' if changelog_item.field == 'summary' else tickets_changelogs[changelog_item.field]
                        for date in dates:
                            if created <= date < changelog_date <= us_date[date][ticket.key]['update'][field]:
                                us_date[date][ticket.key][field] = changelog_item.fromString
                                us_date[date][ticket.key]['update'][field] = changelog_date
                    elif changelog_item.field in (self._super['field_changelog'],):
                        change_super(changelog_date, changelog_item, created, dates, epics_date, ticket, us_date,
                                     self._super)
                    elif SUPER in self._super and changelog_item.field in (self._super[SUPER]['field_changelog'],):
                        change_super(changelog_date, changelog_item, created, dates, epics_date, ticket, us_date,
                                     self._super)
                    elif changelog_item.field not in self._fields_change_ignored:
                        logging.debug(' '.join('Field not ignored', changelog_item.field, changelog_item.fieldtype,
                                               getattr(changelog_item, 'from'),
                                      # changelog_item.fromString, changelog_item.to, changelog_item.toString
                                               ))

        if epics_no_rights:
            logging.warning(' '.join('Right to see', ' '.join(epics_no_rights.keys()), '?'))
            logging.warning(' '.join('Exemple ticket from epic:', epics_no_rights))

        now = datetime.now().strftime('%Y-%m-%d')
        path_file = self._path_data + now.replace('-', '') + self._project + '_' + suffix + '.json'
        with open(path_file, 'w', encoding='utf-8') as f:
            json.dump(us_date, f, indent=2)
        return us_date, path_file

    def sprints(self):
        s = {}
        for sprint in self._jira.sprints(self._board_id):
            if sprint.state == 'future':
                s[sprint.id] = {'name': sprint.name, 'state': sprint.state}
            else:
                s[sprint.id] = {'start_date': sprint.activatedDate[:10], 'end_date': sprint.completeDate[:10],
                                'name': sprint.name, 'state': sprint.state}
        now = datetime.now().strftime('%Y-%m-%d')
        path_file = self._path_data + now.replace('-', '') + self._project + '_' + 'infos_sprints' + '.json'
        with open(path_file, 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=2)
        return s, path_file
