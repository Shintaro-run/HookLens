#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HookLens - Webhook Debugger
Copyright (c) HookLens contributors - by LV3
"""

import argparse
import html
import json
import queue
import threading
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Global event queue for SSE
event_queues = []
event_queues_lock = threading.Lock()

# Store received webhooks
webhooks = []
webhooks_lock = threading.Lock()

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HookLens - Webhook Debugger</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Consolas', monospace;
            background-color: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #30363d;
        }
        h1 {
            font-size: 24px;
            font-weight: 600;
            color: #58a6ff;
        }
        .status {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #f85149;
            transition: background-color 0.3s;
        }
        .status-dot.connected {
            background-color: #3fb950;
        }
        .status-text {
            font-size: 14px;
            color: #8b949e;
        }
        .endpoint-section {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 24px;
        }
        .endpoint-label {
            font-size: 12px;
            color: #8b949e;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .endpoint-url {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .endpoint-url code {
            background-color: #0d1117;
            padding: 10px 14px;
            border-radius: 4px;
            font-size: 14px;
            color: #58a6ff;
            flex-grow: 1;
            border: 1px solid #30363d;
        }
        .copy-btn {
            background-color: #21262d;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 10px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-family: inherit;
            transition: background-color 0.2s, border-color 0.2s;
        }
        .copy-btn:hover {
            background-color: #30363d;
            border-color: #8b949e;
        }
        .copy-btn.copied {
            background-color: #238636;
            border-color: #238636;
        }
        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .logs-title {
            font-size: 16px;
            font-weight: 600;
        }
        .clear-btn {
            background-color: transparent;
            border: 1px solid #30363d;
            color: #8b949e;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-family: inherit;
            transition: background-color 0.2s, color 0.2s;
        }
        .clear-btn:hover {
            background-color: #21262d;
            color: #c9d1d9;
        }
        .test-btn {
            background-color: #238636;
            border: 1px solid #238636;
            color: #ffffff;
            padding: 10px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-family: inherit;
            transition: background-color 0.2s, border-color 0.2s;
        }
        .test-btn:hover {
            background-color: #2ea043;
            border-color: #2ea043;
        }
        .test-btn:disabled {
            background-color: #21262d;
            border-color: #30363d;
            color: #8b949e;
            cursor: not-allowed;
        }
        .no-requests {
            text-align: center;
            padding: 60px 20px;
            color: #8b949e;
            background-color: #161b22;
            border: 1px dashed #30363d;
            border-radius: 6px;
        }
        .no-requests-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
        .request-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .request-item {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow: hidden;
        }
        .request-header {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            transition: background-color 0.2s;
            gap: 12px;
        }
        .request-header:hover {
            background-color: #1c2128;
        }
        .expand-icon {
            color: #8b949e;
            font-size: 12px;
            transition: transform 0.2s;
            width: 16px;
        }
        .request-item.expanded .expand-icon {
            transform: rotate(90deg);
        }
        .method-badge {
            background-color: #238636;
            color: #ffffff;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .method-badge.get { background-color: #1f6feb; }
        .method-badge.post { background-color: #238636; }
        .method-badge.put { background-color: #9e6a03; }
        .method-badge.delete { background-color: #da3633; }
        .method-badge.patch { background-color: #8957e5; }
        .request-path {
            flex-grow: 1;
            font-size: 14px;
            color: #c9d1d9;
        }
        .request-timestamp {
            font-size: 12px;
            color: #8b949e;
        }
        .request-body {
            display: none;
            border-top: 1px solid #30363d;
        }
        .request-item.expanded .request-body {
            display: block;
        }
        .section {
            padding: 16px;
            border-bottom: 1px solid #30363d;
        }
        .section:last-child {
            border-bottom: none;
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .section-title {
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .headers-table {
            width: 100%;
            font-size: 13px;
        }
        .headers-table tr {
            border-bottom: 1px solid #21262d;
        }
        .headers-table tr:last-child {
            border-bottom: none;
        }
        .headers-table td {
            padding: 6px 0;
            vertical-align: top;
        }
        .headers-table td:first-child {
            color: #7ee787;
            padding-right: 16px;
            white-space: nowrap;
        }
        .headers-table td:last-child {
            color: #c9d1d9;
            word-break: break-all;
        }
        .json-content {
            background-color: #0d1117;
            padding: 16px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.5;
        }
        .json-key {
            color: #7ee787;
            cursor: pointer;
        }
        .json-key:hover {
            text-decoration: underline;
        }
        .json-string {
            color: #a5d6ff;
            cursor: pointer;
        }
        .json-string:hover {
            text-decoration: underline;
        }
        .json-number {
            color: #79c0ff;
            cursor: pointer;
        }
        .json-number:hover {
            text-decoration: underline;
        }
        .json-boolean {
            color: #ff7b72;
            cursor: pointer;
        }
        .json-boolean:hover {
            text-decoration: underline;
        }
        .json-null {
            color: #ff7b72;
            cursor: pointer;
        }
        .json-null:hover {
            text-decoration: underline;
        }
        .json-bracket {
            color: #8b949e;
        }
        .raw-body {
            background-color: #0d1117;
            padding: 16px;
            border-radius: 4px;
            white-space: pre-wrap;
            word-break: break-all;
            font-size: 13px;
            color: #c9d1d9;
        }
        .copy-toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #238636;
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 6px;
            font-size: 14px;
            opacity: 0;
            transform: translateY(10px);
            transition: opacity 0.3s, transform 0.3s;
            z-index: 1000;
        }
        .copy-toast.show {
            opacity: 1;
            transform: translateY(0);
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .request-item {
            animation: fadeIn 0.3s ease-out;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>&#128269; HookLens</h1>
            <div class="status">
                <div class="status-dot" id="statusDot"></div>
                <span class="status-text" id="statusText">Disconnected</span>
            </div>
        </header>

        <div class="endpoint-section">
            <div class="endpoint-label">Webhook Endpoint</div>
            <div class="endpoint-url">
                <code id="endpointUrl"></code>
                <button class="copy-btn" onclick="copyEndpoint()">Copy</button>
                <button class="test-btn" id="testBtn" onclick="sendTestWebhook()">Send Test</button>
            </div>
        </div>

        <div class="logs-section">
            <div class="logs-header">
                <span class="logs-title">Request Log</span>
                <button class="clear-btn" onclick="clearLogs()">Clear All</button>
            </div>
            <div id="requestList" class="request-list">
                <div class="no-requests" id="noRequests">
                    <div class="no-requests-icon">&#128229;</div>
                    <div>No requests yet</div>
                    <div style="margin-top: 8px; font-size: 12px;">Send a webhook to the endpoint above</div>
                </div>
            </div>
        </div>
    </div>

    <div class="copy-toast" id="copyToast">Copied to clipboard!</div>

    <script>
        let requests = [];
        let eventSource = null;

        function init() {
            const protocol = window.location.protocol;
            const host = window.location.host;
            document.getElementById('endpointUrl').textContent = protocol + '//' + host + '/webhook';
            connectSSE();
        }

        function connectSSE() {
            if (eventSource) {
                eventSource.close();
            }

            eventSource = new EventSource('/events');

            eventSource.onopen = function() {
                document.getElementById('statusDot').classList.add('connected');
                document.getElementById('statusText').textContent = 'Connected';
            };

            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'webhook') {
                    addRequest(data.payload);
                }
            };

            eventSource.onerror = function() {
                document.getElementById('statusDot').classList.remove('connected');
                document.getElementById('statusText').textContent = 'Disconnected';
                setTimeout(connectSSE, 3000);
            };
        }

        function addRequest(req) {
            requests.unshift(req);
            renderRequests();
        }

        function renderRequests() {
            const container = document.getElementById('requestList');
            const noRequests = document.getElementById('noRequests');

            if (requests.length === 0) {
                noRequests.style.display = 'block';
                container.innerHTML = '';
                container.appendChild(noRequests);
                return;
            }

            noRequests.style.display = 'none';
            container.innerHTML = requests.map((req, index) => createRequestHTML(req, index)).join('');
        }

        function createRequestHTML(req, index) {
            const methodClass = req.method.toLowerCase();
            const headersHTML = Object.entries(req.headers).map(([key, value]) =>
                '<tr><td>' + escapeHtml(key) + '</td><td>' + escapeHtml(value) + '</td></tr>'
            ).join('');

            let bodyHTML = '';
            if (req.body) {
                try {
                    const parsed = JSON.parse(req.body);
                    bodyHTML = formatJSON(parsed, '');
                } catch (e) {
                    bodyHTML = '<div class="raw-body" onclick="copyValue(this.textContent)">' + escapeHtml(req.body) + '</div>';
                }
            } else {
                bodyHTML = '<div class="raw-body" style="color: #8b949e;">(empty)</div>';
            }

            const headersJson = JSON.stringify(req.headers, null, 2);

            return '<div class="request-item" id="request-' + index + '">' +
                '<div class="request-header" onclick="toggleRequest(' + index + ')">' +
                    '<span class="expand-icon">&#9654;</span>' +
                    '<span class="method-badge ' + methodClass + '">' + escapeHtml(req.method) + '</span>' +
                    '<span class="request-path">' + escapeHtml(req.path) + '</span>' +
                    '<span class="request-timestamp">' + escapeHtml(req.timestamp) + '</span>' +
                '</div>' +
                '<div class="request-body">' +
                    '<div class="section">' +
                        '<div class="section-header">' +
                            '<span class="section-title">Headers</span>' +
                            '<button class="copy-btn" onclick="event.stopPropagation(); copyText(\'' + escapeJs(headersJson) + '\')">Copy</button>' +
                        '</div>' +
                        '<table class="headers-table"><tbody>' + headersHTML + '</tbody></table>' +
                    '</div>' +
                    '<div class="section">' +
                        '<div class="section-header">' +
                            '<span class="section-title">Body</span>' +
                            '<button class="copy-btn" onclick="event.stopPropagation(); copyText(\'' + escapeJs(req.body || '') + '\')">Copy</button>' +
                        '</div>' +
                        '<div class="json-content">' + bodyHTML + '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';
        }

        function formatJSON(obj, indent) {
            if (obj === null) {
                return '<span class="json-null" onclick="copyValue(\'null\')">null</span>';
            }
            if (typeof obj === 'boolean') {
                return '<span class="json-boolean" onclick="copyValue(\'' + obj + '\')">' + obj + '</span>';
            }
            if (typeof obj === 'number') {
                return '<span class="json-number" onclick="copyValue(\'' + obj + '\')">' + obj + '</span>';
            }
            if (typeof obj === 'string') {
                return '<span class="json-string" onclick="copyValue(\'' + escapeJs(obj) + '\')">"' + escapeHtml(obj) + '"</span>';
            }
            if (Array.isArray(obj)) {
                if (obj.length === 0) {
                    return '<span class="json-bracket">[]</span>';
                }
                const newIndent = indent + '  ';
                const items = obj.map(item => newIndent + formatJSON(item, newIndent)).join(',\\n');
                return '<span class="json-bracket">[</span>\\n' + items + '\\n' + indent + '<span class="json-bracket">]</span>';
            }
            if (typeof obj === 'object') {
                const keys = Object.keys(obj);
                if (keys.length === 0) {
                    return '<span class="json-bracket">{}</span>';
                }
                const newIndent = indent + '  ';
                const items = keys.map(key => {
                    const value = obj[key];
                    const valueStr = typeof value === 'string' ? value : JSON.stringify(value);
                    return newIndent + '<span class="json-key" onclick="copyValue(\'' + escapeJs(valueStr) + '\')">"' + escapeHtml(key) + '"</span>: ' + formatJSON(value, newIndent);
                }).join(',\\n');
                return '<span class="json-bracket">{</span>\\n' + items + '\\n' + indent + '<span class="json-bracket">}</span>';
            }
            return escapeHtml(String(obj));
        }

        function toggleRequest(index) {
            const item = document.getElementById('request-' + index);
            item.classList.toggle('expanded');
        }

        function copyEndpoint() {
            const url = document.getElementById('endpointUrl').textContent;
            copyToClipboard(url);
        }

        function copyText(text) {
            copyToClipboard(text);
        }

        function copyValue(value) {
            copyToClipboard(value);
        }

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!');
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        }

        function showToast(message) {
            const toast = document.getElementById('copyToast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2000);
        }

        function clearLogs() {
            requests = [];
            renderRequests();
        }

        function sendTestWebhook() {
            const btn = document.getElementById('testBtn');
            btn.disabled = true;
            btn.textContent = 'Sending...';

            const testPayload = {
                event: 'test.webhook',
                timestamp: new Date().toISOString(),
                data: {
                    message: 'This is a test webhook from HookLens',
                    id: Math.random().toString(36).substring(2, 10),
                    nested: {
                        number: 42,
                        boolean: true,
                        array: [1, 2, 3],
                        null_value: null
                    }
                }
            };

            fetch('/webhook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Test-Header': 'HookLens-Test',
                    'X-Request-Id': crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2)
                },
                body: JSON.stringify(testPayload)
            })
            .then(response => {
                if (response.ok) {
                    showToast('Test webhook sent!');
                } else {
                    showToast('Failed to send test webhook');
                }
            })
            .catch(err => {
                showToast('Error: ' + err.message);
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = 'Send Test';
            });
        }

        function escapeHtml(str) {
            if (str === null || str === undefined) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        function escapeJs(str) {
            if (str === null || str === undefined) return '';
            return String(str)
                .replace(/\\\\/g, '\\\\\\\\')
                .replace(/'/g, "\\\\'")
                .replace(/"/g, '\\\\"')
                .replace(/\\n/g, '\\\\n')
                .replace(/\\r/g, '\\\\r')
                .replace(/\\t/g, '\\\\t');
        }

        init();
    </script>
</body>
</html>
'''


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for webhook debugging."""

    def log_message(self, format, *args):
        """Override to suppress default logging."""
        pass

    def send_cors_headers(self):
        """Send CORS headers for cross-origin requests."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/':
            self.serve_gui()
        elif parsed_path.path == '/events':
            self.serve_sse()
        elif parsed_path.path == '/webhook':
            self.handle_webhook('GET')
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/webhook':
            self.handle_webhook('POST')
        else:
            self.send_error(404, 'Not Found')

    def do_PUT(self):
        """Handle PUT requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/webhook':
            self.handle_webhook('PUT')
        else:
            self.send_error(404, 'Not Found')

    def do_DELETE(self):
        """Handle DELETE requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/webhook':
            self.handle_webhook('DELETE')
        else:
            self.send_error(404, 'Not Found')

    def do_PATCH(self):
        """Handle PATCH requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/webhook':
            self.handle_webhook('PATCH')
        else:
            self.send_error(404, 'Not Found')

    def serve_gui(self):
        """Serve the HTML GUI."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

    def serve_sse(self):
        """Serve Server-Sent Events stream."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_cors_headers()
        self.end_headers()

        # Create a queue for this client
        client_queue = queue.Queue()

        with event_queues_lock:
            event_queues.append(client_queue)

        try:
            # Send initial connection event
            self.wfile.write(b'data: {"type": "connected"}\n\n')
            self.wfile.flush()

            # Send existing webhooks
            with webhooks_lock:
                for webhook in webhooks:
                    event_data = json.dumps({'type': 'webhook', 'payload': webhook})
                    self.wfile.write(f'data: {event_data}\n\n'.encode('utf-8'))
                    self.wfile.flush()

            # Wait for new events
            while True:
                try:
                    event = client_queue.get(timeout=30)
                    event_data = json.dumps(event)
                    self.wfile.write(f'data: {event_data}\n\n'.encode('utf-8'))
                    self.wfile.flush()
                except queue.Empty:
                    # Send keep-alive comment
                    self.wfile.write(b': keepalive\n\n')
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with event_queues_lock:
                if client_queue in event_queues:
                    event_queues.remove(client_queue)

    def handle_webhook(self, method):
        """Handle incoming webhook requests."""
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = ''
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8', errors='replace')

        # Collect headers
        headers_dict = {}
        for key, value in self.headers.items():
            headers_dict[key] = value

        # Create webhook data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        webhook_data = {
            'id': str(uuid.uuid4()),
            'timestamp': timestamp,
            'method': method,
            'path': self.path,
            'headers': headers_dict,
            'body': body
        }

        # Store webhook
        with webhooks_lock:
            webhooks.insert(0, webhook_data)
            # Keep only last 100 webhooks
            if len(webhooks) > 100:
                webhooks.pop()

        # Broadcast to all SSE clients
        event = {'type': 'webhook', 'payload': webhook_data}
        with event_queues_lock:
            for q in event_queues:
                try:
                    q.put_nowait(event)
                except queue.Full:
                    pass

        # Log to console
        print(f'[{timestamp}] {method} {self.path}')

        # Send response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        response = {'status': 'received', 'id': webhook_data['id']}
        self.wfile.write(json.dumps(response).encode('utf-8'))


class ThreadedHTTPServer(HTTPServer):
    """HTTP server that handles each request in a separate thread."""

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        thread = threading.Thread(target=self.process_request_thread, args=(request, client_address))
        thread.daemon = True
        thread.start()

    def process_request_thread(self, request, client_address):
        """Process the request in a thread."""
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='HookLens - Webhook Debugger',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python hooklens.py              Start server on port 8080
  python hooklens.py --port 9000  Start server on port 9000

Endpoints:
  GET  /          Web GUI
  GET  /events    SSE stream for real-time updates
  POST /webhook   Receive webhooks (also supports GET, PUT, DELETE, PATCH)
'''
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Port to listen on (default: 8080)'
    )
    args = parser.parse_args()

    server_address = ('', args.port)
    httpd = ThreadedHTTPServer(server_address, WebhookHandler)

    print(f'''
╔═══════════════════════════════════════════════════════════════╗
║                    HookLens - Webhook Debugger                ║
╠═══════════════════════════════════════════════════════════════╣
║  GUI:      http://localhost:{args.port:<5}                            ║
║  Webhook:  http://localhost:{args.port:<5}/webhook                    ║
╚═══════════════════════════════════════════════════════════════╝
''')
    print('Press Ctrl+C to stop the server\n')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down server...')
        httpd.shutdown()


if __name__ == '__main__':
    main()
