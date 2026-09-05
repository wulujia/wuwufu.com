// Page layout and block renderers for 《五福在家》.

#let text-width = 185mm - 24mm - 18mm

#let part-state = state("part", "")

#let book(title: "", subtitle: "", author: "", body) = {
  set document(title: title, author: author)
  set page(
    width: 185mm,
    height: 260mm,
    margin: (inside: 24mm, outside: 18mm, top: 24mm, bottom: 24mm),
    binding: left,
    header: context {
      let p = counter(page).get().first()
      if p > 2 {
        set text(size: 8.5pt, fill: luma(110))
        if calc.odd(p) {
          align(right, part-state.get())
        } else {
          align(left, title)
        }
      }
    },
    footer: context {
      set text(size: 9.5pt)
      align(center, counter(page).display("1"))
    },
  )
  set text(font: ("Noto Serif CJK SC", "Noto Sans CJK SC"), size: 13pt, lang: "zh", region: "cn")
  set par(justify: true, leading: 0.85em, spacing: 0.85em, first-line-indent: (amount: 2em, all: true))
  show heading.where(level: 1): it => {
    part-state.update(it.body)
    align(center, text(size: 28pt, weight: "medium", it.body))
  }
  show heading.where(level: 2): it => {
    v(1.6em, weak: true)
    block(below: 0.6em, text(size: 18pt, weight: "semibold", it.body))
  }
  show outline.entry.where(level: 1): it => {
    v(0.9em, weak: true)
    text(weight: "semibold", it)
  }
  body
}

#let runs(rs) = rs.map(r => if r.b { strong(r.s) } else { r.s }).join()

#let para(rs) = par(runs(rs))

#let verse(lines) = {
  set par(first-line-indent: 0em, justify: false, leading: 0.7em)
  block(inset: (left: 2em), above: 0.9em, below: 0.9em, lines.map(runs).join(linebreak()))
}

// print width from pixel width at about 200 dpi, capped to the text width
#let img-width(w, h) = {
  let mm = w / 200 * 25.4 * 1mm
  let cap = if h > w * 1.3 { text-width * 0.62 } else { text-width }
  calc.min(mm, cap)
}

#let fig(src, w, h) = {
  align(center, block(above: 1em, below: 1em, image(src, width: img-width(w, h))))
}

#let img-grid(cols, imgs) = {
  block(above: 1em, below: 1em,
    grid(columns: (1fr,) * cols, gutter: 4mm, align: center + horizon,
      ..imgs.map(i => image(i.src, width: 100%))))
}

#let piece-meta(date, category) = {
  set par(first-line-indent: 0em)
  let parts = (date, category).filter(s => s != "")
  if parts.len() > 0 {
    block(below: 1.2em, text(size: 9.5pt, fill: luma(110), parts.join("　·　")))
  }
}

#let part-opener(title, subtitle) = {
  pagebreak(weak: true)
  page(header: none, footer: none)[
    #v(30%)
    #heading(level: 1, title)
    #if subtitle != "" {
      v(0.6em)
      align(center, text(size: 13pt, fill: luma(90), subtitle))
    }
  ]
}

#let render-blocks(blocks) = {
  for b in blocks {
    if b.t == "p" { para(b.runs) }
    else if b.t == "verse" { verse(b.lines) }
    else if b.t == "fig" { fig(b.src, b.w, b.h) }
    else if b.t == "grid" { img-grid(b.cols, b.imgs) }
  }
}

#let render-piece(p) = {
  heading(level: 2, p.title)
  context [#metadata((title: p.title, page: here().page())) <piece>]
  piece-meta(p.date, p.category)
  render-blocks(p.blocks)
}
