from .utils import get_figure_layout


def plot_validation(min_influential, max_influential, metric=None):
    data = [dict(
        type="scatter", x=[None], y=[None],
        mode="markers+lines", marker=dict(symbol="x", size=10, color="blue"),
        name="Correlation between LCIA scores when all & only influential inputs vary", showlegend=True,
    )]
    layout = get_figure_layout()
    layout["xaxis"]["title"].update(dict(text="Number of influential inputs"))
    layout["xaxis"]["range"] = [min_influential-1, max_influential+1]
    layout["yaxis"]["title"].update(dict(text="Spearman correlation"))
    layout["yaxis"]["range"] = [-0.1, 1.2]
    layout["height"] = 280
    layout["legend"].update(dict(
        x=0.5, xanchor="center",
        y=-0.43, yanchor="top",
        orientation="h"),
    )
    layout["margin"].update(dict(l=60, b=50, r=0, t=0))
    if metric is not None:
        x = list(metric.keys())
        y = list(metric.values())
        data[0]["x"] = x
        data[0]["y"] = y

    return dict(data=data, layout=layout)
