# model_registry.py
import boto3
import argparse
from datetime import datetime

def list_models(model_package_group_name="document-tampering-models"):
    """List all models in registry"""
    sagemaker = boto3.client('sagemaker')
    
    response = sagemaker.list_model_packages(
        ModelPackageGroupName=model_package_group_name,
        SortBy='CreationTime',
        SortOrder='Descending'
    )
    
    print(f"📦 Models in {model_package_group_name}:")
    for package in response['ModelPackageSummaryList']:
        print(f"  • {package['ModelPackageArn']}")
        print(f"    Status: {package['ModelPackageStatus']}")
        print(f"    Approval: {package['ModelApprovalStatus']}")
        print(f"    Created: {package['CreationTime']}")
        print()

def approve_model(model_package_arn):
    """Approve model for deployment"""
    sagemaker = boto3.client('sagemaker')
    
    sagemaker.update_model_package(
        ModelPackageArn=model_package_arn,
        ModelApprovalStatus='Approved'
    )
    print(f"✅ Model approved: {model_package_arn}")

def main():
    parser = argparse.ArgumentParser(description='Manage model registry')
    parser.add_argument('--list', action='store_true', help='List all models')
    parser.add_argument('--approve', help='Approve model by ARN')
    
    args = parser.parse_args()
    
    if args.list:
        list_models()
    elif args.approve:
        approve_model(args.approve)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
