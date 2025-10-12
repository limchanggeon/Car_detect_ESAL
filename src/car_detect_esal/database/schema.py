"""
교통 데이터베이스 스키마 설계
Traffic Database Schema Design

컴퓨터 비전 기반 교통 데이터 수집 및 분석을 위한 데이터베이스 구조
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

class TrafficDatabaseSchema:
    """교통 데이터베이스 스키마 정의"""
    
    # 1. 차량 탐지 결과 테이블
    DETECTION_TABLE = """
    CREATE TABLE IF NOT EXISTS vehicle_detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        camera_id TEXT NOT NULL,
        camera_name TEXT,
        camera_location TEXT,
        frame_number INTEGER,
        
        -- 차량 정보
        vehicle_type TEXT NOT NULL,  -- car, bus, truck, van, motorbike, etc.
        vehicle_class INTEGER,       -- YOLO class ID
        confidence REAL,             -- 탐지 신뢰도 (0.0 ~ 1.0)
        
        -- 바운딩 박스 좌표 (정규화된 좌표)
        bbox_x REAL,                 -- 중심점 x 좌표
        bbox_y REAL,                 -- 중심점 y 좌표
        bbox_width REAL,             -- 바운딩 박스 너비
        bbox_height REAL,            -- 바운딩 박스 높이
        
        -- ROI 정보
        roi_id INTEGER,              -- ROI 식별자
        roi_name TEXT,               -- ROI 이름 (예: "교차로_A", "진입로_1")
        
        -- 추가 메타데이터
        weather_condition TEXT,      -- 날씨 조건
        lighting_condition TEXT,     -- 조명 조건 (day, night, dawn, dusk)
        
        FOREIGN KEY (roi_id) REFERENCES roi_regions (id)
    );
    """
    
    # 2. ROI(Region of Interest) 정의 테이블
    ROI_TABLE = """
    CREATE TABLE IF NOT EXISTS roi_regions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        roi_name TEXT NOT NULL,
        roi_type TEXT,               -- intersection, entrance, exit, lane
        
        -- ROI 좌표 (정규화된 좌표)
        x1 REAL NOT NULL,            -- 좌상단 x
        y1 REAL NOT NULL,            -- 좌상단 y  
        x2 REAL NOT NULL,            -- 우하단 x
        y2 REAL NOT NULL,            -- 우하단 y
        
        -- ROI 설정 정보
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        description TEXT
    );
    """
    
    # 3. ESAL 계산 결과 테이블
    ESAL_TABLE = """
    CREATE TABLE IF NOT EXISTS esal_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        camera_id TEXT NOT NULL,
        roi_id INTEGER,
        
        -- 시간 구간 정보
        analysis_period TEXT,        -- hourly, daily, weekly, monthly
        period_start DATETIME,
        period_end DATETIME,
        
        -- 차량별 집계
        car_count INTEGER DEFAULT 0,
        bus_count INTEGER DEFAULT 0,
        truck_count INTEGER DEFAULT 0,
        van_count INTEGER DEFAULT 0,
        motorbike_count INTEGER DEFAULT 0,
        other_count INTEGER DEFAULT 0,
        
        -- ESAL 계산 결과
        total_esal REAL,             -- 총 ESAL 값
        car_esal REAL,               -- 승용차 ESAL
        bus_esal REAL,               -- 버스 ESAL
        truck_esal REAL,             -- 트럭 ESAL
        van_esal REAL,               -- 밴 ESAL
        
        -- 도로 상태 예측
        pavement_damage_level INTEGER, -- 1-5 단계
        maintenance_urgency TEXT,      -- low, medium, high, critical
        estimated_maintenance_date DATE,
        
        FOREIGN KEY (roi_id) REFERENCES roi_regions (id)
    );
    """
    
    # 4. 카메라/스트림 정보 테이블
    CAMERA_TABLE = """
    CREATE TABLE IF NOT EXISTS camera_streams (
        id TEXT PRIMARY KEY,         -- 카메라 고유 ID
        name TEXT NOT NULL,
        location TEXT,
        
        -- 스트림 정보
        stream_url TEXT,
        stream_type TEXT,            -- rtsp, http, file
        resolution_width INTEGER,
        resolution_height INTEGER,
        fps REAL,
        
        -- 지리적 위치
        latitude REAL,
        longitude REAL,
        road_type TEXT,              -- highway, national_road, local_road
        road_name TEXT,
        
        -- 운영 정보
        is_active BOOLEAN DEFAULT 1,
        installation_date DATE,
        last_maintenance DATE,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # 5. 유지보수 일정 테이블
    MAINTENANCE_TABLE = """
    CREATE TABLE IF NOT EXISTS maintenance_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT,
        roi_id INTEGER,
        road_section TEXT,           -- 도로 구간
        
        -- 유지보수 정보
        maintenance_type TEXT,       -- preventive, surface_treatment, rehabilitation, reconstruction
        priority_level INTEGER,     -- 1(낮음) ~ 5(높음)
        estimated_cost REAL,
        
        -- 일정 정보
        scheduled_date DATE,
        completion_date DATE NULL,
        status TEXT DEFAULT 'scheduled', -- scheduled, in_progress, completed, cancelled
        
        -- 근거 데이터
        triggering_esal_value REAL,  -- 유지보수를 촉발한 ESAL 값
        analysis_period TEXT,
        notes TEXT,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (camera_id) REFERENCES camera_streams (id),
        FOREIGN KEY (roi_id) REFERENCES roi_regions (id)
    );
    """
    
    # 6. 교통 패턴 분석 테이블
    TRAFFIC_PATTERN_TABLE = """
    CREATE TABLE IF NOT EXISTS traffic_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        roi_id INTEGER,
        
        -- 분석 기간
        analysis_date DATE,
        hour_of_day INTEGER,         -- 0-23
        day_of_week INTEGER,         -- 1(월) ~ 7(일)
        
        -- 교통량 통계
        total_vehicles INTEGER,
        avg_vehicles_per_hour REAL,
        peak_hour INTEGER,           -- 피크 시간대
        peak_volume INTEGER,         -- 피크 시간대 차량 수
        
        -- 차종별 비율
        car_ratio REAL,              -- 승용차 비율 (0.0 ~ 1.0)
        commercial_ratio REAL,       -- 상용차 비율
        heavy_vehicle_ratio REAL,    -- 대형차 비율
        
        -- 속도 정보 (향후 확장)
        avg_speed REAL NULL,
        speed_variance REAL NULL,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (camera_id) REFERENCES camera_streams (id),
        FOREIGN KEY (roi_id) REFERENCES roi_regions (id)
    );
    """
    
    # 7. 시스템 설정 및 메타데이터 테이블
    SYSTEM_CONFIG_TABLE = """
    CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_key TEXT UNIQUE NOT NULL,
        config_value TEXT,
        config_type TEXT,            -- string, integer, float, boolean, json
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # 인덱스 생성 쿼리들
    INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON vehicle_detections(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_detections_camera ON vehicle_detections(camera_id);",
        "CREATE INDEX IF NOT EXISTS idx_detections_vehicle_type ON vehicle_detections(vehicle_type);",
        "CREATE INDEX IF NOT EXISTS idx_esal_camera_period ON esal_analysis(camera_id, analysis_period);",
        "CREATE INDEX IF NOT EXISTS idx_patterns_camera_date ON traffic_patterns(camera_id, analysis_date);",
        "CREATE INDEX IF NOT EXISTS idx_maintenance_status ON maintenance_schedule(status);",
    ]
    
    @classmethod
    def get_all_tables(cls) -> List[str]:
        """모든 테이블 생성 쿼리 반환"""
        return [
            cls.CAMERA_TABLE,
            cls.ROI_TABLE,
            cls.DETECTION_TABLE,
            cls.ESAL_TABLE,
            cls.TRAFFIC_PATTERN_TABLE,
            cls.MAINTENANCE_TABLE,
            cls.SYSTEM_CONFIG_TABLE
        ]
    
    @classmethod
    def get_all_indexes(cls) -> List[str]:
        """모든 인덱스 생성 쿼리 반환"""
        return cls.INDEXES

# ESAL 계산 기준값 (차종별)
ESAL_VALUES = {
    'car': 1,
    'motorbike': 1,
    'van': 150,
    'bus': 10430,
    'truck': 25160,
    'work_van': 7950,
    'caravan': 7950,
    'construction_vehicle': 24820,
    'trailer': 24820,
}

# 유지보수 기준 ESAL 값
MAINTENANCE_THRESHOLDS = {
    'preventive': 500000,          # 예방적 유지보수
    'surface_treatment': 700000,   # 표면 처리
    'rehabilitation': 850000,      # 중간 보수
    'reconstruction': 1000000      # 전면 재건설
}

if __name__ == "__main__":
    print("교통 데이터베이스 스키마 설계 완료")
    print(f"총 {len(TrafficDatabaseSchema.get_all_tables())}개 테이블")
    print(f"총 {len(TrafficDatabaseSchema.get_all_indexes())}개 인덱스")