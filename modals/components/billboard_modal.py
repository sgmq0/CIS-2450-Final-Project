"""Billboard Hot 100 in Spotify Modal."""

from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import polars as pl
from ..modal_helpers import (
    create_modal_title_bar,
    create_modal_backdrop,
    create_modal_container,
    format_list_columns_for_display
)


def create_billboard_modal(billboard_df=None):
    """Create the Billboard Hot 100 in Spotify modal."""
    backdrop = create_modal_backdrop('billboard-modal-backdrop')

    if billboard_df is None or billboard_df.height == 0:
        table_content = html.Div(
            "Click 'Load Billboard Hot 100' to fetch and match songs.",
            style={'padding': '20px', 'textAlign': 'center', 'color': '#666'}
        )
    else:
        # Format the data for display
        display_df = billboard_df.to_pandas()

        # Format the artists column if it's a list
        if 'artists' in display_df.columns:
            display_df['artists'] = display_df['artists'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else str(x)
            )

        columns = [
            {"name": "Rank", "id": "rank", "type": "numeric"},
            {"name": "Billboard Title", "id": "title"},
            {"name": "Billboard Artist", "id": "artist"},
            {"name": "Last Week", "id": "last_week_rank", "type": "numeric"},
            {"name": "Peak", "id": "peak_rank", "type": "numeric"},
            {"name": "Weeks", "id": "weeks_on_chart", "type": "numeric"},
            {"name": "Spotify Track", "id": "track_name"},
            {"name": "Spotify Artist(s)", "id": "artists"},
            {"name": "Album", "id": "album_name"},
            {"name": "Popularity", "id": "popularity", "type": "numeric"},
        ]

        table_content = dash_table.DataTable(
            id='billboard-table',
            columns=columns,
            data=display_df.to_dict('records'),
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '13px',
                'minWidth': '100px',
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'rank'},
                    'width': '60px',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                },
                {
                    'if': {
                        'filter_query': '{rank} <= 10',
                    },
                    'backgroundColor': '#fff3cd',
                },
                {
                    'if': {
                        'filter_query': '{rank} = 1',
                    },
                    'backgroundColor': '#ffd700',
                    'fontWeight': 'bold',
                },
            ],
            sort_action='native',
            filter_action='native',
        )

    modal_content = [
        create_modal_title_bar('Billboard Hot 100 in Spotify', 'close-billboard-modal'),

        html.Div([
            html.P([
                "This modal shows Billboard Hot 100 songs that are also in our Spotify dataset. ",
                "Songs are matched based on track title and artist name."
            ]),
            html.Div([
                html.Button(
                    'Load Billboard Hot 100',
                    id='load-billboard-button',
                    n_clicks=0,
                    style={
                        'marginTop': '10px',
                        'padding': '10px 20px',
                        'backgroundColor': '#28a745',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '4px',
                        'cursor': 'pointer',
                    }
                ),
                dcc.Loading(
                    id='loading-billboard',
                    type='default',
                    children=html.Div(id='billboard-load-status', style={'marginLeft': '15px', 'display': 'inline-block'})
                )
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], className='card', style={'marginBottom': '20px'}),

        html.Div([
            html.Div(id='billboard-stats', style={'marginBottom': '15px'}),
            html.Div(id='billboard-content', children=table_content),
        ], className='card'),
    ]

    modal = create_modal_container(
        'billboard-modal',
        modal_content,
        width='90%',
        max_width='1400px'
    )

    return backdrop, modal


def register_billboard_callbacks(app, spotify_df):
    """Register callbacks for Billboard Hot 100 modal."""
    from data.llm_extraction import extract_billboard_hot100
    from transformations.transformations_stub import get_billboard_songs_in_spotify

    @app.callback(
        [Output('billboard-content', 'children'),
         Output('billboard-stats', 'children'),
         Output('billboard-load-status', 'children')],
        Input('load-billboard-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def load_billboard_comparison(n_clicks):
        """Load Billboard Hot 100 and find matches in Spotify."""
        if n_clicks == 0:
            return dash_table.DataTable(data=[]), "", ""

        try:
            # Extract Billboard chart
            billboard_chart = extract_billboard_hot100()

            # Convert BillboardChart to DataFrame
            billboard_data = [
                {
                    'rank': song.rank,
                    'title': song.title,
                    'artist': song.artist,
                    'last_week_rank': song.last_week_rank,
                    'peak_rank': song.peak_rank,
                    'weeks_on_chart': song.weeks_on_chart
                }
                for song in billboard_chart.songs
            ]
            billboard_df = pl.DataFrame(billboard_data)

            # Find matches in Spotify
            matches_df = get_billboard_songs_in_spotify(billboard_df, spotify_df)

            # Format for display
            display_df = matches_df.to_pandas()

            # Format the artists column if it's a list
            if 'artists' in display_df.columns:
                display_df['artists'] = display_df['artists'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else str(x)
                )

            columns = [
                {"name": "Rank", "id": "rank", "type": "numeric"},
                {"name": "Billboard Title", "id": "title"},
                {"name": "Billboard Artist", "id": "artist"},
                {"name": "Last Week", "id": "last_week_rank", "type": "numeric"},
                {"name": "Peak", "id": "peak_rank", "type": "numeric"},
                {"name": "Weeks", "id": "weeks_on_chart", "type": "numeric"},
                {"name": "Spotify Track", "id": "track_name"},
                {"name": "Spotify Artist(s)", "id": "artists"},
                {"name": "Album", "id": "album_name"},
                {"name": "Popularity", "id": "popularity", "type": "numeric"},
            ]

            table = dash_table.DataTable(
                id='billboard-table',
                columns=columns,
                data=display_df.to_dict('records'),
                page_size=20,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '13px',
                    'minWidth': '100px',
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'borderBottom': '2px solid #dee2e6'
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'rank'},
                        'width': '60px',
                        'textAlign': 'center',
                        'fontWeight': 'bold',
                    },
                    {
                        'if': {
                            'filter_query': '{rank} <= 10',
                        },
                        'backgroundColor': '#fff3cd',
                    },
                    {
                        'if': {
                            'filter_query': '{rank} = 1',
                        },
                        'backgroundColor': '#ffd700',
                        'fontWeight': 'bold',
                    },
                ],
                sort_action='native',
                filter_action='native',
            )

            # Create stats summary
            total_billboard = len(billboard_chart.songs)
            matched = matches_df.height
            match_pct = (matched / total_billboard * 100) if total_billboard > 0 else 0

            stats = html.Div([
                html.H4('Match Statistics', style={'marginTop': 0}),
                html.P([
                    f"Found {matched} of {total_billboard} Billboard Hot 100 songs in Spotify dataset ",
                    f"({match_pct:.1f}% match rate)"
                ]),
            ])

            status_msg = html.Span(
                f"✓ Loaded Billboard Hot 100 ({billboard_chart.chart_date or 'current week'})",
                style={'color': 'green', 'fontWeight': 'bold'}
            )

            return table, stats, status_msg

        except Exception as e:
            error_msg = html.Div([
                html.P(f"Error loading Billboard chart: {str(e)}", style={'color': 'red'}),
                html.P("Please ensure you have set the OPENAI_API_KEY environment variable.",
                       style={'fontSize': '12px', 'color': '#666'})
            ])
            return error_msg, "", ""
