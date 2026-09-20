#!/usr/bin/env python3
"""Génère un PDF A4 recto/verso de flashcards allemand → français.

Page impaire = recto (allemand), page paire = verso (français) en miroir
horizontal, pour impression recto-verso « retourner sur le bord long ».
Les traits de découpe traversent toute la page.

Usage : .venv/bin/python build.py [vocab_module] [sortie.pdf]
"""
import importlib
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

module_name = sys.argv[1] if len(sys.argv) > 1 else "vocab_kapitel1"
out = sys.argv[2] if len(sys.argv) > 2 else f"flashcards_{module_name.replace('vocab_', '')}.pdf"
VOCAB = importlib.import_module(module_name).VOCAB

# ── Polices (Unicode : ü, œ, ≠, →, ¨) ────────────────────────────────────────
FONT_DIR = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("Arial", FONT_DIR + "Arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_DIR + "Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", FONT_DIR + "Arial Italic.ttf"))

# ── Grille ───────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
COLS, ROWS = 3, 7
MARGIN_X, MARGIN_Y = 10 * mm, 10 * mm
CARD_W = (PAGE_W - 2 * MARGIN_X) / COLS
CARD_H = (PAGE_H - 2 * MARGIN_Y) / ROWS
PER_PAGE = COLS * ROWS
PAD = 3 * mm

GERMAN_COLOR = (0.10, 0.10, 0.10)
FRENCH_COLOR = (0.05, 0.25, 0.55)
TAG_COLOR = (0.55, 0.55, 0.55)
LINE_COLOR = (0.65, 0.65, 0.65)


def wrap(text, font, size, max_w):
    """Coupe un texte en lignes ≤ max_w (coupe de préférence après ; / →)."""
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(trial, font, size) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(text, font, max_w, max_h, start=20, floor=7):
    """Trouve la plus grande taille qui tient dans la boîte."""
    size = start
    while size > floor:
        lines = wrap(text, font, size, max_w)
        if len(lines) * size * 1.25 <= max_h and all(
            pdfmetrics.stringWidth(l, font, size) <= max_w for l in lines
        ):
            return size, lines
        size -= 0.5
    return floor, wrap(text, font, floor, max_w)


def draw_grid(c):
    c.setStrokeColorRGB(*LINE_COLOR)
    c.setLineWidth(0.4)
    c.setDash(3, 3)
    for i in range(COLS + 1):
        x = MARGIN_X + i * CARD_W
        c.line(x, 0, x, PAGE_H)
    for j in range(ROWS + 1):
        y = MARGIN_Y + j * CARD_H
        c.line(0, y, PAGE_W, y)
    c.setDash()


def draw_card(c, col, row, main, tag, font, color, main_size_start):
    x0 = MARGIN_X + col * CARD_W
    y0 = PAGE_H - MARGIN_Y - (row + 1) * CARD_H  # reportlab : origine en bas
    inner_w = CARD_W - 2 * PAD
    inner_h = CARD_H - 2 * PAD - 3.5 * mm  # place pour l'étiquette

    size, lines = fit(main, font, inner_w, inner_h, start=main_size_start)
    lh = size * 1.25
    block_h = len(lines) * lh
    cy = y0 + PAD + 3 * mm + (inner_h - block_h) / 2 + block_h - size
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    for line in lines:
        c.drawCentredString(x0 + CARD_W / 2, cy, line)
        cy -= lh

    # étiquette discrète (section · niveau)
    c.setFont("Arial-Italic", 5)
    c.setFillColorRGB(*TAG_COLOR)
    c.drawCentredString(x0 + CARD_W / 2, y0 + PAD - 0.5 * mm, tag)


def footer(c, page_no, side, total):
    c.setFont("Arial", 6.5)
    c.setFillColorRGB(*TAG_COLOR)
    c.drawCentredString(PAGE_W / 2, 4 * mm, f"Feuille {page_no}/{total} · {side}")


c = canvas.Canvas(out, pagesize=A4)
c.setTitle("Flashcards allemand – Kapitel 1")
total_sheets = (len(VOCAB) + PER_PAGE - 1) // PER_PAGE

for sheet in range(total_sheets):
    chunk = VOCAB[sheet * PER_PAGE:(sheet + 1) * PER_PAGE]

    # ── RECTO : allemand ──
    draw_grid(c)
    for i, (de, fr, section, level) in enumerate(chunk):
        col, row = i % COLS, i // COLS
        draw_card(c, col, row, de, f"{section} · {level}", "Arial-Bold", GERMAN_COLOR, 13)
    footer(c, sheet + 1, "RECTO – Deutsch", total_sheets)
    c.showPage()

    # ── VERSO : français, colonnes inversées (retournement bord long) ──
    draw_grid(c)
    for i, (de, fr, section, level) in enumerate(chunk):
        col, row = (COLS - 1) - (i % COLS), i // COLS
        draw_card(c, col, row, fr, f"{section} · {level}", "Arial", FRENCH_COLOR, 12)
    footer(c, sheet + 1, "VERSO – Français", total_sheets)
    c.showPage()

c.save()
print(f"{out} : {len(VOCAB)} cartes, {total_sheets} feuilles ({total_sheets * 2} pages)")
