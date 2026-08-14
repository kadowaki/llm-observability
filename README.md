# llm-observability

gihyo.jp「Python Monthly Topics」2026年8月号
**型で守ったLLMをトレースで見る ― Pydantic AIとLogfireによる可視化**
のサンプルコードです。

記事: https://gihyo.jp/article/2026/08/monthly-python-2608

## 動作環境

```
Python 3.14.6
pydantic 2.13.4
pydantic-ai 2.22.0
logfire 4.39.0
```

記事執筆時に動作を確認した組み合わせを `uv.lock` に固定しています。

## セットアップ

```bash
$ git clone https://github.com/kadowaki/llm-observability.git
$ cd llm-observability
$ uv sync
```

OpenAI APIのキーを設定します。

```bash
$ export OPENAI_API_KEY='sk-...'
```

## 入力データの取得

記事一覧ページを取得してテキスト化します。
`data/monthly_topics.txt` に保存され、各サンプルはこれを読み込みます。

```bash
$ uv run python src/fetch_source.py
```

取得したデータはリポジトリに含めていません。
実行結果は取得時点の記事一覧に依存するため、記事中の出力と件数が異なる場合があります。

## サンプル

| ファイル | 対応する節 | 内容 |
|---|---|---|
| `src/article_common.py` | 2章 | 出力モデルと指示文の定義（各サンプルで共用） |
| `src/example_1.py` | 2章 | 正常系。`run_sync()`で結果だけを受け取る |
| `src/example_2.py` | 3章 | `agent.iter()`でリクエスト数と検証エラーを見る |
| `src/example_3.py` | 4章 | Logfireで計測する |
| `src/example_4.py` | 6章 | Logfire以外のOTelバックエンドに送る |
| `src/example_5.py` | Column | `include_content=False`で本文を記録しない |

```bash
$ uv run python src/example_1.py
```

### Logfireに送る場合（example_3.py）

[Logfire](https://logfire.pydantic.dev/)でプロジェクトを作成し、書き込みトークンを設定します。

```bash
$ export LOGFIRE_TOKEN='pylf_v1_...'
$ uv run python src/example_3.py
```

### otel-tuiに送る場合（example_4.py）

受信側をDockerで起動しておきます。

```bash
$ docker run --rm -it -p 4318:4318 ymtdzzz/otel-tui
```

別のターミナルから実行します。

```bash
$ export OTEL_EXPORTER_OTLP_ENDPOINT='http://localhost:4318'
$ uv run python src/example_4.py
```

## 注意

LLMの出力は確定的ではないため、実行のたびにリトライ回数やトークン数は変わります。
記事中の数値は特定の1回の実行のものです。

各サンプルはOpenAI APIを呼び出すため、実行ごとに料金が発生します。
`retries={"output": 3}`により、1回の実行で最大4回モデルが呼ばれます。

