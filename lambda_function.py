import json
import requests
import boto3

def lambda_handler(event, context):
    url = 'https://www.apple.com/shop/fulfillment-messages?parts.0=MLTT3LL/A&location='
    zipCodes = ['19702', '22043', '07078', '10003']
    availableStores = []
    message = 'iPhone not available'

    for zipCode in zipCodes:
        response = requests.get(url + zipCode).json()
        stores = response['body']['content']['pickupMessage']['stores']
        for store in stores:
            availability = store['partsAvailability']['MLTT3LL/A']
            if availability['storeSelectionEnabled'] or availability['pickupDisplay'] == 'available':
                availableStores.append(store['storeName'])
                break

    if len(availableStores) > 0:
        message = 'iPhone available at ' + ', '.join(availableStores)
        print(message)
        client = boto3.client('sns')
        client.publish(
            TopicArn='arn:aws:sns:us-east-1:233229421924:iphone-availability',
            Message=message
        )

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }
