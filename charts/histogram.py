from charts.chart import Chart
import pandas as pd
import seaborn as sns
from typing import Self


class Histogram(Chart):
    _values: dict
    _figsize: tuple[int, int] = (5, 5)

    def build(self) -> Self:
        df = pd.DataFrame(self._values.values())
        df = df.sort_values(by=["date", "estimate"])
        g = sns.displot(
            data=df,
            x="date",
            hue="estimate",
            hue_order=[0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0],
            palette={
                0.0: "grey",
                0.5: "yellow",
                1.0: "orange",
                2.0: "blue",
                3.0: "green",
                5.0: "purple",
                8.0: "brown",
                13.0: "red",
            },
            multiple="stack",
            cumulative=False,
            height=self._figsize[1],
            aspect=self._figsize[0] / self._figsize[1],
        )
        if self._title:
            g.set(title=self._title)
            g.tight_layout()
        return self


def float_to_int(value: float):
    if value is None:
        return 0
    elif float(value) % 1 == 0:
        return int(float(value))
    return value


def test_histogram():
    import json

    with open("../example/example.json", "r", encoding="utf-8") as fp:
        datas_init = json.load(fp)

    tickets = []
    dates_end = {}
    year_month_date = {"year": 4, "month": 7, "day": 10}
    for data_date, data in datas_init.items():
        for ticket, values in data.items():
            if ticket not in tickets and values["status"] in ("Done", "Closed"):
                if data_date not in dates_end:
                    dates_end[data_date] = {}
                estimate = (
                    float_to_int(values["estimate"]) if "estimate" in values else 1
                )
                dates_end[data_date][ticket] = {
                    "estimate": estimate,
                    "date": data_date[: year_month_date["month"]],
                }
                tickets.append(ticket)

    print("tickets", tickets)
    datas = {}
    for ts in dates_end.values():
        for key, t in ts.items():
            datas[key] = t
    print("dates_end", dates_end)
    print("datas", datas)
    Histogram(
        "Exemple Histogram",
        values=datas,
        filtre="tps_t <= tps_t.quantile(.95) & tps_t >= tps_t.quantile(.05)",
    ).build().show()
