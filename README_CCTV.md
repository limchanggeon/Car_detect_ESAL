CCTV Multi-Stream Detector (PyQt5 PoC)

설명:
- 이 PoC는 PyQt5 기반 데스크탑 앱으로 RTSP 혹은 로컬 비디오 파일을 추가하여
  YOLOv8로 실시간 객체 탐지를 화면에 보여줍니다.

빠른 시작:
1. 가상환경 생성 및 활성화
   python3 -m venv .venv
   source .venv/bin/activate

2. 의존성 설치

   권장: 먼저 PyTorch(특히 GPU/CUDA를 사용하는 경우)는 공식 설치 가이드를 따릅니다:

```bash
# 예: CPU-only 간단 설치
python3 -m pip install --upgrade pip
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

   그 다음 저장소 의존성 설치:

```bash
python3 -m pip install -r requirements-gui.txt
```

   참고: `ultralytics` 패키지는 내부적으로 `torch`를 필요로 합니다. GPU 가속을 사용하려면 적절한 CUDA 버전의 `torch`를 미리 설치하세요.

3. 앱 실행
   python3 gui_cctv.py weights/best.pt

사용법:
- 앱에서 RTSP URL 또는 동영상 경로를 입력하고 "Add Stream"을 누릅니다.
- 각 스트림 패널에서 Start 버튼을 눌러 추론을 시작하고 Stop으로 정지합니다.

참고:
- PoC 용도로 설계되었습니다. 다중 스트림에서 모델을 여러 번 로드하기 때문에 성능/메모리 제약이 있습니다.
- 프로덕션을 위해서는 모델 서버(Triton) 또는 공유 추론 프로세스를 사용하세요.
