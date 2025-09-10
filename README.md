# Car Detection ESAL Analysis System

A comprehensive vehicle detection and pavement load analysis system using YOLOv8 and ESAL (Equivalent Single Axle Load) methodology.

## 🚀 Features

- **Real-time Vehicle Detection**: YOLOv8-based detection with customizable confidence thresholds
- **ESAL Analysis**: Automatic calculation of pavement loads based on detected vehicles
- **Multi-Stream Support**: Monitor multiple video sources simultaneously
- **ROI Selection**: Define regions of interest for targeted analysis
- **Maintenance Recommendations**: Automated pavement maintenance scheduling based on ESAL scores
- **Modern GUI**: Intuitive PyQt5-based interface with real-time updates

## 📁 Project Structure

```
├── src/car_detect_esal/          # Main application package
│   ├── core/                     # Core functionality
│   │   ├── config.py            # Configuration management
│   │   ├── detector.py          # Vehicle detection logic
│   │   └── esal_calculator.py   # ESAL calculation engine
│   ├── gui/                     # User interface components
│   │   ├── main_window.py       # Main application window
│   │   ├── stream_panel.py      # Individual stream panels
│   │   ├── video_label.py       # Video display widget
│   │   └── stream_worker.py     # Background processing
│   └── api/                     # External API integrations
│       ├── ntis_client.py       # NTIS traffic camera API
│       └── cctv_api.py          # CCTV management API
├── config/                      # Configuration files
├── assets/                      # Static assets (HTML, images)
├── scripts/                     # Utility scripts
├── tests/                       # Unit tests
├── weights/                     # AI model weights
├── demo_videos/                 # Sample videos
└── main.py                     # Application entry point
```

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- PyQt5 and PyQtWebEngine
- CUDA-capable GPU (optional, for better performance)

### Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/limchanggeon/Car_detect_ESAL.git
cd Car_detect_ESAL
```

2. **Create virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the application**:
```bash
python main.py
```

### Development Installation

For development with additional tools:
```bash
pip install -e ".[dev,gui]"
```

## 📖 Usage

### Basic Usage

1. **Start the application**: Run `python main.py`
2. **Load model**: Click "🔄 로드" to load a YOLOv8 model (place your model in `weights/best.pt`)
3. **Add video source**: 
   - Enter RTSP URL or video file path
   - Click "🎬 데모 비디오" for sample videos
   - Click "➕ 스트림 추가" to add the source
4. **Select ROI**: Click and drag on the video to define analysis region
5. **Start detection**: Click "▶️ 시작" to begin analysis

### ESAL Scoring

The system uses predefined vehicle weights for ESAL calculation:

| Vehicle Type | ESAL Score |
|--------------|------------|
| Car/SUV/Motorbike | 1 |
| Van | 150 |
| Work Van/Caravan | 7,950 |
| Bus | 10,430 |
| Truck | 25,160 |
| Construction Vehicle/Trailer | 24,820 |

### Maintenance Thresholds

- **500,000 ESAL**: Preventive maintenance (50% design capacity, 10 years)
- **700,000 ESAL**: Surface treatment (70% design capacity, 14 years)  
- **850,000 ESAL**: Intermediate rehabilitation (85% design capacity, 17 years)
- **1,000,000 ESAL**: Full reconstruction (100% design capacity, 20 years)

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

Or run individual test:
```bash
python tests/test_basic.py
```

## 📝 Configuration

Configuration can be customized through:
- `config/settings.py`: Main configuration file
- Environment variables for API keys (e.g., `NTIS_API_KEY`)
- GUI settings panel for model parameters

## 🔌 API Integration

### NTIS Integration

Set your NTIS API key:
```bash
export NTIS_API_KEY="your_api_key_here"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for object detection
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- [OpenCV](https://opencv.org/) for computer vision operations

## 📧 Contact

For questions or support, please open an issue on GitHub or contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: September 2025
