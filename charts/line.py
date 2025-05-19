from charts.chart import Chart
import matplotlib.pyplot as plt


class Line(Chart):
    _datas: dict[str, list[int]]
    _datas_dates: dict[str, list[str]] | None = None
    _end_date: str
    _colors: dict[str, str]
    _bar_label: bool = False
    _legend: bool = True
    _xlabel: str = ""
    _ylabel: str = ""
    _ylabel_width: int = 60
    _figsize: tuple[float, float] | None = None

    def build(self):

        fig, ax = plt.subplots(figsize=self._figsize)
        for label, data in self._datas.items():
            ax.plot(
                data,
                label=label,
            )
        ax.set_title(
            self._title,
            loc="left",
            fontweight="normal",
            fontsize=13,
            color="grey",
            y=1.1,
        )
        if self._legend:
            ax.legend()
        fig.tight_layout()
        return self


def test_line_show():
    Line(
        "Test Line",
        datas={
            "Test line lorem": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "Test line ipsum": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
            "Test line large labels information": [0, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            "Test line Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Test line Aenean posuere efficitur "
            "neque, eget malesuada mi.": [0, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            "Test line e": [0, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            "Test line f": [0, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        },
        xlabel="level",
        ylabel_width=20,
        bar_label=True,
        figsize=(12, 5),
    ).build().show()
