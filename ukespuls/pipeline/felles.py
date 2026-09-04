"""Fellesfunksjoner for UKESPULS-pipelinen."""
import json, os, re, sys, unicodedata

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROT, "demo")
ARBEID = os.path.join(ROT, "arbeid")
ANALYSE = os.path.join(ROT, "analyse")

KANAL_NIVAA = {"vedlegg": 1, "epost": 2, "tale": 3}
KATEGORIER = ["PROGRAM", "BUDSJETT", "RISIKO", "DESIGN", "UPLASSERT"]
DELTA = ["NY", "ENDRET", "UENDRET", "LUKKET"]


def les_json(sti):
    with open(sti, encoding="utf-8") as f:
        return json.load(f)


def skriv_json(sti, data):
    os.makedirs(os.path.dirname(sti), exist_ok=True)
    with open(sti, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  skrev {os.path.relpath(sti, ROT)}")


def arbeidsfil(uke, navn):
    return os.path.join(ARBEID, f"uke-{uke}", navn)


def ordtell(tekst):
    """Teller ord i et rapportpunkt. Kildemerker i parentes/hakeparentes teller ikke."""
    t = re.sub(r"\[[^\]]*\]", " ", tekst)
    t = re.sub(r"\((muntlig|bekreftet i flere kanaler)\)", " ", t)
    return len([o for o in re.split(r"\s+", t.strip()) if o])
