"""
example_3.py — 4章の実行例（Logfireで計測する）

example_2.py との差分は、logfire の2行だけ。
アプリケーション本体のコードには手を入れない。

使い方:
    export OPENAI_API_KEY='sk-...'
    export LOGFIRE_TOKEN='pylf_v1_...'
    uv run python src/example_3.py
"""

import asyncio

import logfire
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior

from article_common import INSTRUCTIONS, SAMPLE_HTML, ArticleList

# この2行を追加するだけで、エージェント実行がトレースとして記録される
logfire.configure()
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
