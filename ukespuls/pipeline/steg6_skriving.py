"""Steg 6 - Skriving. Rapport etter mal, deretter oppdatering av registre og logg."""
import csv, datetime, os, sys
from felles import DEMO, ROT, arbeidsfil, les_json, ordtell
from steg5_delta import forrige_uke

SEKSJONER = [("PROGRAM", "program"), ("BUDSJETT", "budsjett"),
             ("RISIKO", "risiko"), ("DESIGN", "design")]
RISIKO_KOLONNER = ["id","tittel","beskrivelse","forst_observert","siste_bevegelse",
                   "status","kildenivaa","eier","konsekvens"]
BESL_KOLONNER = ["id","dato","beslutning","begrunnelse","besluttet_av","erstatter","kilde"]


def formater(sak):
    t = sak["rapportpunkt"].rstrip()
    if sak["delta"] == "LUKKET":
        t = "Lukket: " + t[0].upper() + t[1:]
    if sak["bekreftet_flere_kanaler"]:
        t += " (bekreftet i flere kanaler)"
    if sak["muntlig"]:
        t += " (muntlig)"
    if sak["register_id"]:
        t += f" [{sak['register_id']}]"
    return "- " + t


def skriv_rapport(an, uke, maks_punkter=5, maks_ord=25):
    inv = les_json(arbeidsfil(uke, "1-inventar.json"))
    n = inv["antall"]
    mal = open(os.path.join(ROT, "config", "rapportmal.md"), encoding="utf-8").read()
    felt = {"prosjekt_kort": an.get("prosjekt_kort", ""), "uke": uke.split("-")[1].lstrip("0"),
            "periode": an["periode"], "n_epost": n["epost"], "n_vedlegg": n["vedlegg"], "n_tale": n["tale"]}
    feil = []
    for kat, navn in SEKSJONER:
        linjer = [formater(s) for s in an["saker"] if s["i_rapport"] and s["kategori"] == kat]
        if len(linjer) > maks_punkter:
            feil.append(f"{kat}: {len(linjer)} punkter (maks {maks_punkter})")
        for l in linjer:
            if ordtell(l[2:]) > maks_ord:
                feil.append(f"{kat}: punkt paa {ordtell(l[2:])} ord (maks {maks_ord}): {l[:60]}...")
        felt[navn] = "\n".join(linjer) or f"- Ingen endring siden uke {int(forrige_uke(uke).split('-')[1])}."
    uklart = ["- " + q["tekst"] + (" (muntlig)" if q.get("muntlig") else "") for q in an.get("uklart", [])]
    if len(uklart) > maks_punkter:
        feil.append(f"UKLART: {len(uklart)} punkter (maks {maks_punkter})")
    felt["uklart"] = "\n".join(uklart) or f"- Ingen endring siden uke {int(forrige_uke(uke).split('-')[1])}."
    if feil:
        sys.exit("FEIL mot stilregler:\n  " + "\n  ".join(feil))
    sti = os.path.join(DEMO, "ut", f"ukesrapport-{uke}.md")
    open(sti, "w", encoding="utf-8").write(mal.format(**felt))
    print(f"  skrev demo/ut/ukesrapport-{uke}.md")
    return sti


def les_csv(sti, kolonner):
    if not os.path.exists(sti):
        return []
    with open(sti, encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def skriv_csv(sti, kolonner, rader):
    with open(sti, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=kolonner, lineterminator="\n")
        w.writeheader()
        for r in rader:
            w.writerow({k: r.get(k, "") for k in kolonner})


def oppdater_risiko(an):
    sti = os.path.join(DEMO, "registre", "risikoregister.csv")
    rader = les_csv(sti, RISIKO_KOLONNER)
    indeks = {r["id"]: r for r in rader}
    brukte = {r["id"] for r in rader}
    endringer = []
    for oppf in an.get("risikoregister", []):
        rid = oppf["id"]
        if oppf["handling"] == "ny":
            if rid in brukte:   # allerede skrevet i en tidligere kjoring - idempotent
                endringer.append(f"{rid} uendret")
                continue
            ny = {k: str(oppf.get(k, "")) for k in RISIKO_KOLONNER}
            ny["id"] = rid
            rader.append(ny)
            endringer.append(f"{rid} ny")
        else:
            if rid not in indeks:
                sys.exit(f"FEIL: ukjent risiko-ID {rid}")
            r = indeks[rid]
            for k in ("beskrivelse", "siste_bevegelse", "status", "kildenivaa", "eier", "konsekvens"):
                if k in oppf and str(oppf[k]) != r.get(k, ""):
                    r[k] = str(oppf[k])
            endringer.append(f"{rid} oppdatert")
    for r in rader:  # hard regel: nivaa 3 kan ikke eskaleres
        if str(r.get("kildenivaa")) == "3" and r.get("status") == "eskalert":
            sys.exit(f"FEIL: {r['id']} har kildenivaa 3 og kan ikke settes til eskalert")
    skriv_csv(sti, RISIKO_KOLONNER, rader)
    print(f"  risikoregister: {', '.join(endringer) or 'ingen endring'}")


def oppdater_beslutninger(an):
    sti = os.path.join(DEMO, "registre", "beslutningslogg.csv")
    rader = les_csv(sti, BESL_KOLONNER)
    brukte = {r["id"] for r in rader}
    endringer = []
    for oppf in an.get("beslutningslogg", []):
        if oppf["handling"] == "ny":
            if oppf["id"] in brukte:   # allerede skrevet i en tidligere kjoring
                endringer.append(f"{oppf['id']} uendret")
                continue
            rad = {k: oppf.get(k, "") for k in BESL_KOLONNER}
            if not rad["begrunnelse"]:
                rad["begrunnelse"] = "ikke oppgitt"
            rader.append(rad)
            endringer.append(f"{oppf['id']} ny")
    skriv_csv(sti, BESL_KOLONNER, rader)
    print(f"  beslutningslogg: {', '.join(endringer) or 'ingen endring'}")


def oppdater_uplassert(an, uke):
    sti = os.path.join(DEMO, "registre", "uplassert.md")
    tekst = open(sti, encoding="utf-8").read().rstrip() if os.path.exists(sti) else "# Uplassert innhold"
    overskrift = f"## Uke {int(uke.split('-')[1])}"
    if overskrift in tekst:
        tekst = tekst.split(overskrift)[0].rstrip()
    linjer = []
    for s in an["saker"]:
        if s["kategori"] != "UPLASSERT":
            continue
        for u in an["utsagn"]:
            if u["sak"] == s["sak"] and u["nivaa"] == s["primaernivaa"]:
                linjer.append(f"- {u['tekst']} (kilde: {u['filnavn']})")
    open(sti, "w", encoding="utf-8").write(tekst + f"\n\n{overskrift}\n" + ("\n".join(linjer) or "- (ingen)") + "\n")
    print(f"  uplassert.md: {len(linjer)} punkter under {overskrift}")


def logg(an, uke):
    sti = os.path.join(ROT, "logg", "kjoringer.log")
    os.makedirs(os.path.dirname(sti), exist_ok=True)
    inv = les_json(arbeidsfil(uke, "1-inventar.json"))
    n = inv["antall"]
    i_rapport = sum(1 for s in an["saker"] if s["i_rapport"])
    linje = (f"{datetime.datetime.now().isoformat(timespec='seconds')} | uke={uke} | "
             f"kilder={len(inv['kilder'])} (epost={n['epost']}, vedlegg={n['vedlegg']}, tale={n['tale']}) | "
             f"utsagn={len(an['utsagn'])} | saker={len(an['saker'])} | i_rapport={i_rapport} | "
             f"uendret_utelatt={sum(1 for s in an['saker'] if s['delta']=='UENDRET')} | "
             f"uplassert={sum(1 for s in an['saker'] if s['kategori']=='UPLASSERT')} | "
             f"risiko_endret={len(an.get('risikoregister', []))} | "
             f"beslutninger_nye={len(an.get('beslutningslogg', []))} | "
             f"ut=ut/ukesrapport-{uke}.md | status=OK\n")
    open(sti, "a", encoding="utf-8").write(linje)
    print(f"  logg/kjoringer.log oppdatert")


def kjor(uke):
    an = les_json(arbeidsfil(uke, "5-delta.json"))
    skriv_rapport(an, uke)
    oppdater_risiko(an)
    oppdater_beslutninger(an)
    oppdater_uplassert(an, uke)
    logg(an, uke)
    return an

if __name__ == "__main__":
    kjor(sys.argv[1] if len(sys.argv) > 1 else "2026-36")
