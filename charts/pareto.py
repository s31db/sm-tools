# https://www.manager-go.com/gestion-de-projet/dossiers-methodes/la-methode-des-20-80
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import math
from chart import Chart


class Pareto(Chart):
    _title: str = 'Pareto'
    _values: dict
    _y_label: str = 'nb items'
    _pareto_items: dict
    _percent: float = 80
    _figsize: list[int] = (8, 6)
    _important_values: dict
    _margin: float = 0.25

    def title(self, title: str):
        self._title = title
        return self

    def y_label(self, y_label: str):
        self._y_label = y_label
        return self

    def values(self, values: dict):
        self._values = values
        return self

    def percent(self, percent: float):
        self._percent = percent
        return self

    def margin(self, margin: float):
        self._margin = margin
        return self

    def build(self):
        self._values = dict(sorted(self._values.items(), key=lambda item: -item[1]))
        total = sum(analyse.values())
        self._pareto_items = {}
        per_current = 0
        per_sum_previous = 0
        self._important_values = {}

        for key, value in self._values.items():
            per_current += value
            per_sum = per_current * 100 / total
            self._pareto_items[key] = {'val': value, 'per': value * 100 / total, 'per_sum': per_sum}
            # Nearly to 80 %
            # if (per_sum_previous < 75 < per_sum) or per_sum <= 80:
            if per_sum_previous <= self._percent:
                self._important_values[key] = {'val': value, 'per': value * 100 / total, 'per_sum': per_sum}
            per_sum_previous = per_sum

        fig, ax = plt.subplots(figsize=self._figsize)
        ax.set_title(self._title)

        # https://towardsdatascience.com/creating-a-dual-axis-combo-chart-in-python-52624b187834

        ax.bar(self._values.keys(), self._values.values(), width=0.5, edgecolor="white", linewidth=0.8)
        # ax.tick_params(axis='x', rotation=60)
        # https://stackoverflow.com/questions/10998621/rotate-axis-text-in-python-matplotlib
        plt.xticks(rotation=45, ha='right')
        ax.set_ylabel(self._y_label)
        ax.legend([self._y_label], loc='upper left')

        max_value = next(iter(self._values.values()))
        value_size = 10 ** int(math.log10(max_value))
        optimize_value_limit = int(math.ceil(max_value / value_size)) * value_size
        ax.set_ylim(0, optimize_value_limit)
        plt.grid(axis='y')

        ax2 = ax.twinx()
        # ax2.set_ylabel('%')
        ax2.grid(False)
        ax2.plot(self._values.keys(), [v['per_sum'] for v in self._pareto_items.values()], linewidth=1, color='red',
                 marker='s')
        ax2.legend(['%'], loc='upper right')
        ax2.set_ylim(0, 100)
        ax2.set_xlim(self._margin - 1, len(self._values.keys()) - self._margin)
        # ax2.set_yticklabels(['{:.2%}'.format(x) for x in range(0, 100, 10)])
        ax2.yaxis.set_major_formatter(ticker.PercentFormatter())

        self.build_percent(self._percent, 'orange')

        plt.subplots_adjust(bottom=0.28)
        return self

    def build_percent(self, percent, color, lw: float = 1, linestyle: str = '--'):
        nb = -1
        nearly_previous = nearly = 0
        for key, value in self._pareto_items.items():
            # Nearly to 80 %
            # if (per_sum_previous < 75 < per_sum) or per_sum <= 80:
            nearly = value['per_sum']
            if nearly <= percent:
                nb += 1
                nearly_previous = nearly
            else:
                break

        x_pos_percent = (percent - nearly_previous) / (nearly - nearly_previous)
        x_pos_percent = nb + x_pos_percent if nb > 0 else 0
        # print(nb, percent, nearly_previous, nearly)
        plt.plot([x_pos_percent, x_pos_percent], [0, percent], linestyle=linestyle, lw=lw, color=color)
        plt.plot([x_pos_percent, len(self._values.keys()) - self._margin], [percent, percent], linestyle=linestyle, lw=lw,
                 color=color)
        return self


if __name__ == '__main__':
    analyse = {'Retard transporteur': 175, 'Retard fournisseur': 36,
               'Problème qualité': 9, "Erreur d'étiquetage": 16, 'Erreur de stock': 8,
               'Erreur de saisie': 11, 'Compte client bloqué': 5, 'Colis perdu': 132, 'Client absent': 12}
    print(Pareto().values(analyse).y_label("Nb d'événements").build(
    ).build_percent(30, 'black').build_percent(90, 'pink', 2, linestyle='dotted').show().img64()[0])
