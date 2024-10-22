import matplotlib.pyplot as plt
import numpy as np
from charts.chart import Chart
from typing import Self


class Barcompare(Chart):
    _nodes: dict[str, dict[str, float]]
    _width_bar: float = 0.3  # the width of the bars
    _ylabel: str = "Score"
    _rotation: float | None = None

    def nodes(self, nodes: dict[str, dict[str, float]]) -> Self:
        self._nodes = nodes
        return self

    def width_bar(self, width_bar: float) -> Self:
        self._width_bar = width_bar
        return self

    def ylabel(self, ylabel: str) -> Self:
        self._ylabel = ylabel
        return self

    def build(self) -> Self:
        fig, ax = plt.subplots()
        values: dict[str, list[float]] = {}
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
        for label, value in values.items():
            rect = ax.bar(pos, value, self._width_bar, label=label)
            ax.bar_label(rect, padding=3)
            pos += self._width_bar

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel(self._ylabel)
        ax.set_title(self._title)
        ax.set_xticks(x, self._nodes.keys())
        if self._rotation:
            plt.xticks(rotation=self._rotation, ha="right")
        ax.legend()
        fig.tight_layout()
        return self

    def show(self) -> Self:
        plt.show()
        return self


def test_barcompare_plan_realized():
    Barcompare("Scores by planned and realized").nodes(
        {
            "Planned PI": {"Planned": 137, "Done": 96.5},
            "Realized PI": {"Planned": 183.25, "Done": 124},
        }
    ).width_bar(0.35).build().show()


def test_barcompare_plan_middle_realized():
    Barcompare("Scores by planned and middle and realized").nodes(
        {
            "Planned PI": {"Planned": 137, "Done": 96.5},
            "Middle PI": {"Planned": 150, "Done": 110},
            "Realized PI": {"Planned": 183.25, "Done": 124},
        }
    ).build().show()


def test_barcompare_plan_middle_realized_with_tests():
    Barcompare("Scores by planned and middle and realized with Tests").nodes(
        {
            "Planned PI": {"Planned": 137, "Tests": 15, "Done": 96.5},
            "Middle PI": {"Planned": 150, "Tests": 22, "Done": 110},
            "Realized PI": {"Planned": 183.25, "Tests": 7, "Done": 124},
        }
    ).width_bar(0.25).build().show()
