import numpy as np

# Local files
from .utils import get_figure_layout, color_bs_red
from constants import ITERATIONS

color_deterministic_score = color_bs_red
opacity = 0.7


def plot_mc_simulations(deterministic_score=None, unit=None, mc_scores=None, iterations=ITERATIONS):
    data = []
    unit_str = ""
    data.append(dict(
        type="scatter", x=[None], y=[None],
        mode="markers", marker=dict(symbol="x", size=20, color=color_deterministic_score),
        name="Deterministic LCIA score", showlegend=True,
    ))
    data.append(dict(
        type="bar", x=[None], y=[None],
        marker=dict(color="blue", opacity=opacity),
        name="LCIA scores from Monte Carlo", showlegend=True,
        opacity=opacity,
    ))
    layout = get_figure_layout()
    layout["yaxis"]["title"].update(dict(text="Frequency"))
    layout["yaxis"]["range"] = [-int(0.02*iterations), int(0.08*iterations)]
    layout["height"] = 400
    layout["legend"].update(dict(
        x=0.5, xanchor="center",
        y=-0.3, yanchor="top",
        orientation="h"),
    )
    layout["margin"].update(dict(l=50, b=50, r=0, t=0))
    if deterministic_score is not None:
        deterministic_score = float(deterministic_score)
        data[0]["x"] = [deterministic_score]
        data[0]["y"] = [0]
        unit_str = f", {unit}"
    if mc_scores is not None:
        mc_scores = np.array(mc_scores)
        mc_scores = mc_scores[np.logical_and(
            mc_scores > np.percentile(mc_scores, 2.5),
            mc_scores < np.percentile(mc_scores, 97.5),
        )]
        num_bins = 60
        bins_ = np.linspace(min(mc_scores), max(mc_scores), num_bins, endpoint=True)
        freq, bins = np.histogram(mc_scores, bins=bins_)
        data[1]["x"] = bins
        data[1]["y"] = freq
        unit_str = f", {unit}"

    layout["xaxis"]["title"].update(dict(text=f"LCIA scores{unit_str}"))

    return dict(data=data, layout=layout)
