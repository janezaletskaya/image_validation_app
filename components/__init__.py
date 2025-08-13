"""
UI компоненты для приложения разметки изображений
"""

from .sidebar import render_sidebar
from .navigation import render_navigation
from .annotation_form import render_annotation_form

__all__ = [
    'render_sidebar',
    'render_navigation',
    'render_annotation_form'
]