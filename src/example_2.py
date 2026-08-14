"""
example_2.py — 3章の実行例（Agent.iter で途中経過を見る）

run_sync() は最終結果しか返さないため、モデルが何回呼ばれたかが分からない。
iter() を使うと実行をノード単位で進められ、usage や履歴にアクセスできる。

失敗したときこそ原因とコストを知りたいので、
try/finally で例外時にも usage を回収する形にしておく。

使い方:
    export OPENAI_API_KEY='sk-...'
    uv run python src/example_2.py
"""

import asyncio

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior

from article_common import INSTRUCTIONS, SAMPLE_HTML, ArticleList

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
                # 例外が発生しても、ここまでの使用量は取得できる
                usage = run.usage
                res = run.result
                history = run.ctx.state.message_history
    except UnexpectedModelBehavior as e:
        print(f"リトライ上限に到達: {e}")

    print(f"モデルリクエスト数: {usage.requests}")
    print(f"入力トークン: {usage.input_tokens}")
    print(f"出力トークン: {usage.output_tokens}")

    # リトライ時にモデルへ返された検証エラーを取り出す
    for message in history:
        for part in message.parts:
            if type(part).__name__ != "RetryPromptPart":
                continue
            print(f"\n--- {len(part.content)}件の検証エラーを返した ---")
            for err in part.content:
                loc = ".".join(str(x) for x in err["loc"])
                print(f"  {loc}: {err['msg']}")
                print(f"    実際の値: {err['input']}")

    if res is not None:
        print(f"\n最終的に {len(res.output.articles)} 件を抽出")


if __name__ == "__main__":
    asyncio.run(main())
