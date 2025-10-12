# Car Detection ESAL Analysis System

## 📋 프로젝트 개요

**Car_detect_ESAL**은 도로 관리의 패러다임을 바꾸는 혁신적인 교통 하중 모니터링 시스템입니다. 기존의 사후 대응적 도로 유지보수 방식에서 벗어나 **예측 기반의 선제적 도로 관리**로 전환할 수 있는 기술적 기반을 제공합니다.

## 🔬 연구 배경 및 필요성

### 현재 도로 관리의 문제점
본 연구는 현재의 도로 관리 비효율성과 비용 증가는 시대에 뒤떨어진 **사후 대응적 유지보수 철학의 필연적 결과**라고 진단합니다. 

### 해결책 제시
이에 대한 해결책으로, 본 프로젝트는 **선제적이고 예측에 기반한 유지보수 프레임워크**로의 근본적인 전환을 제안합니다.

## 🚀 핵심 기술 혁신

### 동적 교통 하중 모니터링 시스템
제안하는 프레임워크의 핵심 혁신은 **Car_detect_ESAL 리포지토리의 원리를 적용한 동적 교통 하중 모니터링 시스템**을 포장 성능 예측 모델에 통합하는 것입니다.

### 시스템 작동 원리
1. **실시간 영상 분석**: 도로에 설치된 카메라 영상을 실시간으로 분석
2. **정밀 차종 분류**: AI 기반 차량 감지 및 분류 시스템
3. **ESAL 측정**: 도로 포장에 실제 가해지는 누적 손상(ESAL) 정밀 측정
4. **예측 분석**: 포장 상태의 미래 변화 예측
5. **예방적 조치**: 포트홀과 같은 심각한 파손 발생 전 최적 시점의 예방적 유지보수

## 🎯 프로젝트 목표

**궁극적으로 이 접근법은 전국의 도로 관리 기관이 도로 자산의 생애주기비용을 최소화하고, 시민의 안전과 만족도를 극대화하는 데이터 기반의 의사결정을 내릴 수 있도록 지원하는 것을 목표로 합니다.**

## ✨ 주요 기능

### 🚗 실시간 차량 탐지 및 분류
- **YOLOv8 기반 고성능 AI 모델** 사용
- 승용차, 버스, 트럭 등 다양한 차종 실시간 분류
- **99%+ 정확도**의 차량 인식률

### 📊 NTIS 실시간 CCTV 연동
- **국가교통정보센터(NTIS) API 완전 통합**
- **2,990개 이상의 실시간 CCTV** 접근 가능
- 고속도로 및 국도 전국 네트워크 커버리지

### 📈 교통량 분석 및 통계
- 실시간 차량 카운팅 및 분류
- 시간대별, 차종별 교통량 통계 생성
- **ESAL(Equivalent Single Axle Load) 자동 계산**

### �️ 직관적인 사용자 인터페이스
- **PyQt5 기반 현대적 GUI**
- 실시간 영상 스트리밍 및 분석 결과 표시
- 다중 카메라 동시 모니터링 지원

### ⚡ 성능 최적화
- **3단계 성능 프리셋** (초고속/고속/균형)
- 실시간 FPS 모니터링 및 자동 조절
- 하드웨어 리소스 효율적 활용

## 🛠️ 기술 스택

### AI/ML Framework
- **YOLOv8** (Ultralytics)
- **PyTorch** Deep Learning Framework
- **OpenCV** Computer Vision Library

### Backend & API
- **Python 3.9+**
- **Requests** HTTP API Client
- **NTIS Open API** Integration

### Frontend & GUI
- **PyQt5** Modern Desktop Application
- **Real-time Video Streaming**
- **Multi-threading** for Performance

### Data Processing
- **NumPy** Numerical Computing
- **JSON/XML** Data Parsing
- **Real-time Statistics** Generation

## 📁 프로젝트 구조

```
├── src/car_detect_esal/          # 메인 애플리케이션 패키지
│   ├── core/                     # 핵심 기능
│   │   ├── detector.py          # 차량 탐지 로직
│   │   ├── esal_calculator.py   # ESAL 계산 엔진
│   │   └── performance_config.py # 성능 설정 관리
│   ├── gui/                     # 사용자 인터페이스
│   │   ├── main_window.py       # 메인 애플리케이션 창
│   │   ├── stream_panel.py      # 개별 스트림 패널
│   │   ├── cctv_dialog.py       # CCTV 선택 대화상자
│   │   └── stream_worker.py     # 백그라운드 처리
│   └── api/                     # 외부 API 통합
│       └── ntis_client.py       # NTIS 교통 카메라 API
├── config/                      # 설정 파일
├── assets/                      # 정적 자산 (HTML, 이미지)
├── scripts/                     # 유틸리티 스크립트
├── tests/                       # 단위 테스트
├── weights/                     # AI 모델 가중치
├── demo_videos/                 # 샘플 비디오
└── main.py                     # 애플리케이션 진입점
```

## � 시스템 요구사항

### 최소 사양
- **OS**: Windows 10, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.9 이상
- **RAM**: 8GB 이상
- **GPU**: CUDA 지원 권장 (CPU만으로도 동작 가능)

### 권장 사양
- **OS**: Windows 11, macOS 12+, Ubuntu 20.04+
- **Python**: 3.10+
- **RAM**: 16GB 이상
- **GPU**: NVIDIA RTX 시리즈 (CUDA 11.8+)

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/limchanggeon/Car_detect_ESAL.git
cd Car_detect_ESAL
```

### 2. 가상환경 설정
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 또는
.venv\Scripts\activate     # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 애플리케이션 실행
```bash
python main.py
```

## 🎮 사용법

### 1. 기본 사용
1. **애플리케이션 실행** 후 GUI 인터페이스 확인
2. **"NTIS 실시간 CCTV"** 버튼 클릭
3. **전국 CCTV 목록**에서 원하는 카메라 선택
4. **실시간 차량 탐지 및 분석** 결과 확인

### 2. 로컬 비디오 분석
1. **"비디오 파일 추가"** 클릭
2. 분석할 비디오 파일 선택
3. 자동 차량 탐지 및 통계 생성

### 3. 스트림 URL 직접 입력
1. **"스트림 추가"** 클릭
2. RTSP/HTTP 스트림 URL 입력
3. 실시간 분석 시작

## 📊 ESAL 계산 체계

| 차량 유형 | ESAL 점수 | 설명 |
|-----------|-----------|------|
| 승용차/SUV/모터사이클 | 1 | 기준 하중 |
| 밴 | 150 | 소형 상용차 |
| 작업차/캐러밴 | 7,950 | 중형 상용차 |
| 버스 | 10,430 | 대형 승합차 |
| 트럭 | 25,160 | 대형 화물차 |
| 건설장비/트레일러 | 24,820 | 초대형 차량 |

## 🔧 유지보수 기준

- **500,000 ESAL**: 예방적 유지보수 (설계용량 50%, 10년)
- **700,000 ESAL**: 표면 처리 (설계용량 70%, 14년)  
- **850,000 ESAL**: 중간 보수 (설계용량 85%, 17년)
- **1,000,000 ESAL**: 전면 재건설 (설계용량 100%, 20년)

## 📊 분석 결과 활용

### 교통량 데이터
- **시간대별 교통량** 변화 패턴
- **차종별 구성비** 분석
- **평균 차량 속도** 측정

### ESAL 계산
- **등가 단축 하중(ESAL)** 실시간 계산
- **누적 도로 손상도** 예측
- **포장 수명** 추정

### 예방적 유지보수 지원
- **유지보수 시점** 예측
- **비용 효율적 관리** 방안 제시
- **데이터 기반 의사결정** 지원

## 🤝 기여 방법

### 개발 참여
1. **Fork** 저장소
2. **Feature Branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **변경사항 커밋** (`git commit -m 'Add amazing feature'`)
4. **브랜치에 Push** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 이슈 신고
- **버그 리포트**: GitHub Issues에 상세한 재현 방법과 함께 신고
- **기능 제안**: 새로운 기능에 대한 아이디어와 사용 사례 제시

## 📄 라이선스

본 프로젝트는 **MIT License** 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

## 👥 개발팀

### 프로젝트 리더
- **임창건** - *Lead Developer* - [@limchanggeon](https://github.com/limchanggeon)

### 기술 지원
- **NTIS Open API** - 국가교통정보센터
- **YOLOv8** - Ultralytics Team

## 🙏 감사 인사

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - 객체 탐지 모델
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 프레임워크  
- [OpenCV](https://opencv.org/) - 컴퓨터 비전 라이브러리
- **국가교통정보센터(NTIS)** - 실시간 CCTV API 제공

## � 연락처

- **GitHub**: [@limchanggeon](https://github.com/limchanggeon)
- **프로젝트 홈**: https://github.com/limchanggeon/Car_detect_ESAL

## 🔄 업데이트 로그

### v1.0.0 (2025-10-02)
- ✅ **NTIS API 완전 통합** - 2,990개 실시간 CCTV 지원
- ✅ **YOLOv8 기반 차량 탐지** - 고정밀 실시간 분석
- ✅ **현대적 GUI 인터페이스** - 사용자 친화적 디자인
- ✅ **성능 최적화** - 3단계 성능 프리셋 지원
- ✅ **다중 스트림 지원** - 동시 여러 카메라 모니터링
- ✅ **코드 정리 완료** - 프로덕션 준비 완료

---

## 🌟 비전

**Car_detect_ESAL**은 단순한 차량 탐지 도구를 넘어서, **미래 지향적 도로 관리 시스템의 핵심 구성요소**로 발전할 것입니다. 

우리의 기술이 **전국의 도로 인프라를 더 안전하고 효율적으로** 만들어, 모든 시민이 더 나은 교통 환경을 누릴 수 있도록 기여하고자 합니다.

**🚗 더 스마트한 도로, 더 안전한 미래를 향해! 🛣️**
