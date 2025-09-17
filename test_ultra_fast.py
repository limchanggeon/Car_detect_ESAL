#!/usr/bin/env python3
"""
나노모델 초고속 테스트 - 최대 성능 확인
"""

import cv2
import time
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from car_detect_esal.core.detector import VehicleDetector
from car_detect_esal.core.performance_config import PerformanceConfig

def test_ultra_fast_mode():
    """초고속 모드 테스트"""
    print("🚀 나노모델 초고속 모드 테스트...")
    
    # 초고속 설정 가져오기
    ultra_fast_config = PerformanceConfig.get_preset("ultra_fast")
    print(f"📋 초고속 설정:")
    print(f"   • 해상도: {ultra_fast_config['imgsz']}x{ultra_fast_config['imgsz']}")
    print(f"   • 신뢰도: {ultra_fast_config['conf']}")
    print(f"   • 목표 FPS: {ultra_fast_config['fps_target']}")
    print(f"   • 처리 간격: {ultra_fast_config['sleep_time']}초")
    
    # 모델 로드 (초고속 설정)
    model_path = project_root / "weights" / "best.pt"
    if not model_path.exists():
        print(f"❌ 모델 파일을 찾을 수 없습니다: {model_path}")
        return
    
    detector = VehicleDetector(
        str(model_path), 
        imgsz=ultra_fast_config['imgsz'], 
        conf=ultra_fast_config['conf']
    )
    print(f"✅ 초고속 모델 로드 완료")
    
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
    
    cap = cv2.VideoCapture(str(demo_video))
    if not cap.isOpened():
        print("❌ 비디오 열기 실패")
        return
    
    # 원본 해상도
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"📏 원본: {orig_width}x{orig_height} → 처리: {ultra_fast_config['imgsz']}x{ultra_fast_config['imgsz']}")
    
    frame_count = 0
    start_time = time.time()
    detection_times = []
    resize_times = []
    total_times = []
    
    print("\n🏃‍♂️ 초고속 모드 테스트 중... (Ctrl+C로 종료)")
    print("=" * 60)
    
    last_print = time.time()
    
    try:
        while frame_count < 100:  # 100프레임 테스트
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            frame_start = time.time()
            
            # 1. 초고속 리사이징
            resize_start = time.time()
            target_size = ultra_fast_config['imgsz']
            if frame.shape[1] != target_size or frame.shape[0] != target_size:
                frame_resized = cv2.resize(frame, (target_size, target_size), interpolation=cv2.INTER_NEAREST)  # INTER_NEAREST가 더 빠름
            else:
                frame_resized = frame
            resize_time = time.time() - resize_start
            resize_times.append(resize_time)
            
            # 2. 초고속 탐지
            detect_start = time.time()
            try:
                annotated, results = detector.detect(frame_resized)
                detect_time = time.time() - detect_start
                detection_times.append(detect_time)
            except Exception as e:
                detect_time = 0
                print(f"⚠️  탐지 오류: {e}")
            
            frame_total_time = time.time() - frame_start
            total_times.append(frame_total_time)
            frame_count += 1
            
            # 초고속 모드 딜레이 (매우 짧음)
            time.sleep(ultra_fast_config['sleep_time'])
            
            # 실시간 진행상황 (더 자주 업데이트)
            current_time = time.time()
            if current_time - last_print >= 0.5:  # 0.5초마다 업데이트
                elapsed = current_time - start_time
                current_fps = frame_count / elapsed if elapsed > 0 else 0
                
                recent_detect = detection_times[-10:] if detection_times else []
                recent_resize = resize_times[-10:] if resize_times else []
                
                avg_detect_ms = sum(recent_detect) / len(recent_detect) * 1000 if recent_detect else 0
                avg_resize_ms = sum(recent_resize) / len(recent_resize) * 1000 if recent_resize else 0
                
                print(f"🏃‍♂️ 프레임: {frame_count:3d}/100 | "
                      f"FPS: {current_fps:6.1f} | "
                      f"탐지: {avg_detect_ms:5.1f}ms | "
                      f"리사이즈: {avg_resize_ms:4.1f}ms")
                
                last_print = current_time
    
    except KeyboardInterrupt:
        print("\n⏹️  테스트 중단됨")
    
    finally:
        cap.release()
        
        # 최종 결과
        total_time = time.time() - start_time
        if frame_count > 0 and total_time > 0:
            final_fps = frame_count / total_time
            avg_detect_ms = sum(detection_times) / len(detection_times) * 1000 if detection_times else 0
            avg_resize_ms = sum(resize_times) / len(resize_times) * 1000 if resize_times else 0
            avg_total_ms = sum(total_times) / len(total_times) * 1000 if total_times else 0
            
            print("\n" + "=" * 60)
            print("🏆 초고속 모드 최종 결과:")
            print(f"   • 총 처리 프레임: {frame_count}")
            print(f"   • 총 소요 시간: {total_time:.1f}초")
            print(f"   • 🚀 최종 FPS: {final_fps:.1f}")
            print(f"   • 평균 탐지 시간: {avg_detect_ms:.1f}ms")
            print(f"   • 평균 리사이즈 시간: {avg_resize_ms:.1f}ms")
            print(f"   • 평균 총 처리 시간: {avg_total_ms:.1f}ms")
            
            # 성능 평가
            if final_fps >= 15:
                print("\n🎉 훌륭한 성능! 목표 FPS 달성!")
            elif final_fps >= 10:
                print("\n✅ 좋은 성능! 실용적인 속도입니다.")
            elif final_fps >= 8:
                print("\n👍 괜찮은 성능! 추가 최적화 고려해보세요.")
            else:
                print("\n💡 성능 개선 권장사항:")
                print("   1. GPU 활용 (CUDA 설치)")
                print("   2. 더 작은 해상도 (256x256)")
                print("   3. 더 높은 confidence (0.9)")
                print("   4. 멀티스레딩 고려")

if __name__ == "__main__":
    test_ultra_fast_mode()