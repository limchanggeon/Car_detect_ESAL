"""
교통 데이터베이스 관리자
Traffic Database Manager

실시간 차량 탐지 결과를 데이터베이스에 저장하고 분석하는 클래스
"""

import sqlite3
import json
import logging
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .schema import TrafficDatabaseSchema, ESAL_VALUES, MAINTENANCE_THRESHOLDS

class TrafficDatabaseManager:
    """교통 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "traffic_data.db"):
        """
        데이터베이스 관리자 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
        # 데이터베이스 디렉토리 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 데이터베이스 초기화
        self._initialize_database()
        
    def _initialize_database(self):
        """데이터베이스 테이블 및 인덱스 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 모든 테이블 생성
                for table_sql in TrafficDatabaseSchema.get_all_tables():
                    conn.execute(table_sql)
                
                # 모든 인덱스 생성
                for index_sql in TrafficDatabaseSchema.get_all_indexes():
                    conn.execute(index_sql)
                
                # 기본 설정값 삽입
                self._insert_default_config(conn)
                
                conn.commit()
                self.logger.info(f"데이터베이스 초기화 완료: {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    def _insert_default_config(self, conn: sqlite3.Connection):
        """기본 시스템 설정값 삽입"""
        default_configs = [
            ('detection_confidence_threshold', '0.5', 'float', '차량 탐지 최소 신뢰도'),
            ('esal_calculation_period', 'daily', 'string', 'ESAL 계산 주기'),
            ('maintenance_check_interval', '7', 'integer', '유지보수 점검 간격(일)'),
            ('database_cleanup_days', '365', 'integer', '데이터 보관 기간(일)'),
        ]
        
        for key, value, type_, desc in default_configs:
            conn.execute("""
                INSERT OR IGNORE INTO system_config 
                (config_key, config_value, config_type, description)
                VALUES (?, ?, ?, ?)
            """, (key, value, type_, desc))
    
    def add_camera_stream(self, camera_id: str, name: str, location: str, 
                         stream_url: str = None, **kwargs) -> bool:
        """
        카메라 스트림 정보 추가
        
        Args:
            camera_id: 카메라 고유 ID
            name: 카메라 이름
            location: 설치 위치
            stream_url: 스트림 URL
            **kwargs: 추가 정보 (latitude, longitude, road_type 등)
        
        Returns:
            bool: 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO camera_streams 
                    (id, name, location, stream_url, latitude, longitude, 
                     road_type, road_name, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    camera_id, name, location, stream_url,
                    kwargs.get('latitude'), kwargs.get('longitude'),
                    kwargs.get('road_type'), kwargs.get('road_name'),
                    kwargs.get('is_active', True), datetime.now()
                ))
                conn.commit()
                self.logger.info(f"카메라 스트림 추가: {camera_id} - {name}")
                return True
                
        except Exception as e:
            self.logger.error(f"카메라 스트림 추가 실패: {e}")
            return False
    
    def add_roi_region(self, camera_id: str, roi_name: str, x1: float, y1: float,
                      x2: float, y2: float, roi_type: str = None) -> Optional[int]:
        """
        ROI 영역 추가
        
        Args:
            camera_id: 카메라 ID
            roi_name: ROI 이름
            x1, y1, x2, y2: ROI 좌표 (정규화된 좌표)
            roi_type: ROI 타입
        
        Returns:
            Optional[int]: ROI ID (실패시 None)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO roi_regions 
                    (camera_id, roi_name, roi_type, x1, y1, x2, y2)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (camera_id, roi_name, roi_type, x1, y1, x2, y2))
                
                roi_id = cursor.lastrowid
                conn.commit()
                self.logger.info(f"ROI 영역 추가: {roi_name} (ID: {roi_id})")
                return roi_id
                
        except Exception as e:
            self.logger.error(f"ROI 영역 추가 실패: {e}")
            return None
    
    def record_vehicle_detection(self, camera_id: str, detections: List[Dict]) -> bool:
        """
        차량 탐지 결과 기록
        
        Args:
            camera_id: 카메라 ID
            detections: 탐지 결과 리스트
                [{
                    'vehicle_type': str,
                    'confidence': float,
                    'bbox': [x, y, w, h],  # 정규화된 좌표
                    'roi_id': int (optional),
                    'frame_number': int (optional),
                }]
        
        Returns:
            bool: 성공 여부
        """
        if not detections:
            return True
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 카메라 정보 조회
                camera_info = conn.execute(
                    "SELECT name, location FROM camera_streams WHERE id = ?",
                    (camera_id,)
                ).fetchone()
                
                camera_name = camera_info[0] if camera_info else None
                camera_location = camera_info[1] if camera_info else None
                
                # 탐지 결과 일괄 삽입
                detection_data = []
                for det in detections:
                    bbox = det.get('bbox', [0, 0, 0, 0])
                    detection_data.append((
                        camera_id,
                        camera_name,
                        camera_location,
                        det.get('frame_number'),
                        det['vehicle_type'],
                        det.get('vehicle_class'),
                        det['confidence'],
                        bbox[0], bbox[1], bbox[2], bbox[3],  # x, y, w, h
                        det.get('roi_id'),
                        det.get('roi_name'),
                        det.get('weather_condition'),
                        det.get('lighting_condition')
                    ))
                
                conn.executemany("""
                    INSERT INTO vehicle_detections 
                    (camera_id, camera_name, camera_location, frame_number,
                     vehicle_type, vehicle_class, confidence,
                     bbox_x, bbox_y, bbox_width, bbox_height,
                     roi_id, roi_name, weather_condition, lighting_condition)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, detection_data)
                
                conn.commit()
                self.logger.debug(f"차량 탐지 결과 {len(detections)}건 기록 완료")
                return True
                
        except Exception as e:
            self.logger.error(f"차량 탐지 결과 기록 실패: {e}")
            return False
    
    def calculate_esal_analysis(self, camera_id: str, roi_id: Optional[int] = None,
                               period: str = 'daily', start_time: datetime = None,
                               end_time: datetime = None) -> Optional[Dict]:
        """
        ESAL 분석 계산 및 저장
        
        Args:
            camera_id: 카메라 ID
            roi_id: ROI ID (선택적)
            period: 분석 주기 ('hourly', 'daily', 'weekly', 'monthly')
            start_time: 분석 시작 시간
            end_time: 분석 종료 시간
        
        Returns:
            Optional[Dict]: ESAL 분석 결과
        """
        if not end_time:
            end_time = datetime.now()
        
        if not start_time:
            if period == 'hourly':
                start_time = end_time - timedelta(hours=1)
            elif period == 'daily':
                start_time = end_time - timedelta(days=1)
            elif period == 'weekly':
                start_time = end_time - timedelta(weeks=1)
            elif period == 'monthly':
                start_time = end_time - timedelta(days=30)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 차량별 집계 쿼리
                where_clause = "WHERE camera_id = ? AND timestamp BETWEEN ? AND ?"
                params = [camera_id, start_time, end_time]
                
                if roi_id:
                    where_clause += " AND roi_id = ?"
                    params.append(roi_id)
                
                query = f"""
                    SELECT vehicle_type, COUNT(*) as count
                    FROM vehicle_detections 
                    {where_clause}
                    GROUP BY vehicle_type
                """
                
                results = conn.execute(query, params).fetchall()
                
                # 차종별 집계
                vehicle_counts = {}
                total_esal = 0.0
                esal_by_type = {}
                
                for vehicle_type, count in results:
                    vehicle_counts[vehicle_type] = count
                    esal_value = ESAL_VALUES.get(vehicle_type, 1) * count
                    esal_by_type[vehicle_type] = esal_value
                    total_esal += esal_value
                
                # 도로 손상 수준 계산 (1-5 단계)
                damage_level = min(5, max(1, int(total_esal / 200000) + 1))
                
                # 유지보수 긴급도 결정
                if total_esal >= MAINTENANCE_THRESHOLDS['reconstruction']:
                    urgency = 'critical'
                    maintenance_type = 'reconstruction'
                elif total_esal >= MAINTENANCE_THRESHOLDS['rehabilitation']:
                    urgency = 'high'
                    maintenance_type = 'rehabilitation'
                elif total_esal >= MAINTENANCE_THRESHOLDS['surface_treatment']:
                    urgency = 'medium'
                    maintenance_type = 'surface_treatment'
                elif total_esal >= MAINTENANCE_THRESHOLDS['preventive']:
                    urgency = 'low'
                    maintenance_type = 'preventive'
                else:
                    urgency = 'low'
                    maintenance_type = 'preventive'
                
                # 예상 유지보수 날짜 계산
                if urgency == 'critical':
                    maintenance_date = end_time + timedelta(days=7)
                elif urgency == 'high':
                    maintenance_date = end_time + timedelta(days=30)
                elif urgency == 'medium':
                    maintenance_date = end_time + timedelta(days=90)
                else:
                    maintenance_date = end_time + timedelta(days=180)
                
                # ESAL 분석 결과 저장
                analysis_data = {
                    'camera_id': camera_id,
                    'roi_id': roi_id,
                    'analysis_period': period,
                    'period_start': start_time,
                    'period_end': end_time,
                    'car_count': vehicle_counts.get('car', 0),
                    'bus_count': vehicle_counts.get('bus', 0),
                    'truck_count': vehicle_counts.get('truck', 0),
                    'van_count': vehicle_counts.get('van', 0),
                    'motorbike_count': vehicle_counts.get('motorbike', 0),
                    'other_count': sum(v for k, v in vehicle_counts.items() 
                                     if k not in ['car', 'bus', 'truck', 'van', 'motorbike']),
                    'total_esal': total_esal,
                    'car_esal': esal_by_type.get('car', 0),
                    'bus_esal': esal_by_type.get('bus', 0),
                    'truck_esal': esal_by_type.get('truck', 0),
                    'van_esal': esal_by_type.get('van', 0),
                    'pavement_damage_level': damage_level,
                    'maintenance_urgency': urgency,
                    'estimated_maintenance_date': maintenance_date.date()
                }
                
                # 데이터베이스에 저장
                conn.execute("""
                    INSERT INTO esal_analysis 
                    (camera_id, roi_id, analysis_period, period_start, period_end,
                     car_count, bus_count, truck_count, van_count, motorbike_count, other_count,
                     total_esal, car_esal, bus_esal, truck_esal, van_esal,
                     pavement_damage_level, maintenance_urgency, estimated_maintenance_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_data['camera_id'], analysis_data['roi_id'],
                    analysis_data['analysis_period'], analysis_data['period_start'],
                    analysis_data['period_end'], analysis_data['car_count'],
                    analysis_data['bus_count'], analysis_data['truck_count'],
                    analysis_data['van_count'], analysis_data['motorbike_count'],
                    analysis_data['other_count'], analysis_data['total_esal'],
                    analysis_data['car_esal'], analysis_data['bus_esal'],
                    analysis_data['truck_esal'], analysis_data['van_esal'],
                    analysis_data['pavement_damage_level'], analysis_data['maintenance_urgency'],
                    analysis_data['estimated_maintenance_date']
                ))
                
                # 유지보수 일정 자동 생성 (긴급도가 높은 경우)
                if urgency in ['high', 'critical']:
                    self._schedule_maintenance(conn, camera_id, roi_id, maintenance_type,
                                             urgency, total_esal, maintenance_date.date())
                
                conn.commit()
                self.logger.info(f"ESAL 분석 완료: {camera_id}, 총 ESAL: {total_esal:.2f}")
                return analysis_data
                
        except Exception as e:
            self.logger.error(f"ESAL 분석 실패: {e}")
            return None
    
    def _schedule_maintenance(self, conn: sqlite3.Connection, camera_id: str,
                            roi_id: Optional[int], maintenance_type: str,
                            urgency: str, esal_value: float, scheduled_date):
        """유지보수 일정 자동 생성"""
        priority_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        cost_map = {
            'preventive': 100000,
            'surface_treatment': 500000,
            'rehabilitation': 2000000,
            'reconstruction': 10000000
        }
        
        conn.execute("""
            INSERT INTO maintenance_schedule 
            (camera_id, roi_id, maintenance_type, priority_level, estimated_cost,
             scheduled_date, triggering_esal_value, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            camera_id, roi_id, maintenance_type,
            priority_map.get(urgency, 2), cost_map.get(maintenance_type, 100000),
            scheduled_date, esal_value,
            f"ESAL 기준 자동 생성 ({urgency} 긴급도)"
        ))
    
    def get_traffic_statistics(self, camera_id: str, 
                              start_date: datetime = None,
                              end_date: datetime = None) -> Dict:
        """
        교통 통계 조회
        
        Args:
            camera_id: 카메라 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            Dict: 교통 통계 정보
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 기본 통계
                stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_detections,
                        COUNT(DISTINCT DATE(timestamp)) as active_days,
                        vehicle_type,
                        COUNT(*) as type_count
                    FROM vehicle_detections 
                    WHERE camera_id = ? AND timestamp BETWEEN ? AND ?
                    GROUP BY vehicle_type
                """, (camera_id, start_date, end_date)).fetchall()
                
                # ESAL 통계
                esal_stats = conn.execute("""
                    SELECT 
                        AVG(total_esal) as avg_daily_esal,
                        MAX(total_esal) as max_daily_esal,
                        SUM(total_esal) as total_period_esal,
                        maintenance_urgency,
                        COUNT(*) as urgency_count
                    FROM esal_analysis 
                    WHERE camera_id = ? AND period_start BETWEEN ? AND ?
                    GROUP BY maintenance_urgency
                """, (camera_id, start_date, end_date)).fetchall()
                
                return {
                    'camera_id': camera_id,
                    'period': {'start': start_date, 'end': end_date},
                    'vehicle_statistics': dict(stats) if stats else {},
                    'esal_statistics': dict(esal_stats) if esal_stats else {},
                    'generated_at': datetime.now()
                }
                
        except Exception as e:
            self.logger.error(f"교통 통계 조회 실패: {e}")
            return {}
    
    def export_data_to_csv(self, table_name: str, output_path: str,
                          start_date: datetime = None, end_date: datetime = None) -> bool:
        """
        데이터베이스 데이터를 CSV로 내보내기
        
        Args:
            table_name: 테이블 이름
            output_path: 출력 파일 경로
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            bool: 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 쿼리 실행
                if table_name == 'vehicle_detections' and start_date and end_date:
                    query = f"SELECT * FROM {table_name} WHERE timestamp BETWEEN ? AND ?"
                    cursor = conn.execute(query, [start_date, end_date])
                else:
                    cursor = conn.execute(f"SELECT * FROM {table_name}")
                
                # 컬럼 이름 가져오기
                column_names = [description[0] for description in cursor.description]
                
                # CSV 파일로 작성
                with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    # 헤더 작성
                    writer.writerow(column_names)
                    # 데이터 작성
                    writer.writerows(cursor.fetchall())
                
                self.logger.info(f"데이터 내보내기 완료: {output_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"데이터 내보내기 실패: {e}")
            return False
    
    def cleanup_old_data(self, retention_days: int = 365) -> int:
        """
        오래된 데이터 정리
        
        Args:
            retention_days: 데이터 보관 기간(일)
        
        Returns:
            int: 삭제된 레코드 수
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 오래된 탐지 결과 삭제
                cursor = conn.execute(
                    "DELETE FROM vehicle_detections WHERE timestamp < ?",
                    (cutoff_date,)
                )
                deleted_count += cursor.rowcount
                
                # 오래된 ESAL 분석 결과 삭제
                cursor = conn.execute(
                    "DELETE FROM esal_analysis WHERE timestamp < ?",
                    (cutoff_date,)
                )
                deleted_count += cursor.rowcount
                
                # 완료된 유지보수 일정 삭제 (1년 후)
                old_maintenance_date = datetime.now() - timedelta(days=365)
                cursor = conn.execute(
                    "DELETE FROM maintenance_schedule WHERE status = 'completed' AND completion_date < ?",
                    (old_maintenance_date,)
                )
                deleted_count += cursor.rowcount
                
                conn.commit()
                self.logger.info(f"데이터 정리 완료: {deleted_count}건 삭제")
                
        except Exception as e:
            self.logger.error(f"데이터 정리 실패: {e}")
            
        return deleted_count
    
    def get_database_status(self) -> Dict:
        """데이터베이스 상태 정보 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                tables_info = {}
                
                table_names = [
                    'camera_streams', 'roi_regions', 'vehicle_detections',
                    'esal_analysis', 'traffic_patterns', 'maintenance_schedule'
                ]
                
                for table in table_names:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    tables_info[table] = count
                
                # 파일 크기
                file_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    'database_path': str(self.db_path),
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'tables': tables_info,
                    'last_check': datetime.now()
                }
                
        except Exception as e:
            self.logger.error(f"데이터베이스 상태 조회 실패: {e}")
            return {}