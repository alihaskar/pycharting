"""API routes for chart data endpoints."""
from fastapi import APIRouter, Query
from typing import Optional, List
from src.api.models import ChartDataResponse, ErrorResponse
from src.api.processor import load_and_process_data
from src.api import exceptions
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chart-data", tags=["chart-data"])


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
    )
):
    """
    Get chart data from CSV file with optional processing.
    
    Args:
        filename: Name of CSV file to load
        indicators: Optional list of indicators to calculate
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        timeframe: Optional timeframe for resampling
        
    Returns:
        ChartDataResponse with columnar array data
        
    Raises:
        HTTPException: If file not found, invalid parameters, or processing error
    """
    try:
        logger.info(f"Request for chart data: filename={filename}")
        
        # Load and process data
        uplot_data, metadata = load_and_process_data(
            filename=filename,
            indicators=indicators,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
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

