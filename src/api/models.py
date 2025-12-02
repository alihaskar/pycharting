"""Pydantic models for API request and response validation."""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


class IndicatorMetadata(BaseModel):
    """Metadata for individual indicators including their type and display information."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "rsi_14",
                "type": "subplot",
                "display_name": "RSI (14)"
            }
        }
    )
    
    name: str = Field(..., description="Column name from DataFrame")
    type: str = Field(..., description="Indicator type: 'overlay' or 'subplot'")
    display_name: Optional[str] = Field(None, description="Human-readable name for display")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate that type is either 'overlay' or 'subplot' (case-insensitive)."""
        if v is None:
            raise ValueError("Type cannot be None")
        
        v_lower = v.lower()
        if v_lower not in ['overlay', 'subplot']:
            raise ValueError(
                f"Invalid indicator type: '{v}'. Must be 'overlay' or 'subplot'"
            )
        return v_lower


class ChartDataRequest(BaseModel):
    """Request model for chart data endpoint."""
    
    filename: str = Field(..., description="CSV filename to load")
    indicators: Optional[List[str]] = Field(
        default=None,
        description="List of indicators with parameters (e.g., ['RSI:14', 'SMA:20'])"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date for filtering (ISO format or YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date for filtering (ISO format or YYYY-MM-DD)"
    )
    timeframe: Optional[str] = Field(
        default=None,
        description="Timeframe for resampling (e.g., '5min', '1h', '1D')"
    )
    
    @field_validator('timeframe')
    @classmethod
    def validate_timeframe(cls, v):
        """Validate timeframe format."""
        if v is None:
            return v
        
        # Basic validation - detailed validation will happen in processing
        import re
        pattern = r'^\d+(min|h|d|w|m)$'
        if not re.match(pattern, v, re.IGNORECASE):
            raise ValueError(
                f"Invalid timeframe format: '{v}'. "
                f"Expected format like '5min', '1h', '1D'"
            )
        return v.lower()


class ChartDataResponse(BaseModel):
    """Response model for chart data endpoint."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [
                    [1704067200000, 1704070800000],  # timestamps
                    [100.0, 101.0],  # open
                    [105.0, 106.0],  # high
                    [95.0, 96.0],    # low
                    [102.0, 103.0],  # close
                    [1000, 1100]     # volume
                ],
                "metadata": {
                    "filename": "sample.csv",
                    "rows": 2,
                    "columns": 6,
                    "timeframe": "1h",
                    "indicators": []
                }
            }
        }
    )
    
    data: List[List] = Field(..., description="Columnar array data for uPlot")
    metadata: dict = Field(..., description="Metadata about the data")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "File not found: sample.csv",
                "error_code": "FILE_NOT_FOUND"
            }
        }
    )
    
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")

