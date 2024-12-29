import tls_client
import os
import time
from base64         import b64encode
import json
from colorama       import Fore
from utils.logger   import Log, color_switch
from utils.utils    import Utils
from utils.config   import Debug, ApiKey, Solver
from utils.design   import banner, update_title

log = Log()
utils = Utils()

def parse_proxy(proxy_str):
    try:
        proxy_str = proxy_str.strip()
        if "@" in proxy_str:
            if Debug:
                log.info(f"Using parsed proxy -> {proxy_str}")
            return proxy_str
        parts = proxy_str.split(":")
        if len(parts) == 2:
            if Debug:
                log.info(f"Using host:port -> {proxy_str}")
            return proxy_str
        if len(parts) == 4:
            user_pass = f"{parts[0]}:{parts[1]}"
            host_port = f"{parts[2]}:{parts[3]}"
            new_proxy = f"{user_pass}@{host_port}"
            if Debug:
                log.info(f"Using parsed proxy -> {new_proxy}")
            return new_proxy
        log.error(f"Invalid proxy format: {proxy_str}")
        return None
    except Exception as e:
        log.error(f"Failed to parse proxy {proxy_str} -> {e}")
        return None

class Joiner:
    def __init__(self, invite):
        self.inv = invite
        self.user_agent = "Discord/196.0 (iPhone; CPU iPhone OS 16.6.1 like Mac OS X)"
        self.session = tls_client.Session(
            client_identifier="safari_ios_16_0",
            random_tls_extension_order=True,
            ja3_string="771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-34-51-43-13-45-28-21,29-23-24-25-256-257,0",
            h2_settings={"HEADER_TABLE_SIZE": 65536, "MAX_CONCURRENT_STREAMS": 1000, "INITIAL_WINDOW_SIZE": 6291456, "MAX_HEADER_LIST_SIZE": 262144},
            h2_settings_order=["HEADER_TABLE_SIZE", "MAX_CONCURRENT_STREAMS", "INITIAL_WINDOW_SIZE", "MAX_HEADER_LIST_SIZE"],
            supported_signature_algorithms=["ECDSAWithP256AndSHA256", "PSSWithSHA256", "PKCS1WithSHA256", "ECDSAWithP384AndSHA384", "PSSWithSHA384", "PKCS1WithSHA384", "PSSWithSHA512", "PKCS1WithSHA512"],
            supported_versions=["GREASE", "1.3", "1.2"],
            key_share_curves=["GREASE", "X25519"],
            cert_compression_algo="brotli",
            pseudo_header_order=[":method", ":authority", ":scheme", ":path"],
            connection_flow=15663105,
            priority_frames=[
                {"stream_id": 15, "priority": {"weight": 1}},
                {"stream_id": 13, "priority": {"weight": 1}},
                {"stream_id": 11, "priority": {"weight": 1}}
            ]
        )
        self.base_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": "https://discord.com/channels/@me",
            "user-agent": self.user_agent,
            "x-discord-locale": "en-US",
            "x-discord-timezone": "America/New_York",
            "x-super-properties": utils._x_super_properties(self.user_agent),
            "connection": "keep-alive",
            "host": "discord.com",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        self.base_cookies = utils._get_cookies(self.session)

    def update_session(self, token, proxy=None):
        try:
            parsed = None
            if proxy:
                parsed = parse_proxy(proxy)
                if parsed:
                    self.session.proxies = {"http": f"http://{parsed}", "https": f"http://{parsed}"}
                    if Debug:
                        log.success(f"Assigned proxy -> {parsed}")
                else:
                    log.error("Parsed proxy is None. Skipping proxy assignment.")
                    self.session.proxies = None
            else:
                self.session.proxies = None
                if Debug:
                    log.info("Proxy not provided")
            self.session.cookies.update(self.base_cookies)
            headers = self.base_headers.copy()
            headers["authorization"] = token
            xctx_vals = utils.get_xcontext_values(self.inv, token, self.session)
            if xctx_vals:
                xctx_dict = {
                    "location": xctx_vals[0],
                    "location_guild_id": xctx_vals[1],
                    "location_channel_id": xctx_vals[2],
                    "location_channel_type": xctx_vals[3]
                }
                headers["x-context-properties"] = b64encode(json.dumps(xctx_dict).encode()).decode()
                if Debug:
                    log.success("Updated x-context-properties -> " + headers["x-context-properties"])
            else:
                headers["x-context-properties"] = b64encode(json.dumps({}).encode()).decode()
            self.session.headers = headers
            return True
        except Exception as e:
            log.error(f"Failed to update session -> {e}")
            return False

    def change_nick(self, guild_id, nick, session):
        token = session.headers.get("authorization")
        r = session.patch(f"https://discord.com/api/v9/guilds/{guild_id}/members/@me", json={"nick": nick})
        if r.status_code == 200:
            log.success(f"Changed Nick -> {color_switch(token[:30] + '*****','green','blue')} -> {nick}")
        elif r.status_code == 429:
            log.error(f"Rate Limited -> {color_switch(token[:30] + '*****','red','blue')}")
        elif r.status_code == 50013: 
            log.error(f"Failed Change Nick (Permissions) {color_switch(token[:30] + '*****','red','blue')} -> {r.text}")
        else:
            log.error(f"Failed Change Nick -> {color_switch(token[:30] + '*****','red','blue')} -> {r.text}")

    def join(self, token, nick, Solve_Cap, proxy=None):
        if not self.update_session(token, proxy):
            return False
        url = f"https://discord.com/api/v9/invites/{self.inv}"
        session_id = utils._fetch_session(token)
        if session_id in ["Invalid token", "429"]:
            log.error(f"{Fore.RED}Cant Fetch Session -> {color_switch(token[:30] + '*****','red','blue')}")
            return False
        payload = {"session_id": session_id}
        try:
            r = self.session.post(url, json=payload)
        except Exception as e:
            log.error(f"{Fore.RED}Request failed -> {e}")
            return False
        if r.status_code == 200:
            log.success("Joined -> " + color_switch(token[:30] + '*****','green','blue'))
            jdata = r.json()
            guild_info = jdata.get("guild")
            if not guild_info:
                log.error("Guild data not found in response")
                return False
            server_id = guild_info.get("id")
            if Debug:
                log.info(f"Server ID -> {server_id}")
            if nick:
                self.change_nick(server_id, nick, self.session)
            return True
        elif r.status_code == 401:
            log.error(f"Invalid -> {color_switch(token[:30] + '*****','red','blue')}")
            return False
        elif "captcha" in r.text:
            rjson = r.json()
            sitekey = rjson.get("captcha_sitekey")
            rqtoken = rjson.get("captcha_rqtoken")
            rqdata = rjson.get("captcha_rqdata")
            if Solve_Cap:
                log.info(f"Captcha -> {color_switch(token[:30] + '*****','yellow','red')}")
                if Debug:
                    log.info(f"Sitekey -> {sitekey}")
                    log.info(f"RQToken -> {rqtoken}")
                    log.info(f"RQData -> {rqdata}")
                if not proxy:
                    log.error("No proxy -> cannot solve captcha")
                    return False
                if Debug:
                    log.info(f"Solving Captcha -> {color_switch(token[:30] + '*****','yellow','red')}")
                solution = utils.solve(sitekey, rqdata, rqtoken, session=self.session, proxy=proxy)
                if solution:
                    log.success(f"Solved -> {solution[:30]} -> {color_switch(token[:30] + '*****','green','blue')}")
                    try:
                        self.session.headers.update({
                            "x-captcha-key": solution,
                            "x-captcha-rqtoken": rqtoken
                        })
                        r = self.session.post(url, json=payload)
                        if r.status_code == 200:
                            log.success("Joined -> " + color_switch(token[:30] + '*****','green','blue'))
                            jdata = r.json()
                            if jdata.get("code") == 10008:
                                return self.join(token, nick, Solve_Cap, proxy)
                            guild_info = jdata.get("guild")
                            if not guild_info:
                                log.error("Guild data not found in response")
                                return False
                            server_id = guild_info.get("id")
                            if Debug:
                                log.info(f"Server ID -> {server_id}")
                            if nick:
                                self.change_nick(server_id, nick, self.session)
                            return True
                        else:
                            log.error(f"Failed (AfterCap) -> {color_switch(token[:30] + '*****','red','blue')} -> {r.text}")
                            return False
                    except Exception as e:
                        if Debug:
                            log.error(f"Captcha error: {e}")
                        return False
            else:
                log.error(f"Captcha -> {color_switch(token[:30] + '*****','red','blue')}")
                return False
        else:
            log.error(f"{Fore.RED}Failed -> {color_switch(token[:30] + '*****','red','blue')} -> {r.text}")
            return False

def main():
    try:
        joined = 0
        error = 0
        captcha = 0
        os.system("cls")
        os.system("title SKIBIDI Joiner")
        banner()
        Inv = log.inp("Enter invite code")
        Delay = log.inp("Enter Delay")
        ChangeNick = log.inp("Change Nickname? (Y/N)").lower()
        if ChangeNick == "y":
            Nick = log.inp("Enter Nickname")
        else:
            Nick = None
        UseProxies = log.inp("Use proxies? (Y/N)").lower()
        if UseProxies == "y":
            try:
                with open("input/proxies.txt", "r") as fp:
                    proxies_list = fp.read().splitlines()
            except:
                log.error("Failed to load proxies")
                proxies_list = []
        else:
            proxies_list = []
        Solve_Cap = log.inp("Solve Captcha? (Y/N) (Requires Proxies)").lower()
        if Solve_Cap == "y":
            Solve_Cap = True
        else:
            Solve_Cap = False
        
        try:
            Delay = float(Delay)
        except ValueError:
            log.error(f"{Fore.RED}Invalid delay value. Please enter a number.")
            return
        os.system("cls")
        banner()
        joiner = Joiner(Inv)
        try:
            with open("input/tokens.txt", "r") as f:
                token_backup = f.read().splitlines()
            p_index = 0
            while True:
                with open("input/tokens.txt", "r+") as f:
                    tokens = f.read().splitlines()
                    if not tokens:
                        log.info(f"Finished -> {Fore.RED}Errors: {Fore.RESET}{error}{Fore.RESET} -> {Fore.GREEN}Joined: {Fore.RESET}{joined}")
                        with open("input/tokens.txt", "w") as fw:
                            fw.write("\n".join(token_backup))
                        input()
                        break
                    token = tokens.pop(0)
                    proxy = None
                    if proxies_list:
                        proxy = proxies_list[p_index % len(proxies_list)]
                        p_index += 1
                    status = joiner.join(token, Nick, Solve_Cap, proxy)
                    if status:
                        joined += 1
                    else:
                        error += 1
                    update_title(joined, error)
                    f.seek(0)
                    f.truncate()
                    f.write("\n".join(tokens))
                    time.sleep(Delay)
        except Exception as e:
            log.error(f"{Fore.RED}Error handling tokens file -> {e}")
    except KeyboardInterrupt:
        print("\n")
        log.info("Exiting...")

if __name__ == "__main__":
    main()
