"""Modern dark theme for the application.

Single source of truth for colors (design tokens) and the Qt stylesheet.
Inspired by the Tokyo Night palette.
"""
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

COLORS = {
    # Backgrounds (dark navy scale)
    'bg':          '#16161e',   # window background
    'surface':     '#1a1b26',   # panels, inputs
    'elevated':    '#24283b',   # cards, headers, toolbar
    'hover':       '#2f3549',   # hover state
    'border':      '#3b4261',

    # Text
    'text':        '#c0caf5',
    'text_muted':  '#565f89',
    'text_bright': '#ffffff',

    # Accent + semantic
    'accent':        '#7aa2f7',
    'accent_hover':  '#89b4fa',
    'accent_active': '#5d84d7',
    'green':         '#9ece6a',
    'red':           '#f7768e',
    'yellow':        '#e0af68',
    'cyan':          '#7dcfff',
    'magenta':       '#bb9af7',
}


def _qss() -> str:
    c = COLORS
    return f"""
    /* ------------------------------- base ------------------------------- */
    QMainWindow, QDialog {{
        background-color: {c['bg']};
    }}
    QWidget {{
        color: {c['text']};
        font-family: 'Segoe UI', 'Yu Gothic UI', 'Noto Sans CJK JP', sans-serif;
        font-size: 13px;
    }}
    QToolTip {{
        background-color: {c['elevated']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 8px;
    }}

    /* ------------------------------ menus ------------------------------- */
    QMenuBar {{
        background-color: {c['bg']};
        color: {c['text']};
        padding: 2px 4px;
        border-bottom: 1px solid {c['border']};
    }}
    QMenuBar::item {{
        padding: 6px 12px;
        border-radius: 6px;
    }}
    QMenuBar::item:selected {{
        background-color: {c['hover']};
    }}
    QMenu {{
        background-color: {c['elevated']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 7px 28px 7px 16px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background-color: {c['accent']};
        color: {c['bg']};
    }}
    QMenu::item:disabled {{
        color: {c['text_muted']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {c['border']};
        margin: 6px 10px;
    }}

    /* ----------------------------- toolbar ------------------------------ */
    QToolBar {{
        background-color: {c['bg']};
        border-bottom: 1px solid {c['border']};
        padding: 6px 8px;
        spacing: 6px;
    }}

    /* ----------------------------- buttons ------------------------------ */
    QPushButton {{
        background-color: {c['elevated']};
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 7px 16px;
        border-radius: 8px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {c['hover']};
        border-color: {c['accent']};
    }}
    QPushButton:pressed {{
        background-color: {c['accent_active']};
        color: {c['bg']};
    }}
    QPushButton:checked {{
        background-color: {c['accent']};
        color: {c['bg']};
        border-color: {c['accent']};
    }}
    QPushButton:disabled {{
        color: {c['text_muted']};
        background-color: {c['surface']};
        border-color: {c['surface']};
    }}
    QPushButton[accent="true"] {{
        background-color: {c['accent']};
        color: {c['bg']};
        border: none;
    }}
    QPushButton[accent="true"]:hover {{
        background-color: {c['accent_hover']};
    }}
    QPushButton[accent="true"]:pressed {{
        background-color: {c['accent_active']};
    }}

    /* ------------------------------ inputs ------------------------------ */
    QLineEdit, QSpinBox, QTextEdit {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 6px 10px;
        border-radius: 8px;
        selection-background-color: {c['accent']};
        selection-color: {c['bg']};
    }}
    QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {{
        border-color: {c['accent']};
    }}
    QLineEdit::placeholder {{
        color: {c['text_muted']};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 18px;
        border: none;
        background: transparent;
    }}
    QSpinBox::up-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid {c['text_muted']};
    }}
    QSpinBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {c['text_muted']};
    }}

    QComboBox {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 6px 10px;
        border-radius: 8px;
    }}
    QComboBox:hover {{
        border-color: {c['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {c['text_muted']};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['elevated']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        selection-background-color: {c['accent']};
        selection-color: {c['bg']};
        padding: 4px;
    }}

    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {c['border']};
        border-radius: 5px;
        background-color: {c['surface']};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c['accent']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['accent']};
        border-color: {c['accent']};
    }}

    /* --------------------------- item views ----------------------------- */
    QTreeWidget, QListWidget {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 4px;
        outline: none;
    }}
    QTreeWidget::item, QListWidget::item {{
        padding: 5px 6px;
        border-radius: 6px;
    }}
    QTreeWidget::item:hover, QListWidget::item:hover {{
        background-color: {c['hover']};
    }}
    QTreeWidget::item:selected, QListWidget::item:selected {{
        background-color: {c['accent']};
        color: {c['bg']};
    }}

    QTableWidget {{
        background-color: {c['surface']};
        alternate-background-color: {c['bg']};
        gridline-color: transparent;
        border: 1px solid {c['border']};
        border-radius: 10px;
        outline: none;
    }}
    QTableWidget::item {{
        padding: 4px 8px;
        border-bottom: 1px solid {c['elevated']};
    }}
    QTableWidget::item:selected {{
        background-color: {c['accent']};
        color: {c['bg']};
    }}
    QHeaderView::section {{
        background-color: {c['bg']};
        color: {c['text_muted']};
        padding: 8px;
        border: none;
        border-bottom: 2px solid {c['border']};
        font-weight: 700;
    }}
    QTableCornerButton::section {{
        background-color: {c['bg']};
        border: none;
    }}

    /* ------------------------------- tabs ------------------------------- */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        border-radius: 10px;
        background-color: {c['bg']};
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {c['text_muted']};
        padding: 9px 20px;
        border: none;
        border-bottom: 2px solid transparent;
        font-weight: 600;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        color: {c['accent']};
        border-bottom: 2px solid {c['accent']};
    }}
    QTabBar::tab:hover:!selected {{
        color: {c['text']};
    }}

    /* ---------------------------- containers ---------------------------- */
    QGroupBox {{
        border: 1px solid {c['border']};
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: 700;
    }}
    QGroupBox::title {{
        color: {c['text_muted']};
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }}

    QSplitter::handle {{
        background-color: transparent;
        width: 6px;
    }}
    QSplitter::handle:hover {{
        background-color: {c['accent']};
    }}

    QStatusBar {{
        background-color: {c['bg']};
        color: {c['text_muted']};
        border-top: 1px solid {c['border']};
    }}
    QStatusBar::item {{
        border: none;
    }}

    /* ---------------------------- scrollbars ---------------------------- */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c['border']};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c['accent']};
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c['border']};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {c['accent']};
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        height: 0; width: 0;
    }}
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
    }}
    """


def apply_theme(app: QApplication):
    """Apply the modern dark theme to the application."""
    app.setStyle("Fusion")

    c = COLORS
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(c['bg']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(c['text']))
    palette.setColor(QPalette.ColorRole.Base, QColor(c['surface']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(c['bg']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(c['elevated']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(c['text']))
    palette.setColor(QPalette.ColorRole.Text, QColor(c['text']))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(c['text_muted']))
    palette.setColor(QPalette.ColorRole.Button, QColor(c['elevated']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(c['text']))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(c['red']))
    palette.setColor(QPalette.ColorRole.Link, QColor(c['accent']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(c['accent']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(c['bg']))
    app.setPalette(palette)

    app.setStyleSheet(_qss())
