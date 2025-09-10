# WebSocket API Documentation

## Overview

The KrathongScanner WebSocket API provides real-time communication between the ArUco detection system and Unity clients. This API enables low-latency transmission of marker detection data, pose information, and system status updates.

## Connection Details

- **Protocol**: WebSocket (ws:// or wss://)
- **Default Host**: localhost
- **Default Port**: 8765
- **Connection Type**: Persistent connection with heartbeat

## Message Format

All messages use JSON format with the following structure:

```json
{
  "type": "message_type",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {},
  "id": "unique_message_id"
}
```

## Message Types

### 1. Marker Detection (`marker_detected`)

Sent when ArUco markers are detected in the camera view.

```json
{
  "type": "marker_detected",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "markers": [
      {
        "id": 1,
        "corners": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
        "center": [x, y],
        "pose": {
          "translation": [x, y, z],
          "rotation": [rx, ry, rz]
        },
        "confidence": 0.95
      }
    ],
    "frame_info": {
      "width": 640,
      "height": 480,
      "fps": 30
    }
  },
  "id": "msg_001"
}
```

### 2. System Status (`system_status`)

Periodic updates about system health and performance.

```json
{
  "type": "system_status",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "status": "running",
    "uptime": 3600,
    "fps": 30.5,
    "markers_detected": 3,
    "camera_status": "active",
    "memory_usage": "45%"
  },
  "id": "msg_002"
}
```

### 3. Error Notification (`error`)

Sent when errors occur in the system.

```json
{
  "type": "error",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "error_code": "CAMERA_ERROR",
    "message": "Camera connection lost",
    "severity": "warning"
  },
  "id": "msg_003"
}
```

### 4. Heartbeat (`heartbeat`)

Regular ping to maintain connection and measure latency.

```json
{
  "type": "heartbeat",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "sequence": 42
  },
  "id": "msg_004"
}
```

## Client Messages

### 1. Subscribe (`subscribe`)

Client can subscribe to specific message types.

```json
{
  "type": "subscribe",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "topics": ["marker_detected", "system_status"]
  },
  "id": "client_001"
}
```

### 2. Unsubscribe (`unsubscribe`)

Client can unsubscribe from specific message types.

```json
{
  "type": "unsubscribe",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "topics": ["system_status"]
  },
  "id": "client_002"
}
```

### 3. Configuration Update (`config_update`)

Client can request configuration changes.

```json
{
  "type": "config_update",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "detection_interval": 0.05,
    "pose_estimation": true
  },
  "id": "client_003"
}
```

## Connection Management

### Connection Lifecycle

1. **Connect**: Client establishes WebSocket connection
2. **Handshake**: Server sends welcome message with connection ID
3. **Subscribe**: Client subscribes to desired message types
4. **Data Flow**: Continuous message exchange
5. **Heartbeat**: Regular ping/pong to maintain connection
6. **Disconnect**: Client closes connection or connection times out

### Reconnection Strategy

- Client should implement exponential backoff for reconnection attempts
- Maximum reconnection attempts: 5 (configurable)
- Reconnection timeout: 60 seconds (configurable)

## Error Handling

### Common Error Codes

- `CONNECTION_ERROR`: WebSocket connection issues
- `CAMERA_ERROR`: Camera hardware or driver problems
- `DETECTION_ERROR`: ArUco detection algorithm errors
- `CONFIGURATION_ERROR`: Invalid configuration parameters
- `PERMISSION_ERROR`: Insufficient permissions

### Error Severity Levels

- `info`: Informational messages
- `warning`: Non-critical issues
- `error`: Critical errors that may affect functionality
- `critical`: System-breaking errors

## Performance Considerations

- **Message Frequency**: Marker detection messages sent at camera FPS (typically 30 FPS)
- **Message Size**: Average message size: 1-5 KB
- **Latency**: Target latency: < 50ms
- **Bandwidth**: Estimated usage: 100-500 KB/s per client

## Unity Integration

### Unity WebSocket Client

```csharp
using WebSocketSharp;
using Newtonsoft.Json;

public class KrathongScannerClient : MonoBehaviour
{
    private WebSocket webSocket;

    void Start()
    {
        webSocket = new WebSocket("ws://localhost:8765");
        webSocket.OnMessage += OnMessage;
        webSocket.Connect();
    }

    void OnMessage(object sender, MessageEventArgs e)
    {
        var message = JsonConvert.DeserializeObject<WebSocketMessage>(e.Data);
        ProcessMessage(message);
    }
}
```

### Message Processing

```csharp
private void ProcessMessage(WebSocketMessage message)
{
    switch (message.type)
    {
        case "marker_detected":
            ProcessMarkerData(message.data);
            break;
        case "system_status":
            UpdateSystemStatus(message.data);
            break;
        case "error":
            HandleError(message.data);
            break;
    }
}
```

## Testing

### Test Endpoints

- **Development**: ws://localhost:8765
- **Staging**: ws://staging.example.com:8765
- **Production**: wss://api.example.com:8765

### Test Tools

- **WebSocket Client**: Use browser developer tools or tools like Postman
- **Load Testing**: Use tools like Artillery or custom scripts
- **Message Validation**: Validate JSON schema compliance
