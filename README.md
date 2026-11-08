# Toggl Time Dashboard

Toggl Track の記録を毎日自動取得し、GitHub Pages で閲覧するダッシュボード。

- `index.html` … ダッシュボード本体（`data.json` を読んで全てブラウザ内で集計）
- `data.json` … Toggl から取得したローデータ（Actions が自動更新）
- `fetch_toggl.py` … Toggl API v9 → `data.json`
- `.github/workflows/update.yml` … 毎日 09:00 JST に実行（前夜の睡眠タイマーが止まった後）

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

- 目標値は `targets.json` で管理（全端末共通）。GitHubで開いて鉛筆アイコン → 数字を書き換え → Commit changes。1〜2分で反映
  - `work_hours_workday` / `work_hours_offday`：Workの上限（稼働日1日・休日1日あたりh）。超えたら赤
  - `cymbi_hours_workday` / `cymbi_hours_offday`：Cymbiの目標（稼働日1日・休日1日あたりh）。下回ったら赤
  - `sleep_hours_per_day`：1日の睡眠目標（h）
  - `kaitaku_percent`：🚀開拓比率の目標（%）
  - `business_hours_per_month`：Cymbi以外の事業ごとの月の上限（h）。その月の稼働日数で割って稼働日に配分。超えたら赤
  - `days_off`：個人的な休み（"YYYY-MM-DD"）。土日・祝日は自動で休日扱い
  - `extra_workdays`：土日・祝日だけど稼働する日（"YYYY-MM-DD"）
- 祝日は `holidays_jp.json`（2025〜2028年）。2029年以降は追加が必要
  - 未設定は `null`（30日平均で判定）
- 取得開始日を変えるときは `update.yml` の `START_DATE`
- 頻度を週1にするときは cron を `'0 0 * * 1'`（月曜 09:00 JST）
- Toggl 側で過去の記録を直しても、毎回全期間を取り直すので反映される
