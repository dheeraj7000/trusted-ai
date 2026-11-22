"""Data send tool implementation."""

from datetime import datetime

from app.models import DataSendRequest, ToolResult


def execute_data_send(request: DataSendRequest) -> ToolResult:
    """Simulate sending data to a destination."""
    return ToolResult(
        tool="data_send",
        success=True,
        result={
            "destination": request.destination,
            "bytes_sent": len(request.payload),
            "timestamp": datetime.utcnow().isoformat(),
        },
        blocked=False,
    )
