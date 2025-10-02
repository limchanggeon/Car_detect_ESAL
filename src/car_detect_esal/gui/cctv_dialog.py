"""
NTIS CCTV 선택 다이얼로그
"""

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from typing import List, Dict, Optional
from ..api.ntis_client import get_cctv_list

class CCTVSelectionDialog(QtWidgets.QDialog):
    """NTIS CCTV 선택 다이얼로그"""
    
    def __init__(self, service_key: str = None, parent=None):
        super().__init__(parent)
        self.service_key = service_key or "e94df8972e194e489d6abbd7e7bc3469"
        self.selected_cctv = None
        self.cctv_list = []
        
        self._setup_ui()
        self._load_cctv_list()
    
    def _setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("🚨 NTIS 실시간 CCTV 선택")
        self.setModal(True)
        self.resize(800, 600)
        
        # 메인 레이아웃
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 헤더
        header_label = QtWidgets.QLabel("📡 국가교통정보센터 실시간 CCTV")
        header_label.setAlignment(QtCore.Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(52, 152, 219, 0.1), stop:1 rgba(155, 89, 182, 0.1));
                border: 2px solid #3498db;
                border-radius: 10px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
        """)
        layout.addWidget(header_label)
        
        # 검색 영역
        search_frame = QtWidgets.QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        search_layout = QtWidgets.QHBoxLayout(search_frame)
        
        search_layout.addWidget(QtWidgets.QLabel("🔍 검색:"))
        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText("CCTV 이름으로 검색...")
        self.search_line.setStyleSheet("""
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
        search_layout.addWidget(self.search_line)
        
        self.refresh_btn = QtWidgets.QPushButton("🔄 새로고침")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        search_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(search_frame)
        
        # CCTV 목록 테이블
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', 'CCTV 이름', '위치(X)', '위치(Y)', '스트림 URL'])
        
        # 테이블 스타일링
        self.table.setStyleSheet("""
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
        
        # 테이블 설정
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        
        # 컬럼 크기 조정
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)  # 마지막 컬럼(URL)을 늘림
        self.table.setColumnWidth(0, 80)   # ID
        self.table.setColumnWidth(1, 200)  # 이름
        self.table.setColumnWidth(2, 80)   # X
        self.table.setColumnWidth(3, 80)   # Y
        
        layout.addWidget(self.table)
        
        # 상태 라벨
        self.status_label = QtWidgets.QLabel("CCTV 목록을 불러오는 중...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                padding: 5px;
            }
        """)
        layout.addWidget(self.status_label)
        
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
        self.search_line.textChanged.connect(self._filter_table)
        self.refresh_btn.clicked.connect(self._load_cctv_list)
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self._on_double_click)
        self.cancel_btn.clicked.connect(self.reject)
        self.select_btn.clicked.connect(self.accept)
    
    def _load_cctv_list(self):
        """CCTV 목록 로드"""
        self.status_label.setText("🔄 CCTV 목록을 불러오는 중...")
        self.refresh_btn.setEnabled(False)
        
        # 워커 스레드로 API 호출
        self.worker = CCTVFetchWorker(self.service_key)
        self.worker.finished.connect(self._on_cctv_loaded)
        self.worker.error.connect(self._on_cctv_error)
        self.worker.start()
    
    def _on_cctv_loaded(self, cctv_list: List[Dict]):
        """CCTV 목록 로드 완료"""
        self.cctv_list = cctv_list
        self._populate_table(cctv_list)
        self.status_label.setText(f"✅ {len(cctv_list)}개의 CCTV를 찾았습니다.")
        self.refresh_btn.setEnabled(True)
    
    def _on_cctv_error(self, error_msg: str):
        """CCTV 목록 로드 오류"""
        self.status_label.setText(f"❌ 오류: {error_msg}")
        self.refresh_btn.setEnabled(True)
        
        # 오류 메시지 박스
        QtWidgets.QMessageBox.warning(
            self, "CCTV 로드 오류",
            f"CCTV 목록을 불러오는 중 오류가 발생했습니다:\n\n{error_msg}\n\n"
            "• 인터넷 연결을 확인해주세요\n"
            "• API 키가 올바른지 확인해주세요\n"  
            "• 잠시 후 다시 시도해주세요"
        )
    
    def _populate_table(self, cctv_list: List[Dict]):
        """테이블에 CCTV 목록 채우기"""
        self.table.setRowCount(len(cctv_list))
        
        for i, cctv in enumerate(cctv_list):
            # ID
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(cctv.get('id', ''))))
            
            # 이름
            name_item = QtWidgets.QTableWidgetItem(cctv.get('name', ''))
            name_item.setToolTip(cctv.get('name', ''))
            self.table.setItem(i, 1, name_item)
            
            # 좌표
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(cctv.get('coordx', ''))))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(cctv.get('coordy', ''))))
            
            # 스트림 URL
            stream_url = cctv.get('stream_url', '')
            url_item = QtWidgets.QTableWidgetItem(stream_url)
            url_item.setToolTip(stream_url)
            
            # URL이 있으면 초록색, 없으면 빨간색
            if stream_url and stream_url.startswith(('http', 'rtsp')):
                url_item.setForeground(QtGui.QColor('#27ae60'))
            else:
                url_item.setForeground(QtGui.QColor('#e74c3c'))
                url_item.setText('❌ URL 없음')
                
            self.table.setItem(i, 4, url_item)
    
    def _filter_table(self):
        """테이블 필터링"""
        search_text = self.search_line.text().lower()
        
        for i in range(self.table.rowCount()):
            # 이름으로 검색
            name_item = self.table.item(i, 1)
            if name_item:
                name = name_item.text().lower()
                should_show = search_text in name
                self.table.setRowHidden(i, not should_show)
    
    def _on_selection_changed(self):
        """선택 변경"""
        selected_rows = self.table.selectionModel().selectedRows()
        self.select_btn.setEnabled(len(selected_rows) > 0)
        
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.cctv_list):
                self.selected_cctv = self.cctv_list[row]
    
    def _on_double_click(self):
        """더블클릭으로 선택"""
        if self.selected_cctv:
            self.accept()
    
    def get_selected_cctv(self) -> Optional[Dict]:
        """선택된 CCTV 반환"""
        return self.selected_cctv


class CCTVFetchWorker(QtCore.QThread):
    """CCTV 목록을 비동기로 가져오는 워커"""
    
    finished = QtCore.pyqtSignal(list)  # List[Dict] 
    error = QtCore.pyqtSignal(str)
    
    def __init__(self, service_key: str):
        super().__init__()
        self.service_key = service_key
    
    def run(self):
        """워커 실행"""
        try:
            # 서울 지역의 CCTV를 기본으로 가져오기 (좌표 기준)
            cctv_list = get_cctv_list(
                service_key=self.service_key,
                numOfRows=100,  # 100개까지
                pageNo=1,
                # 서울 지역 대략적 좌표 (선택사항)
                # minX=126.8, maxX=127.2, minY=37.4, maxY=37.7
            )
            
            # 스트림 URL이 있는 것만 필터링
            valid_cctvs = []
            for cctv in cctv_list:
                stream_url = cctv.get('stream_url', '')
                if stream_url and (stream_url.startswith('http') or stream_url.startswith('rtsp')):
                    valid_cctvs.append(cctv)
                else:
                    # URL이 없어도 일단 목록에 포함 (사용자가 판단하도록)
                    valid_cctvs.append(cctv)
            
            self.finished.emit(valid_cctvs)
            
        except Exception as e:
            self.error.emit(str(e))