# training_pipeline.py
import sagemaker
import boto3
import os
import subprocess
from sagemaker.tensorflow import TensorFlow
from sagemaker.model import ModelPackage
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

def upload_training_data(sagemaker_session):
    """Upload training data to S3"""
    bucket = sagemaker_session.default_bucket()
    subprocess.run([
        "aws", "s3", "cp", "--recursive", 
        "./CASIA2", f"s3://{bucket}/tampered-image-train/"
    ], shell=False)
    return f"s3://{bucket}/tampered-image-train/"

def train_model(sagemaker_session, sagemaker_role, training_data_path):
    """Train the model"""
    estimator = TensorFlow(
        sagemaker_session=sagemaker_session,
        entry_point='model.py',
        role=sagemaker_role,
        instance_count=1,
        instance_type='ml.m5.4xlarge',
        framework_version='2.1.0',
        py_version='py3',
    )
    
    estimator.fit({'train': training_data_path})
    return estimator

def register_model(estimator, model_package_group_name="document-tampering-models"):
    """Register model in SageMaker Model Registry"""
    model_package = estimator.register(
        model_package_group_name=model_package_group_name,
        approval_status="PendingManualApproval",
        description="Document tampering detection model",
        inference_instances=["ml.t2.medium", "ml.m5.large"],
        transform_instances=["ml.m5.large"]
    )
    return model_package.model_package_arn

def main():
    print("🚀 Starting Training Pipeline...")
    
    # Setup
    sagemaker_session, sagemaker_role = setup_sagemaker_session()
    print(f"✅ SageMaker role: {sagemaker_role}")
    
    # Upload data
    training_data_path = upload_training_data(sagemaker_session)
    print(f"✅ Training data uploaded: {training_data_path}")
    
    # Train model
    estimator = train_model(sagemaker_session, sagemaker_role, training_data_path)
    print(f"✅ Model trained: {estimator.model_data}")
    
    # Register model
    model_package_arn = register_model(estimator)
    print(f"✅ Model registered: {model_package_arn}")
    
    # Save model package ARN for deployment
    with open('model_package_arn.txt', 'w') as f:
        f.write(model_package_arn)
    
    print("🎉 Training pipeline completed!")

if __name__ == "__main__":
    main()