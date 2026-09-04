# UKESPULS – Bjørnheia skole

Samler prosjektinformasjon fra e-post, vedlegg og taleopptak gjennom uken og
produserer én kort ukesrapport pluss to levende registre.

## Mappestruktur

```
ukespuls/
├── config/
│   ├── prosjekt.yaml            prosjekt-, budsjett- og rapportkonfigurasjon
│   └── rapportmal.md            malen rapporten fylles inn i
├── pipeline/                    de seks stegene + kjor.py og kontroll.py
├── analyse/uke-ÅÅÅÅ-UU.json     utdraget (steg 2–3) – det eneste som skrives for hånd
├── arbeid/uke-ÅÅÅÅ-UU/          mellomresultat fra hvert steg (1–5), for etterprøving
├── logg/kjoringer.log           én linje per kjøring
└── demo/
    ├── inn/uke-ÅÅÅÅ-UU/{epost,vedlegg,tale}/   kildene for uken
    ├── ut/ukesrapport-ÅÅÅÅ-UU.md               rapporten
    └── registre/                risikoregister.csv, beslutningslogg.csv, uplassert.md
```

## Legge inn en ny uke

1. Opprett `demo/inn/uke-2026-37/` med undermappene `epost/`, `vedlegg/` og `tale/`
   (uke 37 ligger allerede klar).
2. Legg filene inn: én e-post per `.txt`, vedlegg som de er, taleopptak som
   transkribert tekst. Start filnavnet med datoen: `2026-09-09-emne.txt`.
3. Kjør steg 1 for å bygge inventaret:
   `cd pipeline && python3 steg1_inventar.py 2026-37`
4. Lag utdraget `analyse/uke-2026-37.json`. Steg 2 skriver en mal
   (`analyse/uke-2026-37.MAL.json`) hvis fila mangler. Ett utsagn = én sak, med
   `kilde_id` fra inventaret, `sak`, `kategori`, `delta` og – på det utsagnet som
   skal i rapporten – `rapportpunkt`. Dette er det eneste vurderingssteget;
   resten er deterministisk. Legg også inn `uklart`, `risikoregister` og
   `beslutningslogg` i samme fil.
5. Kjør hele pipelinen: `python3 kjor.py 2026-37`
6. Kjør egenkontrollen: `python3 kontroll.py 2026-37`

`kjor.py` uten argument bruker inneværende ISO-uke.

## Hva de seks stegene gjør

| Steg | Fil | Gjør |
|---|---|---|
| 1 | `steg1_inventar.py` | Leser ukemappen, bygger `{kilde_id, kanal, filnavn, dato, avsender, nivå}` |
| 2 | `steg2_utdrag.py` | Validerer utdraget mot inventaret og kobler på kanal og nivå |
| 3 | `steg3_sortering.py` | Håndhever kategoriene og regelen om at tale aldri blir budsjettall |
| 4 | `steg4_dedup.py` | Slår sammen utsagn per sak, beholder høyeste kildenivå, merker flere kanaler |
| 5 | `steg5_delta.py` | Sammenligner mot forrige rapport og registrene; UENDRET faller ut |
| 6 | `steg6_skriving.py` | Skriver rapporten, oppdaterer registrene, uplassert.md og loggen |

Hvert steg kan kjøres alene: `python3 stegN_navn.py 2026-37`. Mellomresultatene
ligger i `arbeid/uke-ÅÅÅÅ-UU/` slik at et hvert punkt kan spores tilbake til fil.

## Reglene systemet håndhever automatisk

- Tale (nivå 3) kan ikke sorteres som BUDSJETT – steg 3 stopper kjøringen.
- Punkter med talekilde som primærkilde merkes `(muntlig)`.
- Risiko på kildenivå 3 kan ikke settes til `eskalert` – steg 6 stopper kjøringen.
- Maks 5 punkter per seksjon og maks 25 ord per punkt – steg 6 stopper kjøringen.
- Tom seksjon skrives som `- Ingen endring siden uke NN.`
- `LUKKET`-punkter får prefiks `Lukket:`.
- Register-ID-er tildeles én gang; en ny ID som allerede finnes blir ikke skrevet på nytt.
- Kjøringen er idempotent: samme uke kan kjøres flere ganger uten å doble registrene.

## Fast kjøring

Systemet kjøres som en planlagt oppgave hver fredag kl. 14:00 (norsk tid).
Oppgaven finner inneværende ISO-uke, kjører pipelinen på `demo/inn/uke-<år>-<uke>/`,
skriver rapporten, oppdaterer registrene og varsler når den er ferdig.
Merk: tidspunktet er satt i UTC (12:00), så i vinterhalvåret kjører den 13:00 norsk tid
med mindre cron-uttrykket endres til `0 13 * * 5`.
