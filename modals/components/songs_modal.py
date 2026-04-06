"""Spotify Tracks Modal Dialog Component."""

from dash import html, dcc, dash_table
from ..modal_helpers import (
	create_modal_title_bar,
	create_modal_backdrop,
	create_modal_container,
	format_list_columns_for_display
)


def create_songs_modal(table_df, artist_options, pop_min, pop_max):
	"""Create the Spotify Tracks Explorer modal."""
	table_data = format_list_columns_for_display(table_df, ['artists', 'track_genre'])
	backdrop = create_modal_backdrop('songs-modal-backdrop')
	
	modal_content = [
		create_modal_title_bar('Spotify Tracks Explorer', 'close-songs-modal'),

		html.Div([
			html.Label(
				'Filter by artist:',
				style={'fontWeight': 'bold', 'marginBottom': '8px', 'display': 'block'}
			),
			dcc.Dropdown(
				id='artist-dropdown',
				options=artist_options,
				multi=False,
				placeholder='Select artist'
			),
			html.Label(
				'Popularity range:',
				style={'fontWeight': 'bold', 'marginTop': '20px', 'marginBottom': '8px', 'display': 'block'}
			),
			dcc.RangeSlider(
				id='popularity-slider',
				min=pop_min,
				max=pop_max,
				value=[pop_min, pop_max],
				marks={pop_min: str(pop_min), pop_max: str(pop_max)},
				step=1
			)
		], className='card', style={'marginBottom': '20px'}),

		html.Div([
			html.H3('Top Tracks Popularity Chart', style={'marginTop': 0}),
			dcc.Loading(children=dcc.Graph(id='popularity-chart'), type='circle')
		], className='card', style={'marginBottom': '20px'}),

		html.Div([
			html.Label('Top tracks by popularity:', style={'fontWeight': 'bold', 'marginBottom': '8px', 'display': 'block'}),
			dash_table.DataTable(
				id='tracks-table',
				columns=[{"name": col.replace('_', ' ').title(), "id": col} for col in table_data.columns],
				data=table_data.to_dict('records'),
				page_size=10,
				style_table={'overflowX': 'auto'},
			)
		])
	]
	
	modal = create_modal_container(
		'songs-modal',
		modal_content,
		width='85%',
		max_width='950px'
	)
	
	return backdrop, modal
