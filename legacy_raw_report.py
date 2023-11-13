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
        print(
            f"Got {count}/{total} assets, first: {resp.body['objects'][0]['id']}, last: {resp.body['objects'][-1]['id']}")
        for record in resp.body['objects']:
            assets[record['id']] = record
            first = False
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
        resp = client.request("GET", "site", query={"limit": 2000, "next": next, "total": True})
    else:
        resp = client.request("GET", "site", query={"limit": 2000, "next": next})
    if resp.body['count'] > 0:
        if first:
            total = resp.body['total']
        count += resp.body['count']
        print(
            f"Got {count}/{total} sites, first: {resp.body['objects'][0]['id']}, last: {resp.body['objects'][-1]['id']}")
        for record in resp.body['objects']:
            sites[record['id']] = record
            first = False
        next = resp.body['next']
    else:
        more = False

fileName = "legacry_raw." + today.strftime('%Y%m%d%H%M%S') + ".csv"


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


# download history
more = True
first = True
end = today.strftime('%Y-%m-%dT%H:%M:%SZ')
start = startDate.strftime('%Y-%m-%dT%H:%M:%SZ')
print(f"Downloading history from {start} to {end}...")
with open(fileName, "w") as f:
    count = 0
    print(
        "AssetIdent,EquipID,CompanyName,Model,SerialNbr,Nickname,SiteName,City,State,SerialNbr1,Category,ReportDate,StartTime,Minutes,Xaxis,Yaxis,Zaxis,ServiceRequest,ReplacedBatteries,Maintenance,FactoryReset,CUSI,Expires,CarrierStatus,Latitude,Longitude",
        file=f)
    while more:
        resp = client.request("GET", "history/json", query={"limit": 10000, "utc": True, "start": start, "end": end})
        if resp.body['count'] > 0:
            count += resp.body['count']
            print(
                f"Got {count} records, first: {resp.body['objects'][0]['ts']}, last: {resp.body['objects'][-1]['ts']}")
            for record in resp.body['objects']:
                asset = assets.get(record['m']['assetId'], None)
                site = sites.get(asset['siteId'], None) if asset.get('siteId') else None
                print(
                    f"{asset['properties'].get('oldAssetIdent', '')},,{asset['manufacturerId']},{asset['modelId']},{asset['properties'].get('serialNumber', '')},{asset['name']},",
                    file=f, end='')
                if site:
                    print(
                        f"{site['name']},{site['address']['city']},{site['address']['state']},{asset['properties'].get('serialNumber', '')},",
                        file=f, end='')
                else:
                    print(f",,,{asset['properties'].get('serialNumber', '')},", file=f, end='')
                print(
                    f"{convert_category(record['m']['event'])},{record['ts']},{record['ts']},{record.get('d', dict()).get('runTime', 0)},0,0,0,0,0,0,0,,,Active,",
                    file=f, end='')
                if record.get('l', None):
                    print(f"{record['l']['coordinates'][1]},{record['l']['coordinates'][0]}", file=f)
                else:
                    print(f"0,0", file=f)
                first = False
            end = resp.body['objects'][-1]['ts']
        else:
            more = False
