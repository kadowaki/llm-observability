"""
example_1.py — 2章の実行例（Logfireなし）

2月号の example_4.py を V2 の API に合わせて更新したもの。
この時点ではまだ計測を入れず、アプリケーション自体が動くことを確認する。

使い方:
    export OPENAI_API_KEY='sk-...'
    uv run python src/example_1.py
"""

from pydantic_ai import Agent

from article_common import INSTRUCTIONS, SAMPLE_HTML, ArticleList

agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=ArticleList,
    instructions=INSTRUCTIONS,
    retries={"output": 3},  # V1では retries=3 だった
)

res = agent.run_sync(SAMPLE_HTML)

for article in res.output.articles:
    print(f"{article.published_date}  {article.author}  {article.summary}")
