# https://matplotlib.org/stable/gallery/pie_and_polar_charts/nested_pie.html#sphx-glr-gallery-pie-and-polar-charts-nested-pie-py
from typing_extensions import Self
from charts.chart import Chart
import matplotlib.pyplot as plt
import numpy as np


class NestedPie(Chart):
    def build(self) -> Self:
        fig, ax = plt.subplots()

        size = 0.3
        # vals = np.array([[60., 32.], [37., 40.], [29., 10.]])
        # print(vals)
        vals = np.array([list(t.values()) for t in list(self._values.values())])
        print(vals)
        # labels = ('11', '22', '33')

        cmap = plt.colormaps["tab20c"]
        outer_colors = cmap(np.arange(3) * 4)
        inner_colors = cmap([1, 2, 5, 6, 9, 10])

        # ax.pie(values.values().sum(axis=1),
        ax.pie(
            vals.sum(axis=1),
            # labels=labels,
            radius=1,
            colors=outer_colors,
            wedgeprops=dict(width=size, edgecolor="w"),
            counterclock=False,
            startangle=-270,
        )

        # ax.pie(values.values().flatten(),
        ax.pie(
            vals.flatten(),
            radius=1 - size,
            colors=inner_colors,
            wedgeprops=dict(width=size, edgecolor="w"),
            counterclock=False,
            startangle=-270,
            # labels=[int(i) for i in vals.flatten()]
        )

        ax.set(aspect="equal", title="Pie plot with `ax.pie`")
        # ax.legend(wedges,
        #           title="Info",
        #           loc="center left",
        #           bbox_to_anchor=(1, 0, 0.5, 1))
        return self


def test_nested_pie():
    vals1 = {
        "": 0,
        "ToDo": 20,
        "In Progress": 30,
        "Blocked": 0,
        "In Test": 0,
        "To Integrate": 0,
        "To Test PO": 20,
        "Done": 10,
    }
    vals2 = {
        "": 0,
        "ToDo": 20,
        "In Progress": 30,
        "Blocked": 50,
        "In Test": 0,
        "To Integrate": 0,
        "To Test PO": 20,
        "Done": 10,
    }
    NestedPie(values={"Val 1": vals1, "Vals 2": vals2}).build().show()
