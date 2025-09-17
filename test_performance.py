#!/usr/bin/env python3
"""
성능 테스트 스크립트 - 탐지 속도 및 해상도 확인
"""

import cv2
import time
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from car_detect_esal.core.detector import VehicleDetector

def test_detection_speed():
    """탐지 속도 테스트"""
    print("🚀 성능 테스트 시작...")
    
    # 모델 로드
    model_path = project_root / "weights" / "best.pt"
    if not model_path.exists():
        print(f"❌ 모델 파일을 찾을 수 없습니다: {model_path}")
        return
    
    detector = VehicleDetector(str(model_path), imgsz=640, conf=0.5)
    print(f"✅ 모델 로드 완료: {model_path}")
    
    # 테스트 비디오 경로
    demo_video = project_root / "demo_videos" / "화면 기록 2025-08-22 오후 4.34.08.mp4"
    if not demo_video.exists():
        # 다른 비디오 파일 찾기
        demo_dir = project_root / "demo_videos"
        video_files = list(demo_dir.glob("*.mp4"))
        if video_files:
            demo_video = video_files[0]
        else:
            print(f"❌ 데모 비디오를 찾을 수 없습니다: {demo_dir}")
            return
    
    print(f"📹 테스트 비디오: {demo_video}")
    
    # 비디오 캡처 시작
    cap = cv2.VideoCapture(str(demo_video))
    if not cap.isOpened():
        print("❌ 비디오 열기 실패")
        return
    
    # 원본 해상도 확인
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"📏 원본 해상도: {orig_width}x{orig_height}")
    
    frame_count = 0
    total_time = 0
    resize_times = []
    detection_times = []
    
    print("\n🔍 성능 측정 중...")
    
    try:
        for i in range(50):  # 50프레임 테스트
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 비디오 처음으로
                continue
            
            frame_start = time.time()
            
            # 1. 리사이징 시간 측정
            resize_start = time.time()
            if frame.shape[1] != 640 or frame.shape[0] != 640:
                frame_resized = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR)
            else:
                frame_resized = frame
            resize_time = time.time() - resize_start
            resize_times.append(resize_time)
            
            # 2. 탐지 시간 측정
            detect_start = time.time()
            annotated, results = detector.detect(frame_resized)
            detect_time = time.time() - detect_start
            detection_times.append(detect_time)
            
            frame_total_time = time.time() - frame_start
            total_time += frame_total_time
            frame_count += 1
            
            # 진행상황 표시
            if frame_count % 10 == 0:
                print(f"  프레임 {frame_count}/50 처리 완료...")
    
    except KeyboardInterrupt:
        print("\n⏹️  사용자가 테스트를 중단했습니다.")
    
    finally:
        cap.release()
    
    if frame_count > 0:
        # 결과 출력
        avg_total_time = total_time / frame_count
        avg_resize_time = sum(resize_times) / len(resize_times) if resize_times else 0
        avg_detect_time = sum(detection_times) / len(detection_times) if detection_times else 0
        fps = 1.0 / avg_total_time if avg_total_time > 0 else 0
        
        print(f"\n📊 성능 테스트 결과:")
        print(f"  • 처리한 프레임 수: {frame_count}")
        print(f"  • 평균 리사이징 시간: {avg_resize_time*1000:.1f}ms")
        print(f"  • 평균 탐지 시간: {avg_detect_time*1000:.1f}ms")
        print(f"  • 평균 총 처리 시간: {avg_total_time*1000:.1f}ms")
        print(f"  • 예상 FPS: {fps:.1f}")
        
        # 권장사항
        if fps < 5:
            print(f"\n⚠️  낮은 FPS 감지! 다음을 확인해보세요:")
            print(f"    - GPU 사용 가능 여부")
            print(f"    - 모델 크기 (현재: 640x640)")
            print(f"    - Confidence 임계값 (현재: 0.5)")
        elif fps < 10:
            print(f"\n💡 보통 성능입니다. 더 나은 성능을 위해:")
            print(f"    - GPU 활용 고려")
            print(f"    - 모델 경량화 고려")
        else:
            print(f"\n✅ 좋은 성능입니다!")
    
    print(f"\n🎯 테스트 완료!")

if __name__ == "__main__":
    test_detection_speed()