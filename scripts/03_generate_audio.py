#!/usr/bin/env python3
"""
Step 3: 把故事腳本的每一句話轉成語音，依角色套用不同的聲音，
再依序存檔（後製腳本再做串接）。

配音服務看 config/podcast.json 的 tts.provider：
- "elevenlabs"：需要 ELEVENLABS_API_KEY，角色用 elevenlabs_voice_id
- "azure"：需要 AZURE_SPEECH_KEY（區域用 tts.azure.region，或 AZURE_SPEECH_REGION），
  角色用 azure_voice（例如 zh-TW-HsiaoChenNeural），可選 azure_prosody 調整語速、音高

用法：
    python 03_generate_audio.py [日期] [--provider azure|elevenlabs]
"""
import json
import os
import sys
import time
from tw_date import today_tw
from pathlib import Path
from xml.sax.saxutils import escape

try:
    import requests
except ImportError:
    sys.exit("請先安裝套件: pip install requests")

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "podcast.json"
STORIES_DIR = ROOT / "output" / "stories"
AUDIO_DIR = ROOT / "output" / "audio"

TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
SUBSCRIPTION_URL = "https://api.elevenlabs.io/v1/user/subscription"
AZURE_TTS_URL = "https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
RETRY_STATUS = {429, 500, 502, 503, 504}


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def remaining_characters(api_key: str) -> int:
    """查 ElevenLabs 本月剩餘字元額度。"""
    resp = requests.get(SUBSCRIPTION_URL, headers={"xi-api-key": api_key}, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"查詢 ElevenLabs 額度失敗 {resp.status_code}: {resp.text[:300]}")
    sub = resp.json()
    return sub["character_limit"] - sub["character_count"]


def post_with_retry(name: str, url: str, **kwargs) -> bytes:
    # 遇到限流或伺服器暫時錯誤就等一下重試，其他錯誤直接中止
    for attempt in range(4):
        resp = requests.post(url, timeout=60, **kwargs)
        if resp.status_code == 200:
            return resp.content
        if resp.status_code not in RETRY_STATUS or attempt == 3:
            break
        wait = 2 ** (attempt + 1)
        print(f"  {name} 回 {resp.status_code}，{wait} 秒後重試...")
        time.sleep(wait)
    raise RuntimeError(f"{name} 錯誤 {resp.status_code}: {resp.text[:300]}")


class ElevenLabsTTS:
    def __init__(self, config: dict):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            sys.exit("請先設定環境變數 ELEVENLABS_API_KEY")
        self.model_id = config["tts"]["model_id"]
        self.voices = {}
        for role in ("narrator", "listener"):
            vid = config["characters"][role]["elevenlabs_voice_id"]
            if vid.startswith("REPLACE_WITH"):
                sys.exit(f"請先在 config/podcast.json 設定 {role} 的 elevenlabs_voice_id")
            self.voices[role] = vid

    def check_quota(self, needed: int):
        remaining = remaining_characters(self.api_key)
        print(f"本次需要 {needed} 字元，ElevenLabs 本月剩餘 {remaining} 字元")
        if needed > remaining:
            sys.exit(f"ElevenLabs 額度不足（需要 {needed}，剩 {remaining}），停止配音。"
                     "請升級方案、等下個月重置，或改用其他 TTS。")

    def synthesize(self, role: str, text: str) -> bytes:
        return post_with_retry(
            "ElevenLabs",
            TTS_URL.format(voice_id=self.voices[role]),
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": self.model_id,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )


class AzureTTS:
    def __init__(self, config: dict):
        self.api_key = os.environ.get("AZURE_SPEECH_KEY")
        if not self.api_key:
            sys.exit("請先設定環境變數 AZURE_SPEECH_KEY")
        azure = config["tts"].get("azure", {})
        self.region = os.environ.get("AZURE_SPEECH_REGION") or azure.get("region", "eastasia")
        self.output_format = azure.get("output_format", "audio-24khz-96kbitrate-mono-mp3")
        self.characters = {}
        for role in ("narrator", "listener"):
            char = config["characters"][role]
            if not char.get("azure_voice"):
                sys.exit(f"請先在 config/podcast.json 設定 {role} 的 azure_voice")
            self.characters[role] = char

    def check_quota(self, needed: int):
        # Azure 沒有查剩餘額度的簡單 API；免費方案超量時會回 429，交給重試與錯誤訊息處理
        print(f"本次需要 {needed} 字元（Azure 語音）")

    def ssml(self, role: str, text: str) -> str:
        char = self.characters[role]
        voice = char["azure_voice"]
        lang = "-".join(voice.split("-")[:2])
        body = escape(text)
        prosody = char.get("azure_prosody") or {}
        if prosody:
            attrs = " ".join(f'{k}="{escape(str(v))}"' for k, v in prosody.items())
            body = f"<prosody {attrs}>{body}</prosody>"
        return (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
                f'<voice name="{voice}">{body}</voice></speak>')

    def synthesize(self, role: str, text: str) -> bytes:
        return post_with_retry(
            "Azure 語音",
            AZURE_TTS_URL.format(region=self.region),
            headers={
                "Ocp-Apim-Subscription-Key": self.api_key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": self.output_format,
                "User-Agent": "podcast-automation",
            },
            data=self.ssml(role, text).encode("utf-8"),
        )


PROVIDERS = {"elevenlabs": ElevenLabsTTS, "azure": AzureTTS}


def main():
    args = sys.argv[1:]
    config = load_config()
    provider = config["tts"].get("provider", "elevenlabs")
    if "--provider" in args:
        i = args.index("--provider")
        provider = args[i + 1]
        del args[i:i + 2]
    if provider not in PROVIDERS:
        sys.exit(f"不支援的配音服務：{provider}（可用：{', '.join(PROVIDERS)}）")
    tts = PROVIDERS[provider](config)

    target_date = args[0] if args else today_tw()
    story_path = STORIES_DIR / f"{target_date}.json"
    if not story_path.exists():
        sys.exit(f"找不到故事檔案：{story_path}")

    with open(story_path, encoding="utf-8") as f:
        story = json.load(f)

    if not story.get("content_review", {}).get("approved"):
        sys.exit("這篇故事尚未通過內容審查（或還沒跑過 02_check_content.py），停止配音。")

    episode_audio_dir = AUDIO_DIR / target_date
    episode_audio_dir.mkdir(parents=True, exist_ok=True)

    def out_path_for(i, line):
        return episode_audio_dir / f"{i:03d}_{line['role']}.mp3"

    # 已經產生過的句子跳過（重跑時不再花額度）；換配音服務時請先刪掉 output/audio/<日期>/
    pending = [(i, line) for i, line in enumerate(story["lines"])
               if not out_path_for(i, line).exists()]
    if pending:
        tts.check_quota(sum(len(line["text"]) for _, line in pending))

    manifest = []
    for i, line in enumerate(story["lines"]):
        out_path = out_path_for(i, line)
        if out_path.exists():
            print(f"[{i+1}/{len(story['lines'])}] ({line['role']}) 已存在，略過")
        else:
            print(f"[{i+1}/{len(story['lines'])}] ({line['role']}) {line['text'][:20]}...")
            out_path.write_bytes(tts.synthesize(line["role"], line["text"]))
        manifest.append({"index": i, "role": line["role"], "file": out_path.name})

    manifest_path = episode_audio_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"完成！共 {len(manifest)} 段語音（{provider}），存在 {episode_audio_dir}")


if __name__ == "__main__":
    main()
