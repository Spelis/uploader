from http.client import TOO_EARLY
from pathlib import Path
import random
from dotenv import set_key, load_dotenv
import requests, os, argparse,json

scriptpath = Path(__file__).parent
envpath = scriptpath / ".env"
load_dotenv(envpath)
token = os.environ.get("CLITOKEN", None)

ap = argparse.ArgumentParser("Uploader CLI Client")
ap.add_argument("baseurl", help="The base url of the api.")
ap.add_argument("action",help="What to do, can be: login, register, profile, upload, delete, get")
ap.add_argument("body",nargs="*")

args = ap.parse_args()
args.body = dict(map(lambda x: tuple(x.split("=")), args.body))

if args.action in ("login", "register"): # pretty much the same approach.
    r = requests.post(f"{args.baseurl}/{args.action}",json=args.body,headers={"Content-Type":"application/json"})
    c = r.json()
    set_key(envpath,"CLITOKEN",c['token'])
    
elif args.action == "profile":
    r = requests.post(f"{args.baseurl}/me",headers={"Authorization": "Bearer " + os.environ.get("CLITOKEN","")})
    print(json.dumps(r.json(),indent=4))
    
elif args.action == "upload":
    # format:str["txt"|"png"]
    # filename: str
    # data: bytes
    with open(args.body.get("data",""),"rb") as f:
        data = f.read()
    r = requests.post(f"{args.baseurl}/up/{args.body.get("format","txt")}/{args.body.get("filename",random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"))}",headers={"Content-Type":"application/json", "Authorization": "Bearer " + os.environ.get("CLITOKEN",""),"data": data})
    print(os.environ.get("CLITOKEN",""))
    print(r.content)

elif args.action == "delete":
    # filename: str
    if args.body.get("filename",None) is None:
        raise Exception("You need to specify the filename!")
    r = requests.post(f"{args.baseurl}/del/{args.body.get("filename")}",headers={"Content-Type":"application/json", "Authorization": "Bearer " + os.environ.get("CLITOKEN","")})

elif args.action == "get":
    # id: int (user id)
    # filename: str
    r = requests.get(f"{args.baseurl}/files/{args.body.get("id",0)}/{args.body.get("filename","")}")
    print(r.content)
    if args.body.get("save"):
        with open(args.body.get("filename",None),"wb") as f:
            f.write(r.content)
