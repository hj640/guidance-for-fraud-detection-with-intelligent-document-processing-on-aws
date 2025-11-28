# deployment_pipeline.py
import sagemaker
import boto3
import os
import argparse
from sagemaker.model import ModelPackage
from sagemaker.serverless import ServerlessInferenceConfig
from sagemaker import get_execution_role
import configparser

def setup_sagemaker_session():
    """Initialize SageMaker session and get role"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    region = config.get('AWS', 'region', fallback='us-east-1')
    
    boto3.setup_default_session(region_name=region)
    os.environ['AWS_DEFAULT_REGION'] = region
    
    boto3_session = boto3.Session()
    sagemaker_session = sagemaker.Session(boto_session=boto3_session)
    
    try: 
        sagemaker_role = get_execution_role()
    except ValueError:
        iam = boto3.client('iam')
        sagemaker_role = iam.get_role(RoleName='SageMakerExecutionRole')['Role']['Arn']
    
    return sagemaker_session, sagemaker_role

def get_serverless_config(stage):
    """Get serverless configuration based on environment"""
    configs = {
        'dev': {
            'memory_size_in_mb': 1024,
            'max_concurrency': 5
        },
        'staging': {
            'memory_size_in_mb': 2048,
            'max_concurrency': 10
        },
        'prod': {
            'memory_size_in_mb': 4096,
            'max_concurrency': 50
        }
    }
    
    config = configs.get(stage, configs['dev'])
    return ServerlessInferenceConfig(
        memory_size_in_mb=config['memory_size_in_mb'],
        max_concurrency=config['max_concurrency']
    )

def deploy_model(model_package_arn, stage, sagemaker_session):
    """Deploy model from registry to specified environment"""
    
    # Create model from registry
    model = ModelPackage(
        model_package_arn=model_package_arn,
        sagemaker_session=sagemaker_session
    )
    
    # Get serverless config for environment
    serverless_config = get_serverless_config(stage)
    
    # Deploy with environment-specific endpoint name
    endpoint_name = f"document-tampering-{stage}"
    
    try:
        predictor = model.deploy(
            initial_instance_count=1,
            endpoint_name=endpoint_name,
            serverless_inference_config=serverless_config
        )
        return predictor.endpoint_name
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️ Endpoint {endpoint_name} already exists, updating...")
            # Update existing endpoint
            predictor = model.deploy(
                initial_instance_count=1,
                endpoint_name=endpoint_name,
                serverless_inference_config=serverless_config,
                update_endpoint=True
            )
            return predictor.endpoint_name
        else:
            raise e

def approve_model(model_package_arn):
    """Approve model in registry for deployment"""
    sagemaker_client = boto3.client('sagemaker')
    
    sagemaker_client.update_model_package(
        ModelPackageArn=model_package_arn,
        ModelApprovalStatus='Approved'
    )
    print(f"✅ Model approved: {model_package_arn}")

def main():
    parser = argparse.ArgumentParser(description='Deploy model to specified environment')
    parser.add_argument('--stage', choices=['dev', 'staging', 'prod'], 
                       default='dev', help='Deployment environment')
    parser.add_argument('--model-package-arn', help='Model package ARN to deploy')
    parser.add_argument('--approve', action='store_true', 
                       help='Auto-approve model for deployment')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Deployment Pipeline for {args.stage}...")
    
    # Setup
    sagemaker_session, _ = setup_sagemaker_session()
    
    # Get model package ARN
    if args.model_package_arn:
        model_package_arn = args.model_package_arn
    else:
        # Read from training pipeline output
        try:
            with open('model_package_arn.txt', 'r') as f:
                model_package_arn = f.read().strip()
        except FileNotFoundError:
            print("❌ No model package ARN found. Run training pipeline first or provide --model-package-arn")
            return
    
    print(f"📦 Using model: {model_package_arn}")
    
    # Auto-approve if requested
    if args.approve:
        approve_model(model_package_arn)
    
    # Deploy model
    endpoint_name = deploy_model(model_package_arn, args.stage, sagemaker_session)
    print(f"✅ Model deployed to {args.stage}: {endpoint_name}")
    
    # Save endpoint info
    with open(f'endpoint_{args.stage}.txt', 'w') as f:
        f.write(endpoint_name)
    
    print(f"🎉 Deployment to {args.stage} completed!")
    print(f"🔗 Endpoint: {endpoint_name}")

if __name__ == "__main__":
    main()
