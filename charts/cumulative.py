from charts.chart import Chart
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from typing import Self


def previous_date(str_date: str) -> str:
    return (datetime.strptime(str_date, "%Y-%m-%d") - timedelta(days=1)).strftime(
        "%d/%m"
    )


class Cumulative(Chart):
    _datas: dict[str, dict[str, dict[str, None | str | int | float | dict[str, str]]]]
    _colors: dict[str, str] = {
        "": "#858080",
        "To Do": "#999898",
        "In Progress": "#5358ad",
        "Test": "forestgreen",
        "Done": "darkgreen",
    }
    _legend: bool = True
    _details: bool = True
    _restart_done: bool = False
    # Todo intervall will be automatic: ratio length date / width graph
    _date_format: bool = True
    _asofs_all: list[str]
    _group_status: dict[str, dict[str, str | int | float]] = {}
    _status_label: dict[str, str] = {}
    _status_done: tuple[str, ...] = ()
    _closed_is_done: bool = False

    def datas(
        self,
        datas: dict[
            str, dict[str, dict[str, None | str | int | float | dict[str, str]]]
        ],
    ) -> Self:
        self._datas = datas
        return self

    def replace_status_label(self, data: dict[str, str]) -> tuple[Self, str]:
        status = data["status"] if "status" in data else data["Status.Name"]
        return self.replace_status(status, data)

    def replace_status(
        self, status: str, data: dict[str, str] | None = None
    ) -> tuple[Self, str]:
        status_r = status
        if self._status_label and status in self._status_label:
            status_r = self._status_label[status]
        if (
            self._closed_is_done
            and data
            and "AssetState" in data
            and data["AssetState"] == 128
        ):
            status_r = "Done"
        return self, status_r

    def replace_status_group(self, data: dict[str, str]) -> tuple[Self, str]:
        status = data["status"] if "status" in data else data["Status.Name"]
        if self._group_status and status in self._group_status:
            return self.replace_status(self._group_status[status], data)
        return self.replace_status(status, data)

    def asofs_all(self, asofs_all: list[str]) -> Self:
        self._asofs_all = asofs_all
        return self

    def details(self, details: bool) -> Self:
        self._details = details
        return self

    def build(self) -> Self:
        colors_project = dict(reversed(self._colors.items()))
        vals: dict[str, list[int]] = {}
        for val in colors_project.keys():
            vals[self.replace_status(val, None)[1]] = []
        asofs: list[str] = self.count_status(vals)

        colors, vals = self.prepare_colors(vals, colors_project=colors_project)
        done_total_first: int = 0
        if self._restart_done:
            for status_done in self._status_done:
                if status_done in vals:
                    done_first = vals[status_done][0]
                    done_total_first += done_first

        fig, ax = plt.subplots(figsize=(8, 4))

        if self._date_format:
            ax.stackplot(
                [datetime.strptime(d[:10], "%Y-%m-%d") for d in asofs],
                list(vals.values()),
                labels=vals.keys(),
                alpha=0.8,
                colors=colors,
            )
        else:
            ax.stackplot(
                [a[8:10] + "/" + a[5:7] for a in asofs],
                list(vals.values()),
                labels=vals.keys(),
                alpha=0.8,
                colors=colors,
            )
            plt.xticks([a[8:10] + "/" + a[5:7] for a in self._asofs_all])
        dates: list[datetime] = [
            datetime.strptime(d[:10], "%Y-%m-%d") for d in self._asofs_all
        ]
        if self._date_format:
            plt.xticks(dates)  # type: ignore
            if len(dates) > 100:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=28))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))
            elif len(dates) > 50:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
            elif len(dates) > 30:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))

        if self._legend:
            ax.legend(loc="upper left")
        ax.set_title(self._title)

        plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
        fig.tight_layout()
        if self._date_format:
            ax.set_xlim(dates[0], dates[-1])
        else:
            ax.set_xlim(xmin=0, xmax=len(self._asofs_all) - 1)
        ax.grid(axis="y")
        if self._restart_done:
            ax.set_ylim(bottom=max(done_total_first - 5, -0.1))
        else:
            ax.set_ylim(bottom=-0.1)
        plt.box(False)
        return self

    def prepare_colors(
        self, vals: dict[str, list[int]], colors_project: dict[str, str]
    ) -> tuple[list[str], dict[str, list[int]]]:
        vals2 = {}
        colors = []
        for key, value in vals.items():
            if sum(value) > 0:
                vals2[key] = value
                colors.append(colors_project[self.replace_status(key)[1]])
        return colors, vals2

    def count_status(self, vals) -> list[str]:
        asofs: list[str] = []
        for d, datas in self._datas.items():
            if d in self._asofs_all:
                asofs.append(d)
                if self._details:
                    statu = [
                        self.replace_status_label(data)[1] for data in datas.values()
                    ]
                else:
                    statu = [
                        self.replace_status_group(data)[1] for data in datas.values()
                    ]
                for status, nb in vals.items():
                    nb.append(statu.count(status))
        return asofs


def test_show():
    from helpers.prepare_date_sprint import sprint_dates
    import json

    with open("../example/example.json", "r", encoding="utf-8") as fp:
        datas = json.load(fp)
    Cumulative().datas(datas).title("Cumulative Flow Diagram").asofs_all(
        [*sprint_dates("2022-08-29", 2)]
    ).build().show()


def test_show_not_dates():
    from helpers.prepare_date_sprint import sprint_dates
    import json

    with open("../example/example.json", "r", encoding="utf-8") as fp:
        datas = json.load(fp)
    Cumulative(date_format=False).datas(datas).title(
        "Cumulative Flow Diagram"
    ).asofs_all([*sprint_dates("2022-08-29", 2)]).build().show()
