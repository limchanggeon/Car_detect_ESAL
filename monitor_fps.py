#!/usr/bin/env python3
"""
실시간 FPS 모니터링 도구 - GUI와 별개로 독립적으로 FPS 측정
"""

import cv2
import time
import sys
import threading
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from car_detect_esal.core.detector import VehicleDetector

class FPSMonitor:
    """FPS 실시간 모니터링 클래스"""
    
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.frame_times = []
        self.last_update = time.time()
        self.current_fps = 0.0
        
    def update(self):
        """프레임 처리 완료 시 호출"""
        current_time = time.time()
        self.frame_times.append(current_time)
        
        # 슬라이딩 윈도우로 FPS 계산
        if len(self.frame_times) > self.window_size:
            self.frame_times.pop(0)
        
        if len(self.frame_times) > 1:
            time_span = self.frame_times[-1] - self.frame_times[0]
            if time_span > 0:
                self.current_fps = (len(self.frame_times) - 1) / time_span
        
        return self.current_fps
    
    def get_fps(self):
        return self.current_fps

def test_real_fps():
    """실제 GUI와 유사한 환경에서 FPS 측정"""
    print("🎯 실시간 FPS 모니터링 시작...")
    
    # 모델 로드
    model_path = project_root / "weights" / "best.pt"
    if not model_path.exists():
        print(f"❌ 모델 파일을 찾을 수 없습니다: {model_path}")
        return
    
    detector = VehicleDetector(str(model_path), imgsz=640, conf=0.5)
    fps_monitor = FPSMonitor(window_size=30)
    
    # 테스트 비디오
    demo_video = project_root / "demo_videos" / "화면 기록 2025-08-22 오후 4.34.08.mp4"
    if not demo_video.exists():
        demo_dir = project_root / "demo_videos"
        video_files = list(demo_dir.glob("*.mp4"))
        if video_files:
            demo_video = video_files[0]
        else:
            print(f"❌ 데모 비디오를 찾을 수 없습니다: {demo_dir}")
            return
    
    print(f"📹 모니터링 비디오: {demo_video.name}")
    
    cap = cv2.VideoCapture(str(demo_video))
    if not cap.isOpened():
        print("❌ 비디오 열기 실패")
        return
    
    # 원본 해상도
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"📏 원본: {orig_width}x{orig_height} → 처리: 640x640")
    
    frame_count = 0
    start_time = time.time()
    last_print = time.time()
    
    # 성능 통계
    detection_times = []
    resize_times = []
    
    print("🔄 실시간 FPS 모니터링 중... (Ctrl+C로 종료)")
    print("=" * 60)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            frame_start = time.time()
            
            # 1. 리사이징 (GUI와 동일)
            resize_start = time.time()
            if frame.shape[1] != 640 or frame.shape[0] != 640:
                frame_resized = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR)
            else:
                frame_resized = frame
            resize_time = time.time() - resize_start
            resize_times.append(resize_time)
            
            # 2. 탐지 (GUI와 동일)
            detect_start = time.time()
            try:
                annotated, results = detector.detect(frame_resized)
                detect_time = time.time() - detect_start
                detection_times.append(detect_time)
            except Exception as e:
                detect_time = 0
                print(f"⚠️  탐지 오류: {e}")
            
            # 3. FPS 업데이트
            current_fps = fps_monitor.update()
            frame_count += 1
            
            # 4. GUI 시뮬레이션 딜레이 (StreamWorker의 0.1초 sleep)
            time.sleep(0.1)
            
            # 1초마다 상태 출력
            current_time = time.time()
            if current_time - last_print >= 1.0:
                elapsed = current_time - start_time
                avg_fps = frame_count / elapsed if elapsed > 0 else 0
                
                # 최근 10개 프레임의 평균 시간
                recent_detect_times = detection_times[-10:] if detection_times else []
                recent_resize_times = resize_times[-10:] if resize_times else []
                
                avg_detect_ms = sum(recent_detect_times) / len(recent_detect_times) * 1000 if recent_detect_times else 0
                avg_resize_ms = sum(recent_resize_times) / len(recent_resize_times) * 1000 if recent_resize_times else 0
                
                print(f"🎬 프레임: {frame_count:4d} | "
                      f"실시간FPS: {current_fps:5.1f} | "
                      f"평균FPS: {avg_fps:5.1f} | "
                      f"탐지: {avg_detect_ms:5.1f}ms | "
                      f"리사이즈: {avg_resize_ms:4.1f}ms")
                
                last_print = current_time
                
                # 저성능 경고
                if current_fps < 2.0 and frame_count > 30:
                    print("⚠️  FPS가 매우 낮습니다! 최적화 권장사항:")
                    print("   - GPU 사용 확인")
                    print("   - confidence 임계값 증가")
                    print("   - 모델 경량화 고려")
                    print("   - 해상도 더 낮춤 고려")
                
    except KeyboardInterrupt:
        print("\n⏹️  모니터링 종료됨")
    
    finally:
        cap.release()
        
        # 최종 통계
        total_time = time.time() - start_time
        if frame_count > 0 and total_time > 0:
            final_fps = frame_count / total_time
            avg_detect_ms = sum(detection_times) / len(detection_times) * 1000 if detection_times else 0
            avg_resize_ms = sum(resize_times) / len(resize_times) * 1000 if resize_times else 0
            
            print("\n" + "=" * 60)
            print("📊 최종 성능 통계:")
            print(f"   • 총 처리 프레임: {frame_count}")
            print(f"   • 총 소요 시간: {total_time:.1f}초")
            print(f"   • 최종 평균 FPS: {final_fps:.2f}")
            print(f"   • 평균 탐지 시간: {avg_detect_ms:.1f}ms")
            print(f"   • 평균 리사이즈 시간: {avg_resize_ms:.1f}ms")
            
            if final_fps < 5:
                print("💡 성능 개선 방안:")
                print("   1. GPU 활용 (CUDA)")
                print("   2. Confidence 임계값 상향 (0.5 → 0.7)")
                print("   3. 해상도 축소 (640 → 416)")
                print("   4. 처리 간격 증가 (0.1s → 0.2s)")

if __name__ == "__main__":
    test_real_fps()