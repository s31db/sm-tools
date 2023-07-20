import matplotlib.pyplot as plt
import pandas as pd
from math import pi

from chart import Chart


def calc(data):
    if data.values == 'First':
        return data
    r = []
    for i in data.values:
        r.append((3 * i[0] + 2 * i[1] + i[2]) / (i[0] + i[1] + i[2]))
    return r


class Radar(Chart):

    def build(self):
        # Set data
        # df = pd.DataFrame({
        #     'group': ['First', 'Second'],
        #     'Easy to release': [2, 2],
        #     'Delivering value': [1, (3*3+2)/4],
        #     'Support': [2, 3],
        #     'Speed': [2, (3 + 3*2)/4],
        #     'Teamwork': [(3*3 + 2.5)/4, (6+2.5+2)/4],
        #     'Pawns or Player': [6/4, 2.5],
        #     'Health of codebase': [7.5/3, 2.5],
        #     'Suitable process': [2, (9+2.75)/4],
        #     'Learning': [8/3, 10/4],
        #     'Mission': [(4*3+1.5)/5, (3 + 3*2)/4],
        #     'Fun': [(3+2+1.5+1+1)/5, 2.5],
        #     'Vision claire global sprint planning': [1, 3],
        #     'S@M': [11/4, (6+4+1.5)/5],
        # })
        df = pd.DataFrame({
            # 'group': ['First', 'Second'],
            'group': ['First'],
            'Délivrer de la valeur': ((3, 4, 0),),
            'Facile à déployer': ((3, 4, 0),),
            'Amusant': ((6, 0, 0),),
            'Santé du code': ((0, 4.5, 0.5),),
            'Apprentissage': ((7, 0, 0),),
            'Mission': ((5, 0, 0),),
            'Pions ou joueurs': ((2, 4, 0),),
            'Rapidité': ((0, 4, 0),),
            'Processus Adapté': ((3, 1, 0),),
            'Support': ((5, 0, 0),),
            "Travail d'équipe": ((3, 1, 0),),
        })
        df = df.apply(calc)
        # print(df.tail(15))
        # exit(0)

        # ------- PART 1: Create background

        # number of variable
        categories = list(df)[1:]
        n_categories = len(categories)

        # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
        angles = [n / float(n_categories) * 2 * pi for n in range(n_categories)]
        angles += angles[:1]

        # Initialise the spider plot
        plt.figure(figsize=(10, 10))
        ax = plt.subplot(111, polar=True)

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

        # Ind1
        values = df.loc[0].drop('group').values.flatten().tolist()
        values += values[:1]
        ax.plot(angles, values, linewidth=1, linestyle='solid', label="Initial")
        ax.fill(angles, values, 'b', alpha=0.1)

        # Ind2
        # values = df.loc[1].drop('group').values.flatten().tolist()
        # values += values[:1]
        # ax.plot(angles, values, linewidth=1, linestyle='solid', label="Itération 16")
        # ax.fill(angles, values, 'r', alpha=0.1)

        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        return self

    def save(self, filepath: str = 'tmp/radar_health_check.png', _format: str = 'png'):
        # bytes_io_img = BytesIO()
        # plt.savefig(bytes_io_img, format='png', dpi=50)
        # bytes_io_img.seek(0)
        # return b64encode(bytes_io_img.read()).decode("utf-8")
        plt.savefig(filepath, format=_format, dpi=50)
        return self


if __name__ == '__main__':
    # print('<img src="data:image/png;base64,' + radar() + '" alt="" />')
    # put_html('<img src="data:image/png;base64,' + radar() + '" alt="" />', source='S@M')
    Radar().build().show()
