#!/usr/bin/env python3
"""
列出要存到「每日集數」網頁 src/ 底下的專案檔案，輸出成 Artifact 工具 `files` 參數用的 JSON。

還沒接 GitHub 時，程式碼跟每天的故事/標題簡介/紀錄都存在網頁的 src/ 裡，
排程每天從那裡還原、做完再存回去（見 DAILY_RUN.md）。
一律用 text/plain 發布，避免 .py / .html 被當成網頁或被拒收。

用法：
    python source_manifest.py > /tmp/files.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INCLUDE = [
    "README.md",
    "DAILY_RUN.md",
    "requirements.txt",
    "config/*.json",
    "scripts/*.py",
    "site/*.html",
    "output/stories/*.json",
    "output/episodes/*.json",
]


def main():
    files = {}
    for pattern in INCLUDE:
        for path in sorted(ROOT.glob(pattern)):
            rel = path.relative_to(ROOT).as_posix()
            files[f"src/{rel}"] = {"from": str(path), "contentType": "text/plain"}
    print(json.dumps(files, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
