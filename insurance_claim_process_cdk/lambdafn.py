from aws_cdk import aws_lambda as lambda_, aws_iam as iam, App, Duration, NestedStack

# Read config.ini
import configparser
from aws_cdk import aws_lambda
from cdk_nag import NagSuppressions

config = configparser.ConfigParser()
config.read("config.ini")


class LambdaStack(NestedStack):
    def __init__(self, app: App, id: str) -> None:
        super().__init__(app, id)

        # Add suppressions for the AwsSolutions-IAM4 finding
        NagSuppressions.add_stack_suppressions(
            self,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Lambda functions require basic execution role for CloudWatch Logs access",
                    "appliesTo": [
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ]
                }
            ]
        )

        with open(
            "insurance_claim_process_cdk/lambdas/raw_json_processing/app.py",
            encoding="utf8",
        ) as fp:
            handler_code = fp.read()
        lambda_raw_json_processing = lambda_.Function(
            self,
            "RawJsonProcessing",
            function_name="insuranceclaimRawJsonProcessing",
            code=lambda_.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_13,
        )
        lambda_role = lambda_raw_json_processing.role
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem", "dynamodb:PutItem"],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/insuranceclaim-bda-results-raw"
                ],
            )
        )
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket", "s3:GetObject"],
                resources=[
                    f"arn:aws:s3:::insuranceclaim-output-{self.account}-{self.region}",
                    f"arn:aws:s3:::insuranceclaim-output-{self.account}-{self.region}/*",
                ],
            )
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket", "s3:GetObject"],
                resources=[
                    f"arn:aws:s3:::insuranceclaim-input-{self.account}-{self.region}",
                    f"arn:aws:s3:::insuranceclaim-input-{self.account}-{self.region}/*",
                ],
            )
        )

        with open(
            "insurance_claim_process_cdk/lambdas/image_tampering_detection/app.py",
            encoding="utf8",
        ) as fp:
            handler_code = fp.read()
        endpoint_name = config["SM_ENDPOINT"]["tampered_image_detection_endpoint"]

        pandas_layer_version = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            "PandasLayerVersion",
            layer_version_arn="arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:4",
        )

        lambda_image_tampering_detection = lambda_.Function(
            self,
            "ImageTamperingDetection",
            function_name="insuranceclaimImageTamperingDetection",
            code=lambda_.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_11,
            environment={"ENDPOINT_NAME": endpoint_name},
            layers=[pandas_layer_version],
        )
        lambda_role = lambda_image_tampering_detection.role
        # Add inline IAM policy to lambda_role, allowing invoke endpoint of SageMaker
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sagemaker:InvokeEndpoint"],
                resources=[
                    f"arn:aws:sagemaker:{self.region}:{self.account}:endpoint/{endpoint_name}"
                ],
            )
        )
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket", "s3:GetObject"],
                resources=[
                    f"arn:aws:s3:::insuranceclaim-input-{self.account}-{self.region}",
                    f"arn:aws:s3:::insuranceclaim-input-{self.account}-{self.region}/*",
                ],
            )
        )


        with open(
            "insurance_claim_process_cdk/lambdas/json_report_generation/app.py",
            encoding="utf8",
        ) as fp:
            handler_code = fp.read()
   
        lambda_json_report_generation = lambda_.Function(
            self,
            "GenerateJSONReport",
            function_name="insuranceclaimJsonReportGeneration",
            code=lambda_.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_13
        )
        lambda_role = lambda_json_report_generation.role
        # Add inline IAM policy to lambda_role, allowing invoke endpoint of SageMaker
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem", "dynamodb:Query"],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/insuranceclaim-bda-results-raw"
                ],
            )
        )


        with open(
            "insurance_claim_process_cdk/lambdas/put_item_dynamodb/app.py",
            encoding="utf8",
        ) as fp:
            handler_code = fp.read()
   
        lambda_put_item_dynamodb = lambda_.Function(
            self,
            "PutItemDynamodb",
            function_name="insuranceclaim-PutItemDynamodb",
            code=lambda_.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_13
        )
        lambda_role = lambda_put_item_dynamodb.role
        # Add inline IAM policy to lambda_role, allowing invoke endpoint of SageMaker
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem", "dynamodb:PutItem"],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/insuranceclaim*"
                ],
            )
        )