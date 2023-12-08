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

args = parser.parse_args()

client = ArmorClient(args.url, token=args.token, debug=False)

today = datetime.datetime.today()

# download assets
print(f"Downloading assets...")
more = True
first = True
next = "true"
assets = []

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
            assets.append(record)
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
        next = resp.body['next']
    else:
        more = False


# download assets
print(f"Building report...")

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

if args.customer:
    fileName = "assets."+args.customer+"."+today.strftime('%Y%m%d%H%M%S') + ".csv"
else:
    fileName = "assets."+today.strftime('%Y%m%d%H%M%S') + ".csv"

with open(fileName, "w") as f:
    print( "assetId,nickname,serialNumber,deviceId,customer,manufacturer,model,siteId,siteName,siteNum,address1,address2,city,state,country,dateLastActivity,runTimeLast1,runTimeLast7,runTimeLast30,chargeTimeLast1,chargeTimeLast7,chargeTimeLast30", file=f)

    for asset in assets:
        if 'siteId' in asset and asset['siteId'] in sites:
            site = sites[asset['siteId']]
            siteName = site['name']
            if 'address' in site:
                address1 = field_or_blank(site['address'], 'address1')
                address2 = field_or_blank(site['address'], 'address2')
                city = field_or_blank(site['address'], 'city')
                state = field_or_blank(site['address'], 'state')
                country = field_or_blank(site['address'], 'country')
            else:
                address1 = ""
                address2 = ""
                city = ""
                state = ""
                country = ""
            if 'tags' in site and 'store' in site['tags']:
                siteNum = site['tags']['store']
            elif 'tags' in site and 'club' in site['tags']:
                siteNum = site['tags']['club']
            else:
                siteNum = -1

        if 'tags' in asset and 'customer' in asset['tags']:
            customer = asset['tags']['customer']
        else:
            customer = "unknown"
        if 'properties' in asset:
            print(f"{asset['id']},{asset['name']},{field_or_blank(asset['properties'],'serialNumber')},{field_or_blank(asset['properties'],'deviceId')},", file=f, end="")
        else:
            print(f"{asset['id']},{asset['name']},,,", file=f, end="")
        print(f"{customer},{field_or_blank(asset,'manufacturerId')},{field_or_blank(asset,'modelId')},", file=f, end="")
        if 'siteId' in asset:
            print(f"{asset['siteId']},{siteName},{siteNum},{address1},{address2},{city},{state},{country},{field_or_blank(asset,'dateLastActivity')},", file=f, end="")
        else:
            print(f",,,,,,{asset['dateLastActivity']},", file=f, end="")
        if 'data' in asset:
            print(f"{field_or_zero(asset['data'],'runTimeLast1')},{field_or_zero(asset['data'],'runTimeLast7')},{field_or_zero(asset['data'],'runTimeLast30')},", file=f, end="")
            print(f"{field_or_zero(asset['data'],'chargeTimeLast1')},{field_or_zero(asset['data'],'chargeTimeLast7')},{field_or_zero(asset['data'],'chargeTimeLast30')}", file=f, end="")
        else:
            print("0,0,0,0,0,0", file=f, end="")
        print("", file=f)
