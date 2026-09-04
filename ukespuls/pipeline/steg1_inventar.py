"""Steg 1 - Inventar. Leser alle filer i ukemappen og bygger kildeliste."""
import os, re, sys
from felles import DEMO, KANAL_NIVAA, arbeidsfil, skriv_json

DATO_RE = re.compile(r"^Dato:\s*(.+)$", re.M | re.I)
FRA_RE = re.compile(r"^Fra:\s*(.+)$", re.M | re.I)
FILDATO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def kjor(uke):
    innmappe = os.path.join(DEMO, "inn", f"uke-{uke}")
    if not os.path.isdir(innmappe):
        sys.exit(f"FEIL: finner ikke {innmappe}")
    kilder, teller = [], {"epost": 0, "vedlegg": 0, "tale": 0}
    for kanal in ("vedlegg", "epost", "tale"):   # nivaarekkefolge
        mappe = os.path.join(innmappe, kanal)
        if not os.path.isdir(mappe):
            continue
        for filnavn in sorted(os.listdir(mappe)):
            if filnavn.startswith("."):
                continue
            sti = os.path.join(mappe, filnavn)
            raa = open(sti, encoding="utf-8", errors="replace").read()
            m = FILDATO_RE.search(filnavn)
            dato = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
            fra = FRA_RE.search(raa)
            dat = DATO_RE.search(raa)
            teller[kanal] += 1
            prefiks = {"epost": "E", "vedlegg": "V", "tale": "T"}[kanal]
            kilder.append({
                "kilde_id": f"{prefiks}{teller[kanal]:02d}",
                "kanal": kanal,
                "filnavn": f"inn/uke-{uke}/{kanal}/{filnavn}",
                "dato": dato,
                "avsender": fra.group(1).strip() if fra else ("dokument" if kanal == "vedlegg" else "prosjektleder"),
                "nivaa": KANAL_NIVAA[kanal],
                "dato_i_fil": dat.group(1).strip() if dat else "",
                "antall_tegn": len(raa),
            })
    ut = {"uke": uke, "antall": teller, "kilder": kilder}
    skriv_json(arbeidsfil(uke, "1-inventar.json"), ut)
    print(f"  {len(kilder)} kilder: {teller['epost']} e-post, {teller['vedlegg']} vedlegg, {teller['tale']} tale")
    return ut


if __name__ == "__main__":
    kjor(sys.argv[1] if len(sys.argv) > 1 else "2026-36")
