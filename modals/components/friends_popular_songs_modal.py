"""Popular Songs Among Friends Modal Dialog Component."""

from ..modal_helpers import create_user_table_modal


def create_friends_popular_songs_modal(user_options):
	"""Create the Popular Songs Among Friends modal."""
	return create_user_table_modal(
		user_options,
		modal_key='friends_popular_songs',
		title='Popular Songs Among Friends',
		table_id='friends-popular-songs-table',
		dropdown_id='friends-popular-songs-user-dropdown',
		table_heading='Popular Songs',
		placeholder='Select user to view popular songs among friends',
		width='80%',
		max_width='900px',
	)
