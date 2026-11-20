"""
WebSocket & Server-Sent Events (SSE) router for live dashboard updates.
Streams new_scan, bin_update, agent_log, discount_offer, and heartbeat events.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import asyncio
import json
from app.api.event_bus import event_bus

router = APIRouter(prefix="", tags=["Live Event Streaming"])


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """WebSocket stream for real-time live events and notifications."""
    await websocket.accept()
    queue = await event_bus.subscribe()
    try:
        while True:
            # Wait for event or heartbeat timeout
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                await websocket.send_text(json.dumps(msg))
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat", "time": asyncio.get_event_loop().time()}))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await event_bus.unsubscribe(queue)


@router.get("/sse/events")
async def sse_events_endpoint():
    """Server-Sent Events fallback for real-time frontend streaming."""
    async def event_generator():
        queue = await event_bus.subscribe()
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
        finally:
            await event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

