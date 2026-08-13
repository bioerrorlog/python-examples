# 実装計画: FastAPI + Cloud Run における構造化ログと audit_log_id の導入

## 1. 背景と現状の問題

### 現状

- Google Cloud の Cloud Run 上で FastAPI 製の API サーバーをホストしている
- 各モジュールで `logger = logging.getLogger(__name__)` を定義し、`logger.info()` 等で出力している
- ログ設定は Python 標準の `logging` のみ（`basicConfig` 相当）

### 問題

Cloud Run は stdout / stderr の各行をそのまま取り込むため、プレーンテキスト出力は Cloud Logging 上で `textPayload` として記録される。これにより以下が発生している。

| 症状 | 原因 |
| --- | --- |
| 任意フィールドで検索できない | すべてが 1 本の文字列であり、正規表現でしか掘れない |

### 要件

アプリ内で API 呼び出しごとに UUID を発行し、それを `audit_log_id` として JSON 構造化ログに含める。1 リクエスト中に出力される全ログエントリが同一の `audit_log_id` を持ち、Cloud Logging 上で横断検索できること。

---

## 2. ゴール / 非ゴール

### ゴール

1. Cloud Logging 上で `jsonPayload` として構造化ログが記録される
2. `severity` が Python のログレベルを正しく反映する
3. 例外が 1 エントリにまとまり、Error Reporting に連携される
4. すべてのログエントリに `audit_log_id`（UUID v4）が自動で付与される
5. レスポンスヘッダ `X-Audit-Log-Id` に同じ値を返す
6. **既存の `logging.getLogger(__name__)` と `logger.info(...)` の呼び出しを一切変更しない**

### 非ゴール（今回は実装しない）

- Cloud Trace との連携（`logging.googleapis.com/trace`）。将来の拡張として §9 に記載
- リクエストヘッダからの `audit_log_id` 引き継ぎ（マイクロサービス間伝播）。今回は常に新規発行する
- ローカル開発用のログ出力切り替え。**常に JSON 出力とする**
- ログシンク / 保持期間 / BigQuery エクスポートの設定

---

## 3. 設計方針

### 3.1 なぜ ContextVar を使うのか

`audit_log_id` をすべての関数の引数として引き回すのは非現実的。「リクエストごとに独立した、どこからでも読める保管場所」が必要になる。

- **グローバル変数は不可**: FastAPI は async のため、1 スレッドが複数リクエストを交互に処理する。`await` での中断中に別リクエストが値を上書きし、値が混ざる
- **`threading.local` も不可**: 上記は同一スレッド内で発生するため解決しない
- **`contextvars.ContextVar`（標準ライブラリ）を使う**: asyncio は Task 生成時にコンテキストをコピーする。Starlette / uvicorn はリクエストごとに Task を作るため、結果としてリクエストごとに独立した値を保持できる

### 3.2 なぜ logging.Filter を使うのか

`logging.Filter` は名前に反して、本用途ではフィルタリングではなく「全 LogRecord に共通フィールドを注入するフック」として使う。すべてのログが必ず Filter を通過するため、標準機能の中でこの目的に適した唯一の場所である。

### 3.3 なぜ `Client()` ではなく `StructuredLogHandler` を直接使うのか

`google.cloud.logging.Client()` は GCP の認証情報とプロジェクト ID を探索するため、認証設定のない環境では初期化に失敗する。`StructuredLogHandler` は「stdout に JSON を 1 行書く」だけのクラスであり、認証もネットワークアクセスも不要。Cloud Run が必要とするのはまさにこの動作のみであるため、こちらを直接使う。

### 3.4 データフロー

```
① リクエスト到着
     ↓
② ミドルウェア: uuid4() を発行 → ContextVar にセット
     ↓
③ エンドポイント / サービス層 / リポジトリ層で logger.info() が呼ばれる
     ↓  （LogRecord が生成される）
④ AuditLogIdFilter: ContextVar から読み出し、record.json_fields に注入
     ↓
⑤ StructuredLogHandler: json_fields を展開して stdout に JSON を 1 行出力
     ↓
⑥ Cloud Run がその行を取り込み、Cloud Logging に jsonPayload として記録
     ↓
⑦ ミドルウェア: レスポンスヘッダに X-Audit-Log-Id を付与して返却
```

---

## 4. 依存関係の追加

```
google-cloud-logging>=3.0
```

`requirements.txt` / `pyproject.toml` / `poetry` など、プロジェクトで使用しているパッケージ管理方式に合わせて追加すること。

`contextvars` は Python 標準ライブラリのためインストール不要。

---

## 5. ファイル構成

以下 3 ファイルを新規作成し、`main.py`（アプリのエントリポイント）を修正する。配置先はプロジェクトのパッケージ構成に合わせること。以下は `app/` 配下を想定した例。

```
app/
├── logging_context.py   # 新規: ContextVar の定義
├── logging_setup.py     # 新規: ハンドラと Filter の設定
├── middleware.py        # 新規: ミドルウェア
├── main.py              # 修正: setup_logging() 呼び出しとミドルウェア登録
└── routes/              # 変更なし
```

> **import パスは実際のパッケージ構成に合わせて修正すること。** 以下のコードは `app.` プレフィックスで記述している。

---

## 6. 実装

### 6.1 `app/logging_context.py`（新規）

```python
from contextvars import ContextVar

audit_log_id_var: ContextVar[str | None] = ContextVar("audit_log_id", default=None)
```

- `default=None` は必須。省略すると未設定時の `.get()` が `LookupError` を送出する

### 6.2 `app/logging_setup.py`（新規）

```python
import logging
import sys

from google.cloud.logging_v2.handlers import StructuredLogHandler
from google.cloud.logging_v2.handlers import setup_logging as _attach_handler

from app.logging_context import audit_log_id_var


class AuditLogIdFilter(logging.Filter):
    """全 LogRecord に audit_log_id を注入する。

    logging.Filter を継承しているが、フィルタリング目的ではなく
    レコードへのフィールド注入フックとして使用している。
    filter() は必ず True を返すこと（False / None を返すとログが破棄される）。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        audit_log_id = audit_log_id_var.get()
        if audit_log_id:
            # extra={"json_fields": {...}} で渡された既存フィールドを壊さないようマージする
            fields = dict(getattr(record, "json_fields", None) or {})
            fields.setdefault("audit_log_id", audit_log_id)
            record.json_fields = fields
        return True


def setup_logging(log_level: int = logging.INFO) -> None:
    """構造化ログのハンドラを root logger に設定する。

    アプリケーション起動時に、FastAPI インスタンス生成より前に一度だけ呼ぶこと。
    """
    handler = StructuredLogHandler(stream=sys.stdout)
    _attach_handler(handler, log_level=log_level)

    audit_filter = AuditLogIdFilter()
    root = logging.getLogger()
    # logger と handler の両方に付ける（理由は下記コメント参照）
    root.addFilter(audit_filter)
    for h in root.handlers:
        h.addFilter(audit_filter)
```

#### 実装上の注意

- **`stream=sys.stdout` を明示すること**。`StructuredLogHandler` の既定は stderr。JSON 内の `severity` が優先されるため実害は出にくいが、意図を明確にするため stdout に揃える
- **Filter を logger と handler の両方に付けること**。`logging` の仕様上、logger に付けた Filter は「その logger 自身に出されたレコード」にしか適用されず、子 logger から伝播してきたレコードには適用されない。handler 側に付けたものは到達した全レコードに適用される。両方に付けても `setdefault` により二重適用の害はない
- **`_attach_handler` の後に `addFilter` すること**。`StructuredLogHandler` は内部に独自の Filter を持つため、自作 Filter を後に登録する
- import は `google.cloud.logging.handlers` からでも可能（同一実体のエイリアス）。プロジェクトの慣習に合わせてよい

### 6.3 `app/middleware.py`（新規）

```python
import uuid

from fastapi import Request

from app.logging_context import audit_log_id_var

AUDIT_LOG_ID_HEADER = "X-Audit-Log-Id"


async def audit_log_id_middleware(request: Request, call_next):
    """リクエストごとに audit_log_id を発行し、ContextVar に格納する。"""
    audit_log_id = str(uuid.uuid4())
    token = audit_log_id_var.set(audit_log_id)
    try:
        response = await call_next(request)
        response.headers[AUDIT_LOG_ID_HEADER] = audit_log_id
        return response
    finally:
        audit_log_id_var.reset(token)
```

#### 実装上の注意

- **`try` / `finally` を使うこと**。エンドポイントが例外を送出した場合でも確実に `reset()` する
- **`reset(token)` を使うこと**。`set(None)` ではなく、`set()` が返したトークンで巻き戻す
- `return response` は必須。ミドルウェアの戻り値がクライアントへのレスポンスそのものになるため、`call_next` から受け取った `Response` オブジェクトを必ず返す

### 6.4 `app/main.py`（修正）

```python
from fastapi import FastAPI

from app.logging_setup import setup_logging
from app.middleware import audit_log_id_middleware

setup_logging()          # FastAPI インスタンス生成より前に呼ぶ

app = FastAPI()

app.middleware("http")(audit_log_id_middleware)

# 既存の router 登録などはそのまま
# app.include_router(...)
```

デコレータ形式で書く場合は以下と等価:

```python
@app.middleware("http")
async def _audit_log_id(request, call_next):
    return await audit_log_id_middleware(request, call_next)
```

### 6.5 既存コードへの変更

**なし。** `routes/`、サービス層、リポジトリ層の `logger = logging.getLogger(__name__)` および `logger.info(...)` / `logger.error(...)` はすべて変更不要。

---

## 7. 期待される出力

### 通常のログ

アプリ側のコード（変更なし）:

```python
logger = logging.getLogger(__name__)
logger.info("order created")
```

Cloud Logging 上のエントリ:

```json
{
  "jsonPayload": {
    "message": "order created",
    "audit_log_id": "3f9c1e2a-7b4d-4f8e-9a1c-2d5b8e0f7a13"
  },
  "severity": "INFO",
  "labels": {
    "python_logger": "app.services.order"
  },
  "sourceLocation": {
    "file": "/app/app/services/order.py",
    "line": "42",
    "function": "create_order"
  }
}
```

`getLogger(__name__)` のモジュール名が `labels.python_logger` として検索軸になる点に注意。既存のモジュール分割がそのまま活きる。

### 追加フィールドを付けたい場合（任意）

```python
logger.info("payment done", extra={"json_fields": {"amount": 4980, "user_id": "u_abc"}})
```

```json
{
  "jsonPayload": {
    "message": "payment done",
    "audit_log_id": "3f9c1e2a-7b4d-4f8e-9a1c-2d5b8e0f7a13",
    "amount": 4980,
    "user_id": "u_abc"
  },
  "severity": "INFO"
}
```

### Cloud Logging でのクエリ例

```
jsonPayload.audit_log_id = "3f9c1e2a-7b4d-4f8e-9a1c-2d5b8e0f7a13"
```

```
resource.type = "cloud_run_revision"
severity >= WARNING
labels.python_logger =~ "^app\.services\."
```

---

## 8. 検証手順

### 8.1 ローカルでの JSON 出力確認

認証設定なしでも動作するため、そのままローカル起動できる。

```bash
uvicorn app.main:app --port 8000
```

任意のエンドポイントを叩き、標準出力に 1 行 JSON が出ることを確認する。

```bash
curl -i localhost:8000/your-endpoint
```

**確認項目:**
- [ ] 標準出力のログが 1 行の JSON である
- [ ] `severity` が呼び出したログレベルと一致する（`logger.info` → `"INFO"`）
- [ ] `jsonPayload` 相当の中に `audit_log_id` が含まれる
- [ ] レスポンスヘッダに `X-Audit-Log-Id` が含まれる
- [ ] レスポンスヘッダの値とログ中の `audit_log_id` が一致する

### 8.2 1 リクエスト内の一貫性

複数箇所でログを出すエンドポイントを叩き、同一リクエスト内の全ログが同じ `audit_log_id` を持つことを確認する。

### 8.3 同時リクエストでの分離

```bash
for i in $(seq 1 20); do curl -s localhost:8000/your-endpoint & done; wait
```

出力 JSON を `audit_log_id` でグループ化し、値が混ざっていないことを確認する。

```bash
# 例: jq でグルーピング
uvicorn app.main:app --port 8000 2>&1 | jq -r '.audit_log_id' | sort | uniq -c
```

### 8.4 async / sync 両方のエンドポイント

`routes/` には `async def` と `def` のエンドポイントが混在している。**両方で `audit_log_id` が付与されることを確認すること。**

```python
@router.get("/test-async")
async def test_async():
    logger.info("async endpoint")
    return {"ok": True}


@router.get("/test-sync")
def test_sync():
    logger.info("sync endpoint")
    return {"ok": True}
```

`def` エンドポイントは Starlette がスレッドプールで実行するが、内部で `anyio.to_thread.run_sync()` を使っており、anyio が現在のコンテキストをコピーしてワーカースレッドに渡すため、ContextVar は正しく引き継がれる。

### 8.5 例外時の挙動

意図的に例外を送出するエンドポイントを用意し、以下を確認する。

- [ ] スタックトレースが 1 エントリにまとまっている
- [ ] `severity` が `ERROR` になっている
- [ ] `audit_log_id` が付与されている

### 8.6 Cloud Run デプロイ後

- [ ] ログエクスプローラで `jsonPayload.audit_log_id` によるクエリが機能する
- [ ] `logger.info()` が INFO として（ERROR ではなく）表示される
- [ ] 例外が Error Reporting に表示される

---

## 9. 既知の落とし穴と対応

### 9.1 Filter が `True` を返さないとログが消える

`filter()` の戻り値が `False` または `None` の場合、そのログは破棄される。`return True` を必ず書くこと。

### 9.2 自前のスレッドプールでは ContextVar が引き継がれない

`ThreadPoolExecutor` や `threading.Thread` を明示的に生成している箇所がある場合、コンテキストは自動コピーされない。該当箇所があれば以下のように明示的に渡す。

```python
import contextvars

ctx = contextvars.copy_context()
executor.submit(ctx.run, some_work)
```

**実装時、コードベース内に `ThreadPoolExecutor` / `threading.Thread` / `ProcessPoolExecutor` の使用箇所がないか grep で確認すること。**

### 9.3 BackgroundTasks

FastAPI の `BackgroundTasks` はレスポンス返却後に実行されるため、ミドルウェアの `finally` で `reset()` された後になる場合がある。バックグラウンド処理でも同じ ID を残したい場合は、タスク関数の引数として明示的に渡し、その中で再度 `set()` すること。

### 9.4 アクセスログの二重化

Cloud Run はリクエストログ（メソッド、パス、ステータス、レイテンシ）を自動で出力する。uvicorn のアクセスログが不要な場合は除外する。

```python
from google.cloud.logging_v2.handlers import setup_logging as _attach_handler

_attach_handler(
    handler,
    log_level=log_level,
    excluded_loggers=("uvicorn.access",),
)
```

**この判断は既存のログ運用次第のため、実装時にプロジェクト側の方針を確認すること。**

### 9.5 ミドルウェアより外側の例外

uvicorn レベルで発生した例外など、ミドルウェアに到達しないエラーでは `X-Audit-Log-Id` が付与されない。`audit_log_id` をユーザー問い合わせ対応に使う想定であれば、500 エラー時にヘッダが付くことを検証し、必要なら例外ハンドラを追加すること。

### 9.6 ブラウザ JS からヘッダを読む場合

ブラウザは既定でカスタムヘッダを JavaScript に露出しない。フロントエンドから読む必要がある場合は CORS の設定が必要。

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[...],
    expose_headers=["X-Audit-Log-Id"],
)
```

同一オリジン配信、またはヘッダをブラウザで読まない場合は不要。

### 9.7 ログエントリのサイズ上限

Cloud Logging の 1 エントリは 256KB を超えると切り捨てられる。`json_fields` に大きなペイロード（リクエストボディ全体など）を入れないこと。

### 9.8 ヘッダ名について

`X-` プレフィックスは RFC 6648（2012）で新規利用が非推奨とされている。本プロジェクトでは既存の慣習に合わせて `X-Audit-Log-Id` を採用する方針で確定済み。**変更しないこと。**

---

## 10. 将来の拡張（今回は実装しない）

### Cloud Trace 連携

Cloud Run が付与する `X-Cloud-Trace-Context` ヘッダを利用すると、Cloud Run のリクエストログとアプリログがログエクスプローラ上で親子表示されるようになる。

実装する場合の概要:

1. `trace_var: ContextVar[str | None]` を追加
2. ミドルウェアで `request.headers.get("X-Cloud-Trace-Context", "")` を取得し、`/` の前の部分を trace ID として抽出
3. `f"projects/{PROJECT_ID}/traces/{trace_id}"` の形式に整形して `trace_var` にセット
4. Filter 内で `record.trace = trace_var.get()` をセット（`StructuredLogHandler` がこの属性を `logging.googleapis.com/trace` として出力する）

注意: `google-cloud-logging` の自動 trace 紐付けは Flask / Django のみ対応のため、FastAPI では上記の手当てが必要。

### 監査ログとしての保持要件

「監査ログ」という要件が Cloud Audit Logs（GCP の管理操作ログ）を指すのか、アプリケーションの業務監査ログを指すのかを依頼元に確認すること。後者で長期保持や改ざん耐性が必要な場合、既定の `_Default` バケットは保持期間 30 日のため、ログシンクで専用バケット（保持期間延長・ロック）や BigQuery へ流す構成の検討が必要。

---

## 11. 受け入れ基準チェックリスト

- [ ] `google-cloud-logging>=3.0` が依存に追加されている
- [ ] `logging_context.py` / `logging_setup.py` / `middleware.py` が作成されている
- [ ] `main.py` で `setup_logging()` が `FastAPI()` より前に呼ばれている
- [ ] ミドルウェアが登録されている
- [ ] `routes/` およびサービス層のコードが一切変更されていない
- [ ] ログが 1 行 JSON で出力される
- [ ] `severity` が Python のログレベルを反映している
- [ ] 全ログに `audit_log_id` が含まれる
- [ ] `async def` / `def` 両方のエンドポイントで動作する
- [ ] 同時リクエストで `audit_log_id` が混ざらない
- [ ] レスポンスヘッダ `X-Audit-Log-Id` が返る
- [ ] 例外が 1 エントリにまとまる
- [ ] `ThreadPoolExecutor` 等の使用箇所を grep で確認済み（あれば対応済み）
