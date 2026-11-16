import os

# import validators.volgactf

# ============================================================================
# SINGLE SOURCE OF TRUTH - edit these at match start. This is the ONLY file.
# The farm reads them through CONFIG below. The arsenal tools (attack/config.py
# -> s4dfarm/config.py, plus defense/traffic) import this same file, so the
# flag format, team IPs and service ports all live HERE, nowhere else.
# ============================================================================

# Real flag regex from the rules (replaces the stub default).
# Examples: r'CTF\.Moscow\{[a-zA-Z\.0-9_-]+\}' , r'VolgaCTF{[\w-]*\.[\w-]*\.[\w-]*}'
FLAG_FORMAT = r'[A-Z0-9]{31}='

# Target teams: {name: ip}. The S4DFarm client reads this; the only team list.
TEAMS = {
    f'Team #{i}': f'10.60.{i}.3'
    for i in range(0, 10)
}

# Service ports/paths (shared with the arsenal exploits via attack/config.py).
WEB_PORT = 8080
WEB_PATH = "/api/v1/profile"
PWN_PORT = 9999

# Standalone / replay tools only (the farm paces itself with --attack-period).
MY_TEAM_IP = "10.60.5.1"     # your team IP, skipped during attacks
PER_TARGET_SLEEP = 2.1       # per-target delay for standalone round-loop tools
TICK_DURATION = 120          # round sleep for standalone round-loop tools
# ============================================================================

CONFIG = {
    'DEBUG': os.getenv('DEBUG') == '1',

    'TEAMS': TEAMS,
    'FLAG_FORMAT': FLAG_FORMAT,

    # ---- Flag submission protocol --------------------------------------
    # SYSTEM_PROTOCOL = one module name in app/protocols/. Shipped:
    #   faust, ructf_http, ructf_tcp, ctf_moscow, ctfcup_tcp, volgactf.
    # Plus two added here:
    #   'custom' -> app/protocols/custom.py, edit it for the organizers'
    #               own scoreboard when none of the shipped ones fit.
    #   'stub'   -> app/protocols/stub.py, marks every flag ACCEPTED and
    #               submits nowhere. For pipeline testing with no scoreboard.
    # Set only the keys the chosen protocol reads (URL/HOST/PORT/TOKEN).
    #
    # Default is 'stub' so the farm boots and flags show in the UI without a
    # scoreboard. ##### CHANGE IT BEFORE THE REAL GAME - stub scores zero. #####
    'SYSTEM_PROTOCOL': 'stub',

    # -- custom scoreboard (edit app/protocols/custom.py) --
    # 'SYSTEM_PROTOCOL': 'custom',
    # 'SYSTEM_URL': 'http://scoreboard.ctf/flags',
    # 'TEAM_TOKEN': 'YOUR_TEAM_TOKEN',

    # -- shipped examples (uncomment one) --
    # 'SYSTEM_PROTOCOL': 'ructf_http',
    # 'SYSTEM_URL': 'http://monitor.ructfe.org/flags',
    # 'SYSTEM_TOKEN': '275_17fc104dd58d429ec11b4a5e82041cd2',
    #
    # 'SYSTEM_PROTOCOL': 'ructf_tcp',   # or faust / ctfcup_tcp (TCP submit)
    # 'SYSTEM_HOST': '10.10.10.10',
    # 'SYSTEM_PORT': '31337',
    # 'TEAM_TOKEN': '4fdcd6e54faa8991',
    #
    # 'SYSTEM_PROTOCOL': 'volgactf',
    # 'SYSTEM_VALIDATOR': 'volgactf',
    # 'SYSTEM_HOST': 'final.volgactf.ru',
    # 'SYSTEM_SERVER_KEY': validators.volgactf.get_public_key('https://final.volgactf.ru'),
    # --------------------------------------------------------------------

    # The server will submit not more than SUBMIT_FLAG_LIMIT flags
    # every SUBMIT_PERIOD seconds. Flags received more than
    # FLAG_LIFETIME seconds ago will be skipped.
    'SUBMIT_FLAG_LIMIT': 100,
    'SUBMIT_PERIOD': 2,
    'FLAG_LIFETIME': 5 * 60,

    # VOLGA: Don't make more than INFO_FLAG_LIMIT requests to get flag info,
    # usually should be more than SUBMIT_FLAG_LIMIT
    # 'INFO_FLAG_LIMIT': 10,

    # Password for the web interface. This key will be excluded from config
    # before sending it to farm clients.
    # ########## DO NOT FORGET TO CHANGE IT ##########
    'SERVER_PASSWORD': os.getenv('SERVER_PASSWORD') or '1234',

    # For all time-related operations
    'TIMEZONE': 'Europe/Moscow',
}
