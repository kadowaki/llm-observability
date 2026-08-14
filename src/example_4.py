"""
example_4.py — 6章の実行例（Logfire以外のOTelバックエンドに送る）

example_3.py との差分は logfire.configure() の引数だけ。
send_to_logfire=False にすると、Logfireへの送信を止めて
OTLP の標準的な送信先（環境変数で指定）にトレースを送る。

使い方:
    # 受信側を起動しておく
    $ docker run --rm -it -p 4318:4318 ymtdzzz/otel-tui

    # 別のターミナルで
    $ export OPENAI_API_KEY='sk-...'
    $ export OTEL_EXPORTER_OTLP_ENDPOINT='http://localhost:4318'
    $ uv run python src/example_4.py
"""

import asyncio

import logfire
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior

from article_common import INSTRUCTIONS, SAMPLE_HTML, ArticleList

# Logfireへの送信を止める。
# 送信先は OTEL_EXPORTER_OTLP_ENDPOINT で指定する
logfire.configure(send_to_logfire=False, service_name="llm-observability")
logfire.instrument_pydantic_ai()

agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=ArticleList,
    instructions=INSTRUCTIONS,
    retries={"output": 3},
)


async def main() -> None:
    usage = None
    res = None

    try:
        async with agent.iter(SAMPLE_HTML) as run:
            try:
                async for _node in run:
                    pass
            finally:
                usage = run.usage
                res = run.result
    except UnexpectedModelBehavior as e:
        print(f"リトライ上限に到達: {e}")

    print(f"モデルリクエスト数: {usage.requests}")
    print(f"入力トークン: {usage.input_tokens}")
    print(f"出力トークン: {usage.output_tokens}")

    if res is not None:
        print(f"最終的に {len(res.output.articles)} 件を抽出")


if __name__ == "__main__":
    asyncio.run(main())
