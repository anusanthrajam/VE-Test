"""Steg 2 - Utdrag. Ett utsagn = en sak. Utdraget gjores av analysemodellen og
legges i analyse/uke-<uke>.json. Dette steget validerer og normaliserer det."""
import os, sys
from felles import ANALYSE, arbeidsfil, les_json, skriv_json, KATEGORIER, DELTA

MAL = {
    "uke": "AAAA-UU", "periode": "dd.mm-dd.mm.aaaa",
    "utsagn": [{"id": "U01", "kilde_id": "E01", "sak": "kort-sak-noekkel",
                "kategori": "PROGRAM|BUDSJETT|RISIKO|DESIGN|UPLASSERT",
                "tekst": "ett enkeltstaaende utsagn, ikke oppsummert",
                "delta": "NY|ENDRET|UENDRET|LUKKET",
                "rapportpunkt": "(valgfritt) formuleringen som skal i rapporten",
                "register_id": "(valgfritt) R-nnn eller B-nnn"}]}


def kjor(uke):
    inv = les_json(arbeidsfil(uke, "1-inventar.json"))
    sti = os.path.join(ANALYSE, f"uke-{uke}.json")
    if not os.path.exists(sti):
        malsti = os.path.join(ANALYSE, f"uke-{uke}.MAL.json")
        skriv_json(malsti, MAL)
        sys.exit(f"FEIL: mangler {sti}. Mal lagt i {malsti} - fyll den ut og kjor igjen.")
    an = les_json(sti)
    gyldige = {k["kilde_id"]: k for k in inv["kilder"]}
    feil = []
    for u in an["utsagn"]:
        if u["kilde_id"] not in gyldige:
            feil.append(f"{u['id']}: ukjent kilde_id {u['kilde_id']}")
        if u["kategori"] not in KATEGORIER:
            feil.append(f"{u['id']}: ugyldig kategori {u['kategori']}")
        if u["delta"] not in DELTA:
            feil.append(f"{u['id']}: ugyldig delta {u['delta']}")
    if feil:
        sys.exit("FEIL i utdrag:\n  " + "\n  ".join(feil))
    for u in an["utsagn"]:
        k = gyldige[u["kilde_id"]]
        u["kanal"], u["nivaa"], u["filnavn"] = k["kanal"], k["nivaa"], k["filnavn"]
    skriv_json(arbeidsfil(uke, "2-utdrag.json"), an)
    print(f"  {len(an['utsagn'])} utsagn fra {len({u['kilde_id'] for u in an['utsagn']})} kilder")
    return an


if __name__ == "__main__":
    kjor(sys.argv[1] if len(sys.argv) > 1 else "2026-36")
