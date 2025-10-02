"""
Main application window
"""

import sys
import os
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets

from ..core import Config, VehicleDetector
from ..core.performance_config import PerformanceConfig
from ..api import get_cctv_list
from .stream_panel import StreamPanel

try:
    from PyQt5 import QtWebEngineWidgets, QtWebChannel
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class NtisFetchWorker(QtCore.QThread):
    """NTIS에서 CCTV 목록을 가져오는 비동기 워커"""
    finished = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)

    def __init__(self, service_key: str = None, parent=None):
        super().__init__(parent)
        self.service_key = service_key
        self._running = True

    def run(self):
        try:
            lst = get_cctv_list(self.service_key)
            self.finished.emit(lst)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QtWidgets.QMainWindow):
    """메인 애플리케이션 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.detector = None
        self.panels = []
        self._cols = 2
        
        # 현재 성능 설정 (나노모델을 위해 fast를 기본으로)
        self.current_performance_preset = "fast"
        
        self._setup_ui()
        self._load_default_model()

    def _setup_ui(self):
        """UI 구성 요소 설정"""
        self.setWindowTitle("🚗 Car Detection ESAL Analysis System v1.0")
        self.setWindowIcon(self._create_app_icon())
        # 탐지화면 중심의 더 큰 창 크기로 설정
        self.resize(1400, 1000)
        
        # 메인 위젯과 수평 레이아웃 (탐지화면 중심)
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 왼쪽: 탐지 화면 영역 (메인)
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 오른쪽: 컨트롤 패널 (고정 폭)
        right_widget = QtWidgets.QWidget()
        right_widget.setFixedWidth(400)  # 고정 폭으로 설정
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 현대적이고 아름다운 애플리케이션 스타일 with 한글 폰트 지원
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #2c3e50;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                margin: 15px 5px;
                padding-top: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(248, 250, 252, 0.9));
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 5px 15px;
                color: white;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6fd8, stop:1 #6a4c93);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4c63d2, stop:1 #5d4e75);
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
            QComboBox {
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                padding: 8px 12px;
                background: white;
                min-height: 20px;
                font-size: 13px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
            QComboBox:focus {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #667eea;
                margin-right: 5px;
            }
            QSpinBox, QDoubleSpinBox {
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                padding: 8px;
                background: white;
                min-height: 20px;
                font-size: 13px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #667eea;
            }
            QLabel {
                color: #2c3e50;
                font-size: 13px;
                font-weight: 500;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6a4c93);
            }
        """)
        
        # 컨트롤 패널들을 오른쪽에 배치
        self._create_control_panel(right_layout)
        self._create_settings_panel(right_layout)
        self._create_performance_panel(right_layout)
        
        # 탐지 화면 영역을 왼쪽에 배치 (메인)
        self._create_stream_area(left_layout)
        
        # 레이아웃에 위젯들 추가
        main_layout.addWidget(left_widget, 3)   # 탐지화면이 더 넓게
        main_layout.addWidget(right_widget, 1)  # 컨트롤 패널은 좁게

    def _create_app_icon(self):
        """애플리케이션 아이콘 생성"""
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtGui.QColor('#4CAF50'))
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtGui.QColor('white'), 2))
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, "🚗")
        painter.end()
        return QtGui.QIcon(pixmap)

    def _create_control_panel(self, parent_layout):
        """상단 컨트롤 패널 생성"""
        control_group = QtWidgets.QGroupBox("📡 스트림 관리")
        control_layout = QtWidgets.QVBoxLayout(control_group)
        
        # 스트림 입력
        input_layout = QtWidgets.QHBoxLayout()
        
        self.input_line = QtWidgets.QLineEdit()
        self.input_line.setPlaceholderText("RTSP URL 또는 비디오 파일 경로를 입력하세요...")
        self.input_line.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        
        self.add_btn = QtWidgets.QPushButton("➕ 스트림 추가")
        self.add_demo_btn = QtWidgets.QPushButton("🎬 데모 비디오")
        self.ntis_btn = QtWidgets.QPushButton("📡 NTIS 카메라")
        
        for btn in [self.add_btn, self.add_demo_btn, self.ntis_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #1976D2; }
                QPushButton:pressed { background: #0D47A1; }
            """)
        
        input_layout.addWidget(self.input_line, 3)
        input_layout.addWidget(self.add_btn)
        input_layout.addWidget(self.add_demo_btn)
        input_layout.addWidget(self.ntis_btn)
        
        # 전체 제어 버튼
        global_layout = QtWidgets.QHBoxLayout()
        self.start_all_btn = QtWidgets.QPushButton("▶️ 모두 시작")
        self.stop_all_btn = QtWidgets.QPushButton("⏹️ 모두 중지")
        
        self.start_all_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: #45a049; }
        """)
        
        self.stop_all_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: #da190b; }
        """)
        
        global_layout.addStretch()
        global_layout.addWidget(self.start_all_btn)
        global_layout.addWidget(self.stop_all_btn)
        global_layout.addStretch()
        
        control_layout.addLayout(input_layout)
        control_layout.addLayout(global_layout)
        parent_layout.addWidget(control_group)
        
        # 시그널 연결
        self.add_btn.clicked.connect(self._add_stream_from_input)
        self.add_demo_btn.clicked.connect(self._select_demo_videos)
        self.ntis_btn.clicked.connect(self._show_ntis_dialog)
        self.start_all_btn.clicked.connect(self._start_all)
        self.stop_all_btn.clicked.connect(self._stop_all)

    def _create_settings_panel(self, parent_layout):
        """설정 패널 생성"""
        settings_group = QtWidgets.QGroupBox("⚙️ 탐지 설정")
        settings_layout = QtWidgets.QHBoxLayout(settings_group)
        
        # 모델 설정
        model_layout = QtWidgets.QHBoxLayout()
        model_layout.addWidget(QtWidgets.QLabel("🤖 모델:"))
        
        self.model_line = QtWidgets.QLineEdit(str(self.config.DEFAULT_MODEL_PATH))
        self.model_browse = QtWidgets.QPushButton("📁 찾기")
        self.model_load = QtWidgets.QPushButton("🔄 로드")
        
        model_layout.addWidget(self.model_line, 2)
        model_layout.addWidget(self.model_browse)
        model_layout.addWidget(self.model_load)
        
        # 탐지 파라미터
        param_layout = QtWidgets.QHBoxLayout()
        param_layout.addWidget(QtWidgets.QLabel("📏 이미지 크기:"))
        
        self.imgsz_spin = QtWidgets.QSpinBox()
        self.imgsz_spin.setRange(128, 2048)
        self.imgsz_spin.setValue(self.config.DEFAULT_IMGSZ)
        param_layout.addWidget(self.imgsz_spin)
        
        param_layout.addWidget(QtWidgets.QLabel("🎯 신뢰도:"))
        self.conf_spin = QtWidgets.QDoubleSpinBox()
        self.conf_spin.setRange(0.01, 1.0)
        self.conf_spin.setSingleStep(0.01)
        self.conf_spin.setValue(self.config.DEFAULT_CONF)
        param_layout.addWidget(self.conf_spin)
        
        settings_layout.addLayout(model_layout, 2)
        settings_layout.addLayout(param_layout, 1)
        parent_layout.addWidget(settings_group)
        
        # 시그널 연결
        self.model_browse.clicked.connect(self._browse_model)
        self.model_load.clicked.connect(self._load_model)

    def _create_performance_panel(self, parent_layout):
        """성능 최적화 패널 생성"""
        perf_group = QtWidgets.QGroupBox("⚡ 성능 최적화 (FPS 개선)")
        perf_layout = QtWidgets.QHBoxLayout(perf_group)
        
        # 성능 프리셋 선택
        preset_layout = QtWidgets.QVBoxLayout()
        preset_layout.addWidget(QtWidgets.QLabel("🚀 성능 프리셋:"))
        
        self.perf_combo = QtWidgets.QComboBox()
        for preset_name in PerformanceConfig.get_preset_names():
            preset_info = PerformanceConfig.get_preset(preset_name)
            self.perf_combo.addItem(f"{preset_info['name']}", preset_name)
        
        # 기본값을 "fast"로 설정 (나노모델에 더 적합)
        for i in range(self.perf_combo.count()):
            if self.perf_combo.itemData(i) == "fast":
                self.perf_combo.setCurrentIndex(i)
                break
        
        self.perf_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
                min-width: 200px;
            }
            QComboBox:hover {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        
        preset_layout.addWidget(self.perf_combo)
        
        # 현재 설정 표시
        self.perf_info_label = QtWidgets.QLabel()
        self.perf_info_label.setWordWrap(True)
        self.perf_info_label.setStyleSheet("""
            QLabel {
                background: #e8f4f8;
                border: 1px solid #b3d9e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                color: #2c3e50;
            }
        """)
        
        # FPS 목표 표시
        fps_layout = QtWidgets.QVBoxLayout()
        fps_layout.addWidget(QtWidgets.QLabel("📊 예상 FPS:"))
        
        self.fps_target_label = QtWidgets.QLabel("10 FPS")
        self.fps_target_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(76, 175, 80, 0.1), stop:1 rgba(139, 195, 74, 0.1));
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                color: #2e7d32;
                text-align: center;
            }
        """)
        fps_layout.addWidget(self.fps_target_label)
        
        # 이제 정보 업데이트 (모든 위젯이 생성된 후)
        self._update_performance_info()
        
        # 적용 버튼
        self.apply_perf_btn = QtWidgets.QPushButton("✅ 설정 적용")
        self.apply_perf_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
        """)
        
        # 레이아웃 구성
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addLayout(preset_layout)
        left_layout.addWidget(self.perf_info_label)
        
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addLayout(fps_layout)
        right_layout.addWidget(self.apply_perf_btn)
        
        perf_layout.addLayout(left_layout, 2)
        perf_layout.addLayout(right_layout, 1)
        
        parent_layout.addWidget(perf_group)
        
        # 시그널 연결
        self.perf_combo.currentIndexChanged.connect(self._on_performance_preset_changed)
        self.apply_perf_btn.clicked.connect(self._apply_performance_settings)

    def _update_performance_info(self):
        """성능 설정 정보 업데이트"""
        preset_name = self.current_performance_preset
        preset = PerformanceConfig.get_preset(preset_name)
        
        info_text = f"""
🔧 해상도: {preset['imgsz']}x{preset['imgsz']}
🎯 신뢰도 임계값: {preset['conf']}
⏱️ 처리 간격: {preset['sleep_time']}초
📝 {preset['description']}
        """.strip()
        
        self.perf_info_label.setText(info_text)
        self.fps_target_label.setText(f"{preset['fps_target']} FPS")

    def _on_performance_preset_changed(self):
        """성능 프리셋 변경 시"""
        preset_name = self.perf_combo.currentData()
        if preset_name:
            self.current_performance_preset = preset_name
            self._update_performance_info()

    def _apply_performance_settings(self):
        """성능 설정 적용"""
        preset = PerformanceConfig.get_preset(self.current_performance_preset)
        
        # 기존 설정 UI 업데이트
        self.imgsz_spin.setValue(preset['imgsz'])
        self.conf_spin.setValue(preset['conf'])
        
        # 모델 재로드 (새로운 설정으로)
        if self.detector:
            try:
                model_path = self.model_line.text()
                self.detector = VehicleDetector(
                    model_path, 
                    imgsz=preset['imgsz'], 
                    conf=preset['conf']
                )
                
                # 실행 중인 스트림들에 새 설정 적용
                for panel in self.panels:
                    panel.detector = self.detector
                    panel.performance_config = preset  # 성능 설정도 업데이트
                    
                    # 워커가 실행 중이면 새로운 설정으로 재시작
                    if hasattr(panel, 'worker') and panel.worker and panel.worker.isRunning():
                        panel.stop()  # 기존 워커 중지
                        QtCore.QTimer.singleShot(500, panel.start)  # 0.5초 후 새 설정으로 재시작
                
                QtWidgets.QMessageBox.information(
                    self, "설정 적용 완료",
                    f"✅ {PerformanceConfig.get_preset(self.current_performance_preset)['name']} 설정이 적용되었습니다!\n\n"
                    f"🔧 해상도: {preset['imgsz']}x{preset['imgsz']}\n"
                    f"🎯 신뢰도: {preset['conf']}\n"
                    f"📊 목표 FPS: {preset['fps_target']}"
                )
                
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, "설정 적용 오류", 
                    f"성능 설정 적용 중 오류가 발생했습니다:\n{e}"
                )

    def _create_stream_area(self, parent_layout):
        """스트림 패널 영역 생성"""
        # 스크롤 영역
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
        """)
        
        self.panels_widget = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(self.panels_widget)
        self.grid.setSpacing(15)
        self.grid.setContentsMargins(10, 10, 10, 10)
        
        self.scroll.setWidget(self.panels_widget)
        parent_layout.addWidget(self.scroll, 1)

    def _load_default_model(self):
        """기본 모델 로드"""
        model_path = Path(self.model_line.text().strip())
        if model_path.exists():
            try:
                # 현재 성능 설정을 사용해서 모델 로드
                from ..core.performance_config import PerformanceConfig
                preset = PerformanceConfig.get_preset(self.current_performance_preset)
                
                self.detector = VehicleDetector(
                    str(model_path),
                    imgsz=preset['imgsz'],
                    conf=preset['conf']
                )
                print(f"[GUI] 기본 모델 로드 완료: {model_path} (성능설정: {self.current_performance_preset})")
            except Exception as e:
                print(f"[GUI] 기본 모델 로드 실패: {e}")

    def _browse_model(self):
        """모델 파일 선택"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "모델 파일 선택",
            str(self.config.PROJECT_ROOT / "weights"),
            "PyTorch Model (*.pt *.pth);;All Files (*)"
        )
        if file_path:
            self.model_line.setText(file_path)

    def _load_model(self):
        """모델 로드"""
        model_path = Path(self.model_line.text().strip())
        if not model_path.exists():
            QtWidgets.QMessageBox.warning(
                self, "모델 로드", f"파일을 찾을 수 없습니다: {model_path}"
            )
            return
            
        try:
            # 현재 성능 설정으로 모델 로드
            from ..core.performance_config import PerformanceConfig
            preset = PerformanceConfig.get_preset(self.current_performance_preset)
            
            self.detector = VehicleDetector(
                str(model_path),
                imgsz=preset['imgsz'],
                conf=preset['conf']
            )
            QtWidgets.QMessageBox.information(
                self, "모델 로드", 
                f"모델 로드 완료: {model_path.name}\n"
                f"성능 설정: {preset['name']}\n"
                f"해상도: {preset['imgsz']}x{preset['imgsz']}\n"
                f"신뢰도: {preset['conf']}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "모델 로드 실패", f"모델 로드 중 오류: {e}"
            )

    def _add_stream_from_input(self):
        """입력란에서 스트림 추가"""
        source = self.input_line.text().strip()
        if source:
            self._add_stream(source)
            self.input_line.clear()

    def _add_stream(self, source: str):
        """스트림 패널 추가"""
        if self.detector is None:
            QtWidgets.QMessageBox.warning(
                self, "모델 필요", "먼저 탐지 모델을 로드해주세요."
            )
            return
        
        # 현재 성능 설정 가져오기
        from ..core.performance_config import PerformanceConfig
        perf_config = PerformanceConfig.get_preset(self.current_performance_preset)
        
        panel = StreamPanel(source, self.detector, perf_config)
        
        # 그리드에 배치
        idx = len(self.panels)
        row = idx // self._cols
        col = idx % self._cols
        self.grid.addWidget(panel, row, col)
        
        self.panels.append(panel)

    def _select_demo_videos(self):
        """데모 비디오 선택"""
        demo_dir = self.config.PROJECT_ROOT / "demo_videos"
        start_dir = str(demo_dir) if demo_dir.exists() else str(Path.cwd())
        
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "데모 비디오 선택", start_dir,
            "Video Files (*.mp4 *.mov *.avi *.mkv);;All Files (*)"
        )
        
        for file_path in files:
            self._add_stream(file_path)

    def _show_ntis_dialog(self):
        """NTIS 카메라 선택 다이얼로그"""
        try:
            # API 상태 안내 메시지
            result = QtWidgets.QMessageBox.question(
                self, "NTIS CCTV 연동",
                "🚨 NTIS 실시간 CCTV 연동\n\n"
                "현재 공공데이터포털 API 서버 연결에 문제가 있어\n"
                "시뮬레이션 모드로 진행합니다.\n\n"
                "다음 옵션을 사용할 수 있습니다:\n"
                "• 📹 테스트용 샘플 CCTV\n"
                "• 🔗 직접 스트림 URL 입력 (RTSP/HTTP)\n"
                "• 📁 로컬 비디오 파일\n\n"
                "계속 진행하시겠습니까?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes
            )
            
            if result == QtWidgets.QMessageBox.Yes:
                self._show_simulation_dialog()
                    
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "NTIS 연동 오류",
                f"NTIS CCTV 연동 중 오류가 발생했습니다:\n\n{e}\n\n"
                "• 인터넷 연결을 확인해주세요\n"
                "• 필요한 라이브러리가 설치되어 있는지 확인해주세요"
            )
    
    def _show_simulation_dialog(self):
        """시뮬레이션 다이얼로그 표시"""
        try:
            from .ntis_simulation_dialog import NTISSimulationDialog
            
            dialog = NTISSimulationDialog(self)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                selected_stream = dialog.get_selected_stream()
                if selected_stream:
                    self._process_selected_stream(selected_stream)
        except ImportError as e:
            QtWidgets.QMessageBox.critical(
                self, "모듈 오류",
                f"시뮬레이션 다이얼로그를 로드할 수 없습니다:\n{e}"
            )
    
    def _process_selected_cctv(self, selected_cctv: dict):
        """선택된 CCTV 처리"""
        stream_url = selected_cctv.get('stream_url', '')
        cctv_name = selected_cctv.get('name', 'Unknown CCTV')
        
        if not stream_url:
            QtWidgets.QMessageBox.warning(
                self, "스트림 URL 없음",
                f"선택한 CCTV '{cctv_name}'에 스트림 URL이 없습니다.\n\n"
                "다른 CCTV를 선택해주세요."
            )
            return
        
        # 스트림 추가
        self._add_stream(stream_url)
        
        # 성공 메시지
        QtWidgets.QMessageBox.information(
            self, "CCTV 추가 완료",
            f"✅ '{cctv_name}' CCTV가 추가되었습니다!\n\n"
            f"🔗 URL: {stream_url[:50]}{'...' if len(stream_url) > 50 else ''}\n"
            f"📍 위치: ({selected_cctv.get('coordx', 'N/A')}, {selected_cctv.get('coordy', 'N/A')})\n\n"
            "▶️ 시작 버튼을 클릭하여 실시간 탐지를 시작하세요."
        )
    
    def _process_selected_stream(self, selected_stream: dict):
        """선택된 스트림 처리"""  
        stream_url = selected_stream.get('stream_url', '')
        stream_name = selected_stream.get('name', 'Unknown Stream')
        
        if not stream_url:
            QtWidgets.QMessageBox.warning(
                self, "스트림 URL 없음",
                "스트림 URL이 비어있습니다."
            )
            return
        
        # 스트림 추가
        self._add_stream(stream_url)
        
        # 성공 메시지
        QtWidgets.QMessageBox.information(
            self, "스트림 추가 완료",
            f"✅ '{stream_name}' 스트림이 추가되었습니다!\n\n"
            f"🔗 URL: {stream_url[:50]}{'...' if len(stream_url) > 50 else ''}\n"
            f"📍 위치: {selected_stream.get('location', 'N/A')}\n\n"
            "▶️ 시작 버튼을 클릭하여 실시간 탐지를 시작하세요."
        )

    def _start_all(self):
        """모든 스트림 시작"""
        for panel in self.panels:
            if not panel.worker or not panel.worker.isRunning():
                panel.start()

    def _stop_all(self):
        """모든 스트림 중지"""
        for panel in self.panels:
            panel.stop()

    def closeEvent(self, event):
        """애플리케이션 종료 시 정리"""
        self._stop_all()
        # 워커 스레드들이 종료될 시간을 줌
        QtCore.QTimer.singleShot(500, lambda: super().closeEvent(event))