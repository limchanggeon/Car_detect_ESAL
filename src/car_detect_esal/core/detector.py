"""
Vehicle detection module using YOLOv8
"""

import cv2
import time
import math
from typing import Optional, Dict, List, Tuple, Any
from PyQt5 import QtCore

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

class VehicleDetector:
    """YOLOv8 기반 차량 탐지 클래스"""
    
    def __init__(self, model_path: str, imgsz: int = 640, conf: float = 0.5):
        self.model_path = model_path
        self.imgsz = imgsz
        self.conf = conf  # 더 높은 confidence로 불필요한 탐지 줄임
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """모델 로드"""
        if YOLO is None:
            raise ImportError("ultralytics 패키지가 설치되어 있지 않습니다.")
        
        try:
            self.model = YOLO(self.model_path)
            print(f"[VehicleDetector] 모델 로드 완료: {self.model_path}")
        except Exception as e:
            raise RuntimeError(f"모델 로드 실패: {e}")
    
    def detect(self, frame: Any, roi: Optional[Tuple[int, int, int, int]] = None) -> Tuple[Any, Any]:
        """
        프레임에서 차량 탐지 수행
        
        Args:
            frame: 입력 프레임
            roi: (x, y, w, h) 관심 영역
            
        Returns:
            (annotated_frame, results)
        """
        if self.model is None:
            return frame, None
            
        try:
            if roi:
                x, y, w, h = roi
                h_frame, w_frame = frame.shape[:2]
                x = max(0, min(int(x), w_frame - 1))
                y = max(0, min(int(y), h_frame - 1))
                w = max(1, min(int(w), w_frame - x))
                h = max(1, min(int(h), h_frame - y))
                
                crop = frame[y:y+h, x:x+w]
                results = self.model(
                    crop, 
                    imgsz=self.imgsz, 
                    conf=self.conf,
                    verbose=False,
                    device='cpu',
                    half=False,
                    max_det=100,
                    agnostic_nms=True,
                    augment=False
                )
                
                try:
                    annotated_crop = results[0].plot()
                except Exception:
                    annotated_crop = crop
                    
                annotated = frame.copy()
                try:
                    annotated[y:y+h, x:x+w] = annotated_crop
                except Exception:
                    annotated = frame
            else:
                # 나노모델 최적화: 더 공격적인 최적화 옵션
                results = self.model(
                    frame, 
                    imgsz=self.imgsz, 
                    conf=self.conf,
                    verbose=False,
                    device='cpu',
                    half=False,
                    max_det=100,    # 최대 탐지 수 제한
                    agnostic_nms=True,  # 클래스 무관 NMS (더 빠름)
                    augment=False   # 증강 비활성화 (속도 향상)
                )
                annotated = results[0].plot()
                
            return annotated, results
            
        except Exception as e:
            print(f"[VehicleDetector] 탐지 오류: {e}")
            return frame, None


class VehicleTracker:
    """간단한 차량 추적 클래스"""
    
    def __init__(self, track_ttl: float = 1.0, match_threshold: float = 50.0):
        self.track_ttl = track_ttl
        self.match_threshold = match_threshold
        self.tracks = []
        self.count = 0
        self.counts = {}
    
    def update(self, detections: List[Tuple[float, float, str]]) -> Dict[str, int]:
        """
        탐지 결과로 추적 업데이트
        
        Args:
            detections: [(x, y, class_name), ...] 형태의 탐지 결과
            
        Returns:
            클래스별 카운트 딕셔너리
        """
        now = time.time()
        
        # 만료된 추적 제거
        self.tracks = [t for t in self.tracks if now - t['last_seen'] < self.track_ttl]
        
        for cx, cy, class_name in detections:
            matched = False
            
            # 기존 추적과 매칭 시도
            for track in self.tracks:
                dx = track['pos'][0] - cx
                dy = track['pos'][1] - cy
                dist = math.hypot(dx, dy)
                
                if dist < self.match_threshold:
                    track['pos'] = (cx, cy)
                    track['last_seen'] = now
                    matched = True
                    break
            
            # 새로운 추적 생성
            if not matched:
                self.tracks.append({
                    'pos': (cx, cy),
                    'last_seen': now
                })
                
                # 카운트 업데이트
                self.counts[class_name] = self.counts.get(class_name, 0) + 1
                self.count += 1
        
        return dict(self.counts)
    
    def reset(self):
        """추적 상태 리셋"""
        self.tracks.clear()
        self.count = 0
        self.counts.clear()