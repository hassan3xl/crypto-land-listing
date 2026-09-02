import logging
import os
import threading
import time
import urllib.request
from django.http import JsonResponse
from django.utils import timezone

logger = logging.getLogger(__name__)


def ping_server(request):
    """Health check endpoint to verify server status and keep Render backend active."""
    return JsonResponse({
        'status': 'ok',
        'message': 'Server is active and healthy',
        'timestamp': timezone.now().isoformat(),
        'environment': os.environ.get('RENDER_SERVICE_TYPE', 'development')
    })


def start_render_keep_alive():
    """
    Background daemon thread function that pings the Render public URL (or local host)
    every 10 minutes to prevent the Render free tier backend from spinning down due to inactivity.
    """
    def _ping_loop():
        # Wait 10 seconds after server startup before starting ping loop
        time.sleep(10)

        while True:
            # Render automatically sets RENDER_EXTERNAL_URL (e.g. https://your-app.onrender.com)
            render_url = (
                os.environ.get('RENDER_EXTERNAL_URL')
                or os.environ.get('APP_URL')
                or os.environ.get('RENDER_URL')
            )
            port = os.environ.get('PORT', '8000')

            if render_url:
                target_url = render_url.rstrip('/') + '/ping/'
            else:
                target_url = f"http://127.0.0.1:{port}/ping/"

            try:
                req = urllib.request.Request(
                    target_url,
                    headers={
                        'User-Agent': 'Render-KeepAlive-Bot/1.0',
                        'Accept': 'application/json'
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"[Keep-Alive] Successfully pinged {target_url}")
            except Exception as err:
                logger.warning(f"[Keep-Alive] Ping to {target_url} failed: {err}")

            # Sleep for 10 minutes (600 seconds) - Render sleeps after 15 minutes of inactivity
            time.sleep(600)

    # Ensure background worker thread starts only once per process
    if not getattr(threading, '_render_keep_alive_started', False):
        setattr(threading, '_render_keep_alive_started', True)
        ping_thread = threading.Thread(
            target=_ping_loop,
            daemon=True,
            name="RenderKeepAliveThread"
        )
        ping_thread.start()
        logger.info("[Keep-Alive] Render anti-sleep background service initialized.")
