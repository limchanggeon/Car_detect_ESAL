#!/usr/bin/env python3
"""
Car Detection ESAL Analysis System

Entry point for the GUI application
"""

import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from PyQt5 import QtWidgets, QtCore, QtGui
from car_detect_esal.gui.main_window import MainWindow

def setup_korean_font():
    """Setup Korean font and rendering optimization"""
    # Default font settings
    font_families = [
        "Arial",
        "Helvetica",
        "sans-serif"
    ]
    
    # Find first available font
    font_db = QtGui.QFontDatabase()
    available_fonts = font_db.families()
    
    selected_font = "sans-serif"
    for font_family in font_families:
        if font_family in available_fonts:
            selected_font = font_family
            print(f"Selected font: {selected_font}")
            break
    
    # Set default application font
    font = QtGui.QFont(selected_font, 11)
    font.setStyleHint(QtGui.QFont.SansSerif)
    font.setStyleStrategy(QtGui.QFont.PreferAntialias)
    
    return font

def main():
    """Main application entry point"""
    print("Car Detection ESAL Analysis System v1.0 Starting...")
    
    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Car Detection ESAL")
    app.setApplicationVersion("1.0.0")
    
    # Set font
    app_font = setup_korean_font()
    app.setFont(app_font)
    
    # Improve text rendering
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    # AA_EnableHighDpiScaling must be set before QCoreApplication is created
    # so we skip it here
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()