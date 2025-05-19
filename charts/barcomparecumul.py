import numpy as np
from charts.barcompare import Barcompare
from typing import Self


class BarcompareCumul(Barcompare):
    _nodes: dict[str, dict[str, tuple[float]]]

    def nodes(self, nodes: dict[str, dict[str, tuple[float]]]) -> Self:
        self._nodes = nodes
        return self

    def draw_rect(self, ax, label, nb, pos, value):
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
        return rect


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
