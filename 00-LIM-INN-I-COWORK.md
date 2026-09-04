# Oppdrag: bygg og kjør UKESPULS

Du skal bygge et system som samler prosjektinformasjon fra flere kanaler gjennom uken og produserer én kort ukesrapport pluss to levende registre. Deretter skal du kjøre det på testdataene som allerede ligger klare, og vise meg resultatet.

**Ikke still meg spørsmål før du starter.** All konfigurasjon står nedenfor. Jobb deg gjennom § 1–7 i rekkefølge og lever det som står i § 7.

---

## 1. Utgangspunkt

Testdataene ligger i `demo/`. Strukturen er:

```
demo/
├── inn/uke-2026-36/
│   ├── epost/        6 filer
│   ├── vedlegg/      okonomirapport-2026-08.csv
│   └── tale/         tale-2026-09-03-1645.txt
├── ut/
│   └── ukesrapport-2026-35.md     ← forrige ukes rapport
└── registre/
    ├── risikoregister.csv
    ├── beslutningslogg.csv
    └── uplassert.md
```

Kopier denne mappen til der du jobber, og behold strukturen. Alt du produserer skal skrives inn i den.

## 2. Prosjektkonfigurasjon

Opprett `config/prosjekt.yaml` med nøyaktig dette innholdet:

```yaml
prosjekt:
  navn: "Bjørnheia skole – nybygg og rehabilitering"
  slug: "bjornheia-skole"
  prosjektleder: "Marte Solvang"
  kontraktsform: "Totalentreprise NS 8407"
  oppstart: "2026-02-16"
  planlagt_ferdig: "2027-08-13"

budsjett:
  totalramme: 175400000
  valuta: NOK
  rapporteres_som: "påløpt vs. budsjett, med prognose mot ramme"
  kilde_dokument: "okonomirapport-*.csv"

rapport:
  ukedag: fredag
  klokkeslett: "14:00"
  maks_punkter_per_seksjon: 5
  maks_ord_per_punkt: 25

kanaler:
  tale_sprak: "no"

terminologi:
  - "avvik"
  - "endringsmelding"
  - "tett bygg"
  - "RIB"
  - "RIE"
  - "vernerunde"
  - "riggområde"
  - "prognose"
```

## 3. Kildehierarki — systemets viktigste regel

| Nivå | Kilde | Status | Kan brukes til |
|---|---|---|---|
| 1 | Vedlegg/dokument | **Fakta** | Alle seksjoner, inkludert tall |
| 2 | E-post | **Fakta med avsenderkontekst** | Alle seksjoner. Tall kun når avsender er kilden til tallet |
| 3 | Tale | **Signal, ikke fakta** | Risiko, tidlige varsler, kontekst |

Harde regler:

1. **Tall fra tale blir aldri budsjettall.** Et muntlig anslag føres som risikopunkt formulert som en indikasjon, aldri som en budsjettlinje.
2. Punkter som bygger på tale merkes `(muntlig)` til slutt.
3. **Avvik oppgraderes ikke.** En muntlig antydning blir ikke «avvik» med mindre det står i dokument eller e-post, eller taleren sier ordet selv.
4. Ingen utledning av årsak som ikke er oppgitt i kilden.
5. Ved motstrid vinner høyeste nivå — og motstriden føres i «Uklart».

## 4. Pipeline — seks steg, kjør dem separat

1. **Inventar.** Les alle filer i ukemappen. Bygg liste: `{kilde_id, kanal, filnavn, dato, avsender, nivå}`.
2. **Utdrag.** Bryt hver kilde ned i enkeltstående utsagn. Ett utsagn = én sak. Ikke oppsummer her. Taleopptaket gir mange og usorterte utsagn — det er forventet.
3. **Sortering.** Merk hvert utsagn `PROGRAM`, `BUDSJETT`, `RISIKO`, `DESIGN` eller `UPLASSERT`. Det som ikke klart hører hjemme, skal til `UPLASSERT` — ikke presses inn i en seksjon.
4. **Deduplisering.** Slå sammen utsagn om samme sak. Behold høyeste kildenivå som primærkilde. Nevnt i flere kanaler markeres `(bekreftet i flere kanaler)`.
5. **Delta.** Sammenlign mot `ut/ukesrapport-2026-35.md` og begge registrene. Merk hvert punkt `NY`, `ENDRET`, `UENDRET` eller `LUKKET`. **Kun NY, ENDRET og LUKKET kommer med i rapporten.** UENDRET utelates helt — det lever videre i risikoregisteret.
6. **Skriving.** Rapport etter malen i § 5, deretter oppdater registrene.

## 5. Rapportmal — bruk eksakt

```markdown
# Ukesrapport — Bjørnheia skole — uke 36 (31.08–04.09.2026)

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

**Stilregler — brudd regnes som feil, ikke smakssak:**

Forbudt:
- Innledende setninger av typen «Denne uken har vært preget av…»
- Avsluttende oppsummering eller «veien videre»
- Vurderende adjektiv som ikke står i kilden («god fremdrift», «utfordrende»)
- Å fylle en seksjon for symmetriens skyld
- Å gjenta punkter fra forrige uke som ikke har endret seg
- Å konvertere muntlige anslag til tall

Påkrevd:
- Maks 5 punkter per seksjon, maks 25 ord per punkt
- Tom seksjon skrives kun som: `- Ingen endring siden uke 35.`
- Hvert punkt skal kunne spores til minst én kildefil
- Usikkerhet uttrykkes ved plassering i «Uklart», ikke ved forbehold inne i punktet
- `LUKKET`-punkter får prefiks `Lukket:`

Selvtest før levering: for hvert punkt, spør «hvilken fil kom dette fra, og står det der eksplisitt?». Punkter uten svar strykes.

## 6. Registre — oppdater, ikke skriv om

**`registre/risikoregister.csv`** — kolonner: `id,tittel,beskrivelse,forst_observert,siste_bevegelse,status,kildenivaa,eier,konsekvens`
- ID-er (`R-nnn`) tildeles én gang og gjenbrukes aldri.
- `status`: `apen` | `overvakes` | `eskalert` | `lukket`
- Et punkt på kildenivå 3 kan ikke settes til `eskalert`.
- `siste_bevegelse` oppdateres kun når noe faktisk endrer seg.

**`registre/beslutningslogg.csv`** — kolonner: `id,dato,beslutning,begrunnelse,besluttet_av,erstatter,kilde`
- `begrunnelse` fylles kun ut når den står i kilden, ellers `ikke oppgitt`.
- `erstatter` peker til tidligere beslutnings-ID når denne overstyrer noe.

**`registre/uplassert.md`** — legg til en seksjon `## Uke 36` med innhold som ikke hørte hjemme noe sted.

## 7. Dette skal du levere

1. `config/prosjekt.yaml` og `config/rapportmal.md`
2. `ut/ukesrapport-2026-36.md`
3. Oppdaterte `registre/risikoregister.csv` og `registre/beslutningslogg.csv`
4. Oppdatert `registre/uplassert.md`
5. `logg/kjoringer.log` med én linje for kjøringen
6. `README.md` som forklarer hvordan jeg legger inn en ny uke og kjører på nytt
7. **En egenkontroll**: gå gjennom de åtte kriteriene i § 8 og skriv `BESTÅTT`/`IKKE BESTÅTT` for hvert, med begrunnelse. Retter du noe, kjør kontrollen på nytt.

## 8. Akseptansekriterier

1. Det muntlige anslaget om ventilasjonskostnad står **ikke** i budsjettseksjonen
2. Motstriden mellom taleopptaket og økonomirapporten står i «Uklart»
3. Uendrede punkter fra uke 35 er ikke gjentatt
4. E-posten om julebord ligger i `uplassert.md`, ikke i rapporten
5. De to e-postene om himling er slått sammen til ett punkt
6. Ingen seksjon har over 5 punkter, intet punkt over 25 ord
7. Hele rapporten er under én A4-side
8. Hvert punkt kan spores til en fil i `inn/uke-2026-36/`

## 9. Når alt er bestått

Sett opp systemet som en gjentakende oppgave hver fredag kl. 14:00, som:
1. finner inneværende ISO-uke,
2. kjører pipelinen i § 4 på `inn/uke-<år>-<uke>/`,
3. skriver rapport og oppdaterer registrene,
4. varsler meg når den er ferdig.

Opprett samtidig neste ukemappe (`inn/uke-2026-37/` med undermappene `epost/`, `vedlegg/`, `tale/`) så den står klar.
