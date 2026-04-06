"""iTunes vs Spotify Artist Comparison Modal."""

from dash import html, dcc, dash_table, callback_context
from dash.dependencies import Input, Output, State
import polars as pl
from ..modal_helpers import (
    create_modal_title_bar,
    create_modal_backdrop,
    create_modal_container,
)


def create_itunes_comparison_modal(comparison_df=None):
    """Create the iTunes vs Spotify Artist Comparison modal."""
    backdrop = create_modal_backdrop('itunes-comparison-modal-backdrop')

    if comparison_df is None or comparison_df.height == 0:
        table_content = html.Div(
            "Click 'Load iTunes Chart' to fetch and compare artists.",
            style={'padding': '20px', 'textAlign': 'center', 'color': '#666'}
        )
    else:
        # Format the comparison data for display
        table_data = comparison_df.to_dicts()

        columns = [
            {"name": "iTunes Artist", "id": "itunes_artist"},
            {"name": "Edit Distance Match", "id": "edit_matched", "type": "text"},
            {"name": "Edit Match Artist", "id": "edit_match"},
            {"name": "Edit Dist", "id": "edit_distance", "type": "numeric", "format": {"specifier": ".2f"}},
            {"name": "Q-gram Match", "id": "qgram_matched", "type": "text"},
            {"name": "Q-gram Artist", "id": "qgram_match"},
            {"name": "Q-gram Sim", "id": "qgram_similarity", "type": "numeric", "format": {"specifier": ".3f"}},
            {"name": "Embedding Match", "id": "embedding_matched", "type": "text"},
            {"name": "Embedding Artist", "id": "embedding_match"},
            {"name": "Embed Dist", "id": "embedding_distance", "type": "numeric", "format": {"specifier": ".3f"}},
        ]

        table_content = dash_table.DataTable(
            id='itunes-comparison-table',
            columns=columns,
            data=table_data,
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '13px',
            },
            style_data_conditional=[
                {
                    'if': {
                        'filter_query': '{edit_matched} = true',
                        'column_id': 'edit_matched'
                    },
                    'backgroundColor': '#d4edda',
                    'color': '#155724',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{edit_matched} = false',
                        'column_id': 'edit_matched'
                    },
                    'backgroundColor': '#f8d7da',
                    'color': '#721c24'
                },
                {
                    'if': {
                        'filter_query': '{qgram_matched} = true',
                        'column_id': 'qgram_matched'
                    },
                    'backgroundColor': '#d4edda',
                    'color': '#155724',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{qgram_matched} = false',
                        'column_id': 'qgram_matched'
                    },
                    'backgroundColor': '#f8d7da',
                    'color': '#721c24'
                },
                {
                    'if': {
                        'filter_query': '{embedding_matched} = true',
                        'column_id': 'embedding_matched'
                    },
                    'backgroundColor': '#d4edda',
                    'color': '#155724',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{embedding_matched} = false',
                        'column_id': 'embedding_matched'
                    },
                    'backgroundColor': '#f8d7da',
                    'color': '#721c24'
                },
            ],
            filter_action='native',
            sort_action='native',
        )

    modal_content = [
        create_modal_title_bar('iTunes vs Spotify Artist Comparison', 'close-itunes-comparison-modal'),

        html.Div([
            html.P([
                "This modal compares iTunes Top Songs artists with the Spotify dataset using three ",
                "approximate string matching strategies:"
            ]),
            html.Ul([
                html.Li([
                    html.Strong("Edit Distance (Levenshtein): "),
                    "Minimum number of character edits needed to transform one string into another."
                ]),
                html.Li([
                    html.Strong("Q-gram Similarity: "),
                    "Measures overlap of character sequences (bigrams). Higher score = more similar."
                ]),
                html.Li([
                    html.Strong("Embedding Distance: "),
                    "Uses transformer models to compute semantic similarity. Lower distance = more similar."
                ]),
            ]),
            html.Div([
                html.Button(
                    'Load iTunes Chart',
                    id='load-itunes-button',
                    n_clicks=0,
                    style={
                        'marginTop': '10px',
                        'padding': '10px 20px',
                        'backgroundColor': '#007bff',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '4px',
                        'cursor': 'pointer',
                    }
                ),
                dcc.Loading(
                    id='loading-itunes',
                    type='default',
                    children=html.Div(id='itunes-load-status', style={'marginLeft': '15px', 'display': 'inline-block'})
                )
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], className='card', style={'marginBottom': '20px'}),

        html.Div([
            html.H3('Artist Matching Results', style={'marginTop': 0}),
            html.Div(id='itunes-comparison-content', children=table_content),
        ], className='card'),
    ]

    modal = create_modal_container(
        'itunes-comparison-modal',
        modal_content,
        width='90%',
        max_width='1400px'
    )

    return backdrop, modal


def register_itunes_comparison_callbacks(app, spotify_df):
    """Register callbacks for iTunes comparison modal."""
    from data.llm_extraction import extract_itunes_chart, get_itunes_artists
    from transformations.transformations_stub import compare_itunes_spotify_artists

    @app.callback(
        [Output('itunes-comparison-content', 'children'),
         Output('itunes-load-status', 'children')],
        Input('load-itunes-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def load_itunes_comparison(n_clicks):
        """Load iTunes chart and perform comparison."""
        if n_clicks == 0:
            return dash_table.DataTable(data=[]), ""

        try:
            # Extract iTunes chart
            itunes_artists = get_itunes_artists()

            # Perform comparison
            comparison_df = compare_itunes_spotify_artists(itunes_artists, spotify_df)

            # Format for display
            table_data = comparison_df.to_dicts()

            columns = [
                {"name": "iTunes Artist", "id": "itunes_artist"},
                {"name": "Edit Match", "id": "edit_matched", "type": "text"},
                {"name": "Edit Match Artist", "id": "edit_match"},
                {"name": "Edit Dist", "id": "edit_distance", "type": "numeric", "format": {"specifier": ".1f"}},
                {"name": "Q-gram Match", "id": "qgram_matched", "type": "text"},
                {"name": "Q-gram Artist", "id": "qgram_match"},
                {"name": "Q-gram Sim", "id": "qgram_similarity", "type": "numeric", "format": {"specifier": ".3f"}},
                {"name": "Embedding Match", "id": "embedding_matched", "type": "text"},
                {"name": "Embedding Artist", "id": "embedding_match"},
                {"name": "Embed Dist", "id": "embedding_distance", "type": "numeric", "format": {"specifier": ".3f"}},
            ]

            table = dash_table.DataTable(
                id='itunes-comparison-table',
                columns=columns,
                data=table_data,
                page_size=15,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '13px',
                },
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{edit_matched} = true',
                            'column_id': 'edit_matched'
                        },
                        'backgroundColor': '#d4edda',
                        'color': '#155724',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {
                            'filter_query': '{edit_matched} = false',
                            'column_id': 'edit_matched'
                        },
                        'backgroundColor': '#f8d7da',
                        'color': '#721c24'
                    },
                    {
                        'if': {
                            'filter_query': '{qgram_matched} = true',
                            'column_id': 'qgram_matched'
                        },
                        'backgroundColor': '#d4edda',
                        'color': '#155724',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {
                            'filter_query': '{qgram_matched} = false',
                            'column_id': 'qgram_matched'
                        },
                        'backgroundColor': '#f8d7da',
                        'color': '#721c24'
                    },
                    {
                        'if': {
                            'filter_query': '{embedding_matched} = true',
                            'column_id': 'embedding_matched'
                        },
                        'backgroundColor': '#d4edda',
                        'color': '#155724',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {
                            'filter_query': '{embedding_matched} = false',
                            'column_id': 'embedding_matched'
                        },
                        'backgroundColor': '#f8d7da',
                        'color': '#721c24'
                    },
                ],
                filter_action='native',
                sort_action='native',
            )

            status_msg = html.Span(
                f"✓ Loaded {len(itunes_artists)} iTunes artists",
                style={'color': 'green', 'fontWeight': 'bold'}
            )

            return table, status_msg

        except Exception as e:
            error_msg = html.Div([
                html.P(f"Error loading iTunes chart: {str(e)}", style={'color': 'red'}),
                html.P("Please ensure you have set the OPENAI_API_KEY environment variable.",
                       style={'fontSize': '12px', 'color': '#666'})
            ])
            return error_msg, ""
