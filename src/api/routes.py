"""API routes for chart data endpoints."""
from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional, List
from src.api.models import ChartDataResponse, ErrorResponse
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
        
        # TODO: Implement data loading and processing (subtask 6.3)
        # For now, return mock response
        return ChartDataResponse(
            data=[
                [1704067200000, 1704070800000],  # timestamps
                [100.0, 101.0],  # open
                [105.0, 106.0],  # high
                [95.0, 96.0],    # low
                [102.0, 103.0],  # close
                [1000, 1100]     # volume
            ],
            metadata={
                "filename": filename,
                "rows": 2,
                "columns": 6,
                "timeframe": timeframe,
                "indicators": indicators or []
            }
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filename}"
        )
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

