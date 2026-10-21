#!/usr/bin/env python3
"""
Step 3: 用 ElevenLabs TTS 把故事腳本的每一句話轉成語音，
依角色套用不同的 voice_id，再依序存檔（後製腳本再做串接）。

Requires: ELEVENLABS_API_KEY environment variable.
需先在 config/podcast.json 填入兩個角色的 elevenlabs_voice_id。
"""
import json
import os
import sys
import time
from tw_date import today_tw
from pathlib import Path

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


def tts_line(api_key: str, voice_id: str, text: str, model_id: str, out_path: Path):
    # 遇到限流或伺服器暫時錯誤就等一下重試，其他錯誤直接中止
    for attempt in range(4):
        resp = requests.post(
            TTS_URL.format(voice_id=voice_id),
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": model_id,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=60,
        )
        if resp.status_code == 200:
            out_path.write_bytes(resp.content)
            return
        if resp.status_code not in RETRY_STATUS or attempt == 3:
            break
        wait = 2 ** (attempt + 1)
        print(f"  ElevenLabs 回 {resp.status_code}，{wait} 秒後重試...")
        time.sleep(wait)
    raise RuntimeError(f"ElevenLabs 錯誤 {resp.status_code}: {resp.text[:300]}")


def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("請先設定環境變數 ELEVENLABS_API_KEY")

    config = load_config()
    voice_map = {
        "narrator": config["characters"]["narrator"]["elevenlabs_voice_id"],
        "listener": config["characters"]["listener"]["elevenlabs_voice_id"],
    }
    for role, vid in voice_map.items():
        if vid.startswith("REPLACE_WITH"):
            sys.exit(f"請先在 config/podcast.json 設定 {role} 的 elevenlabs_voice_id")

    model_id = config["tts"]["model_id"]

    target_date = sys.argv[1] if len(sys.argv) > 1 else today_tw()
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

    # 已經產生過的句子跳過（重跑時不再花額度）
    pending = [(i, line) for i, line in enumerate(story["lines"])
               if not out_path_for(i, line).exists()]
    needed = sum(len(line["text"]) for _, line in pending)
    if pending:
        remaining = remaining_characters(api_key)
        print(f"本次需要 {needed} 字元，ElevenLabs 本月剩餘 {remaining} 字元")
        if needed > remaining:
            sys.exit(f"ElevenLabs 額度不足（需要 {needed}，剩 {remaining}），停止配音。"
                     "請升級方案、等下個月重置，或改用其他 TTS。")

    manifest = []
    for i, line in enumerate(story["lines"]):
        voice_id = voice_map[line["role"]]
        out_path = out_path_for(i, line)
        if out_path.exists():
            print(f"[{i+1}/{len(story['lines'])}] ({line['role']}) 已存在，略過")
        else:
            print(f"[{i+1}/{len(story['lines'])}] ({line['role']}) {line['text'][:20]}...")
            tts_line(api_key, voice_id, line["text"], model_id, out_path)
        manifest.append({"index": i, "role": line["role"], "file": out_path.name})

    manifest_path = episode_audio_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"完成！共 {len(manifest)} 段語音，存在 {episode_audio_dir}")


if __name__ == "__main__":
    main()
