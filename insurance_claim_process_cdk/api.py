import configparser
import os

from aws_cdk import (
    # Duration,
    Stack,
    aws_iam,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_s3_deployment,
    aws_apigateway,
    aws_lambda,
    aws_logs,
    RemovalPolicy,
    aws_s3,
    aws_cognito,
    CfnOutput,
    Duration,
)
from cdk_nag import NagSuppressions
from constructs import Construct

config = configparser.ConfigParser()
config.read('config.ini')

class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Add suppressions for the AwsSolutions-IAM4 finding
        cognito_user_pool_name = config["COGNITO"]["user_pool_name"]
        cognito_user_pool_client_name = config["COGNITO"]["user_pool_client_name"]
        # Create Cognito User Pool for authentication
        user_pool = aws_cognito.UserPool(
            self, "InsuranceClaimProcessUserPool",
            user_pool_name=cognito_user_pool_name,
            self_sign_up_enabled=True,
            auto_verify=aws_cognito.AutoVerifiedAttrs(email=True),
            removal_policy=RemovalPolicy.DESTROY,
            password_policy=aws_cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            #advanced_security_mode=aws_cognito.AdvancedSecurityMode.ENFORCED
        )
        
        # Add auto verification for email using CfnUserPool
        cfn_user_pool = user_pool.node.default_child
        cfn_user_pool.auto_verify_attributes = ["email"]
        
        # Create User Pool Client
        user_pool_client = aws_cognito.UserPoolClient(
            self, "EmployeeAssistantClient",
            user_pool_client_name=cognito_user_pool_client_name,
            user_pool=user_pool,
            generate_secret=False,
        )

         # Create log group for API access logs
        api_log_group = aws_logs.LogGroup(
            self, "ApiGatewayLogs",
            retention=aws_logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create REST API
        api = aws_apigateway.RestApi(
            self,
            "InsuranceClaimApi",
            rest_api_name="Insurance Claim API",
            description="API for insurance claim processing",
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=["*"],  # In production, restrict to your domain
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=["*"],
                max_age=Duration.minutes(5),
            ),
            deploy_options=aws_apigateway.StageOptions(
                stage_name="dev",
                # Refer :https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html
                #       to enable full setup of logging
                #access_log_destination=aws_apigateway.LogGroupLogDestination(api_log_group),
                #logging_level=aws_apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
            )
        )

        # Create a Cognito authorizer for API Gateway
        authorizer = aws_apigateway.CognitoUserPoolsAuthorizer(
            self, "InsuranceClaimProcessAuthorizer",
            cognito_user_pools=[user_pool],
            identity_source="method.request.header.Authorization"
        )

        # [Optional] Expose API via CloudFront Distribution
        #spa_distribution = aws_cloudfront.Distribution(
        #    self,
        #    "CloudFrontDistributionAPI",
        #    default_behavior=aws_cloudfront.BehaviorOptions(
        #        origin=aws_cloudfront_origins.RestApiOrigin(
        #            api,
        #        ),
        #    )
        #)

        with open(
            "insurance_claim_process_cdk/lambdas/api_get_claim_report/app.py",
            encoding="utf8",
        ) as fp:
            handler_code = fp.read()
        lambda_get_claim_report = aws_lambda.Function(
            self,
            "ClaimReport",
            function_name="insuranceclaimApiGetClaimReport",
            code=aws_lambda.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_13,
        )
        lambda_role = lambda_get_claim_report.role
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["dynamodb:GetItem", "dynamodb:PutItem"],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/insuranceclaim-reports-json"
                ],
            )
        )

        with open(
            "insurance_claim_process_cdk/lambdas/api_get_claims/app.py", encoding="utf8"
        ) as fp:
            handler_code = fp.read()
        lambda_get_claims = aws_lambda.Function(
            self,
            "Claims",
            function_name="insuranceclaimApiGetClaims",
            code=aws_lambda.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_13,
        )
        lambda_role = lambda_get_claims.role
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["dynamodb:Scan"],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/insuranceclaim-reports-json"
                ],
            )
        )

        with open(
            "insurance_claim_process_cdk/lambdas/get_presigned_post_url/app.py", encoding="utf8"
        ) as fp:
            handler_code = fp.read()
        lambda_presigned_post_url = aws_lambda.Function(
            self,
            "PresignedPostUrl",
            function_name="insuranceclaimPresignedPostUrl",
            code=aws_lambda.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            environment={"INPUT_BUCKET": f"insuranceclaim-input-{self.account}-{self.region}"}
        )
        lambda_role = lambda_presigned_post_url.role
        # Add inline IAM policy to lambda_role, allowing invoke endpoint of SageMaker
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["s3:ListBucket", "s3:GetObject", "s3:PutObject"],
                resources=[
                    f"arn:aws:s3:::insuranceclaim-input-{self.account}-{self.region}",
                    f"arn:aws:s3:::insuranceclaim-input-{self.account}-{self.region}/*",
                ],
            )
        )

        with open(
            "insurance_claim_process_cdk/lambdas/start_claim_processing/app.py", encoding="utf8"
        ) as fp:
            handler_code = fp.read()
        lambda_start_claim_processing = aws_lambda.Function(
            self,
            "StartClaimProcessing",
            function_name="insuranceclaimStartClaimProcessing",
            code=aws_lambda.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            environment={"BDA_PROJECT_ARN": config["BDA"]["projectArn"]}
        )
        lambda_role = lambda_start_claim_processing.role
        # Add inline IAM policy to lambda_role, allowing invoke endpoint of SageMaker
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[
                    f"arn:aws:states:{self.region}:{self.account}:stateMachine:insuranceclaim-ClaimProcessing",
                ],
            )
            #IAM policy to start SFN execution
        )

        # Create API resources and methods

        # GET /get-claims
        get_claims = api.root.add_resource("get-claims")
        get_claims.add_method(
            "GET",
            aws_apigateway.LambdaIntegration(
                lambda_get_claims,
        #        proxy=True,
                integration_responses=[
                    aws_apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    )
                ]
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            authorizer=authorizer,
        )

        # GET /claim-status/{claimId}
        with open(
            "insurance_claim_process_cdk/lambdas/get_claim_status/app.py", encoding="utf8"
        ) as fp: 
            handler_code = fp.read() 
        lambda_get_claim_status = aws_lambda.Function(
            self, 
            "GetClaimStatus",
            function_name="insuranceclaimApiGetClaimStatus",
            code=aws_lambda.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(30),
            runtime=aws_lambda.Runtime.PYTHON_3_13,
        )
        lambda_role = lambda_get_claim_status.role 
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["dynamodb:GetItem"],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/insuranceclaim-reports-json"
                ],
            )
        )
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["states:ListExecutions", "states:DescribeExecution"],
                resources=[
                    f"arn:aws:states:{self.region}:{self.account}:stateMachine:insuranceclaim-ClaimProcessing",
                    f"arn:aws:states:{self.region}:{self.account}:execution:insuranceclaim-ClaimProcessing:*"
                ],
            )
        )

        claim_status = api.root.add_resource("claim-status")
        claim_status_id = claim_status.add_resource("{claimId}")
        claim_status_id.add_method(
            "GET",
            aws_apigateway.LambdaIntegration(
                lambda_get_claim_status,
                integration_responses=[
                    aws_apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    )
                ]
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            authorizer=authorizer,
        )

        # GET /get-claim-report
        get_claim_report = api.root.add_resource("get-claim-report")
        get_claim_report.add_method(
            "GET",
            aws_apigateway.LambdaIntegration(
                lambda_get_claim_report,
        #        proxy=True,
                integration_responses=[
                    aws_apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    )
                ]
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            authorizer=authorizer,
        )

        # GET /get-presigned-post-url
        get_claims = api.root.add_resource("get-presigned-post-url")
        get_claims.add_method(
            "GET",
            aws_apigateway.LambdaIntegration(
                lambda_presigned_post_url,
        #        proxy=True,
                integration_responses=[
                    aws_apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    )
                ]
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            authorizer=authorizer,
        )

        # GET /start-claim-processing
        start_claim_processing = api.root.add_resource("start-claim-processing")
        start_claim_processing.add_method(
            "GET",
            aws_apigateway.LambdaIntegration(
                lambda_start_claim_processing,
        #        proxy=True,
                integration_responses=[
                    aws_apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    )
                ]
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            authorizer=authorizer,
        )

        # GET / get-claim-status 
        get_claim_status = api.root.add_resource("get-claim-status")
        get_claim_status.add_method(
            "GET",
            aws_apigateway.LambdaIntegration(
                lambda_get_claim_status,
                integration_responses=[
                    aws_apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    )
                ]
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            authorizer=authorizer,
        )

        # GET /view-file
        with open(
            "insurance_claim_process_cdk/lambdas/get_presigned_url/app.py", encoding="utf8"
        ) as fp:
            handler_code = fp.read()
        lambda_get_presigned_url = aws_lambda.Function(
            self,
            "GetPresignedUrl",
            function_name="insuranceclaimGetPresignedUrl",
            code=aws_lambda.InlineCode(handler_code),
            handler="index.lambda_handler",
            timeout=Duration.seconds(30),
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            environment={"INPUT_BUCKET": f"insuranceclaim-input-{self.account}-{self.region}"}
        )
        lambda_role = lambda_get_presigned_url.role
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[
                    f"arn:aws:s3:::insuranceclaim-input-{self.account}-{self.region}/*"
                ],
            )
        )

        view_file = api.root.add_resource("view-file")
        view_file.add_method(
            "GET",
            aws_apigateway.LambdaIntegration(
                lambda_get_presigned_url,
                integration_responses=[
                    aws_apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": "'*'"
                        }
                    )
                ]
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ],
            authorizer=authorizer,
        )

        # Output the API URL
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id , description="Cognito User Pool ID")
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id , description="Cognito User Pool Client ID")
