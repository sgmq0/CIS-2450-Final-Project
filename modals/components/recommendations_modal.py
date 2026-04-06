"""Friend-Based Recommendations Modal Dialog Component."""

from ..modal_helpers import create_user_table_modal


def create_recommendations_modal(user_options):
	"""Create the Friend-Based Recommendations modal."""
	return create_user_table_modal(
		user_options,
		modal_key='recommendations',
		title='Friend-Based Recommendations',
		table_id='recommendations-table',
		dropdown_id='recommendations-dropdown',
		table_heading='Recommended Songs',
		placeholder='Select user to get recommendations',
		info_component_id='recommendations-info',
		description="These songs are popular among your friends but you haven't listened to them yet.",
		width='80%',
		max_width='1000px',
		table_style_overrides=[
			{'if': {'column_id': 'friend_support'}, 'fontWeight': 'bold', 'color': '#667eea'}
		],
	)
