"""
Car Detection ESAL Analysis System Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="car-detect-esal",
    version="1.0.0",
    description="Vehicle Detection and ESAL (Equivalent Single Axle Load) Analysis System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Car Detection ESAL Team",
    author_email="contact@example.com",
    url="https://github.com/limchanggeon/Car_detect_ESAL",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    install_requires=requirements,
    
    extras_require={
        "gui": ["PyQt5", "PyQtWebEngine"],
        "dev": ["pytest", "black", "flake8"],
    },
    
    entry_points={
        "console_scripts": [
            "car-detect-esal=car_detect_esal.gui.main_window:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    
    python_requires=">=3.8",
    
    include_package_data=True,
    package_data={
        "car_detect_esal": ["assets/*", "config/*"],
    },
    
    keywords=["yolo", "vehicle detection", "esal", "pavement analysis", "computer vision"],
)