import configparser
from aws_cdk import (
    # Duration,
    Stack,
    NestedStack,
    # aws_sqs as sqs,
)
from constructs import Construct

from insurance_claim_process_cdk.workflow import WorkflowStack
from insurance_claim_process_cdk.api import ApiStack
from insurance_claim_process_cdk.frontend import FrontEndStack

config = configparser.ConfigParser()
config.read('config.ini')

class InsuranceClaimProcessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.template_options.description = "Guidance for Fraud Detection with Intelligent Document Processing on AWS - Workflow"
        workflow = WorkflowStack(self, "InsuranceClaimProcessWorkflow")

class InsuranceClaimProcessApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.template_options.description = "Guidance for Fraud Detection with Intelligent Document Processing on AWS - API"
        api = ApiStack(self, "InsuranceClaimProcessApi")

class InsuranceClaimProcessFrontEndStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.template_options.description = "Guidance for Fraud Detection with Intelligent Document Processing on AWS - FrontEnd"
        frontend = FrontEndStack(self, "InsuranceClaimProcessFrontEnd")
