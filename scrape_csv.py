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
parser.add_argument('-c', '--customer', help='Customer name to download', default='')
parser.add_argument('-d', '--days', help='Days of history to download', default='30')


args = parser.parse_args()

client = ArmorClient(args.url, token=args.token, debug=False)

today = datetime.datetime.today()
startDate = today - datetime.timedelta(days=int(args.days))

# download assets
print(f"Downloading assets...")
more = True
first = True
next = "true"
assets = []

query = None
if args.customer:
    query = f'tags.customer=="{args.customer}"'

resp = client.request("GET", "asset/csv", query={"search": query})

fileName = "assets."+today.strftime('%Y%m%d%H%M%S') + ".csv"
print(f"Downloading assets...")
with open(fileName, "w") as f:
    f.write(resp.body)

# download sites
print(f"Downloading sites...")
resp = client.request("GET", "site/csv", query={"search": query})

fileName = "sites."+today.strftime('%Y%m%d%H%M%S') + ".csv"
print(f"Downloading sites...")
with open(fileName, "w") as f:
    f.write(resp.body)

# download history
print(f"Downloading history...")

def field_or_blank(d, field):
    if field in d:
        return d[field].replace(",", "")
    else:
        return ""
def field_or_zero(d, field):
    if field in d:
        return d[field]
    else:
        return "0"

fileName = "history."+today.strftime('%Y%m%d%H%M%S') + ".csv"

assetTags = None
if args.customer:
    assetTags = [f'customer:{args.customer}']

more = True
first = True
end = today.strftime('%Y-%m-%dT%H:%M:%SZ')
start = startDate.strftime('%Y-%m-%dT%H:%M:%SZ')

print(f"Downloading history from {start} to {end}...")
with open(fileName, "w") as f:
    count = 0
    print("id,ts,tsl,tzl,m.assetId,m.siteId,m.manufacturerId,m.modelId,m.deviceId,m.txnId,m.event,d.runTime,d.chargeTime", file=f)
    next = None
    while more:
        q = {"limit": 20000, "utc": True, "start": start, "end": end}
        if assetTags:
            q['assetTags'] = assetTags
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
            if 'assetIdx' in resp.body and 'assetTotal' in resp.body:
                print(
                    f"Got {count} records, progress:  {resp.body['assetIdx']}/{resp.body['assetTotal']} assets")
            else:
                print(
                    f"Got {count} records")
            for record in resp.body['objects']:
                print(f"{record['id']},{record['ts']},{record['tsl']},{record['tzl']},{record['m']['assetId']},{field_or_blank(record['m'],'siteId')},{field_or_blank(record['m'],'manufacturerId')},{field_or_blank(record['m'],'modelId')},{field_or_blank(record['m'],'deviceId')},{field_or_blank(record['m'],'txnId')},{record['m']['event']},{record.get('d', dict()).get('runTime', 0)},{record.get('d', dict()).get('chargeTime', 0)}", file=f)
                first = False
        else:
            more = False
