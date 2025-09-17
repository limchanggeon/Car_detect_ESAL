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
    
    def __init__(self, source: str, detector: VehicleDetector, performance_config: dict = None):
        super().__init__()
        self.source = source
        self.detector = detector
        self.performance_config = performance_config or {"sleep_time": 0.1, "imgsz": 640}
        self.roi = None
        self.worker = None
        self.esal_calculator = ESALCalculator()
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 구성 요소 설정"""
        # 메인 레이아웃
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.setLayout(self.layout)
        
        # 프리미엄 카드 디자인 with glassmorphism effects and 한글 폰트 지원
        self.setStyleSheet("""
            StreamPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(248, 250, 252, 0.8));
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                margin: 10px;
                padding: 20px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
            StreamPanel:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(248, 250, 252, 0.9));
                border: 2px solid rgba(102, 126, 234, 0.4);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6fd8, stop:1 #6a4c93);
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
            QLabel {
                color: #333;
            }
        """)

        # 제목 라벨
        self.title_label = QtWidgets.QLabel(f"📹 {self.source}")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 800;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
                color: #2c3e50;
                padding: 10px;
                border-radius: 10px;
                text-align: center;
            }
        """)
        self.layout.addWidget(self.title_label)

        # 비디오 영역 (고정 크기 800x600)
        self.video = VideoLabel()
        # VideoLabel이 이미 setFixedSize(800, 600)로 설정되어 있음
        self.layout.addWidget(self.video, alignment=QtCore.Qt.AlignCenter)

        # 컨트롤 버튼들
        control_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("▶️ 시작")
        self.stop_btn = QtWidgets.QPushButton("⏹️ 중지")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b6b, stop:1 #ee5a52);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 12px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff5252, stop:1 #d32f2f);
            }
        """)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        self.layout.addLayout(control_layout)
        
        # FPS 및 성능 정보 표시
        self.fps_label = QtWidgets.QLabel("🎥 FPS: 0.0 | 대기 중...")
        self.fps_label.setAlignment(QtCore.Qt.AlignCenter)
        self.fps_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(52, 152, 219, 0.1), stop:1 rgba(155, 89, 182, 0.1));
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                font-weight: 700;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", monospace;
                color: #2c3e50;
            }
        """)
        self.layout.addWidget(self.fps_label)

        # 카운터 UI
        counter_frame = QtWidgets.QFrame()
        counter_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        counter_layout = QtWidgets.QVBoxLayout(counter_frame)
        
        # 카운트 정보
        count_info_layout = QtWidgets.QHBoxLayout()
        self.count_label = QtWidgets.QLabel("📊 총 카운트: 0")
        self.count_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: 800;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
                color: #667eea;
                text-align: center;
                padding: 15px;
                border-radius: 15px;
                background-color: rgba(102, 126, 234, 0.1);
            }
        """)
        
        self.reset_btn = QtWidgets.QPushButton("🔄 리셋")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffa726, stop:1 #ff9800);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 11px;
                font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff9800, stop:1 #f57c00);
            }
        """)
        
        self.count_chk = QtWidgets.QCheckBox("카운트 활성화")
        self.count_chk.setChecked(True)
        
        count_info_layout.addWidget(self.count_label)
        count_info_layout.addStretch()
        count_info_layout.addWidget(self.count_chk)
        count_info_layout.addWidget(self.reset_btn)
        
        counter_layout.addLayout(count_info_layout)

        # 상세 분석 영역 (스크롤 뷰 추가)
        analysis_scroll = QtWidgets.QScrollArea()
        analysis_scroll.setWidgetResizable(True)
        analysis_scroll.setMaximumHeight(120)  # 높이 제한
        analysis_scroll.setStyleSheet("""
            QScrollArea {
                background: #f9f9f9;
                border: 1px solid #eee;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                background: #e0e0e0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #bdbdbd;
                border-radius: 5px;
                min-height: 20px;
            }
        """)
        
        analysis_widget = QtWidgets.QWidget()
        analysis_layout = QtWidgets.QVBoxLayout(analysis_widget)
        
        self.breakdown_label = QtWidgets.QLabel("상세 분석이 여기에 표시됩니다")
        self.breakdown_label.setWordWrap(True)
        self.breakdown_label.setStyleSheet("""
            QLabel {
                background: transparent;
                padding: 8px;
                font-family: monospace;
                font-size: 11px;
                color: #333;
            }
        """)
        analysis_layout.addWidget(self.breakdown_label)
        analysis_scroll.setWidget(analysis_widget)
        counter_layout.addWidget(analysis_scroll)

        # ESAL 점수 및 권고사항 (스크롤 뷰 추가)
        score_scroll = QtWidgets.QScrollArea()
        score_scroll.setWidgetResizable(True) 
        score_scroll.setMaximumHeight(100)  # 높이 제한
        score_scroll.setStyleSheet("""
            QScrollArea {
                background: #e8f5e8;
                border: 2px solid #4CAF50;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                background: #c8e6c9;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4CAF50;
                border-radius: 5px;
                min-height: 20px;
            }
        """)
        
        score_widget = QtWidgets.QWidget()
        score_layout = QtWidgets.QVBoxLayout(score_widget)
        
        self.score_label = QtWidgets.QLabel("ESAL 분석 결과가 여기에 표시됩니다")
        self.score_label.setWordWrap(True)
        self.score_label.setStyleSheet("""
            QLabel {
                background: transparent;
                padding: 8px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        score_layout.addWidget(self.score_label)
        score_scroll.setWidget(score_widget)
        counter_layout.addWidget(score_scroll)
        
        self.layout.addWidget(counter_frame)

    def _connect_signals(self):
        """시그널 연결"""
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.reset_btn.clicked.connect(self.reset_count)
        self.video.roi_changed.connect(self.on_roi_changed)

    def on_roi_changed(self, roi):
        """ROI 변경 처리"""
        self.roi = roi
        if self.worker is not None:
            self.worker.roi = roi

    def start(self):
        """스트림 시작"""
        if self.worker is not None and self.worker.isRunning():
            return
            
        self.worker = StreamWorker(self.source, self.detector, self.performance_config)
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
            if self.video._orig_size:
                w, h = self.video._orig_size
                self.title_label.setText(f"📹 {self.source} | {w}x{h}")
        except Exception as e:
            print(f"[StreamPanel] 프레임 처리 오류: {e}")

    def on_status(self, msg: str):
        """상태 메시지 업데이트"""
        # FPS 정보를 FPS 라벨에 표시
        self.fps_label.setText(msg)
        
        # 제목 표시에도 간단한 정보 표시
        base_title = f"📹 {self.source}"
        if "실행 중" in msg or "FPS" in msg:
            # FPS 정보가 있으면 녹색으로 표시
            self.title_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: 800;
                    font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
                    color: #27ae60;
                    padding: 10px;
                    border-radius: 10px;
                    text-align: center;
                }
            """)
        elif "중지" in msg:
            # 중지 시 빨간색으로
            self.title_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: 800;
                    font-family: "SF Pro Display", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
                    color: #e74c3c;
                    padding: 10px;
                    border-radius: 10px;
                    text-align: center;
                }
            """)
        
        self.title_label.setText(f"{base_title}")

    def on_count_changed(self, counts: dict):
        """카운트 변경 처리"""
        try:
            if not self.count_chk.isChecked():
                return
                
            if not isinstance(counts, dict):
                return
            
            # 총 카운트 표시
            total = sum(counts.values())
            self.count_label.setText(f"📊 총 카운트: {total}")

            # ESAL 계산
            total_score, class_scores = self.esal_calculator.calculate_total_score(counts)
            
            # 상세 분석 생성
            breakdown = self.esal_calculator.get_detailed_breakdown(counts)
            self.breakdown_label.setText('\n'.join(breakdown) if breakdown else "탐지된 차량이 없습니다")
            
            # 보수 권고 생성
            recommendation = self.esal_calculator.get_maintenance_recommendation(total_score)
            schedule_info = self.esal_calculator.get_maintenance_schedule_info(total_score)
            
            score_text = f"🔍 총 ESAL 점수: {total_score:,.1f}\n"
            score_text += f"💡 권고사항: {recommendation}"
            
            if schedule_info:
                score_text += f"\n📅 예상 시기: {schedule_info['timing_years']}년 후 ({schedule_info['design_pct']}%)"
            
            self.score_label.setText(score_text)
            
        except Exception as e:
            print(f"[StreamPanel] 카운트 처리 오류: {e}")

    def reset_count(self):
        """카운트 리셋"""
        try:
            if self.worker is not None:
                self.worker.reset_count()
            
            # UI 초기화
            self.count_label.setText("📊 총 카운트: 0")
            self.breakdown_label.setText("상세 분석이 여기에 표시됩니다")
            self.score_label.setText("ESAL 분석 결과가 여기에 표시됩니다")
            
        except Exception as e:
            print(f"[StreamPanel] 리셋 오류: {e}")