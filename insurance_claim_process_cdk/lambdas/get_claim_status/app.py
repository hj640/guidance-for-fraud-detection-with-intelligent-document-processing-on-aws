import boto3
import json

dynamodb = boto3.resource('dynamodb')
sfn = boto3.client('stepfunctions')

def lambda_handler(event, context):
    claim_id = event['pathParameters']['claimId']
    account_id = context.invoked_function_arn.split(":")[4]
    region = context.invoked_function_arn.split(":")[3]
    
    # Check if report exists (processing complete)
    table = dynamodb.Table('insuranceclaim-reports-json')
    response = table.get_item(Key={'claimId': claim_id})
    
    if 'Item' in response:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'COMPLETED',
                'claimId': claim_id
            }),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            }
        }
    
    # Check Step Functions execution status
    try:
        executions = sfn.list_executions(
            stateMachineArn=f"arn:aws:states:{region}:{account_id}:stateMachine:insuranceclaim-ClaimProcessing",
            maxResults=50
        )
        
        for execution in executions['executions']:
            exec_input = json.loads(sfn.describe_execution(executionArn=execution['executionArn'])['input'])
            if exec_input.get('claimId') == claim_id:
                if execution['status'] == 'FAILED':
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'status': 'FAILED',
                            'claimId': claim_id
                        }),
                        'headers': {
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Credentials': True
                        }
                    }
                break
    except Exception as e:
        print(f"Error checking execution status: {e}")
    
    # Otherwise, still processing
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'PROCESSING',
            'claimId': claim_id
        }),
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        }
    }
