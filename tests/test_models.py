"""
Tests for API Pydantic models.
Testing IndicatorMetadata and enhanced ChartMetadata models.
"""

import pytest
from pydantic import ValidationError
from src.api.models import IndicatorMetadata, ChartDataResponse


class TestIndicatorMetadataModel:
    """Test IndicatorMetadata Pydantic model."""
    
    def test_create_indicator_metadata_overlay(self):
        """Test creating indicator metadata for overlay type."""
        indicator = IndicatorMetadata(
            name="sma_20",
            type="overlay"
        )
        
        assert indicator.name == "sma_20"
        assert indicator.type == "overlay"
        assert indicator.display_name is None
    
    def test_create_indicator_metadata_subplot(self):
        """Test creating indicator metadata for subplot type."""
        indicator = IndicatorMetadata(
            name="rsi_14",
            type="subplot"
        )
        
        assert indicator.name == "rsi_14"
        assert indicator.type == "subplot"
        assert indicator.display_name is None
    
    def test_create_indicator_metadata_with_display_name(self):
        """Test creating indicator metadata with display name."""
        indicator = IndicatorMetadata(
            name="rsi_14",
            type="subplot",
            display_name="RSI (14)"
        )
        
        assert indicator.name == "rsi_14"
        assert indicator.type == "subplot"
        assert indicator.display_name == "RSI (14)"
    
    def test_indicator_metadata_rejects_invalid_type(self):
        """Test that invalid type values are rejected."""
        with pytest.raises(ValidationError):
            IndicatorMetadata(
                name="test",
                type="invalid"
            )
    
    def test_indicator_metadata_type_case_insensitive(self):
        """Test that type validation is case-insensitive."""
        # Should accept uppercase
        indicator1 = IndicatorMetadata(name="test", type="OVERLAY")
        assert indicator1.type == "overlay"
        
        # Should accept mixed case
        indicator2 = IndicatorMetadata(name="test", type="SubPlot")
        assert indicator2.type == "subplot"
    
    def test_indicator_metadata_serialization(self):
        """Test serialization to JSON."""
        indicator = IndicatorMetadata(
            name="rsi_14",
            type="subplot",
            display_name="RSI (14)"
        )
        
        data = indicator.model_dump()
        
        assert data["name"] == "rsi_14"
        assert data["type"] == "subplot"
        assert data["display_name"] == "RSI (14)"
    
    def test_indicator_metadata_deserialization(self):
        """Test deserialization from JSON."""
        data = {
            "name": "sma_20",
            "type": "overlay",
            "display_name": "SMA (20)"
        }
        
        indicator = IndicatorMetadata(**data)
        
        assert indicator.name == "sma_20"
        assert indicator.type == "overlay"
        assert indicator.display_name == "SMA (20)"
    
    def test_indicator_metadata_missing_required_fields(self):
        """Test that required fields are enforced."""
        # Missing name
        with pytest.raises(ValidationError):
            IndicatorMetadata(type="overlay")
        
        # Missing type
        with pytest.raises(ValidationError):
            IndicatorMetadata(name="test")
    
    def test_indicator_metadata_empty_type(self):
        """Test that empty type string is rejected."""
        with pytest.raises(ValidationError):
            IndicatorMetadata(name="test", type="")
    
    def test_indicator_metadata_multiple_instances(self):
        """Test creating multiple indicator metadata instances."""
        indicators = [
            IndicatorMetadata(name="sma_10", type="overlay"),
            IndicatorMetadata(name="sma_20", type="overlay"),
            IndicatorMetadata(name="rsi_14", type="subplot"),
            IndicatorMetadata(name="macd", type="subplot")
        ]
        
        assert len(indicators) == 4
        assert all(isinstance(i, IndicatorMetadata) for i in indicators)


class TestEnhancedChartMetadata:
    """Test enhanced ChartMetadata with indicator lists."""
    
    def test_chart_response_with_indicator_metadata(self):
        """Test ChartDataResponse with new indicator fields in metadata."""
        response = ChartDataResponse(
            data=[[1, 2], [100, 101]],
            metadata={
                "filename": "test.csv",
                "rows": 2,
                "columns": 2,
                "available_indicators": ["rsi_14", "sma_20"],
                "overlays": ["sma_20"],
                "subplots": ["rsi_14"]
            }
        )
        
        assert response.metadata["available_indicators"] == ["rsi_14", "sma_20"]
        assert response.metadata["overlays"] == ["sma_20"]
        assert response.metadata["subplots"] == ["rsi_14"]
    
    def test_chart_response_backward_compatibility(self):
        """Test that existing code without indicator fields still works."""
        response = ChartDataResponse(
            data=[[1, 2], [100, 101]],
            metadata={
                "filename": "test.csv",
                "rows": 2,
                "columns": 2
            }
        )
        
        assert response.metadata["filename"] == "test.csv"
        assert "available_indicators" not in response.metadata
    
    def test_chart_response_empty_indicator_lists(self):
        """Test ChartDataResponse with empty indicator lists."""
        response = ChartDataResponse(
            data=[[1, 2], [100, 101]],
            metadata={
                "filename": "test.csv",
                "rows": 2,
                "columns": 2,
                "available_indicators": [],
                "overlays": [],
                "subplots": []
            }
        )
        
        assert response.metadata["available_indicators"] == []
        assert response.metadata["overlays"] == []
        assert response.metadata["subplots"] == []

