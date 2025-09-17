"""
Background worker thread for video stream processing and inference
"""

import time
import math
from PyQt5 import QtCore, QtGui
from typing import Optional, Tuple, Dict
from ..core.detector import VehicleDetector, VehicleTracker

class StreamWorker(QtCore.QThread):
    """
    비디오 소스를 읽고 모델 추론을 수행하여 QImage를 방출하는 워커 스레드
    
    roi 속성이 설정되면 해당 영역만 크롭해서 추론하고, 
    결과를 원본 프레임에 오버레이한다.
    """

    frame_ready = QtCore.pyqtSignal(object)  # QImage
    status = QtCore.pyqtSignal(str)
    count_changed = QtCore.pyqtSignal(object)  # Dict[str, int]

    def __init__(self, source: str, detector: VehicleDetector):
        super().__init__()
        self.source = source
        self.detector = detector
        self._running = True
        
        # ROI: (x, y, w, h) in 원본 프레임 픽셀 좌표 또는 None
        self.roi = None
        
        # 차량 추적기
        self.tracker = VehicleTracker()

    def stop(self):
        """워커 스레드 중지"""
        self._running = False

    def run(self):
        """메인 워커 루프"""
        import cv2
        
        print(f"[StreamWorker] 소스 열기: {self.source}")
        cap = cv2.VideoCapture(self.source)
        
        if not cap.isOpened():
            self.status.emit("소스 열기 실패")
            print(f"[StreamWorker] 소스 열기 실패: {self.source}")
            return

        self.status.emit("실행 중")
        frame_count = 0
        
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
            
            # 상태 업데이트 (주기적으로만)
            if frame_count % 30 == 0:
                total_count = self.tracker.count
                self.status.emit(f"실행 중 | 프레임: {frame_count} | 카운트: {total_count}")
            
            # 적절한 프레임레이트 유지 (처리 속도 최적화)
            time.sleep(0.1)  # ~10 FPS (탐지 속도 향상)

        cap.release()
        self.status.emit("중지됨")

    def _process_frame(self, frame) -> any:
        """프레임 처리 및 차량 탐지"""
        try:
            import cv2
            
            # 프레임을 640x640으로 리사이즈 (속도 최적화)
            h, w = frame.shape[:2]
            if w != 640 or h != 640:
                frame = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR)
            
            # 탐지 수행
            annotated, results = self.detector.detect(frame, self.roi)
            
            # 카운팅 로직 (roi가 있을 때만)
            if self.roi and results is not None:
                detections = self._extract_detections(results, self.roi)
                updated_counts = self.tracker.update(detections)
                
                # 카운트 변경 시그널 방출
                if updated_counts:
                    self.count_changed.emit(dict(updated_counts))
            
            return annotated
            
        except Exception as e:
            print(f"[StreamWorker] 프레임 처리 오류: {e}")
            return frame

    def _extract_detections(self, results, roi) -> list:
        """YOLO 결과에서 탐지된 객체의 중심점과 클래스 추출"""
        detections = []
        
        try:
            boxes = getattr(results[0], 'boxes', None)
            names = getattr(results[0], 'names', {})
            
            if boxes is not None and hasattr(boxes, 'xyxy'):
                xyxy = boxes.xyxy.tolist() if hasattr(boxes.xyxy, 'tolist') else []
                cls_list = boxes.cls.tolist() if hasattr(boxes, 'cls') and hasattr(boxes.cls, 'tolist') else []
                
                for i, bbox in enumerate(xyxy):
                    if len(bbox) < 4:
                        continue
                        
                    x1, y1, x2, y2 = bbox[:4]
                    cx = x1 + (x2 - x1) / 2.0
                    cy = y1 + (y2 - y1) / 2.0
                    
                    # ROI 오프셋을 고려하여 원본 프레임 좌표로 변환
                    orig_cx = roi[0] + cx
                    orig_cy = roi[1] + cy
                    
                    # 클래스 이름 추출
                    class_name = 'unknown'
                    if i < len(cls_list):
                        cls_idx = int(cls_list[i])
                        class_name = str(names.get(cls_idx, 'unknown'))
                    
                    detections.append((orig_cx, orig_cy, class_name))
                    
        except Exception as e:
            print(f"[StreamWorker] 탐지 추출 오류: {e}")
        
        return detections

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