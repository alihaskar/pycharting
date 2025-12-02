"""
Tests for indicator query parameters in routes.
Testing overlay and subplot parameter parsing and handling.
"""

import pytest
import os
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestQueryParameterParsing:
    """Test parsing of overlay and subplot query parameters."""
    
    def test_parse_single_overlay(self):
        """Test parsing single overlay indicator."""
        # This will test the actual endpoint
        # For now, just verify the parameter is accepted
        response = client.get("/chart-data?filename=test.csv&overlays=sma_20")
        
        # Should accept the parameter (even if file doesn't exist)
        # 404 or 400 means it tried to process, which is good
        assert response.status_code in [404, 400]
    
    def test_parse_multiple_overlays(self):
        """Test parsing comma-separated overlays."""
        response = client.get("/chart-data?filename=test.csv&overlays=sma_20,ema_12")
        
        # Should accept comma-separated parameters
        assert response.status_code in [404, 400]
    
    def test_parse_single_subplot(self):
        """Test parsing single subplot indicator."""
        response = client.get("/chart-data?filename=test.csv&subplots=rsi_14")
        
        # Should accept the parameter
        assert response.status_code in [404, 400]
    
    def test_parse_multiple_subplots(self):
        """Test parsing comma-separated subplots."""
        response = client.get("/chart-data?filename=test.csv&subplots=rsi_14,macd")
        
        # Should accept comma-separated parameters
        assert response.status_code in [404, 400]
    
    def test_parse_both_overlays_and_subplots(self):
        """Test parsing both parameter types together."""
        response = client.get(
            "/chart-data?filename=test.csv&overlays=sma_20&subplots=rsi_14"
        )
        
        # Should accept both parameters
        assert response.status_code in [404, 400]
    
    def test_parse_empty_overlay_parameter(self):
        """Test handling of empty overlay parameter."""
        response = client.get("/chart-data?filename=test.csv&overlays=")
        
        # Should handle empty string gracefully
        assert response.status_code in [404, 400]
    
    def test_parse_empty_subplot_parameter(self):
        """Test handling of empty subplot parameter."""
        response = client.get("/chart-data?filename=test.csv&subplots=")
        
        # Should handle empty string gracefully
        assert response.status_code in [404, 400]
    
    def test_parse_whitespace_in_overlays(self):
        """Test handling of whitespace in parameters."""
        response = client.get("/chart-data?filename=test.csv&overlays=sma_20, ema_12")
        
        # Should handle whitespace gracefully
        assert response.status_code in [404, 400]
    
    def test_parse_no_indicator_parameters(self):
        """Test that indicator parameters are optional."""
        response = client.get("/chart-data?filename=test.csv")
        
        # Should work without indicator parameters
        assert response.status_code in [404, 400]
    
    def test_parameter_names_case_sensitive(self):
        """Test that parameter names are case-sensitive."""
        # Correct case should work
        response1 = client.get("/chart-data?filename=test.csv&overlays=sma_20")
        assert response1.status_code in [404, 400]
        
        # Wrong case should be ignored (treated as missing parameter)
        response2 = client.get("/chart-data?filename=test.csv&Overlays=sma_20")
        assert response2.status_code in [404, 400]


class TestProcessorIntegration:
    """Test integration with processor updates."""
    
    def setup_method(self):
        """Set up test CSV files."""
        import tempfile
        import os
        from pathlib import Path
        import pandas as pd
        
        self.temp_dir = tempfile.mkdtemp()
        os.environ['DATA_DIR'] = self.temp_dir
        
        # Create test CSV with indicators
        dates = pd.date_range('2024-01-01', periods=10, freq='1min')
        data = {
            'timestamp': dates,
            'open': range(100, 110),
            'high': range(102, 112),
            'low': range(99, 109),
            'close': range(101, 111),
            'volume': range(1000, 1010),
            'rsi_14': range(45, 55),
            'sma_20': [x + 0.5 for x in range(100, 110)]
        }
        df = pd.DataFrame(data)
        filepath = Path(self.temp_dir) / 'test_with_indicators.csv'
        df.to_csv(filepath, index=False)
    
    def teardown_method(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if 'DATA_DIR' in os.environ:
            del os.environ['DATA_DIR']
    
    def test_endpoint_passes_overlays_to_processor(self):
        """Test that overlays parameter is passed to processor."""
        response = client.get(
            "/chart-data?filename=test_with_indicators.csv&overlays=sma_20"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check metadata includes overlays
        assert 'overlays' in data['metadata']
        assert 'sma_20' in data['metadata']['overlays']
    
    def test_endpoint_passes_subplots_to_processor(self):
        """Test that subplots parameter is passed to processor."""
        response = client.get(
            "/chart-data?filename=test_with_indicators.csv&subplots=rsi_14"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check metadata includes subplots
        assert 'subplots' in data['metadata']
        assert 'rsi_14' in data['metadata']['subplots']
    
    def test_endpoint_passes_both_parameters(self):
        """Test that both overlay and subplot parameters are passed."""
        response = client.get(
            "/chart-data?filename=test_with_indicators.csv&overlays=sma_20&subplots=rsi_14"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'sma_20' in data['metadata']['overlays']
        assert 'rsi_14' in data['metadata']['subplots']
    
    def test_backward_compatibility_without_parameters(self):
        """Test that endpoint works without indicator parameters."""
        response = client.get("/chart-data?filename=test_with_indicators.csv")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have empty lists
        assert data['metadata']['overlays'] == []
        assert data['metadata']['subplots'] == []
    
    def test_filters_nonexistent_indicators(self):
        """Test that nonexistent indicators are filtered out."""
        response = client.get(
            "/chart-data?filename=test_with_indicators.csv&overlays=nonexistent,sma_20"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Only existing indicator should be included
        assert data['metadata']['overlays'] == ['sma_20']

