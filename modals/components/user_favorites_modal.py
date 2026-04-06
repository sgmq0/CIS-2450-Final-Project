"""User Favorite Songs Modal Dialog Component."""

from ..modal_helpers import create_user_table_modal


def create_user_favorites_modal(user_options):
	"""Create the User Favorite Songs modal."""
	return create_user_table_modal(
		user_options,
		modal_key='user_favorites',
		title='User Favorite Songs',
		table_id='user-favorites-table',
		dropdown_id='user-favorites-dropdown',
		table_heading='Favorite Songs',
		placeholder='Select user to view their favorite songs',
		width='80%',
		max_width='1000px',
	)
