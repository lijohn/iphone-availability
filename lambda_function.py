import json
import requests
import time
import boto3

def lambda_handler(event, context):
    url = 'https://www.apple.com/shop/fulfillment-messages?parts.0=MLTT3LL/A&location='
    zipCodes = ['19702', '22043', '07078']
    evaluatedStores = set()  # can be initialized here as a deny list
    availableStores = set()
    message = 'iPhone not available'
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('iphone-availability')
    currentTime = int(time.time())
    cooldown = 900  # time between notifications from the same store

    for zipCode in zipCodes:
        response = requests.get(url + zipCode).json()
        stores = response['body']['content']['pickupMessage']['stores']
        for store in stores:
            storeName = store['storeName']
            if storeName not in evaluatedStores and is_available(store):
                storeUpdate = get_store_update(table, storeName)
                if storeUpdate:
                    lastMessage = storeUpdate['last_message']
                    count = storeUpdate['count']
                    if currentTime > lastMessage + cooldown:
                        availableStores.add(storeName)
                        update_store(table, storeName, currentTime, count + 1)
                    else:
                        update_store(table, storeName, lastMessage, count + 1)
                else:
                    availableStores.add(storeName)
                    update_store(table, storeName, currentTime, 1)
            evaluatedStores.add(storeName)

    if len(availableStores) > 0:
        message = 'iPhone available at ' + ', '.join(sorted(availableStores))
        send_message(message)

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }

def is_available(store):
    availability = store['partsAvailability']['MLTT3LL/A']
    return availability['storeSelectionEnabled'] or availability['pickupDisplay'] == 'available'

def get_store_update(table, store):
    item = table.get_item(Key={'key': store})
    return item.get('Item')

def update_store(table, store, lastMessage, count):
    table.put_item(
        Item={
            'key': store,
            'last_message': lastMessage,
            'last_message_strft': format_time(lastMessage),
            'last_update': format_time(),
            'count': count
        }
    )

def format_time(epochTime=None):
    return time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(epochTime))

def send_message(message):
    client = boto3.client('sns')
    client.publish(
        TopicArn='arn:aws:sns:us-east-1:233229421924:iphone-availability',
        Message=message
    )