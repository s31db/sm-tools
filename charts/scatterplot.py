from charts.chart import Chart
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from typing import Self


class Scatter(Chart):
    _values: dict
    _legend: str | bool | None
    _percent: dict = {0.5: "blue", 0.75: "green", 0.85: "red"}
    _xtick: list | None
    _x: str
    _y: str
    _size: str | None
    _size_order: list | None
    _hue: str | None
    _hue_order: list | None
    _style: str | None
    _style_order: list | None
    _palette: str | None
    _ncol_legend: int | None
    _filtre: str | None = None
    _figsize: tuple[int, int] = (10, 5)

    def by_date(self) -> Self:
        self._x = "date"
        self._y = "tps_t"
        self._xtick = None
        self._size = None
        # self._size = 'estimate'
        self._size_order = None
        # self._size_order = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0]
        self._hue = None
        # self._hue = 'estimate'
        self._hue_order = None
        # self._hue_order = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0]
        self._style = None
        self._style_order = None
        self._palette = None
        self._legend = "full"
        self._legend = None
        # self._ncol_legend = len(self._hue_order) + 1
        # self._ncol_legend = len(self._size_order) + 1
        return self

    def by_estimate(self):
        self._x = "estimate"
        self._y = "tps_t"
        self._xtick = [0, 0.5, 1, 2, 3, 5, 8, 13]
        self._size = None
        self._size_order = None
        self._hue = None
        self._hue_order = None
        self._style = None
        self._style_order = None
        self._palette = "muted"
        self._legend = False
        self._ncol_legend = None
        return self

    def build(self):
        sns.set_theme(style="white", rc={"figure.figsize": self._figsize})

        d = pd.DataFrame(self._values.values())
        if self._filtre:
            d = d.query(self._filtre)

        g = sns.relplot(
            x=self._x,
            y=self._y,
            hue=self._hue,
            size=self._size,
            style=self._style,
            hue_order=self._hue_order,
            size_order=self._size_order,
            style_order=self._style_order,
            sizes=(40, 400),
            alpha=0.5,
            palette=self._palette,
            height=self._figsize[1],
            data=d,
            legend=self._legend,
            aspect=self._figsize[0] / self._figsize[1],
        )

        if self._xtick:
            plt.xticks(self._xtick)
        plt.xlim(-0.5)

        xtick = plt.gca().get_xticks()
        ylim = xtick[-1] + 0.1

        if self._legend:
            sns.move_legend(
                g,
                "upper center",
                bbox_to_anchor=(0.5, 1),
                ncol=self._ncol_legend,
                frameon=True,
            )

        for percent, color in self._percent.items():
            percent_val = d[self._y].quantile(percent)
            plt.plot(
                [-0.5, ylim],
                [percent_val, percent_val],
                linewidth=1,
                color=color,
                linestyle="--",
            )
            plt.text(
                ylim + 0.2,
                percent_val,
                "percent " + str(int(percent * 100)),
                horizontalalignment="left",
                size="medium",
                color=color,
                weight="semibold",
            )

        return self


def float_to_int(value: float):
    if value is None:
        return 0
    elif float(value) % 1 == 0:
        return int(float(value))
    return value


def test_scatter():
    import json
    from datetime import datetime

    y_m_d = "%Y-%m-%d"

    with open("../example/example.json", "r", encoding="utf-8") as fp:
        datas_sm = json.load(fp)

    tickets = []
    dates_end = {}
    dates_l = list(datas_sm.keys())
    for da in dates_l:
        for ticket, value in datas_sm[da].items():
            if ticket not in tickets and value["status"] in ("Done", "Closed"):
                # Find start: In progress
                for st_da in dates_l:
                    # if datas_sm[da][ticket]["created"][:10] <= st_da:
                    if ticket in datas_sm[st_da]:
                        if (
                            datas_sm[st_da][ticket]["status"] is not None
                            and datas_sm[st_da][ticket]["status"] != ""
                        ):
                            if da not in dates_end:
                                dates_end[da] = {}
                            estimate = (
                                float_to_int(datas_sm[da][ticket]["estimate"])
                                if "estimate" in datas_sm[da][ticket]
                                else 1
                            )
                            dates_end[da][ticket] = {
                                "tps": (
                                    datetime.strptime(da, y_m_d)
                                    - datetime.strptime(st_da, y_m_d)
                                ).days,
                                "tps_t": dates_l.index(da) - dates_l.index(st_da),
                                "estimate": estimate,
                                "date": da[2:7],
                            }
                            break
                tickets.append(ticket)
    print(dates_end)
    datas = {}
    estimat = {}
    for ts in dates_end.values():
        for key, t in ts.items():
            es = int(float(t["estimate"]) * 10 if t["estimate"] is not None else 0)
            if es in estimat:
                estimat[es].append(t["tps_t"])
            else:
                estimat[es] = [t["tps_t"]]
            datas[key] = t
    estimat = dict(sorted(estimat.items(), key=lambda item: item[0]))
    assert {10: [1], 20: [5], 30: [0], 40: [2, 1, 0]} == estimat

    s = (
        Scatter(
            values=datas,
            filtre="tps_t <= tps_t.quantile(.95) & tps_t >= tps_t.quantile(.05)",
        )
        .by_date()
        .build()
    )
    s.show()
