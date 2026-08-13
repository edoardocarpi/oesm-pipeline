"""
Formattazione numerica per value_display.

Regole (dal documento di riferimento della pipeline):
- il sito fa parseFloat() su value_display: punto come separatore decimale,
  niente separatori delle migliaia
- "nessun dato" deve essere un vero NULL SQL, mai la stringa "null"
- conversion_note: se è una singola parola minuscola senza spazi il sito la
  nasconde come "codice tecnico interno" — quindi le note vanno sempre scritte
  come frasi leggibili, con spazi
"""

from __future__ import annotations


def format_value_display(value: float | None) -> str | None:
    """None -> None (che diventa un vero NULL SQL in fase di scrittura).
    Altrimenti stringa numerica semplice, punto decimale, precisione originale."""
    if value is None:
        return None
    # repr/str di un float Python non introduce mai separatori delle migliaia
    # e usa sempre il punto — è già nel formato richiesto.
    return str(value)


def is_technical_code(note: str | None) -> bool:
    """Replica la regola del sito: una nota tutta minuscola e senza spazi
    viene trattata come codice tecnico interno e nascosta. Usarla per
    validare (in test o prima della scrittura) che le note pensate per
    essere lette davvero non cadano per errore in questo caso."""
    if not note:
        return False
    return note == note.lower() and " " not in note
