#!/usr/bin/env python3
"""
Step 5: 產生這一集的標題、簡介文字，以及封面圖的生成提示詞（prompt）。
（實際封面圖請另外用圖像生成服務跑這個 prompt，例如 DALL-E / Midjourney /
Stable Diffusion API，這裡先只產生文字素材，避免綁死單一圖像服務。）

Requires: ANTHROPIC_API_KEY environment variable.
"""
import json
import os
import sys
from tw_date import today_tw
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.exit("請先安裝套件: pip install anthropic")

ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = ROOT / "output" / "stories"
EPISODES_DIR = ROOT / "output" / "episodes"

SYSTEM_PROMPT = """你是兒童 Podcast 的內容編輯，請根據提供的故事內容，產生：
1. episode_title：一句吸引人、適合小孩的集數標題（不超過20字）
2. show_notes：100-150字的節目簡介，溫馨口吻，給家長看的導聆文字
3. cover_prompt：一段英文的圖像生成 prompt，用來畫這一集的封面插畫。
   風格要求：溫馨手繪童書插畫風、色彩柔和、適合兒童Podcast封面、
   畫面需扣合故事核心意象，不要出現文字。

只輸出 JSON，格式：
{"episode_title": "...", "show_notes": "...", "cover_prompt": "..."}
"""


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("請先設定環境變數 ANTHROPIC_API_KEY")

    target_date = sys.argv[1] if len(sys.argv) > 1 else today_tw()
    story_path = STORIES_DIR / f"{target_date}.json"
    if not story_path.exists():
        sys.exit(f"找不到故事檔案：{story_path}")

    with open(story_path, encoding="utf-8") as f:
        story = json.load(f)

    full_text = "\n".join(f"{l['role']}: {l['text']}" for l in story["lines"])

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"故事標題：{story['title']}\n主題：{story.get('theme','')}\n\n{full_text}"}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    metadata = json.loads(raw)

    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EPISODES_DIR / f"{target_date}_metadata.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"標題：{metadata['episode_title']}")
    print(f"簡介：{metadata['show_notes']}")
    print(f"封面 prompt：{metadata['cover_prompt']}")
    print(f"已存到：{out_path}")


if __name__ == "__main__":
    main()
