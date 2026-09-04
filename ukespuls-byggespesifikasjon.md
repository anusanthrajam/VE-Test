# UKESPULS v1 — byggespesifikasjon

**Til deg som leser dette (Claude Cowork eller Claude Code):**
Dette er en komplett spesifikasjon for et system som samler inn prosjektinformasjon gjennom uken fra flere kanaler og produserer én kort ukesrapport pluss to levende registre. Bygg det nøyaktig som beskrevet. Der noe er markert `[FYLL INN]`, spør brukeren én gang samlet før du starter — ikke gjett.

**Overordnet krav som slår alt annet:** rapporten skal være kort og faktabasert. Det er ikke lov å fylle ut en seksjon fordi den finnes. Tom seksjon skrives som tom. Se § 9 (Stilregler) — brudd på disse regnes som feil, ikke som smakssak.

---

## 1. Hva systemet gjør

```
Kanaler gjennom uken            Én gang i uken                 Ut
─────────────────────           ──────────────                 ───
E-post (auto-merket)   ─┐
Vedlegg/dokumenter     ─┼──►  /uke-NN/  ──►  6-stegs   ──►  Ukesrapport (ny fil)
Taleopptak (transkribert)┘     (råmappe)      pipeline       Risikoregister (oppdatert)
                                                             Beslutningslogg (oppdatert)
                                                             Spør-meg-liste
```

Rapporten har fire faste deler: **Program**, **Budsjett**, **Nøkkelrisiko**, **Designbeslutninger**. Ingen flere.

---

## 2. Mappestruktur og navnekonvensjon

Opprett denne strukturen. Bruk nøyaktig disse navnene — pipelinen leter etter dem.

```
/Ukespuls/
├── config/
│   ├── prosjekt.yaml            # prosjektkonfigurasjon (§3)
│   └── rapportmal.md            # malen i §6, uendret
├── prosjekter/
│   └── <prosjekt-slug>/
│       ├── inn/
│       │   ├── uke-2026-36/     # ISO-år + ISO-ukenummer, alltid to siffer
│       │   │   ├── epost/       # .eml eller .txt, ett per melding
│       │   │   ├── vedlegg/     # pdf/xlsx/docx, originalt filnavn beholdes
│       │   │   └── tale/        # tale-YYYY-MM-DD-HHMM.txt (transkripsjon)
│       │   └── uke-2026-37/
│       ├── ut/
│       │   └── ukesrapport-2026-36.md
│       └── registre/
│           ├── risikoregister.csv
│           ├── beslutningslogg.csv
│           └── uplassert.md     # innhold som ikke passet i noen seksjon
└── logg/
    └── kjoringer.log            # én linje per kjøring: tidspunkt, uke, antall kilder, status
```

**Regler:**
- Ukemappen opprettes automatisk mandag morgen hvis den ikke finnes.
- Ingen fil slettes eller flyttes ut av `inn/` etter kjøring. Råmaterialet er revisjonsspor.
- Registrene **oppdateres**, skrives aldri på nytt fra bunn. Historikk er poenget.

---

## 3. Konfigurasjon — `config/prosjekt.yaml`

Generer denne filen og fyll den med brukerens svar.

```yaml
prosjekt:
  navn: "[FYLL INN]"
  slug: "[FYLL INN]"           # mappenavn, små bokstaver, bindestrek
  prosjektleder: "[FYLL INN]"
  kontraktsform: "[FYLL INN]"  # f.eks. totalentreprise NS 8407
  oppstart: "[FYLL INN]"
  planlagt_ferdig: "[FYLL INN]"

budsjett:
  totalramme: "[FYLL INN]"
  valuta: NOK
  rapporteres_som: "påløpt vs. budsjett"   # eller: prognose vs. ramme
  kilde_dokument: "[FYLL INN]"  # filnavnmønster, f.eks. "okonomirapport-*.xlsx"

rapport:
  ukedag: fredag
  klokkeslett: "14:00"
  maks_punkter_per_seksjon: 5
  maks_ord_per_punkt: 25
  mottakere: ["[FYLL INN]"]

kanaler:
  epost_label: "[FYLL INN]"     # Gmail-label satt av filter
  drive_mappe: "[FYLL INN]"     # hvis Drive brukes i stedet for lokal disk
  tale_sprak: "no"

terminologi:                     # sikrer at fagbegreper ikke omskrives
  - "avvik"
  - "endringsmelding"
  - "RIB"
  - "RIE"
  - "[FYLL INN flere]"
```

---

## 4. Kildehierarki og evidensregler

Dette er systemets viktigste logikk. Implementer det som en eksplisitt sjekk, ikke som en tone-instruks.

| Nivå | Kilde | Status | Kan brukes til |
|---|---|---|---|
| 1 | Dokument/vedlegg (økonomirapport, protokoll, tegning) | **Fakta** | Alle seksjoner, inkl. tall |
| 2 | E-post | **Fakta med avsenderkontekst** | Alle seksjoner. Tall kun hvis avsender er kilden til tallet |
| 3 | Tale/transkripsjon | **Signal, ikke fakta** | Risiko, tidlige varsler, kontekst |

**Harde regler:**

1. **Tall fra tale blir aldri budsjettall.** «Vi ligger vel 300 000 over på ventilasjon» → føres som risikopunkt med formuleringen «Muntlig indikasjon om overskridelse på ventilasjon; ikke dokumentert». Aldri inn i budsjettseksjonen.
2. **Ingen syntese på tvers av nivåer uten merking.** Hvis en påstand bygger på tale, merkes punktet `(muntlig)`.
3. **Avvik oppgraderes ikke.** En muntlig antydning om forsinkelse blir ikke til «avvik» med mindre det står i dokument eller e-post, eller brukeren eksplisitt sier ordet «avvik» i opptaket.
4. **Ingen utledning av årsak.** Systemet rapporterer hva som er observert, ikke hvorfor, med mindre årsaken er oppgitt i kilden.
5. **Ved motstrid vinner høyeste nivå**, og motstriden føres opp i Spør-meg-listen.

---

## 5. Pipeline — seks steg

Kjør stegene i rekkefølge. Ikke slå dem sammen til én prompt; hvert steg har eget output som mates videre.

**Steg 1 — Innlesing og inventar**
Les alle filer i `inn/uke-NN/`. Bygg en liste: `{kilde_id, kanal, filnavn, dato, avsender, nivå}`. Skriv antall kilder per kanal til loggen. Hvis en kanal er tom, noter det — det er i seg selv informasjon (f.eks. ingen taleopptak denne uken).

**Steg 2 — Utdrag**
Trekk ut hver enkeltstående påstand som eget element: `{utsagn, kilde_id, nivå, seksjonsforslag}`. Ett utsagn = én ting. Ikke oppsummer på dette stadiet — dette er ren nedbryting. Taleopptak gir typisk 20–60 elementer og er usortert; det er forventet.

**Steg 3 — Sortering**
Merk hvert element med én av: `PROGRAM`, `BUDSJETT`, `RISIKO`, `DESIGN`, `UPLASSERT`. Elementer som ikke klart hører hjemme i én av de fire, går til `UPLASSERT` og skrives til `registre/uplassert.md` — de skal ikke presses inn i en seksjon.

**Steg 4 — Deduplisering**
Slå sammen elementer som beskriver samme sak. Behold høyeste kildenivå som primærkilde, men behold referanse til alle. Hvis samme sak er nevnt både i e-post og tale, er det et styrkesignal — noter `(bekreftet i flere kanaler)`.

**Steg 5 — Delta mot forrige uke**
Les forrige ukes rapport og begge registrene. For hvert element, avgjør:
- `NY` — ikke nevnt før
- `ENDRET` — nevnt før, men status/tall/omfang er annerledes
- `UENDRET` — samme som forrige uke
- `LUKKET` — tidligere åpent punkt som nå er avsluttet

**Kun `NY`, `ENDRET` og `LUKKET` kommer med i rapporten.** `UENDRET` utelates fullstendig — det er derfor rapporten holder seg kort. Åpne, uendrede punkter lever videre i risikoregisteret der de hører hjemme.

**Steg 6 — Skriving og registeroppdatering**
Skriv rapporten etter malen i §6. Oppdater deretter registrene (§7, §8). Skriv én linje til `logg/kjoringer.log`.

---

## 6. Rapportmal — `config/rapportmal.md`

Bruk denne eksakt. Ingen ekstra seksjoner, ingen innledning, ingen oppsummering til slutt.

```markdown
# Ukesrapport — {prosjektnavn} — uke {NN} ({dato_fra}–{dato_til})

Kilder: {n} e-post, {n} vedlegg, {n} taleopptak

## Program
- {punkt}

## Budsjett
- {punkt}

## Nøkkelrisiko
- {punkt} [{RISIKO-ID}]

## Designbeslutninger
- {punkt} [{BESL-ID}]

## Uklart / trenger bekreftelse
- {spørsmål}
```

**Utfyllingsregler:**
- Maks 5 punkter per seksjon. Hvis flere kvalifiserer, ta de fem med størst konsekvens og legg resten i registeret.
- Maks 25 ord per punkt. Ett punkt = én sak.
- Tom seksjon skrives som: `- Ingen endring siden uke {NN-1}.` Ikke noe annet.
- Punkter som bygger på tale merkes med `(muntlig)` til slutt.
- `LUKKET`-punkter skrives med prefiks `Lukket:`.
- Ingen adjektiver om fremdrift («god», «tilfredsstillende», «utfordrende») med mindre de står i kilden.
- Ingen prosentanslag som ikke står i et dokument.

---

## 7. Risikoregister — `registre/risikoregister.csv`

```csv
id,tittel,beskrivelse,forst_observert,siste_bevegelse,status,kildenivaa,eier,konsekvens
R-001,Ventilasjon leveranse,Leverandør varsler 3 ukers forsinkelse,2026-08-24,2026-09-04,åpen,1,PL,fremdrift
```

- `id`: `R-` + løpenummer, tildeles én gang og gjenbrukes aldri.
- `status`: `åpen` | `overvåkes` | `eskalert` | `lukket`
- `kildenivaa`: 1–3 etter §4. Et punkt på nivå 3 kan ikke ha status `eskalert` uten at brukeren bekrefter.
- `siste_bevegelse` oppdateres kun når noe faktisk endrer seg — ikke ved hver kjøring.

## 8. Beslutningslogg — `registre/beslutningslogg.csv`

```csv
id,dato,beslutning,begrunnelse,besluttet_av,erstatter,kilde
B-014,2026-09-02,Bytte til systemhimling i fellesareal,Kostnad og leveringstid,Byggherre,B-009,epost/2026-09-02-himling.eml
```

- `begrunnelse` fylles kun ut hvis den står i kilden. Er den ikke oppgitt, skriv `ikke oppgitt` — ikke rekonstruer den.
- `erstatter` peker til tidligere beslutnings-ID hvis denne overstyrer noe. Dette er hele poenget med loggen: om seks måneder skal kjeden kunne leses baklengs.

---

## 9. Stilregler (harde)

Disse gjelder alt som skrives til rapporten.

**Forbudt:**
- Innledende setninger («Denne uken har vært preget av…»)
- Avsluttende oppsummering eller «veien videre»
- Vurderende adjektiv som ikke står i kilden
- Å fylle en seksjon for symmetriens skyld
- Å gjenta punkter fra forrige uke som ikke har endret seg
- Å utlede årsakssammenheng som ikke er oppgitt
- Å konvertere muntlige anslag til tall

**Påkrevd:**
- Hvert punkt skal kunne spores til minst én `kilde_id`
- Usikkerhet uttrykkes ved plassering i «Uklart», ikke ved forbehold i punktet
- Fagterminologi fra `config/prosjekt.yaml` gjengis uendret

**Selvtest før levering:** for hvert punkt i rapporten, still spørsmålet «hvilken fil kom dette fra, og står det der eksplisitt?». Punkter uten svar strykes.

---

## 10. Automatisering

Bygg dette i to nivåer.

**Nivå A — planlagt kjøring (bygg dette først)**
Sett opp en gjentakende oppgave som kjører `{rapport.ukedag}` kl. `{rapport.klokkeslett}`:
1. Finn inneværende ISO-uke
2. Kjør pipelinen §5
3. Skriv rapport + oppdater registre
4. Varsle brukeren med rapporten som vedlegg/lenke

*I Cowork:* opprett dette som en tilbakevendende oppgave.
*I Claude Code:* lag et kjørbart skript + cron-oppføring (`0 14 * * 5`), og en `--week` flagg for manuell kjøring på en gitt uke.

**Nivå B — automatisk innsamling**
- Gmail-filter på avsender/emne → prosjektlabel → ingen manuell tagging
- Vedlegg rutes til `inn/uke-NN/vedlegg/`
- Telefonsnarvei: opptak → transkripsjon → lagres som `tale-YYYY-MM-DD-HHMM.txt` i riktig ukemappe

Hendelsesdrevet trigging («kjør når e-post ankommer») bygges ikke i v1. Ukesrytmen er et bevisst valg: rapporten handler om delta over en uke, ikke om enkelthendelser.

---

## 11. Ekstra for Claude Code (kodevarianten)

Hvis dette bygges som kode, lever følgende:

```
ukespuls/
├── src/
│   ├── ingest.py        # steg 1–2
│   ├── classify.py      # steg 3–4
│   ├── delta.py         # steg 5
│   ├── render.py        # steg 6
│   ├── registers.py     # CSV-lesing/skriving med ID-tildeling
│   └── cli.py           # ukespuls run --project X --week 2026-36
├── schemas/
│   └── report.json      # structured output-skjema (under)
├── tests/
│   └── fixtures/uke-2026-99/   # syntetisk testuke, §12
└── README.md
```

**Structured output-skjema** (bruk dette mot Messages-endepunktet, ikke fritekst):

```json
{
  "uke": "2026-36",
  "kilder": {"epost": 0, "vedlegg": 0, "tale": 0},
  "seksjoner": {
    "program": [{"tekst": "", "kilde_ids": [], "delta": "NY|ENDRET|LUKKET", "muntlig": false}],
    "budsjett": [],
    "risiko": [{"tekst": "", "risiko_id": "", "kilde_ids": [], "delta": "", "muntlig": false}],
    "design": [{"tekst": "", "beslutning_id": "", "kilde_ids": [], "delta": "", "muntlig": false}]
  },
  "uklart": [{"sporsmal": "", "kilde_ids": []}],
  "uplassert": [{"tekst": "", "kilde_ids": []}]
}
```

Renderingen til markdown gjøres i kode, ikke av modellen. Da kan ikke malen drifte mellom uker.

Valider hvert punkt mot `maks_ord_per_punkt` i kode og avvis for lange punkter tilbake til modellen med én omskrivingsrunde.

---

## 12. Testdata og akseptansetest

Lag en syntetisk testuke `tests/fixtures/uke-2026-99/` som inneholder:
- 6 e-poster, hvorav 2 om samme sak (tester dedup)
- 1 økonomirapport med et konkret tall
- 1 taleopptak-transkripsjon på ~400 ord som er usortert, hopper mellom tema, gjentar seg selv, og inneholder **ett muntlig tallanslag som motsier økonomirapporten** (tester §4.1 og §4.5)
- 1 e-post som ikke hører hjemme i noen seksjon (tester `uplassert`)
- En «forrige uke»-rapport der 3 punkter er uendret (tester at de ikke gjentas)

**Akseptansekriterier — alle må passere:**
1. Det muntlige tallet står ikke i budsjettseksjonen
2. Motstriden mellom tale og økonomirapport står i «Uklart»
3. De 3 uendrede punktene fra forrige uke er ikke med
4. Den irrelevante e-posten ligger i `uplassert.md`, ikke i rapporten
5. Ingen seksjon overstiger 5 punkter, intet punkt overstiger 25 ord
6. De to e-postene om samme sak er slått sammen til ett punkt
7. Hele rapporten er under én A4-side
8. Hvert punkt kan spores til en fil i `inn/`

Kjør testen og vis resultatet før du erklærer systemet ferdig.

---

## 13. Definisjon av ferdig

- [ ] Mappestruktur opprettet, `prosjekt.yaml` fylt ut
- [ ] Pipeline kjører ende-til-ende på testuken
- [ ] Alle 8 akseptansekriterier passerer
- [ ] Planlagt ukentlig kjøring satt opp og verifisert
- [ ] Registre oppdateres inkrementelt over to påfølgende kjøringer uten at ID-er endres
- [ ] `README.md` beskriver hvordan man legger inn en ny uke manuelt og kjører på nytt

---

## 14. Spør brukeren om dette før du starter

Samle disse i **ett** spørsmål, ikke ett om gangen:
1. Alle `[FYLL INN]`-felt i `config/prosjekt.yaml`
2. Lokal mappe eller Google Drive?
3. Skal budsjett rapporteres som påløpt-vs-budsjett eller prognose-vs-ramme?
4. Finnes en eksisterende ukesrapport å matche stilen mot? Be om én.
