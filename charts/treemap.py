import logging

from charts.chart import Chart
import plotly.express as px
from prepare_data import tree
from plotly.graph_objs import Figure
from base64 import b64encode
import numpy
from typing_extensions import Self


class Treemap(Chart):
    _title: str = "Treemap"
    _global_parent: str = "Treemap"
    _nodes: dict
    fig: Figure
    _url_server: str
    _colors: dict[str, str]
    _path_data: str
    _path_export: str
    _text_template: str
    _super: dict
    _no_estimate: bool = False

    def nodes(self, nodes: dict) -> Self:
        self._nodes = nodes
        return self

    def build(self) -> Self:
        names = [self._global_parent]
        custom_data = [""]
        custom_data_statues = [""]
        custom_data_types = [""]
        parents = [""]
        values = [0]
        ids = [""]
        colors = {"": "Blue"}

        for key, value in self._nodes.items():
            custom_data.append(key)
            custom_data_statues.append(value["status"])
            if "type" in value:
                custom_data_types.append(value["type"])
            else:
                custom_data_types.append("")
            names.append(value["name"] if "name" in value else value["Name"])
            ids.append(key)
            if "status" in value and value["status"] is not None:
                try:
                    colors[key] = self._colors[value["status"]]
                except KeyError:
                    logging.error("Unknown status: %s", value["status"])
                    colors[key] = "black"
            else:
                if "colors" in self._super:
                    colors[key] = self._super["colors"][key]
                else:
                    colors[key] = "black"
            if "father" in value:
                parents.append(value["father"])
            else:
                parents.append(self._global_parent)
            if "children" in value:
                values.append(0)
            else:
                if self._no_estimate:
                    values.append(1)
                else:
                    if "estimate" in value:
                        estimate = value["estimate"]
                        if estimate is None:
                            estimate = 1
                        values.append(estimate)
                    else:
                        values.append(1)

        self._text_template = (
            "%{label}<br>%{value}<br>"
            "<a href='" + self._url_server + "browse/%{customdata[0]}' "
            "style='color: inherit'>"
            "%{customdata[0]}</a><br>%{customdata[1]}<br>%{customdata[2]}<br>"
        )

        self.figure(
            colors,
            [custom_data, custom_data_statues, custom_data_types],
            ids,
            names,
            parents,
            values,
        )
        return self

    def figure(self, colors, custom_data, ids, names, parents, values) -> Figure:
        self.fig = px.treemap(
            names=names,
            parents=parents,
            values=values,
            ids=ids,
            color=ids,
            color_discrete_map=colors,
            title=self._title,
            # color_continuous_scale='RdBu',
        )
        self.fig.data[0].customdata = numpy.column_stack(custom_data)
        self.fig.data[0].texttemplate = self._text_template
        self.fig.update_traces(root_color="lightgrey")
        self.fig.update_layout(margin=dict(t=50, l=25, r=25, b=25), font={"size": 15})
        self.fig.update_layout(
            legend_title="Legend Title",
            showlegend=True,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )
        self.fig.data[0]["textfont"]["size"] = 11
        return self.fig

    def show(self) -> Self:
        self.fig.show()
        return self

    def img64(self, format_img: str = "png") -> tuple[str, Self]:
        img_bytes = self.fig.to_image(format=format_img)
        encoding = b64encode(img_bytes).decode()
        img_b64 = "data:image/png;base64," + encoding
        return img_b64, self

    def png(self) -> Self:
        self.fig.write_image(
            file=self._path_data + self._title + ".png",
            format="png",
            scale=1,
            width=1900,
            height=1000,
        )
        return self

    def html(self, full_html: bool = True) -> Self:
        with open(self._path_export + self._title + ".html", "w") as f:
            f.write(self.chart_html(full_html=full_html))
        return self

    def chart_html(self, full_html: bool = True) -> str:
        return self.fig.to_html(include_plotlyjs="cdn", full_html=full_html)


def test_treemap():
    import json

    with open("../example/example.json", "r", encoding="utf-8") as fp:
        datas = json.load(fp)
    date = "2022-09-03"
    n = tree.build_tree(datas[date])[1]
    t = Treemap(
        "Treemap " + date,
        nodes=n,
        url_server="",
        colors={
            "": "#858080",
            "ToDo": "#999898",
            "In Progress": "#5358ad",
            "Test": "forestgreen",
            "Done": "darkgreen",
        },
    )
    t.build()
    # t.show()
