import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt


from charts.chart import Chart


class Scatter(Chart):
    _values: dict
    _legend: str | bool
    _percent: dict = {0.5: 'blue', 0.75: 'green', 0.85: 'red'}
    _xtick: list
    _x: str
    _y: str
    _size: str
    _size_order: list
    _hue: str
    _hue_order: list
    _style: str
    _style_order: list
    _palette: str
    _ncol_legend: int
    _filtre: str

    def by_date(self):
        self._x = 'date'
        self._y = 'tps_t'
        self._xtick = None
        self._size = None
        # self._size = 'estimate'
        self._size_order = None
        # self._size_order = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0]
        self._hue = None
        # self._hue = 'estimate'
        self._hue_order = None
        # self._hue_order = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0]
        self._style = None
        self._style_order = None
        self._palette = None
        self._legend = 'full'
        self._legend = None
        # self._ncol_legend = len(self._hue_order) + 1
        # self._ncol_legend = len(self._size_order) + 1
        return self

    def by_estimate(self):
        self._x = 'estimate'
        self._y = 'tps_t'
        self._xtick = [0, 0.5, 1, 2, 3, 5, 8, 13]
        self._size = None
        self._size_order = None
        self._hue = None
        self._hue_order = None
        self._style = None
        self._style_order = None
        self._palette = 'muted'
        self._legend = False
        self._ncol_legend = None
        return self

    def build(self):
        sns.set_theme(style="white")

        d = pd.DataFrame(self._values.values())
        if self._filtre:
            d = d.query(self._filtre)
        print(d.head())

        g = sns.relplot(
            x=self._x,
            y=self._y,
            hue=self._hue,
            size=self._size,
            style=self._style,
            hue_order=self._hue_order,
            size_order=self._size_order,
            style_order=self._style_order,
            sizes=(40, 400),
            alpha=.5, palette=self._palette,
            height=6, data=d, legend=self._legend)

        if self._xtick:
            plt.xticks(self._xtick)
        plt.xlim(-0.5)

        xtick = plt.gca().get_xticks()
        ylim = xtick[-1] + 0.1

        if self._legend:
            sns.move_legend(g, "upper center", bbox_to_anchor=(.5, 1), ncol=self._ncol_legend, frameon=True)

        for percent, color in self._percent.items():
            percent_val = d[self._y].quantile(percent)
            plt.plot([-0.5, ylim], [percent_val, percent_val], linewidth=1, color=color, linestyle='--')
            plt.text(ylim + 0.2, percent_val, "percent " + str(int(percent * 100)),
                     horizontalalignment='left', size='medium', color=color, weight='semibold')

        return self

