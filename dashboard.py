
"""Dashboard (Dash + Polars) with modal dialogs.

Run from homework-2 directory: uv run dashboard.py
"""

from dash import Dash, html
from dash.dependencies import Input, Output, State, ALL
import plotly.express as px
import numpy as np
import polars as pl
import data.data_loader as data_loader
from transformations.transformations_stub import (
    transform_data,
    get_user_friendships,
    get_user_friend_counts,
    get_user_favorite_songs,
    get_songs_by_genre_and_artist,
    get_friend_recommendations,
    get_top_artists_by_friends,
    get_genre_overlap_between_users,
    get_popular_songs_among_friends,
    get_top_genres_among_friends,
    get_top_songs_per_genre
)
from modals.modal_config import (
    MODAL_CONFIGS,
    get_modal_buttons,
    get_modal_ids,
    get_modal_dimensions,
    get_modal_keys
)
from modals.modal_loader import load_modals, build_layout_from_modals
from modals.modal_helpers import table_records_and_columns

# Track any functions that are missing / not implemented so we can surface messages
missing_functions = set()


def _message_table(msg):
    return [{'message': msg}], [{'name': 'Message', 'id': 'message'}]


def _message_table_with_info(msg):
    return [{'message': msg}], [{'name': 'Message', 'id': 'message'}], msg


def create_modal_toggle_callback(modal_key):
    """Factory function to create a modal toggle callback. Looks up IDs and dimensions from config."""
    modal_config = get_modal_ids(modal_key)
    width, max_width = get_modal_dimensions()[modal_key]

    def callback_wrapper(app):
        @app.callback(
            Output(modal_config['modal_id'], 'style'),
            Output(modal_config['backdrop_id'], 'style'),
            [Input(modal_config['button_id'], 'n_clicks'),
             Input(modal_config['close_button_id'], 'n_clicks')],
            [State(modal_config['modal_id'], 'style')]
        )
        def toggle_modal(open_clicks, close_clicks, current_style):
            is_open = current_style.get(
                'display') != 'none' if current_style else False
            if open_clicks or close_clicks:
                is_open = not is_open
            modal_style = {
                'display': 'block' if is_open else 'none',
                'width': width,
                'maxWidth': max_width,
                'backgroundColor': 'white',
                'padding': '0'
            }
            backdrop_style = {'display': 'block' if is_open else 'none'}
            return modal_style, backdrop_style
        return toggle_modal
    return callback_wrapper


def create_app() -> Dash:
    app = Dash(__name__, suppress_callback_exceptions=True)

    spotify_df = data_loader.load_spotify_data(limit=1000)
    spotify_lookup_df = data_loader.load_spotify_data(limit=10000)
    display_cols = ['track_id', 'artists', 'album_name',
                    'track_name', 'track_genre', 'popularity']
    available_cols = [c for c in display_cols if c in spotify_df.columns]

    transformed_df = None
    try:
        transformed_df = transform_data(spotify_df.select(available_cols))
        table_df = transformed_df.to_pandas()
    except NotImplementedError:
        missing_functions.add('transform_data')
        table_df = spotify_df.select(available_cols).to_pandas()

    artist_list = []
    for artists_list in table_df['artists']:
        if isinstance(artists_list, (list, tuple, set, np.ndarray)):
            artist_list.extend([str(a).strip() for a in artists_list])
    artist_options = [{'label': a, 'value': a}
                      for a in sorted(set(artist_list))]
    pop_min, pop_max = int(spotify_df['popularity'].min()), int(
        spotify_df['popularity'].max())

    users_df = data_loader.load_users_dataset()
    social_df_full = data_loader.load_social_dataset()

    # Limit to 100K edges for performance
    social_df = social_df_full.head(100000).with_columns(
        pl.col('src').cast(pl.Int64),
        pl.col('dst').cast(pl.Int64)
    )

    song_edges = social_df.filter(pl.col('dst') >= 1000)
    users_with_songs = song_edges.select(
        'src').unique().sort('src').to_series().to_list()

    user_options = [{'label': row['name'], 'value': int(
        row['user_id'])} for row in users_df.to_dicts()]
    existing_user_ids = set(users_df.select('user_id').to_series().to_list())
    for uid in users_with_songs:
        if uid not in existing_user_ids:
            user_options.append({'label': f'User {uid}', 'value': int(uid)})
    user_options = sorted(user_options, key=lambda x: x['value'])

    friend_counts_df = None
    try:
        friend_counts_df = get_user_friend_counts(users_df, social_df)
    except NotImplementedError:
        missing_functions.add('get_user_friend_counts')

    def make_chart(df):
        chart_df = df.head(10).select(['track_name', 'popularity']).to_pandas()
        if 'track_name' in chart_df.columns and 'popularity' in chart_df.columns:
            fig = px.bar(
                chart_df,
                x='popularity',
                y='track_name',
                orientation='h',
                title='Top 10 Tracks by Popularity',
                labels={'popularity': 'Popularity', 'track_name': 'Track'},
            )
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=420)
            return fig
        return {}

    def make_friend_count_histogram(bin_size: int = 10):
        # If the friend counts function is not implemented, show a labeled figure
        if 'get_user_friend_counts' in missing_functions or friend_counts_df is None:
            fig = px.scatter()
            fig.update_layout(
                title='get_user_friend_counts not implemented',
                annotations=[dict(
                    text='get_user_friend_counts not implemented', x=0.5, y=0.5, showarrow=False)],
                height=300,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            return fig

        binned = friend_counts_df.with_columns(
            (pl.col('friend_count') // bin_size * bin_size).alias('bucket_start')
        ).group_by('bucket_start').agg(
            pl.col('name').count().alias('num_users')
        ).sort('bucket_start')

        hist_pd = binned.to_pandas()
        hist_pd['bucket_label'] = hist_pd['bucket_start'].astype(int).astype(
            str) + '-' + (hist_pd['bucket_start'] + bin_size - 1).astype(int).astype(str)

        fig = px.bar(
            hist_pd,
            x='bucket_label',
            y='num_users',
            title=f'Distribution of Friends per User (bins of {bin_size})',
            labels={
                'bucket_label': 'Friends (range)', 'num_users': 'Number of Users'},
        )
        fig.update_traces(marker_color='#667eea', opacity=0.95)
        fig.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            height=400,
            bargap=0.15,
            xaxis_tickangle=45
        )
        return fig

    header = html.Div([
        html.H1('CIS 2450 — Big Data Analytics', className='header-bar'),
        html.Div('Explore Spotify tracks and user social networks')
    ])

    modal_buttons = [
        html.Button(
            label,
            id=btn_id,
            n_clicks=0,
            style={'marginRight': '10px',
                   'padding': '10px 20px', 'cursor': 'pointer'}
        )
        for (btn_id, label) in get_modal_buttons()
    ]

    controls = html.Div([
        html.Div(modal_buttons, className='card modal-button-group',
                 style={'textAlign': 'center'}),
    ], className='container')

    song_mapping_df = data_loader.load_song_id_mapping()
    song_mapping_df = song_mapping_df.with_columns(
        pl.col('social_song_id').cast(pl.Int64)
    )

    preferences_df = data_loader.load_preferences_data(limit=50000)

    genre_artist_df = None
    try:
        genre_artist_df = get_songs_by_genre_and_artist(transformed_df)
    except NotImplementedError:
        missing_functions.add('get_songs_by_genre_and_artist')

    if genre_artist_df is None or len(genre_artist_df) == 0:
        genre_options = []
    else:
        genre_options = sorted(genre_artist_df.select(
            'genre').unique().to_series().to_list())
        genre_options = [{'label': g, 'value': g} for g in genre_options]

    data_context = {
        'table_df': table_df,
        'artist_options': artist_options,
        'pop_min': pop_min,
        'pop_max': pop_max,
        'user_options': user_options,
        'genre_options': genre_options,
        'initial_histogram': make_friend_count_histogram()
    }

    modals = load_modals(MODAL_CONFIGS, data_context)
    layout_children = build_layout_from_modals([header, controls], modals)
    app.layout = html.Div(layout_children)

    modal_ids = {key: get_modal_ids(key) for key in get_modal_keys()}

    for modal_key in get_modal_keys():
        create_modal_toggle_callback(modal_key)(app)

    @app.callback(
        [Output('friends-popular-songs-table', 'data'),
         Output('friends-popular-songs-table', 'columns')],
        Input('friends-popular-songs-user-dropdown', 'value')
    )
    def update_friends_popular_songs_table(user_id):
        if user_id is None:
            return [], []

        try:
            df = get_popular_songs_among_friends(
                user_id, social_df, song_mapping_df, spotify_lookup_df
            )

            if len(df) == 0:
                return [], []

            df = df.head(100)
            pandas_df = df.to_pandas()
            records, columns = table_records_and_columns(
                pandas_df, list_columns=['artists', 'track_genre'])
            return records, columns
        except NotImplementedError:
            return _message_table('get_popular_songs_among_friends not implemented')
        except Exception:
            return [], []

    @app.callback(
        [Output('friends-top-genres-table', 'data'),
         Output('friends-top-genres-table', 'columns')],
        Input('friends-top-genres-user-dropdown', 'value')
    )
    def update_friends_top_genres_table(user_id):
        if user_id is None:
            return [], []
        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)

        try:
            df = get_top_genres_among_friends(
                user_id, social_df, song_mapping_df, spotify_lookup_df, limit=10
            )

            if hasattr(df, "collect"):
                df = df.collect()

            if df.height == 0:
                return [], []

            pandas_df = df.to_pandas()
            records, columns = table_records_and_columns(pandas_df)
            return records, columns
        except NotImplementedError:
            return _message_table('get_top_genres_among_friends not implemented')
        except Exception:
            return [], []

    @app.callback(
        [Output('top-songs-per-genre-table', 'data'),
         Output('top-songs-per-genre-table', 'columns')],
        Input('top-songs-per-genre-dropdown', 'value')
    )
    def update_top_songs_per_genre_table(track_genre):
        if track_genre is None:
            return [], []

        try:
            df = get_top_songs_per_genre(
                social_df, song_mapping_df, spotify_lookup_df,
                track_genre=track_genre, limit=10
            )

            if hasattr(df, "collect"):
                df = df.collect()

            if df.height == 0:
                return [], []

            pandas_df = df.to_pandas()
            records, columns = table_records_and_columns(
                pandas_df, list_columns=['artists'])
            return records, columns
        except NotImplementedError:
            return _message_table('get_top_songs_per_genre not implemented')
        except Exception:
            return [], []

    @app.callback(
        [Output('user-favorites-table', 'data'),
         Output('user-favorites-table', 'columns')],
        Input('user-favorites-dropdown', 'value')
    )
    def update_user_favorites_table(user_id):
        if user_id is None:
            return [], []
        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)

        try:
            favorites_df = get_user_favorite_songs(
                user_id, social_df, song_mapping_df, spotify_lookup_df)

            if len(favorites_df) == 0:
                return [], []

            if 'transform_data' in missing_functions:
                return _message_table('transform_data not implemented')

            favorites_df = transform_data(favorites_df)
            favorites_df = favorites_df.head(100)

            pandas_df = favorites_df.to_pandas()
            records, columns = table_records_and_columns(
                pandas_df, list_columns=['artists', 'track_genre'])
            return records, columns
        except NotImplementedError:
            return _message_table('get_user_favorite_songs not implemented')
        except Exception:
            return [], []

    @app.callback(
        [Output('recommendations-table', 'data'),
         Output('recommendations-table', 'columns'),
         Output('recommendations-info', 'children')],
        Input('recommendations-dropdown', 'value')
    )
    def update_recommendations_table(user_id):
        if user_id is None:
            return [], [], ''

        try:
            recommendations_df = get_friend_recommendations(
                user_id=user_id,
                preferences_df=preferences_df,
                social_df=social_df,
                spotify_df=transformed_df,
                top_n=10
            )

            if len(recommendations_df) == 0:
                user_friends = social_df.filter(
                    (pl.col('src') == user_id) & (pl.col('dst') < 1000)
                )
                if len(user_friends) == 0:
                    info_msg = 'This user has no friends in the network.'
                else:
                    info_msg = 'No new recommendations found.'
                return [], [], info_msg

            pandas_df = recommendations_df.to_pandas()
            records, columns = table_records_and_columns(
                pandas_df,
                list_columns=['artists', 'track_genre'],
                column_name_map={
                    'track_id': 'Track ID',
                    'track_name': 'Track Name',
                    'artists': 'Artists',
                    'album_name': 'Album',
                    'popularity': 'Popularity',
                    'track_genre': 'Genres',
                    'friend_support': 'Friends Listening'
                }
            )
            num_friends = social_df.filter(
                (pl.col('src') == user_id) & (pl.col('dst') < 1000)
            ).height
            info_msg = f'Showing top {len(records)} recommendations based on {num_friends} friends.'

            return records, columns, info_msg
        except NotImplementedError:
            return _message_table_with_info('get_friend_recommendations not implemented')
        except Exception:
            return [], [], ''

    @app.callback(
        [Output('friend-artists-table', 'data'),
         Output('friend-artists-table', 'columns'),
         Output('friend-artists-info', 'children')],
        Input('friend-artists-dropdown', 'value')
    )
    def update_friend_artists_table(user_id):
        if user_id is None:
            return [], [], ''

        try:
            artists_df = get_top_artists_by_friends(
                user_id=user_id,
                preferences_df=preferences_df,
                social_df=social_df,
                top_n=10
            )

            if len(artists_df) == 0:
                user_friends = social_df.filter(
                    (pl.col('src') == user_id) & (pl.col('dst') < 1000)
                )
                if len(user_friends) == 0:
                    info_msg = 'This user has no friends in the network.'
                else:
                    info_msg = 'No artist data found for this user\'s friends.'
                return [], [], info_msg

            pandas_df = artists_df.to_pandas()
            records, columns = table_records_and_columns(
                pandas_df,
                column_name_map={
                    'artist': 'Artist',
                    'tracks_count': 'Tracks Count',
                    'friend_count': 'Friends Listening'
                }
            )
            num_friends = social_df.filter(
                (pl.col('src') == user_id) & (pl.col('dst') < 1000)
            ).height
            info_msg = f'Showing top {len(records)} artists based on {num_friends} friends.'

            return records, columns, info_msg
        except NotImplementedError:
            return _message_table_with_info('get_top_artists_by_friends not implemented')
        except Exception:
            return [], [], ''

    @app.callback(
        [Output('genre-overlap-table', 'data'),
         Output('genre-overlap-table', 'columns'),
         Output('genre-overlap-info', 'children')],
        Input('genre-overlap-slider', 'value')
    )
    def update_genre_overlap_table(min_shared_genres):
        if min_shared_genres is None:
            min_shared_genres = 3

        try:
            overlap_df = get_genre_overlap_between_users(
                preferences_df=preferences_df,
                users_df=users_df,
                min_shared_genres=min_shared_genres
            )

            if len(overlap_df) == 0:
                info_msg = f'No user pairs found with at least {min_shared_genres} shared genres.'
                return [], [], info_msg

            pandas_df = overlap_df.to_pandas()
            records, columns = table_records_and_columns(
                pandas_df,
                list_columns=['genres_list'],
                column_name_map={
                    'user1_id': 'User 1 ID',
                    'user1_name': 'User 1',
                    'user2_id': 'User 2 ID',
                    'user2_name': 'User 2',
                    'shared_genres': 'Shared Genres',
                    'genres_list': 'Genre List'
                }
            )
            info_msg = f'Found {len(records)} user pairs sharing at least {min_shared_genres} genres.'

            return records, columns, info_msg
        except NotImplementedError:
            return _message_table_with_info('get_genre_overlap_between_users not implemented')
        except Exception:
            return [], [], ''

    @app.callback(
        Output('genre-browser-artist-dropdown', 'options'),
        Output('genre-browser-artist-dropdown', 'value'),
        Output('genre-browser-artist-dropdown', 'disabled'),
        Input('genre-browser-genre-dropdown', 'value')
    )
    def update_artist_options(selected_genre):
        if selected_genre is None:
            return [], None, True

        if genre_artist_df is None:
            return [], None, True

        artists_for_genre = (
            genre_artist_df
            .filter(pl.col('genre') == selected_genre)
            .select('artist')
            .unique()
            .to_series()
            .to_list()
        )

        artist_options = [{'label': a, 'value': a}
                          for a in sorted(artists_for_genre)]
        return artist_options, None, False

    @app.callback(
        [Output('genre-artist-table', 'data'),
         Output('genre-artist-table', 'columns')],
        [Input('genre-browser-genre-dropdown', 'value'),
         Input('genre-browser-artist-dropdown', 'value')]
    )
    def update_genre_artist_table(selected_genre, selected_artist):
        if selected_genre is None:
            return [], []

        if genre_artist_df is None:
            return _message_table('get_songs_by_genre_and_artist not implemented')

        df = genre_artist_df.filter(pl.col('genre') == selected_genre)

        if selected_artist is not None:
            df = df.filter(pl.col('artist') == selected_artist)

        if len(df) == 0:
            return [], []

        display_df = df.select(
            ['genre', 'artist', 'track_name', 'popularity']).to_pandas()
        records, columns = table_records_and_columns(display_df)
        return records, columns

    @app.callback(
        Output('tracks-table', 'data'),
        Output('popularity-chart', 'figure'),
        Input('artist-dropdown', 'value'),
        Input('popularity-slider', 'value')
    )
    def update_table_and_chart(artist, pop_range):
        if 'transform_data' in missing_functions or transformed_df is None:
            fig = px.scatter()
            fig.update_layout(
                title='transform_data not implemented',
                annotations=[
                    dict(text='transform_data not implemented', x=0.5, y=0.5, showarrow=False)],
                height=300,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            return [{'message': 'transform_data not implemented'}], fig

        df = transformed_df
        if artist:
            df = df.filter(pl.col('artists').list.contains(artist))
        if pop_range:
            df = df.filter((pl.col('popularity') >= pop_range[0]) & (
                pl.col('popularity') <= pop_range[1]))

        pandas_df = df.to_pandas()
        records, _ = table_records_and_columns(
            pandas_df, list_columns=['artists', 'track_genre'])
        fig = make_chart(df)
        return records, fig

    @app.callback(
        Output('user-friends-list', 'children'),
        Input('user-dropdown', 'value')
    )
    def update_user_friends(selected_user_id):
        if selected_user_id is None:
            return html.Div('Select a user to see their friends', style={'fontStyle': 'italic', 'color': '#666'})

        try:
            friendships_df = get_user_friendships(users_df, social_df)

            # Filter to just the selected user's friendships
            user_friendships = friendships_df.filter(
                pl.col('src') == selected_user_id)

            if len(user_friendships) == 0:
                return html.Div(f'No friendships found for this user', style={'color': '#999'})

            # Build a list from the friendships dataframe
            friend_list = [
                html.Li(
                    html.Button(
                        f"{row['friend_name']}",
                        id={'type': 'friend-button', 'index': row['dst']},
                        n_clicks=0,
                        style={
                            'background': 'none',
                            'border': 'none',
                            'color': '#667eea',
                            'cursor': 'pointer',
                            'padding': '6px 0',
                            'fontSize': '14px',
                            'textAlign': 'left',
                            'textDecoration': 'underline'
                        }
                    ),
                    style={'padding': '3px 0'}
                )
                for row in user_friendships.to_dicts()
            ]

            return html.Div([
                html.H4(f"Friends ({len(friend_list)})"),
                html.Ul(friend_list, style={
                        'maxHeight': '300px', 'overflowY': 'auto', 'listStyle': 'none'})
            ])
        except NotImplementedError:
            return html.Div('get_user_friendships not implemented', style={'color': '#d32f2f', 'fontWeight': 'bold'})
        except Exception:
            # Fallback to original implementation if get_user_friendships fails
            user_friends = social_df.filter(pl.col('src') == selected_user_id)

            if len(user_friends) == 0:
                return html.Div(f'No friends found for this user', style={'color': '#999'})

            friend_ids = user_friends.select('dst').to_series().to_list()
            friends_names = users_df.filter(
                pl.col('user_id').is_in(friend_ids))

            friend_list = [
                html.Li(
                    html.Button(
                        f"{row['name']} (ID: {row['user_id']})",
                        id={'type': 'friend-button', 'index': row['user_id']},
                        n_clicks=0,
                        style={
                            'background': 'none',
                            'border': 'none',
                            'color': '#667eea',
                            'cursor': 'pointer',
                            'padding': '6px 0',
                            'fontSize': '14px',
                            'textAlign': 'left',
                            'textDecoration': 'underline'
                        }
                    ),
                    style={'padding': '3px 0'}
                )
                for row in friends_names.to_dicts()
            ]

            return html.Div([
                html.H4(f"Friends ({len(friend_list)})"),
                html.Ul(friend_list, style={
                        'maxHeight': '300px', 'overflowY': 'auto', 'listStyle': 'none'})
            ])

    @app.callback(
        Output('user-dropdown', 'value'),
        Input({'type': 'friend-button', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def select_friend_from_list(n_clicks_list):
        from dash import ctx
        if not ctx.triggered or ctx.triggered[0]['value'] == 0:
            return None

        button_id = ctx.triggered[0]['prop_id']
        if button_id and 'friend-button' in button_id:
            import json
            id_dict = json.loads(button_id.split('.')[0])
            return id_dict['index']
        return None

    @app.callback(
        Output('friend-count-histogram', 'figure'),
        Input(modal_ids['users']['button_id'], 'n_clicks')
    )
    def update_friend_histogram(_):
        return make_friend_count_histogram()

    # Register callbacks for LLM-based data integration modals
    from modals.components.itunes_comparison_modal import register_itunes_comparison_callbacks
    from modals.components.billboard_modal import register_billboard_callbacks

    register_itunes_comparison_callbacks(app, spotify_lookup_df)
    register_billboard_callbacks(app, spotify_lookup_df)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8050, dev_tools_ui=False,
            dev_tools_props_check=False)
