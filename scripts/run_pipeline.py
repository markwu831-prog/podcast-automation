#!/usr/bin/env python3
"""
總控腳本：依序跑完 ①~⑤（故事生成 → 內容審查 → 配音 → 後製 → 標題簡介封面）。
不包含 ⑥上傳（這步是人工/半自動，故意不自動化）。

用法：
    python run_pipeline.py              # 處理今天的日期（台灣時間）
    python run_pipeline.py 2026-10-22   # 處理指定日期
    python run_pipeline.py --skip-llm   # 故事/審查/標題簡介已由 Claude 寫好，
                                        # 只做檢查 → 配音 → 後製（雲端排程用這個）

跑完後，output/episodes/<日期>.mp3 跟 <日期>_metadata.json
就是你每天要上傳到 Firstory 的兩樣東西。
"""
import subprocess
import sys
from tw_date import today_tw
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "01_generate_story.py",
    "02_check_content.py",
    "03_generate_audio.py",
    "04_assemble_episode.py",
    "05_generate_metadata.py",
]
# 雲端排程模式：①②⑤ 由排程裡的 Claude 直接寫，這裡只負責檢查格式、配音、後製
SKIP_LLM_STEPS = [
    "validate_episode.py",
    "03_generate_audio.py",
    "04_assemble_episode.py",
]


def main():
    args = sys.argv[1:]
    skip_llm = "--skip-llm" in args
    args = [a for a in args if a != "--skip-llm"]
    target_date = args[0] if args else today_tw()
    print(f"=== 開始產生 {target_date} 的 Podcast 集數 ===\n")

    for step in SKIP_LLM_STEPS if skip_llm else STEPS:
        print(f"\n--- 執行 {step} ---")
        # 01 不需要日期參數（永遠產生「今天」），其餘都吃日期參數
        cmd = [sys.executable, str(ROOT / step)]
        if step != "01_generate_story.py":
            cmd.append(target_date)

        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"\n❌ {step} 執行失敗或未通過審查，流程中止。")
            sys.exit(result.returncode)

    print(f"\n✅ 全部完成！請到 output/episodes/{target_date}.mp3 "
          f"跟 {target_date}_metadata.json 查看成品，準備上傳 Firstory。")


if __name__ == "__main__":
    main()
