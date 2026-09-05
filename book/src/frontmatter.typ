// 卷首：序、自序、年表
#import "template.typ": *
#let ms = json("manuscript.json")

#heading(level: 2, "序")
#piece-meta("", "")
#include "preface.typ"

#pagebreak(weak: true)
#for p in ms.front {
  render-piece(p)
}

#pagebreak(weak: true)
#heading(level: 2, "年表")
#piece-meta("", "")
#set par(first-line-indent: 0em)
#table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 6pt, y: 5pt),
  align: (right, left),
  [1939], [生于福建平和县城关琯溪。祖籍永定县湖山坑头。],
  [1946 到 1951], [平和小溪小学。],
  [1952 到 1957], [福建省平和第一中学。高中班名“保尔班”。],
  [1957 到 1961], [厦门大学化学系。],
  [1961 到 1971], [福建省地质局中心实验室，福州。1965 年随单位迁三明。],
  [1970], [下放永安东坑子劳动一年。],
  [1971 到 1981], [福建省地质七队，漳州。组建实验室。],
  [1981 到 1995], [福建省闽东南地质大队，泉州。主持实验室。1987 年聘高级工程师。],
  [1995 到 2006], [广州钢光（番禺）喇叭制品有限公司。],
  [2004], [儿子建《五福在家 自得其乐》网站。],
  [2007 至今], [休闲在家，泉州。],
)
