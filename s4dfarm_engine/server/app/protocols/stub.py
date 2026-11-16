"""
Stub protocol for pipeline testing WITHOUT a real scoreboard.

Marks every flag ACCEPTED and submits nothing anywhere. Use it to prove the full
loop end to end - exploit prints flag, client ships it, server extracts and
"accepts" it, flag appears in the web UI - before the organizers publish their
real submission spec. Swap SYSTEM_PROTOCOL to 'custom' (or a shipped protocol)
on match day.

Enable in app/config.py:
    'SYSTEM_PROTOCOL': 'stub',
No SYSTEM_HOST / URL / TOKEN needed. Restart: docker compose up --build -d

WARNING: never leave this active during the real game - it scores zero, it only
makes flags look accepted in the UI.
"""

import logging

from models import FlagStatus, SubmitResult

logger = logging.getLogger(__name__)


def submit_flags(flags, config):
    for item in flags:
        logger.info('[stub] pretend-accept %s', item.flag)
        yield SubmitResult(item.flag, FlagStatus.ACCEPTED, 'stub: not really submitted')
