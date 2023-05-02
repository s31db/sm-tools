import matplotlib.pyplot as plt
import numpy as np
from charts.chart import Chart


class Barcompare(Chart):

    _nodes: dict
    _width_bar: float = 0.3  # the width of the bars
    _ylabel: str = 'Score'
    _rotation: float = None

    def nodes(self, nodes: dict):
        self._nodes = nodes
        return self

    def width_bar(self, width_bar: float):
        self._width_bar = width_bar
        return self

    def ylabel(self, ylabel: str):
        self._ylabel = ylabel
        return self

    def build(self):
        fig, ax = plt.subplots()
        values = {}
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
            plt.xticks(rotation=self._rotation, ha='right')
        ax.legend()
        fig.tight_layout()
        return self

    def show(self):
        plt.show()
        return self


if __name__ == '__main__':
    Barcompare('Scores by planned and realized').nodes({
        'Planned PI':  {'Planned': 137, 'Done': 96.5}, 'Realized PI': {'Planned': 183.25, 'Done': 124}
    }).width_bar(0.35).build().show()
    # Bar('Scores by planned and middle and realized').nodes({
    #     'Planned PI': {'Planned': 137, 'Done': 96.5}, 'Middle PI': {'Planned': 150, 'Done': 110},
    #     'Realized PI': {'Planned': 183.25, 'Done': 124}
    # }).build().show()
    Barcompare('Scores by planned and middle and realized with Tests').nodes({
        'Planned PI': {'Planned': 137, 'Tests': 15, 'Done': 96.5},
        'Middle PI': {'Planned': 150, 'Tests': 22, 'Done': 110},
        'Realized PI': {'Planned': 183.25, 'Tests': 7, 'Done': 124}
    }).width_bar(0.25).build().show()
