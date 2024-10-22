from charts.chart import Chart
import matplotlib.pyplot as plt
import numpy as np
import textwrap
import matplotlib.ticker as mtick


class BarHorizontal(Chart):
    _datas: dict[str, list[int]]
    _labels: list[str]
    _colors: dict[str, str]
    _bar_label: bool = False
    _legend: bool = True
    _xlabel: str = ""
    _ylabel: str = ""
    _ylabel_width: int = 60

    def build(self):

        labels = [
            textwrap.fill(
                (
                    label
                    if len(label) <= self._ylabel_width * 2
                    else label[: self._ylabel_width * 2] + "..."
                ),
                width=self._ylabel_width,
            )
            for label in self._datas.keys()
        ]
        data = np.array(list(self._datas.values()))
        data_norm = data / data.sum(axis=1, keepdims=True)
        data_cum = data_norm.cumsum(axis=1)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.invert_yaxis()
        ax.set_xlim(0, np.sum(data_norm, axis=1).max())

        for i, col_label in enumerate(self._labels):
            widths = data_norm[:, i]
            starts = data_cum[:, i] - widths
            rects = ax.barh(
                labels,
                widths,
                left=starts,
                height=0.5,
                label=textwrap.fill(col_label, width=10),
                color=self._colors[col_label],
            )

            if self._bar_label:
                ax.bar_label(rects, label_type="center", color="white")
        if self._legend:
            ax.legend(
                ncols=len(self._labels),
                bbox_to_anchor=(
                    0,
                    1,
                    1,
                    0.1,
                ),
                loc="lower center",
                fontsize="small",
                frameon=False,
            )

        plt.xticks([0, 0.25, 0.5, 0.75, 1])
        ax.grid(color="grey", linestyle="-", linewidth=1, axis="x", alpha=0.7)
        ax.spines["top"].set_visible(False)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
        ax.set_xlabel(self._xlabel)
        ax.set_ylabel(self._ylabel)
        ax.set_title(
            self._title,
            loc="left",
            fontweight="normal",
            fontsize=13,
            color="grey",
            y=1.1,
            x=-0.1,
        )
        fig.tight_layout()

        return self


def test_barhorizontal_show():
    BarHorizontal(
        "Test BarHorizontal",
        datas={
            "lorem": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "ipsum": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
            "large labels information": [0, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Aenean posuere efficitur neque, eget malesuada mi.": [
                0,
                9,
                8,
                7,
                6,
                0,
                4,
                3,
                2,
                1,
            ],
            "e": [0, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            "f": [0, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        },
        labels=[
            "Month1",
            "Month2",
            "Month3",
            "Month4",
            "Month5",
            "Month6",
            "Month7",
            "Month8",
            "Month9",
            "Month10",
        ],
        colors={
            "Month1": "red",
            "Month2": "blue",
            "Month3": "green",
            "Month4": "yellow",
            "Month5": "purple",
            "Month6": "orange",
            "Month7": "black",
            "Month8": "gray",
            "Month9": "pink",
            "Month10": "brown",
        },
        xlabel="Issues",
        ylabel_width=20,
    ).build().show()
