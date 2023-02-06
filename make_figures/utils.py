color_gray_hex = "#b2bcc0"
color_darkgray_hex = "#485063"
color_black_hex = "#212931"
color_light_blue = "#98DEF0"
color_bs_red = "#FC3939"


def get_figure_layout():
    gridcolor = color_gray_hex
    bordercolor = color_darkgray_hex
    textcolor = color_black_hex
    layout = dict(
        xaxis=dict(
            title=dict(font=dict(size=16, color=textcolor)),
            tickfont=dict(size=16, color=textcolor),
            showgrid=True, gridwidth=1, gridcolor=gridcolor,
            zeroline=True, zerolinewidth=1, zerolinecolor=gridcolor,
            showline=True, linewidth=1, linecolor=gridcolor,
        ),
        yaxis=dict(
            title=dict(font=dict(size=16, color=textcolor)),
            tickfont=dict(size=16, color=textcolor),
            showgrid=True, gridwidth=1, gridcolor=gridcolor,
            zeroline=True, zerolinewidth=1, zerolinecolor=gridcolor,
            showline=True, linewidth=1, linecolor=gridcolor,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            font=dict(size=16, color=textcolor),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=bordercolor,
            borderwidth=1,
            x=0.5, xanchor="center",
            y=-0.3, yanchor="top",
        ),
        margin=dict(l=60, b=60, r=10, t=10)
    )
    return layout


# def update_figure_style(fig):
#     grid_color = color_light_blue
#     bordercolor = color_darkgray_hex
#     fig.update_xaxes(
#         title_font_size=12,
#         tickfont_size=12,
#         tickfont_color="white",
#         showgrid=True,
#         gridwidth=1,
#         gridcolor=grid_color,
#         zeroline=True,
#         zerolinewidth=1,
#         zerolinecolor=grid_color,
#         showline=True,
#         linewidth=1,
#         linecolor=grid_color,
#         title_font_color="white",
#     )
#     fig.update_yaxes(
#         title_font_size=12,
#         tickfont_size=12,
#         tickfont_color="white",
#         showgrid=True,
#         gridwidth=1,
#         gridcolor=grid_color,
#         zeroline=True,
#         zerolinewidth=1,
#         zerolinecolor=grid_color,
#         showline=True,
#         linewidth=1,
#         linecolor=grid_color,
#         title_font_color="white",
#     )
#     fig.update_layout(
#         paper_bgcolor="rgba(0,0,0,0)",
#         plot_bgcolor="rgba(0,0,0,0)",
#         legend=dict(
#             font=dict(size=18, color="white"),
#             bgcolor="rgba(0,0,0,0)",
#             bordercolor=bordercolor,
#             borderwidth=0,
#             x=0.5, xanchor="center",
#             y=1.1, yanchor="bottom",
#         ),
#     )
#     return fig
