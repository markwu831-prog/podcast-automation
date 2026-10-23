# 晚安故事屋 Podcast 自動化

每天產生一集約 5 分鐘的原創兒童睡前故事 Podcast（說故事姐姐＋5 歲男孩小豆的雙人對話），
配音後放上私人後台和公開收聽頁，再由使用者手動上傳 Firstory。

開始工作前先讀：
- `HANDOFF.md`：目前狀態、網址與 ID、踩過的坑、待辦
- `DAILY_RUN.md`：每日製作一集的完整步驟（排程跑的就是這份）

規則：
- 日期一律用台灣時間（`scripts/tw_date.py` 或 `TZ=Asia/Taipei date +%F`）。
- git commit 作者用 `markwu831-prog <341995158+markwu831-prog@users.noreply.github.com>`，GitHub 開了 email 隱私，用其他地址推送會被拒絕。
- API 金鑰只用環境變數（`ELEVENLABS_API_KEY`、`AZURE_SPEECH_KEY`），不要寫進任何檔案。
