import matplotlib.pyplot as plt
from io import StringIO
from charts.chart import Chart
from typing import Self


class Burndown(Chart):
    _title: str = "Burndown"
    _values: list[float]
    _dates: list[str]
    _start_is_max: bool = False
    _figsize: tuple[float, float] = (8, 4)
    _indicators: bool = True

    def title(self, title: str) -> Self:
        self._title = title
        return self

    def values(self, values: list[float]) -> Self:
        self._values = values
        return self

    def dates(self, dates: list[str]) -> Self:
        self._dates = dates
        return self

    def start_is_max(self, start_is_max: bool) -> Self:
        self._start_is_max = start_is_max
        return self

    def build(self) -> Self:
        date_limits = (self._dates[0], self._dates[-1])
        start_value = self._values[0] if self._start_is_max else max(self._values)

        fig, ax = plt.subplots(figsize=self._figsize)
        ax.set_title(self._title)
        fig.tight_layout()
        ax.plot(self._dates[: len(self._values)], self._values)
        plt.xticks(self._dates)
        ax.plot(date_limits, (start_value, 0), alpha=0.9, linewidth=0.9)
        if self._indicators:
            ax.fill_between(
                date_limits,
                (start_value, 2),
                (start_value, -3),
                alpha=0.3,
                linewidth=0,
                color="green",
                hatch="**",
            )
            ax.fill_between(
                date_limits,
                [start_value, 2],
                [start_value, 8],
                alpha=0.3,
                linewidth=0,
                color="red",
                hatch="/",
            )
            ax.fill_between(
                date_limits,
                [start_value, -3],
                [start_value, -8],
                alpha=0.2,
                linewidth=0,
                color="red",
            )

        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        ax.set_xlim(xmin=0)
        ax.grid(axis="y")
        ax.set_ylim(bottom=-0.1)
        plt.box(False)
        # fig.autofmt_xdate()
        return self

    def svg(self) -> tuple[str, Self]:
        f = StringIO()
        plt.savefig(f, format="svg")
        return f.getvalue(), self


def test_burdown() -> None:
    # assert Burndown(title4="Exple")._title4 == "Exple"
    b = (
        Burndown(title="Exple Test", start_is_max=False)
        .dates(["26/11", "28/11", "29/11", "30/11"])
        .values([15, 13])
        .build()
    )
    a = b.img64()[0]
    print(len(a))
    a = b.svg()[0]
    print(len(a))
    b.show()
