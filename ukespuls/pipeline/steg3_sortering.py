"""Steg 3 - Sortering. Merker hvert utsagn med seksjon og haandhever kildehierarkiet."""
import sys, collections
from felles import arbeidsfil, les_json, skriv_json

def kjor(uke):
    an = les_json(arbeidsfil(uke, "2-utdrag.json"))
    per_sak = collections.defaultdict(set)
    for u in an["utsagn"]:
        per_sak[u["sak"]].add(u["kategori"])
    feil = [f"saken '{s}' er sortert i flere kategorier: {sorted(k)}"
            for s, k in per_sak.items() if len(k) > 1]
    # Hard regel 1: tall fra tale blir aldri budsjettall
    for u in an["utsagn"]:
        if u["kategori"] == "BUDSJETT" and u["nivaa"] == 3:
            feil.append(f"{u['id']}: utsagn fra tale (nivaa 3) kan ikke sorteres som BUDSJETT")
    if feil:
        sys.exit("FEIL i sortering:\n  " + "\n  ".join(feil))
    fordeling = collections.Counter(u["kategori"] for u in an["utsagn"])
    skriv_json(arbeidsfil(uke, "3-sortert.json"), an)
    print("  " + ", ".join(f"{k}: {v}" for k, v in sorted(fordeling.items())))
    return an

if __name__ == "__main__":
    kjor(sys.argv[1] if len(sys.argv) > 1 else "2026-36")
