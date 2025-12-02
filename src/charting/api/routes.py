"""API routes for chart data endpoints."""
from fastapi import APIRouter, Query
from typing import Optional, List
from charting.api.models import ChartDataResponse, ErrorResponse
from charting.api.processor import load_and_process_data
from charting.api import exceptions
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chart-data", tags=["chart-data"])


def parse_comma_separated(value: Optional[str]) -> List[str]:
    """
    Parse comma-separated string into list.
    
    Handles empty strings, whitespace, and None values gracefully.
    
    Args:
        value: Comma-separated string or None
        
    Returns:
        List of non-empty strings with whitespace stripped
    """
    if not value or not value.strip():
        return []
    
    # Split by comma and strip whitespace from each item
    items = [item.strip() for item in value.split(',')]
    
    # Filter out empty strings
    return [item for item in items if item]


@router.get(
    "",
    response_model=ChartDataResponse,
    responses={
        404: {"model": ErrorResponse, "description": "File not found"},
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Get chart data",
    description="Load and process CSV data with optional indicators and time filtering"
)
async def get_chart_data(
    filename: str = Query(..., description="CSV filename to load"),
    indicators: Optional[List[str]] = Query(
        None,
        description="List of indicators with parameters (e.g., RSI:14, SMA:20)"
    ),
    overlays: Optional[str] = Query(
        None,
        description="Comma-separated overlay indicator names from CSV (e.g., sma_20,ema_12)"
    ),
    subplots: Optional[str] = Query(
        None,
        description="Comma-separated subplot indicator names from CSV (e.g., rsi_14,macd)"
    ),
    start_date: Optional[str] = Query(
        None,
        description="Start date for filtering (ISO format or YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date for filtering (ISO format or YYYY-MM-DD)"
    ),
    timeframe: Optional[str] = Query(
        None,
        description="Timeframe for resampling (e.g., 5min, 1h, 1D)",
        pattern=r"^\d+(min|h|d|w|m)$"
    ),
    # Column mapping parameters (NEW)
    open: Optional[str] = Query(
        None,
        description="Name of open price column in CSV (for custom column names)"
    ),
    high: Optional[str] = Query(
        None,
        description="Name of high price column in CSV (for custom column names)"
    ),
    low: Optional[str] = Query(
        None,
        description="Name of low price column in CSV (for custom column names)"
    ),
    close: Optional[str] = Query(
        None,
        description="Name of close price column in CSV (for custom column names)"
    ),
    volume: Optional[str] = Query(
        None,
        description="Name of volume column in CSV (for custom column names)"
    )
):
    """
    Get chart data from CSV file with optional processing.
    
    Args:
        filename: Name of CSV file to load
        indicators: Optional list of indicators to calculate
        overlays: Comma-separated overlay indicator names
        subplots: Comma-separated subplot indicator names
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        timeframe: Optional timeframe for resampling
        open: Optional custom column name for open prices
        high: Optional custom column name for high prices
        low: Optional custom column name for low prices
        close: Optional custom column name for close prices
        volume: Optional custom column name for volume
        
    Returns:
        ChartDataResponse with columnar array data
        
    Raises:
        HTTPException: If file not found, invalid parameters, or processing error
    """
    try:
        logger.info(f"Request for chart data: filename={filename}")
        
        # Parse comma-separated indicator parameters
        overlay_list = parse_comma_separated(overlays)
        subplot_list = parse_comma_separated(subplots)
        
        if overlay_list:
            logger.info(f"Requested overlays: {overlay_list}")
        if subplot_list:
            logger.info(f"Requested subplots: {subplot_list}")
        
        # Log column mapping if provided
        if any([open, high, low, close, volume]):
            logger.info(f"Custom column mapping: open={open}, high={high}, low={low}, close={close}, volume={volume}")
        
        # Load and process data
        uplot_data, metadata = load_and_process_data(
            filename=filename,
            indicators=indicators,
            overlays=overlay_list,
            subplots=subplot_list,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            column_open=open,
            column_high=high,
            column_low=low,
            column_close=close,
            column_volume=volume
        )
        
        return ChartDataResponse(
            data=uplot_data,
            metadata=metadata
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {filename}")
        raise exceptions.FileNotFoundError(filename)
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        raise exceptions.ValidationError(str(e))
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise exceptions.ProcessingError("Failed to process chart data")

