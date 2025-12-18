import json
import hmac
import hashlib
import base64
from datetime import datetime
import urllib3
import os

# 環境変数から設定を取得
WEBHOOK_URL = os.environ.get('DEVOPS_AGENT_WEBHOOK_URL')
WEBHOOK_SECRET = os.environ.get('DEVOPS_AGENT_WEBHOOK_SECRET')

# HTTP接続用
http = urllib3.PoolManager()


def lambda_handler(event, context):
    """
    AWS DevOps AgentのWebhookをトリガーする簡単なLambda関数

    使用例:
    - 手動でLambdaを実行してテスト
    - SNSやEventBridgeから呼び出し
    - API Gatewayから呼び出し
    """

    try:
        # インシデントデータを作成
        incident_data = {
            'eventType': 'incident',
            'incidentId': f'incident-{int(datetime.utcnow().timestamp())}',
            'action': 'created',
            'priority': 'HIGH',
            'title': 'Test Incident from Lambda',
            'description': 'This is a test incident triggered from AWS Lambda',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'service': 'TestService',
            'data': {
                'metadata': {
                    'region': os.environ.get('AWS_REGION', 'us-east-1'),
                    'environment': 'production',
                    'source': 'aws-lambda'
                }
            }
        }

        # DevOps Agent Webhookを呼び出し
        response = trigger_devops_agent(incident_data)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully triggered DevOps Agent',
                'incidentId': incident_data['incidentId'],
                'webhookResponse': response
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to trigger DevOps Agent',
                'error': str(e)
            })
        }


def trigger_devops_agent(incident_data):
    """
    DevOps Agent WebhookにPOSTリクエストを送信（HMAC認証）

    Args:
        incident_data (dict): インシデント情報

    Returns:
        dict: Webhookからのレスポンス情報
    """

    # ペイロードをJSON文字列に変換
    payload = json.dumps(incident_data)

    # タイムスタンプ生成（ISO 8601形式）
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')

    # HMAC署名を生成
    # 署名対象: "timestamp:payload"
    message = f"{timestamp}:{payload}"
    signature = base64.b64encode(
        hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')

    # HTTPヘッダー
    headers = {
        'Content-Type': 'application/json',
        'x-amzn-event-timestamp': timestamp,
        'x-amzn-event-signature': signature
    }

    # POSTリクエスト送信
    print(f"Sending request to: {WEBHOOK_URL}")
    print(f"Payload: {payload}")

    response = http.request(
        'POST',
        WEBHOOK_URL,
        body=payload,
        headers=headers
    )

    # レスポンスをログ出力
    print(f"Response status: {response.status}")
    print(f"Response body: {response.data.decode('utf-8')}")

    return {
        'statusCode': response.status,
        'body': response.data.decode('utf-8')
    }


# ローカルテスト用
if __name__ == '__main__':
    # ローカルでテストする場合
    test_event = {}
    test_context = {}

    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))
