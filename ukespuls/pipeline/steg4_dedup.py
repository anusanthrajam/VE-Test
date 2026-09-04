"""Steg 4 - Deduplisering. Slaar sammen utsagn om samme sak, beholder hoyeste kildenivaa."""
import sys, collections
from felles import arbeidsfil, les_json, skriv_json

def kjor(uke):
    an = les_json(arbeidsfil(uke, "3-sortert.json"))
    grupper = collections.OrderedDict()
    for u in an["utsagn"]:
        grupper.setdefault(u["sak"], []).append(u)
    saker = []
    for sak, us in grupper.items():
        primaer = min(us, key=lambda x: (x["nivaa"], x["id"]))
        kanaler = sorted({x["kanal"] for x in us})
        punkt = next((x.get("rapportpunkt") for x in us if x.get("rapportpunkt")), primaer["tekst"])
        saker.append({
            "sak": sak,
            "kategori": primaer["kategori"],
            "delta": primaer["delta"],
            "register_id": primaer.get("register_id", ""),
            "rapportpunkt": punkt,
            "primaerkilde": primaer["filnavn"],
            "primaernivaa": primaer["nivaa"],
            "muntlig": primaer["nivaa"] == 3,
            "bekreftet_flere_kanaler": len(kanaler) > 1,
            "kanaler": kanaler,
            "kilder": sorted({x["filnavn"] for x in us}),
            "utsagn_ider": [x["id"] for x in us],
        })
    an["saker"] = saker
    skriv_json(arbeidsfil(uke, "4-deduplisert.json"), an)
    print(f"  {len(an['utsagn'])} utsagn -> {len(saker)} saker "
          f"({sum(1 for s in saker if s['bekreftet_flere_kanaler'])} bekreftet i flere kanaler)")
    return an

if __name__ == "__main__":
    kjor(sys.argv[1] if len(sys.argv) > 1 else "2026-36")
