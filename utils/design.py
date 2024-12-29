from colorama import Fore
import os 

def banner():

    print(f'''{Fore.MAGENTA}
    
                                        |     __|  |--.|__|  |--.|__|.--|  |__|
                                        |__     |    < |  |  _  ||  ||  _  |  |
                                        |_______|__|__||__|_____||__||_____|__|                 
                             
    {Fore.LIGHTMAGENTA_EX}                                            ["MERRY CHRISTMAS"]
    {Fore.RESET}
    ''')

def update_title(sucs,errors):
    os.system(f"title SKIBIDI - S: {sucs} - E: {errors}")