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
parser.add_argument('-s', '--serial', help='Serial number of the asset to download', default='')  # New argument

args = parser.parse_args()

client = ArmorClient(args.url, token=args.token, debug=True)

today = datetime.date.today()
startDate = today - datetime.timedelta(days=int(args.days))

fileName = "assets." + today.strftime('%Y%m%d%H%M%S') + ".json"

# download assets
print(f"Downloading assets...")
more = True
first = True
next_page = "true"
assets = dict()

query = None
if args.serial:  # If serial number is provided, filter by it
    query = f'properties.serialNumber=={args.serial}"'
elif args.customer:  # Otherwise, filter by customer
    query = f'tags.customer=="{args.customer}"'

count = 0
total = 0
while more:
    if first:
        resp = client.request("GET", "asset", query={"search": query, "limit": 2000, "next": next_page, "total": True})
    else:
        resp = client.request("GET", "asset", query={"search": query, "limit": 2000, "next": next_page})
    if resp.body['count'] > 0:
        if first:
            total = resp.body['total']
        count += resp.body['count']
        print(f"Got {count}/{total} assets, first: {resp.body['objects'][0]['id']}, last: {resp.body['objects'][-1]['id']}")
        for record in resp.body['objects']:
            assets[record['id']] = record
            first = False
    else:
        more = False
    if 'next' in resp.body:
        next_page = resp.body['next']
    else:
        more = False

# Manually query the site using siteId
print(f"Downloading sites...")
sites = dict()

if args.serial and assets:
    asset = next(iter(assets.values()))
    site_id = asset.get("siteId")
    if site_id:
        site_query = f'id=="{site_id}"'
        print(f"Querying site with site_id: {site_id}")  # Debugging output
        # Manually construct the query to double-check
        resp = client.request("GET", f"site/{site_id}")
        if resp.body:
            site = resp.body
            sites[site['id']] = site
            print(f"Got site: {site}")  # Debugging output
        else:
            print(f"No site found for site_id: {site_id}")  # Debugging output
    else:
        print("No siteId found in asset")  # Debugging output

elif args.customer:
    # If using customer, query all sites for that customer
    site_query = f'tags.customer=="{args.customer}"'
    more = True
    first = True
    next_page = "true"
    count = 0
    total = 0
    while more:
        if first:
            resp = client.request("GET", "site", query={"search": site_query, "limit": 2000, "next": next_page, "total": True})
        else:
            resp = client.request("GET", "site", query={"search": site_query, "limit": 2000, "next": next_page})
        if resp.body['count'] > 0:
            if first:
                total = resp.body['total']
            count += resp.body['count']
            print(f"Got {count}/{total} sites, first: {resp.body['objects'][0]['id']}, last: {resp.body['objects'][-1]['id']}")
            for record in resp.body['objects']:
                sites[record['id']] = record
                first = False
        else:
            more = False
        if 'next' in resp.body:
            next_page = resp.body['next']
        else:
            more = False

fileName = "legacy_raw." + today.strftime('%Y%m%d%H%M%S') + ".csv"

def field_or_blank(d, field):
    return d.get(field, "") if d else ""

def convert_category(cat):
    categories = {
        "run-start": "RunStart",
        "run-stop": "RunTime",
        "charge-start": "ChargeStart",
        "charge-stop": "ChargeTime"
    }
    return categories.get(cat, "Misc")

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
    next_page = None
    while more:
        q = {"limit": 20000, "utc": True, "start": start, "end": end, "search": f'assetId=="{list(assets.keys())[0]}"'}
        if next_page:
            q['next'] = next_page
        # print(f"Querying history with: {q}")  # Debugging output
        resp = client.request("GET", "history/json", query=q)
        print(f"History response count: {resp.body['count']}")
        # print(f"History response sample: {resp.body['objects'][0] if resp.body['count'] > 0 else 'No records'}")

        if 'next' in resp.body:
            next_page = resp.body['next']
        else:
            next_page = None
            more = False
        if resp.body['count'] > 0:
            count += resp.body['count']
            for record in resp.body['objects']:
                asset = assets.get(record['m']['assetId'])
                if not asset:
                    # print(f"Warning: Asset ID {record['m']['assetId']} not found in assets.")
                    continue
                
                # Retrieve site details using siteId from the history record
                site_id = record['m'].get('siteId')
                site = sites.get(site_id) if site_id else None

                # Extract data from asset tags
                tags = asset.get('tags', {})
                company_name = tags.get('_manufacturer', '')  # Example of retrieving a value from asset tags
                model_name = tags.get('_model', '')
                serial_number = asset['properties'].get('serialNumber', '')
                nickname = asset.get('name', '')
                asset_ident = asset['properties'].get('oldAssetIdent', '')

                # Retrieve site information
                site_name = site['name'] if site else ''
                city = site['address'].get('city', '') if site and 'address' in site else ''
                state = site['address'].get('state', '') if site and 'address' in site else ''
                cusi = site['properties'].get('cusi', '') if site and 'properties' in site else ''

                # Debugging: Print out the linked site data
                # print(f"Linked site details - SiteName: {site_name}, City: {city}, State: {state}")  # Debugging output

                # Convert timestamps
                report_date = datetime.datetime.fromisoformat(record['ts']).strftime('%m/%d/%Y')

                # Handle runtime data
                minutes = record.get('d', dict()).get('runTime', 0)

                # Handle coordinates
                latitude = record['l']['coordinates'][1] if record.get('l') else 0
                longitude = record['l']['coordinates'][0] if record.get('l') else 0

                # Write data to CSV
                print(
                    f"{asset_ident},{nickname},{company_name},{model_name},{serial_number},{nickname},{site_name},{city},{state},"
                    f"{convert_category(record['m']['event'])},{report_date},{report_date},{minutes},0,0,0,0,0,0,0,{cusi},0,Active,{latitude},{longitude}",
                    file=f
                )
                first = False
        elif not more:
            break
