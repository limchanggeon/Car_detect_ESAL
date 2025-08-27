# Car_detect_ESAL

간단한 차량(및 객체) 탐지 PoC 저장소입니다. 이 폴더는 학습된 가중치(`weights/`)와 함께 제공되는 추론 스크립트 및 간단한 GUI를 포함합니다.

## 주요 목적
- 학습된 모델을 이용한 비디오/이미지 추론 데모 제공
- 간단한 GUI로 카메라 스트림을 보여주고 탐지 결과를 시각화

## 파일 구조(요약)
- `cctv_api.py` - CCTV 연동용 간단한 API/헬퍼
- `gui_cctv.py` - 간단한 GUI 실행 파일 (예: PyQt 또는 Tkinter 기반)
- `infer.py` - 단일 이미지 추론 스크립트
- `infer_videos.py` - 비디오 또는 디렉터리의 비디오들에 대한 배치 추론
- `map_picker.html` - 위치 선택/시각화를 위한 간단한 HTML
- `weights/` - 학습된 모델 가중치 (`best.pt`, `last.pt`) — 큰 바이너리는 `.gitignore`로 제외됨

## 빠른 시작
1. Python 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate
```

2. 필요한 패키지 설치 (예시)

```bash
pip install -r requirements.txt  # 프로젝트에 requirements.txt가 없으면 필요한 패키지(torch, opencv-python 등) 설치
```

3. 이미지 추론 실행 예시

```bash
python infer.py --source demo_images/ --weights weights/best.pt
```

4. 비디오 추론 (간단 스크립트 활용)

```bash
bash run_inference.sh demo_videos/ weights/best.pt
```

## 기여
- 이 저장소는 PoC 목적입니다. 이슈나 풀 리퀘스트는 언제든 환영합니다.

## 라이선스
- 이 프로젝트는 `LICENSE` 파일의 MIT 라이선스를 따릅니다.

## 참고
- 루트에 있는 더 상세한 README(학습 데이터/학습 결과)를 참조하세요.
