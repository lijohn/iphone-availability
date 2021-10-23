import json
import requests
import time
import boto3

def lambda_handler(event, context):
    url = 'https://www.apple.com/shop/fulfillment-messages?parts.0=MLTT3LL/A&location='
    zipCodes = ['19702', '22043', '07078']
    evaluatedStores, availableStores = set(), set()
    message = 'iPhone not available'
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('iphone-availability')
    currentTime = int(time.time())

    for zipCode in zipCodes:
        response = requests.get(url + zipCode).json()
        stores = response['body']['content']['pickupMessage']['stores']
        for store in stores:
            storeName = store['storeName']
            if storeName not in evaluatedStores and is_available(store):
                storeUpdate = get_store_update(table, storeName)
                if storeUpdate:
                    lastMessage = storeUpdate['last_message']
                    if currentTime > lastMessage + 600:
                        availableStores.add(storeName)
                        update_store(table, storeName, currentTime)
                    else:
                        update_store(table, storeName, lastMessage)
                else:
                    availableStores.add(storeName)
                    update_store(table, storeName, currentTime)
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

def update_store(table, store, lastMessage):
    table.put_item(
        Item={
            'key': store,
            'last_message': lastMessage,
            'last_update': time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime())
        }
    )

def send_message(message):
    client = boto3.client('sns')
    client.publish(
        TopicArn='arn:aws:sns:us-east-1:233229421924:iphone-availability',
        Message=message
    )