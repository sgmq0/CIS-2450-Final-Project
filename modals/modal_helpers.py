"""Shared helper functions for modal components."""

from dash import html, dcc, dash_table
import numpy as np


def create_modal_title_bar(title: str, close_button_id: str):
	"""Create standardized modal title bar with gradient background."""
	return html.Div([
		html.H2(title, style={'margin': 0, 'color': 'white', 'flex': 1}),
		html.Button(
			'✕',
			id=close_button_id,
			n_clicks=0,
			style={
				'background': 'none',
				'border': 'none',
				'color': 'white',
				'fontSize': '24px',
				'cursor': 'pointer',
				'padding': '0 10px',
				'lineHeight': '1'
			}
		)
	], style={
		'display': 'flex',
		'alignItems': 'center',
		'justifyContent': 'space-between',
		'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
		'color': 'white',
		'padding': '20px',
		'borderRadius': '12px 12px 0 0',
		'marginBottom': '20px'
	})


def create_modal_backdrop(backdrop_id: str):
	"""Create standardized modal backdrop."""
	return html.Div(
		id=backdrop_id,
		className='modal-backdrop',
		style={'display': 'none'}
	)


def create_modal_container(modal_id: str, children, width='80%', max_width='1000px'):
	"""
	Create standardized modal container.
	
	Args:
		modal_id: ID for the modal element
		children: Child components to include in modal
		width: Width percentage (default: '80%')
		max_width: Maximum width (default: '1000px')
		
	Returns:
		html.Div component for modal container
	"""
	return html.Div(
		children,
		id=modal_id,
		className='modal-container',
		style={
			'display': 'none',
			'width': width,
			'maxWidth': max_width,
			'backgroundColor': 'white',
			'padding': '0'
		}
	)


def format_list_columns_for_display(df, columns):
	"""Convert list/array columns to comma-separated strings for table display."""
	df_copy = df.copy()
	for col in columns:
		if col in df_copy.columns:
			df_copy[col] = df_copy[col].apply(
				lambda x: ', '.join(str(i) for i in x) 
				if isinstance(x, (list, tuple, set, np.ndarray)) 
				else str(x)
			)
	return df_copy


def table_records_and_columns(pandas_df, list_columns=None, column_name_map=None):
	"""
	Convert a pandas DataFrame to (records, columns) for Dash DataTable.
	Optionally format list columns for display and rename column headers.

	Returns:
		Tuple of (list of row dicts, list of {name, id} column specs).
	"""
	if list_columns:
		pandas_df = format_list_columns_for_display(pandas_df, list_columns)
	records = pandas_df.to_dict('records')
	if column_name_map:
		columns = [
			{'name': column_name_map.get(col, col), 'id': col}
			for col in pandas_df.columns
		]
	else:
		columns = [{'name': col, 'id': col} for col in pandas_df.columns]
	return records, columns


def create_user_dropdown(dropdown_id: str, user_options, placeholder='Select a user'):
	"""Create standardized user dropdown component."""
	from dash import dcc
	
	return html.Div([
		html.Label(
			'Select a user:',
			style={'fontWeight': 'bold', 'marginBottom': '8px', 'display': 'block'}
		),
		dcc.Dropdown(
			id=dropdown_id,
			className='dropdown-in-modal',
			options=user_options,
			multi=False,
			placeholder=placeholder
		)
	], className='card', style={'marginBottom': '20px'})


def get_standard_table_styles():
	"""Get standardized table styling configuration."""
	return {
		'style_table': {
			'overflowX': 'auto',
			'border': '1px solid #e0e0e0',
			'borderRadius': '8px'
		},
		'style_cell': {
			'textAlign': 'left',
			'padding': '12px',
			'fontFamily': 'Arial, sans-serif',
			'fontSize': '14px'
		},
		'style_header': {
			'backgroundColor': '#f5f5f5',
			'fontWeight': 'bold',
			'borderBottom': '2px solid #667eea',
			'color': '#333'
		},
		'style_data': {
			'borderBottom': '1px solid #f0f0f0'
		},
		'style_data_conditional': [
			{
				'if': {'row_index': 'odd'},
				'backgroundColor': '#fafafa'
			}
		]
	}


def create_user_table_modal(
	user_options,
	*,
	modal_key: str,
	title: str,
	table_id: str,
	dropdown_id: str,
	table_heading: str,
	placeholder: str = 'Select a user',
	info_component_id: str | None = None,
	description: str | None = None,
	width: str = '80%',
	max_width: str = '1000px',
	table_style_overrides: list | None = None,
):
	"""
	Create a modal with a user dropdown and a single table (and optional info text).
	Use this for modals that follow the pattern: select user → show table (e.g. favorites, recommendations).
	"""
	key_dashes = modal_key.replace('_', '-')
	backdrop_id = f'{key_dashes}-modal-backdrop'
	modal_id = f'{key_dashes}-modal'
	close_button_id = f'close-{key_dashes}-modal'

	backdrop = create_modal_backdrop(backdrop_id)
	table_styles = get_standard_table_styles().copy()
	if table_style_overrides:
		table_styles['style_data_conditional'] = table_styles['style_data_conditional'] + table_style_overrides

	if info_component_id:
		dropdown_block = html.Div([
			html.Label('Select a user:', style={'fontWeight': 'bold', 'marginBottom': '8px', 'display': 'block'}),
			dcc.Dropdown(id=dropdown_id, className='dropdown-in-modal', options=user_options, multi=False, placeholder=placeholder),
			html.Div(id=info_component_id, style={'marginTop': '12px', 'color': '#666', 'fontSize': '14px', 'fontStyle': 'italic'})
		], className='card', style={'marginBottom': '20px'})
	else:
		dropdown_block = create_user_dropdown(dropdown_id, user_options, placeholder)

	table_block_children = [
		html.H3(table_heading, style={'marginTop': 0, 'marginBottom': '16px'})
	]
	if description:
		table_block_children.append(
			html.P(description, style={'color': '#666', 'marginBottom': '16px', 'fontSize': '14px'})
		)
	table_block_children.append(
		dcc.Loading(
			children=dash_table.DataTable(
				id=table_id,
				columns=[],
				data=[],
				page_size=10,
				**table_styles
			),
			type='circle',
			style={'minHeight': '200px'}
		)
	)

	modal_content = [
		create_modal_title_bar(title, close_button_id),
		html.Div([
			dropdown_block,
			html.Div(table_block_children, className='card', style={'marginBottom': '20px'})
		], style={'padding': '0 20px 20px 20px'})
	]

	modal = create_modal_container(modal_id, modal_content, width=width, max_width=max_width)
	return backdrop, modal
