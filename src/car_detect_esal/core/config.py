"""
Configuration module for Car Detection ESAL system
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Any

class Config:
    """Central configuration class for the ESAL detection system"""
    
    # 프로젝트 루트 디렉토리
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    
    # 모델 관련 설정
    DEFAULT_MODEL_PATH = PROJECT_ROOT / "weights" / "best.pt"
    DEFAULT_IMGSZ = 640
    DEFAULT_CONF = 0.25
    
    # GUI 설정
    DEFAULT_WINDOW_SIZE = (1200, 800)
    DEFAULT_VIDEO_SIZE = (640, 360)
    
    # NTIS API 설정
    NTIS_API_KEY = os.getenv("NTIS_API_KEY")
    
    # 한국어 클래스명 매핑
    KOREAN_LABEL_MAP: Dict[str, str] = {
        'car': '자동차',
        'cars': '자동차', 
        'truck': '트럭',
        'bus': '버스',
        'motorbike': '오토바이',
        'motorcycle': '오토바이',
        'bike': '오토바이',
        'bicycle': '자전거',
        'person': '사람',
        'people': '사람',
        'van': '밴',
        'work_van': '화물밴',
        'suv': 'SUV',
        'construction_vehicle': '건설차량',
        'caravan': '카라반',
        'trailer': '트레일러',
    }
    
    # 차량별 ESAL 점수 매핑
    SCORE_MAP: Dict[str, int] = {
        'bicycle': 0,
        'person': 0,
        'people': 0,
        'car': 1,
        'cars': 1,
        'suv': 1,
        'motorbike': 1,
        'motorcycle': 1,
        'bike': 1,
        'van': 150,
        'work_van': 7950,
        'caravan': 7950,
        'bus': 10430,
        'construction_vehicle': 24820,
        'trailer': 24820,
        'truck': 25160,
    }
    
    # 보수 기준 임계값 (누적 ESAL 기준)
    MAINTENANCE_THRESHOLDS: List[Tuple[int, str]] = [
        (1_000_000, '전면재포장 (설계 대비 100%, 20년 후)'),
        (850_000, '중간보수 (설계 대비 85%, 17년 후)'),
        (700_000, '표층보수 (설계 대비 70%, 14년 후)'),
        (500_000, '예방보수 (설계 대비 50%, 10년 후)'),
    ]
    
    # 상세 보수 일정
    MAINTENANCE_SCHEDULE: List[Dict[str, Any]] = [
        {
            'stage': '예방보수',
            'cumulative_esal': 500_000,
            'design_pct': 50,
            'timing_years': 10,
            'note': '예방적 유지보수 (균열 실링, 표면 처리)'
        },
        {
            'stage': '표층보수',
            'cumulative_esal': 700_000,
            'design_pct': 70,
            'timing_years': 14,
            'note': '표층 보수 (5cm 절삭 후 재포장)'
        },
        {
            'stage': '중간보수',
            'cumulative_esal': 850_000,
            'design_pct': 85,
            'timing_years': 17,
            'note': '중간층 보수 (10cm 절삭 후 재포장)'
        },
        {
            'stage': '전면재포장',
            'cumulative_esal': 1_000_000,
            'design_pct': 100,
            'timing_years': 20,
            'note': '전면 재포장 (20cm 기층까지 재포장)'
        },
    ]
    
    # 장기 누적 관리 임계값
    LONG_TERM: Dict[str, int] = {
        'monthly': 123_000,
        'yearly': 1_496_500,
    }