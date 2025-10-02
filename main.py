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
    """한글 폰트 설정 및 렌더링 최적화"""
    # 기본 폰트 설정
    font_families = [
        "Apple SD Gothic Neo",  # macOS 기본 한글 폰트
        "Malgun Gothic",        # Windows 기본 한글 폰트
        "맑은 고딕",             # Windows 한글 폰트
        "SF Pro Display",       # Apple 시스템 폰트
        "Noto Sans CJK KR",     # Google 한글 폰트
        "Nanum Gothic",         # 나눔 고딕
        "sans-serif"            # 대체 폰트
    ]
    
    # 사용 가능한 첫 번째 폰트 찾기
    font_db = QtGui.QFontDatabase()
    available_fonts = font_db.families()
    
    selected_font = "sans-serif"
    for font_family in font_families:
        if font_family in available_fonts:
            selected_font = font_family
            print(f"✅ 선택된 폰트: {selected_font}")
            break
    
    # 기본 애플리케이션 폰트 설정
    font = QtGui.QFont(selected_font, 12)
    font.setStyleHint(QtGui.QFont.SansSerif)
    font.setStyleStrategy(QtGui.QFont.PreferAntialias)
    
    return font

def main():
    """Main application entry point"""
    print("🚗 Car Detection ESAL Analysis System v1.0 시작")
    
    # Create QApplication with proper Korean font support
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Car Detection ESAL")
    app.setApplicationVersion("1.0.0")
    
    # 한글 폰트 설정
    korean_font = setup_korean_font()
    app.setFont(korean_font)
    
    # 텍스트 렌더링 개선
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # GUI 초기화 완료
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()