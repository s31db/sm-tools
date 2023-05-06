from charts.cumulative import Cumulative
from charts.treemap import Treemap
from charts.scatterplot import Scatter
from charts.histogram import Histogram
from helpers.prepare_date_sprint import sprint_dates
import json
from config import config
from datetime import datetime, timedelta
from prepare_data import tree
import yaml
from yaml.loader import SafeLoader
from atlassian.jiraSM import JiraSM


def jira_cum(project: str, date_file: str = None,
             suffix: str = '', step: int = 1, details: bool = False, chart_html: bool = False,
             start_date: str = '2023-01-09', weeks: int = 15):
    d = dates(start_date=start_date, weeks=weeks)
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


def jira_treemap(project: str, suffix: str = '', date_file: str = None, html: bool = False, chart_html: bool = False):
    data_conf, n, now = get_tree(project, suffix, date_file)
    if chart_html:
        return Treemap('Treemap ' + now, nodes=n, **data_conf['projects'][project]).build().chart_html()
    elif html:
        Treemap('Treemap ' + now, nodes=n, **data_conf['projects'][project]).build().show().html()
    else:
        Treemap('Treemap ' + now, nodes=n, **data_conf['projects'][project]).build().show()


def get_tree(project: str, suffix: str = '', date_file: str = None):
    if date_file:
        now = date_file
    else:
        now = (datetime.now() + timedelta(days=-0)).strftime('%Y-%m-%d')
    data_conf, datas_sm = prepare_data(project=project, suffix=suffix, date_file=date_file)
    n = tree.build_tree(datas_sm[now])[1]
    return data_conf, n, now


def prepare_data(project: str, suffix: str, date_file: str = None):
    data_conf = jiraconf()
    if date_file:
        now = date_file
    else:
        now = (datetime.now() + timedelta(days=-0)).strftime('%Y-%m-%d')
    print(data_conf['projects'][project]['path_data'] + now.replace('-', '') + project + '_' + suffix + '.json')
    with open(data_conf['projects'][project]['path_data'] + now.replace('-', '') + project + '_' + suffix + '.json',
              'r', encoding='utf-8') as fp:
        datas_sm = json.load(fp)
    return data_conf, datas_sm


def dates(start_date: str = '2023-01-09', weeks: int = 9):
    return list(sprint_dates(start_date, weeks))


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


def sprints(project: str, suffix: str = ''):
    data_conf, datas_sm = prepare_data(project=project, suffix=suffix)
    now = (datetime.now() + timedelta(days=-0)).strftime('%Y-%m-%d')
    print('datas/' + now.replace('-', '') + project + '_' + 'infos_sprints' + '.json')
    with open('datas/' + now.replace('-', '') + project + '_' + 'infos_sprints' + '.json', 'r', encoding='utf-8') as fp:
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


def time_nb(project: str, suffix: str = '', date_file: str = None):
    if date_file:
        now = date_file
    else:
        now = (datetime.now() + timedelta(days=-0)).strftime('%Y-%m-%d')
    data_conf, datas_sm = prepare_data(project=project, suffix=suffix, date_file=now)
    tickets = []
    dates_end = {}
    status_start = ('To Do', 'In Progress', 'Blocked', 'Done', 'Testing', 'Validated', 'Closed')
    dates = list(datas_sm.keys())
    for da in dates:
        if da <= now:
            for ticket, value in datas_sm[da].items():
                if ticket not in tickets and value['status'] in ('Done', 'Testing', 'Validated', 'Closed'):
                    # Find start: In progress
                    for st_da in dates:
                        if datas_sm[da][ticket]['created'][:10] <= st_da <= now:
                            if datas_sm[st_da][ticket]['status'] in status_start:
                                if da not in dates_end:
                                    dates_end[da] = {}
                                estimate = float_to_int(datas_sm[da][ticket]['estimate']) if 'estimate' in \
                                                                                             datas_sm[da][ticket] else 1
                                dates_end[da][ticket] = {'tps': (datetime.strptime(da, '%Y-%m-%d') - datetime.strptime(
                                    st_da, '%Y-%m-%d')).days, 'tps_t': dates.index(da)-dates.index(st_da),
                                                         'estimate': estimate,
                                                         'date': da[:7]}
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

    Scatter(values=datas, filtre='tps_t <= tps_t.quantile(.95) & tps_t >= tps_t.quantile(.05)').by_date().build().show()

    # Find repartition, time with estimate and cost
    for estimate, tps in estimat.items():
        print(estimate/10, ':', sum(tps)/len(tps))


def histogramme(project: str, suffix: str = '', date_file: str = None):
    if date_file:
        now = date_file
    else:
        now = (datetime.now() + timedelta(days=-0)).strftime('%Y-%m-%d')
    data_conf, datas_sm = prepare_data(project=project, suffix=suffix, date_file=now)
    tickets = []
    dates_end = {}
    dates = list(datas_sm.keys())
    for da in dates:
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


def timestr(tim: int, t: int, s: int, st: str):
    n = tim
    if s:
        n = n % s
    n = int(n / t)
    if n > 1:
        return str(n) + ' ' + st + ' '
    elif n == 1:
        return str(n) + ' ' + st[:-1] + ' '
    return ''


def time(tim):
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
