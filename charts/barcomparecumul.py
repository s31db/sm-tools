import matplotlib.pyplot as plt
import numpy as np
from charts.chart import Chart
from typing import Self


class BarcompareCumul(Chart):
    _nodes: dict[str, dict[str, tuple[float]]]
    _width_bar: float = 0.3  # the width of the bars
    _ylabel: str = "Score"
    _rotation: float | None = None
    _colors: dict[str, str] = {}
    _legend: bool = True
    _figsize: tuple[float, float] | None = None

    def nodes(self, nodes: dict[str, dict[str, tuple[float]]]) -> Self:
        self._nodes = nodes
        return self

    def width_bar(self, width_bar: float) -> Self:
        self._width_bar = width_bar
        return self

    def ylabel(self, ylabel: str) -> Self:
        self._ylabel = ylabel
        return self

    def build(self) -> Self:
        fig, ax = plt.subplots(figsize=self._figsize)
        values: dict[str, list[tuple[float]]] = {}
        for node in self._nodes.values():
            for label, v in node.items():
                if label in values:
                    values[label].append(v)
                else:
                    values[label] = [v]

        nb_values = len(values)
        nb = len(self._nodes)
        x = np.arange(nb)  # the label locations
        pos = x - self._width_bar * (nb_values - 1) / 2
        # print(self._colors)
        for label, value in values.items():
            bottom = np.zeros(nb)
            # print(label, value)
            for i in range(len(value[0])):
                vs = []
                for v in value:
                    vs.append(v[i])
                # print(label, vs)
                rect = ax.bar(
                    pos,
                    # value,
                    vs,
                    self._width_bar,
                    label=label,
                    color=self._colors.get(f"{label}_{i}", None),
                    bottom=bottom,
                    edgecolor="black",
                )
                bottom += vs
            ax.bar_label(rect, padding=3)
            pos += self._width_bar

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel(self._ylabel)
        ax.set_title(self._title)
        ax.set_xticks(x, self._nodes.keys())
        if self._rotation:
            plt.xticks(rotation=self._rotation, ha="right")
        if self._legend:
            ax.legend()
        fig.tight_layout()
        return self

    def show(self) -> Self:
        plt.show()
        return self


def test_barcompare_cumul_plan_middle_realized_with_tests():
    BarcompareCumul(
        "Scores by planned and middle and realized with Tests",
        colors={"Planned_1": "yellow", "Tests": "grey", "Done": "green"},
    ).nodes(
        {
            "Planned PI": {"Planned": [137, 25], "Tests": [15, 2], "Done": [96.5, 3]},
            "Middle PI": {"Planned": [120, 150], "Tests": [22, 3], "Done": [2, 110]},
            "Realized PI": {"Planned": [20, 143.25], "Tests": [7, 4], "Done": [124, 4]},
        }
    ).width_bar(
        0.25
    ).build().show()
