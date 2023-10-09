# iphone-availability
Script for AWS Lambda to check for iPhone in-store pickup availability

## Design
A CloudWatch Event trigger invokes the Lambda every minute, which calls Apple's API to get the availability of any given Apple product (by part name) for nearby stores around the given locations (zip code or city), with the option to filter by states.

The Lambda then checks a DynamoDB table to see whether a notification cooldown period for the store has passed (to prevent repeated notifications), updates the table, and adds the store to a list to be sent out as a message.
The DynamoDB table uses the store name as the partition key and the Apple part ID as the sort key to allow for multiple product models to be tracked per invocation.
The Dynamo table can be separately queried to see when each store last had a given Apple device in stock, and how many total minutes that store has had stock.

After creating the message, the Lambda sends it out through an SNS topic with email subscriptions. Individual SNS subscriptions can filter for their desired models with a message attributes scoped subscription filter.
