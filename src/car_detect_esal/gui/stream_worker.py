"""
Background worker thread for video stream processing and inference
"""

import time
import math
from PyQt5 import QtCore, QtGui
from typing import Optional, Tuple, Dict
from ..core.detector import VehicleDetector, VehicleTracker
from ..database import TrafficDatabaseManager

class StreamWorker(QtCore.QThread):
    """
    비디오 소스를 읽고 모델 추론을 수행하여 QImage를 방출하는 워커 스레드
    
    roi 속성이 설정되면 해당 영역만 크롭해서 추론하고, 
    결과를 원본 프레임에 오버레이한다.
    """

    frame_ready = QtCore.pyqtSignal(object)  # QImage
    status = QtCore.pyqtSignal(str)
    count_changed = QtCore.pyqtSignal(object)  # Dict[str, int]

    def __init__(self, source: str, detector: VehicleDetector, performance_config: dict = None, 
                 db_manager: TrafficDatabaseManager = None, camera_id: str = None):
        super().__init__()
        self.source = source
        self.detector = detector
        self._running = True
        
        # 성능 설정 (기본값 사용 또는 전달받은 설정)
        self.performance_config = performance_config or {
            "sleep_time": 0.1,
            "imgsz": 640
        }
        
        # ROI: (x, y, w, h) in 원본 프레임 픽셀 좌표 또는 None
        self.roi = None
        
        # 차량 추적기
        self.tracker = VehicleTracker()
        
        # 데이터베이스 관련
        self.db_manager = db_manager
        self.camera_id = camera_id or f"cam_{int(time.time())}"
        self.detection_buffer = []  # 탐지 결과 버퍼
        self.last_db_save = time.time()
        
        # FPS 측정용 변수들
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0

    def stop(self):
        """워커 스레드 중지"""
        self._running = False

    def run(self):
        """메인 워커 루프"""
        import cv2
        
        # 소스 열기 시도
        cap = cv2.VideoCapture(self.source)
        
        if not cap.isOpened():
            self.status.emit("소스 열기 실패")
            return

        self.status.emit("실행 중")
        frame_count = 0
        last_fps_update = time.time()
        
        while self._running:
            ret, frame = cap.read()
            if not ret:
                # 비디오 파일의 끝에 도달했을 때 처음부터 다시 시작
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame_count += 1
            
            # 프레임 처리 및 탐지 수행
            annotated_frame = self._process_frame(frame)
            
            # QImage로 변환하여 방출
            qimg = self._frame_to_qimage(annotated_frame)
            if qimg is not None:
                self.frame_ready.emit(qimg)
            
            # FPS 계산
            current_time = time.time()
            self.fps_counter += 1
            
            # 1초마다 FPS 업데이트
            if current_time - last_fps_update >= 1.0:
                self.current_fps = self.fps_counter / (current_time - last_fps_update)
                self.fps_counter = 0
                last_fps_update = current_time
            
            # 상태 업데이트 (덜 자주 업데이트하여 UI 부하 감소)
            if frame_count % 30 == 0:  # 30프레임마다 한 번씩만 업데이트
                total_count = self.tracker.count
                self.status.emit(f"🎥 FPS: {self.current_fps:.1f} | 프레임: {frame_count} | 카운트: {total_count}")
            
            # 적절한 프레임레이트 유지 (부드러운 재생을 위해 sleep 시간 단축)
            sleep_time = self.performance_config.get("sleep_time", 0.03)  # 33FPS 목표
            time.sleep(sleep_time)

        cap.release()
        self.status.emit("중지됨")

    def _process_frame(self, frame) -> any:
        """프레임 처리 및 차량 탐지"""
        try:
            import cv2
            
            # 프레임을 성능 설정에 따른 해상도로 리사이즈 (속도 최적화)
            target_size = self.performance_config.get("imgsz", 640)
            h, w = frame.shape[:2]
            original_frame_size = (w, h)  # 데이터베이스 저장용 원본 크기
            
            if w != target_size or h != target_size:
                frame = cv2.resize(frame, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
            
            # 탐지 수행
            annotated, results = self.detector.detect(frame, self.roi)
            
            # 탐지 결과를 추적 시스템에 전달하고 새로운 객체만 DB에 저장
            if results is not None:
                detections = self._extract_detections_with_bbox(results, original_frame_size)
                
                # 추적기 업데이트 - 새로운 객체만 반환
                updated_counts, new_detections = self.tracker.update(detections)
                
                # 새로운 객체만 DB에 저장
                if new_detections and self.db_manager:
                    self._save_new_detections_to_db(new_detections)
                
                # 카운트 변경 시그널 방출
                if updated_counts:
                    self.count_changed.emit(dict(updated_counts))
            
            return annotated
            
        except Exception as e:
            print(f"[StreamWorker] 프레임 처리 오류: {e}")
            return frame

    def _extract_detections_with_bbox(self, results, original_frame_size) -> list:
        """YOLO 결과에서 탐지된 객체의 전체 정보 추출 (추적 및 DB 저장용)"""
        detections = []
        
        try:
            boxes = getattr(results[0], 'boxes', None)
            names = getattr(results[0], 'names', {})
            
            if boxes is None or not hasattr(boxes, 'xyxy'):
                return detections
                
            xyxy = boxes.xyxy.tolist() if hasattr(boxes.xyxy, 'tolist') else []
            cls_list = boxes.cls.tolist() if hasattr(boxes, 'cls') and hasattr(boxes.cls, 'tolist') else []
            conf_list = boxes.conf.tolist() if hasattr(boxes, 'conf') and hasattr(boxes.conf, 'tolist') else []
            
            frame_width, frame_height = original_frame_size
            
            for i, bbox in enumerate(xyxy):
                if len(bbox) < 4:
                    continue
                    
                x1, y1, x2, y2 = bbox[:4]
                
                # 중심점 계산
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                
                # ROI 오프셋 적용 (ROI가 있는 경우)
                if self.roi:
                    cx += self.roi[0]
                    cy += self.roi[1]
                
                # 클래스 및 신뢰도
                vehicle_class = int(cls_list[i]) if i < len(cls_list) else 0
                vehicle_type = str(names.get(vehicle_class, 'unknown'))
                confidence = float(conf_list[i]) if i < len(conf_list) else 0.0
                
                # 낮은 신뢰도는 제외
                if confidence < 0.5:
                    continue
                
                # 정규화된 좌표 계산 (0.0 ~ 1.0)
                norm_x = cx / frame_width
                norm_y = cy / frame_height
                norm_width = (x2 - x1) / frame_width
                norm_height = (y2 - y1) / frame_height
                
                # 차량 타입 매핑
                vehicle_type_map = {
                    'car': 'car',
                    'motorcycle': 'motorbike',
                    'bus': 'bus',
                    'truck': 'truck',
                    'bicycle': 'motorbike',
                    'van': 'van'
                }
                
                standardized_type = vehicle_type_map.get(vehicle_type.lower(), 'car')
                
                # bbox 데이터
                bbox_data = {
                    'vehicle_type': standardized_type,
                    'vehicle_class': vehicle_class,
                    'bbox_x': norm_x,
                    'bbox_y': norm_y,
                    'bbox_width': norm_width,
                    'bbox_height': norm_height
                }
                
                # (중심x, 중심y, 클래스명, 신뢰도, bbox데이터) 형태로 반환
                detections.append((cx, cy, standardized_type, confidence, bbox_data))
                    
        except Exception as e:
            print(f"[StreamWorker] 탐지 추출 오류: {e}")
        
        return detections

    def _save_new_detections_to_db(self, new_detections):
        """새로 발견된 객체만 DB에 저장 (중복 방지)"""
        try:
            if not self.db_manager or not new_detections:
                return
            
            # 버퍼에 추가
            self.detection_buffer.extend(new_detections)
            
            # 버퍼가 가득 차거나 일정 시간이 지나면 저장
            current_time = time.time()
            buffer_full = len(self.detection_buffer) >= 20  # 20개씩 배치 저장 (이전 50에서 감소)
            time_to_save = (current_time - self.last_db_save) >= 10  # 10초마다 저장 (이전 30초에서 감소)
            
            if (buffer_full or time_to_save) and self.detection_buffer:
                try:
                    success = self.db_manager.record_vehicle_detection(
                        self.camera_id, 
                        self.detection_buffer
                    )
                    
                    if success:
                        saved_count = len(self.detection_buffer)
                        self.detection_buffer.clear()
                        self.last_db_save = current_time
                        print(f"[DB] ✅ {saved_count}개의 새로운 차량 저장 완료 (중복 제거됨)")
                    else:
                        print("[DB] ❌ 데이터베이스 저장 실패")
                        
                except Exception as e:
                    print(f"[DB] 저장 중 오류: {e}")
                    
        except Exception as e:
            print(f"[StreamWorker] DB 저장 처리 오류: {e}")

    def _frame_to_qimage(self, frame) -> Optional[QtGui.QImage]:
        """OpenCV 프레임을 QImage로 변환"""
        try:
            import cv2
            
            # BGR to RGB 변환
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = rgb.strides[0]
            
            qimg = QtGui.QImage(
                rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888
            )
            
            # QImage가 자체 버퍼를 소유하도록 복사
            return qimg.copy()
            
        except Exception as e:
            print(f"[StreamWorker] QImage 변환 오류: {e}")
            try:
                # 그레이스케일로 폴백
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                h, w = gray.shape
                qimg = QtGui.QImage(gray.data, w, h, w, QtGui.QImage.Format_Grayscale8)
                return qimg.copy()
            except:
                return None

    def reset_count(self):
        """카운트 리셋"""
        self.tracker.reset()