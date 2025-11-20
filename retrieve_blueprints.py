import boto3
import json
import os

client = boto3.client('bedrock-data-automation', region_name='us-east-1')
project_arn = "arn:aws:bedrock:us-east-1:730076539151:data-automation-project/30fafe32db59"

# List all blueprints using projectFilter
response = client.list_blueprints(projectFilter={'projectArn': project_arn})

# Create directory for schemas
os.makedirs('schemas', exist_ok=True)

for i, blueprint in enumerate(response['blueprints']):
    blueprint_arn = blueprint['blueprintArn']
    blueprint_name = blueprint.get('blueprintName', f'blueprint_{i}')
    
    print(f"Getting schema for: {blueprint_name}")
    
    # Get blueprint details
    blueprint_response = client.get_blueprint(blueprintArn=blueprint_arn)
    schema_string = blueprint_response['blueprint']['schema']
    
    # Parse the escaped JSON string
    schema = json.loads(schema_string)
    
    # Save formatted schema to file
    filename = f"schemas/{blueprint_name}_schema.json"
    with open(filename, 'w') as f:
        json.dump(schema, f, indent=2)
    
    print(f"Saved: {filename}")

print("All schemas downloaded to schemas/ directory")



