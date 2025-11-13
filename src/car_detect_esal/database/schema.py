"""
교통 데이터베이스 스키마 설계
Traffic Database Schema Design

컴퓨터 비전 기반 교통 데이터 수집 및 분석을 위한 데이터베이스 구조
"""

import pymysql
from datetime import datetime
from typing import Dict, List, Optional
import json

class TrafficDatabaseSchema:
    """교통 데이터베이스 스키마 정의"""
    
    # 1. 차량 탐지 결과 테이블
    DETECTION_TABLE = """
    CREATE TABLE IF NOT EXISTS vehicle_detections (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        camera_id VARCHAR(100) NOT NULL,
        camera_name VARCHAR(255),
        camera_location VARCHAR(255),
        frame_number INT,
        
        -- 차량 정보
        vehicle_type VARCHAR(50) NOT NULL,  -- car, bus, truck, van, motorbike, etc.
        vehicle_class INT,       -- YOLO class ID
        confidence FLOAT,             -- 탐지 신뢰도 (0.0 ~ 1.0)
        
        -- 바운딩 박스 좌표 (정규화된 좌표)
        bbox_x FLOAT,                 -- 중심점 x 좌표
        bbox_y FLOAT,                 -- 중심점 y 좌표
        bbox_width FLOAT,             -- 바운딩 박스 너비
        bbox_height FLOAT,            -- 바운딩 박스 높이
        
        -- ROI 정보
        roi_id INT,              -- ROI 식별자
        roi_name VARCHAR(100),               -- ROI 이름 (예: "교차로_A", "진입로_1")
        
        -- 추가 메타데이터
        weather_condition VARCHAR(50),      -- 날씨 조건
        lighting_condition VARCHAR(50),     -- 조명 조건 (day, night, dawn, dusk)
        
        INDEX idx_timestamp (timestamp),
        INDEX idx_camera (camera_id),
        INDEX idx_vehicle_type (vehicle_type),
        FOREIGN KEY (roi_id) REFERENCES roi_regions (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 2. ROI(Region of Interest) 정의 테이블
    ROI_TABLE = """
    CREATE TABLE IF NOT EXISTS roi_regions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        camera_id VARCHAR(100) NOT NULL,
        roi_name VARCHAR(100) NOT NULL,
        roi_type VARCHAR(50),               -- intersection, entrance, exit, lane
        
        -- ROI 좌표 (정규화된 좌표)
        x1 FLOAT NOT NULL,            -- 좌상단 x
        y1 FLOAT NOT NULL,            -- 좌상단 y  
        x2 FLOAT NOT NULL,            -- 우하단 x
        y2 FLOAT NOT NULL,            -- 우하단 y
        
        -- ROI 설정 정보
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        description TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 3. ESAL 계산 결과 테이블
    ESAL_TABLE = """
    CREATE TABLE IF NOT EXISTS esal_analysis (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        camera_id VARCHAR(100) NOT NULL,
        roi_id INT,
        
        -- 시간 구간 정보
        analysis_period VARCHAR(50),        -- hourly, daily, weekly, monthly
        period_start DATETIME,
        period_end DATETIME,
        
        -- 차량별 집계
        car_count INT DEFAULT 0,
        bus_count INT DEFAULT 0,
        truck_count INT DEFAULT 0,
        van_count INT DEFAULT 0,
        motorbike_count INT DEFAULT 0,
        other_count INT DEFAULT 0,
        
        -- ESAL 계산 결과
        total_esal FLOAT,             -- 총 ESAL 값
        car_esal FLOAT,               -- 승용차 ESAL
        bus_esal FLOAT,               -- 버스 ESAL
        truck_esal FLOAT,             -- 트럭 ESAL
        van_esal FLOAT,               -- 밴 ESAL
        
        -- 도로 상태 예측
        pavement_damage_level INT, -- 1-5 단계
        maintenance_urgency VARCHAR(50),      -- low, medium, high, critical
        estimated_maintenance_date DATE,
        
        INDEX idx_camera_period (camera_id, analysis_period),
        FOREIGN KEY (roi_id) REFERENCES roi_regions (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 4. 카메라/스트림 정보 테이블
    CAMERA_TABLE = """
    CREATE TABLE IF NOT EXISTS camera_streams (
        id VARCHAR(100) PRIMARY KEY,         -- 카메라 고유 ID
        name VARCHAR(255) NOT NULL,
        location VARCHAR(255),
        
        -- 스트림 정보
        stream_url TEXT,
        stream_type VARCHAR(50),            -- rtsp, http, file
        resolution_width INT,
        resolution_height INT,
        fps FLOAT,
        
        -- 지리적 위치
        latitude FLOAT,
        longitude FLOAT,
        road_type VARCHAR(100),              -- highway, national_road, local_road
        road_name VARCHAR(255),
        
        -- 운영 정보
        is_active BOOLEAN DEFAULT 1,
        installation_date DATE,
        last_maintenance DATE,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 5. 유지보수 일정 테이블
    MAINTENANCE_TABLE = """
    CREATE TABLE IF NOT EXISTS maintenance_schedule (
        id INT AUTO_INCREMENT PRIMARY KEY,
        camera_id VARCHAR(100),
        roi_id INT,
        road_section VARCHAR(255),           -- 도로 구간
        
        -- 유지보수 정보
        maintenance_type VARCHAR(100),       -- preventive, surface_treatment, rehabilitation, reconstruction
        priority_level INT,     -- 1(낮음) ~ 5(높음)
        estimated_cost FLOAT,
        
        -- 일정 정보
        scheduled_date DATE,
        completion_date DATE NULL,
        status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, in_progress, completed, cancelled
        
        -- 근거 데이터
        triggering_esal_value FLOAT,  -- 유지보수를 촉발한 ESAL 값
        analysis_period VARCHAR(50),
        notes TEXT,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_status (status),
        FOREIGN KEY (camera_id) REFERENCES camera_streams (id),
        FOREIGN KEY (roi_id) REFERENCES roi_regions (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 6. 교통 패턴 분석 테이블
    TRAFFIC_PATTERN_TABLE = """
    CREATE TABLE IF NOT EXISTS traffic_patterns (
        id INT AUTO_INCREMENT PRIMARY KEY,
        camera_id VARCHAR(100) NOT NULL,
        roi_id INT,
        
        -- 분석 기간
        analysis_date DATE,
        hour_of_day INT,         -- 0-23
        day_of_week INT,         -- 1(월) ~ 7(일)
        
        -- 교통량 통계
        total_vehicles INT,
        avg_vehicles_per_hour FLOAT,
        peak_hour INT,           -- 피크 시간대
        peak_volume INT,         -- 피크 시간대 차량 수
        
        -- 차종별 비율
        car_ratio FLOAT,              -- 승용차 비율 (0.0 ~ 1.0)
        commercial_ratio FLOAT,       -- 상용차 비율
        heavy_vehicle_ratio FLOAT,    -- 대형차 비율
        
        -- 속도 정보 (향후 확장)
        avg_speed FLOAT NULL,
        speed_variance FLOAT NULL,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        INDEX idx_camera_date (camera_id, analysis_date),
        FOREIGN KEY (camera_id) REFERENCES camera_streams (id),
        FOREIGN KEY (roi_id) REFERENCES roi_regions (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 7. 시스템 설정 및 메타데이터 테이블
    SYSTEM_CONFIG_TABLE = """
    CREATE TABLE IF NOT EXISTS system_config (
        id INT AUTO_INCREMENT PRIMARY KEY,
        config_key VARCHAR(100) UNIQUE NOT NULL,
        config_value TEXT,
        config_type VARCHAR(50),            -- string, integer, float, boolean, json
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # 인덱스 생성 쿼리들 (이미 테이블에 포함됨)
    INDEXES = [
        # 이미 각 테이블의 CREATE 문에 INDEX가 포함되어 있음
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