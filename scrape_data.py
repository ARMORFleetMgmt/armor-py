################################################
##      Copyright, ARMOR Technologies, Inc.   ##
################################################

import argparse
import json
from client import ArmorClient
import datetime

parser = argparse.ArgumentParser(
    prog='ARMOR Fleet Management Data Scraper',
    description='Downloads key data in JSON format',
    epilog='Copyright 2023 ARMOR Technologies, Inc.')
parser.add_argument('-u', '--url', help='API URL', default="https://app.armordata.io/api/v1/")
parser.add_argument('-t', '--token', help='API Token', default="AT:gVUV7pVIM........9E4B1XMQP", required=True)
parser.add_argument('-d', '--days', help='Days of history to download', default='30')
parser.add_argument('-a', '--all', help='Download all data', default=False)

args = parser.parse_args()

client = ArmorClient(args.url, token=args.token, debug=False)

today = datetime.date.today()
startDate =today - datetime.timedelta(days=int(args.days))

fileName = "assets."+today.strftime('%Y%m%d%H%M%S') + ".json"

# download assets
print(f"Downloading assets...")
more = True
first = True
next = "true"
with open(fileName, "w") as f:
    print("[", file=f)
    count = 0
    total = 0
    while more:
        if first:
            resp = client.request("GET", "asset", query={"limit": 2000, "next": next, "total": True})
        else:
            resp = client.request("GET", "asset", query={"limit": 2000, "next": next})
        if resp.body['count'] > 0:
            if first:
                total = resp.body['total']
            count += resp.body['count']
            print(f"Got {count}/{total} assets, first: {resp.body['objects'][0]['id']}, last: {resp.body['objects'][-1]['id']}")
            for record in resp.body['objects']:
                if not first:
                    print(",", file=f)
                first = False
                json.dump(record, f, indent=2)

            next = resp.body['next']
        else:
            more = False
    print("]", file=f)

fileName = "sites."+today.strftime('%Y%m%d%H%M%S') + ".json"

# download sites
print(f"Downloading sites...")
more = True
first = True
next = "true"
with open(fileName, "w") as f:
    print("[", file=f)
    count = 0
    total = 0
    while more:
        if first:
            resp = client.request("GET", "site", query={"limit": 2000, "next": next, "total": True})
        else:
            resp = client.request("GET", "site", query={"limit": 2000, "next": next})
        if resp.body['count'] > 0:
            if first:
                total = resp.body['total']
            count += resp.body['count']
            print(f"Got {count}/{total} sites, first: {resp.body['objects'][0]['id']}, last: {resp.body['objects'][-1]['id']}")
            for record in resp.body['objects']:
                if not first:
                    print(",", file=f)
                first = False
                json.dump(record, f, indent=2)

            next = resp.body['next']
        else:
            more = False
    print("]", file=f)

fileName = "history."+today.strftime('%Y%m%d%H%M%S') + ".json"

# download history
print(f"Downloading history...")
more = True
first = True
end = today.strftime('%Y-%m-%dT%H:%M:%SZ')
start = startDate.strftime('%Y-%m-%dT%H:%M:%SZ')
with open(fileName, "w") as f:
    print("[", file=f)
    count = 0
    next = None
    while more:
        q = {"limit": 20000, "utc": True}
        if not args.all:
            q["start"] = start
            q["end"] = end
        if next:
            q['next'] = next
        resp = client.request("GET", "history/json", query=q)
        if 'next' in resp.body:
            next = resp.body['next']
        else:
            next = None
            more = False
        if resp.body['count'] > 0:
            count += resp.body['count']
            print(
                f"Got {count} records, progress:  {resp.body['assetIdx']}/{resp.body['assetTotal']} assets")
            for record in resp.body['objects']:
                if not first:
                    print(",", file=f)
                first = False
                json.dump(record, f, indent=2)
        else:
            more = False
    print("]", file=f)
