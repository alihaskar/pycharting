"""
Tests for detector logging functionality

Tests cover:
- Logging configuration
- Detection logging
- Classification logging
- Error logging
- Log level control
"""
import pytest
import pandas as pd
import logging
from unittest.mock import patch, MagicMock


class TestLoggingSetup:
    """Test logging configuration and setup"""
    
    def test_detector_has_logger(self):
        """detector module should have a configured logger"""
        from src.python_api import detector
        
        assert hasattr(detector, 'logger')
        assert isinstance(detector.logger, logging.Logger)
    
    def test_logger_name_is_detector_module(self):
        """Logger should be named after the module"""
        from src.python_api import detector
        
        assert 'detector' in detector.logger.name


class TestDetectionLogging:
    """Test logging during column detection"""
    
    @patch('src.python_api.detector.logger')
    def test_logs_ohlc_detection_success(self, mock_logger):
        """Should log successful OHLC column detection"""
        from src.python_api.detector import detect_ohlc_columns_via_mapper
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0]
        }, index=dates)
        
        result = detect_ohlc_columns_via_mapper(df)
        
        # Should log INFO about detected columns
        assert mock_logger.info.called or mock_logger.debug.called
    
    @patch('src.python_api.detector.logger')
    def test_logs_standardization_process(self, mock_logger):
        """Should log DataFrame standardization"""
        from src.python_api.detector import standardize_dataframe
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [103.0, 104.0, 105.0, 106.0, 107.0]
        }, index=dates)
        
        result = standardize_dataframe(df)
        
        # Should log the standardization process
        assert mock_logger.info.called or mock_logger.debug.called


class TestClassificationLogging:
    """Test logging during indicator classification"""
    
    @patch('src.python_api.detector.logger')
    def test_logs_user_override_usage(self, mock_logger):
        """Should log when user overrides are used"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['custom_ind']
        user_mapping = {'custom_ind': True}
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        # Should log that user override was applied
        assert mock_logger.info.called or mock_logger.debug.called
    
    @patch('src.python_api.detector.logger')
    def test_logs_pattern_matching_fallback(self, mock_logger):
        """Should log when pattern matching is used"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['sma_20']  # No user mapping
        
        overlays, subplots = classify_indicators_enhanced(indicators, None)
        
        # Should log pattern matching was used
        assert mock_logger.debug.called
    
    @patch('src.python_api.detector.logger')
    def test_logs_unknown_indicator_warning(self, mock_logger):
        """Should warn when indicator in user_mapping not in indicator list"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['sma_20']
        user_mapping = {
            'sma_20': True,
            'unknown_indicator': True  # Not in indicators list
        }
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        # Should log warning about unknown indicator
        assert mock_logger.warning.called


class TestErrorLogging:
    """Test logging during error conditions"""
    
    @patch('src.python_api.detector.logger')
    def test_logs_column_not_found_error(self, mock_logger):
        """Should log when columns cannot be detected"""
        from src.python_api.detector import standardize_dataframe
        
        dates = pd.date_range('2024-01-01', periods=5, freq='1h')
        df = pd.DataFrame({
            'price': [100.0, 101.0, 102.0, 103.0, 104.0]
        }, index=dates)
        
        try:
            standardize_dataframe(df)
        except Exception:
            pass
        
        # Should log error or warning
        assert mock_logger.error.called or mock_logger.warning.called


class TestLogLevelControl:
    """Test log level configuration"""
    
    def test_can_set_log_level_debug(self):
        """Should be able to set logger to DEBUG level"""
        from src.python_api import detector
        
        original_level = detector.logger.level
        detector.logger.setLevel(logging.DEBUG)
        
        assert detector.logger.level == logging.DEBUG
        
        # Restore
        detector.logger.setLevel(original_level)
    
    def test_can_set_log_level_info(self):
        """Should be able to set logger to INFO level"""
        from src.python_api import detector
        
        original_level = detector.logger.level
        detector.logger.setLevel(logging.INFO)
        
        assert detector.logger.level == logging.INFO
        
        # Restore
        detector.logger.setLevel(original_level)

