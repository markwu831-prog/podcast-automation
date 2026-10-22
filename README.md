# 晚安故事屋 — AI 自動生成 Podcast 腳本

涵蓋流程①~⑤（故事生成 → 內容審查 → AI 配音 → 後製 → 標題/簡介/封面 prompt）。
⑥上傳 Firstory 之後的步驟刻意不自動化（沒有公開 API），由你手動完成。

## 使用前準備

1. 安裝相依套件：
   ```
   pip install -r requirements.txt
   ```
   另外系統要有 `ffmpeg`（pydub 剪接音訊需要）。

2. 設定環境變數：
   ```
   export ANTHROPIC_API_KEY="你的 Anthropic API key"
   export ELEVENLABS_API_KEY="你的 ElevenLabs API key"
   ```

3. 編輯 `config/podcast.json`：
   - 把 `narrator` 和 `listener` 的 `elevenlabs_voice_id` 換成你在 ElevenLabs
     Voice Library 選好的兩個聲音的實際 Voice ID
   - （選用）把片頭/片尾/背景音樂檔放到 `assets/` 資料夾，並在
     `assembly` 區塊確認路徑正確；沒有的話會自動略過這些步驟

## 執行

跑完整流程：
```
python scripts/run_pipeline.py
```

故事、審查、標題簡介已經由 Claude 寫好時（雲端排程用這個），只跑檢查 → 配音 → 後製：
```
python scripts/run_pipeline.py --skip-llm
```

或單獨跑某一步（除錯用）：
```
python scripts/01_generate_story.py
python scripts/02_check_content.py
python scripts/03_generate_audio.py
python scripts/04_assemble_episode.py
python scripts/05_generate_metadata.py
python scripts/validate_episode.py         # 檢查故事/審查/標題簡介格式
python scripts/06_build_episode_record.py  # 整理成每日集數網頁用的紀錄
```

日期一律用台灣時間（`scripts/tw_date.py`），雲端機器是 UTC 也不會錯開。

## 雲端每日排程

每天台灣時間早上 6 點，Claude 雲端排程會開一個新對話，照 `DAILY_RUN.md` 做出當天的一集：
- 故事、內容審查（獨立的子代理）、標題簡介由排程裡的 Claude 直接寫，不需要 ANTHROPIC_API_KEY
- 配音、後製用腳本跑
- 成品放上「每日集數」網頁：https://claude.ai/artifact/7VMwvNXEp1Z63wJQ4q1aT3
  可以試聽、下載（mp3 + 標題簡介文字檔的 zip）、標記是否已上傳 Firstory
- 故事、標題簡介、紀錄每天推到 GitHub（`markwu831-prog/podcast-automation`），音檔只放網頁
- 跑完會推播／寄信通知

## 產出位置

- `output/stories/<日期>.json` — 故事腳本 + 審查結果
- `output/audio/<日期>/` — 逐句語音檔
- `output/episodes/<日期>.mp3` — 最終完整單集音檔
- `output/episodes/<日期>_metadata.json` — 標題、簡介、封面 prompt
- `output/episodes/<日期>_record.json` — 寫進每日集數網頁的紀錄

拿到 `.mp3` 跟 metadata 之後，手動上傳到 Firstory 後台即可。

## 目前進度（2026-10-21）

- 每日自動化：雲端排程 + 每日集數網頁（見上方「雲端每日排程」）

- 第 1 集試作完成：《害羞的小刺蝟找朋友》，腳本在 `output/stories/2026-10-21.json`
  - 用 ElevenLabs 免費聲音：姐姐 Sarah（EXAVITQu4vr4xnSDxMaL）、小豆 Jessica（cgSgspJ2msm6clMCkdW9）
  - 結果：可以用，但有外國腔；900 字只有約 2 分 48 秒，所以字數已改成 1500-1700 字
- 免費方案限制：社群聲音庫（台灣腔）和 Voice Design 都要付費方案才能透過 API 使用
  - 台灣腔候選（需 Creator 方案）：姐姐 Angel（aQwAQvuS5kErJvZlR7wN）、小豆 Lulu（BT0SH7Hb8NRPpT5xbCgg）
- 下一步：改用 Azure 語音（免費、有台灣腔 zh-TW-HsiaoChenNeural / HsiaoYuNeural），等申請金鑰
- ElevenLabs 免費方案每月只有 10,000 字元，一集約 1,600 字，每月只夠約 6 集；
  每天跑（每月約 48,000 字元）需要升級付費方案或改用 Azure。
  配音前會先查額度，不夠就停止並通知，不會做到一半
- 網路設定：每個雲端環境各自設定，要改的是 Claude Code 雲端環境的 Network access
  （對話標題列的環境選單 → Edit），不是 claude.ai 的 Settings → Capabilities
  （那個只管一般聊天的程式執行）。目前這個環境已經連得到 `api.elevenlabs.io`；
  之後改用 Azure 要加 `eastasia.tts.speech.microsoft.com`（依 Azure 區域而定）
- API 金鑰一律用環境變數，不寫進檔案

## 待辦（之後要補的部分）

- [x] 03_generate_audio.py 加上 Azure TTS 版本（`tts.provider` 設成 `azure`，需要 AZURE_SPEECH_KEY）
- [ ] 片頭/片尾/背景音樂（第 1 集是用瀏覽器程式即時合成的，04 腳本需要 mp3 素材）

- [ ] 封面圖目前只產生文字 prompt，還沒接圖像生成 API，需要你決定要用哪個服務
- [ ] 片頭/片尾/背景音樂素材還沒準備
