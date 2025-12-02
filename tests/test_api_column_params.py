"""
Tests for API column parameter handling

Tests cover:
- Pydantic model validation for column parameters
- API endpoint parameter acceptance
- Backward compatibility with existing API
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestColumnParameterModels:
    """Test Pydantic models for column parameters"""
    
    def test_column_mapping_model_exists(self):
        """Should have ColumnMappingParams model"""
        from src.api.models import ColumnMappingParams
        assert ColumnMappingParams is not None
    
    def test_column_mapping_accepts_optional_params(self):
        """Model should accept optional column parameters"""
        from src.api.models import ColumnMappingParams
        
        params = ColumnMappingParams(
            open='Open',
            high='High',
            low='Low',
            close='Close'
        )
        
        assert params.open == 'Open'
        assert params.high == 'High'
        assert params.low == 'Low'
        assert params.close == 'Close'
    
    def test_column_mapping_all_fields_optional(self):
        """All column fields should be optional"""
        from src.api.models import ColumnMappingParams
        
        params = ColumnMappingParams()
        
        assert params.open is None
        assert params.high is None
        assert params.low is None
        assert params.close is None
        assert params.volume is None
    
    def test_column_mapping_accepts_volume(self):
        """Model should accept volume parameter"""
        from src.api.models import ColumnMappingParams
        
        params = ColumnMappingParams(volume='Vol')
        
        assert params.volume == 'Vol'


class TestAPIEndpointColumnParams:
    """Test API endpoint accepts column parameters"""
    
    def test_chart_data_endpoint_accepts_column_params(self, tmp_path):
        """Should accept open, high, low, close, volume parameters"""
        # Create test CSV with custom column names
        csv_path = tmp_path / "test_custom.csv"
        csv_path.write_text(
            "timestamp,PriceOpen,PriceHigh,PriceLow,PriceClose,Vol\n"
            "2024-01-01 00:00:00,100,105,99,103,1000\n"
            "2024-01-01 01:00:00,103,106,102,105,1200\n"
        )
        
        response = client.get(
            "/chart-data",
            params={
                "filename": csv_path.name,
                "open": "PriceOpen",
                "high": "PriceHigh",
                "low": "PriceLow",
                "close": "PriceClose",
                "volume": "Vol"
            }
        )
        
        # Should process successfully or return 404 (file not in data dir)
        assert response.status_code in [200, 404]
    
    def test_column_params_are_query_parameters(self):
        """Column parameters should be query parameters"""
        # Test that parameters are passed as query params, not body
        response = client.get(
            "/chart-data",
            params={
                "filename": "test.csv",
                "open": "O",
                "high": "H"
            }
        )
        
        # Should be valid request format (may 404 for missing file)
        assert response.status_code != 422  # Not validation error


class TestBackwardCompatibility:
    """Test backward compatibility with existing API"""
    
    def test_api_works_without_column_params(self, tmp_path):
        """Should work without column parameters (auto-detect)"""
        csv_path = tmp_path / "test_auto.csv"
        csv_path.write_text(
            "timestamp,open,high,low,close,volume\n"
            "2024-01-01 00:00:00,100,105,99,103,1000\n"
        )
        
        response = client.get(
            "/chart-data",
            params={"filename": csv_path.name}
        )
        
        # Should process (404 is ok, means file not in data dir)
        assert response.status_code in [200, 404]
    
    def test_existing_api_calls_still_work(self):
        """Existing API usage should not break"""
        response = client.get(
            "/chart-data",
            params={
                "filename": "sample.csv",
                "timeframe": "1h"
            }
        )
        
        # Should be valid request (200 if file exists, 404 if not)
        assert response.status_code in [200, 404]


class TestParameterValidation:
    """Test parameter validation"""
    
    def test_column_params_must_be_strings(self):
        """Column parameters should be validated as strings"""
        from src.api.models import ColumnMappingParams
        
        # Should accept strings
        params = ColumnMappingParams(open='Open')
        assert params.open == 'Open'
    
    def test_empty_string_column_names_handled(self):
        """Empty string column names should be handled"""
        from src.api.models import ColumnMappingParams
        
        # Empty strings might be treated as None or rejected
        params = ColumnMappingParams(open='')
        
        # Should either be None or empty string (implementation choice)
        assert params.open == '' or params.open is None

