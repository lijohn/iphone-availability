# iphone-availability
Script for AWS Lambda to check for iPhone 13 Pro in-store pickup availability

## Design
A CloudWatch Event trigger invokes the Lambda every minute, which calls Apple's API and gets the availability of all of the stores in the given zip codes. 

The Lambda then checks a DynamoDB table to see whether the store has had stock in the last 10 minutes (to prevent repeated notifications), updates the table, and adds the store to a list to be sent out as a message.
The Dynamo table can be separately queried to see when each store last had iPhones in stock, and how many times a notification has been sent out for that store.

After creating the message, the Lambda sends it out through an SNS topic with email subscriptions.

## Future

This code can be reused for any Apple product as the product model can be inputted as a parameter through the same API. 
Additional emails, products, and locations can be onboarded, with subscription filters being attached per email subscription.
