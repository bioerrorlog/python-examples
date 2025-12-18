from aws_cdk import (
    Duration,
    Stack,
    aws_lambda,
    aws_ssm,
)
from constructs import Construct

class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda関数の作成
        devops_webhook_lambda = aws_lambda.Function(
            self, "DevOpsWebhookLambda",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler="simple.lambda_handler",
            code=aws_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                # 環境変数はSSM Parameter Storeから取得することを推奨
                # デプロイ前に以下のパラメータをSSMに作成してください:
                # - /devops-agent/webhook-url
                # - /devops-agent/webhook-secret
                "DEVOPS_AGENT_WEBHOOK_URL": aws_ssm.StringParameter.from_string_parameter_name(
                    self, "WebhookUrl",
                    string_parameter_name="/devops-agent/webhook-url"
                ).string_value,
                "DEVOPS_AGENT_WEBHOOK_SECRET": aws_ssm.StringParameter.from_string_parameter_name(
                    self, "WebhookSecret",
                    string_parameter_name="/devops-agent/webhook-secret"
                ).string_value,
            },
            description="Lambda function to trigger DevOps Agent webhook",
        )
