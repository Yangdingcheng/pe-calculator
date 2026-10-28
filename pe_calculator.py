#!/usr/bin/env python3
"""运动换算计算器：体育课随手要用的八种换算。

子命令：
  pace       距离+用时 → 配速 / 速度，可附带多距离成绩预测（里格尔公式）
  splits     目标成绩 → 每圈/每段分段配速表（操场 400 米或自定义段长）
  score      按示例标准表给单项成绩打分（查分对标，正式请核对官方标准）
  calorie    按体重与时长估算运动热量消耗（MET 法）
  heartrate  靶心率区间（可选静息心率，用卡氏公式更贴合个体）
  stride     步频/步幅/速度 三者互算
  bmi        BMI 与成人参考等级（学生请用 score / 体测工具查分档）
  time       秒 ↔ 分:秒 格式互转

示例：
  python pe_calculator.py pace 1000 4:05
  python pe_calculator.py splits 1000 4:00 --lap 400
  python pe_calculator.py score 初一 男 1000米跑 4:10
  python pe_calculator.py calorie 跳绳 --weight 45 --minutes 20
"""

from __future__ import annotations

import argparse
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

MET_TABLE = {"健步走": 3.5, "慢跑": 7.0, "跑步": 9.8, "快跑": 11.5, "跳绳": 11.8,
             "游泳": 8.0, "骑行": 7.5, "篮球": 6.5, "足球": 7.0, "羽毛球": 5.5, "乒乓球": 4.0}


def parse_time(v) -> float:
    if v is None or str(v).strip() == "":
        raise ValueError("空成绩")
    s = str(v).strip().replace("：", ":")
    try:
        return float(s)
    except ValueError:
        pass
    m = re.match(r"^(?:(\d+)\s*[:'分])?\s*(\d+(?:\.\d+)?)\s*(?:\"|秒)?$", s)
    if m:
        return int(m.group(1) or 0) * 60 + float(m.group(2))
    raise ValueError(f"无法解析：{v}")


def fmt_time(seconds: float) -> str:
    seconds = round(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def riegel(t: float, d_from: float, d_to: float) -> float:
    return t * (d_to / d_from) ** 1.06


def cmd_pace(distance: float, time_str: str, predict: bool):
    t = parse_time(time_str)
    pace = t / (distance / 1000)
    speed = distance / t * 3.6
    print(f"{distance:g} 米用时 {fmt_time(t)}（{t:g} 秒）")
    print(f"  平均配速 {fmt_time(pace)} /公里 · 平均速度 {speed:.1f} km/h")
    if predict:
        print("  成绩预测（里格尔公式，跨度越大越粗略，仅供参考）：")
        for d in (100, 200, 400, 800, 1000, 1500, 3000, 5000):
            if d != distance:
                print(f"    {d} 米 ≈ {fmt_time(riegel(t, distance, d))}")


def compute_splits(distance: float, total_s: float, lap: float) -> list[tuple[float, float, float]]:
    """返回 [(段终点距离， 本段用时， 累计用时)]，匀速模型。"""
    per_m = total_s / distance
    out = []
    done = 0.0
    while done < distance - 1e-9:
        seg = min(lap, distance - done)
        done += seg
        out.append((done, seg * per_m, done * per_m))
    return out


def cmd_splits(distance: float, time_str: str, lap: float):
    t = parse_time(time_str)
    print(f"目标：{distance:g} 米跑进 {fmt_time(t)}（匀速分段，段长 {lap:g} 米）")
    for end, seg_t, cum_t in compute_splits(distance, t, lap):
        print(f"  到 {end:g} 米：本段 {fmt_time(seg_t)} · 累计 {fmt_time(cum_t)}")
    print("  提示：实战常用负分割（后程略快），把每段目标再压 1–2 秒练节奏。")


def _score_points(breakpoints: list, value: float) -> float:
    pts = sorted(([float(p), float(s)] for p, s in breakpoints), key=lambda x: x[0])
    def interp(a, b, v):
        return b[1] if b[0] == a[0] else a[1] + (v - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
    if value <= pts[0][0]:
        return pts[0][1] if pts[0][1] >= pts[-1][1] else interp(pts[0], pts[1], value)
    if value >= pts[-1][0]:
        return pts[-1][1] if pts[-1][1] >= pts[0][1] else max(0.0, interp(pts[-2], pts[-1], value))
    for a, b in zip(pts, pts[1:]):
        if a[0] <= value <= b[0]:
            return interp(a, b, value)
    return pts[-1][1]


def cmd_score(grade: str, gender: str, event: str, value_str: str):
    path = os.path.join(BASE, "data", "standards_sample.json")
    std = json.load(open(path, encoding="utf-8"))
    table = (std.get(grade) or {}).get(gender) or {}
    spec = table.get(event)
    if not isinstance(spec, list):
        have = [k for k, v in table.items() if isinstance(v, list)]
        print(f"示例标准表暂无 {grade}/{gender}/{event}；该组别可查：{'、'.join(have)}")
        print("（标准表为节选示例，正式使用请核对官方文件后替换 data/standards_sample.json）")
        return
    val = parse_time(value_str)
    score = max(0.0, min(100.0, _score_points(spec, val)))
    level = "优秀" if score >= 90 else "良好" if score >= 80 else "及格" if score >= 60 else "不及格"
    print(f"{grade} {gender} {event} 成绩 {value_str} → 约 {score:.0f} 分（{level}）")
    print("（按仓库内示例标准表插值计算，正式评定请以官方最新标准为准）")


def cmd_calorie(activity: str, weight: float, minutes: float):
    met = MET_TABLE.get(activity)
    if met is None:
        print(f"暂不支持「{activity}」，可选：{'、'.join(MET_TABLE)}")
        return
    kcal = met * weight * minutes / 60
    print(f"{activity}（MET {met}）· 体重 {weight:g} kg · {minutes:g} 分钟 → 约消耗 {kcal:.0f} 千卡")
    print("  MET 法为人群平均估算，个体差异约 ±20%。")


def cmd_heartrate(age: int, rest: int = 0):
    hrmax = 220 - age
    if rest:
        hrr = hrmax - rest
        lo, mid, hi = rest + hrr * 0.6, rest + hrr * 0.7, rest + hrr * 0.8
        print(f"年龄 {age} · 静息心率 {rest} → 卡氏公式靶心率：有氧区 {lo:.0f}–{hi:.0f} 次/分（中点 {mid:.0f}）")
    else:
        print(f"年龄 {age} → 最大心率约 {hrmax}；有氧区（60%–80%）{round(hrmax * 0.6)}–{round(hrmax * 0.8)} 次/分；热身区 {round(hrmax * 0.5)}–{round(hrmax * 0.6)}")
    print("  均为估算公式，课堂以学生主观感受与表现为准。")


def cmd_stride(speed_kmh: float = 0, cadence: float = 0, stride_m: float = 0):
    if speed_kmh and cadence:
        stride = speed_kmh * 1000 / 60 / cadence
        print(f"速度 {speed_kmh} km/h · 步频 {cadence:g} 步/分 → 步幅约 {stride:.2f} 米")
    elif stride_m and cadence:
        speed = stride_m * cadence * 60 / 1000
        print(f"步幅 {stride_m} 米 · 步频 {cadence:g} 步/分 → 速度约 {speed:.1f} km/h（配速 {fmt_time(3600 / speed)}/公里）")
    elif speed_kmh and stride_m:
        cad = speed_kmh * 1000 / 60 / stride_m
        print(f"速度 {speed_kmh} km/h · 步幅 {stride_m} 米 → 步频约 {cad:.0f} 步/分")
    else:
        print("需要任意两个量：--speed（km/h）/ --cadence（步/分）/ --stride（米）")


def cmd_bmi(height_cm: float, weight_kg: float):
    bmi = weight_kg / (height_cm / 100) ** 2
    band = "偏低" if bmi < 18.5 else "正常" if bmi < 24 else "超重" if bmi < 28 else "肥胖"
    print(f"身高 {height_cm:g}cm · 体重 {weight_kg:g}kg → BMI = {bmi:.1f}（成人参考：{band}）")
    print("  学生体测分档请用 score 子命令或体测分析工具按年级性别查标准表。")


def cmd_time(value: str):
    t = parse_time(value)
    print(f"{value} = {t:g} 秒 = {fmt_time(t)}")


def main():
    ap = argparse.ArgumentParser(description="运动换算计算器")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pace"); p.add_argument("distance", type=float); p.add_argument("time"); p.add_argument("--predict", action="store_true")
    p = sub.add_parser("splits"); p.add_argument("distance", type=float); p.add_argument("time"); p.add_argument("--lap", type=float, default=400)
    p = sub.add_parser("score"); p.add_argument("grade"); p.add_argument("gender"); p.add_argument("event"); p.add_argument("value")
    p = sub.add_parser("calorie"); p.add_argument("activity"); p.add_argument("--weight", type=float, required=True); p.add_argument("--minutes", type=float, required=True)
    p = sub.add_parser("heartrate"); p.add_argument("age", type=int); p.add_argument("--rest", type=int, default=0)
    p = sub.add_parser("stride"); p.add_argument("--speed", type=float, default=0); p.add_argument("--cadence", type=float, default=0); p.add_argument("--stride", type=float, dest="stride_m", default=0)
    p = sub.add_parser("bmi"); p.add_argument("height_cm", type=float); p.add_argument("weight_kg", type=float)
    p = sub.add_parser("time"); p.add_argument("value")
    args = ap.parse_args()
    if args.cmd == "pace":
        cmd_pace(args.distance, args.time, args.predict)
    elif args.cmd == "splits":
        cmd_splits(args.distance, args.time, args.lap)
    elif args.cmd == "score":
        cmd_score(args.grade, args.gender, args.event, args.value)
    elif args.cmd == "calorie":
        cmd_calorie(args.activity, args.weight, args.minutes)
    elif args.cmd == "heartrate":
        cmd_heartrate(args.age, args.rest)
    elif args.cmd == "stride":
        cmd_stride(args.speed, args.cadence, args.stride_m)
    elif args.cmd == "bmi":
        cmd_bmi(args.height_cm, args.weight_kg)
    elif args.cmd == "time":
        cmd_time(args.value)


if __name__ == "__main__":
    main()
