"""
Simple Main Window - Clean and Minimalist Design
"""

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from ..core import Config, VehicleDetector
from ..database import TrafficDatabaseManager
from .stream_panel import StreamPanel


class MainWindow(QtWidgets.QMainWindow):
    """Simple and clean main window"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.detector = None
        self.panels = []
        self._cols = 2
        
        # Database
        try:
            self.db_manager = TrafficDatabaseManager()
        except Exception as e:
            print(f"DB init failed: {e}")
            self.db_manager = None
        
        self._setup_ui()
        self._load_model()

    def _setup_ui(self):
        """Setup minimalist UI"""
        self.setWindowTitle("Traffic Detection System")
        self.resize(1200, 700)
        
        # Dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: #1e1e1e;
            }
            QWidget {
                background: #1e1e1e;
                color: #e0e0e0;
                font-family: "SF Pro Display", "Segoe UI", Arial;
                font-size: 13px;
            }
            QPushButton {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px 16px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: #3d3d3d;
                border: 1px solid #4d4d4d;
            }
            QPushButton:pressed {
                background: #252525;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left: Video area
        self.video_area = QtWidgets.QWidget()
        self.video_area.setStyleSheet("background: #000000;")
        self.video_layout = QtWidgets.QGridLayout(self.video_area)
        self.video_layout.setSpacing(2)
        self.video_layout.setContentsMargins(2, 2, 2, 2)
        
        # Right: Compact control sidebar
        sidebar = QtWidgets.QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background: #252525; border-left: 1px solid #3d3d3d;")
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(12)
        
        # Title
        title = QtWidgets.QLabel("Control Panel")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        sidebar_layout.addWidget(title)
        
        # Add stream section
        add_group = QtWidgets.QGroupBox("Add Stream")
        add_layout = QtWidgets.QVBoxLayout(add_group)
        add_layout.setSpacing(8)
        
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL or path...")
        add_layout.addWidget(self.url_input)
        
        # Input buttons row
        input_btn_layout = QtWidgets.QHBoxLayout()
        input_btn_layout.setSpacing(6)
        
        browse_btn = QtWidgets.QPushButton("📁 Browse...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #2d4a5e;
                border: 1px solid #3d5a6e;
                font-size: 11px;
                padding: 6px;
            }
            QPushButton:hover {
                background: #3d5a6e;
            }
        """)
        browse_btn.clicked.connect(self._browse_video)
        input_btn_layout.addWidget(browse_btn)
        
        add_btn = QtWidgets.QPushButton("+ Add")
        add_btn.clicked.connect(self._add_stream)
        input_btn_layout.addWidget(add_btn)
        
        add_layout.addLayout(input_btn_layout)
        
        # Demo videos section
        demo_label = QtWidgets.QLabel("Quick demo videos:")
        demo_label.setStyleSheet("font-size: 11px; color: #808080; margin-top: 8px;")
        add_layout.addWidget(demo_label)
        
        demo_btn_layout = QtWidgets.QHBoxLayout()
        demo_btn_layout.setSpacing(6)
        
        demo1_btn = QtWidgets.QPushButton("Demo 1")
        demo1_btn.setStyleSheet("""
            QPushButton {
                background: #1a4d2e;
                border: 1px solid #2d6a4f;
                font-size: 11px;
                padding: 6px;
            }
            QPushButton:hover {
                background: #2d6a4f;
            }
        """)
        demo1_btn.clicked.connect(lambda: self._add_demo_video(1))
        demo_btn_layout.addWidget(demo1_btn)
        
        demo2_btn = QtWidgets.QPushButton("Demo 2")
        demo2_btn.setStyleSheet(demo1_btn.styleSheet())
        demo2_btn.clicked.connect(lambda: self._add_demo_video(2))
        demo_btn_layout.addWidget(demo2_btn)
        
        demo3_btn = QtWidgets.QPushButton("Demo 3")
        demo3_btn.setStyleSheet(demo1_btn.styleSheet())
        demo3_btn.clicked.connect(lambda: self._add_demo_video(3))
        demo_btn_layout.addWidget(demo3_btn)
        
        add_layout.addLayout(demo_btn_layout)
        
        sidebar_layout.addWidget(add_group)
        
        # Quick actions
        action_group = QtWidgets.QGroupBox("Quick Actions")
        action_layout = QtWidgets.QVBoxLayout(action_group)
        action_layout.setSpacing(6)
        
        start_all_btn = QtWidgets.QPushButton("▶ Start All")
        start_all_btn.setStyleSheet("""
            QPushButton {
                background: #2d5016;
                border: 1px solid #3d6026;
            }
            QPushButton:hover {
                background: #3d6026;
            }
        """)
        start_all_btn.clicked.connect(self._start_all)
        action_layout.addWidget(start_all_btn)
        
        stop_all_btn = QtWidgets.QPushButton("■ Stop All")
        stop_all_btn.setStyleSheet("""
            QPushButton {
                background: #501616;
                border: 1px solid #602626;
            }
            QPushButton:hover {
                background: #602626;
            }
        """)
        stop_all_btn.clicked.connect(self._stop_all)
        action_layout.addWidget(stop_all_btn)
        
        clear_btn = QtWidgets.QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_all)
        action_layout.addWidget(clear_btn)
        
        sidebar_layout.addWidget(action_group)
        
        # Settings section
        settings_group = QtWidgets.QGroupBox("Detection Settings")
        settings_layout = QtWidgets.QFormLayout(settings_group)
        settings_layout.setSpacing(8)
        
        self.conf_spin = QtWidgets.QDoubleSpinBox()
        self.conf_spin.setRange(0.0, 1.0)
        self.conf_spin.setSingleStep(0.05)
        self.conf_spin.setValue(0.5)
        settings_layout.addRow("Confidence:", self.conf_spin)
        
        self.iou_spin = QtWidgets.QDoubleSpinBox()
        self.iou_spin.setRange(0.0, 1.0)
        self.iou_spin.setSingleStep(0.05)
        self.iou_spin.setValue(0.45)
        settings_layout.addRow("IOU:", self.iou_spin)
        
        sidebar_layout.addWidget(settings_group)
        
        # Stats section
        self.stats_label = QtWidgets.QLabel("Streams: 0\nDetections: 0")
        self.stats_label.setStyleSheet("""
            padding: 12px;
            background: #2d2d2d;
            border-radius: 4px;
            font-size: 12px;
            color: #b0b0b0;
        """)
        self.stats_label.setAlignment(QtCore.Qt.AlignCenter)
        sidebar_layout.addWidget(self.stats_label)
        
        # Database Statistics Section
        if self.db_manager:
            db_group = QtWidgets.QGroupBox("Database Stats")
            db_layout = QtWidgets.QVBoxLayout(db_group)
            db_layout.setSpacing(4)
            
            # Total detections
            self.db_total_label = QtWidgets.QLabel("Total: 0")
            self.db_total_label.setStyleSheet("color: #90b0d0; font-size: 11px;")
            db_layout.addWidget(self.db_total_label)
            
            # Today's detections
            self.db_today_label = QtWidgets.QLabel("Today: 0")
            self.db_today_label.setStyleSheet("color: #90b0d0; font-size: 11px;")
            db_layout.addWidget(self.db_today_label)
            
            # View details button
            view_db_btn = QtWidgets.QPushButton("View Details")
            view_db_btn.setStyleSheet("""
                QPushButton {
                    background: #2d4a5e;
                    border: 1px solid #3d5a6e;
                    font-size: 11px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: #3d5a6e;
                }
            """)
            view_db_btn.clicked.connect(self._show_database_viewer)
            db_layout.addWidget(view_db_btn)
            
            sidebar_layout.addWidget(db_group)
            
            # Auto-refresh DB stats
            self.db_refresh_timer = QtCore.QTimer()
            self.db_refresh_timer.timeout.connect(self._refresh_db_stats)
            self.db_refresh_timer.start(5000)  # Every 5 seconds
            self._refresh_db_stats()  # Initial refresh
        
        # ROI Guide
        roi_guide = QtWidgets.QLabel("💡 ROI Detection:\nDrag on video to select area\nDouble-click to reset")
        roi_guide.setStyleSheet("""
            padding: 8px;
            background: #2d3d2d;
            border: 1px solid #3d5d3d;
            border-radius: 4px;
            font-size: 10px;
            color: #90c090;
            line-height: 1.4;
        """)
        roi_guide.setAlignment(QtCore.Qt.AlignLeft)
        roi_guide.setWordWrap(True)
        sidebar_layout.addWidget(roi_guide)
        
        sidebar_layout.addStretch()
        
        # DB status at bottom
        if self.db_manager:
            db_label = QtWidgets.QLabel("● Database Connected")
            db_label.setStyleSheet("color: #50a050; font-size: 11px;")
        else:
            db_label = QtWidgets.QLabel("○ Database Offline")
            db_label.setStyleSheet("color: #a05050; font-size: 11px;")
        db_label.setAlignment(QtCore.Qt.AlignCenter)
        sidebar_layout.addWidget(db_label)
        
        # Add to main layout
        layout.addWidget(self.video_area, 1)
        layout.addWidget(sidebar, 0)
        
        # Update timer
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self._update_stats)
        self.update_timer.start(1000)

    def _load_model(self):
        """Load detection model"""
        try:
            self.detector = VehicleDetector(
                model_path=str(self.config.DEFAULT_MODEL_PATH),
                conf=0.5
            )
            print("Model loaded successfully")
        except Exception as e:
            print(f"Model load failed: {e}")

    def _add_stream(self):
        """Add new video stream"""
        url = self.url_input.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a video URL or path")
            return
        
        self._add_video_panel(url)

    def _browse_video(self):
        """Browse for video file"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            str(self.config.PROJECT_ROOT),  # Start from project root
            "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv);;All Files (*.*)"
        )
        
        if file_path:
            self.url_input.setText(file_path)
            print(f"Selected video: {file_path}")

    def _add_demo_video(self, demo_num):
        """Add demo video from local files"""
        # Look for demo videos in common locations
        import os
        from pathlib import Path
        
        # Search paths for demo videos
        search_paths = [
            self.config.PROJECT_ROOT / "demo_videos",
            self.config.PROJECT_ROOT / "videos",
            self.config.PROJECT_ROOT / "samples",
            Path.home() / "Downloads",
            Path.home() / "Videos",
        ]
        
        # Demo video filename patterns
        demo_patterns = [
            f"demo{demo_num}.mp4",
            f"demo_{demo_num}.mp4",
            f"sample{demo_num}.mp4",
            f"traffic{demo_num}.mp4",
            f"video{demo_num}.mp4",
        ]
        
        # Search for demo video
        found_video = None
        for search_path in search_paths:
            if search_path.exists():
                for pattern in demo_patterns:
                    video_path = search_path / pattern
                    if video_path.exists():
                        found_video = str(video_path)
                        break
                if found_video:
                    break
        
        if found_video:
            print(f"Loading Demo Video {demo_num}: {found_video}")
            self._add_video_panel(found_video)
        else:
            # If not found, show file browser
            QtWidgets.QMessageBox.information(
                self, 
                "Demo Video Not Found",
                f"Demo video {demo_num} not found in standard locations.\n\n"
                f"Please select a video file manually."
            )
            self._browse_video()
    
    def _add_video_panel(self, url):
        """Add video panel to grid"""
        try:
            # Generate camera ID from URL
            import hashlib
            camera_id = f"cam_{hashlib.md5(url.encode()).hexdigest()[:8]}"
            
            panel = StreamPanel(
                source=url,
                detector=self.detector,
                performance_config={"sleep_time": 0.03, "imgsz": 640},
                db_manager=self.db_manager,
                camera_id=camera_id
            )
            
            row = len(self.panels) // self._cols
            col = len(self.panels) % self._cols
            self.video_layout.addWidget(panel, row, col)
            
            self.panels.append(panel)
            self.url_input.clear()
            self._update_stats()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add stream:\n{e}")
            import traceback
            traceback.print_exc()

    def _start_all(self):
        """Start all streams"""
        for panel in self.panels:
            if not panel.worker or not panel.worker.isRunning():
                panel.start()

    def _stop_all(self):
        """Stop all streams"""
        for panel in self.panels:
            if panel.worker and panel.worker.isRunning():
                panel.stop()

    def _clear_all(self):
        """Remove all streams"""
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm",
            "Remove all streams?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            for panel in self.panels:
                if panel.worker and panel.worker.isRunning():
                    panel.stop()
                panel.deleteLater()
            self.panels.clear()
            self._update_stats()

    def _update_stats(self):
        """Update statistics display"""
        total_detections = 0
        for panel in self.panels:
            if panel.worker and hasattr(panel.worker, 'total_count'):
                total_detections += panel.worker.total_count
        
        self.stats_label.setText(f"Streams: {len(self.panels)}\nDetections: {total_detections}")
    
    def _refresh_db_stats(self):
        """Refresh database statistics"""
        if not self.db_manager:
            return
        
        try:
            from datetime import datetime
            
            # Get total detections
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM vehicle_detections")
            result = cursor.fetchone()
            total_count = result['count'] if result else 0
            
            # Get today's detections
            today = datetime.now().date()
            cursor.execute(
                "SELECT COUNT(*) as count FROM vehicle_detections WHERE DATE(timestamp) = %s",
                (today,)
            )
            result = cursor.fetchone()
            today_count = result['count'] if result else 0
            
            cursor.close()
            conn.close()
            
            self.db_total_label.setText(f"Total: {total_count:,}")
            self.db_today_label.setText(f"Today: {today_count:,}")
            
        except Exception as e:
            print(f"[MainWindow] DB stats refresh failed: {e}")
            self.db_total_label.setText("Total: Error")
            self.db_today_label.setText("Today: Error")
    
    def _show_database_viewer(self):
        """Show database viewer dialog"""
        if not self.db_manager:
            QtWidgets.QMessageBox.warning(self, "Warning", "Database not connected")
            return
        
        viewer = DatabaseViewerDialog(self.db_manager, self)
        viewer.exec_()

    def closeEvent(self, event):
        """Handle window close"""
        self._stop_all()
        event.accept()


class DatabaseViewerDialog(QtWidgets.QDialog):
    """Database viewer dialog"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Database Viewer")
        self.resize(1100, 650)
        self._setup_ui()
        self._refresh_data()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Dark theme
        self.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                color: #e0e0e0;
            }
            QTableWidget {
                background: #252525;
                border: 1px solid #3d3d3d;
                color: #e0e0e0;
                gridline-color: #404040;
                alternate-background-color: #2a2a2a;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #333333;
            }
            QTableWidget::item:selected {
                background: #3d5a6e;
                color: #ffffff;
            }
            QHeaderView::section {
                background: #1e1e1e;
                color: #a0a0a0;
                padding: 8px;
                border: 1px solid #3d3d3d;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px 16px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: #3d3d3d;
            }
            QComboBox {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QLineEdit {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
        """)
        
        # Top controls
        controls_layout = QtWidgets.QHBoxLayout()
        
        # Filter by vehicle type
        controls_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.filter_combo = QtWidgets.QComboBox()
        self.filter_combo.addItems(["All", "car", "truck", "bus", "van", "motorbike"])
        self.filter_combo.currentTextChanged.connect(self._refresh_data)
        controls_layout.addWidget(self.filter_combo)
        
        # Search
        controls_layout.addWidget(QtWidgets.QLabel("Search:"))
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Camera name...")
        self.search_input.textChanged.connect(self._refresh_data)
        controls_layout.addWidget(self.search_input)
        
        controls_layout.addStretch()
        
        # Clear Database button
        clear_btn = QtWidgets.QPushButton("Clear DB")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #5c1a1a;
                border: 1px solid #7c2a2a;
            }
            QPushButton:hover {
                background: #6c2a2a;
            }
        """)
        clear_btn.clicked.connect(self._clear_database)
        controls_layout.addWidget(clear_btn)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_data)
        controls_layout.addWidget(refresh_btn)
        
        # Export button
        export_btn = QtWidgets.QPushButton("Export CSV")
        export_btn.clicked.connect(self._export_csv)
        controls_layout.addWidget(export_btn)
        
        layout.addLayout(controls_layout)
        
        # Split layout for table and statistics
        content_layout = QtWidgets.QHBoxLayout()
        
        # Main table (left side)
        table_layout = QtWidgets.QVBoxLayout()
        table_label = QtWidgets.QLabel("Detection Records")
        table_label.setStyleSheet("font-weight: bold; font-size: 12px; padding: 4px;")
        table_layout.addWidget(table_label)
        
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Camera", "Vehicle Type", 
            "Confidence", "ESAL Score"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(32)  # Row height
        self.table.setShowGrid(True)
        table_layout.addWidget(self.table)
        
        content_layout.addLayout(table_layout, 3)  # 70% width
        
        # Statistics panel (right side)
        stats_widget = QtWidgets.QWidget()
        stats_widget.setFixedWidth(250)
        stats_layout = QtWidgets.QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(8, 0, 0, 0)
        
        # Class distribution
        class_group = QtWidgets.QGroupBox("Detection by Class")
        class_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                padding-top: 8px;
            }
        """)
        class_layout = QtWidgets.QVBoxLayout(class_group)
        
        self.class_stats = QtWidgets.QTableWidget()
        self.class_stats.setColumnCount(2)
        self.class_stats.setHorizontalHeaderLabels(["Class", "Count"])
        self.class_stats.horizontalHeader().setStretchLastSection(True)
        self.class_stats.verticalHeader().setVisible(False)
        self.class_stats.setMaximumHeight(200)
        self.class_stats.setAlternatingRowColors(True)
        self.class_stats.setStyleSheet("""
            QTableWidget {
                background: #252525;
                alternate-background-color: #2a2a2a;
                gridline-color: #404040;
                border: 1px solid #3d3d3d;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background: #1e1e1e;
                color: #a0a0a0;
                padding: 6px;
                border: 1px solid #3d3d3d;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        class_layout.addWidget(self.class_stats)
        
        stats_layout.addWidget(class_group)
        
        # ESAL Score distribution
        esal_group = QtWidgets.QGroupBox("ESAL Scores")
        esal_group.setStyleSheet(class_group.styleSheet())
        esal_layout = QtWidgets.QVBoxLayout(esal_group)
        
        self.esal_stats = QtWidgets.QTextEdit()
        self.esal_stats.setReadOnly(True)
        self.esal_stats.setMaximumHeight(180)
        self.esal_stats.setStyleSheet("""
            QTextEdit {
                background: #252525;
                border: 1px solid #3d3d3d;
                font-family: "Courier New", monospace;
                font-size: 10px;
                padding: 8px;
                color: #d0d0d0;
                line-height: 1.3;
            }
        """)
        esal_layout.addWidget(self.esal_stats)
        
        stats_layout.addWidget(esal_group)
        stats_layout.addStretch()
        
        content_layout.addWidget(stats_widget, 1)  # 30% width
        
        layout.addLayout(content_layout)
        
        # Bottom info
        self.info_label = QtWidgets.QLabel("Loading...")
        self.info_label.setStyleSheet("color: #808080; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _refresh_data(self):
        """Refresh table data"""
        try:
            from ..core.esal_calculator import ESALCalculator
            esal_calc = ESALCalculator()
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM vehicle_detections WHERE 1=1"
            params = []
            
            # Filter by vehicle type
            vehicle_filter = self.filter_combo.currentText()
            if vehicle_filter != "All":
                query += " AND vehicle_type = %s"
                params.append(vehicle_filter)
            
            # Search by camera name
            search_text = self.search_input.text().strip()
            if search_text:
                query += " AND camera_name LIKE %s"
                params.append(f"%{search_text}%")
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Calculate class counts
            class_counts = {}
            esal_scores = []
            
            # Update main table
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                vehicle_type = row['vehicle_type'] or 'unknown'
                
                # Count by class
                class_counts[vehicle_type] = class_counts.get(vehicle_type, 0) + 1
                
                # Calculate ESAL score for this detection
                esal_score = esal_calc._get_score_per_vehicle(vehicle_type)
                esal_scores.append((vehicle_type, esal_score))
                
                # Fill table
                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(
                    str(row['timestamp']) if row['timestamp'] else 'N/A'
                ))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(
                    row['camera_name'] or 'Unknown'
                ))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(
                    vehicle_type
                ))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(
                    f"{row['confidence']:.2f}" if row['confidence'] else 'N/A'
                ))
                self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(
                    f"{esal_score:.2f}"
                ))
            
            # Update class statistics table
            self.class_stats.setRowCount(len(class_counts))
            sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
            for i, (vehicle_class, count) in enumerate(sorted_classes):
                self.class_stats.setItem(i, 0, QtWidgets.QTableWidgetItem(vehicle_class))
                count_item = QtWidgets.QTableWidgetItem(f"{count:,}")
                count_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.class_stats.setItem(i, 1, count_item)
            
            # Update ESAL statistics
            esal_text = "ESAL Score by Vehicle Type:\n\n"
            esal_by_class = {}
            for vtype, score in esal_scores:
                if vtype not in esal_by_class:
                    esal_by_class[vtype] = []
                esal_by_class[vtype].append(score)
            
            for vtype in sorted(esal_by_class.keys()):
                scores = esal_by_class[vtype]
                avg_score = sum(scores) / len(scores)
                total_score = sum(scores)
                esal_text += f"{vtype:12s}: {avg_score:6.2f} avg\n"
                esal_text += f"{'':12s}  {total_score:6.2f} total\n\n"
            
            total_esal = sum(score for _, score in esal_scores)
            esal_text += f"{'─' * 25}\n"
            esal_text += f"{'Total ESAL':12s}: {total_esal:6.2f}\n"
            
            self.esal_stats.setText(esal_text)
            
            self.info_label.setText(f"Showing {len(rows)} records (max 1000) | Total ESAL: {total_esal:.2f}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"[DatabaseViewer] Refresh failed: {e}")
            import traceback
            traceback.print_exc()
            self.info_label.setText(f"Error: {e}")
    
    def _export_csv(self):
        """Export table to CSV"""
        try:
            from datetime import datetime
            
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Export to CSV",
                f"detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                headers = []
                for col in range(self.table.columnCount()):
                    headers.append(self.table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Data
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)
            
            QtWidgets.QMessageBox.information(
                self, 
                "Success", 
                f"Exported {self.table.rowCount()} records to:\n{file_path}"
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Export failed:\n{e}"
            )
    
    def _clear_database(self):
        """Clear all detection records from database"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Database Clear",
            "⚠️ WARNING ⚠️\n\n"
            "This will DELETE ALL detection records from the database!\n\n"
            "This action CANNOT be undone.\n\n"
            "Are you sure you want to continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply != QtWidgets.QMessageBox.Yes:
            return
        
        # Double confirmation
        confirm_text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Final Confirmation",
            "Type 'DELETE' to confirm database clear:",
            QtWidgets.QLineEdit.Normal,
            ""
        )
        
        if not ok or confirm_text != "DELETE":
            QtWidgets.QMessageBox.information(
                self,
                "Cancelled",
                "Database clear operation cancelled."
            )
            return
        
        try:
            # Get count before deletion using a fresh connection
            conn1 = self.db_manager.get_connection()
            cursor1 = conn1.cursor()
            cursor1.execute("SELECT COUNT(*) as count FROM vehicle_detections")
            result = cursor1.fetchone()
            record_count = result['count'] if result else 0
            cursor1.close()
            conn1.close()
            
            # Use TRUNCATE instead of DELETE for better performance and avoid locking issues
            conn2 = self.db_manager.get_connection()
            cursor2 = conn2.cursor()
            
            try:
                # TRUNCATE is faster and avoids row-level locking
                cursor2.execute("TRUNCATE TABLE vehicle_detections")
                conn2.commit()
            except Exception as truncate_error:
                # If TRUNCATE fails, try DELETE with explicit table lock
                print(f"[Clear DB] TRUNCATE failed, trying DELETE: {truncate_error}")
                cursor2.execute("DELETE FROM vehicle_detections")
                conn2.commit()
            
            cursor2.close()
            conn2.close()
            
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Database cleared successfully!\n\n"
                f"Deleted {record_count:,} records."
            )
            
            # Refresh the view
            self._refresh_data()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to clear database:\n{e}"
            )
