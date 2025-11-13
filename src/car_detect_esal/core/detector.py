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
            # 모델 로드 완료
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
    """차량 추적 클래스 - 중복 저장 방지"""
    
    def __init__(self, track_ttl: float = 3.0, match_threshold: float = 100.0):
        """
        Args:
            track_ttl: 추적 유지 시간(초) - 객체가 이 시간동안 사라지면 추적 종료
            match_threshold: 같은 객체로 판단하는 거리 임계값(픽셀)
        """
        self.track_ttl = track_ttl
        self.match_threshold = match_threshold
        self.tracks = []  # 현재 추적 중인 객체들
        self.count = 0  # 총 발견한 객체 수
        self.counts = {}  # 클래스별 카운트
        self.next_track_id = 0  # 다음 추적 ID
        self.saved_track_ids = set()  # DB에 이미 저장된 추적 ID들
    
    def update(self, detections: List[Tuple[float, float, str, float, Dict]]) -> Tuple[Dict[str, int], List[Dict]]:
        """
        탐지 결과로 추적 업데이트 및 새로운 객체만 반환
        
        Args:
            detections: [(x, y, class_name, confidence, bbox_data), ...] 형태의 탐지 결과
            
        Returns:
            (클래스별 카운트 딕셔너리, 새로 발견된 객체 리스트)
        """
        now = time.time()
        new_detections = []  # DB에 저장할 새로운 객체들
        
        # 만료된 추적 제거 (3초 이상 안 보인 객체)
        self.tracks = [t for t in self.tracks if now - t['last_seen'] < self.track_ttl]
        
        # 각 탐지 결과에 대해 처리
        for detection_data in detections:
            cx, cy, class_name, confidence, bbox_data = detection_data
            matched = False
            matched_track = None
            
            # 기존 추적과 매칭 시도 (가장 가까운 객체 찾기)
            min_dist = float('inf')
            for track in self.tracks:
                # 같은 클래스만 매칭
                if track['class_name'] != class_name:
                    continue
                    
                dx = track['pos'][0] - cx
                dy = track['pos'][1] - cy
                dist = math.hypot(dx, dy)
                
                if dist < self.match_threshold and dist < min_dist:
                    min_dist = dist
                    matched_track = track
                    matched = True
            
            # 기존 추적과 매칭된 경우 - 위치만 업데이트
            if matched and matched_track:
                matched_track['pos'] = (cx, cy)
                matched_track['last_seen'] = now
                matched_track['confidence'] = max(matched_track.get('confidence', 0), confidence)
            
            # 새로운 추적 생성 - 처음 보는 객체
            else:
                track_id = self.next_track_id
                self.next_track_id += 1
                
                new_track = {
                    'track_id': track_id,
                    'pos': (cx, cy),
                    'class_name': class_name,
                    'confidence': confidence,
                    'last_seen': now,
                    'first_seen': now,
                    'bbox_data': bbox_data
                }
                self.tracks.append(new_track)
                
                # 카운트 업데이트
                self.counts[class_name] = self.counts.get(class_name, 0) + 1
                self.count += 1
                
                # DB에 저장할 새로운 객체로 추가 (한 번만 저장)
                if track_id not in self.saved_track_ids:
                    detection_record = {
                        'vehicle_type': bbox_data['vehicle_type'],
                        'vehicle_class': bbox_data['vehicle_class'],
                        'confidence': confidence,
                        'bbox_x': bbox_data['bbox_x'],
                        'bbox_y': bbox_data['bbox_y'],
                        'bbox_width': bbox_data['bbox_width'],
                        'bbox_height': bbox_data['bbox_height'],
                        'track_id': track_id  # 추적 ID 추가
                    }
                    new_detections.append(detection_record)
                    self.saved_track_ids.add(track_id)
        
        return dict(self.counts), new_detections
    
    def reset(self):
        """추적 상태 리셋"""
        self.tracks.clear()
        self.count = 0
        self.counts.clear()
        self.next_track_id = 0
        self.saved_track_ids.clear()