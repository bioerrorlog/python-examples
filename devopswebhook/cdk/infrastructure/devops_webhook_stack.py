from aws_cdk import (
    Duration,
    Stack,
    aws_lambda,
    aws_ssm,
)
from constructs import Construct

class DevOpsWebhookStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SSMパラメータの作成
        webhook_url_param = aws_ssm.StringParameter(
            self, "WebhookUrlParameter",
            parameter_name="/devops-agent/webhook-url",
            string_value="https://your-webhook-url.example.com",
            description="DevOps Agent Webhook URL",
            tier=aws_ssm.ParameterTier.STANDARD,
        )

        webhook_secret_param = aws_ssm.StringParameter(
            self, "WebhookSecretParameter",
            parameter_name="/devops-agent/webhook-secret",
            string_value="your-webhook-secret-here",
            description="DevOps Agent Webhook Secret",
            tier=aws_ssm.ParameterTier.STANDARD,
        )

        # Lambda関数の作成
        devops_webhook_lambda = aws_lambda.Function(
            self, "DevOpsWebhookLambda",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler="webhook_trigger.lambda_handler",
            code=aws_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "DEVOPS_AGENT_WEBHOOK_URL": webhook_url_param.string_value,
                "DEVOPS_AGENT_WEBHOOK_SECRET": webhook_secret_param.string_value,
            },
            description="Lambda function to trigger DevOps Agent webhook",
        )
