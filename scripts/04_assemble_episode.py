#!/usr/bin/env python3
"""
Step 4: 把 03 產出的逐句語音檔，依序串接起來，
並加上片頭、片尾、背景音樂，輸出最終的單集 mp3。

Requires: pip install pydub  (另外系統要有 ffmpeg)
片頭/片尾/背景音樂請自行準備好放在 config/podcast.json 指定的路徑
（可以用免版稅音樂庫，例如 YouTube Audio Library）。
"""
import json
import sys
from tw_date import today_tw
from pathlib import Path

try:
    from pydub import AudioSegment
except ImportError:
    sys.exit("請先安裝套件: pip install pydub（並確認系統已安裝 ffmpeg）")

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "podcast.json"
STORIES_DIR = ROOT / "output" / "stories"
AUDIO_DIR = ROOT / "output" / "audio"
EPISODES_DIR = ROOT / "output" / "episodes"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    config = load_config()
    asm = config["assembly"]

    target_date = sys.argv[1] if len(sys.argv) > 1 else today_tw()
    episode_audio_dir = AUDIO_DIR / target_date
    manifest_path = episode_audio_dir / "manifest.json"
    if not manifest_path.exists():
        sys.exit(f"找不到語音 manifest：{manifest_path}（請先跑 03_generate_audio.py）")

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. 依序串接每一句對話，中間留一點停頓
    print("串接對話語音...")
    dialogue = AudioSegment.empty()
    gap = AudioSegment.silent(duration=350)
    for item in manifest:
        seg = AudioSegment.from_file(episode_audio_dir / item["file"])
        dialogue += seg + gap

    # 2. 疊加背景音樂（整段對話期間，音量調低）
    bg_path = ROOT / asm["background_music_path"]
    if bg_path.exists():
        print("疊加背景音樂...")
        bg = AudioSegment.from_file(bg_path)
        bg = bg + asm["background_music_volume_db"]
        # 迴圈背景音樂到跟對話一樣長
        loops_needed = (len(dialogue) // len(bg)) + 1
        bg_full = (bg * loops_needed)[: len(dialogue)]
        dialogue = dialogue.overlay(bg_full)
    else:
        print(f"（找不到背景音樂 {bg_path}，略過此步驟）")

    # 3. 接上片頭、片尾
    crossfade = asm["crossfade_ms"]
    final = dialogue

    intro_path = ROOT / asm["intro_music_path"]
    if intro_path.exists():
        print("加入片頭...")
        intro = AudioSegment.from_file(intro_path)
        final = intro.append(final, crossfade=min(crossfade, len(intro), len(final)))
    else:
        print(f"（找不到片頭音樂 {intro_path}，略過）")

    outro_path = ROOT / asm["outro_music_path"]
    if outro_path.exists():
        print("加入片尾...")
        outro = AudioSegment.from_file(outro_path)
        final = final.append(outro, crossfade=min(crossfade, len(final), len(outro)))
    else:
        print(f"（找不到片尾音樂 {outro_path}，略過）")

    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EPISODES_DIR / f"{target_date}.mp3"
    final.export(out_path, format="mp3", bitrate="128k")

    duration_sec = len(final) / 1000
    print(f"完成！總長度：{duration_sec/60:.1f} 分鐘")
    print(f"已輸出：{out_path}")


if __name__ == "__main__":
    main()
