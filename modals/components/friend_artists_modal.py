"""Friend Artists Modal Dialog Component."""

from ..modal_helpers import create_user_table_modal


def create_friend_artists_modal(user_options):
	"""Create the Friend Artists modal."""
	return create_user_table_modal(
		user_options,
		modal_key='friend_artists',
		title='Top Artists Among Friends',
		table_id='friend-artists-table',
		dropdown_id='friend-artists-dropdown',
		table_heading='Popular Artists',
		placeholder='Select user to see popular artists among their friends',
		info_component_id='friend-artists-info',
		description="These artists are most listened to by this user's friends.",
		width='75%',
		max_width='900px',
		table_style_overrides=[
			{'if': {'column_id': 'tracks_count'}, 'fontWeight': 'bold', 'color': '#667eea'}
		],
	)
