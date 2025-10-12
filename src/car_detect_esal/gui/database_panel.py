"""
데이터베이스 통계 및 관리 패널
Database Statistics and Management Panel
"""

from datetime import datetime, timedelta
from PyQt5 import QtCore, QtGui, QtWidgets
from ..database import TrafficDatabaseManager


class DatabaseStatsWidget(QtWidgets.QWidget):
    """데이터베이스 통계 위젯"""
    
    def __init__(self, db_manager: TrafficDatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._setup_ui()
        self._setup_timer()
        
    def _setup_ui(self):
        """UI 설정"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        
        # 제목
        title = QtWidgets.QLabel("📊 데이터베이스 통계")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
            }
        """)
        layout.addWidget(title)
        
        # 실시간 통계 그룹
        self.stats_group = QtWidgets.QGroupBox("실시간 데이터")
        stats_layout = QtWidgets.QFormLayout(self.stats_group)
        stats_layout.setSpacing(6)
        
        # 통계 라벨들
        self.total_detections_label = QtWidgets.QLabel("0")
        self.today_detections_label = QtWidgets.QLabel("0")
        self.active_cameras_label = QtWidgets.QLabel("0")
        self.total_esal_label = QtWidgets.QLabel("0.0")
        self.db_size_label = QtWidgets.QLabel("0 MB")
        
        # 스타일 적용
        for label in [self.total_detections_label, self.today_detections_label, 
                      self.active_cameras_label, self.total_esal_label, self.db_size_label]:
            label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #27ae60;
                    font-size: 14px;
                }
            """)
        
        stats_layout.addRow("총 탐지 수:", self.total_detections_label)
        stats_layout.addRow("오늘 탐지:", self.today_detections_label)
        stats_layout.addRow("활성 카메라:", self.active_cameras_label)
        stats_layout.addRow("총 ESAL:", self.total_esal_label)
        stats_layout.addRow("DB 크기:", self.db_size_label)
        
        layout.addWidget(self.stats_group)
        
        # 차종별 통계 그룹
        self.vehicle_stats_group = QtWidgets.QGroupBox("차종별 통계 (오늘)")
        vehicle_layout = QtWidgets.QFormLayout(self.vehicle_stats_group)
        vehicle_layout.setSpacing(6)
        
        self.car_count_label = QtWidgets.QLabel("0")
        self.truck_count_label = QtWidgets.QLabel("0")
        self.bus_count_label = QtWidgets.QLabel("0")
        self.van_count_label = QtWidgets.QLabel("0")
        self.motorbike_count_label = QtWidgets.QLabel("0")
        
        for label in [self.car_count_label, self.truck_count_label, 
                      self.bus_count_label, self.van_count_label, self.motorbike_count_label]:
            label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #3498db;
                    font-size: 13px;
                }
            """)
        
        vehicle_layout.addRow("🚗 승용차:", self.car_count_label)
        vehicle_layout.addRow("🚛 트럭:", self.truck_count_label)
        vehicle_layout.addRow("🚌 버스:", self.bus_count_label)
        vehicle_layout.addRow("🚐 밴:", self.van_count_label) 
        vehicle_layout.addRow("🏍️ 오토바이:", self.motorbike_count_label)
        
        layout.addWidget(self.vehicle_stats_group)
        
        # 유지보수 알림 그룹
        self.maintenance_group = QtWidgets.QGroupBox("유지보수 알림")
        maintenance_layout = QtWidgets.QVBoxLayout(self.maintenance_group)
        
        self.maintenance_list = QtWidgets.QListWidget()
        self.maintenance_list.setMaximumHeight(100)
        self.maintenance_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: white;
            }
        """)
        maintenance_layout.addWidget(self.maintenance_list)
        
        layout.addWidget(self.maintenance_group)
        
        # 버튼 그룹
        button_layout = QtWidgets.QHBoxLayout()
        
        self.refresh_btn = QtWidgets.QPushButton("🔄 새로고침")
        self.export_btn = QtWidgets.QPushButton("📊 내보내기")
        self.cleanup_btn = QtWidgets.QPushButton("🧹 정리")
        
        for btn in [self.refresh_btn, self.export_btn, self.cleanup_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #3498db);
                }
                QPushButton:pressed {
                    background: #2980b9;
                }
            """)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.cleanup_btn)
        
        layout.addLayout(button_layout)
        
        # 시그널 연결
        self.refresh_btn.clicked.connect(self.refresh_stats)
        self.export_btn.clicked.connect(self.export_data)
        self.cleanup_btn.clicked.connect(self.cleanup_data)
        
        # 초기 통계 로드
        self.refresh_stats()
        
    def _setup_timer(self):
        """자동 새로고침 타이머 설정"""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(30000)  # 30초마다 새로고침
        
    def refresh_stats(self):
        """통계 새로고침"""
        if not self.db_manager:
            return
            
        try:
            # 데이터베이스 상태 조회
            status = self.db_manager.get_database_status()
            
            if status:
                # 기본 통계 업데이트
                self.total_detections_label.setText(f"{status['tables'].get('vehicle_detections', 0):,}")
                self.active_cameras_label.setText(f"{status['tables'].get('camera_streams', 0)}")
                self.db_size_label.setText(f"{status['file_size_mb']} MB")
                
                # 오늘 탐지 수 및 차종별 통계 조회
                self._update_today_stats()
                
                # ESAL 통계 업데이트
                self._update_esal_stats()
                
                # 유지보수 알림 업데이트
                self._update_maintenance_alerts()
                
        except Exception as e:
            print(f"통계 새로고침 실패: {e}")
            
    def _update_today_stats(self):
        """오늘 통계 업데이트"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                # 오늘 탐지 수
                today = datetime.now().date()
                today_count = conn.execute(
                    "SELECT COUNT(*) FROM vehicle_detections WHERE DATE(timestamp) = ?",
                    (today,)
                ).fetchone()[0]
                self.today_detections_label.setText(f"{today_count:,}")
                
                # 차종별 통계
                vehicle_stats = conn.execute("""
                    SELECT vehicle_type, COUNT(*) 
                    FROM vehicle_detections 
                    WHERE DATE(timestamp) = ?
                    GROUP BY vehicle_type
                """, (today,)).fetchall()
                
                stats_dict = dict(vehicle_stats)
                self.car_count_label.setText(f"{stats_dict.get('car', 0):,}")
                self.truck_count_label.setText(f"{stats_dict.get('truck', 0):,}")
                self.bus_count_label.setText(f"{stats_dict.get('bus', 0):,}")
                self.van_count_label.setText(f"{stats_dict.get('van', 0):,}")
                self.motorbike_count_label.setText(f"{stats_dict.get('motorbike', 0):,}")
                
        except Exception as e:
            print(f"오늘 통계 업데이트 실패: {e}")
            
    def _update_esal_stats(self):
        """ESAL 통계 업데이트"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                # 최근 7일 평균 ESAL
                week_ago = datetime.now() - timedelta(days=7)
                avg_esal = conn.execute(
                    "SELECT AVG(total_esal) FROM esal_analysis WHERE timestamp >= ?",
                    (week_ago,)
                ).fetchone()[0]
                
                if avg_esal:
                    self.total_esal_label.setText(f"{avg_esal:,.1f}")
                else:
                    self.total_esal_label.setText("0.0")
                    
        except Exception as e:
            print(f"ESAL 통계 업데이트 실패: {e}")
            
    def _update_maintenance_alerts(self):
        """유지보수 알림 업데이트"""
        try:
            import sqlite3
            self.maintenance_list.clear()
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                # 긴급 유지보수 일정 조회
                urgent_maintenance = conn.execute("""
                    SELECT camera_id, maintenance_type, priority_level, scheduled_date
                    FROM maintenance_schedule 
                    WHERE status = 'scheduled' AND priority_level >= 3
                    ORDER BY priority_level DESC, scheduled_date ASC
                    LIMIT 5
                """).fetchall()
                
                for camera_id, mtype, priority, sdate in urgent_maintenance:
                    urgency = "🔴 긴급" if priority >= 4 else "🟡 높음"
                    item_text = f"{urgency} {camera_id}: {mtype} ({sdate})"
                    self.maintenance_list.addItem(item_text)
                    
                if not urgent_maintenance:
                    self.maintenance_list.addItem("✅ 긴급 유지보수 없음")
                    
        except Exception as e:
            print(f"유지보수 알림 업데이트 실패: {e}")
            
    def export_data(self):
        """데이터 내보내기"""
        if not self.db_manager:
            QtWidgets.QMessageBox.warning(self, "경고", "데이터베이스가 연결되지 않았습니다.")
            return
            
        # 파일 선택 대화상자
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "데이터 내보내기", 
            f"traffic_data_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # 최근 30일 데이터 내보내기
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                if self.db_manager.export_data_to_csv('vehicle_detections', file_path, start_date, end_date):
                    QtWidgets.QMessageBox.information(self, "성공", f"데이터가 성공적으로 내보내졌습니다.\n{file_path}")
                else:
                    QtWidgets.QMessageBox.warning(self, "실패", "데이터 내보내기에 실패했습니다.")
                    
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "오류", f"내보내기 중 오류 발생:\n{e}")
                
    def cleanup_data(self):
        """오래된 데이터 정리"""
        if not self.db_manager:
            QtWidgets.QMessageBox.warning(self, "경고", "데이터베이스가 연결되지 않았습니다.")
            return
            
        reply = QtWidgets.QMessageBox.question(
            self, "데이터 정리", 
            "1년 이상 된 오래된 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                deleted_count = self.db_manager.cleanup_old_data(365)
                QtWidgets.QMessageBox.information(
                    self, "완료", 
                    f"데이터 정리가 완료되었습니다.\n삭제된 레코드: {deleted_count:,}개"
                )
                self.refresh_stats()
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "오류", f"데이터 정리 중 오류 발생:\n{e}")


class ESALAnalysisWidget(QtWidgets.QWidget):
    """ESAL 분석 위젯"""
    
    def __init__(self, db_manager: TrafficDatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 설정"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        
        # 제목
        title = QtWidgets.QLabel("⚖️ ESAL 분석")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
            }
        """)
        layout.addWidget(title)
        
        # 분석 설정 그룹
        settings_group = QtWidgets.QGroupBox("분석 설정")
        settings_layout = QtWidgets.QFormLayout(settings_group)
        
        # 카메라 선택
        self.camera_combo = QtWidgets.QComboBox()
        self.camera_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
            }
        """)
        settings_layout.addRow("카메라:", self.camera_combo)
        
        # 분석 기간 선택
        self.period_combo = QtWidgets.QComboBox()
        self.period_combo.addItems(["hourly", "daily", "weekly", "monthly"])
        self.period_combo.setCurrentText("daily")
        self.period_combo.setStyleSheet(self.camera_combo.styleSheet())
        settings_layout.addRow("분석 기간:", self.period_combo)
        
        # 분석 버튼
        self.analyze_btn = QtWidgets.QPushButton("📊 ESAL 분석 실행")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #e74c3c);
            }
        """)
        settings_layout.addRow(self.analyze_btn)
        
        layout.addWidget(settings_group)
        
        # 분석 결과 그룹
        results_group = QtWidgets.QGroupBox("분석 결과")
        results_layout = QtWidgets.QVBoxLayout(results_group)
        
        self.results_text = QtWidgets.QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                font-family: monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # 시그널 연결
        self.analyze_btn.clicked.connect(self.run_esal_analysis)
        
        # 카메라 목록 로드
        self._load_cameras()
        
    def _load_cameras(self):
        """카메라 목록 로드"""
        if not self.db_manager:
            return
            
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cameras = conn.execute("SELECT id, name FROM camera_streams WHERE is_active = 1").fetchall()
                
                self.camera_combo.clear()
                for cam_id, cam_name in cameras:
                    self.camera_combo.addItem(f"{cam_name} ({cam_id})", cam_id)
                    
                if not cameras:
                    self.camera_combo.addItem("등록된 카메라 없음", None)
                    
        except Exception as e:
            print(f"카메라 목록 로드 실패: {e}")
            
    def run_esal_analysis(self):
        """ESAL 분석 실행"""
        if not self.db_manager:
            self.results_text.setPlainText("데이터베이스가 연결되지 않았습니다.")
            return
            
        camera_id = self.camera_combo.currentData()
        if not camera_id:
            self.results_text.setPlainText("분석할 카메라를 선택해주세요.")
            return
            
        period = self.period_combo.currentText()
        
        try:
            self.results_text.setPlainText("ESAL 분석 실행 중...")
            QtCore.QCoreApplication.processEvents()
            
            # ESAL 분석 실행
            result = self.db_manager.calculate_esal_analysis(camera_id, period=period)
            
            if result:
                # 결과 포맷팅
                output = f"""
ESAL 분석 결과 ({result['analysis_period']})
카메라: {result['camera_id']}
분석 기간: {result['period_start']} ~ {result['period_end']}

=== 차량 집계 ===
승용차: {result['car_count']:,}대
버스: {result['bus_count']:,}대  
트럭: {result['truck_count']:,}대
밴: {result['van_count']:,}대
오토바이: {result['motorbike_count']:,}대
기타: {result['other_count']:,}대

=== ESAL 분석 ===
총 ESAL: {result['total_esal']:,.2f}
승용차 ESAL: {result['car_esal']:,.2f}
버스 ESAL: {result['bus_esal']:,.2f}
트럭 ESAL: {result['truck_esal']:,.2f}
밴 ESAL: {result['van_esal']:,.2f}

=== 도로 상태 평가 ===
포장 손상 수준: {result['pavement_damage_level']}/5
유지보수 긴급도: {result['maintenance_urgency']}
예상 유지보수 일자: {result['estimated_maintenance_date']}
"""
                self.results_text.setPlainText(output)
            else:
                self.results_text.setPlainText("ESAL 분석에 실패했습니다. 데이터가 부족하거나 오류가 발생했습니다.")
                
        except Exception as e:
            self.results_text.setPlainText(f"분석 중 오류 발생:\n{e}")