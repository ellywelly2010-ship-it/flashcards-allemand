# Kapitel 1 sans les mots déjà connus (cochés le 2026-09-20). Réutilise les clips de kapitel1.
from spoken_kapitel1 import SPOKEN as ALL

KNOWN = {1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 20, 29, 31, 33, 34, 39, 44, 45, 51, 52}
CLIPS_FROM = "kapitel1"
SPOKEN = [(i, fr, de) for i, (fr, de) in enumerate(ALL, 1) if i not in KNOWN]
