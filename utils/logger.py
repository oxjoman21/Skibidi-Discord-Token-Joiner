from colorama       import Fore, Style
from datetime       import datetime

def color_switch(msg, start_color, end_color):
    named_colors = {
        "black": "#000000",
        "red": "#FF0000",
        "green": "#00FF00",
        "blue": "#0000FF",
        "white": "#FFFFFF",
        "yellow": "#FFFF00",
        "magenta": "#FF00FF",
        "cyan": "#00FFFF",
        "gray": "#808080",
        "orange": "#FFA500"
    }

    if start_color in named_colors:
        start_color = named_colors[start_color]
    if end_color in named_colors:
        end_color = named_colors[end_color]

    rs = int(start_color[1:3], 16)
    gs = int(start_color[3:5], 16)
    bs = int(start_color[5:7], 16)
    re = int(end_color[1:3], 16)
    ge = int(end_color[3:5], 16)
    be = int(end_color[5:7], 16)

    length = len(msg)
    output = []

    for i, char in enumerate(msg):
        if length > 1:
            ratio = i / (length - 1)
        else:
            ratio = 0
        r = int(rs + (re - rs) * ratio)
        g = int(gs + (ge - gs) * ratio)
        b = int(bs + (be - bs) * ratio)
        output.append(f"\033[38;2;{r};{g};{b}m{char}\033[0m")

    return "".join(output)

class Log:

    def __init__(self):
        
        pass

    def datime(self):
        return datetime.now().strftime("%M:%S")

    def success(self,msg):
        print(f"{Fore.MAGENTA}[{self.datime()}] {Fore.GREEN}SUC {Fore.RESET}{msg}{Fore.RESET}")    

    def error(self,msg):
        print(f"{Fore.MAGENTA}[{self.datime()}] {Fore.RED}ERR {Fore.RESET}{msg}{Fore.RESET}")

    def info(self,msg):
        print(f"{Fore.MAGENTA}[{self.datime()}] {Fore.BLUE}INF {Fore.RESET}{msg}{Fore.RESET}")

    def inp(self,msg):
        return input(f"{Fore.MAGENTA}[{self.datime()}] {Fore.YELLOW}INP {Fore.RESET}{msg}{Fore.RESET} \n{Fore.MAGENTA}[{self.datime()}] {Fore.YELLOW}->  {Fore.RESET}")
