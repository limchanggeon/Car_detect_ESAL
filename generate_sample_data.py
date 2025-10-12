"""
데이터베이스 시연용 샘플 데이터 생성
Sample Data Generator for Database Demo

발표용으로 실제 교통 데이터와 유사한 샘플 데이터를 생성합니다.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.car_detect_esal.database import TrafficDatabaseManager, ESAL_VALUES

class SampleDataGenerator:
    """샘플 데이터 생성기"""
    
    def __init__(self, db_path: str = "data/traffic_data.db"):
        """
        초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_manager = TrafficDatabaseManager(db_path)
        
        # 샘플 카메라 정보
        self.sample_cameras = [
            {
                'id': 'ntis_001',
                'name': '강남대로 교차로',
                'location': '서울특별시 강남구 강남대로 123',
                'stream_url': 'rtsp://example.com/stream1',
                'latitude': 37.5665,
                'longitude': 126.9780,
                'road_type': 'national_road',
                'road_name': '강남대로'
            },
            {
                'id': 'ntis_002', 
                'name': '서초IC 진입로',
                'location': '서울특별시 서초구 서초대로 456',
                'stream_url': 'rtsp://example.com/stream2',
                'latitude': 37.4833,
                'longitude': 127.0522,
                'road_type': 'highway',
                'road_name': '경부고속도로'
            },
            {
                'id': 'ntis_003',
                'name': '한강대교 남단',
                'location': '서울특별시 용산구 한강로 789',
                'stream_url': 'rtsp://example.com/stream3',
                'latitude': 37.5326,
                'longitude': 126.9860,
                'road_type': 'national_road',
                'road_name': '한강로'
            },
            {
                'id': 'demo_001',
                'name': '시연용 비디오 1',
                'location': '데모 영상',
                'stream_url': 'demo_videos/sample1.mp4',
                'road_type': 'local_road',
                'road_name': '시연용 도로'
            }
        ]
        
        # 차종별 출현 확률 (실제 교통 패턴 반영)
        self.vehicle_probabilities = {
            'car': 0.75,         # 승용차 75%
            'truck': 0.12,       # 트럭 12%
            'van': 0.08,         # 밴 8%
            'bus': 0.04,         # 버스 4%
            'motorbike': 0.01    # 오토바이 1%
        }
        
        # 시간대별 교통량 패턴 (0~23시)
        self.hourly_traffic_pattern = [
            0.3, 0.2, 0.1, 0.1, 0.2, 0.4,  # 0-5시 (새벽)
            0.7, 1.0, 1.2, 0.9, 0.8, 0.8,  # 6-11시 (출근시간대)
            0.9, 0.8, 0.7, 0.8, 0.9, 1.1,  # 12-17시 (일과시간)
            1.3, 1.2, 0.9, 0.7, 0.5, 0.4   # 18-23시 (퇴근시간대)
        ]
        
    def generate_sample_data(self, days: int = 30):
        """
        샘플 데이터 생성
        
        Args:
            days: 생성할 데이터 기간 (일)
        """
        print(f"📊 {days}일간의 샘플 데이터 생성 시작...")
        
        # 1. 카메라 정보 등록
        self._add_sample_cameras()
        
        # 2. ROI 영역 등록  
        self._add_sample_rois()
        
        # 3. 차량 탐지 데이터 생성
        self._generate_detection_data(days)
        
        # 4. ESAL 분석 데이터 생성
        self._generate_esal_analysis(days)
        
        # 5. 유지보수 일정 생성
        self._generate_maintenance_schedule()
        
        print("✅ 샘플 데이터 생성 완료!")
        self._print_database_summary()
        
    def _add_sample_cameras(self):
        """샘플 카메라 정보 추가"""
        print("📹 카메라 정보 등록 중...")
        
        for cam in self.sample_cameras:
            success = self.db_manager.add_camera_stream(
                camera_id=cam['id'],
                name=cam['name'],
                location=cam['location'],
                stream_url=cam['stream_url'],
                latitude=cam.get('latitude'),
                longitude=cam.get('longitude'),
                road_type=cam.get('road_type'),
                road_name=cam.get('road_name'),
                is_active=True
            )
            
            if success:
                print(f"  ✅ {cam['name']} 등록 완료")
            else:
                print(f"  ❌ {cam['name']} 등록 실패")
                
    def _add_sample_rois(self):
        """샘플 ROI 영역 추가"""
        print("🎯 ROI 영역 등록 중...")
        
        roi_configs = [
            {'camera_id': 'ntis_001', 'roi_name': '차선_1', 'type': 'lane', 'coords': (0.1, 0.3, 0.4, 0.7)},
            {'camera_id': 'ntis_001', 'roi_name': '차선_2', 'type': 'lane', 'coords': (0.4, 0.3, 0.7, 0.7)},
            {'camera_id': 'ntis_002', 'roi_name': '진입구간', 'type': 'entrance', 'coords': (0.0, 0.2, 1.0, 0.8)},
            {'camera_id': 'ntis_003', 'roi_name': '교차로_중앙', 'type': 'intersection', 'coords': (0.2, 0.2, 0.8, 0.8)},
            {'camera_id': 'demo_001', 'roi_name': 'ROI_1', 'type': 'lane', 'coords': (0.3, 0.4, 0.7, 0.8)},
        ]
        
        for roi in roi_configs:
            roi_id = self.db_manager.add_roi_region(
                camera_id=roi['camera_id'],
                roi_name=roi['roi_name'],
                roi_type=roi['type'],
                x1=roi['coords'][0],
                y1=roi['coords'][1],
                x2=roi['coords'][2],
                y2=roi['coords'][3]
            )
            
            if roi_id:
                print(f"  ✅ {roi['roi_name']} (ID: {roi_id}) 등록 완료")
                
    def _generate_detection_data(self, days: int):
        """차량 탐지 데이터 생성"""
        print(f"🚗 {days}일간의 차량 탐지 데이터 생성 중...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        total_detections = 0
        
        # 각 카메라별로 데이터 생성
        for camera in self.sample_cameras:
            camera_id = camera['id']
            camera_detections = 0
            
            # 하루씩 데이터 생성
            current_time = start_time
            while current_time < end_time:
                # 하루 동안의 탐지 데이터 생성
                daily_detections = self._generate_daily_detections(camera_id, current_time)
                camera_detections += len(daily_detections)
                
                # 배치로 데이터베이스에 저장 (성능 향상)
                if daily_detections:
                    self.db_manager.record_vehicle_detection(camera_id, daily_detections)
                
                current_time += timedelta(days=1)
                
            total_detections += camera_detections
            print(f"  📹 {camera['name']}: {camera_detections:,}건 탐지 데이터 생성")
            
        print(f"  ✅ 총 {total_detections:,}건의 탐지 데이터 생성 완료")
        
    def _generate_daily_detections(self, camera_id: str, date: datetime) -> list:
        """하루 동안의 탐지 데이터 생성"""
        detections = []
        
        # 카메라별 기본 교통량 (하루 기준)
        base_traffic = {
            'ntis_001': 1200,  # 강남대로 - 높은 교통량
            'ntis_002': 800,   # 서초IC - 중간 교통량  
            'ntis_003': 600,   # 한강대교 - 중간 교통량
            'demo_001': 300    # 시연용 - 낮은 교통량
        }
        
        daily_count = base_traffic.get(camera_id, 500)
        
        # 요일 패턴 (월=0, 일=6)
        weekday_multiplier = 1.0
        if date.weekday() < 5:  # 평일
            weekday_multiplier = 1.2
        else:  # 주말
            weekday_multiplier = 0.8
            
        daily_count = int(daily_count * weekday_multiplier)
        
        # 시간대별로 탐지 데이터 분산
        for hour in range(24):
            hour_multiplier = self.hourly_traffic_pattern[hour]
            hourly_count = int(daily_count * hour_multiplier / 24)
            
            # 해당 시간대의 탐지 데이터 생성
            for _ in range(hourly_count):
                # 시간 내에서 랜덤한 분/초
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                detection_time = date.replace(hour=hour, minute=minute, second=second)
                
                # 차종 선택 (확률 기반)
                vehicle_type = self._random_vehicle_type()
                
                # 랜덤한 바운딩 박스 좌표 (정규화된 좌표)
                bbox = [
                    random.uniform(0.1, 0.8),  # x (중심점)
                    random.uniform(0.2, 0.7),  # y (중심점)
                    random.uniform(0.05, 0.15), # width
                    random.uniform(0.08, 0.20)  # height
                ]
                
                detection = {
                    'vehicle_type': vehicle_type,
                    'vehicle_class': self._get_class_id(vehicle_type),
                    'confidence': random.uniform(0.6, 0.98),
                    'bbox': bbox,
                    'frame_number': random.randint(1, 10000),
                    'roi_id': random.choice([None, 1, 2, 3]),  # 일부 탐지만 ROI 내부
                    'roi_name': None,
                    'weather_condition': random.choice(['sunny', 'cloudy', 'rainy', None]),
                    'lighting_condition': self._get_lighting_condition(hour)
                }
                
                # 탐지 시간을 수동으로 설정하기 위해 timestamp 필드 추가
                detection['timestamp'] = detection_time
                
                detections.append(detection)
                
        return detections
        
    def _random_vehicle_type(self) -> str:
        """확률 기반 차종 선택"""
        rand = random.random()
        cumulative = 0.0
        
        for vehicle_type, prob in self.vehicle_probabilities.items():
            cumulative += prob
            if rand <= cumulative:
                return vehicle_type
                
        return 'car'  # 기본값
        
    def _get_class_id(self, vehicle_type: str) -> int:
        """차종별 클래스 ID 반환"""
        class_map = {
            'car': 2,
            'truck': 7, 
            'van': 5,
            'bus': 5,
            'motorbike': 3
        }
        return class_map.get(vehicle_type, 2)
        
    def _get_lighting_condition(self, hour: int) -> str:
        """시간대별 조명 조건"""
        if 6 <= hour < 18:
            return 'day'
        elif 18 <= hour < 20 or 5 <= hour < 7:
            return 'dusk' if 18 <= hour < 20 else 'dawn'
        else:
            return 'night'
            
    def _generate_esal_analysis(self, days: int):
        """ESAL 분석 데이터 생성"""
        print("⚖️ ESAL 분석 데이터 생성 중...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 각 카메라별로 일일 ESAL 분석 생성
        for camera in self.sample_cameras:
            camera_id = camera['id']
            analysis_count = 0
            
            current_time = start_time
            while current_time < end_time:
                # 해당 날짜의 ESAL 분석 실행
                result = self.db_manager.calculate_esal_analysis(
                    camera_id=camera_id,
                    period='daily',
                    start_time=current_time,
                    end_time=current_time + timedelta(days=1)
                )
                
                if result:
                    analysis_count += 1
                    
                current_time += timedelta(days=1)
                
            print(f"  📊 {camera['name']}: {analysis_count}개 ESAL 분석 완료")
            
    def _generate_maintenance_schedule(self):
        """유지보수 일정 생성"""
        print("🔧 유지보수 일정 생성 중...")
        
        # 임의의 유지보수 일정 생성 (시연용)
        maintenance_items = [
            {
                'camera_id': 'ntis_001',
                'road_section': '강남대로 123번지 ~ 456번지',
                'maintenance_type': 'surface_treatment',
                'priority_level': 3,
                'estimated_cost': 1500000,
                'scheduled_date': datetime.now() + timedelta(days=15),
                'triggering_esal_value': 750000,
                'notes': '표면 균열 및 포트홀 보수 필요'
            },
            {
                'camera_id': 'ntis_002',
                'road_section': '경부고속도로 서초IC 진입로',
                'maintenance_type': 'preventive',
                'priority_level': 2,
                'estimated_cost': 800000,
                'scheduled_date': datetime.now() + timedelta(days=45),
                'triggering_esal_value': 520000,
                'notes': '예방적 유지보수 - 정기 점검'
            },
            {
                'camera_id': 'ntis_003',
                'road_section': '한강로 교량 구간',
                'maintenance_type': 'rehabilitation',
                'priority_level': 4,
                'estimated_cost': 3500000,
                'scheduled_date': datetime.now() + timedelta(days=7),
                'triggering_esal_value': 920000,
                'notes': '교량 조인트 교체 및 포장 재시공'
            }
        ]
        
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                for item in maintenance_items:
                    conn.execute("""
                        INSERT INTO maintenance_schedule 
                        (camera_id, road_section, maintenance_type, priority_level, 
                         estimated_cost, scheduled_date, triggering_esal_value, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['camera_id'], item['road_section'], item['maintenance_type'],
                        item['priority_level'], item['estimated_cost'], item['scheduled_date'],
                        item['triggering_esal_value'], item['notes']
                    ))
                    
                conn.commit()
                print(f"  ✅ {len(maintenance_items)}개 유지보수 일정 생성 완료")
                
        except Exception as e:
            print(f"  ❌ 유지보수 일정 생성 실패: {e}")
            
    def _print_database_summary(self):
        """데이터베이스 요약 정보 출력"""
        print("\n" + "="*60)
        print("📊 데이터베이스 현황 요약")
        print("="*60)
        
        status = self.db_manager.get_database_status()
        
        if status:
            print(f"💾 데이터베이스 파일: {status['database_path']}")
            print(f"📁 파일 크기: {status['file_size_mb']} MB")
            print(f"⏰ 마지막 확인: {status['last_check']}")
            print("\n📋 테이블별 레코드 수:")
            
            for table, count in status['tables'].items():
                table_name_kr = {
                    'camera_streams': '카메라 정보',
                    'roi_regions': 'ROI 영역',
                    'vehicle_detections': '차량 탐지',
                    'esal_analysis': 'ESAL 분석',
                    'traffic_patterns': '교통 패턴',
                    'maintenance_schedule': '유지보수 일정'
                }.get(table, table)
                
                print(f"  • {table_name_kr}: {count:,}건")
                
        print("\n🎯 발표 활용 포인트:")
        print("  1. 실시간 차량 탐지 결과가 자동으로 데이터베이스에 저장")
        print("  2. ESAL 기반 도로 손상 예측 및 유지보수 일정 자동화")
        print("  3. 교통 패턴 분석을 통한 데이터 기반 의사결정 지원")
        print("  4. CSV 내보내기 기능으로 추가 분석 및 보고서 작성 가능")
        print("="*60)


def main():
    """메인 실행 함수"""
    print("🚗 교통 데이터베이스 샘플 데이터 생성기")
    print("=" * 50)
    
    # 데이터 디렉토리 생성
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 샘플 데이터 생성기 인스턴스 생성
    generator = SampleDataGenerator("data/traffic_data.db")
    
    # 30일간의 샘플 데이터 생성
    generator.generate_sample_data(days=30)
    
    print(f"\n✅ 모든 작업이 완료되었습니다!")
    print(f"📁 데이터베이스 파일: data/traffic_data.db")
    print(f"🎯 이제 GUI 애플리케이션을 실행하여 데이터베이스 기능을 확인할 수 있습니다.")


if __name__ == "__main__":
    main()