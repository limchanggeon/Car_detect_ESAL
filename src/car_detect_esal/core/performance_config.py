"""
성능 최적화 설정 관리
"""

class PerformanceConfig:
    """성능 최적화를 위한 설정 클래스"""
    
    # 성능 프리셋 설정
    PRESETS = {
        "ultra_fast": {
            "name": "초고속 (1-3 FPS 목표)",
            "imgsz": 320,
            "conf": 0.8,
            "fps_target": 2,
            "sleep_time": 0.5,
            "description": "최대한 빠른 처리, 정확도는 다소 떨어질 수 있음"
        },
        "fast": {
            "name": "고속 (3-8 FPS 목표)", 
            "imgsz": 416,
            "conf": 0.7,
            "fps_target": 5,
            "sleep_time": 0.2,
            "description": "속도와 정확도의 균형"
        },
        "balanced": {
            "name": "균형 (8-15 FPS 목표)",
            "imgsz": 640,
            "conf": 0.5,
            "fps_target": 10,
            "sleep_time": 0.1,
            "description": "기본 설정, 적당한 속도와 정확도"
        },
        "quality": {
            "name": "고품질 (15+ FPS 목표)",
            "imgsz": 640,
            "conf": 0.3,
            "fps_target": 20,
            "sleep_time": 0.05,
            "description": "최고 정확도, 고성능 하드웨어 필요"
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