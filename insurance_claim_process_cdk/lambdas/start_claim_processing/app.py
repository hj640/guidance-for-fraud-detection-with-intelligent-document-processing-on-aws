"""
A lambda function which retrieves claim report from a dynamodb table insuranceclaim-reports-json using a partition key claimId
"""
import boto3
import json
import os

sfn = boto3.client('stepfunctions')

def lambda_handler(event, context):
    account_id = context.invoked_function_arn.split(":")[4]
    region = context.invoked_function_arn.split(":")[3]
    bda_project_arn = os.environ['BDA_PROJECT_ARN']
    claim_id = event["queryStringParameters"]['claim_id']
    response = sfn.start_execution(
        stateMachineArn=f"arn:aws:states:{region}:{account_id}:stateMachine:insuranceclaim-ClaimProcessing",
        input=json.dumps({ "claimId": claim_id,
                    "inputBucket": f"insuranceclaim-input-{account_id}-{region}",
                    "outputBucket": f"insuranceclaim-output-{account_id}-{region}",
                    "bdaProjectArn": bda_project_arn})
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(response, default = str),
        'headers': {
            "Access-Control-Allow-Origin": "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials": True, # Required for cookies, authorization headers with HTTPS
        },
    }