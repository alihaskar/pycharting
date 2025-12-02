"""Pydantic models for OHLC data validation."""
from datetime import datetime
from typing import Union
from pydantic import BaseModel, field_validator, model_validator


class OHLCRecord(BaseModel):
    """
    Pydantic model for validating a single OHLC (Open, High, Low, Close) record.
    
    Validates:
    - All required fields are present
    - Prices are numeric
    - High >= max(open, close)
    - Low <= min(open, close)
    - Volume >= 0
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Union[int, float]
    
    @field_validator("volume")
    @classmethod
    def validate_volume_non_negative(cls, v: Union[int, float]) -> Union[int, float]:
        """Validate that volume is non-negative."""
        if v < 0:
            raise ValueError(f"Volume must be non-negative, got {v}")
        return v
    
    @model_validator(mode="after")
    def validate_ohlc_relationships(self) -> "OHLCRecord":
        """
        Validate OHLC price relationships.
        
        Rules:
        - High must be >= max(open, close)
        - Low must be <= min(open, close)
        """
        # Validate high is >= open
        if self.high < self.open:
            raise ValueError(
                f"High ({self.high}) must be >= open ({self.open})"
            )
        
        # Validate high is >= close
        if self.high < self.close:
            raise ValueError(
                f"High ({self.high}) must be >= close ({self.close})"
            )
        
        # Validate low is <= open
        if self.low > self.open:
            raise ValueError(
                f"Low ({self.low}) must be <= open ({self.open})"
            )
        
        # Validate low is <= close
        if self.low > self.close:
            raise ValueError(
                f"Low ({self.low}) must be <= close ({self.close})"
            )
        
        return self

