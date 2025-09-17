"""
성능 최적화 설정 관리
"""

class PerformanceConfig:
    """성능 최적화를 위한 설정 클래스"""
    
    # 성능 프리셋 설정
    PRESETS = {
        "ultra_fast": {
            "name": "초고속 (15+ FPS 목표)",
            "imgsz": 320,
            "conf": 0.8,
            "fps_target": 20,
            "sleep_time": 0.02,  # 매우 짧은 딜레이
            "description": "최고 속도, 낮은 해상도로 빠른 탐지"
        },
        "fast": {
            "name": "고속 (8-15 FPS 목표)", 
            "imgsz": 416,
            "conf": 0.7,
            "fps_target": 12,
            "sleep_time": 0.05,
            "description": "빠른 속도와 적당한 정확도"
        },
        "balanced": {
            "name": "균형 (3-8 FPS 목표)",
            "imgsz": 640,
            "conf": 0.5,
            "fps_target": 6,
            "sleep_time": 0.1,
            "description": "속도와 정확도의 균형"
        },
        "quality": {
            "name": "고품질 (1-5 FPS 목표)",
            "imgsz": 640,
            "conf": 0.3,
            "fps_target": 3,
            "sleep_time": 0.2,
            "description": "최고 정확도, 높은 해상도"
        }
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> dict:
        """프리셋 설정 가져오기"""
        return cls.PRESETS.get(preset_name, cls.PRESETS["balanced"])
    
    @classmethod
    def get_preset_names(cls) -> list:
        """사용 가능한 프리셋 이름들"""
        return list(cls.PRESETS.keys())
    
    @classmethod
    def recommend_preset_for_fps(cls, target_fps: float) -> str:
        """목표 FPS에 따른 프리셋 추천"""
        if target_fps < 3:
            return "ultra_fast"
        elif target_fps < 8:
            return "fast" 
        elif target_fps < 15:
            return "balanced"
        else:
            return "quality"