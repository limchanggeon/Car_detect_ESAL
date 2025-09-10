#!/usr/bin/env python3
"""
간단한 YOLOv8 추론 스크립트
사용 예:
  python infer.py --model weights/best.pt --source labels.jpg

이 스크립트는 로컬에 ultralytics가 설치되어 있다고 가정합니다.
설치가 되어있지 않으면 오류 메시지와 함께 설치 명령을 출력합니다.
"""
import argparse
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Run inference with a YOLOv8 model")
    p.add_argument("--model", default="weights/best.pt", help="경로 또는 모델 이름 (기본: weights/best.pt)")
    p.add_argument("--source", default="labels.jpg", help="이미지/폴더/비디오/스트림 입력 (기본: labels.jpg)")
    p.add_argument("--imgsz", type=int, default=640, help="입력 이미지 크기 (기형: 640)")
    p.add_argument("--conf", type=float, default=0.25, help="confidence threshold")
    p.add_argument("--device", default=None, help="device, 예: 0 or cpu (기본: 자동)")
    p.add_argument("--save-dir", default="runs/detect/predict", help="결과 저장 디렉터리")
    p.add_argument("--exist-ok", action="store_true", help="기존 디렉터리 덮어쓰기")
    return p.parse_args()


def main():
    args = parse_args()

    try:
        from ultralytics import YOLO
    except Exception as e:
        print("ultralytics 패키지가 필요합니다. 아래 명령으로 설치하세요:")
        print("  python3 -m pip install -r requirements.txt")
        print("또는:\n  python3 -m pip install ultralytics")
        sys.exit(1)

    model_path = Path(args.model)
    if not model_path.exists():
        print(f"경고: 모델 파일을 찾을 수 없습니다: {model_path}\n계속하려면 유효한 모델 경로를 지정하세요.")
        # 그래도 시도해봄 (ultralytics는 허용된 모델 이름일 경우 다운로드 시도)

    print(f"모델: {args.model}")
    print(f"입력: {args.source}")
    print(f"이미지 크기: {args.imgsz}, conf: {args.conf}")

    y = YOLO(args.model)

    # predict에 필요한 인자 구성
    project = str(Path(args.save_dir).parent)
    name = Path(args.save_dir).name

    print("추론 시작...")
    results = y.predict(
        source=args.source,
        imgsz=args.imgsz,
        conf=args.conf,
        device=args.device,
        save=True,
        project=project,
        name=name,
        exist_ok=args.exist_ok,
    )

    # 결과 요약 출력
    print("추론 완료. 저장된 결과 경로:")
    print(Path(project) / name)


if __name__ == "__main__":
    main()
