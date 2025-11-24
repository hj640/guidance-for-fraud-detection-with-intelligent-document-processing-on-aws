import json
import boto3
import os

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    params = event.get('queryStringParameters', {})
    claim_id = params.get('claimId')
    file_name = params.get('fileName')
    
    if not claim_id or not file_name:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'claimId and fileName required'}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }
    
    bucket = os.environ['INPUT_BUCKET']
    key = f"{claim_id}/{file_name}"
    
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=3600
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'url': url}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }
