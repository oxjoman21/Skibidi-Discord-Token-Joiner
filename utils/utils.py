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
    def _fetch_session(self, token):
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
                        "os": "iOS",
                        "browser": "Discord iOS",
                        "device": "iPhone15,3",
                        "system_locale": "en-US",
                        "browser_version": "196.0",
                        "os_version": "16.6.1",
                        "client_build_number": 196000,
                        "client_version": "196.0",
                        "device_vendor_id": self._generate_device_id()
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

    def _x_super_properties(self, user_agent):
        device_id = self._generate_device_id()
        properties = {
            "os": "iOS",
            "browser": "Discord iOS",
            "device": "iPhone13,4",
            "system_locale": "en-US",
            "browser_user_agent": user_agent,
            "browser_version": "196.0",
            "os_version": "16.6.1",
            "client_build_number": 196000,
            "release_channel": "stable",
            "device_vendor_id": device_id,
            "device_id": device_id,
            "browser_push": True,
            "is_popup": False,
            "client_version": "196.0"
        }
        return base64.b64encode(json.dumps(properties).encode()).decode()

    def _generate_track(self):
        return base64.b64encode(json.dumps({
            "os": "iOS",
            "browser": "Discord iOS",
            "device": "iPhone15,3",
            "system_locale": "en-US",
            "release_channel": "stable",
            "client_build_number": 196000
        }).encode()).decode()

    def _generate_fingerprint(self):
        return ''.join(random.choices('0123456789', k=19))

    def _generate_device_id(self):
        return ''.join(random.choices('0123456789ABCDEF', k=32))

    def _get_cookies(self, session) -> Dict[str, str]:
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

    def _native(self):
        response = requests.get("https://updates.discord.com/distributions/app/manifests/latest", params={"install_id": "0", "channel": "stable", "platform": "win", "arch": "x86"}, headers={"user-agent": "Discord-Updater/1", "accept-encoding": "gzip"}, timeout=10).json()
        return int(response["metadata_version"])

    def _main_version(self):
        response = requests.get("https://discord.com/api/downloads/distributions/app/installers/latest", params={"channel": "stable", "platform": "win", "arch": "x86"}, allow_redirects=False, timeout=10).text
        match = re.search(r"x86/(.*?)/", response)
        return match.group(1) if match else "Unknown"

    def _build(self):
        page = requests.get("https://discord.com/app", timeout=10).text
        assets = re.findall(r'src="/assets/([^"]+)"', page)
        for asset in reversed(assets):
            js = requests.get(f"https://discord.com/assets/{asset}", timeout=10).text
            if "buildNumber:" in js:
                return int(js.split('buildNumber:"')[1].split('"')[0])
        return -1

    def _build_version(self) -> Tuple[int, str, int]:
        return (self._build(), self._main_version(), self._native())

    def _browser(self, user_agent):
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
                "useragent": "Discord/196.0 (iPhone; CPU iPhone OS 16.6.1 like Mac OS X)"
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
