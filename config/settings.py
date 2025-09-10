"""
Configuration files and project settings
"""

import json
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "model": {
        "path": "weights/best.pt",
        "imgsz": 640,
        "conf": 0.25
    },
    "gui": {
        "window_size": [1200, 800],
        "video_size": [640, 360],
        "grid_columns": 2
    },
    "esal": {
        "score_map": {
            "bicycle": 0,
            "person": 0,
            "people": 0,
            "car": 1,
            "cars": 1,
            "suv": 1,
            "motorbike": 1,
            "motorcycle": 1,
            "bike": 1,
            "van": 150,
            "work_van": 7950,
            "caravan": 7950,
            "bus": 10430,
            "construction_vehicle": 24820,
            "trailer": 24820,
            "truck": 25160
        },
        "maintenance_thresholds": [
            {"score": 1000000, "message": "전면재포장 (설계 대비 100%, 20년 후)"},
            {"score": 850000, "message": "중간보수 (설계 대비 85%, 17년 후)"},
            {"score": 700000, "message": "표층보수 (설계 대비 70%, 14년 후)"},
            {"score": 500000, "message": "예방보수 (설계 대비 50%, 10년 후)"}
        ]
    }
}

def load_config(config_path: Path = None) -> dict:
    """Load configuration from file or return defaults"""
    if config_path is None:
        config_path = Path(__file__).parent / "default_config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Config load error: {e}, using defaults")
    
    return DEFAULT_CONFIG

def save_config(config: dict, config_path: Path = None):
    """Save configuration to file"""
    if config_path is None:
        config_path = Path(__file__).parent / "user_config.json"
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Configuration saved to {config_path}")
    except Exception as e:
        print(f"Config save error: {e}")

# Save default config on import
if __name__ == "__main__":
    default_path = Path(__file__).parent / "default_config.json"
    save_config(DEFAULT_CONFIG, default_path)