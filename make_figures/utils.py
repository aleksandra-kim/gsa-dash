import json

color_gray_hex = "#b2bcc0"
color_darkgray_hex = "#485063"
color_black_hex = "#212931"
color_light_blue = "#98def0"


def read_json(fp):
    with open(fp, 'r') as f:
        data = json.load(f)
    return data


def update_figure_style(fig):
    grid_color = color_light_blue
    bordercolor = color_darkgray_hex
    fig.update_xaxes(
        title_font_size=12,
        tickfont_size=12,
        tickfont_color="white",
        showgrid=True,
        gridwidth=1,
        gridcolor=grid_color,
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor=grid_color,
        showline=True,
        linewidth=1,
        linecolor=grid_color,
        title_font_color="white",
    )
    fig.update_yaxes(
        title_font_size=12,
        tickfont_size=12,
        tickfont_color="white",
        showgrid=True,
        gridwidth=1,
        gridcolor=grid_color,
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor=grid_color,
        showline=True,
        linewidth=1,
        linecolor=grid_color,
        title_font_color="white",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            font=dict(size=18, color="white"),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=bordercolor,
            borderwidth=0,
            x=0.5, xanchor="center",
            y=1.1, yanchor="bottom",
        ),
    )
    return fig
