import numpy as np

# Local files
from .utils import get_figure_layout, color_bs_red
from constants import ITERATIONS

color_deterministic_score = color_bs_red
opacity = 0.6


def plot_mc_simulations(deterministic_score=None, unit=None, mc_scores=None, iterations=ITERATIONS):
    data = []
    unit_str = ""
    if deterministic_score is not None:
        deterministic_score = float(deterministic_score)
        data.append(dict(
            type="scatter",
            x=[deterministic_score],
            y=[0],
            mode="markers",
            marker=dict(symbol="x", size=20, color=color_deterministic_score),
            name="Deterministic LCIA score",
            showlegend=True,
        ))
        unit_str = f", {unit}"

    if mc_scores is not None:
        num_bins = 40
        bins_ = np.linspace(min(mc_scores), max(mc_scores), num_bins, endpoint=True)
        freq, bins = np.histogram(mc_scores, bins=bins_)
        data.append(dict(
            type="bar",
            x=bins,
            y=freq,
            name="LCIA scores from MC simulations",
            showlegend=True,
            opacity=opacity,
        ))
        unit_str = f", {unit}"

    layout = get_figure_layout()
    layout["xaxis"]["title"].update(dict(text=f"LCIA scores{unit_str}"))
    layout["yaxis"]["title"].update(dict(text="Frequency"))
    layout["yaxis"]["range"] = [-int(0.1*iterations), int(0.3*iterations)]

    return dict(data=data, layout=layout)
