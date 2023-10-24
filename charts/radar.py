import matplotlib.pyplot as plt
import pandas as pd
from math import pi
from typing import Sequence

from matplotlib.projections.polar import PolarAxes

from charts.chart import Chart


def calc(data):
    if type(data.values[0]) is str:
        return data
    r = []
    for i in data.values:
        r.append((3 * i[0] + 2 * i[1] + i[2]) / (i[0] + i[1] + i[2]))
    return r


class Radar(Chart):
    def build(self, df: pd.DataFrame):
        df = df.apply(calc)

        # ------- PART 1: Create background

        # number of variable
        categories: Sequence[str] = tuple(df)[2:]  # type: ignore
        n_categories = len(categories)

        # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
        angles = [n / float(n_categories) * 2 * pi for n in range(n_categories)]
        angles += angles[:1]

        # Initialise the spider plot
        plt.figure(figsize=(10, 10))
        ax: PolarAxes = plt.subplot(111, polar=True)  # type: ignore

        # If you want the first axis to be on top:
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)

        # Draw one axe per variable + add labels
        plt.xticks(angles[:-1], categories)

        # Draw ylabels
        ax.set_rlabel_position(0)
        plt.yticks([1, 2, 3], ["red", "orange", "green"], color="grey", size=7)
        plt.ylim(0, 3.5)

        # ------- PART 2: Add plots

        # Plot each individual = each line of the data
        # I don't make a loop, because plotting more than 3 groups makes the chart unreadable
        for i in df.index:
            loc = df.loc[i]
            values = loc.drop("group").drop("color").to_numpy().flatten().tolist()
            values += values[:1]
            ax.plot(angles, values, linewidth=1, linestyle="solid", label=loc.group)
            ax.fill(angles, values, loc.color, alpha=0.1)

        # Add legend
        plt.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1))
        return self


def test_squad_health_check():
    df = pd.DataFrame(
        {
            "group": ["First"],
            "color": ["b"],
            "Délivrer de la valeur": ((3, 4, 0),),
            "Facile à déployer": ((3, 4, 0),),
            "Amusant": ((6, 0, 0),),
            "Santé du code": ((0, 4.5, 0.5),),
            "Apprentissage": ((7, 0, 0),),
            "Mission": ((5, 0, 0),),
            "Pions ou joueurs": ((2, 4, 0),),
            "Rapidité": ((0, 4, 0),),
            "Processus Adapté": ((3, 1, 0),),
            "Support": ((5, 0, 0),),
            "Travail d'équipe": ((3, 1, 0),),
        }
    )
    Radar().build(df).show()


def test_kanban():
    df = pd.DataFrame(
        {
            # 'group': ['First', 'Second'],
            "group": ["Temps 1", "Temps 2"],
            "color": ["b", "r"],
            "Visualiser": ((3, 4, 0), (6, 4, 0)),
            "Limiter le travail en cours": ((6, 0, 0), (7, 4, 0)),
            "Gérer et mesurer le flux de travail": ((7, 0, 0), (8, 4, 0)),
            "Rendre explicite les règles de gestion des processus": (
                (6, 0, 0),
                (3, 4, 0),
            ),
            "Implémenter des boucles de feedbacks": ((3, 4, 0), (6, 4, 0)),
            "S'améliorer de manière collaborative": ((0, 4.5, 0.5), (2, 4, 0)),
        }
    )
    # Radar().build(df).save("tmp/radar_health_check.png").show()
    Radar().build(df).save("tmp/radar_health_check.png")
    # Radar().build(df).show()
