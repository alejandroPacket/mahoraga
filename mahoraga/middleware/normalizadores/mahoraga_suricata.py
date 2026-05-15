#!/usr/bin/env python3
"""
MAHORAGA — Normalizador de alertas Suricata
Convierte eventos eve.json de Suricata al schema de entrada de SENTINEL.

Uso:
  python3 mahoraga_suricata.py                  # procesa alertas nuevas en tiempo real
  python3 mahoraga_suricata.py --test           # genera una alerta de prueba
  python3 mahoraga_suricata.py --file eve.json  # procesa un archivo específico
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime

EVE_LOG = "/var/log/suricata/eve.json"
ESTADO_FILE = os.path.expanduser("~/tinyclaw/mahoraga_suricata_estado.json")

# ─────────────────────────────────────────────
# Sanitización anti prompt-injection
# ─────────────────────────────────────────────
PALABRAS_PROHIBIDAS = [
    "ignore", "override", "system", "forget", "pretend",
    "instruccion", "prompt", "disregard", "new task",
    "DROP", "DELETE", "UNION", "SELECT", "INSERT"
]

def sanitizar(texto: str) -> str:
    if not texto:
        return "N/A"
    texto = texto[:200]
    for palabra in PALABRAS_PROHIBIDAS:
        if palabra.lower() in texto.lower():
            return "[CONTENIDO SANITIZADO — posible injection detectado]"
    return texto

# ─────────────────────────────────────────────
# Clasificación de IPs
# ─────────────────────────────────────────────
def clasificar_ip(ip: str) -> str:
    if not ip or ip == "N/A":
        return "N/A"
    if (ip.startswith("10.") or
        ip.startswith("192.168.") or
        ip.startswith("172.16.") or
        ip.startswith("172.17.") or
        ip.startswith("172.18.") or
        ip.startswith("172.19.") or
        ip.startswith("172.2") or
        ip.startswith("172.30.") or
        ip.startswith("172.31.") or
        ip.startswith("127.") or
        ip.startswith("fe80") or
        ip.startswith("fc") or
        ip.startswith("fd")):
        return f"{ip} (interna)"
    return f"{ip} (externa)"

# ─────────────────────────────────────────────
# Mapeo de severidad desde prioridad Suricata
# ─────────────────────────────────────────────
def mapear_severidad(evento: dict) -> str:
    alert = evento.get("alert", {})
    severity = alert.get("severity", 3)
    categoria = alert.get("category", "").lower()

    # Categorías críticas siempre CRITICAL
    criticas = ["trojan", "malware", "exploit", "ransomware",
                "c2", "command and control", "backdoor"]
    if any(c in categoria for c in criticas):
        return "CRITICAL"

    if severity == 1:
        return "CRITICAL"
    elif severity == 2:
        return "HIGH"
    elif severity == 3:
        return "MEDIUM"
    else:
        return "LOW"

# ─────────────────────────────────────────────
# Normalización de evento Suricata → schema SENTINEL
# ─────────────────────────────────────────────
def normalizar_evento(evento: dict) -> str:
    if evento.get("event_type") != "alert":
        return None

    alert = evento.get("alert", {})
    timestamp = evento.get("timestamp", "N/A")
    src_ip = clasificar_ip(evento.get("src_ip", "N/A"))
    dest_ip = clasificar_ip(evento.get("dest_ip", "N/A"))
    src_port = str(evento.get("src_port", "N/A"))
    dest_port = str(evento.get("dest_port", "N/A"))
    proto = evento.get("proto", "N/A")
    hostname = evento.get("in_iface", "N/A")
    severidad = mapear_severidad(evento)
    firma = sanitizar(alert.get("signature", "N/A"))
    categoria = sanitizar(alert.get("category", "N/A"))
    accion = alert.get("action", "N/A")
    sid = alert.get("signature_id", "N/A")

    # Descripción limpia
    descripcion = f"Suricata SID:{sid} — {firma}. Proto:{proto} Accion:{accion}"
    descripcion = sanitizar(descripcion)

    schema = f"""Analiza esta alerta con el pipeline MAHORAGA:

ALERTA DE SEGURIDAD
===================
Timestamp     : {timestamp}
Fuente        : Suricata IDS
Severidad_raw : {severidad}
Hostname      : {hostname}
Usuario       : N/A
Proceso       : N/A
IP_origen     : {src_ip}
IP_destino    : {dest_ip}
Puerto_dest   : {dest_port}
Hash_archivo  : N/A
Descripcion   : {descripcion}"""

    return schema

# ─────────────────────────────────────────────
# Lectura de estado (última posición procesada)
# ─────────────────────────────────────────────
def leer_estado() -> int:
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE) as f:
            return json.load(f).get("posicion", 0)
    return 0

def guardar_estado(posicion: int):
    with open(ESTADO_FILE, "w") as f:
        json.dump({"posicion": posicion, "ultima_ejecucion": datetime.now().isoformat()}, f)

# ─────────────────────────────────────────────
# Procesamiento del eve.json
# ─────────────────────────────────────────────
def procesar_eve(archivo: str = EVE_LOG, desde_inicio: bool = False) -> list:
    alertas = []

    if not os.path.exists(archivo):
        print(f"[ERROR] No se encuentra {archivo}")
        return alertas

    posicion = 0 if desde_inicio else leer_estado()

    with open(archivo, "r") as f:
        f.seek(posicion)
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                evento = json.loads(linea)
                schema = normalizar_evento(evento)
                if schema:
                    alertas.append(schema)
            except json.JSONDecodeError:
                continue
        nueva_posicion = f.tell()

    guardar_estado(nueva_posicion)
    return alertas

# ─────────────────────────────────────────────
# Alerta de prueba
# ─────────────────────────────────────────────
def generar_alerta_prueba() -> str:
    return """Analiza esta alerta con el pipeline MAHORAGA:

ALERTA DE SEGURIDAD
===================
Timestamp     : 2026-05-13T18:40:56.796723-0600
Fuente        : Suricata IDS
Severidad_raw : MEDIUM
Hostname      : wlp3s0
Usuario       : N/A
Proceso       : N/A
IP_origen     : 192.168.1.64 (interna)
IP_destino    : 192.168.1.254 (interna)
Puerto_dest   : N/A
Hash_archivo  : N/A
Descripcion   : Suricata SID:9000001 — ICMP Test MAHORAGA. Proto:ICMP Accion:allowed"""

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="MAHORAGA — Normalizador Suricata")
    parser.add_argument("--test", action="store_true", help="Genera una alerta de prueba")
    parser.add_argument("--file", type=str, help="Archivo eve.json a procesar")
    parser.add_argument("--todo", action="store_true", help="Procesa desde el inicio del archivo")
    args = parser.parse_args()

    if args.test:
        print("\n[MAHORAGA] Alerta de prueba generada:\n")
        print(generar_alerta_prueba())
        return

    archivo = args.file or EVE_LOG
    desde_inicio = args.todo

    print(f"[MAHORAGA] Procesando alertas de Suricata desde: {archivo}")
    alertas = procesar_eve(archivo, desde_inicio)

    if not alertas:
        print("[MAHORAGA] No hay alertas nuevas.")
        return

    print(f"[MAHORAGA] {len(alertas)} alerta(s) nueva(s) encontrada(s):\n")
    for i, alerta in enumerate(alertas, 1):
        print(f"{'='*60}")
        print(f"ALERTA {i} de {len(alertas)}")
        print(f"{'='*60}")
        print(alerta)
        print()

if __name__ == "__main__":
    main()
