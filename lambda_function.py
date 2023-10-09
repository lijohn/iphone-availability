import json
import requests
import time
import boto3
import os

parts = ['MTQN3LL/A', 'MTQQ3LL/A', 'MU673LL/A']
locations = ['Portland, OR']
states = ['OR']

DEFAULT_MESSAGE = 'No products available or cooldown has not passed'
COOLDOWN_PERIOD = 900  # time between notifications from the same store

def lambda_handler(event, context):
    for part in parts:
        message = check_store_availability(part)
        if message != DEFAULT_MESSAGE:
            send_message(message, part)

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }

def check_store_availability(part):
    url = 'https://www.apple.com/shop/fulfillment-messages?parts.0={}&location='.format(part)
    evaluatedStores = set()  # can be initialized here as a deny list
    availableStores = set()
    message = DEFAULT_MESSAGE
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMO_TABLE_NAME'])
    currentTime = int(time.time())
    partName = part

    for location in locations:
        response = requests.get(url + location).json()
        stores = response['body']['content']['pickupMessage']['stores']
        for store in stores:
            storeName = store['storeName']
            if storeName not in evaluatedStores and is_available(store, part):
                partName = get_part_name(store, part)
                storeUpdate = get_store_update(table, storeName, part)
                if storeUpdate:
                    lastMessage = storeUpdate['last_message']
                    count = storeUpdate['count']
                    if currentTime > lastMessage + COOLDOWN_PERIOD:
                        availableStores.add(storeName)
                        update_store(table, storeName, part, currentTime, count + 1)
                    else:
                        update_store(table, storeName, part, lastMessage, count + 1)
                else:
                    availableStores.add(storeName)
                    update_store(table, storeName, part, currentTime, 1)
            evaluatedStores.add(storeName)

    if len(availableStores) > 0:
        message = partName + ' available at ' + ', '.join(sorted(availableStores))

    return message

def is_available(store, part):
    availability = store['partsAvailability'][part]
    return store['state'] in states and availability['pickupDisplay'] == 'available'

def get_part_name(store, part):
    return store['partsAvailability'][part]['messageTypes']['regular']['storePickupProductTitle']

def get_store_update(table, store, part):
    item = table.get_item(
        Key={
            'store': store,
            'part': part
        }
    )
    return item.get('Item')

def update_store(table, store, part, lastMessage, count):
    table.put_item(
        Item={
            'store': store,
            'part': part,
            'last_message': lastMessage,
            'last_message_strft': format_time(lastMessage),
            'last_update': format_time(),
            'count': count
        }
    )

def format_time(epochTime=None):
    return time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(epochTime))

def send_message(message, part):
    client = boto3.client('sns')
    client.publish(
        TopicArn=os.environ['SNS_ARN'],
        Message=message,
        MessageAttributes={
            'model': {
                'DataType': 'String',
                'StringValue': part
          }
        }
    )
