#!/usr/bin/env python3
"""运动换算计算器测试：python run_tests.py"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from pe_calculator import compute_splits, fmt_time, parse_time, riegel, _score_points

PASS = []
def check(name, cond):
    PASS.append((name, bool(cond)))
    print(("✅" if cond else "❌"), name)
    assert cond, name

check("时间解析", parse_time("4分05秒") == 245 and parse_time("245") == 245)
check("时间格式", fmt_time(245) == "4:05" and fmt_time(65) == "1:05")
splits = compute_splits(1000, 240, 400)
check("分段段数", len(splits) == 3 and splits[-1][0] == 1000)
check("分段累计=总时", abs(splits[-1][2] - 240) < 0.01)
check("分段末段短", splits[-1][1] < splits[0][1])
check("里格尔单调", riegel(245, 1000, 2000) > 490 and riegel(60, 400, 100) < 60)

import json
std = json.load(open(os.path.join(BASE, "data", "standards_sample.json"), encoding="utf-8"))
bp = std["初一"]["男"]["1000米跑"]
check("查分满分点", _score_points(bp, 235) == 100)
bp50 = std["五年级"]["女"]["50米跑"]
check("查分插值", abs(_score_points(bp50, 8.55) - 95) < 0.01)

def cli(*a):
    r = subprocess.run([sys.executable, os.path.join(BASE, "pe_calculator.py"), *a],
                       capture_output=True, text=True)
    return r
r = cli("pace", "1000", "4:05")
check("CLI-配速", r.returncode == 0 and "14.7" in r.stdout)
r = cli("splits", "1000", "4:00")
check("CLI-分段", r.returncode == 0 and "累计" in r.stdout)
r = cli("score", "初一", "男", "1000米跑", "3:55")
check("CLI-查分满分", r.returncode == 0 and "100 分" in r.stdout)
r = cli("calorie", "跳绳", "--weight", "45", "--minutes", "20")
check("CLI-卡路里", r.returncode == 0 and "177" in r.stdout)  # 11.8*45*20/60=177
r = cli("heartrate", "12", "--rest", "70")
check("CLI-卡氏心率", r.returncode == 0 and "卡氏" in r.stdout)
r = cli("stride", "--speed", "12", "--cadence", "180")
check("CLI-步幅", r.returncode == 0 and "1.11" in r.stdout)

print(f"\n全部 {len(PASS)} 项测试通过 ✅" if all(c for _, c in PASS) else "\n存在失败 ❌")
