import numpy as np
import plotly.graph_objects as go

# Local files
from .utils import get_figure_layout
from constants import DEFAULT_ITERATIONS

app_color = {"graph_bg": "#132b57", "graph_line": "#ff4595"}
opacity = 0.6


def plot_mc_simulations(deterministic_score, unit, mc_scores=None, iterations=DEFAULT_ITERATIONS):
    deterministic_score = float(deterministic_score)
    data = [
        dict(
            type="scatter",
            x=[deterministic_score],
            y=[0],
            mode="markers",
            marker=dict(symbol="x", size=20, color='red'),
            name="Deterministic LCIA score",
            showlegend=True,
        )
    ]
    layout = get_figure_layout()
    layout["xaxis"]["title"].update(dict(text=unit))
    layout["yaxis"]["title"].update(dict(text="Frequency"))
    layout["yaxis"]["range"] = [-int(0.1*iterations), int(0.5*iterations)]

    if mc_scores is not None:
        num_bins = 40
        bins_ = np.linspace(min(mc_scores), max(mc_scores), num_bins, endpoint=True)
        freq, bins = np.histogram(mc_scores, bins=bins_)
        data.append(
            dict(
                type="bar",
                x=bins,
                y=freq,
                name="Scores from MC simulations",
                showlegend=True,
                opacity=opacity,
            )
        )
    return dict(data=data, layout=layout)


# def plot_unct_distributions():
#
#     Yfg = read_json("make_figures/data/lca_scores_1000_fg.json")
#     Ybg = read_json("make_figures/data/lca_scores_1000_bg.json")
#     Yfb = read_json("make_figures/data/lca_scores_1000_fb.json")
#
#     Y_array = np.hstack([Yfg, Ybg, Yfb])
#     Y_dict = {
#         "foreground": Yfg,
#         "background": Ybg,
#         "foreground+background": Yfb,
#     }
#
#     fig = go.Figure()
#     opacity = 0.8
#
#     num_bins = 100
#     bins_ = np.linspace(min(Y_array), max(Y_array), num_bins, endpoint=True)
#
#     # # Deterministic score
#     # fig.add_trace(
#     #     go.Scatter(
#     #         x=[deterministic_score],
#     #         y=[0],
#     #         mode="markers",
#     #         marker_symbol="x",
#     #         marker_color="red",
#     #         marker_size=15,
#     #         name="Deterministic LCIA score",
#     #         showlegend=True,
#     #     ),
#     # )
#
#     for name, Y in Y_dict.items():
#         # Uncertainties distribution
#         freq, bins = np.histogram(Y, bins=bins_)
#         fig.add_trace(
#             go.Bar(
#                 x=bins,
#                 y=freq,
#                 name=name,
#                 showlegend=True,
#                 opacity=opacity,
#             ),
#         )
#
#     fig.update_layout(
#         width=480, height=300,
#         barmode='overlay',
#         legend=dict(
#             x=0.5, y=0.9
#         ),
#         margin=dict(l=0, b=0, r=0, t=0),
#         plot_bgcolor=app_color["graph_bg"],
#         paper_bgcolor=app_color["graph_bg"],
#     )
#     fig.update_xaxes(title="LCIA scores, kg CO2-eq")
#     fig.update_yaxes(title="Count")
#
#     return fig
