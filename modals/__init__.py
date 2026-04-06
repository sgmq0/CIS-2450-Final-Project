"""Modal dialog components for the dashboard."""

from .modal_config import (
	MODAL_CONFIGS,
	get_modal_keys,
	get_modal_config,
	get_modal_buttons,
	get_modal_ids,
	get_modal_dimensions
)
from .modal_loader import load_modals, build_layout_from_modals

__all__ = [
	'MODAL_CONFIGS',
	'get_modal_keys',
	'get_modal_config',
	'get_modal_buttons',
	'get_modal_ids',
	'get_modal_dimensions',
	'load_modals',
	'build_layout_from_modals',
]
