from charts.chart import Chart
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates


def previous_date(str_date):
    return (datetime.strptime(str_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%d/%m')


class Cumulative(Chart):

    _datas: dict
    _colors: dict = {'Done': 'darkgreen', 'Test': 'forestgreen', 'In Progress': '#5358ad', 'To Do': '#999898',
                     '': '#858080'}
    _legend: bool = True
    _details: bool = True
    _restart_done: bool = False
    _date_format: bool = True
    _asofs_all: list
    _group_status: dict = {}
    _status_done: list = []

    def datas(self, datas: dict):
        self._datas = datas
        return self

    def asofs_all(self, asofs_all: list):
        self._asofs_all = asofs_all
        return self

    def colors(self, colors: dict):
        self._colors = colors
        return self

    def details(self, details: bool):
        self._details = details
        return self

    def build(self):
        vals = {}
        for val in self._colors.keys():
            vals[val] = []
        asofs = []
        for d, datas in self._datas.items():
            if d in self._asofs_all:
                asofs.append(d)
                if self._details:
                    statu = [data['status'] for data in datas.values()]
                else:
                    statu = [data['status'] if data['status'] not in self._group_status else
                             self._group_status[data['status']]
                             for data in datas.values()]
                for status, nb in vals.items():
                    nb.append(statu.count(status))

        vals2 = {}
        colors = []
        for key, value in vals.items():
            if sum(value) > 0:
                vals2[key] = value
                colors.append(self._colors[key])
        vals = vals2
        print(vals)
        if self._restart_done:
            done_total_first = 0
            for status_done in self._status_done:
                if status_done in vals:
                    done_first = vals[status_done][0]
                    done_total_first += done_first

        fig, ax = plt.subplots(figsize=(8, 4))

        if self._date_format:
            ax.stackplot([datetime.strptime(d, "%Y-%m-%d") for d in asofs], list(vals.values()),
                         labels=vals.keys(), alpha=0.8, colors=colors)
        else:
            ax.stackplot([a[8:10] + '/' + a[5:7] for a in asofs], list(vals.values()),
                         labels=vals.keys(), alpha=0.8, colors=colors)
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in self._asofs_all]
        if self._date_format:
            plt.xticks(dates)
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))

        if self._legend:
            ax.legend(loc='upper left')
        ax.set_title(self._title)

        plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
        fig.tight_layout()
        if self._date_format:
            ax.set_xlim(dates[0], dates[-1])
        else:
            ax.set_xlim(xmin=0, xmax=len(self._asofs_all)-1)
        ax.grid(axis='y')
        if self._restart_done:
            ax.set_ylim(bottom=max(done_total_first - 5, -0.1))
        else:
            ax.set_ylim(bottom=-0.1)
        plt.box(False)
        return self

    def show(self):
        plt.show()
        return self


def test_show():
    from helpers.prepare_date_sprint import sprint_dates
    import json
    with open('../example/example.json', 'r', encoding='utf-8') as fp:
        datas = json.load(fp)
    Cumulative().datas(datas).title('Cumulative Flow Diagram').asofs_all(
        [*sprint_dates('2022-08-29', 2)]).build().show()


def test_show_not_dates():
    from helpers.prepare_date_sprint import sprint_dates
    import json
    with open('../example/example.json', 'r', encoding='utf-8') as fp:
        datas = json.load(fp)
    Cumulative(date_format=False).datas(datas).title('Cumulative Flow Diagram').asofs_all(
        [*sprint_dates('2022-08-29', 2)]).build().show()
