"""UKESPULS - kjorer hele pipelinen i seks steg. Bruk: python3 kjor.py [uke]"""
import datetime, sys
import steg1_inventar, steg2_utdrag, steg3_sortering, steg4_dedup, steg5_delta, steg6_skriving

def gjeldende_uke():
    aar, uke, _ = datetime.date.today().isocalendar()
    return f"{aar}-{uke:02d}"

def main():
    uke = sys.argv[1] if len(sys.argv) > 1 else gjeldende_uke()
    print(f"UKESPULS - uke {uke}")
    for nr, (navn, modul) in enumerate([
        ("Inventar", steg1_inventar), ("Utdrag", steg2_utdrag), ("Sortering", steg3_sortering),
        ("Deduplisering", steg4_dedup), ("Delta", steg5_delta), ("Skriving", steg6_skriving)], 1):
        print(f"\nSteg {nr}: {navn}")
        modul.kjor(uke)
    print("\nFerdig.")

if __name__ == "__main__":
    main()
