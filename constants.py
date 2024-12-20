#!python3

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file

pushOverUser = os.getenv("PUSHOVER_USER")
pushOverToken = os.getenv("PUSHOVER_TOKEN")
tankUtilityUser = os.getenv("TANKUTILITY_USER")
tankUtilityPw = os.getenv("TANKUTILITY_PW")