# =============================================================================== #
#                               WebSocket Routing                                 #
# =============================================================================== #
# Reference: Advanced Web Development[CM3035] - week 12, 6.407 Implement a consumer

from django.urls import re_path
from . import consumers

# WebSocket ASGI url
websocket_urlpatterns = [
    re_path(r'ws/(?P<contact>\w+)/$', consumers.LiveChatConsumer.as_asgi()),
]
