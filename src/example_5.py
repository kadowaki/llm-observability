"""
example_5.py — Column の実行例（本文をトレースに記録しない）

example_3.py との差分は capabilities の指定だけ。
include_content=False にすると、プロンプトやモデルの出力が
トレースに含まれなくなる。

スパンの構造・トークン数・レイテンシは引き続き記録されるため、
「何回呼ばれたか」「どれくらいかかったか」は把握できる。

使い方:
    export OPENAI_API_KEY='sk-...'
    export LOGFIRE_TOKEN='pylf_v1_...'
    uv run python src/example_5.py
"""

import asyncio

import logfire
from pydantic_ai import Agent
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models.instrumented import InstrumentationSettings

from article_common import INSTRUCTIONS, SAMPLE_HTML, ArticleList

logfire.configure()
logfire.instrument_pydantic_ai()

agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=ArticleList,
    instructions=INSTRUCTIONS,
    retries={"output": 3},
    # メッセージ本文をトレースに含めない
    capabilities=[Instrumentation(settings=InstrumentationSettings(include_content=False))],
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
