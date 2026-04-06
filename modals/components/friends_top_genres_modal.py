"""Top Genres Among Friends Modal Dialog Component."""

from ..modal_helpers import create_user_table_modal


def create_friends_top_genres_modal(user_options):
	"""Create the Top Genres Among Friends modal."""
	return create_user_table_modal(
		user_options,
		modal_key='friends_top_genres',
		title='Top Genres Among Friends',
		table_id='friends-top-genres-table',
		dropdown_id='friends-top-genres-user-dropdown',
		table_heading='Top Genres',
		placeholder='Select user to view top genres among friends',
		width='80%',
		max_width='900px',
	)
