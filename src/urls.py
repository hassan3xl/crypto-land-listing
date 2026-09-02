from django.contrib import admin
from django.urls import include, path

from src.keep_alive import ping_server, start_render_keep_alive

# Start Render keep-alive background worker thread
start_render_keep_alive()

urlpatterns = [
    path('ping/', ping_server, name='ping_server'),
    path('admin-panel/', admin.site.urls),
    path('notifications/', include('notifications.urls')),
    path('', include('app.urls')),
]
