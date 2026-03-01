"""
UI Styles and Theming
Accessibility-first styling for the ISL Recognition System
"""

import config

# CustomTkinter theme settings
APPEARANCE_MODE = "dark"
COLOR_THEME = "blue"

# Color palette (high contrast for accessibility)
COLORS = config.COLORS

# Font configurations
FONTS = {
    'header': (config.FONT_FAMILY, config.FONT_SIZE_HEADER, 'bold'),
    'subheader': (config.FONT_FAMILY, config.FONT_SIZE_LARGE, 'bold'),
    'normal': (config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
    'large': (config.FONT_FAMILY, config.FONT_SIZE_LARGE),
    'output': (config.FONT_FAMILY, config.FONT_SIZE_OUTPUT, 'bold'),
    'small': (config.FONT_FAMILY, 12),
}

# Button styles
BUTTON_STYLES = {
    'primary': {
        'fg_color': COLORS['accent'],
        'hover_color': COLORS['accent_hover'],
        'text_color': COLORS['text_primary'],
        'corner_radius': 10,
        'height': 48,  # Minimum touch target
    },
    'secondary': {
        'fg_color': COLORS['bg_light'],
        'hover_color': COLORS['bg_medium'],
        'text_color': COLORS['text_primary'],
        'corner_radius': 10,
        'height': 48,
    },
    'success': {
        'fg_color': COLORS['success'],
        'hover_color': '#3db892',
        'text_color': COLORS['bg_dark'],
        'corner_radius': 10,
        'height': 48,
    }
}

# Frame styles
FRAME_STYLES = {
    'main': {
        'fg_color': COLORS['bg_dark'],
        'corner_radius': 0,
    },
    'card': {
        'fg_color': COLORS['bg_medium'],
        'corner_radius': 15,
    },
    'panel': {
        'fg_color': COLORS['bg_light'],
        'corner_radius': 10,
    }
}

# Label styles  
LABEL_STYLES = {
    'title': {
        'text_color': COLORS['text_primary'],
        'font': FONTS['header'],
    },
    'subtitle': {
        'text_color': COLORS['text_secondary'],
        'font': FONTS['large'],
    },
    'normal': {
        'text_color': COLORS['text_primary'],
        'font': FONTS['normal'],
    },
    'output': {
        'text_color': COLORS['success'],
        'font': FONTS['output'],
    },
    'status': {
        'text_color': COLORS['text_secondary'],
        'font': FONTS['small'],
    }
}

# Progress bar styles
PROGRESS_STYLES = {
    'recording': {
        'progress_color': COLORS['accent'],
        'fg_color': COLORS['bg_light'],
        'height': 10,
        'corner_radius': 5,
    }
}
