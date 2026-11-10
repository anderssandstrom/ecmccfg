"""Live SIM IOC limit modes and OFF/DIR tests, with stationary disabled axes."""
from .base import SlitCase
from ..limit_modes import LimitModeChecks


class SoftLimitModeTests(LimitModeChecks, SlitCase):
    pass
