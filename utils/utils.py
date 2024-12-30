import base64
import json
import re
import websocket
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning
from typing import Dict, Tuple, Optional
from .logger import Log
from .config import Debug, ApiKey
import time
import random

warnings.simplefilter("ignore", InsecureRequestWarning)

log = Log()

class Utils:
    def fetch_session(self, token, user_agent):
        ws = websocket.WebSocket()
        try:
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            recv = json.loads(ws.recv())
            payload = {
                "op": 2,
                "d": {
                    "token": token,
                    "capabilities": 8189,
                    "properties": {
                        "os": "Windows",
                        "browser": "Chrome",
                        "device": "",
                        "system_locale": "en-US",
                        "browser_version": "111.0.5563.110",
                        "os_version": "10",
                        "client_build_number": 111000,
                        "client_version": "111.0.5563.110",
                        "device_vendor_id": "unknown",
                        "browser_user_agent": user_agent,
                    },
                    "presence": {
                        "status": "online",
                        "since": 0,
                        "activities": [],
                        "afk": False
                    },
                    "compress": False,
                    "client_state": {
                        "guild_versions": {},
                        "highest_last_message_id": "0",
                        "read_state_version": 0,
                        "user_guild_settings_version": -1,
                        "user_settings_version": -1,
                        "private_channels_version": "0",
                        "api_code_version": 0
                    }
                }
            }
            ws.send(json.dumps(payload))
            result = json.loads(ws.recv())
            if result.get("t") == "READY":
                return result["d"]["session_id"]
            if result.get("op") == 9:
                return "Invalid token"
            if result.get("op") == 429:
                return "429"
            return "An unknown error occurred"
        except websocket.WebSocketException as e:
            return f"WebSocket error: {e}"
        except json.JSONDecodeError as e:
            return f"JSON error: {e}"

    def x_super_properties(self, user_agent):
        properties = {
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": user_agent,
            "browser_version": self.browser(user_agent),
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "https://discord.com/",
            "referring_domain_current": "discord.com",
            "release_channel": "stable",
            "client_build_number": self.build(),
            "native_build_number": self.native(),
            "client_event_source": None
        }
        return base64.b64encode(json.dumps(properties).encode()).decode()

    def get_cookies(self, session) -> Dict[str, str]:
        cookies = {}
        try:
            response = session.get("https://discord.com")
            for cookie_name, cookie_value in response.cookies.items():
                if cookie_name.startswith("__") and cookie_name.endswith("uid"):
                    cookies[cookie_name] = cookie_value
            return cookies
        except Exception as e:
            log.error(f"Error while fetching cookies -> {e}")
        return cookies

    def native(self):
        response = requests.get("https://updates.discord.com/distributions/app/manifests/latest", params={"install_id": "0", "channel": "stable", "platform": "win", "arch": "x86"}, headers={"user-agent": "Discord-Updater/1", "accept-encoding": "gzip"}, timeout=10).json()
        return int(response["metadata_version"])

    def build(self):
        page = requests.get("https://discord.com/app", timeout=10).text
        assets = re.findall(r'src="/assets/([^"]+)"', page)
        for asset in reversed(assets):
            js = requests.get(f"https://discord.com/assets/{asset}", timeout=10).text
            if "buildNumber:" in js:
                return int(js.split('buildNumber:"')[1].split('"')[0])
        return -1

    def build_version(self) -> Tuple[int, str, int]:
        return (self._build(), self._main_version(), self._native())

    def browser(self, user_agent):
        patterns = {"Chrome": r"Chrome/([\d.]+)", "Firefox": r"Firefox/([\d.]+)", "Safari": r"Version/([\d.]+).*Safari", "Opera": r"Opera/([\d.]+)", "Edge": r"Edg/([\d.]+)", "IE": r"MSIE ([\d.]+);"}
        for pattern in patterns.values():
            match = re.search(pattern, user_agent)
            if match:
                return match.group(1)
        return "Unknown"

    def get_xcontext_values(self, invite, token, session) -> Optional[Tuple[str, str, str, str]]:
        headers = {"Authorization": token}
        r = session.get(f"https://discord.com/api/v9/invites/{invite}", headers=headers)
        if r.status_code == 200:
            data = r.json()
            guild_id = data.get("guild", {}).get("id")
            channel_id = data.get("channel", {}).get("id")
            ctype = data.get("type", "unknown")
            if not guild_id or not channel_id:
                return None
            return ("Join Guild", guild_id, channel_id, str(ctype))
        return None

    def solve(self, sitekey, rqdata=None, rqtoken=None, session=None, proxy=None):
        if Debug:
            log.info(f"Starting solve -> sitekey: {sitekey}, rqdata: {rqdata}, rqtoken: {rqtoken}, proxy: {proxy}")
        if not proxy:
            log.error("Proxy required to solve captcha")
            return None
        parts = proxy.replace("http://", "").replace("https://", "").split(":")
        parsed = None
        if len(parts) == 4:
            parsed = f"http://{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}"
        if proxy and not parsed:
            return None
        url = "https://api.razorcap.xyz/create_task"
        headers = {}
        payload = {
            "key": ApiKey,
            "type": "hcaptcha_enterprise",
            "data": {
                "sitekey": sitekey,
                "siteurl": "discord.com",
                "proxy": parsed,
                "rqdata": rqdata,
                "useragent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (like Gecko) Chrome/111.0.5563.110 Safari/537.36"
            }
        }
        r = session.post(url, headers=headers, json=payload)
        if Debug:
            log.info(f"Create task response -> {r.text}")
        if r.status_code == 200:
            info = r.json()
            if Debug:
                log.info(str(info))
            tid = info.get("task_id")
            st = info.get("status")
            if not tid or st == "error":
                return None
            start_time = time.time()
            while True:
                time.sleep(2)
                poll = requests.get(f"https://api.razorcap.xyz/get_result/{tid}", headers=headers)
                if poll.status_code == 200:
                    pres = poll.json()
                    if pres.get("status") == "solved":
                        return pres.get("response_key")
                    if pres.get("status") == "error" or time.time() - start_time > 60:
                        break
                else:
                    break
        return None
