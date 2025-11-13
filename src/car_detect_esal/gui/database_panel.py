"""
Database Statistics and Management Panel
"""

from datetime import datetime, timedelta
from PyQt5 import QtCore, QtGui, QtWidgets
from ..database import TrafficDatabaseManager


class DatabaseStatsWidget(QtWidgets.QWidget):
    """Database statistics widget"""
    
    def __init__(self, db_manager: TrafficDatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._setup_ui()
        self._setup_timer()
        self.refresh_stats()
        
    def _setup_ui(self):
        """Setup UI"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Refresh Statistics")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #5a5c5e;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #6a6c6e; }
        """)
        refresh_btn.clicked.connect(self.refresh_stats)
        layout.addWidget(refresh_btn)
        
        # Real-time statistics group
        self.stats_group = QtWidgets.QGroupBox("Real-time Data")
        self.stats_group.setStyleSheet("""
            QGroupBox {
                background: #3c3f41;
                border: 1px solid #555555;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                font-size: 11px;
                font-weight: bold;
                color: #dcdcdc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 3px 8px;
            }
        """)
        stats_layout = QtWidgets.QVBoxLayout(self.stats_group)
        stats_layout.setSpacing(4)
        
        # Statistics labels
        self.total_detections_label = self._create_stat_label("Total Detections: 0")
        self.today_detections_label = self._create_stat_label("Today: 0")
        self.active_cameras_label = self._create_stat_label("Active Cameras: 0")
        self.latest_detection_label = self._create_stat_label("Latest: Never")
        
        stats_layout.addWidget(self.total_detections_label)
        stats_layout.addWidget(self.today_detections_label)
        stats_layout.addWidget(self.active_cameras_label)
        stats_layout.addWidget(self.latest_detection_label)
        
        layout.addWidget(self.stats_group)
        
        # Vehicle statistics group
        self.vehicle_stats_group = QtWidgets.QGroupBox("Vehicle Types (Today)")
        self.vehicle_stats_group.setStyleSheet(self.stats_group.styleSheet())
        vehicle_layout = QtWidgets.QVBoxLayout(self.vehicle_stats_group)
        vehicle_layout.setSpacing(4)
        
        self.car_count_label = self._create_stat_label("Car: 0")
        self.truck_count_label = self._create_stat_label("Truck: 0")
        self.bus_count_label = self._create_stat_label("Bus: 0")
        self.van_count_label = self._create_stat_label("Van: 0")
        self.motorbike_count_label = self._create_stat_label("Motorbike: 0")
        
        vehicle_layout.addWidget(self.car_count_label)
        vehicle_layout.addWidget(self.truck_count_label)
        vehicle_layout.addWidget(self.bus_count_label)
        vehicle_layout.addWidget(self.van_count_label)
        vehicle_layout.addWidget(self.motorbike_count_label)
        
        layout.addWidget(self.vehicle_stats_group)
        
        # Recent detections list
        self.recent_group = QtWidgets.QGroupBox("Recent Detections")
        self.recent_group.setStyleSheet(self.stats_group.styleSheet())
        recent_layout = QtWidgets.QVBoxLayout(self.recent_group)
        
        self.recent_list = QtWidgets.QTextEdit()
        self.recent_list.setReadOnly(True)
        self.recent_list.setMaximumHeight(150)
        self.recent_list.setStyleSheet("""
            QTextEdit {
                background: #2b2d30;
                color: #dcdcdc;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 10px;
                font-family: "Courier New", "Consolas", monospace;
                padding: 4px;
            }
        """)
        recent_layout.addWidget(self.recent_list)
        
        layout.addWidget(self.recent_group)
        layout.addStretch()
        
    def _create_stat_label(self, text):
        """Create styled statistics label"""
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("""
            QLabel {
                color: #a8dadc;
                font-size: 11px;
                font-weight: normal;
                padding: 2px 4px;
            }
        """)
        return label
        
    def _setup_timer(self):
        """Setup auto-refresh timer"""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(30000)
        
    def refresh_stats(self):
        """Refresh statistics"""
        if not self.db_manager:
            self.total_detections_label.setText("Total Detections: N/A (No DB)")
            return
            
        try:
            status = self.db_manager.get_database_status()
            
            if status:
                self.total_detections_label.setText(f"Total Detections: {status.get('total_detections', 0):,}")
                self.active_cameras_label.setText(f"Active Cameras: {status.get('total_cameras', 0)}")
                
                latest = status.get('latest_detection')
                if latest:
                    self.latest_detection_label.setText(f"Latest: {latest}")
                else:
                    self.latest_detection_label.setText("Latest: Never")
                
                self._update_today_stats()
                self._update_recent_detections()
                
        except Exception as e:
            print(f"[DB Panel] Statistics refresh failed: {e}")
            self.total_detections_label.setText(f"Total Detections: Error")
            
    def _update_today_stats(self):
        """Update today's statistics"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            cursor.execute(
                "SELECT COUNT(*) as count FROM vehicle_detections WHERE DATE(timestamp) = %s",
                (today,)
            )
            result = cursor.fetchone()
            today_count = result['count'] if result else 0
            self.today_detections_label.setText(f"Today: {today_count:,}")
            
            cursor.execute("""
                SELECT vehicle_type, COUNT(*) as count
                FROM vehicle_detections 
                WHERE DATE(timestamp) = %s
                GROUP BY vehicle_type
            """, (today,))
            
            vehicle_stats = cursor.fetchall()
            stats_dict = {row['vehicle_type']: row['count'] for row in vehicle_stats}
            
            self.car_count_label.setText(f"Car: {stats_dict.get('car', 0):,}")
            self.truck_count_label.setText(f"Truck: {stats_dict.get('truck', 0):,}")
            self.bus_count_label.setText(f"Bus: {stats_dict.get('bus', 0):,}")
            self.van_count_label.setText(f"Van: {stats_dict.get('van', 0):,}")
            self.motorbike_count_label.setText(f"Motorbike: {stats_dict.get('motorbike', 0):,}")
            
            cursor.close()
            conn.close()
                
        except Exception as e:
            print(f"[DB Panel] Today's statistics update failed: {e}")
            
    def _update_recent_detections(self):
        """Update recent detections list"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, camera_name, vehicle_type, confidence
                FROM vehicle_detections
                ORDER BY timestamp DESC
                LIMIT 20
            """)
            
            recent = cursor.fetchall()
            
            text_lines = []
            for row in recent:
                ts = row['timestamp'].strftime('%H:%M:%S') if row['timestamp'] else 'N/A'
                cam = row['camera_name'] or 'Unknown'
                vtype = row['vehicle_type'] or 'unknown'
                conf = row['confidence'] or 0.0
                text_lines.append(f"[{ts}] {cam[:15]:<15} | {vtype:<10} | {conf:.2f}")
            
            self.recent_list.setText("\n".join(text_lines) if text_lines else "No recent detections")
            
            cursor.close()
            conn.close()
                
        except Exception as e:
            print(f"[DB Panel] Recent detections update failed: {e}")
            self.recent_list.setText(f"Error: {e}")


class ESALAnalysisWidget(QtWidgets.QWidget):
    """ESAL Analysis Widget"""
    
    def __init__(self, db_manager: TrafficDatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup UI"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        
        title = QtWidgets.QLabel("ESAL Analysis")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #dcdcdc;
                padding: 8px;
                background: #3c3f41;
                border-radius: 6px;
            }
        """)
        layout.addWidget(title)
        
        settings_group = QtWidgets.QGroupBox("Analysis Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                background: #3c3f41;
                border: 1px solid #555555;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                font-size: 11px;
                font-weight: bold;
                color: #dcdcdc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 3px 8px;
            }
        """)
        settings_layout = QtWidgets.QFormLayout(settings_group)
        
        self.camera_combo = QtWidgets.QComboBox()
        self.camera_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #555555;
                border-radius: 6px;
                background: #2b2d30;
                color: #dcdcdc;
                font-size: 11px;
            }
        """)
        settings_layout.addRow("Camera:", self.camera_combo)
        
        self.period_combo = QtWidgets.QComboBox()
        self.period_combo.addItems(["hourly", "daily", "weekly", "monthly"])
        self.period_combo.setCurrentText("daily")
        self.period_combo.setStyleSheet(self.camera_combo.styleSheet())
        settings_layout.addRow("Period:", self.period_combo)
        
        self.analyze_btn = QtWidgets.QPushButton("Run ESAL Analysis")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: #5a5c5e;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #6a6c6e; }
        """)
        settings_layout.addRow(self.analyze_btn)
        
        layout.addWidget(settings_group)
        
        results_group = QtWidgets.QGroupBox("Analysis Results")
        results_group.setStyleSheet(settings_group.styleSheet())
        results_layout = QtWidgets.QVBoxLayout(results_group)
        
        self.results_text = QtWidgets.QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background: #2b2d30;
                color: #dcdcdc;
                border: 1px solid #555555;
                border-radius: 4px;
                font-family: "Courier New", "Consolas", monospace;
                font-size: 10px;
                padding: 8px;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        self.analyze_btn.clicked.connect(self.run_esal_analysis)
        self._load_cameras()
        
    def _load_cameras(self):
        """Load camera list"""
        if not self.db_manager:
            return
            
        try:
            cameras = self.db_manager.get_camera_list()
            
            self.camera_combo.clear()
            for cam in cameras:
                cam_id = cam.get('id')
                cam_name = cam.get('name', 'Unknown')
                self.camera_combo.addItem(f"{cam_name} ({cam_id})", cam_id)
                
            if not cameras:
                self.camera_combo.addItem("No registered cameras", None)
                
        except Exception as e:
            print(f"[ESAL Widget] Camera list load failed: {e}")
            
    def run_esal_analysis(self):
        """Run ESAL analysis"""
        if not self.db_manager:
            self.results_text.setPlainText("Database not connected.")
            return
            
        camera_id = self.camera_combo.currentData()
        if not camera_id:
            self.results_text.setPlainText("Please select a camera for analysis.")
            return
            
        period = self.period_combo.currentText()
        
        try:
            self.results_text.setPlainText("Running ESAL analysis...")
            QtCore.QCoreApplication.processEvents()
            
            result = self.db_manager.calculate_esal_analysis(camera_id, period=period)
            
            if result:
                output = f"""
ESAL Analysis Results ({result.get('analysis_period', 'N/A')})
Camera: {result.get('camera_id', 'N/A')}
Period: {result.get('period_start', 'N/A')} ~ {result.get('period_end', 'N/A')}

=== Vehicle Count ===
Cars: {result.get('car_count', 0):,}
Buses: {result.get('bus_count', 0):,}
Trucks: {result.get('truck_count', 0):,}
Vans: {result.get('van_count', 0):,}
Motorbikes: {result.get('motorbike_count', 0):,}
Other: {result.get('other_count', 0):,}

=== ESAL Analysis ===
Total ESAL: {result.get('total_esal', 0):,.2f}
Car ESAL: {result.get('car_esal', 0):,.2f}
Bus ESAL: {result.get('bus_esal', 0):,.2f}
Truck ESAL: {result.get('truck_esal', 0):,.2f}
Van ESAL: {result.get('van_esal', 0):,.2f}

=== Road Condition Assessment ===
Pavement Damage Level: {result.get('pavement_damage_level', 'N/A')}/5
Maintenance Urgency: {result.get('maintenance_urgency', 'N/A')}
Estimated Maintenance Date: {result.get('estimated_maintenance_date', 'N/A')}
"""
                self.results_text.setPlainText(output)
            else:
                self.results_text.setPlainText("ESAL analysis failed. Insufficient data or error occurred.")
                
        except Exception as e:
            self.results_text.setPlainText(f"Analysis error:\n{e}")
