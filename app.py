#!/usr/bin/env python3
import configparser
import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks, NagSuppressions


from insurance_claim_process_cdk.insurance_claim_process_stack import InsuranceClaimProcessStack
from insurance_claim_process_cdk.insurance_claim_process_stack import InsuranceClaimProcessApiStack
from insurance_claim_process_cdk.insurance_claim_process_stack import InsuranceClaimProcessFrontEndStack

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="aws_cdk")
warnings.filterwarnings("ignore", category=UserWarning, module="cdk_nag")

config = configparser.ConfigParser()
config.read('config.ini')

app = cdk.App()


# Add AwsSolutionsChecks to your entire app
cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

workflow_stack = InsuranceClaimProcessStack(app, "InsuranceClaimProcessStack",
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    env=cdk.Environment(region=config["AWS"]["region"]),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
)

api_stack = InsuranceClaimProcessApiStack(app, "InsuranceClaimProcessApiStack",
    env=cdk.Environment(region=config["AWS"]["region"])
)

frontend_stack = InsuranceClaimProcessFrontEndStack(app, "InsuranceClaimProcessFrontEndStack",
    env=cdk.Environment(region=config["AWS"]["region"])
)

nag_suppressions = [
    {"id": "AwsSolutions-S1", "reason": "Server Access Logging is not required for non-production code."},
    {"id": "AwsSolutions-IAM4", "reason": "Managed policies are acceptable for non-production code."},
    {"id": "AwsSolutions-IAM5", "reason": "IAM policies are with '*' resources have been reviewed that they only have access to log destinations or resource names have prefixes."},
    {"id": "AwsSolutions-L1", "reason": "Lambda functions have dependencies on Python 3.11"},
    {"id": "AwsSolutions-COG1", "reason": "Token-based API is acceptable for non-production code."},
    {"id": "AwsSolutions-COG2", "reason": "User pool is acceptable for non-production code."},
    {"id": "AwsSolutions-COG3", "reason": "User pool is acceptable for non-production code."},
    {"id": "AwsSolutions-APIG1", "reason": "Access logging is acceptable for non-production code."},
    {"id": "AwsSolutions-APIG2", "reason": "Request validation is acceptable for non-production code."},
    {"id": "AwsSolutions-APIG3", "reason": "WAF is acceptable for non-production code."},
    {"id": "AwsSolutions-APIG4", "reason": "API keys are acceptable for non-production code."},
    {"id": "AwsSolutions-COG4", "reason": "Cognito user pool is acceptable for non-production code."},
    {"id": "AwsSolutions-APIG6", "reason": "API steps are acceptable for non-production code."},
    {"id": "AwsSolutions-APIG2", "reason": "Request validation is acceptable for non-production code."},
    {"id": "AwsSolutions-SF1", "reason": "Step function is acceptable for non-production code."},
    {"id": "AwsSolutions-SF2", "reason": "X-Ray is acceptable for non-production code."},
    {"id": "AwsSolutions-SNS3", "reason": "SNS topic is acceptable for non-production code."},
    {"id": "AwsSolutions-CFR1", "reason": "The CloudFront distribution may require Geo restrictions"},
    {"id": "AwsSolutions-CFR2", "reason": "The Web Application Firewall"},
    {"id": "AwsSolutions-CFR4", "reason": "The CloudFront distribution allows for SSLv3 or TLSv1 for HTTPS viewer connections"},
    {"id": "AwsSolutions-CFR7", "reason": "The CloudFront distribution does not have an associated WAFWebACL"},
    {"id": "AwsSolutions-DDB3", "reason": "Point-in-time Recovery is acceptable for non-production code."}
]

for stack in [workflow_stack, api_stack, frontend_stack]:
    NagSuppressions.add_stack_suppressions(
        stack,
        nag_suppressions,
        apply_to_nested_stacks=True
    )

app.synth()
