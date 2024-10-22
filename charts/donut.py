from typing_extensions import Self
from charts.chart import Chart
import matplotlib.pyplot as plt
import numpy as np


class Donut(Chart):
    _values = list[dict[str, float]]
    _colors: dict[str, str] = {
        "": "darkkhaki",
        "To Do": "olive",
        "ToDo": "olive",
        "In Progress": "blue",
        "Blocked": "red",
        "In Test": "palegreen",
        "To Integrate": "greenyellow",
        "To Test PO": "forestgreen",
        "Accepted": "forestgreen",
        "Done": "darkgreen",
    }

    def build(self) -> Self:
        legend = False
        nb = len(self._values)
        size = (min((15, nb * 5 + 1)), 6 + (nb - 1) // 3 * 3)
        fig, axes = plt.subplots(
            -(-nb // 3), min([nb, 3]), figsize=size, subplot_kw=dict(aspect="equal")
        )

        for i, data in enumerate(self._values):
            data = {k: v for k, v in data.items() if v > 0}
            used = []
            if nb > 3:
                ax = axes[i // min([nb, 3]), i % 3]
            elif nb > 1:
                ax = axes[i]
            else:
                ax = axes
            colors = {key: self._colors[key] for key, d in data.items() if d > 0}
            wedges, texts, autotexts = ax.pie(
                data.values(),
                center=(-20, 0),
                wedgeprops=dict(width=0.7 * 1.2),
                radius=1.2,
                startangle=-270,
                autopct=lambda pct: pct_labels(pct, data, used),
                colors=colors.values(),
                shadow=False,
                counterclock=False,
                textprops=dict(color="w"),
            )

        if nb % 3 != 0 and nb > 3:
            for n in range(i + 1, i + 1 + 3 - nb % 3):
                fig.delaxes(axes[n // min([nb, 3])][n % 3])
        if legend:
            fig.legend(
                labels=colors.keys(),
                loc="center right",
                borderaxespad=1.1,
                title="Status",
            )

            if nb == 1:
                plt.subplots_adjust(left=-0.2, wspace=0.2)
            else:
                plt.subplots_adjust(left=-0.001, wspace=0.002, hspace=0.1)

        plt.subplots_adjust(top=0.85, bottom=0.15)
        plt.setp(autotexts, size=11, weight="bold")
        return self


def pct_labels(pct, allvals, used, disp=True):
    absolute = int(np.round(pct / 100.0 * np.sum([x for x in allvals.values()])))
    v = int(absolute)
    for key, val in allvals.items():
        if val == v and key not in used:
            used.append(key)
            break
    if disp:
        return key if v > 0 else ""
    return ""


def test_donut():
    Donut(
        "test donut",
        values=[
            {
                "": 0,
                "To Do": 1,
                "In Progress": 2,
                "Blocked": 3,
                "In Test": 4,
                "Done": 5,
            }
        ],
    ).build().show()


def test_donut_3():
    Donut(
        "test donut",
        values=[
            {
                "": 0,
                "To Do": 1,
                "In Progress": 2,
                "Blocked": 3,
                "In Test": 4,
                "Done": 5,
            },
            {
                "": 0,
                "To Do": 1,
                "In Progress": 2,
                "In Test": 7,
                "Done": 5,
            },
            {
                "": 0,
                "To Do": 1,
                "Done": 10,
            },
        ],
    ).build().show()


def test_donut_4():
    Donut(
        "test donut",
        values=[
            {
                "": 0,
                "To Do": 1,
                "In Progress": 2,
                "Blocked": 3,
                "In Test": 4,
                "Done": 5,
            },
            {
                "": 0,
                "To Do": 1,
                "In Progress": 2,
                "In Test": 7,
                "Done": 5,
            },
            {
                "": 0,
                "To Do": 1,
                "Done": 10,
            },
            {
                "": 0,
                "Done": 35,
            },
        ],
    ).build().show()
