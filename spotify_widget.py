import sys
import threading
import os
import json
import winreg
import subprocess
import glob
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox, QFrame
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.storage.streams import Buffer, InputStreamOptions
import asyncio
from pycaw.pycaw import AudioUtilities

class MediaUpdater(QObject):
    update_signal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        
    def run_async(self, coro):
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
                if result is not None:
                    if isinstance(result, dict):
                        self.update_signal.emit(result)
                else:
                    self.update_signal.emit({'status': 'no_session'})
            except Exception as e:
                print(f"Error in async: {e}")
                self.update_signal.emit({'status': 'error'})
            finally:
                loop.close()
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()

class IconButton(QPushButton):
    def __init__(self, icon_type, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.is_hovered = False
        self.is_pressed_state = False
        
    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        self.is_pressed_state = True
        self.update()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.is_pressed_state = False
        self.update()
        super().mouseReleaseEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        
        if self.icon_type in ['play', 'pause']:
            if self.is_pressed_state:
                painter.setBrush(QColor(29, 185, 84, 200))
            elif self.is_hovered:
                painter.setBrush(QColor(30, 215, 96, 220))
            else:
                painter.setBrush(QColor(29, 185, 84, 180))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect.adjusted(1, 1, -1, -1))
            icon_color = QColor(255, 255, 255)
        else:
            if self.is_pressed_state:
                painter.setBrush(QColor(255, 255, 255, 35))
            elif self.is_hovered:
                painter.setBrush(QColor(255, 255, 255, 50))
            else:
                painter.setBrush(QColor(255, 255, 255, 25))
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect.adjusted(1, 1, -1, -1))
            icon_color = QColor(255, 255, 255, 240)
        
        painter.setBrush(icon_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        if self.icon_type == 'prev':
            path = QPainterPath()
            path.moveTo(center_x + 3, center_y - 5)
            path.lineTo(center_x + 3, center_y + 5)
            path.lineTo(center_x - 3, center_y)
            path.closeSubpath()
            painter.drawPath(path)
            
        elif self.icon_type == 'next':
            path = QPainterPath()
            path.moveTo(center_x - 3, center_y - 5)
            path.lineTo(center_x - 3, center_y + 5)
            path.lineTo(center_x + 3, center_y)
            path.closeSubpath()
            painter.drawPath(path)
            
        elif self.icon_type == 'play':
            path = QPainterPath()
            path.moveTo(center_x - 3, center_y - 6)
            path.lineTo(center_x - 3, center_y + 6)
            path.lineTo(center_x + 5, center_y)
            path.closeSubpath()
            painter.drawPath(path)
            
        elif self.icon_type == 'pause':
            painter.drawRect(int(center_x - 4), int(center_y - 5), 3, 10)
            painter.drawRect(int(center_x + 1), int(center_y - 5), 3, 10)

class HeaderButton(QPushButton):
    def __init__(self, button_type, parent=None):
        super().__init__(parent)
        self.button_type = button_type
        self.is_hovered = False
        self.is_pressed_state = False
        self.is_locked = False
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def set_locked(self, locked):
        self.is_locked = locked
        self.update()
        
    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        self.is_pressed_state = True
        self.update()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.is_pressed_state = False
        self.update()
        super().mouseReleaseEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        
        if self.button_type == 'close':
            if self.is_pressed_state:
                painter.setBrush(QColor(200, 50, 50, 200))
            elif self.is_hovered:
                painter.setBrush(QColor(220, 60, 60, 180))
            else:
                painter.setBrush(QColor(255, 255, 255, 20))
        else:
            if self.is_pressed_state:
                painter.setBrush(QColor(255, 255, 255, 40))
            elif self.is_hovered:
                painter.setBrush(QColor(255, 255, 255, 50))
            else:
                painter.setBrush(QColor(255, 255, 255, 20))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.adjusted(2, 2, -2, -2))
        
        icon_color = QColor(255, 255, 255, 240)
        painter.setPen(QPen(icon_color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        if self.button_type == 'close':
            painter.drawLine(int(center_x - 3.5), int(center_y - 3.5), 
                           int(center_x + 3.5), int(center_y + 3.5))
            painter.drawLine(int(center_x + 3.5), int(center_y - 3.5), 
                           int(center_x - 3.5), int(center_y + 3.5))
        elif self.button_type == 'lock':
            painter.setBrush(icon_color)
            painter.setPen(Qt.PenStyle.NoPen)
            
            if self.is_locked:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(icon_color, 1.5))
                painter.drawArc(int(center_x - 3), int(center_y - 5), 6, 6, 0, 180 * 16)
                
                painter.setBrush(icon_color)
                painter.setPen(Qt.PenStyle.NoPen)
                path = QPainterPath()
                path.addRoundedRect(center_x - 3.5, center_y - 1, 7, 5, 1, 1)
                painter.drawPath(path)
                
                painter.setBrush(QColor(0, 0, 0, 100))
                painter.drawEllipse(int(center_x - 1), int(center_y), 2, 2)
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(icon_color, 1.5))
                painter.drawArc(int(center_x - 2), int(center_y - 5), 6, 6, 45 * 16, 135 * 16)
                
                painter.setBrush(icon_color)
                painter.setPen(Qt.PenStyle.NoPen)
                path = QPainterPath()
                path.addRoundedRect(center_x - 3.5, center_y - 1, 7, 5, 1, 1)
                painter.drawPath(path)
                
                painter.setBrush(QColor(0, 0, 0, 100))
                painter.drawEllipse(int(center_x - 1), int(center_y), 2, 2)
        elif self.button_type == 'view':
            painter.setBrush(icon_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(center_x - 4), int(center_y - 5), 8, 3, 1, 1)
            painter.drawRoundedRect(int(center_x - 4), int(center_y + 2), 8, 3, 1, 1)
        else:
            painter.setBrush(icon_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(center_x - 1.5), int(center_y - 6), 3, 3)
            painter.drawEllipse(int(center_x - 1.5), int(center_y - 1.5), 3, 3)
            painter.drawEllipse(int(center_x - 1.5), int(center_y + 3), 3, 3)
            
class SpotifyButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_hovered = False
        self.is_pressed_state = False
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        self.is_pressed_state = True
        self.update()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.is_pressed_state = False
        self.update()
        super().mouseReleaseEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        
        if self.is_pressed_state:
            painter.setBrush(QColor(29, 185, 84, 220))
        elif self.is_hovered:
            painter.setBrush(QColor(30, 215, 96, 200))
        else:
            painter.setBrush(QColor(30, 215, 96, 180))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.adjusted(2, 2, -2, -2))
        
        painter.setPen(QPen(QColor(25, 20, 20, 255), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        
        painter.drawArc(int(center_x - 7), int(center_y - 6), 14, 12, 15 * 16, 150 * 16)
        
        painter.drawArc(int(center_x - 6), int(center_y - 2), 12, 9, 15 * 16, 150 * 16)
        
        painter.drawArc(int(center_x - 5), int(center_y + 2), 10, 7, 15 * 16, 150 * 16)

class SettingsMenu(QWidget):
    def __init__(self, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 380)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)
        
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        self.spotify_logo_button = SpotifyButton()
        self.spotify_logo_button.setFixedSize(28, 28)
        self.spotify_logo_button.clicked.connect(self.launch_spotify)
        title_layout.addWidget(self.spotify_logo_button)
        
        title = QLabel("Settings")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 700;
                color: rgba(255, 255, 255, 0.95);
                background: transparent;
            }
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        content_layout.addLayout(title_layout)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: rgba(255, 255, 255, 0.2); max-height: 1px;")
        content_layout.addWidget(separator)
        content_layout.addSpacing(4)
        
        startup_info_layout = QVBoxLayout()
        startup_info_layout.setSpacing(4)
        
        startup_label = QLabel("Launch at startup")
        startup_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                background: transparent;
            }
        """)
        startup_info_layout.addWidget(startup_label)
        
        startup_hint = QLabel("Use add_to_startup.bat to enable")
        startup_hint.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 10px;
                font-style: italic;
                background: transparent;
            }
        """)
        startup_info_layout.addWidget(startup_hint)
        
        content_layout.addLayout(startup_info_layout)
        
        content_layout.addSpacing(4)
        
        self.always_on_top_checkbox = QCheckBox("Always on Top")
        self.always_on_top_checkbox.setStyleSheet("""
            QCheckBox {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1.5px solid rgba(255, 255, 255, 0.4);
                background: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator:checked {
                background: rgba(29, 185, 84, 0.8);
                border: 1.5px solid rgba(29, 185, 84, 1);
            }
            QCheckBox::indicator:hover {
                border: 1.5px solid rgba(255, 255, 255, 0.6);
            }
        """)
        self.always_on_top_checkbox.setChecked(self.parent_widget.settings.get('always_on_top', False))
        self.always_on_top_checkbox.stateChanged.connect(self.toggle_always_on_top)
        content_layout.addWidget(self.always_on_top_checkbox)
        
        content_layout.addSpacing(8)
        
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
        """)
        content_layout.addWidget(theme_label)
        
        theme_buttons_layout = QHBoxLayout()
        theme_buttons_layout.setSpacing(8)
        
        self.glass_mode_button = QPushButton("Glass")
        self.glass_mode_button.setFixedHeight(32)
        self.glass_mode_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.glass_mode_button.clicked.connect(lambda: self.set_theme_mode('glass'))
        
        self.dark_mode_button = QPushButton("Dark")
        self.dark_mode_button.setFixedHeight(32)
        self.dark_mode_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dark_mode_button.clicked.connect(lambda: self.set_theme_mode('dark'))
        
        theme_buttons_layout.addWidget(self.glass_mode_button)
        theme_buttons_layout.addWidget(self.dark_mode_button)
        content_layout.addLayout(theme_buttons_layout)
        
        self.update_theme_buttons()
        
        content_layout.addSpacing(8)
        
        opacity_label = QLabel("Opacity")
        opacity_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
        """)
        content_layout.addWidget(opacity_label)
        
        opacity_container = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(30)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self.parent_widget.windowOpacity() * 100))
        self.opacity_slider.setStyleSheet("""
            QSlider {
                background: transparent;
            }
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.15);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(255, 255, 255, 0.6);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: rgba(255, 255, 255, 0.95);
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        
        self.opacity_value = QLabel(f"{self.opacity_slider.value()}%")
        self.opacity_value.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 11px;
                background: transparent;
                min-width: 35px;
            }
        """)
        
        opacity_container.addWidget(self.opacity_slider)
        opacity_container.addWidget(self.opacity_value)
        content_layout.addLayout(opacity_container)
        
        content_layout.addSpacing(8)
        
        position_label = QLabel("Default Position")
        position_label.setStyleSheet(opacity_label.styleSheet())
        content_layout.addWidget(position_label)
        
        position_grid = QHBoxLayout()
        position_grid.setSpacing(8)
        
        positions = [
            ("TL", "Top Left"),
            ("TR", "Top Right"),
            ("BL", "Bottom Left"),
            ("BR", "Bottom Right")
        ]
        
        for pos_code, pos_name in positions:
            btn = QPushButton(pos_code)
            btn.setFixedSize(58, 32)
            btn.setToolTip(pos_name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.15);
                    color: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.25);
                    border: 1px solid rgba(255, 255, 255, 0.4);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.35);
                }
            """)
            btn.clicked.connect(lambda checked, p=pos_code: self.set_position(p))
            position_grid.addWidget(btn)
        
        content_layout.addLayout(position_grid)
        
        content_layout.addStretch()
        
        version = QLabel("Version 1.0.0")
        version.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 10px;
                background: transparent;
            }
        """)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(version)
        
        main_layout.addWidget(content)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, rect.width(), rect.height(), 12, 12)
        
        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        gradient.setColorAt(0, QColor(40, 40, 40, 240))
        gradient.setColorAt(1, QColor(30, 30, 30, 240))
        
        painter.fillPath(path, QBrush(gradient))
        
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 11, 11)
    
    def launch_spotify(self):
        self.parent_widget.launch_spotify()
    
    def update_theme_buttons(self):
        current_theme = self.parent_widget.settings.get('theme', 'glass')
        
        if current_theme == 'glass':
            self.glass_mode_button.setStyleSheet("""
                QPushButton {
                    background: rgba(29, 185, 84, 0.8);
                    color: rgba(255, 255, 255, 0.95);
                    border: 1.5px solid rgba(29, 185, 84, 1);
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(30, 215, 96, 0.9);
                }
            """)
            self.dark_mode_button.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.15);
                    color: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.25);
                    border: 1px solid rgba(255, 255, 255, 0.4);
                }
            """)
        else:
            self.dark_mode_button.setStyleSheet("""
                QPushButton {
                    background: rgba(29, 185, 84, 0.8);
                    color: rgba(255, 255, 255, 0.95);
                    border: 1.5px solid rgba(29, 185, 84, 1);
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(30, 215, 96, 0.9);
                }
            """)
            self.glass_mode_button.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.15);
                    color: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.25);
                    border: 1px solid rgba(255, 255, 255, 0.4);
                }
            """)
    
    def set_theme_mode(self, mode):
        self.parent_widget.settings['theme'] = mode
        self.parent_widget.save_settings()
        self.update_theme_buttons()
        self.parent_widget.update()
    
    def toggle_always_on_top(self, state):
        always_on_top = state == Qt.CheckState.Checked.value
        self.parent_widget.settings['always_on_top'] = always_on_top
        self.parent_widget.save_settings()
        
        flags = self.parent_widget.windowFlags()
        if always_on_top:
            self.parent_widget.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.parent_widget.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        
        self.parent_widget.show()
    
    def change_opacity(self, value):
        self.parent_widget.setWindowOpacity(value / 100)
        self.opacity_value.setText(f"{value}%")
        self.parent_widget.settings['opacity'] = value
        self.parent_widget.save_settings()
    
    def set_position(self, position):
        screen = QApplication.primaryScreen().geometry()
        widget_width = self.parent_widget.width()
        widget_height = self.parent_widget.height()
        margin = 20
        
        positions = {
            'TL': (margin, margin),
            'TR': (screen.width() - widget_width - margin, margin),
            'BL': (margin, screen.height() - widget_height - 70),
            'BR': (screen.width() - widget_width - margin, screen.height() - widget_height - 70)
        }
        
        if position in positions:
            x, y = positions[position]
            self.parent_widget.move(x, y)
            self.parent_widget.save_position()

class RoundedAlbumArt(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap_to_draw = None
        self.parent_widget = parent
        self.spotify_button_rect = None
        self.is_hovered = False
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def setPixmap(self, pixmap):
        self.pixmap_to_draw = pixmap
        self.update()
    
    def enterEvent(self, event):
        if self.pixmap_to_draw is None:
            self.is_hovered = True
            self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if self.pixmap_to_draw is None and event.button() == Qt.MouseButton.LeftButton:
            if self.parent_widget:
                self.parent_widget.launch_spotify()
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.pixmap_to_draw:
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
            
            if self.is_hovered:
                painter.setBrush(QBrush(QColor(29, 185, 84, 100)))
            else:
                painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
            
            painter.setPen(QPen(QColor(255, 255, 255, 40), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
            
            center_x = self.width() / 2
            center_y = self.height() / 2
            
            painter.setPen(Qt.PenStyle.NoPen)
            if self.is_hovered:
                painter.setBrush(QColor(255, 255, 255, 240))
            else:
                painter.setBrush(QColor(255, 255, 255, 180))
            
            painter.drawEllipse(int(center_x - 20), int(center_y - 20), 40, 40)
            
            painter.setPen(QPen(QColor(29, 185, 84), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(int(center_x - 12), int(center_y - 8), 24, 16, 0, 180 * 16)
            painter.drawArc(int(center_x - 10), int(center_y - 3), 20, 12, 0, 180 * 16)
            painter.drawArc(int(center_x - 8), int(center_y + 2), 16, 8, 0, 180 * 16)
            
            painter.setPen(QColor(255, 255, 255, 200))
            font = painter.font()
            font.setPointSize(9)
            font.setWeight(600)
            painter.setFont(font)
            text_rect = self.rect()
            text_rect.adjust(0, 35, 0, 0)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, 
                           "Click to launch")
            
            return
        
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        painter.setClipPath(path)
        
        scaled_pixmap = self.pixmap_to_draw.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)

class VolumeController:
    def __init__(self):
        self.spotify_session = None
    
    def get_spotify_session(self):
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.name().lower() in ["spotify.exe", "spotify"]:
                    return session
        except Exception as e:
            print(f"Error finding Spotify session: {e}")
        return None
    
    def set_volume(self, volume_level):
        try:
            session = self.get_spotify_session()
            if session:
                volume = session.SimpleAudioVolume
                volume.SetMasterVolume(volume_level / 100.0, None)
        except Exception as e:
            print(f"Error setting volume: {e}")
    
    def get_volume(self):
        try:
            session = self.get_spotify_session()
            if session:
                volume = session.SimpleAudioVolume
                return int(volume.GetMasterVolume() * 100)
        except Exception as e:
            print(f"Error getting volume: {e}")
        return 100

class SpotifyWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        if getattr(sys, 'frozen', False):
            self.config_file = os.path.join(os.path.dirname(sys.executable), 'widget_config.json')
        else:
            self.config_file = os.path.join(os.path.dirname(__file__), 'widget_config.json')
        
        self.load_settings()
        
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.settings.get('always_on_top', False):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 125)
        self.setWindowOpacity(self.settings.get('opacity', 100) / 100)

        self.dragging = False
        self.is_locked = self.settings.get('is_locked', False)  # ← MODIFIÉ ICI (point 2)
        self.current_session = None
        self.media_updater = MediaUpdater()
        self.media_updater.update_signal.connect(self.on_media_update)
        self.is_playing = False
        self.duration = 0
        self.is_seeking = False
        self.compact_mode = True
        
        self.volume_controller = VolumeController()

        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 420, 125)
        self.container.setStyleSheet("QWidget { background: transparent; }")

        self.album_art_label = RoundedAlbumArt(self)
        self.album_art_label.setStyleSheet("QLabel { background: transparent; border: none; }")

        self.song_title_label = QLabel("No media playing")
        self.song_title_label.setWordWrap(False)

        self.artist_label = QLabel("Launch Spotify")
        self.artist_label.setWordWrap(False)

        self.current_time_label = QLabel("0:00")
        self.current_time_label.setFixedWidth(32)

        self.total_time_label = QLabel("0:00")
        self.total_time_label.setFixedWidth(32)

        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setEnabled(True)
        self.progress_bar.setStyleSheet("""
            QSlider {
                background: transparent;
            }
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.15);
                height: 5px;
                border-radius: 2.5px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.95),
                    stop:1 rgba(255, 255, 255, 0.8));
                border-radius: 2.5px;
            }
            QSlider::handle:horizontal {
                background: rgba(255, 255, 255, 0.95);
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
            QSlider::handle:horizontal:hover {
                background: rgba(255, 255, 255, 1);
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        self.progress_bar.sliderPressed.connect(self.on_slider_pressed)
        self.progress_bar.sliderReleased.connect(self.on_slider_released)

        self.prev_button = IconButton('prev')
        self.prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_button.clicked.connect(self.previous_song)

        self.play_button = IconButton('play')
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.clicked.connect(self.toggle_playback)

        self.next_button = IconButton('next')
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.clicked.connect(self.next_song)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        current_volume = self.volume_controller.get_volume()
        self.volume_slider.setValue(current_volume)
        self.volume_slider.setStyleSheet("""
            QSlider {
                background: transparent;
            }
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.12);
                height: 3px;
                border-radius: 1.5px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(255, 255, 255, 0.6);
                border-radius: 1.5px;
            }
            QSlider::handle:horizontal {
                background: rgba(255, 255, 255, 0.9);
                width: 8px;
                height: 8px;
                margin: -2.5px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal:hover {
                background: rgba(255, 255, 255, 1);
                width: 10px;
                height: 10px;
                margin: -3.5px 0;
            }
        """)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

        self.setup_compact_layout()

        self.view_button = HeaderButton('view', self)
        self.view_button.move(312, 8)
        self.view_button.clicked.connect(self.toggle_view_mode)
        self.view_button.raise_()

        self.view_button = HeaderButton('view', self)
        self.view_button.move(312, 8)
        self.view_button.clicked.connect(self.toggle_view_mode)
        self.view_button.raise_()

        self.lock_button = HeaderButton('lock', self)
        self.lock_button.move(338, 8)
        self.lock_button.clicked.connect(self.toggle_lock)
        self.lock_button.set_locked(self.is_locked)  # ← AJOUTÉ ICI (point 3)
        self.lock_button.raise_()
        
        self.settings_button = HeaderButton('settings', self)
        self.settings_button.move(364, 8)
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.raise_()
        
        self.close_button = HeaderButton('close', self)
        self.close_button.move(390, 8)
        self.close_button.clicked.connect(self.close_application)
        self.close_button.raise_()

        self.load_position()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_song_info)
        self.timer.start(1000)

        self.volume_sync_timer = QTimer(self)
        self.volume_sync_timer.timeout.connect(self.sync_volume_slider)
        self.volume_sync_timer.start(2000)

        self.update_song_info()

    def launch_spotify(self):
        try:
            possible_paths = [
                os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    subprocess.Popen([path])
                    print(f"Spotify launched from: {path}")
                    return
            
            windowsapps_pattern = r"C:\Program Files\WindowsApps\SpotifyAB.SpotifyMusic_*\Spotify.exe"
            matches = glob.glob(windowsapps_pattern)
            if matches:
                subprocess.Popen([matches[0]])
                print(f"Spotify launched from: {matches[0]}")
                return
            
            subprocess.Popen(['cmd', '/c', 'start', 'spotify:'])
            print("Spotify launched via protocol")
        except Exception as e:
            print(f"Error launching Spotify: {e}")

    def setup_compact_layout(self):
        if self.container.layout():
            old_layout = self.container.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    self.clear_layout(item.layout())
            QWidget().setLayout(old_layout)
        
        main_layout = QHBoxLayout(self.container)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        self.album_art_label.setFixedSize(80, 80)
        main_layout.addWidget(self.album_art_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        self.song_title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.song_title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: rgba(255, 255, 255, 0.95);
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.artist_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        
        self.current_time_label.setStyleSheet("""
            QLabel {
                font-size: 9px;
                font-weight: 500;
                color: rgba(255, 255, 255, 0.65);
                background: transparent;
                border: none;
            }
        """)
        
        self.total_time_label.setStyleSheet("""
            QLabel {
                font-size: 9px;
                font-weight: 500;
                color: rgba(255, 255, 255, 0.65);
                background: transparent;
                border: none;
            }
        """)
        
        info_layout.addWidget(self.song_title_label)
        info_layout.addWidget(self.artist_label)
        info_layout.addSpacing(3)
        
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.total_time_label)
        info_layout.addLayout(progress_layout)
        info_layout.addSpacing(4)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.prev_button.setFixedSize(28, 28)
        self.play_button.setFixedSize(32, 32)
        self.next_button.setFixedSize(28, 28)
        
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addStretch()
        
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(0)
        volume_layout.addSpacing(40)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addSpacing(40)
        controls_layout.addLayout(volume_layout)
        
        info_layout.addLayout(controls_layout)
        info_layout.addStretch()
        
        main_layout.addLayout(info_layout)

    def setup_nowplaying_layout(self):
        if self.container.layout():
            old_layout = self.container.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    self.clear_layout(item.layout())
            QWidget().setLayout(old_layout)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(15, 50, 15, 18)
        main_layout.setSpacing(0)
        
        self.album_art_label.setFixedSize(240, 240)
        album_container = QHBoxLayout()
        album_container.addStretch()
        album_container.addWidget(self.album_art_label)
        album_container.addStretch()
        main_layout.addLayout(album_container)
        
        main_layout.addSpacing(16)
        
        info_text_layout = QHBoxLayout()
        info_text_layout.setSpacing(6)
        
        self.song_title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.song_title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 700;
                color: rgba(255, 255, 255, 0.95);
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        
        separator = QLabel("•")
        separator.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: rgba(255, 255, 255, 0.5);
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.artist_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        
        info_text_layout.addStretch()
        info_text_layout.addWidget(self.song_title_label)
        info_text_layout.addWidget(separator)
        info_text_layout.addWidget(self.artist_label)
        info_text_layout.addStretch()
        main_layout.addLayout(info_text_layout)
        
        main_layout.addSpacing(16)
        
        self.current_time_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: 500;
                color: rgba(255, 255, 255, 0.65);
                background: transparent;
                border: none;
            }
        """)
        
        self.total_time_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: 500;
                color: rgba(255, 255, 255, 0.65);
                background: transparent;
                border: none;
            }
        """)
        
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.total_time_label)
        main_layout.addLayout(progress_layout)
        
        main_layout.addSpacing(24)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(35)
        
        self.prev_button.setFixedSize(44, 44)
        self.play_button.setFixedSize(56, 56)
        self.next_button.setFixedSize(44, 44)
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        
        main_layout.addSpacing(18)
        
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(0)
        volume_layout.addSpacing(20)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addSpacing(20)
        main_layout.addLayout(volume_layout)
        
        main_layout.addSpacing(8)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self.clear_layout(item.layout())

    def toggle_view_mode(self):
        self.compact_mode = not self.compact_mode
        
        if self.compact_mode:
            self.setFixedSize(420, 125)
            self.container.setGeometry(0, 0, 420, 125)
            self.setup_compact_layout()
            
            self.view_button.move(312, 8)
            self.lock_button.move(338, 8)
            self.settings_button.move(364, 8)
            self.close_button.move(390, 8)
        else:
            self.setFixedSize(300, 490)
            self.container.setGeometry(0, 0, 300, 490)
            self.setup_nowplaying_layout()
            
            self.view_button.move(168, 8)
            self.lock_button.move(194, 8)
            self.settings_button.move(220, 8)
            self.close_button.move(246, 8)
        
        screen = QApplication.primaryScreen().geometry()
        current_pos = self.pos()
        
        if current_pos.x() + self.width() > screen.width():
            self.move(screen.width() - self.width() - 20, current_pos.y())
        if current_pos.y() + self.height() > screen.height():
            self.move(current_pos.x(), screen.height() - self.height() - 70)
        
        self.save_position()

    def load_settings(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
        except:
            self.settings = {}
        
        if 'opacity' not in self.settings:
            self.settings['opacity'] = 100
        if 'theme' not in self.settings:
            self.settings['theme'] = 'glass'
    
    def save_settings(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.lock_button.set_locked(self.is_locked)
        self.settings['is_locked'] = self.is_locked
        self.save_settings()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, rect.width(), rect.height(), 16, 16)
        
        theme = self.settings.get('theme', 'glass')
        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        
        if theme == 'dark':
            gradient.setColorAt(0, QColor(30, 30, 30, 250))
            gradient.setColorAt(1, QColor(20, 20, 20, 250))
        else:
            gradient.setColorAt(0, QColor(255, 255, 255, 38))
            gradient.setColorAt(1, QColor(255, 255, 255, 20))
        
        painter.fillPath(path, QBrush(gradient))
        
        painter.setPen(QPen(QColor(255, 255, 255, 64), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 15.5, 15.5)

    def on_volume_changed(self, value):
        self.volume_controller.set_volume(value)

    def sync_volume_slider(self):
        current_volume = self.volume_controller.get_volume()
        if abs(self.volume_slider.value() - current_volume) > 2:
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(current_volume)
            self.volume_slider.blockSignals(False)

    def close_application(self):
        self.timer.stop()
        self.volume_sync_timer.stop()
        QApplication.quit()

    def open_settings(self):
        menu = SettingsMenu(self)
        
        screen = QApplication.primaryScreen().geometry()
        button_pos = self.settings_button.mapToGlobal(self.settings_button.rect().bottomLeft())
        
        menu_width = menu.width()
        menu_height = menu.height()
        
        menu_x = button_pos.x() - menu_width + self.settings_button.width()
        menu_y = button_pos.y() + 5
        
        if menu_y + menu_height > screen.height():
            menu_y = self.settings_button.mapToGlobal(self.settings_button.rect().topLeft()).y() - menu_height - 5
        
        if menu_x + menu_width > screen.width():
            menu_x = screen.width() - menu_width - 10
        
        if menu_x < 0:
            menu_x = 10
        
        if menu_y < 0:
            menu_y = 10
        
        menu.move(menu_x, menu_y)
        menu.show()

    def load_position(self):
        if 'x' in self.settings and 'y' in self.settings:
            self.move(self.settings['x'], self.settings['y'])
        else:
            self.position_bottom_right()
    
    def save_position(self):
        self.settings['x'] = self.x()
        self.settings['y'] = self.y()
        self.save_settings()

    def position_bottom_right(self):
        screen = QApplication.primaryScreen().geometry()
        widget_width = self.width()
        widget_height = self.height()
        
        x = screen.width() - widget_width - 20
        y = screen.height() - widget_height - 70
        
        self.move(x, y)

    def on_slider_pressed(self):
        self.is_seeking = True

    def on_slider_released(self):
        self.is_seeking = False
        if self.current_session and self.duration > 0:
            new_position_seconds = (self.progress_bar.value() / 100) * self.duration
            self.seek_to_position(new_position_seconds)

    def seek_to_position(self, position_seconds):
        if self.current_session:
            def seek():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    ticks = int(position_seconds * 10_000_000)
                    loop.run_until_complete(
                        self.current_session.try_change_playback_position_async(ticks)
                    )
                except Exception as e:
                    print(f"Error seeking: {e}")
                finally:
                    loop.close()
            
            thread = threading.Thread(target=seek, daemon=True)
            thread.start()
            QTimer.singleShot(800, self.update_song_info)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_locked:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragging and not self.is_locked:
            current_pos = event.globalPosition().toPoint()
            diff = current_pos - self.drag_position
            self.move(self.pos() + diff)
            self.drag_position = current_pos

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.save_position()

    def format_time(self, seconds):
        if seconds is None or seconds <= 0:
            return "0:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def update_song_info(self):
        if not self.is_seeking:
            self.media_updater.run_async(self.get_media_info())

    def on_media_update(self, info):
        try:
            if info.get('status') in ['no_session', 'error']:
                self.song_title_label.setText("No media playing")
                self.artist_label.setText("Launch Spotify")
                self.is_playing = False
                self.play_button.icon_type = 'play'
                self.play_button.update()
                self.progress_bar.setValue(0)
                self.current_time_label.setText("0:00")
                self.total_time_label.setText("0:00")
                self.duration = 0
                self.album_art_label.pixmap_to_draw = None
                self.album_art_label.update()
                self.current_session = None
                return
            
            title = info['title']
            if len(title) > 32:
                title = title[:29] + "..."
            self.song_title_label.setText(title)
            
            artist = info['artist']
            if len(artist) > 38:
                artist = artist[:35] + "..."
            self.artist_label.setText(artist)
            
            self.is_playing = info['is_playing']
            if self.is_playing:
                self.play_button.icon_type = 'pause'
            else:
                self.play_button.icon_type = 'play'
            self.play_button.update()
            
            current_pos = info.get('position', 0)
            self.duration = info.get('duration', 0)
            
            self.current_time_label.setText(self.format_time(current_pos))
            self.total_time_label.setText(self.format_time(self.duration))
            
            if self.duration > 0 and not self.is_seeking:
                progress = int((current_pos / self.duration) * 100)
                self.progress_bar.setMaximum(100)
                self.progress_bar.setValue(progress)
            
            if info['thumbnail']:
                pixmap = QPixmap()
                pixmap.loadFromData(info['thumbnail'])
                self.album_art_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Error updating UI: {e}")

    async def get_media_info(self):
        try:
            sessions = await MediaManager.request_async()
            current_session = sessions.get_current_session()
            
            if current_session is None:
                self.current_session = None
                return None
            
            self.current_session = current_session
            info = await current_session.try_get_media_properties_async()
            playback_info = current_session.get_playback_info()
            playback_status = playback_info.playback_status
            
            timeline = current_session.get_timeline_properties()
            position = timeline.position.total_seconds() if timeline.position else 0
            duration = timeline.end_time.total_seconds() if timeline.end_time else 0
            
            thumbnail_data = None
            try:
                if info.thumbnail:
                    thumb_stream_ref = info.thumbnail
                    thumb_stream = await thumb_stream_ref.open_read_async()
                    if thumb_stream.size > 0:
                        buffer = Buffer(thumb_stream.size)
                        await thumb_stream.read_async(buffer, thumb_stream.size, InputStreamOptions.READ_AHEAD)
                        thumbnail_data = bytes(buffer)
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
            
            return {
                'title': info.title or 'Unknown title',
                'artist': info.artist or 'Unknown artist',
                'is_playing': playback_status == 4,
                'thumbnail': thumbnail_data,
                'position': position,
                'duration': duration
            }
        except Exception as e:
            print(f"Error getting media info: {e}")
            return None

    def toggle_playback(self):
        if self.current_session:
            self.media_updater.run_async(self.current_session.try_toggle_play_pause_async())
            QTimer.singleShot(300, self.update_song_info)

    def next_song(self):
        if self.current_session:
            self.media_updater.run_async(self.current_session.try_skip_next_async())
            QTimer.singleShot(500, self.update_song_info)

    def previous_song(self):
        if self.current_session:
            self.media_updater.run_async(self.current_session.try_skip_previous_async())
            QTimer.singleShot(500, self.update_song_info)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = SpotifyWidget()
    widget.show()
    sys.exit(app.exec())
