"""
Basic tests for the Car Detection ESAL system
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from car_detect_esal.core.config import Config
from car_detect_esal.core.esal_calculator import ESALCalculator

class TestConfig(unittest.TestCase):
    """Test configuration module"""
    
    def test_config_initialization(self):
        """Test that config initializes properly"""
        config = Config()
        self.assertIsInstance(config.SCORE_MAP, dict)
        self.assertGreater(len(config.SCORE_MAP), 0)
        self.assertIn('car', config.SCORE_MAP)

class TestESALCalculator(unittest.TestCase):
    """Test ESAL calculation functionality"""
    
    def setUp(self):
        self.calculator = ESALCalculator()
    
    def test_score_calculation(self):
        """Test basic score calculation"""
        score = self.calculator.calculate_class_score('car', 5)
        self.assertEqual(score, 5.0)  # car has score 1
        
        score = self.calculator.calculate_class_score('truck', 2) 
        self.assertEqual(score, 50320.0)  # truck has score 25160
    
    def test_total_score_calculation(self):
        """Test total score calculation"""
        counts = {'car': 3, 'truck': 1, 'bicycle': 2}
        total_score, class_scores = self.calculator.calculate_total_score(counts)
        
        expected_total = 3 * 1 + 1 * 25160 + 2 * 0  # 25163
        self.assertEqual(total_score, expected_total)
        self.assertEqual(len(class_scores), 3)
    
    def test_maintenance_recommendation(self):
        """Test maintenance recommendation logic"""
        # Low score
        rec = self.calculator.get_maintenance_recommendation(100)
        self.assertEqual(rec, '정기 모니터링')
        
        # High score
        rec = self.calculator.get_maintenance_recommendation(1500000)
        self.assertIn('전면재포장', rec)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)