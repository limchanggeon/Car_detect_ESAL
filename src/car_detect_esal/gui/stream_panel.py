"""
Stream panel widget containing video display and controls
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from typing import Optional
from .video_label import VideoLabel
from .stream_worker import StreamWorker
from ..core.detector import VehicleDetector
from ..core.esal_calculator import ESALCalculator

class StreamPanel(QtWidgets.QWidget):
    """단일 스트림을 위한 패널 위젯"""
    
    def __init__(self, source: str, detector: VehicleDetector, performance_config: dict = None, 
                 db_manager=None, camera_id: str = None):
        super().__init__()
        self.source = source
        self.detector = detector
        self.performance_config = performance_config or {"sleep_time": 0.1, "imgsz": 640}
        self.roi = None
        self.worker = None
        self.esal_calculator = ESALCalculator()
        
        # 데이터베이스 관련
        self.db_manager = db_manager
        self.camera_id = camera_id
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 구성 요소 설정"""
        # 메인 레이아웃
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(4)
        self.setLayout(self.layout)
        
        # 심플하고 깔끔한 다크 테마
        self.setStyleSheet("""
            StreamPanel {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QPushButton {
                background: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: #3d3d3d;
                border: 1px solid #4d4d4d;
            }
            QPushButton:pressed {
                background: #252525;
            }
            QPushButton:disabled {
                background: #252525;
                color: #666666;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
            }
        """)

        # 상단 정보바 (URL + 상태)
        info_layout = QtWidgets.QHBoxLayout()
        info_layout.setSpacing(8)
        
        # URL 라벨 (짧게 표시)
        source_name = self.source.split('/')[-1] if '/' in self.source else self.source
        if len(source_name) > 30:
            source_name = source_name[:27] + "..."
        self.title_label = QtWidgets.QLabel(source_name)
        self.title_label.setStyleSheet("font-weight: bold; color: #a0a0a0;")
        info_layout.addWidget(self.title_label)
        
        info_layout.addStretch()
        
        # ROI 상태 라벨
        self.roi_label = QtWidgets.QLabel("Full Frame")
        self.roi_label.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
        self.roi_label.setToolTip("Drag to select ROI | Double-click to reset")
        info_layout.addWidget(self.roi_label)
        
        # 상태 라벨
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #808080; font-size: 10px;")
        info_layout.addWidget(self.status_label)
        
        self.layout.addLayout(info_layout)

        # 비디오 영역 (유연한 크기, 비율 유지)
        self.video = VideoLabel()
        self.video.setMinimumSize(320, 240)
        self.video.setStyleSheet("background: #000000; border: 1px solid #2d2d2d;")
        self.layout.addWidget(self.video)

        # 하단 컨트롤바 (버튼 + 통계)
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.setSpacing(4)
        
        # 컨트롤 버튼들
        self.start_btn = QtWidgets.QPushButton("Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #2d5016;
                border: 1px solid #3d6026;
            }
            QPushButton:hover {
                background: #3d6026;
            }
        """)
        
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #5c1a1a;
                border: 1px solid #6c2a2a;
            }
            QPushButton:hover {
                background: #6c2a2a;
            }
        """)
        
        bottom_layout.addWidget(self.start_btn)
        bottom_layout.addWidget(self.stop_btn)
        
        bottom_layout.addStretch()
        
        # FPS 및 통계 라벨
        self.fps_label = QtWidgets.QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet("color: #808080; font-size: 10px;")
        bottom_layout.addWidget(self.fps_label)
        
        self.count_label = QtWidgets.QLabel("Count: 0")
        self.count_label.setStyleSheet("color: #808080; font-size: 10px;")
        bottom_layout.addWidget(self.count_label)
        
        self.layout.addLayout(bottom_layout)

    def _connect_signals(self):
        """시그널 연결"""
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.video.roi_changed.connect(self.on_roi_changed)
    
    def on_roi_changed(self, roi):
        """ROI 변경 처리"""
        self.roi = roi
        if self.worker is not None:
            self.worker.roi = roi
        
        if roi:
            x, y, w, h = roi
            self.roi_label.setText(f"ROI: {w}×{h}")
            self.roi_label.setStyleSheet("color: #FF9800; font-size: 10px; font-weight: bold;")
            print(f"[StreamPanel] ROI set: x={x}, y={y}, w={w}, h={h}")
        else:
            self.roi_label.setText("Full Frame")
            self.roi_label.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
            print(f"[StreamPanel] ROI cleared (detecting full frame)")

    def start(self):
        """스트림 시작"""
        if self.worker is not None and self.worker.isRunning():
            return
            
        # 데이터베이스 매니저와 카메라 ID를 포함하여 StreamWorker 생성
        self.worker = StreamWorker(
            self.source, 
            self.detector, 
            self.performance_config,
            self.db_manager,
            self.camera_id
        )
        
        self.worker.frame_ready.connect(self.on_frame)
        self.worker.status.connect(self.on_status)
        self.worker.count_changed.connect(self.on_count_changed)
        
        if self.roi is not None:
            self.worker.roi = self.roi
            
        self.worker.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop(self):
        """스트림 중지"""
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_frame(self, qimg: QtGui.QImage):
        """프레임 업데이트"""
        try:
            self.video.set_qimage(qimg)
        except Exception as e:
            print(f"[StreamPanel] Frame error: {e}")

    def on_status(self, msg: str):
        """상태 메시지 업데이트"""
        self.fps_label.setText(msg)
        
        if "Running" in msg or "FPS" in msg:
            self.status_label.setText("Running")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
        elif "Stopped" in msg:
            self.status_label.setText("Stopped")
            self.status_label.setStyleSheet("color: #f44336; font-size: 10px; font-weight: bold;")

    def on_count_changed(self, counts: dict):
        """카운트 변경 처리"""
        try:
            if not isinstance(counts, dict):
                return
            
            total = sum(counts.values())
            self.count_label.setText(f"Count: {total}")
            
        except Exception as e:
            print(f"[StreamPanel] Count error: {e}")