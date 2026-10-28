# 运动换算计算器 🧮

体育课和训练时随手要用的八种换算，一个文件全搞定，纯 Python 标准库、零依赖、离线可用。
成绩写法很宽容：`245`、`4:05`、`4'05"`、`4分05秒` 都认。

## 八个子命令

```bash
python pe_calculator.py pace 1000 4:05              # 配速 + 速度
python pe_calculator.py pace 1000 4:05 --predict    # 附带 100→5000 米成绩预测（里格尔公式）
python pe_calculator.py splits 1000 4:00 --lap 400  # 目标成绩 → 每圈分段配速表
python pe_calculator.py score 初一 男 1000米跑 4:10  # 按示例标准表查分对标
python pe_calculator.py calorie 跳绳 --weight 45 --minutes 20   # MET 法估算热量消耗
python pe_calculator.py heartrate 12 --rest 70      # 靶心率（给静息心率则用卡氏公式）
python pe_calculator.py stride --speed 12 --cadence 180         # 步频步幅速度互算
python pe_calculator.py bmi 142 38                  # BMI（成人参考）
python pe_calculator.py time 245                    # 秒 ↔ 分:秒
python run_tests.py                                 # 自检
```

## 使用场景

- **耐力跑教学**：定下 1000 米目标成绩，用 `splits` 打出每圈该跑多少秒，贴在操场边照着练节奏；
- **查分对标**：学生问"我 4 分 10 秒能得多少分"，`score` 按示例标准表插值给出分数和等级，
  比翻纸质标准表快得多；
- **成绩预测**：用最近一次 400 米成绩粗估 1000 米潜力（里格尔公式，跨度越大越粗略，只作参考）；
- **运动量估算**：跳绳 20 分钟消耗多少，`calorie` 按体重给 MET 法估算（个体差异约 ±20%）；
- **心率监控**：给出手表心率后对照靶心率区间判断强度；提供静息心率时用卡氏（心率储备）公式更贴合个体。

## 关于查分标准

`score` 用的 `data/standards_sample.json` 是依据公开框架**节选整理的示例标准表**
（五年级、初一），数值可能与最新官方文件有出入；正式评定请以官方最新标准为准，
替换该 JSON 即可更新，程序不用改。批量算全班成绩请用姊妹项目「体测成绩分析」。

## License

MIT
