"""
Tests for enhanced indicator classification with user overrides

Tests cover:
- User-provided indicator mappings
- Pattern matching fallback
- Mixed explicit + auto classification
- Edge cases and validation
"""
import pytest
import pandas as pd


class TestIndicatorClassificationWithOverrides:
    """Test indicator classification with user-provided mappings"""
    
    def test_classify_with_user_override_overlay(self):
        """Should use user-provided mapping for overlay indicators"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['custom_ind_1', 'custom_ind_2', 'rsi_14']
        user_mapping = {
            'custom_ind_1': True,  # True = overlay
            'custom_ind_2': True
        }
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        assert 'custom_ind_1' in overlays
        assert 'custom_ind_2' in overlays
        assert 'rsi_14' in subplots  # Auto-classified via pattern
    
    def test_classify_with_user_override_subplot(self):
        """Should use user-provided mapping for subplot indicators"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['custom_oscillator', 'sma_20']
        user_mapping = {
            'custom_oscillator': False  # False = subplot
        }
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        assert 'custom_oscillator' in subplots
        assert 'sma_20' in overlays  # Auto-classified via pattern
    
    def test_classify_all_user_provided_no_fallback(self):
        """Should handle all indicators explicitly mapped"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['ind_1', 'ind_2', 'ind_3']
        user_mapping = {
            'ind_1': True,
            'ind_2': False,
            'ind_3': True
        }
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        assert set(overlays) == {'ind_1', 'ind_3'}
        assert set(subplots) == {'ind_2'}
    
    def test_classify_user_override_takes_precedence(self):
        """User mapping should override pattern matching"""
        from src.python_api.detector import classify_indicators_enhanced
        
        # RSI normally auto-classified as subplot
        indicators = ['rsi_14', 'sma_20']
        user_mapping = {
            'rsi_14': True  # Override: treat as overlay!
        }
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        assert 'rsi_14' in overlays  # User override
        assert 'sma_20' in overlays  # Auto-classified
        assert len(subplots) == 0
    
    def test_classify_with_empty_user_mapping(self):
        """Should fallback to pattern matching with empty user mapping"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['sma_20', 'rsi_14']
        user_mapping = {}
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        assert 'sma_20' in overlays
        assert 'rsi_14' in subplots
    
    def test_classify_with_none_user_mapping(self):
        """Should handle None user mapping gracefully"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['sma_20', 'rsi_14']
        
        overlays, subplots = classify_indicators_enhanced(indicators, None)
        
        assert 'sma_20' in overlays
        assert 'rsi_14' in subplots


class TestIndicatorClassificationValidation:
    """Test validation and edge cases"""
    
    def test_warns_on_unknown_indicator_in_mapping(self):
        """Should warn if user mapping includes indicators not in list"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['rsi_14']
        user_mapping = {
            'rsi_14': True,
            'unknown_indicator': True  # Not in indicators list
        }
        
        # Should not raise, but may log warning
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        assert 'rsi_14' in overlays
        assert 'unknown_indicator' not in overlays
        assert 'unknown_indicator' not in subplots
    
    def test_handles_indicator_name_case_sensitivity(self):
        """User mapping keys should match indicator names exactly"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['RSI_14', 'sma_20']
        user_mapping = {
            'RSI_14': True  # Exact match required
        }
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        assert 'RSI_14' in overlays  # Matched exactly
        assert 'sma_20' in overlays  # Auto-classified
    
    def test_handles_empty_indicator_list(self):
        """Should handle empty indicator list gracefully"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = []
        user_mapping = {'ind': True}
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        assert overlays == []
        assert subplots == []


class TestMixedClassification:
    """Test mixed explicit and auto classification scenarios"""
    
    def test_partial_override_with_fallback(self):
        """Some indicators explicit, others auto-classified"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['custom_1', 'sma_20', 'rsi_14', 'custom_2', 'ema_12']
        user_mapping = {
            'custom_1': True,
            'custom_2': False
        }
        
        overlays, subplots = classify_indicators_enhanced(indicators, user_mapping)
        
        # Explicit mappings
        assert 'custom_1' in overlays
        assert 'custom_2' in subplots
        
        # Auto-classified
        assert 'sma_20' in overlays
        assert 'ema_12' in overlays
        assert 'rsi_14' in subplots
    
    def test_unknown_indicator_defaults_to_subplot(self):
        """Unknown indicators without mapping should default to subplot"""
        from src.python_api.detector import classify_indicators_enhanced
        
        indicators = ['totally_unknown_indicator']
        
        overlays, subplots = classify_indicators_enhanced(indicators, None)
        
        assert 'totally_unknown_indicator' in subplots
        assert len(overlays) == 0

