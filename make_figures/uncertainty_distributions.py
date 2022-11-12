import numpy as np
import plotly.graph_objects as go

# Local files
from .utils import read_json

app_color = {"graph_bg": "#132b57", "graph_line": "#ff4595"}


def plot_unct_distributions():

    Yfg = read_json("make_figures/data/lca_scores_1000_fg.json")
    Ybg = read_json("make_figures/data/lca_scores_1000_bg.json")
    Yfb = read_json("make_figures/data/lca_scores_1000_fb.json")

    Y_array = np.hstack([Yfg, Ybg, Yfb])
    Y_dict = {
        "foreground": Yfg,
        "background": Ybg,
        "foreground+background": Yfb,
    }

    fig = go.Figure()
    opacity = 0.8

    num_bins = 100
    bins_ = np.linspace(min(Y_array), max(Y_array), num_bins, endpoint=True)

    # # Deterministic score
    # fig.add_trace(
    #     go.Scatter(
    #         x=[deterministic_score],
    #         y=[0],
    #         mode="markers",
    #         marker_symbol="x",
    #         marker_color="red",
    #         marker_size=15,
    #         name="Deterministic LCIA score",
    #         showlegend=True,
    #     ),
    # )

    for name, Y in Y_dict.items():
        # Uncertainties distribution
        freq, bins = np.histogram(Y, bins=bins_)
        fig.add_trace(
            go.Bar(
                x=bins,
                y=freq,
                name=name,
                showlegend=True,
                opacity=opacity,
            ),
        )

    fig.update_layout(
        width=480, height=300,
        barmode='overlay',
        legend=dict(
            x=0.5, y=0.9
        ),
        margin=dict(l=0, b=0, r=0, t=0),
        plot_bgcolor=app_color["graph_bg"],
        paper_bgcolor=app_color["graph_bg"],
    )
    fig.update_xaxes(title="LCIA scores, kg CO2-eq")
    fig.update_yaxes(title="Count")

    return fig
