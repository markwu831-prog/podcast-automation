#!/usr/bin/env python3
"""
Step 1: Generate today's children's story script (dialogue format).

Produces a JSON file with alternating narrator (女) / listener (男) lines,
ready to feed into the TTS step.

Requires: ANTHROPIC_API_KEY environment variable.
"""
import json
import os
import sys
from tw_date import now_tw_iso, today_tw
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.exit("請先安裝套件: pip install anthropic")

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "podcast.json"
OUTPUT_DIR = ROOT / "output" / "stories"

SYSTEM_PROMPT = """你是一位專門為學齡前兒童創作睡前故事的作家兼廣播腳本編劇。
你要寫出完全原創的故事（不取材自任何特定出版品或既有角色），
風格溫馨、教育寓意明確、適合睡前聆聽，沒有恐怖、暴力或悲傷結局。

故事要寫成雙人對話廣播腳本格式：
- 「女」：說故事姐姐，溫柔親切，負責主要敘事
- 「男」：5歲小男孩聽眾，天真活潑，會在故事進行中適時插話——提問、驚訝、複誦重點、說出感想

要求：
1. 全文繁體中文
2. 總字數（含雙方對話）落在 1500-1700 字之間（約 5 分鐘音檔）
3. 故事要有清楚的起承轉合與明確寓意（友誼、勇氣、分享、誠實、禮貌等品格教育方向皆可，每天自由發揮不重複）
4. 男孩的插話要自然、符合5歲小孩的語氣，不要太書面或太成熟
5. 結尾女生要用一兩句話點出故事寓意，男孩簡短回應做結

輸出格式為 JSON（不要有其他文字），結構如下：
{
  "title": "故事標題",
  "theme": "本篇寓意主題（如：分享、誠實...）",
  "lines": [
    {"role": "narrator", "text": "..."},
    {"role": "listener", "text": "..."},
    ...
  ]
}
"""


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def generate_story(client: "anthropic.Anthropic", config: dict) -> dict:
    cfg = config["story_direction"]
    word_lo, word_hi = config["show"]["target_word_count"]

    user_prompt = (
        f"今天的日期是 {today_tw()}。"
        f"請創作一篇全新的原創兒童故事廣播腳本，字數 {word_lo}-{word_hi} 字之間，"
        f"語氣：{cfg['tone']}。避免內容：{'、'.join(cfg['avoid'])}。"
        "主題請自由發揮，但不要跟你過去常見的老套題材重複（例如不要每次都用龜兔賽跑類的老故事），"
        "盡量每天呈現不同的情境與角色設定。"
    )

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = message.content[0].text
    # 容錯：若模型外包了 ```json 區塊
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    return json.loads(raw_text)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("請先設定環境變數 ANTHROPIC_API_KEY")

    config = load_config()
    client = anthropic.Anthropic(api_key=api_key)

    print("正在生成今天的故事...")
    story = generate_story(client, config)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{today_tw()}.json"
    story["generated_at"] = now_tw_iso()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    total_chars = sum(len(l["text"]) for l in story["lines"])
    print(f"完成：{story['title']}（主題：{story.get('theme', '未標註')}）")
    print(f"對話行數：{len(story['lines'])}，總字數約：{total_chars}")
    print(f"已存到：{out_path}")


if __name__ == "__main__":
    main()
