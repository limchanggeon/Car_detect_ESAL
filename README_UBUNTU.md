# 🚗 Car Detection ESAL - Ubuntu Installation Guide

## Ubuntu에서 설치하기

### 방법 1: 자동 설치 스크립트 사용 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/limchanggeon/Car_detect_ESAL.git
cd Car_detect_ESAL

# 2. 설치 스크립트 실행
chmod +x install_ubuntu.sh
./install_ubuntu.sh

# 3. 애플리케이션 실행
source .venv/bin/activate
python main.py
```

### 방법 2: 수동 설치

#### 1. 시스템 패키지 설치
```bash
# 패키지 목록 업데이트
sudo apt update

# Python 개발 패키지 설치
sudo apt install -y python3-dev python3-pip python3-venv

# PyQt5 시스템 패키지 설치
sudo apt install -y python3-pyqt5 python3-pyqt5-dev python3-pyqt5.qtwebengine

# OpenCV 시스템 의존성 설치
sudo apt install -y libopencv-dev python3-opencv

# Qt 추가 의존성 설치
sudo apt install -y \
    qtbase5-dev \
    qtchooser \
    qt5-qmake \
    qtbase5-dev-tools \
    libqt5webkit5-dev \
    libxcb-xinerama0
```

#### 2. Python 가상환경 설정
```bash
# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# pip 업그레이드
pip install --upgrade pip
```

#### 3. Python 의존성 설치
```bash
# Ubuntu용 requirements 파일 사용
pip install -r requirements-ubuntu.txt
```

## 문제 해결

### PyQt5 설치가 멈추는 경우
- 현재 pip 프로세스를 `Ctrl+C`로 중단
- 시스템 패키지 매니저로 PyQt5 설치: `sudo apt install python3-pyqt5`
- 그 다음 나머지 의존성만 pip로 설치

### GUI가 실행되지 않는 경우
```bash
# X11 플랫폼 강제 사용
export QT_QPA_PLATFORM=xcb

# 또는 Wayland 사용
export QT_QPA_PLATFORM=wayland
```

### 가상환경 활성화
```bash
# 가상환경 활성화 (매번 실행 전에 필요)
source .venv/bin/activate

# 비활성화
deactivate
```

## 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 애플리케이션 실행
python main.py
```

## 시스템 요구사항

- Ubuntu 18.04 이상
- Python 3.6 이상
- 최소 4GB RAM
- GPU 사용 시 CUDA 지원 GPU 권장

## 참고사항

- Ubuntu에서는 시스템 패키지 매니저를 통해 PyQt5를 설치하는 것이 더 안정적입니다
- pip로 PyQt5를 설치할 때 컴파일 시간이 오래 걸릴 수 있습니다
- X11 디스플레이 서버가 필요합니다 (대부분의 Ubuntu 데스크탑에서 기본 제공)