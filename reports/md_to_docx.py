"""Конвертация отчётов из Markdown в Word (.docx)."""
import re
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


REPORTS_DIR = os.path.dirname(os.path.abspath(__file__))
DESKTOP = os.path.expanduser("~/Desktop")


def set_cell_bg(cell, color_hex):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tcPr.append(shd)


def add_run_with_style(para, text, bold=False, code=False):
    run = para.add_run(text)
    run.bold = bold
    if code:
        run.font.name = "Courier New"
        run.font.size = Pt(9)
    return run


def parse_inline(para, text):
    """Разбирает inline-разметку: **bold**, `code`, обычный текст."""
    pattern = re.compile(r"(\*\*(.+?)\*\*|`(.+?)`)")
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            para.add_run(text[last:m.start()])
        if m.group(2):
            add_run_with_style(para, m.group(2), bold=True)
        elif m.group(3):
            add_run_with_style(para, m.group(3), code=True)
        last = m.end()
    if last < len(text):
        para.add_run(text[last:])


def md_to_docx(md_path, docx_path):
    doc = Document()

    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Times New Roman"
    style_normal.font.size = Pt(12)

    for level in range(1, 5):
        hstyle = doc.styles[f"Heading {level}"]
        hstyle.font.name = "Times New Roman"
        hstyle.font.bold = True
        hstyle.font.color.rgb = RGBColor(0, 0, 0)
        hstyle.font.size = Pt(16 - (level - 1) * 2)

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")

        # Заголовки
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            para = doc.add_heading(level=level)
            para.clear()
            run = para.add_run(text)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(16 - (level - 1) * 2)
            run.font.color.rgb = RGBColor(0, 0, 0)
            i += 1
            continue

        # Горизонтальный разделитель
        if re.match(r"^---+$", line):
            para = doc.add_paragraph()
            pPr = para._p.get_or_add_pPr()
            pb = OxmlElement("w:pBdr")
            bot = OxmlElement("w:bottom")
            bot.set(qn("w:val"), "single")
            bot.set(qn("w:sz"), "6")
            bot.set(qn("w:space"), "1")
            bot.set(qn("w:color"), "999999")
            pb.append(bot)
            pPr.append(pb)
            i += 1
            continue

        # Таблица markdown
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i].rstrip("\n"))
                i += 1
            rows = [
                [c.strip() for c in r.strip("|").split("|")]
                for r in table_lines
                if not re.match(r"^\|[-| :]+\|$", r.strip())
            ]
            if not rows:
                continue
            cols = len(rows[0])
            tbl = doc.add_table(rows=len(rows), cols=cols)
            tbl.style = "Table Grid"
            for r_idx, row_data in enumerate(rows):
                for c_idx, cell_text in enumerate(row_data):
                    cell = tbl.rows[r_idx].cells[c_idx]
                    cell.text = ""
                    para = cell.paragraphs[0]
                    parse_inline(para, cell_text)
                    for run in para.runs:
                        run.font.size = Pt(10)
                        run.font.name = "Times New Roman"
                    if r_idx == 0:
                        for run in para.runs:
                            run.bold = True
                        set_cell_bg(cell, "D9D9D9")
            doc.add_paragraph()
            continue

        # Блок кода
        if line.startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            i += 1
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Inches(0.3)
            run = para.add_run("\n".join(code_lines))
            run.font.name = "Courier New"
            run.font.size = Pt(9)
            shading = OxmlElement("w:shd")
            shading.set(qn("w:val"), "clear")
            shading.set(qn("w:color"), "auto")
            shading.set(qn("w:fill"), "F2F2F2")
            para._p.get_or_add_pPr().append(shading)
            continue

        # Маркированный список
        m = re.match(r"^[-*]\s+(.*)", line)
        if m:
            para = doc.add_paragraph(style="List Bullet")
            parse_inline(para, m.group(1))
            for run in para.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
            i += 1
            continue

        # Нумерованный список
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            para = doc.add_paragraph(style="List Number")
            parse_inline(para, m.group(1))
            for run in para.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
            i += 1
            continue

        # Пустая строка
        if line.strip() == "":
            i += 1
            continue

        # Обычный абзац
        para = doc.add_paragraph()
        parse_inline(para, line)
        for run in para.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
        i += 1

    doc.save(docx_path)
    print(f"Сохранён: {docx_path}")


if __name__ == "__main__":
    reports = [
        "отчет_ПР1.md",
        "отчет_ПР2.md",
        "отчет_ПР3.md",
        "отчет_ПР5.md",
    ]
    for name in reports:
        src = os.path.join(REPORTS_DIR, name)
        dst = os.path.join(DESKTOP, name.replace(".md", ".docx"))
        md_to_docx(src, dst)
