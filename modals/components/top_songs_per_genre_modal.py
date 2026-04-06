"""Top Songs Per Genre Modal Dialog Component."""

from dash import html, dcc, dash_table
from ..modal_helpers import (
	create_modal_title_bar,
	create_modal_backdrop,
	create_modal_container,
	get_standard_table_styles
)


def create_top_songs_per_genre_modal(genre_options):
	"""Create the Top Songs Per Genre modal."""
	backdrop = create_modal_backdrop('top-songs-per-genre-modal-backdrop')
	table_styles = get_standard_table_styles()

	modal_content = [
		create_modal_title_bar('Top Songs Per Genre', 'close-top-songs-per-genre-modal'),

		html.Div([
			html.Div([
				html.Label(
					'Select a genre:',
					style={'fontWeight': 'bold', 'marginBottom': '8px', 'display': 'block'}
				),
				dcc.Dropdown(
					id='top-songs-per-genre-dropdown',
					className='dropdown-in-modal',
					options=genre_options,
					multi=False,
					placeholder='Select genre to view top songs'
				)
			], className='card', style={'marginBottom': '20px'}),

			html.Div([
				html.H3('Top Songs', style={'marginTop': 0, 'marginBottom': '16px'}),
				dcc.Loading(
					children=dash_table.DataTable(
						id='top-songs-per-genre-table',
						columns=[],
						data=[],
						page_size=10,
						**table_styles
					),
					type='circle',
					style={'minHeight': '200px'}
				)
			], className='card', style={'marginBottom': '20px'})
		], style={'padding': '0 20px 20px 20px'})
	]

	modal = create_modal_container(
		'top-songs-per-genre-modal',
		modal_content,
		width='85%',
		max_width='1000px'
	)

	return backdrop, modal
