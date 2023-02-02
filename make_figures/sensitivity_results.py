import pandas as pd

from .utils import get_figure_layout


def plot_model_linearity(linearity=None):
    data = []
    if linearity is not None:
        data = linearity
    layout = get_figure_layout()
    layout["xaxis"]["title"].update(dict(text="Monte Carlo iterations"))
    layout["yaxis"]["title"].update(dict(text="Degree of linearity"))
    layout["height"] = 200
    return dict(data=data, layout=layout)


def plot_gsa_ranking(sensitivity_indices=None):
    data = []
    if sensitivity_indices is not None:
        data = sensitivity_indices
    layout = get_figure_layout()
    layout["xaxis"]["title"].update(dict(text="Sensitivity index"))
    layout["yaxis"]["title"].update(dict(text="Model input"))
    layout["height"] = 400
    return dict(data=data, layout=layout)


def create_table_gsa_ranking(df):
    return df


# import pandas as pd
# from dash import html
#
#
# def get_prioritized_list():
#     df = pd.read_excel("make_figures/data/GSA_results.xlsx")
#     df = df[["input_names", "output_names", "spearman"]]
#     df = df.reset_index()
#     df.columns = ["", "input", "output", "spearman"]
#     df['spearman'] = [f"{val:.3f}" for val in df['spearman']]
#     return df
#
#
# def generate_table(dataframe, max_rows=20):
#     return html.Table([
#         html.Thead(
#             html.Tr([html.Th(col) for col in dataframe.columns])
#         ),
#         html.Tbody([
#             html.Tr([
#                 html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
#             ]) for i in range(min(len(dataframe), max_rows))
#         ])
#     ])
