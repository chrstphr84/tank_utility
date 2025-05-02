#!/usr/bin/env python3

import os
from pathlib import Path
from dotenv import load_dotenv

# Look for .env file in the script directory if not found in current directory
script_dir = Path(__file__).resolve().parent
env_path = script_dir / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()  # Try default location

# Tank Utility credentials
tankUtilityUser = os.getenv("TANKUTILITY_USER")
tankUtilityPw = os.getenv("TANKUTILITY_PW")

# Pushover credentials
pushOverUser = os.getenv("PUSHOVER_USER")
pushOverToken = os.getenv("PUSHOVER_TOKEN")