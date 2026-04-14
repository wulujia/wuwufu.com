#!/usr/bin/env python3
"""
批量把 uncategorized 文章分配到合适的分类。
"""

import re
from pathlib import Path

POSTS = Path(__file__).parent.parent / "content" / "posts"

assignments = {
    # 亦思亦录（33篇）
    "2008年世态汉字.md": "亦思亦录",
    "一个纪念品的构想.md": "亦思亦录",
    "云顶酒店.md": "亦思亦录",
    "五福临门-恭贺新春.md": "亦思亦录",
    "五福在家.md": "亦思亦录",
    "五福在家-2.md": "亦思亦录",
    "会动的鸟叫图.md": "亦思亦录",
    "光标在标志上游走.md": "亦思亦录",
    "到《小山丛竹》走走.md": "亦思亦录",
    "到东湖公园走走.md": "亦思亦录",
    "匆匆台湾自由行-2.md": "亦思亦录",
    "北京街头随拍：王府井.md": "亦思亦录",
    "印尼泗水、巴厘岛之行.md": "亦思亦录",
    "回顾.md": "亦思亦录",
    "回顾87年人生旅途的主要站点.md": "亦思亦录",
    "我见到放心石了.md": "亦思亦录",
    "新加坡樟宜机场景观《雨滴》.md": "亦思亦录",
    "新加坡滨海湾花园.md": "亦思亦录",
    "新年快乐.md": "亦思亦录",
    "早安-脸谱视频.md": "亦思亦录",
    "早安，您好！-鸟儿你唱吧！.md": "亦思亦录",
    "机场1号航站楼及精彩回味.md": "亦思亦录",
    "植物园、民居及其它.md": "亦思亦录",
    "用ai豆包让照片动起来.md": "亦思亦录",
    "回眸温文尔雅的青春.md": "亦思亦录",
    "祝所有妈妈母亲节快乐！.md": "亦思亦录",
    "祝贺党的生日.md": "亦思亦录",
    "简单动作.md": "亦思亦录",
    "蝉鸣.md": "亦思亦录",
    "赴新加坡第一天.md": "亦思亦录",
    "逛乌节路随拍.md": "亦思亦录",
    "钢光纪念相册.md": "亦思亦录",
    "青蛙大战.md": "亦思亦录",
    "鱼尾狮国家博物馆.md": "亦思亦录",

    # 儿女小抽屉（5）
    "外孙女小时候的画.md": "儿女小抽屉",
    "女儿的青春彩页.md": "儿女小抽屉",
    "小孙女学画画-2.md": "儿女小抽屉",
    "小孙子幼儿涂鸦.md": "儿女小抽屉",
    "浪花朵朵.md": "儿女小抽屉",

    # 差差书法（8）
    "五福在家（字）.md": "差差书法",
    "合德（对联）.md": "差差书法",
    "合德（对联2）.md": "差差书法",
    "早安-自画像等等.md": "差差书法",
    "早安您好（2）.md": "差差书法",
    "福通.md": "差差书法",
    "自己制作早安图片.md": "差差书法",
    "祖国万年青-2.md": "差差书法",

    # 业余涂画（4）
    "少年自画像.md": "业余涂画",
    "拼图11幅.md": "业余涂画",
    "永定山庄.md": "业余涂画",
    "说拼图.md": "业余涂画",

    # 签名设计（4）
    "元涵（商标）.md": "签名设计",
    "文璇茶庄（商标等）.md": "签名设计",
    "签名设计-肃真.md": "签名设计",
    "艺术签名-书写轨迹-2.md": "签名设计",

    # 我的诗（3）
    "《能吃会睡》等等.md": "我的诗",
    "中国茶道.md": "我的诗",
    "剃光头就是好！.md": "我的诗",

    # 慢慢变老（3）
    "我才86呢！.md": "慢慢变老",
    "弹指一瞬-六十二年.md": "慢慢变老",
    "年虽耄耋心未老.md": "慢慢变老",
}


def main():
    missing = []
    fixed = 0
    for filename, new_cat in assignments.items():
        path = POSTS / filename
        if not path.exists():
            missing.append(filename)
            continue

        text = path.read_text("utf-8")
        # 替换 categories block 中的 uncategorized
        # 保持多分类的情况（虽然这些都是单一 uncategorized，但稳妥起见）
        new_text = re.sub(
            r'(categories:\n(?:  - .*\n)*  - )uncategorized(\n)',
            rf'\1{new_cat}\2',
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        if new_text != text:
            path.write_text(new_text, "utf-8")
            fixed += 1
        else:
            print(f"  未修改: {filename}")

    print(f"已分类: {fixed} 篇")
    if missing:
        print(f"\n找不到 {len(missing)} 个文件:")
        for m in missing:
            print(f"  {m}")


if __name__ == "__main__":
    main()
