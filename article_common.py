"""
article_common.py — 記事に掲載するコード（2月号の article_common_strict.py の更新版）

2月号からの変更点:
    - summary フィールドを追加（入力に存在しないため LLM が生成する）
    - min_length / max_length を両方指定（上限だけだと反対側に振り切れるため）

入力データは fetch_source.py で取得したものを使う。
2月号は6件の抜粋HTMLだったが、本記事では記事一覧から25件を取得する。
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

# 解析対象の入力をファイルから読み込む
source_path = Path(__file__).parent.parent / "data" / "monthly_topics.txt"
SAMPLE_HTML = source_path.read_text(encoding="utf-8")


class ArticleInfo(BaseModel):
    """記事のメタデータ"""

    title: str = Field(min_length=1, description="記事のタイトル")
    author: str = Field(min_length=1, description="著者名")
    published_date: date = Field(description="公開日")
    url: str = Field(description="記事のURL（相対パス）")
    # 追加: 入力に存在しないため、LLMが生成する必要がある
    summary: str = Field(min_length=10, max_length=25, description="記事内容の要約")

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        """URLが`/article/`で始まる相対パスかを検証し、不正なら例外を送出する"""
        if not v.startswith("/article/"):
            raise ValueError(
                f"URLは'/article/'で始まる相対パスである必要があります（実際の値: {v}）"
            )
        return v


class ArticleList(BaseModel):
    """記事一覧"""

    articles: list[ArticleInfo] = Field(min_length=1)


INSTRUCTIONS = """\
与えられたHTMLから記事の一覧情報を抽出してください。

- タイトル、著者名、公開日、URLは、入力の表記どおりに正確に写してください
- summaryには、タイトルから読み取れる内容を25字以内の日本語で要約してください
"""
