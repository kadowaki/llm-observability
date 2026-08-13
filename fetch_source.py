"""
fetch_source.py — 入力スナップショットの取得

Python Monthly Topics の記事一覧ページを取得し、
テキストに変換して data/ に保存する。

意図:
    - ベンチマークをネットワークに依存させない（再現性）
    - 実ページのノイズをあえて残す（整形しすぎると抽出が簡単になりすぎる）
    - 取得結果そのものはリポジトリに含めない（data/ は .gitignore）

依存は標準ライブラリ + httpx のみ（httpx は pydantic-ai が持っている）。

使い方:
    uv run python fetch_source.py
    uv run python fetch_source.py --pages 3     # ページ送りも取得する
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import httpx

LIST_URL = "https://gihyo.jp/list/group/Python-Monthly-Topics"
DATA_DIR = Path(__file__).parent.parent / "data"

ARTICLE_URL = re.compile(r"/article/\d{4}/\d{2}/[\w-]+")


class TextExtractor(HTMLParser):
    """
    タグを剥がしてテキスト化する。ただしリンクは「テキスト (URL)」の形で残す。

    整形しすぎないのが目的なので、ナビゲーションやサイドバーも落とさない。
    そこに混ざるノイズこそが、抽出タスクの現実的な難しさを作る。
    """

    SKIP = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0
        self._href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag == "a":
            self._href = dict(attrs).get("href")
        elif tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "a" and self._href:
            # 相対パスのまま残す。
            # 2月号のサンプルHTMLも href="/article/..." の形だったため、
            # 出力モデルの url フィールドもこの形を前提にしている。
            self.parts.append(f" ({self._href})")
            self._href = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = data.strip()
        if not text:
            return
        # インライン要素で分割されたテキストを空白で連結すると、
        # 日本語が「Python 3. 15新機能」のように崩れる。
        # 英数字どうしが隣接するときだけ空白を入れる。
        if self.parts:
            prev = self.parts[-1]
            if prev and prev[-1].isascii() and prev[-1].isalnum() and text[0].isascii():
                self.parts.append(" ")
        self.parts.append(text)

    def text(self) -> str:
        raw = "".join(self.parts)
        # 空行の連続だけ潰す。それ以外のノイズは残す。
        return re.sub(r"\n\s*\n+", "\n\n", raw).strip()


def fetch(pages: int) -> str:
    chunks: list[str] = []
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for page in range(1, pages + 1):
            url = LIST_URL if page == 1 else f"{LIST_URL}/{page}"
            print(f"取得中: {url}")
            res = client.get(url)
            if res.status_code != 200:
                print(f"  スキップ (HTTP {res.status_code})")
                continue
            parser = TextExtractor()
            parser.feed(res.text)
            chunks.append(parser.text())
    return "\n\n".join(chunks)


def report(text: str) -> None:
    """制約設計に必要な情報を出す"""
    urls = ARTICLE_URL.findall(text)
    uniq = sorted(set(urls))

    print("\n" + "=" * 60)
    print("スナップショットの内容")
    print("=" * 60)
    print(f"文字数: {len(text):,}")
    print(f"推定トークン数: {len(text) // 2:,} 前後（日本語は1文字≒0.5〜1トークン）")
    print(f"記事URL: 延べ {len(urls)} / ユニーク {len(uniq)}")

    # slug の形を数える。制約のURLパターンを決めるための材料。
    slugs = Counter()
    for u in uniq:
        slug = u.rsplit("/", 1)[-1]
        # 末尾の数字を除いた「形」でまとめる
        slugs[re.sub(r"\d+$", "N", slug)] += 1

    print("\nslug の形（上位10件）:")
    for shape, count in slugs.most_common(10):
        print(f"  {count:4d}  {shape}")

    print("\n先頭5件のURL:")
    for u in uniq[:5]:
        print(f"  {u}")

    print("  （他連載のURLが混ざると件数チェックが常に失敗して差が出なくなる）")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=1, help="取得するページ数")
    args = ap.parse_args()

    text = fetch(args.pages)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "monthly_topics.txt"
    out.write_text(text, encoding="utf-8")
    print(f"\n保存: {out}")

    report(text)


if __name__ == "__main__":
    main()
