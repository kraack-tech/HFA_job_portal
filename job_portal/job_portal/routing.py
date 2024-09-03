# Reference: Advanced Web Development[CM3035] - week 12, 6.407 Implement a consumer
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import spectrumjobs.routing

# WebScoket variable
application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        # Spectrumjobs route handler
        URLRouter(
            spectrumjobs.routing.websocket_urlpatterns
        )
    ),
})
