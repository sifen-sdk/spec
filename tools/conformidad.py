#!/usr/bin/env python3
"""Verifica los casos de conformidad que se pueden calcular sin XML ni firma (CDC y QR).

Es una implementación de referencia mínima, solo para comprobar que los casos de conformidad/ son coherentes
consigo mismos. No es un SDK. Sin dependencias: biblioteca estándar de Python 3.
"""
import glob
import hashlib
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QR_BASE = {
    "produccion": "https://ekuatia.set.gov.py/consultas/qr?",
    "test": "https://ekuatia.set.gov.py/consultas-test/qr?",
}
ORDEN_CDC = [
    "tipoDocumento", "rucEmisor", "digitoVerificadorRuc", "establecimiento", "puntoExpedicion", "numeroDocumento",
    "tipoContribuyente", "fechaEmision", "tipoEmision", "codigoSeguridad",
]
ORDEN_QR = ["nVersion", "Id", "dFeEmiDE", "dRucRec", "dTotGralOpe", "dTotIVA", "cItems", "DigestValue", "IdCSC"]


def modulo11(digitos):
    """Dígito verificador módulo 11 con pesos 2 a 11 desde la derecha."""
    total, peso = 0, 2
    for ch in reversed(digitos):
        total += int(ch) * peso
        peso = 2 if peso == 11 else peso + 1
    resto = total % 11
    return "0" if resto <= 1 else str(11 - resto)


def caso_cdc(c):
    base = "".join(c["entrada"][k] for k in ORDEN_CDC)
    dv = modulo11(base)
    cdc = base + dv
    kude = " ".join(cdc[i:i + 4] for i in range(0, len(cdc), 4))
    return {"cdc": cdc, "digitoVerificador": dv, "representacionKude": kude}


def caso_qr(c):
    e = dict(c["entrada"])
    e["dFeEmiDE"] = e["dFeEmiDE"].encode("utf-8").hex()
    e["DigestValue"] = e["DigestValue"].encode("utf-8").hex()
    datos = "&".join(f"{k}={e[k]}" for k in ORDEN_QR)
    h = hashlib.sha256((datos + e["CSC"]).encode("utf-8")).hexdigest()
    url = QR_BASE[e["ambiente"]] + datos + "&cHashQR=" + h
    return {"datos": datos, "cHashQR": h, "url": url, "dCarQR": url.replace("&", "&amp;")}


def main():
    fallas, total = [], 0
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "conformidad", "*", "*.json"))):
        c = json.load(open(ruta, encoding="utf-8"))
        calc = {"cdc": caso_cdc, "qr": caso_qr}.get(c.get("tipo"))
        if calc is None:
            continue
        total += 1
        obtenido = calc(c)
        for clave, esperado in c["esperado"].items():
            if obtenido.get(clave) != esperado:
                fallas.append(f"{os.path.relpath(ruta, RAIZ)}: {clave}: esperado {esperado!r}, obtenido {obtenido.get(clave)!r}")
    if fallas:
        print("\n".join(fallas))
        return 1
    print(f"OK: {total} casos de conformidad verificados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
