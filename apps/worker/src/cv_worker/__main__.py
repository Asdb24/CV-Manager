from cv_foundation.server import arguments, serve
from cv_foundation.settings import Component

from cv_worker.app import create_app

settings, owned_stdio = arguments(Component.WORKER)
try:
    serve(create_app(settings), settings, Component.WORKER, owned_stdio)
except OSError:
    raise SystemExit("OWNED_PORT_UNAVAILABLE") from None
