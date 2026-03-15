"""Virtual Office - Real-time agent dashboard."""
from .server import OfficeHub, OfficeEvent, create_app, get_office_html

__all__ = ["OfficeHub", "OfficeEvent", "create_app", "get_office_html"]
