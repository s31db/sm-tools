from charts.chart import Chart
import matplotlib.pyplot as plt
import numpy as np
import textwrap
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
from datetime import datetime
from typing import Self


class BarHorizontal(Chart):
    _datas: dict[str, list[int]]
    _datas_dates: dict[str, list[str]] = None
    _end_date: str
    _labels: list[str]
    _colors: dict[str, str]
    _bar_label: bool = False
    _legend: bool = True
    _xlabel: str = ""
    _ylabel: str = ""
    _ylabel_width: int = 60
    _format_date: str = "%Y-%m-%d"
    _figsize: tuple[float, float] = (12, 5)

    def build(self) -> Self:

        fig, ax = plt.subplots(figsize=self._figsize)
        ax.invert_yaxis()

        if self._datas_dates:
            self.build_dates(ax)
        else:
            self.build_horizontal(ax)
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

    def build_horizontal(self, ax) -> Self:
        data = np.array(list(self._datas.values()))
        data_norm = data / data.sum(axis=1, keepdims=True)
        data_cum = data_norm.cumsum(axis=1)

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
        return self

    def build_dates(self, ax) -> Self:

        datas = self.prepare_dates()

        for y, (ticket, data) in enumerate(datas.items()):
            for col_label, start, end in data:
                rects = ax.barh(
                    y,
                    end - start,
                    left=start,
                    label=col_label,
                    color=self._colors[col_label],
                )
                width = int(rects.patches[0].get_width()) * 10
                if self._bar_label:
                    ax.text(
                        start + (end - start) / 2,
                        y,
                        textwrap.fill(col_label, width=70 if width == 0 else width),
                        ha="center",
                        va="center",
                        fontsize=10,
                        color="white",
                    )

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.xticks(rotation=45)

        ax.set_yticks(range(len(self._datas_dates.keys())))
        ax.set_yticklabels(
            [
                textwrap.fill(col_label, width=40)
                for col_label in self._datas_dates.keys()
            ]
        )

        # Legends without duplicates.
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if self._legend:
            ax.legend(by_label.values(), by_label.keys(), title="Statuts")

        plt.grid(axis="x", linestyle="--", alpha=0.5)
        return self

    def prepare_dates(self) -> dict[str, list[str]]:
        date_end = self.format_date(self._end_date)
        datas = {}
        for key, data in self._datas_dates.items():
            d = datas[key] = []
            for i in range(len(data)):
                d.append(
                    (
                        data[i][0],
                        self.format_date(data[i][1]),
                        (
                            date_end
                            if len(data) == i + 1
                            else self.format_date(data[i + 1][1])
                        ),
                    )
                )
        return datas

    def format_date(self, date_string: str) -> datetime:
        return datetime.strptime(date_string, self._format_date)


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
        bar_label=True,
    ).build().show()


def test_barhorizontal_workflow_show():
    todo = "To Do"
    progress = "In Progress"
    review = "Review"
    done = "Done"
    BarHorizontal(
        "Test BarHorizontal Workflow dates",
        end_date="2024-01-09 18:00",
        format_date="%Y-%m-%d %H:%M",
        datas_dates={
            "T1": (
                (todo, "2024-01-01 08:00"),
                (progress, "2024-01-02 10:00"),
                (review, "2024-01-03 14:00"),
                # Return to In Progress
                (progress, "2024-01-03 18:00"),
                (done, "2024-01-04 12:00"),
            ),
            "T2": (
                (todo, "2024-01-01 09:00"),
                (progress, "2024-01-02 12:00"),
                (review, "2024-01-04 16:00"),
                (done, "2024-01-05 14:00"),
            ),
        },
        colors={
            todo: "gray",
            progress: "blue",
            review: "orange",
            done: "green",
        },
        ylabel="Tickets",
        ylabel_width=20,
        legend=False,
        bar_label=True,
    ).build().show()


def test_prepare_dates():
    todo = "To Do"
    progress = "In Progress"
    review = "Review"
    done = "Done"
    bar = BarHorizontal(
        "Test prepare dates",
        end_date="2024-01-09 18:00",
        format_date="%Y-%m-%d %H:%M",
        datas_dates={
            "T1": (
                (todo, "2024-01-01 08:00"),
                (progress, "2024-01-02 10:00"),
                (review, "2024-01-03 14:00"),
                (progress, "2024-01-03 18:00"),
                (done, "2024-01-04 12:00"),
            ),
            "T2": (
                (todo, "2024-01-01 09:00"),
                (progress, "2024-01-02 12:00"),
                (review, "2024-01-04 16:00"),
                (done, "2024-01-05 14:00"),
            ),
        },
    )
    datas = bar.prepare_dates()
    assert [
        (
            todo,
            datetime(2024, 1, 1, 8, 0),
            datetime(2024, 1, 2, 10, 0),
        ),
        (
            progress,
            datetime(2024, 1, 2, 10, 0),
            datetime(2024, 1, 3, 14, 0),
        ),
        (
            review,
            datetime(2024, 1, 3, 14, 0),
            datetime(2024, 1, 3, 18, 0),
        ),
        (
            progress,
            datetime(2024, 1, 3, 18, 0),
            datetime(2024, 1, 4, 12, 0),
        ),
        (
            done,
            datetime(2024, 1, 4, 12, 0),
            datetime(2024, 1, 9, 18, 0),
        ),
    ] == datas["T1"]
    assert [
        (
            todo,
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 2, 12, 0),
        ),
        (
            progress,
            datetime(2024, 1, 2, 12, 0),
            datetime(2024, 1, 4, 16, 0),
        ),
        (
            review,
            datetime(2024, 1, 4, 16, 0),
            datetime(2024, 1, 5, 14, 0),
        ),
        (
            done,
            datetime(2024, 1, 5, 14, 0),
            datetime(2024, 1, 9, 18, 0),
        ),
    ] == datas["T2"]
