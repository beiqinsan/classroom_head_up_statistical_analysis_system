# utils/xunfei_spark.py
import os
import time
import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime
from typing import AsyncGenerator
import websockets
import json
import httpx

class XunFeiSpark:
    def __init__(self):
        self.app_id = os.getenv("AIGC_APP_ID")
        self.api_key = os.getenv("AIGC_API_KEY")
        self.api_secret = os.getenv("AIGC_API_SECRET")
        self.host = "spark-api.xf-yun.com"
        self.path = "v4.0/chat"
