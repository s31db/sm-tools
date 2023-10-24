from charts.chart import Chart
import pandas as pd
import seaborn as sns


class Histogram(Chart):
    _values: dict

    def build(self):
        df = pd.DataFrame(self._values.values())
        df = df.sort_values(by=["date", "estimate"])
        sns.displot(
            data=df,
            x="date",
            hue="estimate",
            hue_order=[0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0],
            palette={
                0.0: "grey",
                0.5: "yellow",
                1.0: "orange",
                2.0: "blue",
                3.0: "green",
                5.0: "purple",
                8.0: "brown",
                13.0: "red",
            },
            multiple="stack",
            cumulative=False,
        )
        return self
