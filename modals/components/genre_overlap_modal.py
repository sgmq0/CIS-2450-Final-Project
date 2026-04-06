"""Genre Overlap Modal Dialog Component."""

from dash import html, dcc, dash_table
from ..modal_helpers import (
	create_modal_title_bar,
	create_modal_backdrop,
	create_modal_container,
	get_standard_table_styles
)


def create_genre_overlap_modal():
	"""Create the Genre Overlap modal."""

	backdrop = create_modal_backdrop('genre-overlap-modal-backdrop')

	table_styles = get_standard_table_styles()
	table_styles['style_data_conditional'].append({
		'if': {'column_id': 'shared_genres'},
		'fontWeight': 'bold',
		'color': '#667eea'
	})

	modal_content = [
		create_modal_title_bar('Genre Overlap Between Users', 'close-genre-overlap-modal'),

		html.Div([
			html.Div([
				html.Label(
					'Minimum shared genres:',
					style={'fontWeight': 'bold', 'marginBottom': '8px', 'display': 'block'}
				),
				dcc.Slider(
					id='genre-overlap-slider',
					min=1,
					max=10,
					value=3,
					marks={i: str(i) for i in range(1, 11)},
					step=1
				),
				html.Div(
					id='genre-overlap-info',
					style={'marginTop': '12px', 'color': '#666', 'fontSize': '14px', 'fontStyle': 'italic'}
				)
			], className='card', style={'marginBottom': '20px'}),

			html.Div([
				html.H3('User Pairs with Similar Tastes', style={'marginTop': 0, 'marginBottom': '16px'}),
				html.P(
					'These users share common music genres in their listening preferences.',
					style={'color': '#666', 'marginBottom': '16px', 'fontSize': '14px'}
				),
				dcc.Loading(
					children=dash_table.DataTable(
						id='genre-overlap-table',
						columns=[],
						data=[],
						page_size=15,
						**table_styles
					),
					type='circle',
					style={'minHeight': '200px'}
				)
			], className='card', style={'marginBottom': '20px'})
		], style={'padding': '0 20px 20px 20px'})
	]

	modal = create_modal_container(
		'genre-overlap-modal',
		modal_content,
		width='85%',
		max_width='1100px'
	)

	return backdrop, modal
