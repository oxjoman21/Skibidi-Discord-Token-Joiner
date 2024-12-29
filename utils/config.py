import yaml
import sys

try:
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    Debug = config["Main"]["debug"]
    ApiKey = config["Main"]["api_key"]
    Solver = config["Main"]["solver"]
except FileNotFoundError:
    print("Could not find 'config.yaml'. Please create it.")
    sys.exit()
except KeyError as e:
    print(f"Missing config key -> {e}")
    sys.exit()
except Exception as e:
    print(f"Error loading config -> {e}")
    sys.exit()

