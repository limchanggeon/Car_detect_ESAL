#!/usr/bin/env python3
"""
디렉터리 내 비디오 파일들을 순회하며 YOLOv8 모델로 실시간(보여주기) 추론을 수행하고
주석된 비디오를 저장하는 스크립트입니다.

사용법:
  python infer_videos.py --model weights/best.pt --folder demo_videos

옵션:
  --watch : 폴더를 계속 감시하여 새 비디오가 추가되면 자동으로 처리합니다.
"""
import argparse
import sys
import time
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Run YOLOv8 inference on videos in a folder")
    p.add_argument("--model", default="weights/best.pt", help="모델 파일 경로 (기본: weights/best.pt)")
    p.add_argument("--folder", default="demo_videos", help="비디오가 들어있는 폴더 (기본: demo_videos)")
    p.add_argument("--imgsz", type=int, default=640, help="입력 이미지 크기")
    p.add_argument("--conf", type=float, default=0.25, help="confidence threshold")
    p.add_argument("--device", default=None, help="device, 예: 0 or cpu (기본: 자동)")
    p.add_argument("--save-dir", default="runs/detect/video_predict", help="결과 저장 디렉터리")
    p.add_argument("--exist-ok", action="store_true", help="기존 디렉터리 덮어쓰기")
    p.add_argument("--watch", action="store_true", help="폴더를 감시하여 새 파일이 들어오면 자동 처리")
    p.add_argument("--interval", type=float, default=5.0, help="감시 모드에서 폴더 폴링 간격(초)")
    return p.parse_args()


def list_videos(folder: Path):
    exts = ["*.mp4", "*.mov", "*.avi", "*.mkv"]
    files = []
    for e in exts:
        files.extend(sorted(folder.glob(e)))
    return files


def main():
    args = parse_args()

    try:
        from ultralytics import YOLO
    except Exception:
        print("ultralytics 패키지가 필요합니다. 아래 명령으로 설치하세요:")
        print("  python3 -m pip install -r requirements.txt")
        sys.exit(1)

    model_path = Path(args.model)
    folder = Path(args.folder)
    if not folder.exists():
        print(f"폴더가 존재하지 않아 생성합니다: {folder}")
        folder.mkdir(parents=True, exist_ok=True)

    processed = set()

    y = YOLO(str(model_path))

    def process(video_path: Path):
        print(f"처리 시작: {video_path}")
        project = str(Path(args.save_dir).parent)
        # 결과 폴더 이름에 원본 비디오명을 붙임
        name = Path(args.save_dir).name + "_" + video_path.stem
        y.predict(
            source=str(video_path),
            imgsz=args.imgsz,
            conf=args.conf,
            device=args.device,
            save=True,
            show=True,
            project=project,
            name=name,
            exist_ok=args.exist_ok,
        )
        print(f"처리 완료: {video_path} -> {Path(project)/name}")

    while True:
        videos = list_videos(folder)
        new_videos = [v for v in videos if v not in processed]
        if new_videos:
            for v in new_videos:
                try:
                    process(v)
                except KeyboardInterrupt:
                    print("중단 요청, 종료합니다.")
                    sys.exit(0)
                except Exception as e:
                    print(f"비디오 처리 중 오류: {v} -> {e}")
                processed.add(v)
        else:
            if not args.watch:
                print("처리할 새 비디오가 없습니다. 종료합니다.")
                break
        if args.watch:
            time.sleep(args.interval)
        else:
            break


if __name__ == "__main__":
    main()
