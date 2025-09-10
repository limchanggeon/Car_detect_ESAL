"""
ESAL (Equivalent Single Axle Load) 계산 모듈
"""

from typing import Dict, List, Tuple, Optional
from .config import Config

class ESALCalculator:
    """ESAL 점수 계산 및 보수 권고 클래스"""
    
    def __init__(self):
        self.config = Config()
    
    def calculate_class_score(self, class_name: str, count: int) -> float:
        """
        특정 클래스의 총 ESAL 점수 계산
        
        Args:
            class_name: 차량 클래스명
            count: 차량 수
            
        Returns:
            총 ESAL 점수
        """
        score_per_vehicle = self._get_score_per_vehicle(class_name)
        return count * score_per_vehicle
    
    def calculate_total_score(self, counts: Dict[str, int]) -> Tuple[float, Dict[str, float]]:
        """
        전체 ESAL 점수 및 클래스별 세부 점수 계산
        
        Args:
            counts: 클래스별 차량 수 딕셔너리
            
        Returns:
            (총점, 클래스별_세부점수)
        """
        total_score = 0.0
        class_scores = {}
        
        for class_name, count in counts.items():
            class_score = self.calculate_class_score(class_name, count)
            class_scores[class_name] = class_score
            total_score += class_score
        
        return total_score, class_scores
    
    def get_maintenance_recommendation(self, total_score: float) -> str:
        """
        총 ESAL 점수에 따른 보수 권고 반환
        
        Args:
            total_score: 총 ESAL 점수
            
        Returns:
            보수 권고 메시지
        """
        for threshold, message in sorted(self.config.MAINTENANCE_THRESHOLDS, 
                                       key=lambda x: -x[0]):
            if total_score >= threshold:
                return message
        
        return '정기 모니터링' if total_score > 0 else '조치 불필요'
    
    def get_detailed_breakdown(self, counts: Dict[str, int]) -> List[str]:
        """
        클래스별 상세 점수 분석 반환
        
        Args:
            counts: 클래스별 차량 수
            
        Returns:
            상세 분석 문자열 리스트
        """
        breakdown = []
        
        for class_name, count in sorted(counts.items(), 
                                      key=lambda x: (-x[1], x[0])):
            score_per = self._get_score_per_vehicle(class_name)
            subtotal = count * score_per
            korean_name = self.config.KOREAN_LABEL_MAP.get(class_name, class_name)
            
            breakdown.append(
                f"{korean_name}({class_name}): {count} × {score_per} = {subtotal:.1f}"
            )
        
        return breakdown
    
    def _get_score_per_vehicle(self, class_name: str) -> float:
        """
        차량 클래스별 ESAL 점수 반환
        
        Args:
            class_name: 차량 클래스명
            
        Returns:
            차량당 ESAL 점수
        """
        name_lower = class_name.lower()
        
        # 직접 매칭 시도
        score = self.config.SCORE_MAP.get(name_lower)
        if score is not None:
            return float(score)
        
        # 부분 매칭 시도
        for key in self.config.SCORE_MAP.keys():
            if key in name_lower:
                return float(self.config.SCORE_MAP[key])
        
        # 매칭되지 않으면 0점
        return 0.0
    
    def get_maintenance_schedule_info(self, total_score: float) -> Optional[Dict]:
        """
        현재 점수에 해당하는 보수 일정 정보 반환
        
        Args:
            total_score: 총 ESAL 점수
            
        Returns:
            보수 일정 정보 딕셔너리 또는 None
        """
        for schedule in sorted(self.config.MAINTENANCE_SCHEDULE,
                             key=lambda x: -x['cumulative_esal']):
            if total_score >= schedule['cumulative_esal']:
                return schedule
        
        return None