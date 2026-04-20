"""
generate.py
xai-org/x-algorithm の最新内容を取得し、Claude API でダッシュボード HTML を再生成する。
"""

import os
import re
import json
import requests
import anthropic

# ── 設定 ──────────────────────────────────────────────────────────────────
REPO = "xai-org/x-algorithm"
FILES_TO_FETCH = [
    "README.md",
    "home-mixer/scorers/weighted_scorer.rs",
    "home-mixer/scorers/oon_scorer.rs",
    "home-mixer/filters/pre_scoring_filters.rs",
    "phoenix/README.md",
]
GITHUB_API = "https://api.github.com"
OUTPUT_FILE = "index.html"
# ──────────────────────────────────────────────────────────────────────────


def fetch_github_file(path: str, token: str | None = None) -> str:
    """GitHub API からファイルの内容を取得する（Base64デコード）。"""
    url = f"{GITHUB_API}/repos/{REPO}/contents/{path}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 404:
        return f"[{path}: not found]"
    resp.raise_for_status()

    data = resp.json()
    import base64
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def fetch_latest_commit(token: str | None = None) -> str:
    """最新コミット SHA と日時を取得する。"""
    url = f"{GITHUB_API}/repos/{REPO}/commits/main"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    sha = data["sha"][:7]
    date = data["commit"]["committer"]["date"][:10]
    return f"{sha} ({date})"


def build_source_context(token: str | None) -> str:
    """取得したファイル群を1つのコンテキスト文字列にまとめる。"""
    parts = []
    for path in FILES_TO_FETCH:
        content = fetch_github_file(path, token)
        # 長すぎるファイルは先頭 6000 文字だけ使う
        if len(content) > 6000:
            content = content[:6000] + "\n...[truncated]"
        parts.append(f"=== {path} ===\n{content}\n")
    return "\n".join(parts)


def read_current_html() -> str:
    """現在の index.html を読み込む。存在しない場合は空文字を返す。"""
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""


SYSTEM_PROMPT = """
あなたはXのアルゴリズムを解析して、日本語のインタラクティブダッシュボードHTMLを生成するエキスパートです。

## 出力ルール
- 完全な自己完結型 HTML ファイル（DOCTYPE～</html>まで）を出力してください
- 外部依存はGoogle Fonts（Noto Sans JP + Space Mono）のみ許可
- ダークテーマ固定（背景 #0a0a0a 系）
- 日本語UIで以下の8タブ構成を維持すること：
  1. 全体像（パイプライン・TweepCred）
  2. 加算アルゴ（正のエンゲージメント重みランキング）
  3. 減算アルゴ（負のシグナルランキング）
  4. Premium比較（無料 vs Premium の機能・リーチ比較）
  5. シャドウバン（原因・検出・解除手順）
  6. 新アカウント（定義・立ち上げ戦略）
  7. ハッシュタグ（個数別インパクト・回避策）
  8. リンク（外部リンクの影響・回避策＝ツリーに貼るなど）
  ※ 「宣伝文（PR）」タブも追加：本文にPRと書いた場合の影響と、減算なら回避方法

## 重要な分析ポイント
- 宣伝・PR表記がアルゴリズムに与える影響を必ず含める
- ソースコードから読み取れる重み・フィルター・スコアラーの情報を優先
- 数値は可能な限り具体的に（×150、−40%など）
- 回避策は実践的に（「ツリーにつける」「リプライ欄に貼る」など）

## デザイン要件
- 現在のCSSスタイルを維持（Space Mono + Noto Sans JP、ダークテーマ）
- バーチャートで重みを視覚化
- バッジ（badge-green/red/blue/amber）で重要度を表示
- モバイル対応（最大幅600px以下でサイドバー非表示・モバイルタブ表示）
- ヘッダーにコミットSHAと日付を表示（SOURCE_COMMIT プレースホルダーを使う）

## HTMLコメント
- ソースコードから変更が確認された箇所には <!-- updated: YYYY-MM-DD --> コメントを追加

コード以外の説明文は一切不要です。HTMLのみを出力してください。
""".strip()


def generate_html(source_context: str, current_html: str, commit_info: str) -> str:
    """Claude API を呼び出して HTML を生成する。"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_message = f"""
## 最新のソースコード（xai-org/x-algorithm, commit: {commit_info}）

{source_context}

---

## 現在のダッシュボードHTML（差分参照用・変更がなければ内容を保持）

{current_html[:8000] if current_html else "[初回生成]"}

---

上記ソースコードを分析し、最新情報を反映した完全なダッシュボードHTMLを生成してください。
ヘッダーのSOURCE_COMMITは「{commit_info}」に置き換えてください。
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text

    # コードブロックが含まれていたら中身だけ抜き出す
    match = re.search(r"```html\s*([\s\S]+?)```", raw, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # <!DOCTYPE から始まるブロックを探す
    match = re.search(r"(<!DOCTYPE[\s\S]+</html>)", raw, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return raw.strip()


def main():
    token = os.environ.get("GITHUB_TOKEN")

    print("📡 Fetching latest source from xai-org/x-algorithm ...")
    commit_info = fetch_latest_commit(token)
    print(f"   Latest commit: {commit_info}")

    source_context = build_source_context(token)
    print(f"   Fetched {len(source_context):,} chars of source")

    current_html = read_current_html()
    print(f"   Current HTML: {len(current_html):,} chars")

    print("🤖 Calling Claude API to regenerate dashboard ...")
    new_html = generate_html(source_context, current_html, commit_info)
    print(f"   Generated HTML: {len(new_html):,} chars")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"✅ Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
