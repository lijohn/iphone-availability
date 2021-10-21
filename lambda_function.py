import json
import requests
from time import time
import boto3

def lambda_handler(event, context):
    url = 'https://www.apple.com/shop/fulfillment-messages?parts.0=MLTT3LL/A&location='
    zipCodes = ['19702', '22043', '07078']
    availableStores = set()
    message = 'iPhone not available'

    for zipCode in zipCodes:
        response = requests.get(url + zipCode).json()
        stores = response['body']['content']['pickupMessage']['stores']
        for store in stores:
            availability = store['partsAvailability']['MLTT3LL/A']
            if availability['storeSelectionEnabled'] or availability['pickupDisplay'] == 'available':
                availableStores.add(store['storeName'])
                break

    if len(availableStores) > 0:
        message = 'iPhone available at ' + ', '.join(availableStores)

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('iphone-availability')
        lastMessage = get_last_message(table)

        currentTime = int(time())
        count = lastMessage['count']
        lastUpdate = lastMessage['timestamp']

        # only send repeated messages every 10 minutes
        if lastMessage['message'] == message:
            if currentTime > lastUpdate + 600:
                send_message(message + " (" + str(count) + " minutes)")
                lastUpdate = currentTime
            update_last_message(table, message, lastUpdate, count + 1)
        else:
            send_message(message)
            update_last_message(table, message, currentTime, 0)

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }

def get_last_message(table):
    item = table.get_item(Key={'key': 'lastMessage'})
    return item['Item']

def update_last_message(table, message, currentTime, count):
    table.put_item(
        Item={
            'key': 'lastMessage',
            'message': message,
            'timestamp': currentTime,
            'count': count
        }
    )

def send_message(message):
    client = boto3.client('sns')
    client.publish(
        TopicArn='arn:aws:sns:us-east-1:233229421924:iphone-availability',
        Message=message
    )