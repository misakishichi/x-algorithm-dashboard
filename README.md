# X Algorithm Dashboard 🇯🇵

xai-org/x-algorithm のソースコードを解析した、日本語インタラクティブダッシュボード。

**🌐 GitHub Pages:** `https://<your-username>.github.io/<repo-name>`

## 機能

- 全体パイプライン解説
- 加算・減算アルゴリズムの重みランキング（バーチャート）
- Premium vs. 無料の比較表
- シャドウバンの原因・検出・解除手順
- 新アカウントの立ち上げ戦略
- ハッシュタグ・外部リンク・PR表記の影響と回避策

## 自動更新の仕組み

```
毎日 JST 9:00
    ↓
GitHub Actions が起動
    ↓
xai-org/x-algorithm の最新コードを取得
    ↓
Claude API (claude-sonnet-4-20250514) でダッシュボードを再生成
    ↓
変更があれば index.html を自動コミット・Push
    ↓
GitHub Pages が最新版を公開
```

## セットアップ

### 1. リポジトリをフォーク or 作成

```bash
git clone https://github.com/<your-username>/<repo-name>
cd <repo-name>
```

### 2. Anthropic API キーを GitHub Secrets に登録

```
リポジトリ → Settings → Secrets and variables → Actions
→ New repository secret
Name:  ANTHROPIC_API_KEY
Value: sk-ant-xxxxxxxxx（あなたのAPIキー）
```

### 3. GitHub Pages を有効化

```
リポジトリ → Settings → Pages
→ Source: Deploy from a branch
→ Branch: main / (root)
→ Save
```

### 4. 初回手動実行

```
Actions タブ → Update X Algorithm Dashboard → Run workflow
```

## ファイル構成

```
├── index.html                        # ダッシュボード本体（自動更新される）
├── generate.py                       # 更新スクリプト（Claude API呼び出し）
└── .github/
    └── workflows/
        └── update.yml               # GitHub Actions ワークフロー
```

## ローカルで手動実行

```bash
pip install requests anthropic
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxx
python generate.py
```

## 更新頻度の変更

`.github/workflows/update.yml` の `cron` を編集：

```yaml
# 毎日 JST 9:00
- cron: '0 0 * * *'

# 毎週月曜 JST 9:00
- cron: '0 0 * * 1'

# 6時間ごと
- cron: '0 */6 * * *'
```

## Source

- [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm) — Apache 2.0
