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

from PyQt5 import QtWidgets
from car_detect_esal.gui.main_window import MainWindow

def main():
    """Main application entry point"""
    print("🚗 Car Detection ESAL Analysis System v1.0 시작")
    
    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Car Detection ESAL")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    print("✅ GUI 초기화 완료")
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()