#import "template.typ": *
#let ms = json("manuscript.json")
#let comments = json("comments.json")
#let sigs = json("signatures.json")

#part-opener("附录", "")

// ---- 签名墙 ----
#heading(level: 2, "签名墙")
#piece-meta("2005 年到 2025 年", "签名设计")
#par[这些签名是为同事、朋友、医生和素不相识的网友设计的。设计的原则写在第四部《初尝签名设计的乐趣》里。]
#v(0.5em)
#align(center, block(image("/book/images/crops/signature-wulujia.jpg", width: 60mm)))
#align(center, text(size: 10pt, fill: luma(110))[吴鲁加，2009 年])
#v(1em)
#grid(columns: (1fr, 1fr, 1fr), gutter: 3mm, align: center + horizon,
  ..sigs.map(s => image(s.src, width: 100%)))

// ---- 留言选 ----
#pagebreak(weak: true)
#heading(level: 2, "留言选")
#piece-meta("2004 年到 2020 年", "")
#par[博客二十年收到 589 条留言。这里选了 59 条，按时间排。留言者用当时的网名；已知真名的注在括号里。]
#v(0.8em)
#set par(first-line-indent: 0em)
#for c in comments {
  block(above: 1.3em, below: 0.4em, breakable: false, {
    text(size: 10pt, fill: luma(110), c.name + "　·　" + c.date + "　·　《" + c.post + "》")
    linebreak()
    set text(size: 12pt)
    set par(leading: 0.75em)
    c.text.split("\n").join(linebreak())
  })
}

// ---- 博客大事记 ----
#pagebreak(weak: true)
#heading(level: 2, "博客大事记")
#piece-meta("", "")
#table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 6pt, y: 5pt),
  align: (right, left),
  [2004 年 10 月], [儿子建站《五福在家 自得其乐》。第一条留言来自儿子：“老爸，在这儿做网站的，这个人和你同年哦。”],
  [2005 年 7 月], [把几十年的诗、字、标志、签名设计整批放上网，其中有些是四五十年前的东西。],
  [2006 年 12 月], [写《愿这可爱的自留地伴我同行，永远！》。开设《儿女小抽屉》。],
  [2009 年 12 月], [参加第二届全国中老年博客大赛，投票排名第九，获“十佳博客提名奖”，福建省唯一获奖者。],
  [2010 年 11 月], [在福建省地矿局康乐大讲堂讲《网络和阅读让我快乐充实》。此时网站有约 400 篇，i170 浏览量超过 180 万人次。],
  [2011 年 5 月], [搬到 WordPress。把旧站的留言一条条贴回新站。],
  [2013 年 4 月 18 日], [发第一条朋友圈。第一个微信好友是儿子。这一年发了 523 条。],
  [2015 年到 2017 年], [网站停更，文字都在朋友圈。],
  [2018 年 7 月到 11 月], [把 2014 年到 2017 年的 170 条朋友圈补录进博客。],
  [2024 年], [儿子把网站迁到 wuwufu.com 静态站。9 月赴新加坡。],
  [2025 年 9 月], [用 AI 让老照片动起来。这是本书选的最后一篇。],
)

// ---- 编后记 ----
#pagebreak(weak: true)
#heading(level: 2, "编后记")
#piece-meta("", "")
#include "afterword.typ"
