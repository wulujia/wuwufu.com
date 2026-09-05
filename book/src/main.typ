#import "template.typ": *

#let ms = json("manuscript.json")

#show: book.with(title: ms.book.title, subtitle: ms.book.subtitle, author: ms.book.author)

// title page
#page(header: none, footer: none)[
  #v(22%)
  #align(center)[
    #text(size: 40pt, weight: "medium")[#ms.book.title]
    #v(1.2em)
    #text(size: 13pt, fill: luma(90))[#ms.book.subtitle]
    #v(14%)
    #image(ms.book.signature, width: 55mm)
  ]
]

#page(header: none, footer: none)[]

// front matter
#include "frontmatter.typ"

#pagebreak(weak: true)
#align(center, text(size: 24pt, weight: "medium")[目录])
#v(1.5em)
#outline(title: none, depth: 2, indent: 1.5em)

// body
#for part in ms.parts {
  part-opener(part.title, part.subtitle)
  for p in part.pieces {
    render-piece(p)
  }
}

#include "backmatter.typ"
