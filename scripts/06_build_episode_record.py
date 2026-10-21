#!/usr/bin/env python3
"""
Step 6: 把當天的故事、標題簡介、音檔長度整理成一筆紀錄 JSON，
給「每日集數」網頁的資料庫用（雲端排程用 ArtifactData 寫入）。

用法：
    python 06_build_episode_record.py                # 今天（台灣時間），成功的集數
    python 06_build_episode_record.py 2026-10-22
    python 06_build_episode_record.py 2026-10-22 --failed "ElevenLabs 額度不足"

輸出：output/episodes/<日期>_record.json
"""
import json
import subprocess
import sys
from pathlib import Path

from tw_date import now_tw_iso, today_tw

ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = ROOT / "output" / "stories"
EPISODES_DIR = ROOT / "output" / "episodes"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(out.stdout.strip()), 1)


def main():
    args = sys.argv[1:]
    error = None
    if "--failed" in args:
        i = args.index("--failed")
        error = args[i + 1] if i + 1 < len(args) else "這次排程沒有成功產生音檔。"
        del args[i:i + 2]
    target_date = args[0] if args else today_tw()

    story = load_json(STORIES_DIR / f"{target_date}.json")
    metadata = load_json(EPISODES_DIR / f"{target_date}_metadata.json")
    mp3_path = EPISODES_DIR / f"{target_date}.mp3"

    record = {
        "date": target_date,
        "story_title": story.get("title", ""),
        "theme": story.get("theme", ""),
        "episode_title": metadata.get("episode_title", ""),
        "show_notes": metadata.get("show_notes", ""),
        "cover_prompt": metadata.get("cover_prompt", ""),
        "char_count": sum(len(l["text"]) for l in story.get("lines", [])),
        "created_at": now_tw_iso(),
        "uploaded": False,
    }
    if error:
        record.update(status="failed", error=error)
    else:
        if not mp3_path.exists():
            sys.exit(f"找不到音檔：{mp3_path}（請先跑 04_assemble_episode.py）")
        record.update(
            status="ready",
            audio_path=f"episodes/{target_date}.mp3",
            duration_sec=audio_duration(mp3_path),
        )

    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EPISODES_DIR / f"{target_date}_record.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"已輸出：{out_path}")


if __name__ == "__main__":
    main()
