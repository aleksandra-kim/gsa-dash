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
