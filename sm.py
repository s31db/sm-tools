from charts.cumulative import Cumulative
from charts.treemap import Treemap
from charts.scatterplot import Scatter
from charts.histogram import Histogram
from charts.burndown import Burndown
from helpers.prepare_date_sprint import sprint_dates
import json
from config import config
from datetime import date, datetime, timedelta
from prepare_data import tree
import yaml
from yaml.loader import SafeLoader
from atlassian.jiraSM import JiraSM
from atlassian.tempo_jira import Tempo

Y_M_D = '%Y-%m-%d'


def jira_cum(project: str, date_file: str = None,
             suffix: str = '', step: int = 1, details: bool = False, chart_html: bool = False,
             start_date: str = '2023-01-09', weeks: int = 15, now: bool = False):
    d = dates(start_date=start_date, weeks=weeks, now=now)
    data_conf, datas_sm = prepare_data(project=project, suffix=suffix, date_file=date_file)
    i = 0
    filter_dates = []
    for da in d:
        if i == 0:
            filter_dates.append(da)
        if i == step:
            i = 0
        else:
            i += 1
    cum = Cumulative(project, restart_done=True, **data_conf['projects'][project]).details(details)
    my_dict = data_conf['projects'][project]['colors']
    my_dict = dict(reversed(my_dict.items()))
    if chart_html:
        return cum.datas(datas_sm).colors(my_dict).asofs_all(filter_dates).build().chart_html()
    else:
        cum.datas(datas_sm).colors(my_dict).asofs_all(filter_dates).build().show()


def jira_treemap(project: str, suffix: str = '', date_file: str = None, html: bool = False, show: bool = False):
    data_conf, n, now = get_tree(project, suffix, date_file)
    t = Treemap(project + ' ' + now, global_parent=project, nodes=n, **data_conf['projects'][project]).build()
    if html:
        t.html()
    if show:
        t.show()
    return t


def get_tree(project: str, suffix: str = '', date_file: str = None):
    now = datefile(date_file)
    data_conf, datas_sm = prepare_data(project=project, suffix=suffix, date_file=date_file)
    n = tree.build_tree(datas_sm[now])[1]
    return data_conf, n, now


def prepare_data(project: str, suffix: str, date_file: str = None):
    data_conf = jiraconf()
    now = datefile(date_file)
    path_file = f"{data_conf['projects'][project]['path_data']}{now.replace('-', '')}{project}_{suffix}'.json'"
    print(path_file)
    with open(path_file, 'r', encoding='utf-8') as fp:
        datas_sm = json.load(fp)
    return data_conf, datas_sm


def dates(start_date: str = '2023-01-09', weeks: int = 9, now: bool = False, limit: str = None,
          end_date: str = None) -> list[date]:
    return list(sprint_dates(start_date, weeks, now=now, limit=limit, end_date=end_date))


def extract_jira(project: str, start_date: str, filtre: str = '', suffix: str = ''):
    data_conf = jiraconf()
    d = dates(start_date, 128)
    JiraSM(project=project, **data_conf['projects'][project]).conn().epic_ticket(list(d), filtre=filtre, suffix=suffix)


def jiraconf():
    c = config()
    with open(c.JIRA.conf, 'r', encoding='utf-8') as f:
        data_conf = yaml.load(f, Loader=SafeLoader)
    return data_conf


def false_status(project: str):
    data_conf = jiraconf()
    JiraSM(project=project, **data_conf['projects'][project]).conn().false_status()


def remaining(project: str):
    data_conf = jiraconf()
    JiraSM(project=project, **data_conf['projects'][project]).conn().remaining()


def workload(project: str, start_date: str, date_to: str):
    data_conf = jiraconf()
    with JiraSM(project=project, **data_conf['projects'][project]).conn() as conn:
        conn.workload(start_date=start_date, date_to=datefile(date_to))


def fmt_date_file(date: str):
    return date.replace('-', '')


def workload_analyse(project: str, start_date: str, date_to: str, date_file: str = None) -> [dict, dict]:
    data_conf = jiraconf()
    now = datefile(date_file)
    ends = (f"workloads_{project}_{fmt_date_file(start_date)}_"
            f"{fmt_date_file(datefile(date_to))}_{fmt_date_file(now)}.json")

    print(data_conf['Common']['path_data'] + ends)
    with open(data_conf['Common']['path_data'] + ends, 'r', encoding='utf-8') as fp:
        datas_sm = json.load(fp)
    # print(datas_sm)
    # infos au global
    works_project_global = {}
    # infos par projet, par personne, par journée
    works_project = {}
    # infos par personne, par journée
    works = {}
    for datas in datas_sm:
        datas['time'] = time(datas['timeSpentSecond']).strip()
        month = datas['day'][:7]
        _project = datas['project']
        if _project not in works_project:
            works_project[_project] = {}
            works_project_global[_project] = {'timeSpentSecond': 0, 'tickets': {}}

        if datas['author'] not in works_project[datas['project']]:
            works_project[_project][datas['author']] = {}
        if month not in works_project[_project][datas['author']]:
            works_project[_project][datas['author']][month] = {'time': None, 'timeSpentSecond': 0, 'tickets': []}
        if datas['day'] not in works_project[_project][datas['author']]:
            works_project[_project][datas['author']][datas['day']] = {'time': None, 'timeSpentSecond': 0, 'tickets': []}

        works_project_global[_project]['timeSpentSecond'] += int(datas['timeSpentSecond'])
        if datas['key'] in works_project_global[_project]['tickets']:
            works_project_global[_project]['tickets'][datas['key']] += int(datas['timeSpentSecond'])
        else:
            works_project_global[_project]['tickets'][datas['key']] = int(datas['timeSpentSecond'])

        works_project[_project][datas['author']][month]['timeSpentSecond'] += int(datas['timeSpentSecond'])
        works_project[_project][datas['author']][datas['day']]['timeSpentSecond'] += int(
            datas['timeSpentSecond'])
        works_project[_project][datas['author']][month]['tickets'].append(datas)
        works_project[_project][datas['author']][datas['day']]['tickets'].append(datas)

        if datas['author'] not in works:
            works[datas['author']] = {}
        if month not in works[datas['author']]:
            works[datas['author']][month] = {'time': None, 'timeSpentSecond': 0, 'projects': {}, 'tickets': []}
        if datas['day'] not in works[datas['author']]:
            works[datas['author']][datas['day']] = {'time': None, 'timeSpentSecond': 0, 'projects': {}, 'tickets': []}

        # if 'project' in datas:
        if _project not in works[datas['author']][datas['day']]['projects']:
            works[datas['author']][datas['day']]['projects'][_project] = {
                'time': None, 'timeSpentSecond': 0, 'tickets': []}
        if _project not in works[datas['author']][month]['projects']:
            works[datas['author']][month]['projects'][_project] = {
                'time': None, 'timeSpentSecond': 0, 'tickets': []}

        works[datas['author']][month]['projects'][_project]['timeSpentSecond'] += int(datas['timeSpentSecond'])
        works[datas['author']][datas['day']]['projects'][_project]['timeSpentSecond'] += int(
            datas['timeSpentSecond'])

        works[datas['author']][month]['projects'][_project]['tickets'].append(datas)
        works[datas['author']][datas['day']]['projects'][_project]['tickets'].append(datas)

        works[datas['author']][month]['timeSpentSecond'] += int(datas['timeSpentSecond'])
        works[datas['author']][datas['day']]['timeSpentSecond'] += int(datas['timeSpentSecond'])

        works[datas['author']][month]['tickets'].append(datas)
        works[datas['author']][datas['day']]['tickets'].append(datas)

    for wproject in works_project.values():
        for wp in wproject.values():
            for work_day in wp.values():
                work_day['time'] = time_days(work_day['timeSpentSecond']).strip()
    with open(data_conf['Common']['path_data'] + 'calc_projects_' + ends, 'w', encoding='utf-8') as f:
        json.dump(works_project, f, indent=2)
    for work in works.values():
        for work_day in work.values():
            work_day['time'] = time_days(work_day['timeSpentSecond']).strip()
            for proj in work_day['projects'].values():
                proj['time'] = time_days(proj['timeSpentSecond']).strip()
    with open(data_conf['Common']['path_data'] + 'calc_personnes_' + ends, 'w', encoding='utf-8') as f:
        json.dump(works, f, indent=2)
    # print(time_days(works_project_global[project]['timeSpentSecond']))
    # for key, value in works_project_global[project]['tickets'].items():
    #     print(key, time_days(value))
    return works_project, work


def analyse_workload(start_date: str, date_to: str, date_file: str = None):
    data_conf = jiraconf()
    now = datefile(date_file)
    ends = 'workloads' + fmt_date_file(start_date) + '_' + fmt_date_file(date_to) + '_' + now.replace('-', '') + '.json'

    with open(data_conf['Common']['path_data'] + 'teams.json', 'r', encoding='utf-8') as fp:
        datas_sm = json.load(fp)
    with open(data_conf['Common']['path_data'] + 'calc_personnes_' + ends, 'r', encoding='utf-8') as f:
        workloads = json.load(f)
    month = start_date[:7]
    out_project = datas_sm['out_project_'+month]
    ds = dates(start_date=start_date, weeks=0, now=True, limit=now)
    sum_project = {'all': {}}
    teams = {'all': None}
    for person, infos in out_project.items():
        print(person)
        # Ajout infos project
        team = infos['team']
        teams[team] = None
        if person not in workloads:
            print('\t', 'no works')
            print('\t'*2, infos['dates'])
            if "other_projects" in infos:
                print('\t'*2, infos['other_projects'])
        else:
            if month in workloads[person]:
                if team not in sum_project:
                    sum_project[team] = {}
                for projects, projects_infos in workloads[person][month]['projects'].items():
                    print('\t', month, projects, projects_infos['time'])
                    for t in ['all', team]:
                        if projects in sum_project[t]:
                            sum_project[t][projects]['timeSpentSecond'] += projects_infos['timeSpentSecond']
                        else:
                            sum_project[t][projects] = {'timeSpentSecond': projects_infos['timeSpentSecond']}

            for d in ds:
                if d not in workloads[person]:
                    print('\t', d, 'no works')
                elif workloads[person][d]['time'] != '1 day':
                    print('\t', d, '\t', 'pb works', workloads[person][d]['time'],
                          ' '.join([key + ' ' + v['time'] for key, v in workloads[person][d]['projects'].items()]))
                else:
                    print('\t', d, 'ok',
                          ' '.join([key + ' ' + v['time'] for key, v in workloads[person][d]['projects'].items()]))
                if d in infos['dates']:
                    print('\t' * 2, infos['dates'][d], 'out_project')

                if 'other_projects' in infos:
                    for other_project, other_project_infos in infos['other_projects'].items():
                        if d in other_project_infos['dates']:
                            print('\t' * 2,  other_project, other_project_infos['dates'][d], 'hors jira')
    for team in teams.keys():
        if team in sum_project:
            for projects, project_info in sum_project[team].items():
                print(team, month, projects, time_days(project_info['timeSpentSecond']))
        else:
            print(team, month, 'no works')


def analyse_workload_planned(project: str, start_date: str, date_to: str, date_file: str = None,
                             limit_today: bool = False):
    data_conf = jiraconf()
    now = datefile(date_file)
    ends = f"{fmt_date_file(start_date)}_{fmt_date_file(datefile(date_to))}_{now.replace('-', '')}.json"
    ds = dates(start_date=start_date, weeks=0, now=limit_today, end_date=datefile(date_to) if not limit_today else None)
    sum_project = {'all': {}}
    sum_project_person = {'all': {}}
    sum_project_planned = {'all': {}}
    d_person = {}

    with open(f"{data_conf['Common']['path_data']}calc_personnes_workloads_{project}_{ends}", 'r', encoding='utf-8') as f:
        workloads = json.load(f)

    with open(data_conf['Common']['path_data'] + 'plan' + ends, 'r', encoding='utf-8') as f:
        planneds = json.load(f)

    with open(data_conf['Common']['path_data'] + 'teams' + ends, 'r', encoding='utf-8') as f:
        teams_members = json.load(f)

    members_used = []
    for team, members in teams_members.items():
        for person, person_infos in members.items():
            person_id = person.split('@')[0].lower()
            if person_id not in members_used:
                members_used.append(person_id)
                person_name = ' '.join([p[0].upper() + p[1:] for p in person.split('@')[0].split('.')])
                if 'dateToANSI' not in person_infos or start_date <= person_infos['dateToANSI']:
                    d_person[person_id] = {'name': person_name, 'days': {}}
                    sum_project_person[person_id] = {'all': {}}

                for d in ds:
                    if 'dateToANSI' in person_infos and d > person_infos['dateToANSI']:
                        break
                    d_person[person_id]['days'][d] = {}
                    month = d[:7]
                    if person_id in workloads:
                        if d in workloads[person_id]:
                            d_person[person_id]['days'][d]['works'] = {}
                            for key, v in workloads[person_id][d]['projects'].items():
                                d_person[person_id]['days'][d]['works'][key] = v['timeSpentSecond']

                            if month not in sum_project:
                                sum_project[month] = {}
                            if month not in sum_project_person[person_id]:
                                sum_project_person[person_id][month] = {'all': {}}
                            for project, projects_infos in workloads[person_id][d]['projects'].items():

                                if project in sum_project[month]:
                                    sum_project[month][project]['timeSpentSecond'] += projects_infos['timeSpentSecond']
                                else:
                                    sum_project[month][project] = {'timeSpentSecond': projects_infos['timeSpentSecond']}

                                if project in sum_project['all']:
                                    sum_project['all'][project]['timeSpentSecond'] += projects_infos['timeSpentSecond']
                                else:
                                    sum_project['all'][project] = {'timeSpentSecond': projects_infos['timeSpentSecond']}

                                if project in sum_project_person[person_id][month]:
                                    sum_project_person[person_id][month][project]['timeSpentSecond'] += \
                                        projects_infos['timeSpentSecond']
                                else:
                                    sum_project_person[person_id][month][project] = {
                                        'timeSpentSecond': projects_infos['timeSpentSecond']}

                                if project in sum_project_person[person_id]['all']:
                                    sum_project_person[person_id]['all'][project]['timeSpentSecond'] += \
                                        projects_infos['timeSpentSecond']
                                else:
                                    sum_project_person[person_id]['all'][project] = {
                                        'timeSpentSecond': projects_infos['timeSpentSecond']}

                    if person in planneds and d in planneds[person]:
                        d_person[person_id]['days'][d]['plan'] = {}
                        for project_key, projects_infos in planneds[person][d].items():
                            project = projects_infos['summary']
                            seconds = projects_infos['secondsPerDay']
                            d_person[person_id]['days'][d]['plan'][project] = seconds

                            if d[:7] not in sum_project_planned:
                                sum_project_planned[month] = {}

                            if project in sum_project_planned[month]:
                                sum_project_planned[month][project]['timeSpentSecond'] += seconds
                            else:
                                sum_project_planned[month][project] = {'timeSpentSecond': seconds}

                            if project in sum_project_planned['all']:
                                sum_project_planned['all'][project]['timeSpentSecond'] += seconds
                            else:
                                sum_project_planned['all'][project] = {'timeSpentSecond': seconds}

    for p_infos in d_person.values():
        print(p_infos['name'])
        for d, d_infos in p_infos['days'].items():
            print('\t', d, end=' ')
            if 'works' in d_infos:
                for key, v in d_infos['works'].items():
                    print(key, time_days(v), end=' ')
                print()
            else:
                print('\tNo works on Jira Logs !')
            if 'plan' in d_infos:
                for key, v in d_infos['plan'].items():
                    print('\t\t\t Plan ', key, time_days(v))
            else:
                print('\t\t\t No plan !')

    print('--------------LOG---------------')
    for d, projects in sum_project.items():
        for project, project_info in projects.items():
            print('Log', d, project, time_days(project_info['timeSpentSecond']))

    print('--------------Plan---------------')
    for d, projects in sum_project_planned.items():
        for project, project_info in projects.items():
            print('Plan', d, project, time_days(project_info['timeSpentSecond']))

    print('--------------Log by Person---------------')
    for p, sum_projects in sum_project_person.items():
        for d, projects in sum_projects.items():
            for project, project_info in projects.items():
                if 'timeSpentSecond' in project_info:
                    print('Log person', p, d, project, time_days(project_info['timeSpentSecond']))

    return ds, d_person, sum_project, sum_project_planned, sum_project_person


def worklog_plan_html(project: str, date_file: str = None,
                      start_date: str = '2023-08-01', date_to: str = '2023-10-01',  limit_today: bool = False):
    workload(project=project, start_date=start_date, date_to=datefile(date_to) if not limit_today else None)
    workload_analyse(project=project, start_date=start_date, date_to=datefile(date_to) if not limit_today else None)

    planned(project=project, start_date=start_date, date_to=datefile(date_to) if not limit_today else None)
    ds, d_person, sum_project, sum_project_planned, sum_project_person = analyse_workload_planned(
        project=project,
        start_date=start_date, date_to=datefile(date_to) if not limit_today else None,
        date_file=date_file, limit_today=limit_today)
    for p_infos in d_person.values():
        yield (f"<details open><summary>{p_infos['name']} <button class='cp' "
               f"id='cpb_{p_infos['name'].replace(' ', '_')}'")
        yield 'style="padding: 8px 8px; background-color: transparent; border: none; cursor: pointer;">'
        yield '&#x1F4CB;</button></summary>'
        yield f"<div id='div_cpb_{p_infos['name'].replace(' ', '_')}'>"
        for d, d_infos in p_infos['days'].items():
            yield '{0} :'.format(d)
            if 'works' in d_infos:
                for key, v in d_infos['works'].items():
                    yield f' {key} {time_days(v)}'
            else:
                yield ' No works on Jira Logs !'
            if 'plan' in d_infos:
                yield ' / Plan :'
                for key, v in d_infos['plan'].items():
                    yield f' {key} {time_days(v)}'
            else:
                yield ' / No plan on Tempo !'
            yield '<br/>'
        yield '</div>'
        yield '</details>'


def out_person(project: str):
    data_conf = jiraconf()
    JiraSM(project=project, **data_conf['projects'][project]).conn().out_person()


def sprints(project: str, suffix: str = ''):
    data_conf, datas_sm = prepare_data(project=project, suffix=suffix)
    now = (datetime.now() + timedelta(days=-0)).strftime(Y_M_D)
    print(data_conf['projects'][project]['path_data'] +
          now.replace('-', '') + project + '_' + 'infos_sprints' + '.json')
    with open(data_conf['projects'][project]['path_data'] +
              now.replace('-', '') + project + '_' + 'infos_sprints' + '.json', 'r', encoding='utf-8') as fp:
        s = json.load(fp)
    sprints_info = {}
    for key, sprint in s.items():
        if sprint['state'] != 'future':
            sprints_info[key] = sprint
            sprints_info[key]['start'] = {}
            sprints_info[key]['end'] = {}

            for ticket, details in datas_sm[sprint['start_date']].items():
                if details['sprints'] is not None and key in [sp.split('[id=')[-1].split(',rapidViewId=')[0]
                                                              for sp in details['sprints']]:
                    sprints_info[key]['start'][ticket] = details

            for ticket, details in datas_sm[sprint['end_date']].items():
                if details['sprints'] is not None and key in [sp.split('[id=')[-1].split(',rapidViewId=')[0]
                                                              for sp in details['sprints']]:
                    sprints_info[key]['end'][ticket] = details

    sprints_calcul = {}
    for key, sprint in sprints_info.items():
        planned = sum([float(t['estimate']) for t in sprint['start'].values() if t['estimate'] is not None])
        realized = sum([float(t['estimate']) for t in sprint['end'].values() if t['estimate'] is not None and
                        t['status'] in ('Done', 'Fini', 'Closed')])
        total = sum([float(t['estimate']) for t in sprint['end'].values() if t['estimate'] is not None])
        sprints_calcul[sprint['name']] = {'Planned': planned, 'Realized': realized, 'Total': total}
    from charts.barcompare import Barcompare
    Barcompare('Sprint By Sprint', rotation=45).nodes(
        sprints_calcul).width_bar(0.25).build().show()


def prepare_color(nb: int):
    import matplotlib.pyplot as plt
    sm = plt.cm.ScalarMappable(cmap=plt.cm.cool)
    sm.set_clim(vmin=0, vmax=nb)
    for i in range(nb):
        c = sm.to_rgba(i)
        print('#%02x%02x%02x' % (int(c[0] * 100), int(c[1] * 100), int(c[2] * 100)))


def float_to_int(value: float):
    if value is None:
        return 0
    elif float(value) % 1 == 0:
        return int(float(value))
    return value


def weeks_of_mounth(da: str):
    date = datetime.strptime(da, Y_M_D)
    return str(date.isocalendar()[1])


def time_nb(project: str, suffix: str = '', date_file: str = None):
    now = datefile(date_file)
    datas_sm = prepare_data(project=project, suffix=suffix, date_file=now)[1]
    tickets = []
    dates_end = {}
    status_start = ('To Do', 'In Progress', 'Blocked', 'Done', 'Testing', 'Validated', 'Closed')
    dates_l = list(datas_sm.keys())
    for da in dates_l:
        if da <= now:
            for ticket, value in datas_sm[da].items():
                if ticket not in tickets and value['status'] in ('Done', 'Testing', 'Validated', 'Closed'):
                    # Find start: In progress
                    for st_da in dates_l:
                        if datas_sm[da][ticket]['created'][:10] <= st_da <= now:
                            if datas_sm[st_da][ticket]['status'] in status_start:
                                if da not in dates_end:
                                    dates_end[da] = {}
                                estimate = float_to_int(datas_sm[da][ticket]['estimate']) if 'estimate' in \
                                                                                             datas_sm[da][ticket] else 1
                                dates_end[da][ticket] = {'tps': (datetime.strptime(da, Y_M_D) - datetime.strptime(
                                    st_da, Y_M_D)).days, 'tps_t': dates_l.index(da)-dates_l.index(st_da),
                                                         'estimate': estimate,
                                                         'date': da[2:7] + '-' + weeks_of_mounth(da)}
                                break
                    tickets.append(ticket)
    print(dates_end)
    datas = {}
    estimat = {}
    for ts in dates_end.values():
        for key, t in ts.items():
            # if key in ('', ):
            #     continue
            es = int(float(t['estimate']) * 10 if t['estimate'] is not None else 0)
            if es in estimat:
                estimat[es].append(t['tps_t'])
            else:
                estimat[es] = [t['tps_t']]
            datas[key] = t
    estimat = dict(sorted(estimat.items(), key=lambda item: item[0]))

    # s = Scatter(values=datas, filtre='tps_t <= tps_t.quantile(.95) & tps_t >= tps_t.quantile(.05)').by_date().build()
    s = Scatter(values=datas).by_date().build()
    # s.show()

    # Find repartition, time with estimate and cost
    for estimate, tps in estimat.items():
        print(estimate/10, ':', sum(tps)/len(tps))
    return s.chart_html()


def datefile(date_file:str, delta: int = None) -> str:
    if date_file:
        now = date_file
    elif delta is not None:
        now = (datetime.now() + timedelta(days=delta)).strftime(Y_M_D)
    else:
        now = datetime.now().strftime(Y_M_D)
    return now


def histogramme(project: str, suffix: str = '', date_file: str = None):
    now = datefile(date_file)
    datas_sm = prepare_data(project=project, suffix=suffix, date_file=now)[1]
    tickets = []
    dates_end = {}
    datas_dates = list(datas_sm.keys())
    for da in datas_dates:
        if da <= now:
            for ticket, value in datas_sm[da].items():
                if ticket not in tickets and value['status'] in ('Done', 'Closed'):
                    if da not in dates_end:
                        dates_end[da] = {}
                    estimate = float_to_int(datas_sm[da][ticket]['estimate']) if 'estimate' in \
                                                                                 datas_sm[da][ticket] else 1
                    dates_end[da][ticket] = {
                                             'estimate': estimate,
                                             'date': da[:7]}
                    tickets.append(ticket)

    datas = {}
    for ts in dates_end.values():
        for key, t in ts.items():
            # if key in ('', ):
            #     continue
            datas[key] = t
    print(datas)
    Histogram(values=datas, filtre='tps_t <= tps_t.quantile(.95) & tps_t >= tps_t.quantile(.05)').build().show()


def timestr(tim: int, t: int, s: int | None, st: str):
    n = tim
    if s:
        n = n % s
    n = int(n / t)
    if n > 1:
        return str(n) + ' ' + st + ' '
    elif n == 1:
        return str(n) + ' ' + st[:-1] + ' '
    return ''


def time(tim: int | None) -> str:
    if tim is None or tim == 0:
        return '0'
    else:
        m = 60
        h = 60 * m
        d = 8 * h
        w = d * 5
        ti = ' '
        ti += timestr(tim, w, None, 'weeks')
        ti += timestr(tim, d, w, 'days')
        ti += timestr(tim, h, d, 'hours')
        ti += timestr(tim, m, h, 'minutes')
        return ti


def time_days(tim: int | None):
    if tim is None or tim == 0:
        return '0'
    else:
        m = 60
        h = 60 * m
        d = 8 * h
        w = 5 * d
        ti = ' '
        ti += timestr(tim, w, None, 'weeks')
        ti += timestr(tim, d, w, 'days')
        ti += timestr(tim, h, d, 'hours')
        ti += timestr(tim, m, h, 'minutes')
        return ti


def analysis_tree(project: str, date_file: str = None):
    data_conf, n, now = get_tree(project=project, date_file=date_file)
    epics = {}
    for story, v in n.items():
        if v['lvl'] == 0:
            father = v['father'] if 'father' in v else 'No Epics'
            father_name = v['father.name'] if 'father' in v else 'No Epics'
        else:
            father = story
            father_name = v['name']
        if father in epics:
            epics[father]['stories'][story] = v
        else:
            epics[father] = {'name': father_name, 'stories': {story: v}}
            # epics[father] = {'name': v['father.name'] if 'father' in v else 'No Epics', 'stories': [{story: v}]}

    for epic, v in epics.items():
        yield v['name'], Treemap('Treemap ' + v['name'] + ' ' + now, nodes=v['stories'],
                                 **data_conf['projects'][project]).build().chart_html(), '' if \
            epic == 'No Epics' else ' <b>' + time(n[epic]['aggregatetimeestimate']) + '</b> / ' + \
                                    time(n[epic]['aggregatetimeoriginalestimate']) + ' --> Spent ' + \
                                    time(n[epic]['aggregatetimespent'])


def re_tree(project: str, start_date: str, filtre: str = '', suffix: str = ''):
    data_conf = jiraconf()
    d = dates(start_date, 128)
    JiraSM(project=project, **data_conf['projects'][project]).conn().tree_jira(list(d), filtre=filtre, suffix=suffix)


def burndown(project: str, sprint: str = None, suffix: str = '', date_file: str = None, filtre: str = ''):
    data_conf = jiraconf()
    conf = data_conf['projects'][project]
    conf['type_base'] = None
    with JiraSM(project=project, **conf).conn() as conn:
        if sprint:
            pass
        else:
            sprint_id, sprint_infos = conn.sprint_actif()
            sprint = sprint_infos['name']
            filtre = ' and sprint={0} '.format(sprint_id)
        d = [sprint_infos['start_date']]
        print(sprint_infos, d)
        d += dates(sprint_infos['start_date'][:10], 0, now=False, end_date=sprint_infos['end_date'][:10])
        print(sprint_infos, d)
        datas_sm = conn.epic_ticket(list(d), filtre=filtre, suffix=suffix)[0]
    # After extract
    now = datefile(date_file)
    datas_sm = prepare_data(project=project, suffix=suffix, date_file=now)[1]

    # print(t)
    sums = []
    for dd in d:
        if dd <= now:
            sum = 0
            for ticket in datas_sm[dd].values():
                if 'timeestimate' in ticket and ticket['timeestimate'] is not None:
                    sum += int(ticket['timeestimate'])
            sums.append(sum // 3600)
    b = Burndown(title=project + ' ' + sprint, start_is_max=True, indicators=False).dates(
        ['Start'] + [dd[5:7] + '/' + dd[8:10] for dd in d[1:]]).values(sums).build()
    # b.show()
    return b.chart_html()


def planned(project: str, start_date: str, date_to: str):
    data_conf = jiraconf()
    t = Tempo(project=project, **data_conf['projects'][project]).conn()
    t.planned(start_date=start_date, date_to=datefile(date_to))
