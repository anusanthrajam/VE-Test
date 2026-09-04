"""Steg 5 - Delta. Sammenligner mot forrige ukesrapport og registrene.
Kun NY, ENDRET og LUKKET gaar videre til rapporten."""
import csv, os, re, sys
from felles import DEMO, arbeidsfil, les_json, skriv_json

def forrige_uke(uke):
    aar, nr = uke.split("-")
    return f"{aar}-{int(nr)-1:02d}"

def kjor(uke):
    an = les_json(arbeidsfil(uke, "4-deduplisert.json"))
    forrige = os.path.join(DEMO, "ut", f"ukesrapport-{forrige_uke(uke)}.md")
    forrige_tekst = open(forrige, encoding="utf-8").read() if os.path.exists(forrige) else ""
    kjente = set(re.findall(r"\[([RB]-\d{3})\]", forrige_tekst))
    for navn in ("risikoregister.csv", "beslutningslogg.csv"):
        sti = os.path.join(DEMO, "registre", navn)
        if os.path.exists(sti):
            with open(sti, encoding="utf-8") as f:
                kjente |= {r["id"] for r in csv.DictReader(f)}
    for s in an["saker"]:
        s["kjent_fra_for"] = s["register_id"] in kjente if s["register_id"] else False
        s["i_rapport"] = s["delta"] in ("NY", "ENDRET", "LUKKET") and s["kategori"] != "UPLASSERT"
    utelatt = [s["sak"] for s in an["saker"] if s["delta"] == "UENDRET"]
    an["forrige_rapport"] = os.path.relpath(forrige, DEMO) if forrige_tekst else None
    skriv_json(arbeidsfil(uke, "5-delta.json"), an)
    print(f"  {sum(1 for s in an['saker'] if s['i_rapport'])} saker til rapport, "
          f"{len(utelatt)} UENDRET utelatt, "
          f"{sum(1 for s in an['saker'] if s['kategori']=='UPLASSERT')} til uplassert.md")
    return an

if __name__ == "__main__":
    kjor(sys.argv[1] if len(sys.argv) > 1 else "2026-36")
