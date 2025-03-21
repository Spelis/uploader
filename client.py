from pathlib import Path
from dotenv import set_key, load_dotenv
import requests, os, argparse

scriptpath = Path(__file__).parent
envpath = scriptpath / ".env"
load_dotenv(str(envpath))
token = os.environ.get("CLITOKEN", None)

ap = argparse.ArgumentParser("Uploader CLI Client")
ap.add_argument("action",help="What to do, can be: login, register, profile, upload, delete, get")
ap.add_argument("args",nargs="*")

args = ap.parse_args()
args.args = dict(map(lambda x: tuple(x.split("=")), args.args))

print(args)
