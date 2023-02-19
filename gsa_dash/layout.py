import os
from dash import dcc, html, DiskcacheManager, CeleryManager, dash_table
import bw2data as bd
import dash_bootstrap_components as dbc
from make_figures import plot_mc_simulations, plot_model_linearity, create_table_gsa_ranking, plot_validation
from constants import (
    ITERATIONS, SEED, INTERVAL_TIME, LINEARITY_THRESHOLD, PAGE_SIZE,
    VALIDATION_MIN, VALIDATION_MAX, VALIDATION_STEP, VALIDATION_ITERATIONS
)

color_even = "rgb(222, 221, 232, 0.5)"
color_odd = "#FBFAF1"
color_none = "rgba(0,0,0,0)"
color_light_purple = "rgb(175, 144, 193, 0.6)"
color_blue = "rgba(0, 0, 255, 0.5)"


def create_background_callback_manager():
    if 'REDIS_URL' in os.environ:
        # Use Redis & Celery if REDIS_URL set as an env variable
        from celery import Celery
        celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
        background_callback_manager = CeleryManager(celery_app)
    else:
        # Diskcache for non-production apps when developing locally
        import diskcache
        cache = diskcache.Cache("./cache")
        background_callback_manager = DiskcacheManager(cache)
    return background_callback_manager


def create_layout():
    layout = html.Div([
        get_header(),
        get_top_controls(),
        get_tabs(),
    ])
    return layout


def get_header():
    header = html.Header([
        html.H1("Global Sensitivity Analysis Of Life Cycle Assessment"),
        html.H3("the complete story in one dashboard")
    ], className="d--header")
    return header


def get_top_controls():
    projects = [p.name for p in bd.projects]
    top_controls = html.Div([
        html.Div([
            html.Div([
                html.Label("Project", className="label"),
                dcc.Dropdown(projects, id="project"),
            ], className="control-project"),
            html.Div([
                html.Label("Database", className="label"),
                dcc.Dropdown([], id="database"),
            ], className="control-database"),
            html.Div([
                html.Label("Activity", className="label"),
                dcc.Dropdown([], id="activity"),
            ], className="control-activity"),
            html.Div([
                html.Label("Amount", className="label"),
                dbc.Input(id="amount", value=1, type="number", min=0)
            ], className="control-amount"),
            html.Div([
                html.Label("Method", className="label"),
                dcc.Dropdown([], id="method"),
            ], className="control-method"),
            html.Div([
                html.Label("LCIA score", className="label"),
                html.Div([
                    html.Span(id="score", className="score"),
                    html.Span(id="method-unit", className="method-unit")
                ], className="score-unit")
            ], className="output-lcia"),
            # html.Div(children=dbc.Spinner(color="primary"), id="loading")
        ], className="top-controls-container"),
    ], className="top-controls")
    return top_controls


def get_tabs():
    tab1_content = get_tab_motivation()
    tab2_content = get_tab_uncertainty_propagation()
    tab3_content = get_tab_sensitivity_analysis()
    tab4_content = get_tab_gsa_validation()
    # tab5_content = get_tab_summary()
    tabs = dbc.Tabs(
        active_tab="tab-motivation",
        children=[
            dbc.Tab(tab1_content, className="tab-content", label="Motivation", tab_id="tab-motivation"),
            dbc.Tab(tab2_content, className="tab-content", label="Uncertainty propagation", tab_id="tab-propagation"),
            dbc.Tab(tab3_content, className="tab-content", label="Global sensitivity analysis"),
            dbc.Tab(tab4_content, className="tab-content", label="GSA validation"),
            # dbc.Tab(tab5_content, className="tab-content", label="Summary"),
        ],
        className="tabs-container"
    )
    return tabs


def get_tab_motivation():
    tab = html.Div([
        html.H4([
            "This dashboard attempts to combine the motivation behind",
            html.Br(),
            "Global Sensitivity Analysis of Life Cycle Assessment, ",
            html.Br(),
            "with necessary computations and visualization of the results - all in one place."],
            style={"marginBottom": "40px", "color": "#FF5C00", "textAlign": "center", "lineHeight": 1.6,
                   "fontWeight": 520}),
        html.H2("So... what is life cycle assessment?"),
        dcc.Markdown(
            '''
            __Life Cycle Assessment (LCA)__ is a methodology for assessing environmental impacts associated with all the 
            stages of the life cycle of a product, process or service. For instance, the impacts for manufacturing 
            a product are assessed from raw material extraction and processing (cradle), through the product's 
            manufacture, distribution and use, to the recycling or final disposal of the materials composing it (grave).
            ''',
            style={"marginBottom": "16px"}
        ),
        dcc.Markdown(
            '''
            LCA models are based on the analysis of complex supply chains and environmental processes. Naturally, 
            they contain numerous uncertainties that can affect the interpretation of LCA results, and reduce our 
            confidence in the environmental impact estimates.
            ''',
            style={"marginBottom": "40px"}
        ),
        html.H2("What can we do with the uncertainties?"),
        dcc.Markdown(
            '''
            At the very least, we can try to understand how much they affect LCA results. For that, we conduct 
            __uncertainty analysis__ by first propagating uncertainties from LCA model inputs to the output, and then 
            analyzing the resulting distribution of Life Cycle Impact Assessment (LCIA) scores and robustness of the LCA.
            ''',
            style={"marginBottom": "40px"}
        ),
        html.H2("Why is global sensitivity analysis needed?"),
        html.P([
            "For the following reasons:",
            dcc.Markdown(
                "&nbsp $\\circ$ &nbsp it allows us to understand the main uncertainty drivers in LCA models;",
                mathjax=True,
            ),
            dcc.Markdown(
                "&nbsp $\\circ$ &nbsp it helps in prioritizing data collection, which eventually can reduce the overall uncertainty;",
                mathjax=True,
            ),
            dcc.Markdown(
                "&nbsp $\\circ$ &nbsp it supports improved modelling of most important processes.",
                mathjax=True, style={"marginBottom": "16px"}
            ),
        ]),
        dcc.Markdown(
            '''
            Formally, __sensitivity analysis__ is the study of how the uncertainty in the output of a model or system can be 
            allocated to different sources of uncertainty in its inputs.
            ''',
            style={"marginBottom": "16px"}
        ),
        html.P([
            "It refers to a family of methods that can determine, which varying or uncertain model inputs",
            dcc.Markdown(
                "&nbsp $\\circ$ &nbsp are __influential__, meaning that they lead to most significant changes in the model output;",
                mathjax=True,
            ),
            dcc.Markdown(
                "&nbsp $\\circ$ &nbsp are __non-influential__, namely, they can be fixed to any value in their range  "
                "without significantly affecting the model output.",
                mathjax=True, style={"marginBottom": "16px"}
            ),
        ]),
        dcc.Markdown(
            '''
            __Global Sensitivity Analysis (GSA)__ means that the effect on the model output is studied by varying all 
            model inputs simultaneously, as opposed to the __local sensitivity analysis__, where each input is varied 
            one at a time. In LCA it is common to use the local analysis due to its simplicity, even though it is 
            only suitable for linear models.
            ''',
            style={"marginBottom": "40px"}
        ),
        html.H2("What is an LCA model?"),
        dcc.Markdown(
            '''The matrix-based LCA model can be expressed as &nbsp $y = CBT^{-1}d$, &nbsp where''',
            mathjax=True, style={"marginBottom": "16px"}
        ),
        html.Table([
            html.Tr([
                html.Td(dcc.Markdown("$d \\in \\mathbb{R}^{n}$", mathjax=True)),
                html.Td(dcc.Markdown("Final demand vector")),
                html.Td(dcc.Markdown("Selects the products, whose environmental impacts we aim to estimate.")),
            ]),
            html.Tr([
                html.Td(dcc.Markdown("$T \\in \\mathbb{R}^{n \\times n}$", mathjax=True)),
                html.Td(dcc.Markdown("Technology / &nbsp &nbsp &nbsp Technosphere matrix")),
                html.Td(dcc.Markdown("Stores information about energy, material and waste flows of the considered $n$ "
                                     "manufacturing processes. Each element in the matrix is called an intermediate "
                                     "exchange.", mathjax=True)),
            ]),
            html.Tr([
                html.Td(dcc.Markdown("$B\\in \\mathbb{R}^{m \\times n}$", mathjax=True)),
                html.Td(dcc.Markdown("Intervention / &nbsp &nbsp &nbsp Biosphere matrix")),
                html.Td(dcc.Markdown("Contains $m$ resources and emissions needed for or resulting from $n$ manufacturing "
                                     "processes. Each element in the matrix is called an elementary exchange or "
                                     "environmental flow.", mathjax=True)),
            ]),
            html.Tr([
                html.Td(dcc.Markdown("$C\\in \\mathbb{R}^{p \\times m}$", mathjax=True)),
                html.Td(dcc.Markdown("Characterization matrix")),
                html.Td(dcc.Markdown("Consists of characterization factors that weigh $m$ resources and emissions to "
                                     "compute environmental impacts for $p$ impact categories.", mathjax=True)),
            ]),
            html.Tr([
                html.Td(dcc.Markdown("$y\\in \\mathbb{R}^{p}$", mathjax=True)),
                html.Td(dcc.Markdown("Impact scores")),
                html.Td(dcc.Markdown("Life cycle impact assessment (LCIA) results for $p$ impact categories.", mathjax=True)),
            ]),
        ], style={"marginBottom": "16px"}),
        dcc.Markdown(
            '''
            For the sake of GSA we think of this model as &nbsp $y = f(\\mathbf{x}) = f(x_1, x_2, ..., x_k)$, &nbsp where 
            &nbsp $\\mathbf{x} \\in \\mathbb{R}^{k}$ &nbsp is the vector of $k$ uncertain model inputs. Here we only consider 
            __parameter uncertainty__, and define as LCA model inputs uncertain intermediate exchanges, environmental flows and 
            characterization factors.
            ''',
            mathjax=True, style={"marginBottom": "16px"}
        ),
    ], className="tab-motivation")
    return tab


def get_tab_uncertainty_propagation():
    fig = plot_mc_simulations()
    mc_controls = get_mc_controls()
    progress = get_progress()
    tab = html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.H2("Uncertainty propagation"),
                dcc.Markdown(
                    '''
                    In statistics, propagation of uncertainty (or propagation of error) is the effect of
                    inputs' uncertainties on the uncertainty of a function $y = f(\\mathbf{x}) = f(x_1, x_2, ..., x_k)$ 
                    based on them. It can be conducted analytically using formulas or numerically with `Monte Carlo (MC) 
                    simulations`. In LCA, it is common to use the latter. 
                    ''',
                    mathjax=True, style={"marginBottom": "16px"}
                ),
                html.P(html.Img(
                    src="https://raw.githubusercontent.com/aleksandra-kim/gsa-dash/a0a4c318b84cfe56032381fce8299b6d7450df85/latex_images/monte_carlo.svg",
                    style={"width": "95%"}
                    ),
                    style={"marginBottom": "16px", "textAlign": "center"}
                ),
                dcc.Markdown(
                    '''
                    For each simulation, random samples are drawn from the predefined input distributions, and 
                    LCIA scores are computed. The user can define number of `iterations N` and `random seed` to ensure 
                    reproducibility of random samples.                     
                    ''',
                    style={"marginBottom": "16px"}
                ),
            ]), width=5, align="start"),
            dbc.Col(html.Div([
                html.H2("Monte Carlo simulations"),
                html.P(
                    "Define LCA study in the menu above, then start MC simulations!",
                    style={"marginBottom": "16px", "textAlign": "center"}
                ),
                mc_controls,
                progress,
                dcc.Graph(id='mc-graph', figure=fig),
            ]), width=6, align="start"),
        ], justify="evenly"),
    ], className="tab-propagation")
    return tab


def get_mc_controls():
    mc_controls = html.Div([
        html.Div([
            html.Div([
                html.Label("Iterations", className="label"),
                dbc.Input(id="iterations", value=ITERATIONS, type="number")
            ], className="control-iterations"),
            html.Div([
                html.Label("Iterations chunk", className="label"),
                dbc.Input(id="iterations-chunk", value=ITERATIONS // 10, type="number")
            ], className="control-iterations-chunk"),
            html.Div([
                html.Label("Random seed", className="label"),
                dbc.Input(id="seed", value=SEED, type="number")
            ], className="control-random-seed"),
            dcc.Store(id="directory"),
            dcc.Store(id="mc-state", data=0),
            dcc.Store(id="mc-finished", data=False),
            dbc.Button("Start", id="btn-start-mc", n_clicks=0, outline=False, color="primary",
                       className="btn-start-mc"),
            dbc.Button("Cancel", id="btn-cancel-mc", n_clicks=0, outline=False, color="warning",
                       className="btn-cancel-mc"),
        ], className="mc-controls-container")
    ], className="mc-controls")
    return mc_controls


def get_progress():
    progress = html.Div([
        html.Label("Progress:"),
        dcc.Interval(id="mc-interval", n_intervals=0, interval=INTERVAL_TIME * 1000),
        dbc.Progress(id="mc-progress", className="mc-progress", value=0, label="0%"),
    ], className="mc-progress-container")
    return progress


def get_tab_sensitivity_analysis():
    fig_model_linearity = plot_model_linearity(linearity_threshold=LINEARITY_THRESHOLD, iterations_default=ITERATIONS)
    df = create_table_gsa_ranking()
    df_data = df.to_dict("records")
    columns = [{"name": i, "id": i} for i in df.columns]
    tab = html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.H2("Global sensitivity analysis"),
                dcc.Markdown(
                    '''
                    For each model input, we compute _sensitivity index_ - quantitative measure of input's importance. 
                    Widely used indices are correlation coefficients, Sobol indices, Shapley values, delta indices. 
                    ''',
                    style={"marginBottom": "16px"}
                ),
                dcc.Markdown(
                    '''
                    Typically, sensitivity indices for LCA models are computed numerically based on MC simulations.
                    More simulations yield better convergence of the sensitivity indices estimates.
                    ''',
                    style={"marginBottom": "16px"}
                ),
                html.P(html.Img(
                    src="https://raw.githubusercontent.com/aleksandra-kim/gsa-dash/e1bb64fafda45efa0f7363baf8f8bff53166c8fd/latex_images/sensitivity_indices_v3.svg",
                    style={"width": "70%"}
                    ),
                    style={"marginBottom": "16px", "textAlign": "center"}
                ),
                dcc.Markdown(
                    '''
                    Which GSA method to use depends on its underlying assumptions, one of the important one being the 
                    `degree of model linearity`.
                    '''
                ),
            ]), width=5, align="start"),
            dbc.Col(html.Div([
                html.H2("LCA model linearity"),
                dcc.Markdown(
                    '''
                    General LCA model is linear with respect to environmental flows and characterization 
                    factors, and non-linear in intermediate exchanges. 
                    ''',
                    mathjax=True, style={"marginBottom": "16px"}
                ),
                dcc.Markdown(
                    '''
                    Linearity of a particular model can be determined with standardized linear regression coefficients. 
                    If linear regression explains LCA model outcomes well (linearity $>$ chosen `linearity threshold`), 
                    then the model is considered sufficiently linear and correlation coefficients are used. Otherwise, 
                    the dashboard computes feature importance indices from the gradient boosted tree method.
                    ''',
                    mathjax=True, style={"marginBottom": "16px"}
                ),
                dcc.Markdown(
                    '''
                    Linearity also depends on the number of MC simulations, as shown below:
                    ''',
                    mathjax=True, style={"marginBottom": "16px"}
                ),
                dcc.Graph(id='linearity-graph', figure=fig_model_linearity, className="linearity-graph"),
            ]), width=6, align="start"),
        ], justify="evenly", className="row-gsa", style={"marginBottom": "60px"}),
        dbc.Col(html.H2("Influential model inputs, aka GSA results")),
        dbc.Row([
            dcc.Markdown(
                    '''
                    The table below lists influential model inputs, ranked with GSA. It also shows the contributions of
                    each model input to the total deterministic LCIA score to show what is important in the
                    deterministic LCA model. Note that __inputs with low contributions might still be influential in the 
                    GSA sense__, in case they have wide uncertainty distribution or depending on how they interact with 
                    other varying inputs. While contribution analysis helps interpret the results, it is important to 
                    remember about its static nature, as compared to GSA, where uncertainty in inputs is the key. 
                    ''',
                mathjax=True, style={"marginBottom": "16px", "width": "100%"}
                ),
            dbc.Col(
                dash_table.DataTable(
                    data=df_data, columns=columns, id="ranking-table", page_size=PAGE_SIZE, sort_action='native',
                    style_table={"font-family": "sans-serif", "borderBottom": f'1px solid {color_light_purple}',
                                 'textOverflow': 'ellipsis'},
                    style_header={'backgroundColor': f'{color_light_purple}', 'textAlign': 'center',
                                  "font-family": "sans-serif", "font-size": "16px", "font-weight": 550,
                                  "color": "black"},
                    style_cell={"backgroundColor": color_none, 'textAlign': 'left', 'whiteSpace': 'pre-line',
                                'overflow': 'hidden', 'textOverflow': 'ellipsis'},
                    style_cell_conditional=[
                        {'if': {'column_id': 'Rank'}, 'width': '7%', 'textAlign': 'center'},
                        {'if': {'column_id': 'LCA model input'}, 'width': '40%'},
                        {'if': {'column_id': 'Amount'}, 'width': '13%'},
                        {'if': {'column_id': 'Type'}, 'width': '10%'},
                        {'if': {'column_id': 'GSA index'}, 'width': '15%'},
                        {'if': {'column_id': 'Contribution'}, 'width': '15%'},
                    ],
                    style_data={"border": '1px solid white', "font-family": "sans-serif",
                                'height': 'auto', 'lineHeight': '19px', 'textOverflow': 'ellipsis'},
                    style_data_conditional=get_style_data_conditional(color_even),
                ),
            ),
        ], justify="evenly", className="row-gsa"),
        dcc.Store(id='sensitivity-indices'),
    ], className="tab-sensitivity", style={"width": "1460px"})
    return tab


def get_style_data_conditional(bg_color):
    style_data_conditional = [
        {'if': {'row_index': "even"}, 'backgroundColor': f'{bg_color}'},
        {'if': {'column_id': 'Amount'}, 'textAlign': 'left'},
        {'if': {'column_id': 'GSA index'}, 'textAlign': 'right'},
        {'if': {'column_id': 'Contribution'}, 'textAlign': 'right'},
    ]
    return style_data_conditional


def style_bars_in_datatable(df, column, color_bars=color_blue, bar_percentage_in_cell=70):
    styles = get_style_data_conditional(color_even)
    values = df[column].values
    max_value = values.max()
    for i, val in enumerate(values):
        color_row = color_even if i % 2 == 0 else color_odd
        max_bound_percentage = int(val/max_value * bar_percentage_in_cell)
        style_element = {
            'if': {
                'filter_query': '{{column}} = {{val}} && {{Rank}}={i}'.format(column=column, val=val, i=i+1),
                'column_id': column,
            },
            'background': (
                f"""
                    linear-gradient(90deg,
                    {color_bars} 0%,
                    {color_bars} {max_bound_percentage}%,
                    {color_row} {max_bound_percentage}%,
                    {color_row} 100%)
                """
            ),
            'paddingBottom': 2, 'paddingTop': 2
        }
        styles.append(style_element)
    return styles


def get_tab_gsa_validation():
    fig = plot_validation(min_influential=VALIDATION_MIN, max_influential=VALIDATION_MAX)
    val_controls = get_validation_controls()
    tab = html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.H2("Validation of GSA results"),
                dcc.Markdown(
                    '''
                    Since the quality of sensitivity indices estimates depends on the number of MC simulations, it is 
                    necessary to ensure their sufficient convergence. Here the goal was to determine the main 
                    uncertainty drivers, therefore we compare the following:
                    ''',
                    mathjax=True, style={"marginBottom": "16px"}
                ),
                html.Table([
                    html.Tr([
                        html.Td(
                            dcc.Markdown('''$\\bullet$ LCIA scores when all model inputs vary;''', mathjax=True),
                            style={"width": "40%", "verticalAlign": "top"}
                        ),
                        html.Td(html.Img(
                            src="https://raw.githubusercontent.com/aleksandra-kim/gsa-dash/993ea4be4ae182729736c618b4a56ace4009a3b1/latex_images/validation_all.svg",
                            style={"width": "100%"}
                        ), style={"width": "45%"}),
                    ], style={"border": 0}),
                    html.Br(),
                    html.Tr([
                        html.Td([
                            dcc.Markdown(
                                '''
                                $\\bullet$ LCIA scores when influential inputs vary such that they take the same values 
                                as in the above case, while the non-influential inputs are set to their prescribed values.
                                ''',
                                mathjax=True, style={"marginBottom": "80px"},
                            ),
                        ],  style={"verticalAlign": "top"}),
                        html.Td(html.Img(
                            src="https://raw.githubusercontent.com/aleksandra-kim/gsa-dash/993ea4be4ae182729736c618b4a56ace4009a3b1/latex_images/validation_inf.svg",
                            style={"width": "100%"}
                        )),
                    ], style={"marginBottom": "16px", "border": 0}),
                    html.Br(),
                ]),
                dcc.Markdown(
                    '''                                
                    If the correlation between $Y_{\\text{all}}$ and $Y_{\\text{inf}}$ is close to 1, it 
                    means that by varying only influential inputs, the overall LCIA scores distribution is
                    reasonably captured. Hence, the influential inputs were identified correctly. Otherwise, more MC 
                    simulations are needed.
                    ''',
                    mathjax=True
                ),
            ]), width=6, align="start"),
            dbc.Col(html.Div(
                [
                    html.H2("MC simulations for GSA validation"),
                    dcc.Markdown(
                        '''
                        To determine how many inputs capture the overall LCIA scores distribution sufficiently, we run 
                        additional MC simulations for the increasing number of ranked influential inputs. Specify below 
                        the minimum, maximum and step for the number of influential inputs to test.
                        ''',
                        style={"marginBottom": "16px", "textAlign": "center"}
                    ),
                ] +
                val_controls +
                [dcc.Graph(id='val-graph', figure=fig, className="val-graph")]
            ), width=5, align="start"),
        ], justify="evenly"),
    ], className="tab-validation")
    return tab


def get_validation_controls():
    slider_inputs = html.Div([
        html.Div([
            html.Label("Inputs min", className="label"),
            dbc.Input(id="val-min", value=VALIDATION_MIN, type="number")
        ], className="val-min"),
        html.Div([
            html.Label("Inputs max", className="label"),
            dbc.Input(id="val-max", value=VALIDATION_MAX, type="number")
        ], className="val-max"),
        html.Div([
            html.Label("Inputs step", className="label"),
            dbc.Input(id="val-step", value=VALIDATION_STEP, type="number")
        ], className="val-step"),
    ], className="val-controls-container")
    # slider = html.Div(html.Div(
    #         dcc.RangeSlider(
    #             VALIDATION_MIN, VALIDATION_MAX, VALIDATION_STEP, value=[VALIDATION_MIN, VALIDATION_MAX],
    #             id='val-slider', className="val-slider",
    #         ), className="val-controls-container"
    #     ), className="val-controls"
    # )
    iterations_inputs = html.Div([
        html.Div([
            html.Label("Iterations", className="label"),
            dbc.Input(id="val-iterations", value=VALIDATION_ITERATIONS, type="number")
        ], className="val-iterations"),
        dbc.Button("Start", id="btn-start-val", n_clicks=0, outline=False, color="primary",
                   className="btn-start-val"),
        dbc.Button("Cancel", id="btn-cancel-val", n_clicks=0, outline=False, color="warning",
                   className="btn-cancel-val"),
        dcc.Store(id="val-directory"),
        dcc.Store(id="val-state", data=0),
        dcc.Store(id="val-finished", data=False),
        dcc.Interval(id="val-interval", n_intervals=0, interval=INTERVAL_TIME * 1000),
    ], className="val-controls-container")
    val_controls = [slider_inputs, iterations_inputs]
    return val_controls


def get_tab_summary():
    tab = dbc.Card(
        dbc.CardBody(
            [
                html.H2("Summary"),
                dbc.Button("Don't click here", color="danger"),
            ]
        ),
    )
    return tab


def get_lca_config(state_or_input):
    lca_config = dict(
        project=state_or_input('project', 'value'),
        database=state_or_input("database", "value"),
        activity=state_or_input('activity', "value"),
        amount=state_or_input('amount', "value"),
        method=state_or_input("method", "value"),
    )
    return lca_config


def get_mc_config(state_or_input):
    mc_config = dict(
        iterations=state_or_input('iterations', 'value'),
        iterations_chunk=state_or_input('iterations-chunk', 'value'),
        seed=state_or_input("seed", "value"),
    )
    return mc_config


def get_lca_mc_config(state_or_input):
    lca_config = get_lca_config(state_or_input)
    mc_config = get_mc_config(state_or_input)
    lca_mc_config = {**lca_config, **mc_config}
    return lca_mc_config


def get_val_config(state_or_input):
    val_config = dict(
        val_min=state_or_input('val-min', 'value'),
        val_max=state_or_input('val-max', 'value'),
        val_step=state_or_input("val-step", "value"),
        val_iterations=state_or_input("val-iterations", "value"),
    )
    return val_config
