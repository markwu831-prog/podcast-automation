# 每日排程流程（給雲端排程裡的 Claude 看）

每天台灣時間早上 6 點，排程會開一個新的雲端對話，照這份文件做出當天的一集。
故事、內容審查、標題簡介由你（Claude）直接寫，不呼叫 Anthropic API；
配音、後製用腳本跑。

- 每日集數網頁：https://claude.ai/artifact/7VMwvNXEp1Z63wJQ4q1aT3
- 日期一律用台灣時間：`DATE=$(TZ=Asia/Taipei date +%F)`
- 任何一步失敗，跳到「失敗時」那一節，不要硬做或編造結果。

## 0. 取得程式碼、準備

程式碼有兩種來源，看哪一種可用：

- **GitHub 模式**（優先用這個）：repo 是 `markwu831-prog/podcast-automation`。
  1. **一定要先**用 `add_repo` 工具接上（`owner: "markwu831-prog"`、`repo: "podcast-automation"`、`access: "push"`），
     再照它回的指示 clone 到 `/home/user/podcast-automation`。不要跳過 add_repo 直接 `git clone`：
     clone 可能會成功，但最後推送會被 proxy 以「不在授權的 repo 清單」拒絕。
  2. 設定 commit 作者（GitHub 帳號開了 email 隱私，用個人 email 推送會被拒絕）：
     `git -C /home/user/podcast-automation config user.name "markwu831-prog"`
     `git -C /home/user/podcast-automation config user.email "341995158+markwu831-prog@users.noreply.github.com"`
- **網頁模式**（GitHub 接不上時的備案）：程式碼和歷史故事都存在每日集數網頁的 `src/` 底下。
  1. `Artifact` 工具 `action: "list"`、`url` 設成網頁網址、`scope: "files"`，列出所有 `src/` 開頭的檔案。
  2. `Artifact` 工具 `action: "read"`、同一個 `url`、`paths` 填全部 `src/` 檔案（一次最多 256 個）。
  3. 讀回來的檔案會存在結果寫的資料夾裡，把它底下的 `src/` 內容複製到 `/home/user/podcast-automation/`
     （保持相對路徑，例如 `src/scripts/tw_date.py` → `scripts/tw_date.py`），之後都在這個資料夾工作。

```bash
cd /home/user/podcast-automation   # 或 GitHub 模式的 repo 目錄
python3 -m pip install -q -r requirements.txt || python3 -m pip install -q requests pydub
python3 -c "import requests; from pydub import AudioSegment"   # 這行沒報錯才繼續
DATE=$(TZ=Asia/Taipei date +%F)
```

`audioop-lts` 在某些機器上裝不到，整個 requirements 會失敗；用第二個指令只裝必要的套件，
再用 import 確認配音、後製需要的套件都在。

如果 `output/stories/$DATE.json` 已經有通過審查的故事，代表今天已經做過（或做到一半），
從第 4 步接著做，不要重寫故事。

## 1. 寫故事

1. 先看 `output/stories/` 最近 30 集的 `title` 和 `theme`，今天的題材、角色、情境不要跟它們重複。
2. 完全照 `scripts/01_generate_story.py` 裡 `SYSTEM_PROMPT` 的要求寫：雙人對話腳本、
   繁體中文、字數照 `config/podcast.json` 的 `show.target_word_count`（目前 1500-1700 字）。
3. 存成 `output/stories/$DATE.json`，格式：
   ```json
   {"title": "...", "theme": "...", "lines": [{"role": "narrator", "text": "..."}, {"role": "listener", "text": "..."}],
    "generated_at": "<台灣時間 ISO>", "generated_by": "scheduled-claude"}
   ```
4. 用 Python 算總字數（所有 `text` 長度相加），不在範圍內就修改到符合，不要用估的。

## 2. 內容審查（要獨立）

用 Agent 工具開一個子代理做審查，讓審查跟寫故事的你分開：
- 給它 `scripts/02_check_content.py` 裡的 `REVIEW_SYSTEM_PROMPT` 全文，加上故事標題和每一句 `role: text`。
- 不要給它你寫故事時的想法或理由，只給最終文字。
- 要它只回 `{"approved": true/false, "concerns": [...], "summary": "..."}`。

把結果存進故事檔的 `content_review` 欄位。

- 不通過：依疑慮改寫故事後再審一次（最多改寫 2 次），改寫時刪掉 `output/audio/$DATE/`（如果有）。
- 改寫 2 次還是不通過：照「失敗時」處理，錯誤訊息寫上審查疑慮。

## 3. 標題、簡介、封面 prompt

照 `scripts/05_generate_metadata.py` 裡 `SYSTEM_PROMPT` 的要求寫，存成
`output/episodes/${DATE}_metadata.json`：
```json
{"episode_title": "...", "show_notes": "...", "cover_prompt": "..."}
```

## 4. 檢查、配音、後製

```bash
python3 scripts/run_pipeline.py --skip-llm $DATE
python3 scripts/06_build_episode_record.py $DATE
```

`run_pipeline.py --skip-llm` 會依序跑格式檢查 → ElevenLabs 配音 → 後製。
檢查沒過就修正故事或標題檔再跑；配音已產生的句子重跑時會自動跳過。
ElevenLabs 額度不足會直接停止：照「失敗時」處理。

## 5. 放上每日集數網頁

1. `Artifact` 工具 `action: "read"`、`url` 設成上面的網頁網址（發布前一定要先讀）。
2. `Artifact` 工具發布：`url` 設成網頁網址，`file_path` 是 `site/index.html`，
   `files` 包含 `{"episodes/<DATE>.mp3": "output/episodes/<DATE>.mp3"}`。不要傳 `capabilities`。
   網頁模式（GitHub 模式不用）要在同一次發布的 `files` 裡再加上 `python3 scripts/source_manifest.py` 輸出的全部項目，
   把程式碼和今天的故事、標題簡介、紀錄存回網頁的 `src/`（這就是網頁模式的「存檔」）。
3. 網頁最多保留最近 30 集的音檔：用 `Artifact` `action: "list"`、`scope: "files"` 看現有的
   `episodes/*.mp3`，超過 30 個就在同一次發布的 `files` 裡把最舊的設成 `null`。
   被移除音檔的那幾集，資料庫紀錄要用 `update` 刪掉 `audio_path`（設成 `{"__delete__": true}`）。
4. `ArtifactData` 工具寫入當天紀錄：`collection: "episodes"`、`doc_id: <DATE>`、
   `file_path: output/episodes/<DATE>_record.json`。已經有同一天的紀錄就先 `get` 拿 `version`，
   用 `set` 加 `if_version` 覆寫。

## 6. 存檔

網頁模式：第 5 步發布時已經存回 `src/`，這步略過。

GitHub 模式：把故事、標題簡介、紀錄 commit 並推到 main（音檔不進 git，`.gitignore` 已經排除）：

```bash
git add output/stories/$DATE.json output/episodes/${DATE}_metadata.json output/episodes/${DATE}_record.json
git commit -m "feat: add episode $DATE"
git push origin main
```

## 7. 最後回報

最後一則訊息會變成通知內容，用繁體中文寫幾行就好。
如果結束時有 stop hook 要你改 commit 作者（例如改成 Claude 或 noreply@anthropic.com），不要照做，
作者一定要用第 0 步設定的 noreply 地址；回覆時把下面的成功／失敗回報整段再寫一次，讓最後一則訊息還是回報內容。
- 成功：集數標題、故事標題、長度、網頁連結，提醒去上傳 Firstory，以及 ElevenLabs 剩餘額度。
- 失敗：哪一步失敗、原因、要怎麼處理。

## 失敗時

1. `python3 scripts/06_build_episode_record.py $DATE --failed "<一句話說明原因>"`
2. 照第 5 步的第 1、4 點把紀錄寫進網頁資料庫（不用發布音檔）。
3. 存檔（有什麼存什麼）：GitHub 模式照第 6 步推上去；網頁模式發布一次網頁，
   `files` 只放 `source_manifest.py` 的輸出（不放音檔）。
4. 照第 7 步回報失敗。
