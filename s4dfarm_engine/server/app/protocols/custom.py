"""
Custom scoreboard protocol template.

Use this when the organizers run their own flag-submission system and none of the
shipped protocols (faust, ructf_http, ructf_tcp, ctf_moscow, ctfcup_tcp, volgactf)
match it. Copy the shape of the shipped modules: define submit_flags(flags, config)
as a generator that yields one SubmitResult per flag.

To enable:
  1. Fill in the request below to match the real scoreboard spec.
  2. In app/config.py set:
         'SYSTEM_PROTOCOL': 'custom',
     plus whatever keys you reference here (SYSTEM_URL / SYSTEM_HOST / SYSTEM_PORT /
     TEAM_TOKEN / ...).
  3. Restart the server: docker compose up --build -d

Status mapping is the only part that must be right:
  - FlagStatus.ACCEPTED : scored. Done, never resent.
  - FlagStatus.REJECTED : permanently dead (own flag, too old, expired, invalid,
                          already submitted). Dropped, never resent.
  - FlagStatus.QUEUED   : transient / not-yet (timeout, game not started, service
                          down, flag not in checker DB yet). Resent next tick.

Rule: only call something REJECTED when you are sure it will never score. Anything
uncertain goes to QUEUED so the flag is retried instead of thrown away. A wrongly
REJECTED flag is a lost point; a wrongly QUEUED flag just costs one retry.
"""

import logging

import requests

from models import FlagStatus, SubmitResult

logger = logging.getLogger(__name__)

TIMEOUT = 5

# Substrings that classify the scoreboard's per-flag response message.
# EDIT these to match the real verdict strings the scoreboard returns.
ACCEPTED_MARKERS = ['accepted', 'correct', 'congrat', 'success']
REJECTED_MARKERS = ['own', 'your own flag', 'too old', 'expired', 'invalid',
                    'wrong', 'already', 'duplicate', 'not valid']
# Anything not matched by the two lists above is treated as QUEUED (retry).


def _classify(message):
    m = (message or '').lower()
    if any(s in m for s in ACCEPTED_MARKERS):
        return FlagStatus.ACCEPTED
    if any(s in m for s in REJECTED_MARKERS):
        return FlagStatus.REJECTED
    return FlagStatus.QUEUED


def submit_flags(flags, config):
    # ----------------------------------------------------------------------
    # EDIT THIS BLOCK to match the organizers' submission API.
    #
    # Example: HTTP POST a JSON array of flag strings with a team token header,
    # expecting back a JSON array of {"flag": ..., "msg": ...} objects.
    # Swap for GET/PUT, form data, raw TCP, etc. as the real spec requires.
    # ----------------------------------------------------------------------
    resp = requests.post(
        config['SYSTEM_URL'],
        headers={'X-Team-Token': config['TEAM_TOKEN']},
        json=[item.flag for item in flags],
        timeout=TIMEOUT,
    )

    # Map the scoreboard's response back to one SubmitResult per flag.
    # EDIT the parsing to match the real response shape. If the call itself
    # fails (network error, non-JSON, scoreboard down), let it raise: S4DFarm
    # keeps the flags QUEUED and retries them next tick.
    results = resp.json()
    for item in results:
        flag = item['flag']
        message = item.get('msg', '')
        yield SubmitResult(flag, _classify(message), message)
    # ----------------------------------------------------------------------
