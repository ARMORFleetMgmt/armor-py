# armor-py


This package provides some useful scripts for interacting with the ARMOR Fleet Management platform from Python.

It implements the REST API that is available here: https://app.armordata.io/swaggerui/

This package is expected to change frequently, and may be replaced by a formal python SDK in the future.

## Using the client
```python

from client import ArmorClient

# authenticating with an application token
client = ArmorClient("https://app.armordata.io/api/v1/", token="AT:adfasdf....asdfasd")

# authenticating with a username and password
client = ArmorClient("https://app.armordata.io/api/v1/", username="user@domain.com", password="password")

resp = client.request("GET", "asset", query={"limit": 20})
```

## Utilities
### scrape_data.py
This utility downloads assets, sites, and history to JSON files.
```bash
python scrape_data.py -t "AT:xxxx" -d 30
```
* -u: The URL used to access the Armor platform API.
* -t: The application token used to authenticate with the platform.
* -d: The number of days of history to download.

## License

Mozilla Public License Version 2.0