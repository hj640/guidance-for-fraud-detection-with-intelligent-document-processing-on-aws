from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct

from insurance_claim_process_cdk.dynamodb import DynamoDBStack
from insurance_claim_process_cdk.lambdafn import LambdaStack
from insurance_claim_process_cdk.s3 import S3Stack
from insurance_claim_process_cdk.statemachines import BaseSfnStateMachineStack
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

class WorkflowStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        stepfunctions = BaseSfnStateMachineStack(self, "InsuranceClaimProcessStepFunctions", config["BDA"]["projectArn"])
        s3 = S3Stack(self, "InsuranceClaimProcessS3")
        dynamodb = DynamoDBStack(self, "InsuranceClaimProcessDynamoDB")
        lambda_ = LambdaStack(self, "InsuranceClaimProcessLambda")