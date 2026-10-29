#!/usr/bin/env python3
"""Sostituisce gli UUID presenti in determinate chiavi di un file JSON,
lasciando invariato tutto il resto del testo."""
import argparse
import json
import re
import uuid
from pathlib import Path

UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
UUID_RE = re.compile(UUID)


def costruisci_regex(chiavi):
    k = "|".join(re.escape(c) for c in chiavi)
    # "chiave" : "uuid"
    singolo = re.compile(rf'("(?:{k})"\s*:\s*")({UUID})(")')
    # "chiave" : [ "uuid", "uuid", ... ]  (opzionale, se qualche chiave contiene liste)
    lista = re.compile(rf'("(?:{k})"\s*:\s*\[)([^\]]*)(\])')
    return singolo, lista


def main():
    p = argparse.ArgumentParser(description="Sostituisce UUID in chiavi JSON preservando il formato")
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("-k", "--chiavi", nargs="+", default=["id_gruppo", "id_atto"],
                   help="chiavi con gli UUID da sostituire (default: id_gruppo id_atto)")
    p.add_argument("--in-place", action="store_true",
                   help="sovrascrive l'originale (default: scrive <nome>.nuovo<ext>)")
    p.add_argument("-m", "--salva-mappa", type=Path,
                   help="salva la mappa vecchio->nuovo in un file JSON")
    args = p.parse_args()

    singolo, lista = costruisci_regex(args.chiavi)
    mappa = {}  # condivisa tra i file

    def nuovo(vecchio):
        chiave = vecchio.lower()
        if chiave not in mappa:
            mappa[chiave] = str(uuid.uuid4())
        n = mappa[chiave]
        return n.upper() if vecchio.isupper() else n  # mantiene il maiuscolo se c'era

    def rimpiazza_singolo(m):
        return m.group(1) + nuovo(m.group(2)) + m.group(3)

    def rimpiazza_lista(m):
        corpo = UUID_RE.sub(lambda u: nuovo(u.group(0)), m.group(2))
        return m.group(1) + corpo + m.group(3)

    for path in args.files:
        # newline="" preserva gli a capo originali (CRLF/LF)
        with open(path, encoding="utf-8", newline="") as f:
            testo = f.read()

        testo_nuovo = singolo.sub(rimpiazza_singolo, testo)
        testo_nuovo = lista.sub(rimpiazza_lista, testo_nuovo)

        json.loads(testo_nuovo)  # controllo: il risultato deve essere ancora JSON valido

        out = path if args.in_place else path.with_name(path.stem + ".nuovo" + path.suffix)
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(testo_nuovo)
        print(f"{path} -> {out}")

    print(f"UUID distinti sostituiti: {len(mappa)}")
    if args.salva_mappa:
        args.salva_mappa.write_text(json.dumps(mappa, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()