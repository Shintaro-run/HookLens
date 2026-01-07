# HookLens

A lightweight webhook debugger that receives webhooks locally and displays them in a real-time browser GUI.

## Architecture

```
┌──────────────┐    Webhook (POST)     ┌──────────────────┐
│ External     │ ───────────────────▶ │                  │
│ System       │                       │  Python Server   │
│ (Source)     │                       │  (HookLens)      │
└──────────────┘                       │                  │
                                       │                  │
┌──────────────┐    SSE (GET)          │                  │
│ Browser      │ ◀─────────────────── │                  │
│ (GUI)        │                       │                  │
└──────────────┘                       └──────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Server | Python 3.7+ (standard library only) |
| HTTP Server | `http.server.HTTPServer` |
| Real-time | Server-Sent Events (SSE) |
| Threading | `threading` module |
| Frontend | Embedded HTML/CSS/JavaScript |
| Styling | Dark theme, CSS3 |

**Zero Dependencies**: No pip install required. Uses only Python standard library modules:
- `http.server` - HTTP request handling
- `json` - JSON parsing and serialization
- `threading` - Concurrent request handling
- `queue` - Thread-safe event queue for SSE
- `datetime` - Timestamp generation
- `argparse` - Command-line argument parsing
- `html` - HTML escaping
- `uuid` - Unique request ID generation

## Features

- **Real-time Display**: Webhooks appear instantly via Server-Sent Events (SSE)
- **Zero Dependencies**: Uses only Python standard library (no pip install required)
- **Dark Mode UI**: Clean, modern interface with monospace fonts
- **JSON Formatting**: Automatic pretty-printing with syntax highlighting
- **Copy Functionality**: One-click copy for URLs, headers, body, and individual JSON values
- **Accordion View**: Expandable/collapsible request details
- **Multi-method Support**: Handles GET, POST, PUT, DELETE, and PATCH requests
- **Built-in Test**: Send test webhooks directly from the UI

## Requirements

- Python 3.7 or higher

## Installation

No installation required. Simply download `hooklens.py` and run it.

```bash
git clone git@github.com:Shintaro-run/HookLens.git
cd HookLens
```

## Usage

### Start the server

```bash
# Default port (8080)
python hooklens.py

# Custom port
python hooklens.py --port 9000
```

### Access the GUI

Open your browser and navigate to:
```
http://localhost:8080
```

### Send webhooks

Send webhooks to:
```
http://localhost:8080/webhook
```

Example with curl:
```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "user.created", "data": {"id": 123, "name": "John"}}'
```

### Test Button

Click the **Send Test** button in the GUI to instantly send a sample webhook. This allows you to verify the setup is working without any external tools.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web GUI |
| GET | `/events` | SSE stream for real-time updates |
| POST | `/webhook` | Receive webhooks |
| GET | `/webhook` | Receive webhooks (also supported) |
| PUT | `/webhook` | Receive webhooks (also supported) |
| DELETE | `/webhook` | Receive webhooks (also supported) |
| PATCH | `/webhook` | Receive webhooks (also supported) |

## GUI Features

### Request Display
- Timestamp
- HTTP method (color-coded badge)
- Request path
- Headers table
- Body with JSON syntax highlighting

### Copy Functions
- **Endpoint URL**: Copy the webhook endpoint URL
- **Headers**: Copy all headers as JSON
- **Body**: Copy the entire request body
- **JSON Values**: Click any key or value to copy it

### Controls
- **Send Test**: Send a test webhook to verify setup
- **Clear All**: Remove all logged requests
- **Accordion**: Click request header to expand/collapse details

## Screenshots

The interface features:
- Dark theme (background: #0d1117, text: #c9d1d9)
- Connection status indicator
- Endpoint URL display with copy and test buttons
- Request list with expandable details

## License

Copyright (c) HookLens contributors - by LV3
