# 交接：從雲端工作階段移到 MacBook Air（2026-10-23）

這份文件整理雲端 Claude Code 工作階段做完的事、現在的狀態、在 Mac 上要怎麼接手。
以後每日排程改在 MacBook Air 的桌面版 Claude Code 跑（排程時間要把 Mac 打開）。

## 目前狀態

**已經完成的：**
- 流程①~⑤：故事 → 內容審查 → 配音 → 後製 → 標題／簡介／封面 prompt。
- 排程模式：故事、審查、標題簡介由 Claude 直接寫（不用 ANTHROPIC_API_KEY），審查用獨立的子代理；
  配音、後製用 `scripts/run_pipeline.py --skip-llm`。完整步驟在 `DAILY_RUN.md`。
- 日期一律用台灣時間（`scripts/tw_date.py`）。
- 配音（`scripts/03_generate_audio.py`）：配音前先查 ElevenLabs 額度、已產生的句子重跑會跳過、暫時性錯誤自動重試。
- **Azure 配音程式已寫好，但還沒測過**（沒有金鑰）：`config/podcast.json` 的 `tts.provider` 改成 `azure` 就切換，
  需要環境變數 `AZURE_SPEECH_KEY`。聲音：姐姐 `zh-TW-HsiaoChenNeural`、小豆 `zh-TW-HsiaoYuNeural`（音高 +12%、語速 +5%）。
- 兩個網頁：
  - **私人後台**（只有自己能用，要登入）：試聽、下載 mp3＋簡介 zip、打勾記錄「已上傳 Firstory」。
  - **公開收聽頁**（不用登入）：給家人朋友分享，只有收聽和簡介。

**已經做好的集數：**

| 日期 | 集數標題 | 長度 |
|---|---|---|
| 10/21 | 害羞的小刺蝟圓圓交朋友 | 5:26 |
| 10/22 | 小狐狸橘橘勇敢說真話 | 5:37 |
| 10/23 | 小海獺波波的貝殼小屋 | 5:34 |

10/24 雲端那次**卡在權限確認、沒有做出來**（見下方「雲端排程收尾」）。三集都還沒上傳 Firstory。

## 重要網址與 ID

- GitHub repo：https://github.com/markwu831-prog/podcast-automation（私人）
- 私人後台：https://claude.ai/artifact/7VMwvNXEp1Z63wJQ4q1aT3
- 公開收聽頁：https://claude.ai/artifact/TuvMhFUZ5MmngCpn1dPm5S
- 雲端排程（試做，**已停用**）：`trig_01Bf9Ke5wc5yPhCA9D3nbfpZ`
- 卡住的 10/24 雲端對話：`cse_01RZ3kPdPU5CYmBAFhMXfkAT`
- git commit 作者：`markwu831-prog <341995158+markwu831-prog@users.noreply.github.com>`

## Mac 第一次設定

```bash
# 1. 取得程式碼
git clone https://github.com/markwu831-prog/podcast-automation.git
cd podcast-automation
git config user.name "markwu831-prog"
git config user.email "341995158+markwu831-prog@users.noreply.github.com"

# 2. 安裝工具與套件
brew install ffmpeg python
python3 -m pip install -r requirements.txt

# 3. API 金鑰放在 shell 設定檔（例如 ~/.zshrc），不要寫進任何專案檔案
export ELEVENLABS_API_KEY="..."
# 之後拿到 Azure 金鑰再加：
# export AZURE_SPEECH_KEY="..."

# 4. 確認環境（應該顯示「檢查通過」）
python3 scripts/validate_episode.py 2026-10-23
```

然後用桌面版 Claude Code 打開這個資料夾。它會自動讀 `CLAUDE.md`，再請它讀這份 `HANDOFF.md`。

**注意：** 桌面版 Claude 要讀得到 `ELEVENLABS_API_KEY`。如果它是從 Dock 打開、讀不到 `~/.zshrc` 的變數，
請它跑 `echo ${ELEVENLABS_API_KEY:+已設定}` 確認；讀不到就用 Claude Code 的設定（settings.json 的 `env`）設定。

## 在 Mac 上排程

1. 在桌面版 Claude Code 建一個每天 **5:50**（台灣時間）的排程任務，提示詞：
   「照 repo 裡的 DAILY_RUN.md，用本機模式做出今天的晚安故事屋。」
2. 排程只有在 Mac 開著、Claude App 開著時才會跑。錯過的那天不會自己補做；打開後可以手動叫它照 DAILY_RUN.md 補做。
3. 在 Mac 上是**本機模式**：程式碼就在 repo 裡，`git pull` 同步後直接做，做完 commit 推回 GitHub；不需要網頁備份（`src/`）。
4. **Mac 的排程建好之後，不要再打開雲端排程**，避免兩邊各做一集、重複扣 ElevenLabs 額度。

## 雲端排程收尾（10/24 結果）

- 試做結果：10/21（手動測試）、10/22、10/23 成功；**10/24 失敗**，雲端排程已停用。
- 10/24 失敗原因：雲端排程沒有接 GitHub 的工具，只能從私人後台的 `src/` 還原程式碼；
  讀 `src/config/podcast.json` 時被 Claude Code 當成受保護的設定檔，跳出要人按「允許」的確認，排程沒人按就一直卡著。
- 10/24 這集的補法（擇一）：
  - 打開卡住的那個雲端對話按「允許」，讓它繼續做完；或
  - 在 Mac 上用本機模式補做：`git pull` 後叫 Claude「照 DAILY_RUN.md 本機模式做 2026-10-24 這集」。
- 不要再重新打開雲端排程，改用 Mac 排程。

## 踩過的坑

- **日期**：雲端機器是 UTC，台灣早上 6 點時 UTC 還是前一天；一律用 `tw_date.py` 或 `TZ=Asia/Taipei date +%F`。
- **pydub**：Python 3.13 拿掉了 audioop，要裝 `audioop-lts`；有些機器裝不到，就只裝 `requests pydub` 再確認能 import。
- **GitHub 推送被拒（email 隱私）**：commit 作者一定要用上面的 noreply 地址。
- **stop hook 要求改作者**：雲端環境結束時會提示把作者改成 Claude，不要照做（會被 email 隱私擋）。
- **雲端排程推不上 GitHub**：排程開的雲端對話沒有 `add_repo` 工具，proxy 會拒絕推送；這是改到 Mac 的主因之一。
- **設定檔名**：`config/settings.json` 這個檔名會被 Artifact 讀取的安全規則擋，所以改名成 `config/podcast.json`。
- **分享網頁要求登入**：私人後台用了資料庫和下載功能，沒登入的人打不開；分享請用公開收聽頁。
- **公開收聽頁的分享設定**：要在該頁的 Share 選單設成「知道連結的任何人」（只有擁有者能改）。
- **Artifact 發布**：更新別的對話做的網頁前要先 `read`；被別人（例如排程）更新過會要求先合併最新版。
- **網頁模式卡權限確認**：還原 `config/` 底下的檔案會被當成受保護設定檔，要人按允許；無人值守的排程會卡住。本機模式沒有這個問題。
- **網頁備份 `src/` 會蓋掉網頁**：網頁模式會用 `src/site/index.html` 重新發布私人後台，`src/` 沒同步就會退回舊版頁面。
  本機模式不用網頁備份，問題就不存在。
- **ElevenLabs 聲音庫的聲音**（例如台灣腔 Yu `fQj4gJSexpu8RDE2Ii5m`）：免費方案不能用 API 呼叫，會回 402。

## 待辦

- [ ] **配音額度**：ElevenLabs 免費方案每月 10,000 字元，目前剩約 4,400（11/21 重置），一集約 1,550 字。
      10/24 做完後大概只夠再做一集。要每天跑：拿到 Azure 金鑰後測 Azure（每月免費 50 萬字元），或升級 ElevenLabs。
- [ ] **測試 Azure**：設好 `AZURE_SPEECH_KEY` 後，先用 `python3 scripts/03_generate_audio.py 2026-10-23 --provider azure`
      配一集試聽（先把 `output/audio/2026-10-23/` 移走，不然會跳過已存在的句子），聲音可以再把 `tts.provider` 改成 `azure`。
- [ ] 公開收聽頁 Share 設成「知道連結的任何人」，用無痕視窗確認打得開。
- [ ] 片頭、片尾、背景音樂：放 mp3 到 `assets/`（路徑見 `config/podcast.json` 的 `assembly`），沒有的話後製會略過。
- [ ] 封面圖：目前只產生英文 prompt，還沒接圖像生成服務。
- [ ] Firstory 上傳：沒有公開 API，要手動上傳；上傳完到私人後台打勾。
