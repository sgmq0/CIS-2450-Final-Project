"""Genre & Artist Browser Modal Dialog Component."""

from dash import html, dcc, dash_table
from ..modal_helpers import (
	create_modal_title_bar,
	create_modal_backdrop,
	create_modal_container
)


def create_genre_artist_modal(genre_options):
	"""Create the Genre & Artist Browser modal."""

	backdrop = create_modal_backdrop('genre-artist-modal-backdrop')

	modal_content = [
		create_modal_title_bar('Browse by Genre & Artist', 'close-genre-artist-modal'),

		html.Div([
			html.Label(
				'Select a genre:',
				style={'fontWeight': 'bold', 'marginBottom': '8px', 'display': 'block'}
			),
			dcc.Dropdown(
				id='genre-browser-genre-dropdown',
				className='dropdown-in-modal',
				options=genre_options,
				multi=False,
				placeholder='Select genre'
			),
			html.Label(
				'Select an artist (optional):',
				style={'fontWeight': 'bold', 'marginTop': '20px', 'marginBottom': '8px', 'display': 'block'}
			),
			dcc.Dropdown(
				id='genre-browser-artist-dropdown',
				className='dropdown-in-modal',
				options=[],
				multi=False,
				placeholder='Select artist (select genre first)',
				disabled=True
			),
			html.Label(
				'Songs:',
				style={'fontWeight': 'bold', 'marginTop': '20px', 'marginBottom': '8px', 'display': 'block'}
			),
			dash_table.DataTable(
				id='genre-artist-table',
				columns=[],
				data=[],
				page_size=10,
				style_table={'overflowX': 'auto'}
			)
		], className='card', style={'marginBottom': '20px'})
	]

	modal = create_modal_container(
		'genre-artist-modal',
		modal_content,
		width='85%',
		max_width='1100px'
	)

	return backdrop, modal
