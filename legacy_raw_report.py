################################################
##      Copyright, ARMOR Technologies, Inc.   ##
################################################

import argparse
import json
from client import ArmorClient
import datetime

parser = argparse.ArgumentParser(
    prog='ARMOR Fleet Management Legacy Raw Data Report',
    description='Downloads data in the format of the old armor platforms raw report',
    epilog='Copyright 2023 ARMOR Technologies, Inc.')
parser.add_argument('-u', '--url', help='API URL', default="https://app.armordata.io/api/v1/")
parser.add_argument('-t', '--token', help='API Token', default="AT:gVUV7pVIM........9E4B1XMQP", required=True)
parser.add_argument('-d', '--days', help='Days of history to download', default='30')
parser.add_argument('-c', '--customer', help='Customer name to download', default='')

args = parser.parse_args()

client = ArmorClient(args.url, token=args.token, debug=False)

today = datetime.date.today()
startDate = today - datetime.timedelta(days=int(args.days))

fileName = "assets." + today.strftime('%Y%m%d%H%M%S') + ".json"

# download assets
print(f"Downloading assets...")
more = True
first = True
next = "true"
assets = dict()

query = None
if args.customer:
    query = f'tags.customer=="{args.customer}"'

count = 0
total = 0
while more:
    if first:
        resp = client.request("GET", "asset", query={"search": query, "limit": 2000, "next": next, "total": True})
    else:
        resp = client.request("GET", "asset", query={"search": query, "limit": 2000, "next": next})
    if resp.body['count'] > 0:
        if first:
            total = resp.body['total']
        count += resp.body['count']
        print(
            f"Got {count}/{total} assets, first: {resp.body['objects'][0]['id']}, last: {resp.body['objects'][-1]['id']}")
        for record in resp.body['objects']:
            assets[record['id']] = record
            first = False
    else:
        more = False
    if 'next' in resp.body:
        next = resp.body['next']
    else:
        more = False

# download sites
print(f"Downloading sites...")
more = True
first = True
next = "true"

sites = dict()

count = 0
total = 0
while more:
    if first:
        resp = client.request("GET", "site", query={"search": query, "limit": 2000, "next": next, "total": True})
    else:
        resp = client.request("GET", "site", query={"search": query, "limit": 2000, "next": next})
    if resp.body['count'] > 0:
        if first:
            total = resp.body['total']
        count += resp.body['count']
        print(
            f"Got {count}/{total} sites, first: {resp.body['objects'][0]['id']}, last: {resp.body['objects'][-1]['id']}")
        for record in resp.body['objects']:
            sites[record['id']] = record
            first = False
    else:
        more = False
    if 'next' in resp.body:
        next = resp.body['next']
    else:
        more = False

fileName = "legacy_raw." + today.strftime('%Y%m%d%H%M%S') + ".csv"


def field_or_blank(d, field):
    if field in d:
        return d[field]
    else:
        return ""


def convert_category(cat):
    if cat == "run-start":
        return "RunStart"
    elif cat == "run-stop":
        return "RunTime"
    elif cat == "charge-start":
        return "ChargeStart"
    elif cat == "charge-stop":
        return "ChargeTime"
    else:
        return "Misc"


assetTags = None
if args.customer:
    assetTags = [f'customer:{args.customer}']
# download history
more = True
first = True
end = today.strftime('%Y-%m-%dT%H:%M:%SZ')
start = startDate.strftime('%Y-%m-%dT%H:%M:%SZ')
print(f"Downloading history from {start} to {end}...")
with open(fileName, "w") as f:
    count = 0
    print(
        "AssetIdent,EquipID,CompanyName,Model,SerialNbr,Nickname,SiteName,City,State,Category,ReportDate,StartTime,Minutes,Xaxis,Yaxis,Zaxis,ServiceRequest,ReplacedBatteries,Maintenance,FactoryReset,CUSI,Expires,CarrierStatus,Latitude,Longitude",
        file=f)
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
                asset = assets.get(record['m']['assetId'], None)
                site = sites.get(asset['siteId'], None) if asset.get('siteId') else None
                print(
                    f"{asset['properties'].get('oldAssetIdent', '')},,{field_or_blank(asset,'manufacturerId')},{field_or_blank(asset,'modelId')},{asset['properties'].get('serialNumber', '')},{asset['name']},",
                    file=f, end='')
                cusi = ''
                if site:
                    if 'properties' in site:
                        cusi = site['properties'].get('cusi', '')
                    if 'address' in site and 'city' in site['address'] and 'state' in site['address']:
                        city = site['address'].get('city','')
                        state = site['address'].get('state','')
                    print(
                        f"{site['name']},{city},{state},",
                        file=f, end='')
                else:
                    print(f",,,", file=f, end='')
                record['ts'] = datetime.datetime.fromisoformat(record['ts']).strftime('%m/%d/%Y')
                print(
                    f"{convert_category(record['m']['event'])},{record['ts']},{record['ts']},{record.get('d', dict()).get('runTime', 0)},0,0,0,0,0,0,0,{cusi},0,Active,",
                    file=f, end='')
                if record.get('l', None):
                    print(f"{record['l']['coordinates'][1]},{record['l']['coordinates'][0]}", file=f)
                else:
                    print(f"0,0", file=f)
                first = False
        else:
            more = False
