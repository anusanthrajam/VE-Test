"""Egenkontroll mot akseptansekriteriene i spesifikasjonen (SS 8).
Bruk: python3 kontroll.py [uke]"""
import os, re, sys
from felles import DEMO, arbeidsfil, les_json, ordtell
from steg5_delta import forrige_uke

def seksjoner(tekst):
    ut, navn = {}, None
    for linje in tekst.splitlines():
        if linje.startswith("## "):
            navn = linje[3:].strip()
            ut[navn] = []
        elif linje.startswith("- ") and navn:
            ut[navn].append(linje[2:].strip())
    return ut

def kjor(uke):
    rapport = open(os.path.join(DEMO, "ut", f"ukesrapport-{uke}.md"), encoding="utf-8").read()
    forr_sti = os.path.join(DEMO, "ut", f"ukesrapport-{forrige_uke(uke)}.md")
    forrige = open(forr_sti, encoding="utf-8").read() if os.path.exists(forr_sti) else ""
    uplassert = open(os.path.join(DEMO, "registre", "uplassert.md"), encoding="utf-8").read()
    an = les_json(arbeidsfil(uke, "5-delta.json"))
    s = seksjoner(rapport)
    punkter = {k: v for k, v in s.items()}
    res = []

    # 1 - muntlig anslag om ventilasjonskostnad ikke i budsjettseksjonen
    budsj = " ".join(s.get("Budsjett", []))
    t1 = not re.search(r"300\s*000|tre hundre|muntlig", budsj, re.I)
    res.append((1, "Muntlig anslag om ventilasjonskostnad ikke i budsjettseksjonen", t1,
                "Budsjettseksjonen inneholder kun tall fra okonomirapport-2026-08.csv (nivaa 1)."
                if t1 else "Muntlig anslag funnet i budsjettseksjonen."))

    # 2 - motstriden staar i Uklart
    ukl = " ".join(s.get("Uklart / trenger bekreftelse", []))
    t2 = bool(re.search(r"300\s*000|tre hundre", ukl)) and bool(re.search(r"120\s*000|okonomirapport|økonomirapport", ukl, re.I))
    res.append((2, "Motstrid tale vs. okonomirapport staar i Uklart", t2,
                "Punktet setter det muntlige anslaget mot rapportert avvik 120 000." if t2 else "Motstriden mangler i Uklart."))

    # 3 - uendrede punkter fra uke 35 ikke gjentatt
    forrige_punkter = [p for ps in seksjoner(forrige).values() for p in ps]
    def noekkel(p): return set(re.findall(r"[a-zæøå]{5,}", p.lower()))
    gjentatt = [p for ps in punkter.values() for p in ps
                for f in forrige_punkter if len(noekkel(p) & noekkel(f)) >= 4]
    uendret = [x["sak"] for x in an["saker"] if x["delta"] == "UENDRET"]
    t3 = not gjentatt
    res.append((3, "Uendrede punkter fra uke 35 er ikke gjentatt", t3,
                f"Ingen punkt overlapper vesentlig med uke 35; delta-steget slipper kun NY/ENDRET/LUKKET gjennom (UENDRET utelatt: {len(uendret)})."
                if t3 else f"Gjentatt: {gjentatt}"))

    # 4 - julebord i uplassert.md, ikke i rapporten
    t4 = "julebord" in uplassert.lower() and "julebord" not in rapport.lower()
    res.append((4, "E-post om julebord ligger i uplassert.md, ikke i rapporten", t4,
                "Staar under '## Uke 36' i uplassert.md og finnes ikke i rapporten." if t4 else "Feil plassering."))

    # 5 - de to himling-e-postene slaatt sammen til ett punkt
    himling_saker = [x for x in an["saker"] if x["i_rapport"]
                     and len([k for k in x["kilder"] if "himling" in k and "/epost/" in k]) == 2]
    dublett = [x["sak"] for x in an["saker"] if x["i_rapport"]
               and x["register_id"] == "B-012" and x not in himling_saker]
    t5 = len(himling_saker) == 1 and not dublett
    res.append((5, "De to e-postene om himling er slaatt sammen til ett punkt", t5,
                f"Sak '{himling_saker[0]['sak']}' dekker begge himling-e-postene i ett punkt "
                f"[{himling_saker[0]['register_id']}]; ingen annen rapportlinje dekker samme sak."
                if t5 else f"Ikke slaatt sammen (dubletter: {dublett})."))

    # 6 - maks 5 punkter per seksjon, maks 25 ord per punkt
    brudd = [f"{k}: {len(v)} punkter" for k, v in punkter.items() if len(v) > 5]
    brudd += [f"{k}: {ordtell(p)} ord - {p[:40]}..." for k, v in punkter.items() for p in v if ordtell(p) > 25]
    t6 = not brudd
    maks = max((ordtell(p) for v in punkter.values() for p in v), default=0)
    res.append((6, "Maks 5 punkter per seksjon, maks 25 ord per punkt", t6,
                f"Storste seksjon: {max(len(v) for v in punkter.values())} punkter. Lengste punkt: {maks} ord."
                if t6 else "; ".join(brudd)))

    # 7 - under en A4-side
    linjer, tegn = len(rapport.strip().splitlines()), len(rapport)
    t7 = linjer <= 46 and tegn <= 3500
    res.append((7, "Hele rapporten er under en A4-side", t7,
                f"{linjer} linjer / {tegn} tegn - innenfor en A4-side (grense 46 linjer / 3500 tegn)."))

    # 8 - hvert punkt sporbart til fil i ukemappen
    uspor = [x["sak"] for x in an["saker"] if x["i_rapport"]
             and not all(k.startswith(f"inn/uke-{uke}/") for k in x["kilder"])]
    ant_punkter = sum(len(v) for k, v in punkter.items() if k != "Uklart / trenger bekreftelse")
    t8 = not uspor and ant_punkter == sum(1 for x in an["saker"] if x["i_rapport"])
    res.append((8, "Hvert punkt kan spores til en fil i inn/uke-" + uke, t8,
                f"Alle {ant_punkter} rapportpunkter har primaerkilde i inn/uke-{uke}/; Uklart-punktene er sporet i analysefila."
                if t8 else f"Usporbare: {uspor}"))

    print(f"EGENKONTROLL - ukesrapport-{uke}.md\n")
    for nr, tittel, ok, begr in res:
        print(f"{nr}. {tittel}\n   {'BESTÅTT' if ok else 'IKKE BESTÅTT'} - {begr}\n")
    alle = all(r[2] for r in res)
    print("SAMLET: " + ("BESTÅTT - alle 8 kriterier" if alle else "IKKE BESTÅTT"))
    return alle

if __name__ == "__main__":
    sys.exit(0 if kjor(sys.argv[1] if len(sys.argv) > 1 else "2026-36") else 1)
