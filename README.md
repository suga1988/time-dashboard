# Toggl Time Dashboard

Toggl Track の記録を毎日自動取得し、GitHub Pages で閲覧するダッシュボード。

- `index.html` … ダッシュボード本体（`data.json` を読んで全てブラウザ内で集計）
- `data.json` … Toggl から取得したローデータ（Actions が自動更新）
- `fetch_toggl.py` … Toggl API v9 → `data.json`
- `.github/workflows/update.yml` … 毎日 05:00 JST に実行

## 初期設定（1回だけ）

1. このリポジトリを **Public** で作成し、ファイル一式をアップロード
2. **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `TOGGL_API_TOKEN`
   - Secret: Toggl Track → Profile settings → 最下部 "API Token"
3. **Settings → Pages → Build and deployment**
   - Source: Deploy from a branch
   - Branch: `main` / `/ (root)` → Save
4. **Actions タブ → "Update Toggl data" → Run workflow** で初回実行
   （Actions が無効なら "I understand my workflows, go ahead and enable them"）
5. 数分後、`https://<ユーザー名>.github.io/<リポジトリ名>/` で表示

## 運用

- 目標値はダッシュボード上の「目標」ボタンで設定（端末のブラウザに保存）
- 取得開始日を変えるときは `update.yml` の `START_DATE`
- 頻度を週1にするときは cron を `'0 20 * * 0'`（月曜 05:00 JST）
- Toggl 側で過去の記録を直しても、毎回全期間を取り直すので反映される
