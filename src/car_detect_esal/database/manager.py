"""
교통 데이터베이스 관리자 (MariaDB/MySQL 버전)
Traffic Database Manager for MariaDB/MySQL
"""

import pymysql
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .schema import TrafficDatabaseSchema, ESAL_VALUES, MAINTENANCE_THRESHOLDS

class TrafficDatabaseManager:
    """교통 데이터베이스 관리 클래스 (MariaDB/MySQL)"""
    
    def __init__(self, config_path: str = None):
        """
        데이터베이스 관리자 초기화
        
        Args:
            config_path: 데이터베이스 설정 파일 경로 (JSON)
                        None이면 기본 설정 사용
        """
        self.logger = logging.getLogger(__name__)
        
        # 설정 로드
        if config_path is None:
            # 기본 설정 경로
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "database.json"
        
        self.config = self._load_config(config_path)
        
        # 데이터베이스 초기화
        self._initialize_database()
    
    def _load_config(self, config_path: Path) -> Dict:
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config['database']
        except Exception as e:
            self.logger.warning(f"설정 파일 로드 실패 ({config_path}): {e}")
            # 기본 설정 반환
            return {
                'host': 'localhost',
                'port': 3306,
                'user': 'traffic_user',
                'password': 'traffic_password',
                'database': 'traffic_db',
                'charset': 'utf8mb4'
            }
    
    def get_connection(self):
        """MariaDB 연결 생성"""
        return pymysql.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            charset=self.config.get('charset', 'utf8mb4'),
            autocommit=False,  # 명시적 commit 사용
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def _initialize_database(self):
        """데이터베이스 테이블 및 인덱스 생성"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 모든 테이블 생성
            for table_sql in TrafficDatabaseSchema.get_all_tables():
                cursor.execute(table_sql)
            
            # 모든 인덱스 생성 (이미 테이블에 포함됨)
            for index_sql in TrafficDatabaseSchema.get_all_indexes():
                if index_sql.strip():  # 빈 문자열 체크
                    cursor.execute(index_sql)
            
            # 기본 설정값 삽입
            self._insert_default_config(cursor)
            
            conn.commit()
            self.logger.info(f"데이터베이스 초기화 완료: {self.config['database']}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _insert_default_config(self, cursor):
        """기본 시스템 설정값 삽입"""
        default_configs = [
            ('detection_confidence_threshold', '0.5', 'float', '차량 탐지 최소 신뢰도'),
            ('esal_calculation_period', 'daily', 'string', 'ESAL 계산 주기'),
            ('maintenance_check_interval', '7', 'integer', '유지보수 점검 간격(일)'),
            ('database_cleanup_days', '365', 'integer', '데이터 보관 기간(일)'),
        ]
        
        for key, value, type_, desc in default_configs:
            cursor.execute("""
                INSERT IGNORE INTO system_config 
                (config_key, config_value, config_type, description)
                VALUES (%s, %s, %s, %s)
            """, (key, value, type_, desc))
    
    def add_camera_stream(self, camera_id: str, name: str, location: str, 
                         stream_url: str = None, **kwargs) -> bool:
        """카메라 스트림 정보 추가"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                REPLACE INTO camera_streams 
                (id, name, location, stream_url, latitude, longitude, 
                 road_type, road_name, is_active, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            if conn:
                conn.rollback()
            self.logger.error(f"카메라 스트림 추가 실패: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def add_roi_region(self, camera_id: str, roi_name: str, x1: float, y1: float,
                      x2: float, y2: float, roi_type: str = None) -> Optional[int]:
        """ROI 영역 추가"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO roi_regions 
                (camera_id, roi_name, roi_type, x1, y1, x2, y2)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (camera_id, roi_name, roi_type, x1, y1, x2, y2))
            
            roi_id = cursor.lastrowid
            conn.commit()
            
            self.logger.info(f"ROI 영역 추가: {roi_name} (ID: {roi_id})")
            return roi_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"ROI 영역 추가 실패: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def record_vehicle_detection(self, camera_id: str, detections: List[Dict]) -> bool:
        """차량 탐지 결과 기록 (배치 처리)"""
        if not detections:
            return True
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 카메라 정보 조회
            cursor.execute("""
                SELECT name, location FROM camera_streams WHERE id = %s
            """, (camera_id,))
            
            camera_info = cursor.fetchone()
            if not camera_info:
                self.logger.warning(f"카메라 정보를 찾을 수 없음: {camera_id}")
                camera_name = "Unknown"
                camera_location = "Unknown"
            else:
                camera_name = camera_info['name']
                camera_location = camera_info['location']
            
            # 배치 INSERT
            insert_data = []
            for det in detections:
                insert_data.append((
                    camera_id,
                    camera_name,
                    camera_location,
                    det.get('frame_number'),
                    det['vehicle_type'],
                    det.get('vehicle_class'),
                    det['confidence'],
                    det['bbox_x'],
                    det['bbox_y'],
                    det['bbox_width'],
                    det['bbox_height'],
                    det.get('roi_id'),
                    det.get('roi_name')
                ))
            
            cursor.executemany("""
                INSERT INTO vehicle_detections 
                (camera_id, camera_name, camera_location, frame_number,
                 vehicle_type, vehicle_class, confidence,
                 bbox_x, bbox_y, bbox_width, bbox_height,
                 roi_id, roi_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, insert_data)
            
            conn.commit()
            self.logger.info(f"차량 탐지 결과 {len(detections)}건 기록 완료")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"차량 탐지 결과 기록 실패: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_detection_statistics(self, camera_id: str = None, 
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict:
        """탐지 통계 조회"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 기본 쿼리
            query = """
                SELECT 
                    COUNT(*) as total_count,
                    vehicle_type,
                    COUNT(*) as count
                FROM vehicle_detections
                WHERE 1=1
            """
            params = []
            
            # 조건 추가
            if camera_id:
                query += " AND camera_id = %s"
                params.append(camera_id)
            
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
            
            query += " GROUP BY vehicle_type"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Organize statistics
            stats = {
                'total': sum(r['count'] for r in results),
                'by_vehicle_type': {r['vehicle_type']: r['count'] for r in results}
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {'total': 0, 'by_vehicle_type': {}}
        finally:
            if conn:
                conn.close()

    def get_database_status(self) -> Dict:
        """Get database status and statistics"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            status = {
                'total_detections': 0,
                'total_cameras': 0,
                'total_roi': 0,
                'latest_detection': None
            }
            
            # Total detections
            cursor.execute("SELECT COUNT(*) as count FROM vehicle_detections")
            result = cursor.fetchone()
            if result:
                status['total_detections'] = result['count']
            
            # Total cameras
            cursor.execute("SELECT COUNT(*) as count FROM camera_streams WHERE is_active = 1")
            result = cursor.fetchone()
            if result:
                status['total_cameras'] = result['count']
            
            # Total ROIs
            cursor.execute("SELECT COUNT(*) as count FROM roi_regions WHERE is_active = 1")
            result = cursor.fetchone()
            if result:
                status['total_roi'] = result['count']
            
            # Latest detection
            cursor.execute("SELECT timestamp FROM vehicle_detections ORDER BY timestamp DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                status['latest_detection'] = result['timestamp']
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get database status: {e}")
            return {'total_detections': 0, 'total_cameras': 0, 'total_roi': 0, 'latest_detection': None}
        finally:
            if conn:
                conn.close()

    def get_camera_list(self) -> List[Dict]:
        """Get list of all cameras"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, location, is_active, created_at
                FROM camera_streams
                ORDER BY created_at DESC
            """)
            
            cameras = cursor.fetchall()
            return cameras if cameras else []
            
        except Exception as e:
            self.logger.error(f"Failed to get camera list: {e}")
            return []
        finally:
            if conn:
                conn.close()

# Previous version compatibility wrapper
def create_database_manager(db_path: str = None):
    """Previous version compatibility function"""
    return TrafficDatabaseManager()
