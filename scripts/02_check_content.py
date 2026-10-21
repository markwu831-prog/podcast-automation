#!/usr/bin/env python3
"""
Step 2: 內容複審 — 檢查故事是否適合學齡前兒童收聽。

讀取 01 產生的故事 JSON，請 AI 做第二次獨立審查（分離 persona，
不看自己剛剛寫的理由，只看最終文字），輸出通過/不通過 + 理由。
不通過則標記，不會自動進到下一步（等你人工看一次，這是刻意保留的把關）。
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

REVIEW_SYSTEM_PROMPT = """你是兒童內容安全審查員，專門審查給學齡前（3-6歲）兒童聽的故事。
請嚴格檢查以下面向，任何一項不符就判定不通過：
1. 沒有恐怖、暴力、血腥、死亡細節
2. 沒有悲傷或令人不安的結局
3. 沒有不適合兒童的性/成人內容
4. 沒有教導錯誤價值觀（說謊有好結果、霸凌被鼓勵等）
5. 語言難度適合5歲兒童理解
6. 沒有商業置入或品牌置入

請只輸出 JSON，格式：
{"approved": true/false, "concerns": ["問題1", "問題2"...], "summary": "一句話總評"}
若沒有問題，concerns 給空陣列。
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
        system=REVIEW_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"故事標題：{story['title']}\n\n{full_text}"}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    review = json.loads(raw)

    story["content_review"] = review
    with open(story_path, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    print(f"審查結果：{'✅ 通過' if review['approved'] else '❌ 不通過'}")
    print(f"總評：{review['summary']}")
    if review["concerns"]:
        print("疑慮：")
        for c in review["concerns"]:
            print(f"  - {c}")

    if not review["approved"]:
        print("\n⚠️ 未通過自動審查，請人工確認後再繼續下一步（不會自動往下跑）。")
        sys.exit(1)


if __name__ == "__main__":
    main()
