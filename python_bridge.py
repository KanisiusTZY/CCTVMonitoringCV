import urllib.request
import json
import threading

LARAVEL_API_URL = "http://localhost:8000/api/incidents"

def _send_async(zone_id: str, event_type: str, person_count: int = 1, duration_seconds: float = None, description: str = ""):
    payload = {
        "zone_id": zone_id,
        "event_type": event_type,
        "person_count": person_count,
        "duration_seconds": duration_seconds,
        "description": description or f"Zone {zone_id} event {event_type}"
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        LARAVEL_API_URL,
        data=data,
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            pass
    except Exception as e:
        # Silently catch offline or timeout errors to avoid blocking CV loop
        pass

def send_incident(zone_id: str, event_type: str, person_count: int = 1, duration_seconds: float = None, description: str = ""):
    """
    Kirim log insiden ke backend Laravel secara asynchronous agar tidak mengganggu kecepatan FPS.
    """
    t = threading.Thread(
        target=_send_async,
        args=(zone_id, event_type, person_count, duration_seconds, description),
        daemon=True
    )
    t.start()
