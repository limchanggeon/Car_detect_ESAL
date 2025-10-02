"""
NTIS CCTV 시뮬레이션 및 직접 URL 입력 다이얼로그  
"""

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from typing import List, Dict, Optional

class NTISSimulationDialog(QtWidgets.QDialog):
    """NTIS CCTV 시뮬레이션 다이얼로그 (실제 API 연결 안될 때 대체용)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_stream = None
        self._setup_ui()
        self._load_sample_data()
    
    def _setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("🚨 NTIS 실시간 CCTV (시뮬레이션 모드)")
        self.setModal(True)
        self.resize(900, 700)
        
        # 메인 레이아웃
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 헤더
        header_label = QtWidgets.QLabel("📡 국가교통정보센터 CCTV (데모 모드)")
        header_label.setAlignment(QtCore.Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(231, 76, 60, 0.1), stop:1 rgba(155, 89, 182, 0.1));
                border: 2px solid #e74c3c;
                border-radius: 10px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
        """)
        layout.addWidget(header_label)
        
        # 알림 메시지
        info_label = QtWidgets.QLabel(
            "⚠️ NTIS API 서버에 연결할 수 없어 시뮬레이션 모드로 실행됩니다.\n"
            "아래에서 테스트용 CCTV를 선택하거나 직접 스트림 URL을 입력하세요."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 6px;
                padding: 10px;
                color: #856404;
                font-size: 12px;
            }
        """)
        layout.addWidget(info_label)
        
        # 탭 위젯
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 6px;
                background: white;
            }
            QTabBar::tab {
                background: #f8f9fa;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)
        
        # 탭 1: 샘플 CCTV
        self._create_sample_tab()
        
        # 탭 2: 직접 URL 입력
        self._create_url_input_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 버튼 영역
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QtWidgets.QPushButton("❌ 취소")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        
        self.select_btn = QtWidgets.QPushButton("✅ 선택")
        self.select_btn.setEnabled(False)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #219a52;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.select_btn)
        layout.addLayout(button_layout)
        
        # 시그널 연결
        self.cancel_btn.clicked.connect(self.reject)
        self.select_btn.clicked.connect(self.accept)
    
    def _create_sample_tab(self):
        """샘플 CCTV 탭"""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        # 설명
        desc_label = QtWidgets.QLabel("📹 테스트용 샘플 CCTV 목록")
        desc_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        layout.addWidget(desc_label)
        
        # 샘플 CCTV 테이블
        self.sample_table = QtWidgets.QTableWidget()
        self.sample_table.setColumnCount(4)
        self.sample_table.setHorizontalHeaderLabels(['이름', '위치', '타입', '스트림 URL'])
        
        # 테이블 스타일
        self.sample_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                gridline-color: #e0e0e0;
                selection-background-color: rgba(52, 152, 219, 0.3);
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background: rgba(52, 152, 219, 0.2);
            }
            QHeaderView::section {
                background: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #3498db;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        self.sample_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.sample_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        
        # 컬럼 크기 조정
        header = self.sample_table.horizontalHeader() 
        self.sample_table.setColumnWidth(0, 200)  # 이름
        self.sample_table.setColumnWidth(1, 150)  # 위치
        self.sample_table.setColumnWidth(2, 100)  # 타입
        header.setStretchLastSection(True)        # URL
        
        layout.addWidget(self.sample_table)
        
        # 시그널 연결
        self.sample_table.selectionModel().selectionChanged.connect(self._on_sample_selection_changed)
        self.sample_table.doubleClicked.connect(self._on_sample_double_click)
        
        self.tab_widget.addTab(tab, "📹 샘플 CCTV")
    
    def _create_url_input_tab(self):
        """직접 URL 입력 탭"""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        # 설명
        desc_label = QtWidgets.QLabel("🔗 직접 스트림 URL 입력")
        desc_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        layout.addWidget(desc_label)
        
        # URL 입력 영역
        url_frame = QtWidgets.QFrame()
        url_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        url_layout = QtWidgets.QVBoxLayout(url_frame)
        
        # 스트림 이름
        url_layout.addWidget(QtWidgets.QLabel("CCTV 이름:"))
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("예: 강남역 사거리 CCTV")
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        url_layout.addWidget(self.name_input)
        
        url_layout.addSpacing(10)
        
        # 스트림 URL
        url_layout.addWidget(QtWidgets.QLabel("스트림 URL:"))
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("예시 URL을 복사해서 사용하거나 직접 입력하세요")
        # 기본값으로 테스트 가능한 URL 설정
        self.url_input.setText("http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4")
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        url_layout.addWidget(self.url_input)
        
        # URL 형식 안내 및 예시
        format_info = QtWidgets.QLabel(
            "💡 지원되는 형식 및 예시:\n\n"
            "• RTSP 스트림:\n"
            "  rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4\n\n"
            "• HTTP MP4:\n"
            "  http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4\n\n"
            "• HTTP Live Streaming:\n"
            "  http://server/stream.m3u8\n\n"
            "• 로컬 파일:\n"
            "  ./demo_videos/video.mp4\n\n"
            "• IP 카메라 (일반적인 형식):\n"
            "  rtsp://admin:password@192.168.1.100:554/stream"
        )
        format_info.setStyleSheet("""
            QLabel {
                background: #e8f4f8;
                border: 1px solid #b3d9e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 11px;
                color: #2c3e50;
            }
        """)
        url_layout.addWidget(format_info)
        
        layout.addWidget(url_frame)
        layout.addStretch()
        
        # 시그널 연결
        self.name_input.textChanged.connect(self._on_url_input_changed)
        self.url_input.textChanged.connect(self._on_url_input_changed)
        
        self.tab_widget.addTab(tab, "🔗 직접 입력")
    
    def _load_sample_data(self):
        """샘플 데이터 로드"""
        # 테스트용 샘플 CCTV 데이터 (실제 사용 가능한 URL 포함)
        sample_data = [
            {
                'name': '테스트용 로컬 비디오 1',
                'location': '로컬',
                'type': 'MP4',
                'url': './demo_videos/화면 기록 2025-08-22 오후 4.34.08.mp4'
            },
            {
                'name': '테스트용 로컬 비디오 2', 
                'location': '로컬',
                'type': 'MP4',
                'url': './demo_videos/화면 기록 2025-08-26 오후 3.29.27.mp4'
            },
            {
                'name': 'Big Buck Bunny (테스트 스트림)',
                'location': '인터넷',
                'type': 'HTTP',
                'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
            },
            {
                'name': 'Sintel (테스트 스트림)',
                'location': '인터넷', 
                'type': 'HTTP',
                'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4'
            },
            {
                'name': '샘플 RTSP 스트림',
                'location': '시뮬레이션',
                'type': 'RTSP',
                'url': 'rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4'
            },
            {
                'name': '직접 입력하기',
                'location': '사용자 정의',
                'type': 'Custom',
                'url': '여기를 선택하면 직접 입력 탭으로 이동합니다'
            }
        ]
        
        self.sample_data = sample_data
        self.sample_table.setRowCount(len(sample_data))
        
        for i, item in enumerate(sample_data):
            self.sample_table.setItem(i, 0, QtWidgets.QTableWidgetItem(item['name']))
            self.sample_table.setItem(i, 1, QtWidgets.QTableWidgetItem(item['location']))
            self.sample_table.setItem(i, 2, QtWidgets.QTableWidgetItem(item['type']))
            
            url_item = QtWidgets.QTableWidgetItem(item['url'])
            url_item.setToolTip(item['url'])
            
            # 로컬 파일이면 초록색, 원격이면 주황색
            if item['url'].startswith('./') or item['url'].startswith('/'):
                url_item.setForeground(QtGui.QColor('#27ae60'))
            else:
                url_item.setForeground(QtGui.QColor('#f39c12'))
                
            self.sample_table.setItem(i, 3, url_item)
    
    def _on_sample_selection_changed(self):
        """샘플 선택 변경"""
        selected_rows = self.sample_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.sample_data):
                # '직접 입력하기' 선택 시 URL 입력 탭으로 전환
                if self.sample_data[row]['name'] == '직접 입력하기':
                    self.tab_widget.setCurrentIndex(1)  # URL 입력 탭으로 전환
                    self.selected_stream = None
                    self.select_btn.setEnabled(False)
                else:
                    self.selected_stream = {
                        'name': self.sample_data[row]['name'],
                        'stream_url': self.sample_data[row]['url'],
                        'location': self.sample_data[row]['location'],
                        'type': self.sample_data[row]['type']
                    }
                    self.select_btn.setEnabled(True)
        else:
            self.selected_stream = None
            self.select_btn.setEnabled(False)
    
    def _on_sample_double_click(self):
        """샘플 더블클릭"""
        if self.selected_stream:
            self.accept()
    
    def _on_url_input_changed(self):
        """URL 입력 변경"""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if name and url:
            self.selected_stream = {
                'name': name,
                'stream_url': url,
                'location': '사용자 입력',
                'type': 'Custom'
            }
            self.select_btn.setEnabled(True)
        else:
            if self.tab_widget.currentIndex() == 1:  # URL 입력 탭이 활성화된 경우
                self.selected_stream = None
                self.select_btn.setEnabled(False)
    
    def get_selected_stream(self) -> Optional[Dict]:
        """선택된 스트림 반환"""
        return self.selected_stream