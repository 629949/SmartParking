import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import iot.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartpark.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(iot.routing.websocket_urlpatterns)
    ),
})
