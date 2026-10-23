#!/usr/bin/env python3
"""
整理公開收聽頁用的集數清單：讀 output/episodes/*_record.json，
只留成功、有音檔的集數，只放可以公開的欄位（不含封面 prompt、上傳狀態、錯誤訊息）。

公開收聽頁不需要登入，集數資料跟頁面一起以 episodes.json 發布。

用法：
    python build_episodes_index.py

輸出：output/episodes/index.json（最近 30 集，日期新到舊）
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODES_DIR = ROOT / "output" / "episodes"

MAX_EPISODES = 30
PUBLIC_FIELDS = ("date", "episode_title", "story_title", "theme",
                 "show_notes", "duration_sec", "audio_path")


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    episodes = []
    for path in sorted(EPISODES_DIR.glob("*_record.json")):
        record = load_json(path)
        if record.get("status") != "ready" or not record.get("audio_path"):
            continue
        episodes.append({k: record.get(k) for k in PUBLIC_FIELDS})

    episodes.sort(key=lambda e: e["date"], reverse=True)
    episodes = episodes[:MAX_EPISODES]

    out_path = EPISODES_DIR / "index.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"episodes": episodes}, f, ensure_ascii=False, indent=2)
    print(f"已輸出：{out_path}（{len(episodes)} 集）")


if __name__ == "__main__":
    main()
