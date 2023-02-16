import numpy as np
from .utils import get_figure_layout


def plot_validation(influential=None, metric=None):
    data = [dict(
        type="scatter", x=[None], y=[None],
        mode="markers+lines", marker=dict(symbol="x", size=20, color="blue"),
        name="Spearman correlation", showlegend=False,
    )]
    layout = get_figure_layout()
    layout["xaxis"]["title"].update(dict(text="# influential inputs"))
    # layout["xaxis"]["range"] = [-1, influential+1]
    layout["yaxis"]["title"].update(dict(text="Spearman correlation"))
    layout["yaxis"]["range"] = [-0.1, 1.1]
    layout["height"] = 400
    layout["legend"].update(dict(
        x=0.5, xanchor="center",
        y=-0.3, yanchor="top",
        orientation="h"),
    )
    layout["margin"].update(dict(l=50, b=50, r=0, t=0))
    if metric is not None:
        print(metric)
        x = list(metric.keys())
        y = list(metric.values())
        data[0]["x"] = x
        data[0]["y"] = y

    return dict(data=data, layout=layout)
