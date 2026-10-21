"""
共用：取得台灣時間的「今天」日期字串。

雲端排程的機器時區是 UTC，台灣早上 6 點時 UTC 還是前一天，
所以日期一律用 Asia/Taipei 算，避免檔名跟集數日期錯開。
"""
from datetime import datetime
from zoneinfo import ZoneInfo

TW = ZoneInfo("Asia/Taipei")


def today_tw() -> str:
    return datetime.now(TW).date().isoformat()


def now_tw_iso() -> str:
    return datetime.now(TW).isoformat(timespec="seconds")
