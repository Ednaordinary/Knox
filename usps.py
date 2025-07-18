import os
import requests
import traceback
from dotenv import load_dotenv

load_dotenv()

def get_token(ref=False):
    if not ref:
        with open("token.txt", "r") as token_file:
            token = token_file.read()
            if token.strip() == "":
                return get_token(ref=True)
        return token
    else:
        #os.getenv('DISCORD_TOKEN')
        data = {
            "client_id": os.getenv('USPS_CLIENT_ID'),
            "client_secret": os.getenv('USPS_CLIENT_SECRET'),
            "grant_type": "client_credentials",
        }
        response = requests.post("https://apis.usps.com/oauth2/v3/token", json=data)
        if response.status_code != 200:
            print(response.json())
            return None
        token = response.json()["access_token"]
        with open("token.txt", "w") as token_file:
            token_file.write(token)
        return token

def get_price_single(token, zip_code, weight):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + str(token),
    }
    data = {
        "originZIPCode": os.getenv('ORIGIN_ZIP'),
        "destinationZIPCode": str(zip_code),
        "weight": weight,
        "height": 0,
        "length": 0,
        "width": 0,
        "mailClass": "USPS_GROUND_ADVANTAGE",
        "processingCategory": "MACHINABLE",
        "rateIndicator": "SP",
        "priceType": "COMMERCIAL",
        "destinationEntryFacilityType": "NONE",
    }
    try:
        response = requests.post("https://apis.usps.com/prices/v3/base-rates/search", headers=headers, json=data)
        print(response)
        if response.status_code != 200:
            print(response.json())
            return None
        return response.json()["totalBasePrice"]
    except:
        print(traceback.format_exc())
        return None

def get_price(zip_code, weight):
    token = get_token()
    if token == None:
        return None
    price = get_price_single(token, zip_code, weight)
    if price == None:
        token = get_token(ref=True)
        if token == None:
            return None
        price = get_price_single(token, zip_code, weight)
        if price == None:
            return None
        return price
    return price
