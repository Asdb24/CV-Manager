from cv_foundation.server import arguments, serve
from cv_foundation.settings import Component

from cv_api.app import create_app

settings, owned_stdio = arguments(Component.API)
try:
    serve(create_app(settings), settings, Component.API, owned_stdio)
except OSError:
    raise SystemExit("OWNED_PORT_UNAVAILABLE") from None
