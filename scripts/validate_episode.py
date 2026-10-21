#!/usr/bin/env python3
"""
檢查當天的故事腳本、審查結果、標題簡介檔格式是否正確，
給「由排程裡的 Claude 直接寫」的模式用（不經過 01/02/05 的 API 呼叫），
在花 ElevenLabs 額度配音之前先擋下格式錯誤。

用法：
    python validate_episode.py              # 檢查今天（台灣時間）
    python validate_episode.py 2026-10-22   # 檢查指定日期
"""
import json
import sys
from pathlib import Path

from tw_date import today_tw

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "podcast.json"
STORIES_DIR = ROOT / "output" / "stories"
EPISODES_DIR = ROOT / "output" / "episodes"

# 字數允許比設定的範圍多/少一點，避免差幾個字就整個流程中止
WORD_COUNT_TOLERANCE = 100


def check_story(story: dict, word_lo: int, word_hi: int) -> list:
    errors = []
    for key in ("title", "theme", "lines", "content_review"):
        if key not in story:
            errors.append(f"故事缺少欄位：{key}")
    if errors:
        return errors

    lines = story["lines"]
    if not isinstance(lines, list) or not lines:
        return ["lines 必須是非空陣列"]
    for i, line in enumerate(lines):
        if line.get("role") not in ("narrator", "listener"):
            errors.append(f"第 {i} 句 role 必須是 narrator 或 listener：{line.get('role')}")
        if not str(line.get("text", "")).strip():
            errors.append(f"第 {i} 句 text 是空的")

    total = sum(len(l.get("text", "")) for l in lines)
    if not (word_lo - WORD_COUNT_TOLERANCE <= total <= word_hi + WORD_COUNT_TOLERANCE):
        errors.append(f"總字數 {total} 不在 {word_lo}-{word_hi} 字範圍內")

    review = story["content_review"]
    if not isinstance(review, dict) or "approved" not in review:
        errors.append("content_review 格式錯誤，需要 approved / concerns / summary")
    elif review["approved"] is not True:
        errors.append(f"內容審查未通過：{review.get('concerns')}")
    return errors


def check_metadata(metadata: dict) -> list:
    errors = []
    for key in ("episode_title", "show_notes", "cover_prompt"):
        if not str(metadata.get(key, "")).strip():
            errors.append(f"標題簡介檔缺少欄位：{key}")
    return errors


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else today_tw()
    with open(CONFIG_PATH, encoding="utf-8") as f:
        word_lo, word_hi = json.load(f)["show"]["target_word_count"]

    errors = []
    story_path = STORIES_DIR / f"{target_date}.json"
    if not story_path.exists():
        errors.append(f"找不到故事檔案：{story_path}")
    else:
        with open(story_path, encoding="utf-8") as f:
            story = json.load(f)
        errors += check_story(story, word_lo, word_hi)

    metadata_path = EPISODES_DIR / f"{target_date}_metadata.json"
    if not metadata_path.exists():
        errors.append(f"找不到標題簡介檔：{metadata_path}")
    else:
        with open(metadata_path, encoding="utf-8") as f:
            errors += check_metadata(json.load(f))

    if errors:
        print("❌ 檢查未通過：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    total = sum(len(l["text"]) for l in story["lines"])
    print(f"✅ 檢查通過：{story['title']}（{len(story['lines'])} 句，{total} 字）")


if __name__ == "__main__":
    main()
