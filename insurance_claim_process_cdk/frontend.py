
import os

from aws_cdk import (
    # Duration,
    CfnOutput,
    Duration,
    Stack,
    aws_iam,
    aws_s3,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_s3_deployment,
    RemovalPolicy,
)
from constructs import Construct


class FrontEndStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # create S3 bucket     
        cloudfront_bucket = aws_s3.Bucket(
            self,
            f"insuranceclaim-frontend-bucket",
            bucket_name=f"insuranceclaim-frontend-{self.account}-{self.region}",
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            enforce_ssl=True,
            #auto_delete_objects=True,
            object_ownership=aws_s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
        )
        
        # Create Origin Access Control
        origin_access_control = aws_cloudfront.CfnOriginAccessControl(
            self,
            "OAC",
            origin_access_control_config=aws_cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="OAC",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4"
            )
        )

        # Create CloudFront distribution
        # S3 bucket for CloudFront logs
        cloudfront_logs_bucket_name = f"insuranceclaim-cloudfront-logs-{self.account}-{self.region}"
        cloudfront_logs_bucket = aws_s3.Bucket(
            self, "CloudFrontLogsBucket",
            bucket_name=cloudfront_logs_bucket_name,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=aws_s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,  # Required for CloudFront logs
            lifecycle_rules=[
                aws_s3.LifecycleRule(
                    expiration=Duration.days(90)  # Auto-delete logs after 90 days
                )
            ]
        )

        spa_distribution = aws_cloudfront.Distribution(
            self,
            "CloudFrontDistributionSPA",
            
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.S3BucketOrigin(
                    bucket=cloudfront_bucket,
                ),
                viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=aws_cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            error_responses=[
                aws_cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html"
                ),
                aws_cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html"
                )
            ],
            log_bucket=cloudfront_logs_bucket,
        )

        # Add OAC to the distribution's S3 origin
        cfn_distribution = spa_distribution.node.default_child
        cfn_distribution.add_property_override(
            "DistributionConfig.Origins.0.S3OriginConfig.OriginAccessIdentity", ""
        )
        cfn_distribution.add_property_override(
            "DistributionConfig.Origins.0.OriginAccessControlId", 
            origin_access_control.attr_id
        )

        # Grant CloudFront access to the bucket
        cloudfront_bucket.add_to_resource_policy(
            aws_iam.PolicyStatement(
                actions=["s3:*"],
                resources=[cloudfront_bucket.arn_for_objects("*")],
                principals=[aws_iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{spa_distribution.distribution_id}"
                    }
                }
            )
        )

        # Deploy React app to S3
        if os.path.exists("./frontend/build"):
            aws_s3_deployment.BucketDeployment(
                self,
                "DeployReactApp",
                sources=[aws_s3_deployment.Source.asset("./frontend/build")],  # Adjust the path to your React build folder
                destination_bucket=cloudfront_bucket,
                distribution=spa_distribution,
                distribution_paths=["/*"]
            )

        CfnOutput(self, "UIDomain", value=spa_distribution.domain_name, description="API Gateway endpoint URL")
