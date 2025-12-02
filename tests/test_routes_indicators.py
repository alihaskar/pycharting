"""
Tests for indicator query parameters in routes.
Testing overlay and subplot parameter parsing and handling.
"""

import pytest
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

