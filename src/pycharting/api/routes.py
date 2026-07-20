"""API Routes Definition for PyCharting.

This module defines the REST API endpoints that the frontend JavaScript uses to:
1. Fetch sliced and diced OHLC data (`/data`).
2. Manage data sessions (`/sessions`).
3. Check system status (`/status`).
4. Initialize demo data (`/data/init`).

The data is served from the in-memory `_data_managers` registry, which is populated
by the main Python process via `src.api.interface.plot()`.
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from pycharting.data.ingestion import DataManager

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api", tags=["data"])

# In-memory storage for active DataManager instances
# In production, this would use a proper session/cache management
_data_managers: dict[str, DataManager] = {}


class DataResponse(BaseModel):
    """Response model for data endpoint."""

    index: list
    open: list | None = None
    high: list | None = None
    low: list | None = None
    close: list | None = None
    overlays: dict[str, list] = Field(default_factory=dict)
    subplots: dict[str, list] = Field(default_factory=dict)
    subplot_meta: dict[str, list] | None = None
    trades: list | None = None
    start_index: int
    end_index: int
    total_length: int


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str | None = None


class InitDataResponse(BaseModel):
    """Response model for the demo-data initialization endpoint."""

    session_id: str
    status: str
    data_points: int
    message: str


class SessionInfo(BaseModel):
    """Metadata describing a single active data session."""

    session_id: str
    data_points: int
    has_overlays: bool
    has_subplots: bool


class SessionListResponse(BaseModel):
    """Response model for the sessions listing endpoint."""

    sessions: list[SessionInfo]
    count: int


class DeleteSessionResponse(BaseModel):
    """Response model for the session deletion endpoint."""

    session_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    """Response model for the API status endpoint."""

    status: str
    active_sessions: int
    endpoints: dict[str, str]


@router.get("/data", response_model=DataResponse)
async def get_data(
    start_index: int = Query(0, ge=0, description="Start index for data slice"),
    end_index: int | None = Query(None, ge=0, description="End index for data slice"),
    session_id: str = Query("default", description="Session identifier for data source"),
):
    """Retrieve a specific slice of OHLC data.

    This endpoint is optimized for high-performance frontend rendering. Instead of sending the full dataset
    at once (which could be millions of points), the frontend requests only the necessary chunk
    based on the current zoom level and viewport.

    Args:
        start_index (int): The zero-based index of the first data point to retrieve.
        end_index (Optional[int]): The zero-based index of the last data point (exclusive).
            If None, retrieves data until the end of the series.
        session_id (str): The ID of the data session to query.

    Returns:
        DataResponse: A JSON object containing parallel arrays for index, open, high, low, close,
        overlays, and subplots for the requested range.

    Raises:
        HTTPException(404): If the specified session_id does not exist.
        HTTPException(500): If an internal error occurs during data slicing.
    """
    # Check if session exists
    if session_id not in _data_managers:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found. Please initialize data first.")

    data_manager = _data_managers[session_id]

    try:
        # Get data chunk
        chunk = data_manager.get_chunk(start_index, end_index)

        # Add metadata
        actual_end = end_index if end_index is not None else data_manager.length

        return DataResponse(**chunk, start_index=start_index, end_index=actual_end, total_length=data_manager.length)

    except Exception as e:
        logger.exception("Error fetching data chunk")
        raise HTTPException(status_code=500, detail=f"Error fetching data: {e!s}") from e


@router.post("/data/init", response_model=InitDataResponse)
async def initialize_data(
    session_id: str = Query("default", description="Session identifier"),
) -> InitDataResponse:
    """Initialize a demo data session.

    This endpoint is primarily used for testing or the standalone demo mode.
    It generates synthetic random walk data and registers it under the given session ID.

    Args:
        session_id (str): The ID to assign to the new session.

    Returns:
        InitDataResponse: Status message and session details.
    """
    import numpy as np

    try:
        # Generate demo OHLC data
        n = 1000
        timestamps = np.arange(n)

        # Simulate price movement
        price = 100.0
        open_data = []
        high = []
        low = []
        close_data = []

        for _i in range(n):
            o = price
            change = np.random.randn() * 2
            c = o + change
            h = max(o, c) + abs(np.random.randn())
            lo = min(o, c) - abs(np.random.randn())

            open_data.append(o)
            high.append(h)
            low.append(lo)
            close_data.append(c)

            price = c

        # Create DataManager
        dm = DataManager(
            index=timestamps,
            open=np.array(open_data),
            high=np.array(high),
            low=np.array(low),
            close=np.array(close_data),
        )

        # Store in session
        _data_managers[session_id] = dm

        logger.info(f"Initialized session '{session_id}' with {n} data points")

    except Exception as e:
        logger.exception("Error initializing data")
        raise HTTPException(status_code=500, detail=f"Error initializing data: {e!s}") from e
    else:
        return InitDataResponse(
            session_id=session_id,
            status="initialized",
            data_points=n,
            message="Demo dataset created successfully",
        )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions() -> SessionListResponse:
    """List all currently active data sessions.

    Returns:
        SessionListResponse: A list of session objects, each with metadata like the
        number of data points and active features (overlays, subplots).
    """
    sessions = [
        SessionInfo(
            session_id=session_id,
            data_points=dm.length,
            has_overlays=len(dm.overlays) > 0,
            has_subplots=len(dm.subplots) > 0,
        )
        for session_id, dm in _data_managers.items()
    ]

    return SessionListResponse(sessions=sessions, count=len(sessions))


@router.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str) -> DeleteSessionResponse:
    """Remove a data session from memory.

    This frees up resources associated with a specific dataset.

    Args:
        session_id (str): The ID of the session to remove.

    Returns:
        DeleteSessionResponse: Confirmation message.

    Raises:
        HTTPException(404): If the session ID is not found.
    """
    if session_id not in _data_managers:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    del _data_managers[session_id]
    logger.info(f"Deleted session '{session_id}'")

    return DeleteSessionResponse(session_id=session_id, status="deleted", message="Session deleted successfully")


@router.get("/status", response_model=StatusResponse)
async def api_status() -> StatusResponse:
    """Get API status and statistics.

    Returns:
        StatusResponse: API status information.
    """
    return StatusResponse(
        status="healthy",
        active_sessions=len(_data_managers),
        endpoints={
            "data": "/api/data",
            "init": "/api/data/init",
            "sessions": "/api/sessions",
            "status": "/api/status",
        },
    )
