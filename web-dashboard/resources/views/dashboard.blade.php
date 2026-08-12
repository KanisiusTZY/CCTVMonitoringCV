<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>CCTV Dashboard</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-card: rgba(30, 41, 59, 0.7);
            --bg-card-hover: rgba(51, 65, 85, 0.8);
            --border-color: rgba(255, 255, 255, 0.1);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-purple: #818cf8;
            --accent-emerald: #10b981;
            --accent-rose: #f43f5e;
            --accent-amber: #f59e0b;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(129, 140, 248, 0.12) 0px, transparent 50%);
            background-attachment: fixed;
            padding-bottom: 40px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 40px;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 500;
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-emerald);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent-emerald);
            box-shadow: 0 0 10px var(--accent-emerald);
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }

        .container {
            max-width: 1440px;
            margin: 30px auto;
            padding: 0 30px;
        }

        .grid-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            border-color: rgba(56, 189, 248, 0.4);
            box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.5);
        }

        .stat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        .stat-value {
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-main);
        }

        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }

        .icon-blue { background: rgba(56, 189, 248, 0.15); color: var(--accent-blue); }
        .icon-purple { background: rgba(129, 140, 248, 0.15); color: var(--accent-purple); }
        .icon-emerald { background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); }
        .icon-amber { background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); }

        .main-layout {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }

        @media (max-width: 1024px) {
            .main-layout {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 28px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }

        .panel-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.25rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .video-container {
            width: 100%;
            border-radius: 14px;
            overflow: hidden;
            background: #000;
            position: relative;
            aspect-ratio: 16 / 9;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }

        .video-feed-overlay {
            position: absolute;
            top: 15px;
            left: 15px;
            display: flex;
            gap: 10px;
            z-index: 10;
        }

        .badge-live {
            background: rgba(244, 63, 94, 0.85);
            color: #fff;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .log-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 400px;
            overflow-y: auto;
            padding-right: 6px;
        }

        .log-list::-webkit-scrollbar {
            width: 6px;
        }
        .log-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
        }

        .log-item {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
        }

        .log-item:hover {
            background: rgba(30, 41, 59, 0.9);
            border-color: rgba(56, 189, 248, 0.3);
        }

        .log-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .log-zone {
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--accent-blue);
        }

        .log-time {
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .log-event {
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .event-enter { background: rgba(16, 185, 129, 0.2); color: var(--accent-emerald); }
        .event-exit { background: rgba(245, 158, 11, 0.2); color: var(--accent-amber); }
        .event-violation { background: rgba(244, 63, 94, 0.2); color: var(--accent-rose); }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 16px;
        }

        .form-label {
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-muted);
        }

        .form-input {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 10px 14px;
            color: var(--text-main);
            font-family: inherit;
            font-size: 0.9rem;
            transition: border-color 0.2s ease;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-blue);
        }

        .btn-primary {
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            color: #fff;
            border: none;
            border-radius: 10px;
            padding: 12px 20px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.25);
        }

        .btn-primary:hover {
            opacity: 0.95;
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(56, 189, 248, 0.35);
        }

        .toast {
            position: fixed;
            bottom: 25px;
            right: 25px;
            background: rgba(16, 185, 129, 0.95);
            color: #fff;
            padding: 14px 24px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.68, -0.55, 0.27, 1.55);
            z-index: 1000;
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>

    <!-- Header Navigation -->
    <header class="header">
        <div class="header-title">
            <i class="fa-solid fa-video"></i>
            <span>CCTV Analytics & Monitoring</span>
        </div>
        <div style="display: flex; gap: 15px; align-items: center;">
            <div class="status-badge">
                <span class="pulse-dot"></span>
                <span>Laravel Framework v9.x Active</span>
            </div>
            <div class="status-badge" style="background: rgba(129, 140, 248, 0.15); color: var(--accent-purple); border-color: rgba(129, 140, 248, 0.3);">
                <i class="fa-solid fa-brain"></i>
                <span>YOLOv8 Engine Ready</span>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- Key Metrics Grid -->
        <div class="grid-stats">
            <div class="stat-card">
                <div class="stat-header">
                    <span>Active Camera Source</span>
                    <div class="stat-icon icon-blue"><i class="fa-solid fa-camera"></i></div>
                </div>
                <div class="stat-value" id="stat-source">{{ $config['source'] ?? 'm.mp4' }}</div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <span>Active Chair Zones</span>
                    <div class="stat-icon icon-purple"><i class="fa-solid fa-chair"></i></div>
                </div>
                <div class="stat-value">{{ $activeZonesCount }} Zones</div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <span>Total Recorded Incidents</span>
                    <div class="stat-icon icon-amber"><i class="fa-solid fa-bell"></i></div>
                </div>
                <div class="stat-value" id="stat-incidents">{{ $totalIncidents }}</div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <span>AI Model Confidence</span>
                    <div class="stat-icon icon-emerald"><i class="fa-solid fa-sliders"></i></div>
                </div>
                <div class="stat-value" id="stat-conf">{{ ($config['confidence'] ?? 0.1) * 100 }}%</div>
            </div>
        </div>

        <!-- Main Workspace Layout -->
        <div class="main-layout">
            <!-- Left Column: Video Feed & Zone Overview -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">
                        <i class="fa-solid fa-display" style="color: var(--accent-blue);"></i>
                        <span>Live Video Stream & Detection Feed</span>
                    </div>
                    <span style="font-size: 0.85rem; color: var(--text-muted);">Source: {{ $config['source'] ?? 'm.mp4' }}</span>
                </div>

                <div class="video-container">
                    <div class="video-feed-overlay">
                        <div class="badge-live" id="streamLiveBadge">
                            <span class="pulse-dot" style="background: #fff; box-shadow: none;"></span>
                            LIVE AI CV STREAM
                        </div>
                        <span id="streamStatusText" style="background: rgba(15,23,42,0.85); color: var(--accent-blue); padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; border: 1px solid var(--border-color);">
                            Connecting Python AI Engine...
                        </span>
                    </div>

                    <!-- Live MJPEG Stream from Python Engine (Local or Remote Colab via Proxy) -->
                    <img id="mjpegFeed" src="/stream-proxy" style="width: 100%; height: 100%; object-fit: contain; display: block;">

                    <!-- Offline Screen Overlay when Python Engine is stopped -->
                    <div id="offlineOverlay" style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.95); gap: 14px; padding: 40px; text-align: center;">
                        <div style="width: 60px; height: 60px; border-radius: 50%; background: rgba(244, 63, 94, 0.12); color: var(--accent-rose); display: flex; align-items: center; justify-content: center; font-size: 1.6rem; border: 1px solid rgba(244, 63, 94, 0.25);">
                            <i class="fa-solid fa-video-slash"></i>
                        </div>
                        <h3 style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 700; color: #f8fafc;">Stream Tidak Tersedia</h3>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">
                            Silakan aktifkan service monitoring AI untuk melihat stream live.
                        </p>
                    </div>
                </div>

                <!-- Active Zone Details List -->
                <div style="margin-top: 10px;">
                    <h4 style="font-size: 1rem; margin-bottom: 12px; color: var(--text-muted);">Configured Detection Zones ({{ $activeZonesCount }})</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;" id="zoneBadgeList">
                        @if(isset($config['chair_zones']))
                            @foreach($config['chair_zones'] as $zone)
                                <span style="background: rgba(51, 65, 85, 0.7); border: 1px solid var(--border-color); padding: 6px 12px; border-radius: 8px; font-size: 0.85rem;">
                                    <i class="fa-solid fa-chair" style="color: var(--accent-blue); margin-right: 6px;"></i>
                                    {{ $zone['id'] }}
                                </span>
                            @endforeach
                        @endif
                    </div>
                </div>
            </div>

            <!-- Right Column: Real-time Incident Feed & Rules Configurator -->
            <div style="display: flex; flex-direction: column; gap: 30px;">
                <!-- Realtime Incident Logs -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <i class="fa-solid fa-clock-rotate-left" style="color: var(--accent-amber);"></i>
                            <span>Recent Incident Logs</span>
                        </div>
                        <i class="fa-solid fa-arrows-rotate" style="color: var(--text-muted); cursor: pointer;" onclick="refreshLogs()" title="Refresh Logs"></i>
                    </div>

                    <div class="log-list" id="logContainer">
                        @forelse($logs as $log)
                            <div class="log-item">
                                <div class="log-info">
                                    <span class="log-zone">{{ $log->zone_id }}</span>
                                    <span class="log-time">{{ $log->created_at->diffForHumans() }}</span>
                                </div>
                                <span class="log-event {{ $log->event_type == 'ENTER' ? 'event-enter' : ($log->event_type == 'EXIT' ? 'event-exit' : 'event-violation') }}">
                                    {{ $log->event_type }}
                                </span>
                            </div>
                        @empty
                            <div style="text-align: center; color: var(--text-muted); padding: 30px 0;">
                                <i class="fa-regular fa-folder-open" style="font-size: 2rem; margin-bottom: 8px; opacity: 0.5;"></i>
                                <p>No detection logs recorded yet.</p>
                            </div>
                        @endforelse
                    </div>
                </div>

                <!-- Detection Threshold Rules Configurator -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <i class="fa-solid fa-sliders" style="color: var(--accent-purple);"></i>
                            <span>Detection Rule Settings</span>
                        </div>
                    </div>

                    <form id="configForm">
                        <div class="form-group">
                            <label class="form-label">Video Source File</label>
                            <input type="text" class="form-input" id="cfg-source" name="source" value="{{ $config['source'] ?? 's.mp4' }}">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Custom Stream URL / Ngrok URL (Opsional)</label>
                            <input type="text" class="form-input" id="cfg-stream-url" name="stream_url" value="{{ $config['stream_url'] ?? '' }}" placeholder="misal: https://xxxx.ngrok-free.app/video_feed">
                            <small style="margin-top: 4px; display: block;"><a id="directStreamLink" href="{{ $config['stream_url'] ?? '#' }}" target="_blank" style="color: var(--accent-blue); text-decoration: underline;">[Klik di sini 1x jika Cloudflare/Ngrok minta konfirmasi akses]</a></small>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div class="form-group">
                                <label class="form-label">Confidence Threshold</label>
                                <input type="number" step="0.05" min="0.05" max="1.0" class="form-input" id="cfg-confidence" name="confidence" value="{{ $config['confidence'] ?? 0.1 }}">
                            </div>

                            <div class="form-group">
                                <label class="form-label">Enter Threshold (s)</label>
                                <input type="number" step="0.1" class="form-input" id="cfg-enter" name="enter_seconds" value="{{ $config['enter_seconds'] ?? 2 }}">
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div class="form-group">
                                <label class="form-label">Exit Threshold (s)</label>
                                <input type="number" step="0.1" class="form-input" id="cfg-exit" name="exit_seconds" value="{{ $config['exit_seconds'] ?? 0.5 }}">
                            </div>

                            <div class="form-group">
                                <label class="form-label">Miss Tolerance (s)</label>
                                <input type="number" step="0.1" class="form-input" id="cfg-miss" name="miss_tolerance_seconds" value="{{ $config['miss_tolerance_seconds'] ?? 0.5 }}">
                            </div>
                        </div>

                        <button type="submit" class="btn-primary" style="width: 100%; margin-top: 10px;">
                            <i class="fa-solid fa-floppy-disk"></i>
                            Save Config Settings
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Notification Toast -->
    <div class="toast" id="toast">
        <i class="fa-solid fa-circle-check"></i>
        <span id="toastMsg">Settings updated successfully!</span>
    </div>

    <script>
        // Update Config via AJAX
        document.getElementById('configForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const payload = {
                source: document.getElementById('cfg-source').value,
                stream_url: document.getElementById('cfg-stream-url').value,
                confidence: parseFloat(document.getElementById('cfg-confidence').value),
                enter_seconds: parseFloat(document.getElementById('cfg-enter').value),
                exit_seconds: parseFloat(document.getElementById('cfg-exit').value),
                miss_tolerance_seconds: parseFloat(document.getElementById('cfg-miss').value)
            };

            fetch('/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'success') {
                    showToast('Configuration updated & synced!');
                    document.getElementById('stat-source').innerText = data.config.source;
                    document.getElementById('stat-conf').innerText = (data.config.confidence * 100) + '%';
                    checkStreamStatus();
                }
            })
            .catch(err => {
                showToast('Failed to update config!', true);
            });
        });

        // Refresh Logs
        function refreshLogs() {
            fetch('/logs')
            .then(res => res.json())
            .then(data => {
                const container = document.getElementById('logContainer');
                document.getElementById('stat-incidents').innerText = data.total;
                
                if(!data.logs || data.logs.length === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; color: var(--text-muted); padding: 30px 0;">
                            <i class="fa-regular fa-folder-open" style="font-size: 2rem; margin-bottom: 8px; opacity: 0.5;"></i>
                            <p>No detection logs recorded yet.</p>
                        </div>`;
                    return;
                }

                let html = '';
                data.logs.forEach(log => {
                    const badgeClass = log.event_type === 'ENTER' ? 'event-enter' : (log.event_type === 'EXIT' ? 'event-exit' : 'event-violation');
                    html += `
                        <div class="log-item">
                            <div class="log-info">
                                <span class="log-zone">${log.zone_id}</span>
                                <span class="log-time">${new Date(log.created_at).toLocaleTimeString()}</span>
                            </div>
                            <span class="log-event ${badgeClass}">
                                ${log.event_type}
                            </span>
                        </div>`;
                });
                container.innerHTML = html;
            });
        }

        // Auto Refresh Logs every 5 seconds
        setInterval(refreshLogs, 5000);

        let isFetchingFrame = false;

        function rtrim(str, ch) {
            let res = str;
            while (res.length > 0 && res.endsWith(ch)) {
                res = res.substring(0, res.length - 1);
            }
            return res;
        }

        function fetchNextStreamFrame() {
            if (isFetchingFrame) return;
            isFetchingFrame = true;

            const customUrl = document.getElementById('cfg-stream-url').value.trim();
            const targetImg = document.getElementById('mjpegFeed');
            const offlineOverlay = document.getElementById('offlineOverlay');
            const statusTxt = document.getElementById('streamStatusText');
            const liveBadge = document.getElementById('streamLiveBadge');

            let frameUrl = '/current-frame-proxy?t=' + Date.now();

            if (customUrl) {
                const baseUrl = customUrl.replace(/\/video_feed|\/status|\/current_frame\.jpg$/g, '');
                frameUrl = rtrim(baseUrl, '/') + '/current_frame.jpg?t=' + Date.now();
            }

            const tempImg = new Image();
            // DO NOT set crossOrigin (standard HTML img bypasses CORS rules)
            tempImg.onload = () => {
                targetImg.src = tempImg.src;
                targetImg.style.display = 'block';
                offlineOverlay.style.display = 'none';
                if (liveBadge) liveBadge.style.display = 'flex';

                if (customUrl) {
                    statusTxt.innerText = 'Remote Colab GPU Live Feed Active (Direct HTTP/2 20+ FPS)';
                    statusTxt.style.color = '#10b981';
                } else {
                    statusTxt.innerText = 'Python YOLOv8 AI Feed Online (Port 5000)';
                    statusTxt.style.color = '#10b981';
                }

                isFetchingFrame = false;
                requestAnimationFrame(fetchNextStreamFrame);
            };

            tempImg.onerror = () => {
                isFetchingFrame = false;
                setTimeout(fetchNextStreamFrame, 40);
            };

            tempImg.src = frameUrl;
        }

        fetchNextStreamFrame();

        function showOfflineScreen() {
            const img = document.getElementById('mjpegFeed');
            const offlineOverlay = document.getElementById('offlineOverlay');
            const statusTxt = document.getElementById('streamStatusText');
            const liveBadge = document.getElementById('streamLiveBadge');
            img.removeAttribute('src');
            img.style.display = 'none';
            offlineOverlay.style.display = 'flex';
            if (liveBadge) liveBadge.style.display = 'none';
            statusTxt.innerText = 'Stream Tidak Tersedia';
            statusTxt.style.color = '#f43f5e';
        }

        setInterval(checkStreamStatus, 2000);
        checkStreamStatus();

        function showToast(msg, isError = false) {
            const toast = document.getElementById('toast');
            const toastMsg = document.getElementById('toastMsg');
            toastMsg.innerText = msg;
            toast.style.background = isError ? 'rgba(244, 63, 94, 0.95)' : 'rgba(16, 185, 129, 0.95)';
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }
    </script>
</body>
</html>
