"""Users & Friends Explorer Modal Dialog Component."""

from dash import html, dcc
from ..modal_helpers import (
	create_modal_title_bar,
	create_modal_backdrop,
	create_modal_container
)


def create_users_modal(user_options, initial_histogram=None):
	"""Create the Users & Friends Explorer modal."""
	
	backdrop = create_modal_backdrop('users-modal-backdrop')
	
	modal_content = [
		create_modal_title_bar('Users & Friends Explorer', 'close-users-modal'),

		html.Div([
			html.Div([
				html.Label(
					'Select a user:',
					style={'fontWeight': 'bold', 'marginBottom': '8px', 'display': 'block'}
				),
				dcc.Dropdown(
					id='user-dropdown',
					options=user_options,
					multi=False,
					placeholder='Select user'
				),
				html.Div(id='user-friends-list', style={'marginTop': '20px'})
			], className='card two-col-left', style={
				'marginBottom': '20px',
				'paddingRight': '20px',
				'width': '45%',
				'display': 'inline-block',
				'verticalAlign': 'top'
			}),

			html.Div([
				html.H3('Friends Distribution', style={'marginTop': 0}),
				dcc.Loading(children=dcc.Graph(id='friend-count-histogram', figure=initial_histogram), type='circle')
			], className='card two-col-right', style={'width': '55%', 'display': 'inline-block'})
		], style={'padding': '0 20px 20px 20px'})
	]
	
	modal = create_modal_container(
		'users-modal',
		modal_content,
		width='88%',
		max_width='1250px'
	)
	
	return backdrop, modal
