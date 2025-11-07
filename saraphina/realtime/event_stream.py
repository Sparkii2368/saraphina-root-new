"""
Real-Time Event Stream with WebSocket support.
Provides live telemetry, recovery progress, and push notifications.
"""
import asyncio
import json
import time
from typing import Dict, Set, Any, Optional, List
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict
import uuid


@dataclass
class Event:
    """System event for streaming"""
    event_id: str
    event_type: str  # telemetry, recovery_progress, alert, notification
    timestamp: float
    device_id: Optional[str]
    user_id: Optional[str]
    data: Dict[str, Any]
    priority: int = 0  # 0=low, 1=medium, 2=high, 3=critical


class EventBus:
    """Central event bus for pub/sub"""
    def __init__(self):
        self.subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self.history: List[Event] = []
        self.max_history = 1000
    
    def subscribe(self, channel: str) -> asyncio.Queue:
        """Subscribe to event channel"""
        queue = asyncio.Queue(maxsize=100)
        self.subscribers[channel].add(queue)
        return queue
    
    def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """Unsubscribe from channel"""
        if channel in self.subscribers:
            self.subscribers[channel].discard(queue)
    
    async def publish(self, event: Event, channels: List[str]):
        """Publish event to multiple channels"""
        self.history.append(event)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        for channel in channels:
            if channel in self.subscribers:
                dead_queues = set()
                for queue in self.subscribers[channel]:
                    try:
                        await asyncio.wait_for(queue.put(event), timeout=1.0)
                    except asyncio.TimeoutError:
                        dead_queues.add(queue)
                    except Exception:
                        dead_queues.add(queue)
                
                # Clean up dead queues
                for dq in dead_queues:
                    self.subscribers[channel].discard(dq)
    
    def get_history(self, channel: Optional[str] = None, since: Optional[float] = None) -> List[Event]:
        """Get event history"""
        events = self.history
        if since:
            events = [e for e in events if e.timestamp >= since]
        # Channel filtering would require metadata on events
        return events


class WebSocketManager:
    """Manages WebSocket connections and streaming"""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.connections: Dict[str, Dict[str, Any]] = {}  # connection_id -> {ws, user_id, channels}
    
    async def connect(self, connection_id: str, websocket, user_id: str, channels: List[str]):
        """Register new WebSocket connection"""
        queues = {ch: self.event_bus.subscribe(ch) for ch in channels}
        self.connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "channels": channels,
            "queues": queues,
            "connected_at": time.time()
        }
    
    async def disconnect(self, connection_id: str):
        """Clean up WebSocket connection"""
        if connection_id in self.connections:
            conn = self.connections[connection_id]
            for ch, queue in conn["queues"].items():
                self.event_bus.unsubscribe(ch, queue)
            del self.connections[connection_id]
    
    async def stream_to_client(self, connection_id: str):
        """Stream events to WebSocket client"""
        if connection_id not in self.connections:
            return
        
        conn = self.connections[connection_id]
        ws = conn["websocket"]
        
        # Merge all queues for this connection
        while True:
            try:
                # Wait for events from any subscribed channel
                tasks = [queue.get() for queue in conn["queues"].values()]
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                for task in done:
                    event = task.result()
                    await ws.send_json(asdict(event))
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                
            except Exception as e:
                print(f"Stream error for {connection_id}: {e}")
                await self.disconnect(connection_id)
                break


class PushNotificationService:
    """Push notification abstraction (FCM, APNS, etc.)"""
    def __init__(self):
        self.device_tokens: Dict[str, List[str]] = defaultdict(list)  # user_id -> [tokens]
        self.sent_notifications: List[Dict] = []
    
    def register_device_token(self, user_id: str, token: str, platform: str):
        """Register push notification token"""
        if token not in self.device_tokens[user_id]:
            self.device_tokens[user_id].append(token)
    
    async def send_push(self, user_id: str, title: str, body: str, data: Optional[Dict] = None):
        """Send push notification (mock implementation)"""
        tokens = self.device_tokens.get(user_id, [])
        if not tokens:
            return {"status": "no_tokens", "user_id": user_id}
        
        notification = {
            "notification_id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "body": body,
            "data": data or {},
            "tokens": tokens,
            "sent_at": time.time()
        }
        self.sent_notifications.append(notification)
        
        # In production: integrate with FCM, APNS, etc.
        # await fcm_client.send(tokens, title, body, data)
        
        return {"status": "sent", "notification_id": notification["notification_id"]}
    
    async def send_to_multiple_users(self, user_ids: List[str], title: str, body: str, data: Optional[Dict] = None):
        """Broadcast notification to multiple users"""
        results = []
        for user_id in user_ids:
            result = await self.send_push(user_id, title, body, data)
            results.append(result)
        return results


class EventStreamOrchestrator:
    """Coordinates real-time events, WebSocket, and push notifications"""
    def __init__(self):
        self.event_bus = EventBus()
        self.ws_manager = WebSocketManager(self.event_bus)
        self.push_service = PushNotificationService()
    
    async def emit_telemetry(self, device_id: str, user_id: str, telemetry_data: Dict):
        """Emit device telemetry event"""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type="telemetry",
            timestamp=time.time(),
            device_id=device_id,
            user_id=user_id,
            data=telemetry_data,
            priority=0
        )
        await self.event_bus.publish(event, channels=["telemetry", f"user:{user_id}", f"device:{device_id}"])
    
    async def emit_recovery_progress(self, session_id: str, device_id: str, user_id: str, step: Dict):
        """Emit recovery progress update"""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type="recovery_progress",
            timestamp=time.time(),
            device_id=device_id,
            user_id=user_id,
            data={"session_id": session_id, "step": step},
            priority=2
        )
        await self.event_bus.publish(event, channels=["recovery", f"user:{user_id}", f"session:{session_id}"])
        
        # Send push notification for critical steps
        if step.get("status") == "success":
            await self.push_service.send_push(
                user_id,
                "Device Located!",
                f"Found your device using {step.get('method', 'recovery')}",
                data={"session_id": session_id, "device_id": device_id}
            )
    
    async def emit_alert(self, device_id: str, user_id: str, alert_type: str, message: str, metadata: Optional[Dict] = None):
        """Emit system alert"""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type="alert",
            timestamp=time.time(),
            device_id=device_id,
            user_id=user_id,
            data={"alert_type": alert_type, "message": message, "metadata": metadata or {}},
            priority=3
        )
        await self.event_bus.publish(event, channels=["alerts", f"user:{user_id}"])
        
        # Always push critical alerts
        if alert_type in ["geofence_breach", "device_lost", "tamper_detected"]:
            await self.push_service.send_push(
                user_id,
                f"Alert: {alert_type.replace('_', ' ').title()}",
                message,
                data={"device_id": device_id, "alert_type": alert_type}
            )
    
    async def emit_notification(self, user_id: str, title: str, body: str, channels: Optional[List[str]] = None):
        """Emit generic notification"""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type="notification",
            timestamp=time.time(),
            device_id=None,
            user_id=user_id,
            data={"title": title, "body": body},
            priority=1
        )
        target_channels = channels or [f"user:{user_id}"]
        await self.event_bus.publish(event, channels=target_channels)


# Global singleton
_orchestrator = None

def get_event_orchestrator() -> EventStreamOrchestrator:
    """Get global event orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EventStreamOrchestrator()
    return _orchestrator
