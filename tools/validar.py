#!/usr/bin/env python3
"""Valida la especificación. Sin dependencias: solo la biblioteca estándar de Python 3.

Uso:  python3 tools/validar.py              valida todo lo cargado
      python3 tools/validar.py --cobertura  además exige que todo elemento de los esquemas cubiertos tenga su campo

El formato que se valida está descrito en FORMATO.md. Este programa es la referencia: si FORMATO.md y este
programa no coinciden, es un error de FORMATO.md.
"""
import glob
import hashlib
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errores = []

DOCS = re.compile(r"^(MT150|NT0(0[1-9]|1[0-9]|2[0-7])|XSD|GUIA-MP|GUIA-PRUEBAS|DEC872|RG[0-9]+-[0-9]{4})$")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NOMBRE = re.compile(r"^[a-z][a-zA-Z0-9]*$")
TIPOS_CAMPO = {"grupo", "alfanumerico", "numerico", "fecha", "fecha_hora", "binario", "xml"}
ESTADOS = {"vigente", "futuro", "eliminado"}
TIPOS_REGLA = {"obligatorio", "opcional", "condicional", "prohibido", "aritmetica", "formato", "dependencia"}
OPS_VALOR = {"igual", "distinto", "mayor", "mayor_igual", "menor", "menor_igual"}
OPS_LISTA = {"en", "no_en"}
OPS_SIN = {"presente", "ausente"}
CUANTIFICADORES = {"alguno", "todos"}
CLASES = {"aprobacion", "aprobacion_con_observacion", "rechazo", "en_proceso", "transitorio", "bloqueo", "informativo"}


def err(archivo, msg):
    errores.append(f"{os.path.relpath(archivo, RAIZ)}: {msg}")


def lista(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def cargar(ruta):
    try:
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        err(ruta, f"no es JSON válido: {e}")
        return None


def datos(carpeta):
    return sorted(glob.glob(os.path.join(RAIZ, carpeta, "**", "*.json"), recursive=True))


def validar_fuentes(archivo, donde, fuentes):
    if not isinstance(fuentes, list) or not fuentes:
        err(archivo, f"{donde}: falta 'fuentes' (toda entrada cita su fuente oficial)")
        return
    for f in fuentes:
        if not isinstance(f, dict) or not DOCS.match(str(f.get("doc", ""))):
            err(archivo, f"{donde}: fuente con 'doc' desconocido: {f!r}")
        elif not str(f.get("ref", "")).strip():
            err(archivo, f"{donde}: fuente sin 'ref' (campo, validación, sección o archivo): {f!r}")


def validar_vigencia(archivo, donde, v):
    if v is None:
        return
    if not isinstance(v, dict) or not set(v) <= {"desde", "hasta"}:
        err(archivo, f"{donde}: 'vigencia' admite solo 'desde' y 'hasta'")
        return
    for extremo, porambiente in v.items():
        if not isinstance(porambiente, dict) or not set(porambiente) <= {"test", "produccion"} or not porambiente:
            err(archivo, f"{donde}: vigencia.{extremo} debe indicar 'test' y/o 'produccion'")
            continue
        for amb, fecha in porambiente.items():
            if fecha is not None and not FECHA.match(str(fecha)):
                err(archivo, f"{donde}: vigencia.{extremo}.{amb} debe ser AAAA-MM-DD o null")


def validar_condicion(archivo, donde, c, ids):
    if not isinstance(c, dict) or len(c) == 0:
        err(archivo, f"{donde}: condición vacía o mal formada")
        return
    if "todas" in c or "alguna" in c:
        clave = "todas" if "todas" in c else "alguna"
        if len(c) != 1 or not isinstance(c[clave], list) or len(c[clave]) < 2:
            err(archivo, f"{donde}: '{clave}' lleva una lista de al menos dos condiciones y nada más")
            return
        for sub in c[clave]:
            validar_condicion(archivo, donde, sub, ids)
        return
    if "no" in c:
        if len(c) != 1:
            err(archivo, f"{donde}: 'no' lleva una sola condición y nada más")
            return
        validar_condicion(archivo, donde, c["no"], ids)
        return
    campo, op = c.get("campo"), c.get("op")
    if "cuantificador" in c:
        if c["cuantificador"] not in CUANTIFICADORES:
            err(archivo, f"{donde}: cuantificador desconocido {c['cuantificador']!r}")
        c = {k: v for k, v in c.items() if k != "cuantificador"}
    if campo not in ids:
        err(archivo, f"{donde}: la condición usa un campo inexistente: {campo!r}")
    if op in OPS_VALOR:
        if "valor" not in c or isinstance(c["valor"], (list, dict)) or set(c) != {"campo", "op", "valor"}:
            err(archivo, f"{donde}: '{op}' lleva exactamente campo, op y valor")
    elif op in OPS_LISTA:
        if not isinstance(c.get("valores"), list) or not c["valores"] or set(c) != {"campo", "op", "valores"}:
            err(archivo, f"{donde}: '{op}' lleva exactamente campo, op y valores (lista no vacía)")
    elif op in OPS_SIN:
        if set(c) != {"campo", "op"}:
            err(archivo, f"{donde}: '{op}' lleva exactamente campo y op")
    else:
        err(archivo, f"{donde}: operador desconocido: {op!r}")


def elementos_xsd(arbol):
    """Nombre de elemento -> conjunto de archivos donde aparece."""
    out = {}

    def visitar(archivo, lista):
        for h in lista:
            out.setdefault(h["nombre"], set()).add(archivo)
            visitar(archivo, h.get("hijos", []))

    for archivo, d in arbol.items():
        visitar(archivo, d.get("elementos", []))
        for t in d.get("tipos_complejos", {}).values():
            visitar(archivo, t.get("hijos", []))
    return out


def main():
    cobertura = "--cobertura" in sys.argv

    # --- esquemas oficiales: el índice coincide con los archivos -------------------------------------------------
    indice_ruta = os.path.join(RAIZ, "xsd", "indice.json")
    indice = cargar(indice_ruta) or {"archivos": []}
    en_indice = set()
    for a in indice.get("archivos", []):
        en_indice.add(a.get("archivo"))
        ruta = os.path.join(RAIZ, "xsd", "oficial", str(a.get("archivo")))
        if not os.path.exists(ruta):
            err(indice_ruta, f"falta el archivo {a.get('archivo')}")
            continue
        with open(ruta, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != a.get("sha256"):
                err(indice_ruta, f"{a.get('archivo')}: el contenido no coincide con el sha256 del índice")
    for f in glob.glob(os.path.join(RAIZ, "xsd", "oficial", "*")):
        if os.path.basename(f) not in en_indice:
            err(indice_ruta, f"{os.path.basename(f)} está en xsd/oficial pero no en el índice")

    arbol_ruta = os.path.join(RAIZ, "xsd", "arbol.json")
    arbol = cargar(arbol_ruta) if os.path.exists(arbol_ruta) else {}
    xsd = elementos_xsd(arbol or {})

    # --- contradicciones ---------------------------------------------------------------------------------------
    contra_ruta = os.path.join(RAIZ, "contradicciones.md")
    contradicciones = set()
    for ruta in [contra_ruta] + sorted(glob.glob(os.path.join(RAIZ, "contradicciones.d", "*.md"))):
        for cid in re.findall(r"^#{2,3} (C-\d{3})\b", open(ruta, encoding="utf-8").read(), re.M):
            if cid in contradicciones:
                err(ruta, f"contradicción repetida: {cid}")
            contradicciones.add(cid)

    # --- catálogos ---------------------------------------------------------------------------------------------
    catalogos = set()
    for ruta in datos("catalogos"):
        d = cargar(ruta)
        if d is None:
            continue
        cid = d.get("id")
        if not cid or cid != os.path.splitext(os.path.basename(ruta))[0]:
            err(ruta, "el 'id' del catálogo debe coincidir con el nombre del archivo")
        catalogos.add(cid)
        validar_fuentes(ruta, "catálogo", d.get("fuentes"))
        if not FECHA.match(str(d.get("tomado", ""))):
            err(ruta, "falta 'tomado' (fecha AAAA-MM-DD en que se tomó de la fuente)")
        vistos = set()
        for e in d.get("entradas", []):
            clave = (str(e.get("padre", "")), str(e.get("codigo")))
            if e.get("codigo") is None or "descripcion" not in e:
                err(ruta, f"entrada sin 'codigo' o 'descripcion': {e!r}")
            if clave in vistos:
                err(ruta, f"código repetido: {clave}")
            vistos.add(clave)
            validar_vigencia(ruta, f"código {e.get('codigo')}", e.get("vigencia"))
        if not d.get("entradas"):
            err(ruta, "catálogo sin 'entradas'")

    # --- campos ------------------------------------------------------------------------------------------------
    campos = {}
    origen = {}
    por_archivo = []
    for ruta in datos("campos"):
        d = cargar(ruta)
        if d is None:
            continue
        if not d.get("esquemas") or not all(e in (arbol or {}) for e in d.get("esquemas", [])):
            err(ruta, "'esquemas' debe listar archivos existentes de xsd/oficial")
        por_archivo.append((ruta, d))
        for c in d.get("campos", []):
            cid = c.get("id")
            donde = f"campo {cid}"
            if not cid or not isinstance(cid, str):
                err(ruta, f"campo sin 'id': {c!r}")
                continue
            if cid in campos:
                err(ruta, f"{donde}: id repetido (ya está en {os.path.relpath(origen[cid], RAIZ)})")
            campos[cid] = c
            origen[cid] = ruta
            for k in ("xml", "nombre", "tipo", "ocurrencia", "descripcion"):
                if not str(c.get(k, "")).strip():
                    err(ruta, f"{donde}: falta '{k}'")
            if c.get("tipo") not in TIPOS_CAMPO:
                err(ruta, f"{donde}: tipo desconocido {c.get('tipo')!r}")
            if not NOMBRE.match(str(c.get("nombre", ""))):
                err(ruta, f"{donde}: 'nombre' debe ser lowerCamelCase en inglés: {c.get('nombre')!r}")
            if not re.match(r"^\d+-(\d+|N)$", str(c.get("ocurrencia", ""))):
                err(ruta, f"{donde}: 'ocurrencia' debe tener la forma 0-1, 1-1, 1-999 o 0-N")
            if c.get("estado", "vigente") not in ESTADOS:
                err(ruta, f"{donde}: estado desconocido {c.get('estado')!r}")
            if c.get("catalogo") is not None and c["catalogo"] not in catalogos:
                err(ruta, f"{donde}: catálogo inexistente {c['catalogo']!r}")
            for cc in lista(c.get("contradiccion")):
                if cc not in contradicciones:
                    err(ruta, f"{donde}: contradicción inexistente {cc!r}")
            validar_fuentes(ruta, donde, c.get("fuentes"))
            validar_vigencia(ruta, donde, c.get("vigencia"))
            en_xsd = any(e in xsd.get(c.get("xml"), set()) for e in d.get("esquemas", []))
            if c.get("estado", "vigente") == "vigente" and not en_xsd and not c.get("contradiccion"):
                err(ruta, f"{donde}: '{c.get('xml')}' no existe en {d.get('esquemas')}; si es correcto, "
                          "registrá la contradicción y citála en 'contradiccion'")

    for ruta, d in por_archivo:
        nombres = {}
        for c in d.get("campos", []):
            padre = c.get("padre")
            if padre is not None and padre not in campos:
                err(ruta, f"campo {c.get('id')}: padre inexistente {padre!r}")
            clave = (padre, c.get("nombre"))
            if clave in nombres:
                err(ruta, f"campo {c.get('id')}: el nombre '{c.get('nombre')}' se repite bajo el mismo padre "
                          f"(también en {nombres[clave]})")
            nombres[clave] = c.get("id")

    # --- catálogos: los campos que declaran usar existen -------------------------------------------------------
    for ruta in datos("catalogos"):
        d = cargar(ruta) or {}
        for cid in d.get("campos", []):
            if cid not in campos:
                err(ruta, f"'campos' cita un campo inexistente: {cid!r}")
        for cod, des in (d.get("descripciones") or {}).items():
            if cod not in campos or des not in campos:
                err(ruta, f"'descripciones' cita un campo inexistente: {cod!r} -> {des!r}")

    # --- evidencia ---------------------------------------------------------------------------------------------
    evidencias = set()
    dir_evidencia = os.path.join(RAIZ, "evidencia")
    if os.path.isdir(dir_evidencia):
        for f in sorted(os.listdir(dir_evidencia)):
            m = re.match(r"^(E-\d{3})-[a-z0-9-]+\.md$", f)
            if not m:
                err(os.path.join(dir_evidencia, f), "el nombre debe ser E-nnn-<tema>.md")
            elif m.group(1) in evidencias:
                err(os.path.join(dir_evidencia, f), f"id de evidencia repetido {m.group(1)}")
            else:
                evidencias.add(m.group(1))

    # --- reglas ------------------------------------------------------------------------------------------------
    reglas = set()
    for ruta in datos("reglas"):
        d = cargar(ruta)
        if d is None:
            continue
        for r in d.get("reglas", []):
            rid = r.get("id")
            donde = f"regla {rid}"
            if not rid or rid in reglas:
                err(ruta, f"{donde}: falta el id o está repetido")
            reglas.add(rid)
            if r.get("campo") not in campos:
                err(ruta, f"{donde}: campo inexistente {r.get('campo')!r}")
            tipo = r.get("tipo")
            if tipo not in TIPOS_REGLA:
                err(ruta, f"{donde}: tipo desconocido {tipo!r}")
            validar_fuentes(ruta, donde, r.get("fuentes"))
            validar_vigencia(ruta, donde, r.get("vigencia"))
            if not str(r.get("texto", "")).strip():
                err(ruta, f"{donde}: falta 'texto' (qué exige SIFEN, en una frase)")
            cond, no_decl = r.get("condicion"), r.get("no_declarativa", False)
            if cond is not None:
                validar_condicion(ruta, donde, cond, campos)
            if tipo in ("condicional", "prohibido") and cond is None and not no_decl:
                err(ruta, f"{donde}: una regla '{tipo}' lleva 'condicion', o 'no_declarativa': true si no se "
                          "puede expresar")
            if tipo == "aritmetica":
                if not str(r.get("formula", "")).strip():
                    err(ruta, f"{donde}: una regla aritmética lleva 'formula' tal como figura en la fuente")
                for op in r.get("operandos", []):
                    if op not in campos:
                        err(ruta, f"{donde}: operando inexistente {op!r}")
            for cc in lista(r.get("contradiccion")):
                if cc not in contradicciones:
                    err(ruta, f"{donde}: contradicción inexistente {cc!r}")
            desc = r.get("descartada")
            if desc is not None:
                if not isinstance(desc, dict) or set(desc) != {"contradiccion", "evidencia"}:
                    err(ruta, f"{donde}: 'descartada' lleva exactamente 'contradiccion' y 'evidencia'")
                else:
                    if desc["contradiccion"] not in contradicciones:
                        err(ruta, f"{donde}: contradicción inexistente {desc['contradiccion']!r}")
                    if desc["evidencia"] not in evidencias:
                        err(ruta, f"{donde}: evidencia inexistente {desc['evidencia']!r}")

    # --- respuestas --------------------------------------------------------------------------------------------
    vistos = set()
    for ruta in datos("respuestas"):
        d = cargar(ruta)
        if d is None:
            continue
        for r in d.get("respuestas", []):
            clave = (r.get("codigo"), r.get("servicio"))
            donde = f"respuesta {r.get('codigo')}"
            if not re.match(r"^\d{4}$", str(r.get("codigo", ""))):
                err(ruta, f"{donde}: 'codigo' debe tener cuatro dígitos")
            if clave in vistos:
                err(ruta, f"{donde}: repetida para el servicio {r.get('servicio')!r}")
            vistos.add(clave)
            if r.get("clase") not in CLASES:
                err(ruta, f"{donde}: clase desconocida {r.get('clase')!r}")
            if not str(r.get("mensaje", "")).strip():
                err(ruta, f"{donde}: falta 'mensaje'")
            validar_fuentes(ruta, donde, r.get("fuentes"))
            validar_vigencia(ruta, donde, r.get("vigencia"))

    # --- cobertura: todo elemento de los esquemas cubiertos tiene su campo ----------------------------------------
    if cobertura:
        cubiertos = cargar(os.path.join(RAIZ, "xsd", "cobertura.json")) or {}
        con_campo = {}
        for ruta, d in por_archivo:
            for e in d.get("esquemas", []):
                con_campo.setdefault(e, set()).update(c.get("xml") for c in d.get("campos", []))
        todos = set().union(*con_campo.values()) if con_campo else set()
        exceptuados = cubiertos.get("excepciones", {})
        for nombre, contra in exceptuados.items():
            if contra not in contradicciones:
                err(os.path.join(RAIZ, "xsd", "cobertura.json"), f"excepción {nombre}: contradicción inexistente")
        for esquema in cubiertos.get("esquemas", []):
            if esquema not in (arbol or {}):
                err(os.path.join(RAIZ, "xsd", "cobertura.json"), f"esquema inexistente {esquema}")
                continue
            propios = set()

            def visitar(lista):
                for h in lista:
                    propios.add(h["nombre"])
                    visitar(h.get("hijos", []))

            visitar(arbol[esquema].get("elementos", []))
            for t in arbol[esquema].get("tipos_complejos", {}).values():
                visitar(t.get("hijos", []))
            for nombre in sorted(propios):
                if nombre not in todos and nombre not in exceptuados and not nombre.startswith("ds:"):
                    err(os.path.join(RAIZ, "xsd", "oficial", esquema), f"el elemento '{nombre}' no tiene campo")

    if errores:
        print("\n".join(errores))
        print(f"\n{len(errores)} error(es)")
        return 1
    print(f"OK: {len(campos)} campos, {len(reglas)} reglas, {len(catalogos)} catálogos, "
          f"{len(vistos)} respuestas, {len(contradicciones)} contradicciones, {len(en_indice)} esquemas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
