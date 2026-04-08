import argparse
import requests
import debug

debug.start_debug("ctl")

API = "http://localhost:5000"

def main():
    parser = argparse.ArgumentParser("airpodsctl")

    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("connect")
    sub.add_parser("state")

    noise = sub.add_parser("noise")
    noise.add_argument("mode", type=int)

    raw = sub.add_parser("raw")
    raw.add_argument("hex")

    rec = sub.add_parser("record")
    rec.add_argument("action", choices=["start","stop","save","replay"])

    args = parser.parse_args()

    if args.cmd == "connect":
        print(requests.get(API+"/connect").json())

    elif args.cmd == "state":
        print(requests.get(API+"/state").json())

    elif args.cmd == "noise":
        print(requests.get(f"{API}/noise/{args.mode}").json())

    elif args.cmd == "raw":
        print(requests.post(f"{API}/raw", data=args.hex).json())

    elif args.cmd == "record":
        print(requests.get(f"{API}/record/{args.action}").json())

debug.end_debug("ctl")

if __name__ == "__main__":
    main()