#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词表整理生成器（M1 一次性执行卡，plan/05 §3）。

从公开词表快照（Dete.txt / banned-words.md，经 api.github.com 获取）整理出
4 类词表 JSON，逐条挂锚点（literal/variant）、定风险、写建议，只收 verified。

纪律：
- 本脚本是词表的**生成器冻结件**：词表内容以代码形式可复核、可重生成；
- literal 条目的词面必须逐字见于条款正文（--check 时实测断言，违者退出 1）；
- variant 条目必须带 note 说明语义类属判定依据；
- 否定易词（如"安全""最"单字、"无副作用"整词按语境而定）不进规则包，留候选台账。

用法：py -X utf8 tools/gen_wordlists.py [--check]
  默认写 references/wordlists/*.json；--check 只重生成到内存并核对库内位级一致。
"""

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = _REPO_ROOT / "references" / "wordlists"

SRC_NOTE = ("非官方整理（来源：es3344520/advertising-limit-words 的 Dete.txt 与 "
            "dx2020z/ad-redline-guardian 的 references/banned-words.md 公开快照，"
            "2026-10-15 经 api.github.com 获取），法条原文为准")

S_ABS_LIT = "删除该表述，或改为可核实的客观事实描述"
S_ABS_VAR = "删除绝对化表述，改为可核实的客观描述（如具体数据并附出处）"
S_MED = "删除医疗功效表述；普通商品改为客观成分/质地描述，医疗商品须持证并按审查证明发布"
S_HF = "删除功效/疾病预防治疗表述；保健食品须显著标明“本品不能代替药物”"
S_HF_SAFETY = "删除安全性断言，改为可核实成分/检测描述"
S_IND = "删除该表述，改为可验证的具体事实（附出处或证明文件）"

ABS = "绝对化用语"
MED = "医疗违禁"
HF = "保健食品违禁"
IND = "行业违禁"

# (word, risk, doc, clause, basis, suggestion, note)
# note 仅 variant 必填；literal 可省
ENTRIES = {
    "absolute-terms.json": (ABS, [
        ("国家级", "high", "advertising-law", "第九条", "literal", S_ABS_LIT, None),
        ("最高级", "high", "advertising-law", "第九条", "literal", S_ABS_LIT, None),
        ("最佳", "high", "advertising-law", "第九条", "literal", S_ABS_LIT, None),
        ("最好", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "“最+褒义形容词”绝对化断言，属第九条（三）“等用语”语义类属"),
        ("最优", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "“最+褒义形容词”绝对化断言"),
        ("最优秀", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "“最+褒义形容词”绝对化断言"),
        ("最强", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "“最+程度断言”绝对化断言"),
        ("最先进", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "“最+程度断言”绝对化断言"),
        ("最高端", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "“最+程度断言”绝对化断言"),
        ("最低价", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "价格类绝对化断言，无法逐域核实"),
        ("最便宜", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "价格类绝对化断言"),
        ("全网最低", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "范围+绝对化价格断言，无法逐域核实"),
        ("全网最优", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "范围+绝对化断言"),
        ("第一", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性序位断言，无据即绝对化"),
        ("NO.1", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "“第一”的西文变体，排他性序位断言"),
        ("TOP.1", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "“第一”的西文变体"),
        ("销量第一", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性序位断言，须附统计出处"),
        ("全网第一", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性序位断言"),
        ("全国第一", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性序位断言"),
        ("行业第一", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性序位断言"),
        ("中国第一", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性序位断言"),
        ("第一品牌", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性序位断言"),
        ("销量冠军", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "序位断言，须附统计出处"),
        ("顶级", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "级域程度断言，属绝对化变体"),
        ("顶尖", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "程度断言，属绝对化变体"),
        ("极品", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "品级绝对化断言"),
        ("绝对", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "绝对化承诺词面（如“绝对有效”）"),
        ("独一无二", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性断言"),
        ("绝无仅有", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性断言"),
        ("史无前例", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性断言"),
        ("空前绝后", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性断言"),
        ("世界级", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "与“国家级”同构的级域断言"),
        ("宇宙级", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "与“国家级”同构的级域断言"),
        ("全球级", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "与“国家级”同构的级域断言"),
        ("万能", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "全效断言"),
        ("全能", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "全效断言"),
        ("终极", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "程度断言"),
        ("极致", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "程度断言，营销语境常用，风险略低于明文列举"),
        ("首选", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性推荐断言，语境依赖"),
        ("唯一", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性断言，有真实排他性证明时属语境豁免候选"),
        ("仅此一家", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "排他性断言"),
        ("首个", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "序位断言，须附首例出处"),
        ("首家", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "序位断言"),
        ("首款", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "序位断言"),
        ("世界领先", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "领先断言，须附出处"),
        ("行业领先", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "领先断言，须附出处"),
        ("全球首发", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "首发断言，须附出处"),
        ("全网首发", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "首发断言"),
        ("领先上市", "medium", "advertising-law", "第九条", "variant", S_ABS_VAR, "序位断言"),
        ("100%有效", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "全称效果断言，无法逐例证实"),
    ]),
    "medical.json": (MED, [
        ("治愈", "high", "medical-ad-measures", "第七条", "literal", S_MED, None),
        ("疗效", "high", "medical-ad-measures", "第七条", "literal", S_MED, None),
        ("保证治愈", "high", "medical-ad-measures", "第七条", "literal", S_MED, None),
        ("治疗", "high", "advertising-law", "第十七条", "literal", S_MED, None),
        ("根治", "high", "advertising-law", "第十七条", "variant", S_MED, "“治愈”的同义强化变体，属第十七条医疗用语语义类属"),
        ("痊愈", "high", "advertising-law", "第十七条", "variant", S_MED, "“治愈”同义变体"),
        ("药到病除", "high", "advertising-law", "第十七条", "variant", S_MED, "功效保证断言，属第十七条医疗用语"),
        ("包治百病", "high", "advertising-law", "第十七条", "variant", S_MED, "功效保证断言"),
        ("三天即愈", "high", "advertising-law", "第十七条", "variant", S_MED, "限时治愈保证"),
        ("彻底康复", "high", "advertising-law", "第十七条", "variant", S_MED, "治愈保证变体"),
        ("消炎", "high", "advertising-law", "第十七条", "variant", S_MED, "医疗用语，易与药品混淆"),
        ("杀菌", "medium", "advertising-law", "第十七条", "variant", S_MED, "医疗用语变体；消毒产品有资质时属语境豁免候选"),
        ("抗菌", "medium", "advertising-law", "第十七条", "variant", S_MED, "医疗用语变体；有资质时属语境豁免候选"),
        ("疗效显著", "high", "medical-ad-measures", "第七条", "variant", S_MED, "“宣传治愈率、有效率等诊疗效果”类断言变体"),
    ]),
    "health-food.json": (HF, [
        ("治疗功能", "high", "advertising-law", "第十八条", "literal", S_HF, None),
        ("疾病预防", "high", "advertising-law", "第十八条", "literal", S_HF, None),
        ("抗癌", "high", "advertising-law", "第十八条", "variant", S_HF, "疾病预防/治疗功能表述，属第十八条（二）语义类属"),
        ("防癌", "high", "advertising-law", "第十八条", "variant", S_HF, "疾病预防功能表述"),
        ("降三高", "high", "advertising-law", "第十八条", "variant", S_HF, "疾病治疗功能表述"),
        ("降血糖", "high", "advertising-law", "第十八条", "variant", S_HF, "疾病治疗功能表述"),
        ("降血压", "high", "advertising-law", "第十八条", "variant", S_HF, "疾病治疗功能表述"),
        ("无副作用", "high", "advertising-law", "第十八条", "variant", S_HF_SAFETY, "安全性断言，属第十八条（一）“表示功效、安全性的断言或者保证”"),
        ("无任何副作用", "high", "advertising-law", "第十八条", "variant", S_HF_SAFETY, "安全性断言"),
        ("丰胸", "high", "advertising-law", "第十八条", "variant", S_HF, "高风险功效词"),
        ("壮阳", "high", "advertising-law", "第十八条", "variant", S_HF, "高风险功效词"),
        ("增高", "high", "advertising-law", "第十八条", "variant", S_HF, "高风险功效词"),
        ("减肥", "medium", "advertising-law", "第十八条", "variant", S_HF, "普通食品宣称减肥属功效断言；语境依赖（保健食品需注册证）"),
        ("瘦身", "medium", "advertising-law", "第十八条", "variant", S_HF, "功效断言变体"),
        ("燃脂", "medium", "advertising-law", "第十八条", "variant", S_HF, "功效断言变体"),
        ("溶脂", "medium", "advertising-law", "第十八条", "variant", S_HF, "功效断言变体"),
        ("美白", "medium", "advertising-law", "第十八条", "variant", S_HF, "特证化妆品功效词，无注册证即违规（语境依赖）"),
        ("祛斑", "medium", "advertising-law", "第十八条", "variant", S_HF, "特证化妆品功效词"),
        ("祛痘", "medium", "advertising-law", "第十八条", "variant", S_HF, "特证化妆品功效词"),
        ("排毒", "medium", "advertising-law", "第十八条", "variant", S_HF, "夸大语境下的功效断言"),
        ("纯天然", "medium", "advertising-law", "第二十八条", "variant", S_HF_SAFETY, "无法证实的绝对化安全断言，属第二十八条（二）允诺与实际不符"),
        ("零添加", "medium", "advertising-law", "第二十八条", "variant", S_HF_SAFETY, "安全断言变体，需可证实"),
    ]),
    "industry.json": (IND, [
        ("保本", "high", "advertising-law", "第二十五条", "literal", S_IND, None),
        ("保收益", "high", "advertising-law", "第二十五条", "literal", S_IND, None),
        ("无风险", "high", "advertising-law", "第二十五条", "literal", S_IND, None),
        ("稳赚", "high", "advertising-law", "第二十五条", "variant", S_IND, "保证性收益承诺，属第二十五条（一）语义类属"),
        ("零风险", "high", "advertising-law", "第二十五条", "variant", S_IND, "“无风险”变体"),
        ("躺赚", "high", "advertising-law", "第二十五条", "variant", S_IND, "误导性收益承诺"),
        ("包回本", "high", "advertising-law", "第二十五条", "variant", S_IND, "保证性承诺"),
        ("稳赢", "high", "advertising-law", "第二十五条", "variant", S_IND, "保证性承诺"),
        ("必涨", "high", "advertising-law", "第二十五条", "variant", S_IND, "保证性承诺"),
        ("月入过万", "high", "advertising-law", "第二十五条", "variant", S_IND, "收益承诺（作为效果承诺时），语境依赖"),
        ("日入千元", "high", "advertising-law", "第二十五条", "variant", S_IND, "收益承诺，语境依赖"),
        ("驰名商标", "high", "advertising-law", "第九条", "variant", S_IND, "《广告法》第十四条禁止用于宣传；归入权威背书类（第九条（二）国家信用类属）"),
        ("国家机关推荐", "high", "advertising-law", "第九条", "variant", S_IND, "冒用国家机关名义，属第九条（二）"),
        ("国家机关专供", "high", "advertising-law", "第九条", "variant", S_IND, "冒用国家机关名义"),
        ("政府指定", "high", "advertising-law", "第九条", "variant", S_IND, "冒用国家机关名义"),
        ("质检推荐", "high", "advertising-law", "第九条", "variant", S_IND, "冒用国家机关名义"),
        ("国家免检", "high", "advertising-law", "第九条", "variant", S_IND, "冒用国家质量信用（免检制度已废止）"),
        ("质量免检", "high", "advertising-law", "第九条", "variant", S_IND, "冒用国家质量信用"),
        ("免抽检", "high", "advertising-law", "第九条", "variant", S_IND, "冒用国家质量信用"),
        ("专供", "medium", "advertising-law", "第九条", "variant", S_IND, "“专供国家机关”类断言，需语境判断"),
        ("特供", "medium", "advertising-law", "第九条", "variant", S_IND, "同“专供”"),
        ("央视上榜", "high", "advertising-law", "第二十八条", "variant", S_IND, "无法验证的背书引用，属第二十八条（三）虚构引用语"),
        ("CCTV推荐", "high", "advertising-law", "第二十八条", "variant", S_IND, "无法验证的背书引用"),
        ("专家推荐", "medium", "advertising-law", "第二十八条", "variant", S_IND, "需真实可查证明文件，否则涉虚假广告"),
        ("院士推荐", "high", "advertising-law", "第二十八条", "variant", S_IND, "需真实可查证明文件"),
        ("仅此一天", "medium", "advertising-law", "第二十八条", "variant", S_IND, "虚构紧迫感（无真实活动时），属第二十八条（二）允诺不符"),
        ("最后一天", "medium", "advertising-law", "第二十八条", "variant", S_IND, "虚构紧迫感"),
        ("错过再等一年", "medium", "advertising-law", "第二十八条", "variant", S_IND, "虚构紧迫感"),
        ("秒杀全行业", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "贬低竞品+绝对化断言"),
        ("吊打同行", "high", "advertising-law", "第九条", "variant", S_ABS_VAR, "贬低竞品+绝对化断言"),
        ("假一赔万", "medium", "advertising-law", "第二十八条", "variant", S_IND, "无兑现机制即虚假允诺"),
        ("假一罚十", "medium", "advertising-law", "第二十八条", "variant", S_IND, "无兑现机制即虚假允诺"),
        ("点击领奖", "medium", "advertising-law", "第二十八条", "variant", S_IND, "虚假承诺类，无真实活动即误导"),
        ("全民免单", "medium", "advertising-law", "第二十八条", "variant", S_IND, "虚假承诺类"),
        ("恭喜获奖", "medium", "advertising-law", "第二十八条", "variant", S_IND, "虚假承诺类"),
        ("开光", "medium", "advertising-law", "第九条", "variant", S_IND, "迷信类宣传，属第九条（八）迷信内容语义类属（平台普遍禁宣）"),
        ("辟邪", "medium", "advertising-law", "第九条", "variant", S_IND, "迷信类宣传"),
        ("镇宅", "medium", "advertising-law", "第九条", "variant", S_IND, "迷信类宣传"),
        ("招财进宝", "medium", "advertising-law", "第九条", "variant", S_IND, "迷信类宣传"),
        ("转运", "medium", "advertising-law", "第九条", "variant", S_IND, "迷信类宣传"),
        ("开运", "medium", "advertising-law", "第九条", "variant", S_IND, "迷信类宣传"),
        ("灵验", "medium", "advertising-law", "第九条", "variant", S_IND, "迷信类宣传"),
        ("风水改运", "medium", "advertising-law", "第九条", "variant", S_IND, "迷信类宣传"),
        ("包过", "high", "advertising-law", "第二十八条", "variant", S_IND, "效果保证断言（教育类无据即虚假允诺）"),
        ("保过", "high", "advertising-law", "第二十八条", "variant", S_IND, "效果保证断言"),
        ("一次通关", "high", "advertising-law", "第二十八条", "variant", S_IND, "效果保证断言"),
        ("一次通过", "high", "advertising-law", "第二十八条", "variant", S_IND, "效果保证断言"),
    ]),
}


def build_payloads():
    payloads = {}
    for fname, (cat, items) in ENTRIES.items():
        entries = []
        for word, risk, doc, clause, basis, sug, note in items:
            anchor = {"doc": doc, "clause": clause, "basis": basis}
            if basis == "variant":
                if not note:
                    raise ValueError("variant 条目缺 note：%s" % word)
                anchor["note"] = note
            entries.append({
                "word": word,
                "category": cat,
                "risk": risk,
                "anchor": anchor,
                "source": {"type": "non_official", "ref": "公开整理词表（来源快照）", "note": SRC_NOTE},
                "status": "verified",
                "suggestion": sug,
            })
        entries.sort(key=lambda e: e["word"])
        payloads[fname] = {"category": cat, "entries": entries}
    return payloads


def render(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main(argv=None):
    check_only = "--check" in (argv or sys.argv[1:])
    payloads = build_payloads()
    ok = True
    for fname, payload in payloads.items():
        data = render(payload).encode("utf-8")
        path = OUT / fname
        if check_only:
            if not path.is_file() or path.read_bytes() != data:
                print("位级不一致：%s" % fname, file=sys.stderr)
                ok = False
        else:
            path.write_bytes(data)
            print("written %s %d 词条" % (fname, len(payload["entries"])))
    if not ok:
        return 1
    print("WORDLISTS_OK" if check_only else "WORDLISTS_WRITTEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
