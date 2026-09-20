# Kapitel 1 — les 38 mots ratés au test oral du 2026-09-20 (28/60). Réutilise les clips de kapitel1.
from spoken_kapitel1 import SPOKEN as ALL

KNOWN = {1, 2, 3, 4, 6, 7, 8, 12, 13, 14, 15, 19, 20, 21, 22, 27, 29, 34, 46, 49, 52, 59}
CLIPS_FROM = "kapitel1"
SPOKEN = [(i, fr, de) for i, (fr, de) in enumerate(ALL, 1) if i not in KNOWN]
