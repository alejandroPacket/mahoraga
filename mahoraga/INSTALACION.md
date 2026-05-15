# MAHORAGA — Guia de Instalacion Completa
## Sistema Multiagente de Ciberdefensa sobre TinyClaw v2.0.0
**Version:** 1.0 | **Fecha:** Mayo 2026

---

## Requisitos previos

Antes de comenzar, asegurate de tener lo siguiente:

- Sistema operativo: Pop!_OS o Ubuntu 22.04+
- Conexion a internet estable
- Cuenta en Google AI Studio con API key de Gemini 2.0 Flash
  (obtener en: https://aistudio.google.com/apikey)
- Acceso al repositorio privado mahoraga en GitHub
- Minimo 4GB de RAM y 10GB de espacio en disco
- Python 3.10 o superior instalado

Verificar version de Python:

    python3 --version

---

## PARTE 1 — Instalacion de TinyClaw

### Paso 1 — Instalar dependencias del sistema

    sudo apt-get update
    sudo apt-get install -y git curl sqlite3 python3 python3-pip unzip

### Paso 2 — Instalar Bun (runtime requerido por TinyClaw)

TinyClaw usa Bun en lugar de Node.js. Instalarlo con:

    curl -fsSL https://bun.sh/install | bash

Despues de la instalacion, recargar el shell:

    source ~/.bashrc

Verificar que Bun quedo instalado:

    bun --version

Debe mostrar algo como: 1.x.x

### Paso 3 — Clonar el repositorio oficial de TinyClaw

    git clone https://github.com/warengonzaga/tinyclaw.git
    cd tinyclaw

### Paso 4 — Instalar dependencias de TinyClaw

    bun install

Este comando descarga todos los paquetes necesarios. Puede tardar
varios minutos dependiendo de la conexion a internet.

### Paso 5 — Ejecutar el setup wizard de TinyClaw

    bun run cli setup

El wizard te pedira los siguientes datos en orden:

1. Aceptar la licencia GPL-3.0 — escribe 'y' y presiona Enter
2. API key del provider — por ahora escribe cualquier texto,
   despues la cambiaremos a Gemini
3. Soul seed — escribe cualquier numero, por ejemplo: 3891542847
   (este numero determina la personalidad del agente)
4. Configuracion TOTP 2FA — sigue las instrucciones en pantalla,
   necesitaras una app de autenticacion como Google Authenticator
5. Recovery token — guarda este token en un lugar seguro

### Paso 6 — Verificar que TinyClaw arranca correctamente

    bun run cli start

Si todo esta bien, veras en los logs:

    [INFO][Tiny Claw is ready!]
    [INFO][API server: http://localhost:3000]

Abre http://localhost:3000 en el navegador y verifica que el
dashboard carga correctamente. Luego detiene el servidor con Ctrl+C.

---

## PARTE 2 — Instalacion de MAHORAGA

### Paso 7 — Clonar el repositorio MAHORAGA

En una carpeta separada (no dentro de tinyclaw), clona el repo:

    cd ~
    git clone https://github.com/alejandroPacket/mahoraga.git
    cd mahoraga

### Paso 8 — Copiar los archivos de MAHORAGA a TinyClaw

    cp escribir_agents_md.py ~/tinyclaw/
    cp mahoraga_suricata.py ~/tinyclaw/
    cp -r mahoraga/ ~/tinyclaw/

Verificar que los archivos se copiaron correctamente:

    ls ~/tinyclaw/escribir_agents_md.py
    ls ~/tinyclaw/mahoraga_suricata.py
    ls ~/tinyclaw/mahoraga/seeds/

### Paso 9 — Instalar los seeds de los agentes

Este script escribe el archivo AGENTS.md con la definicion completa
de Oracle, SENTINEL, ATLAS y AEGIS, y genera el checksum de SOUL.md:

    cd ~/tinyclaw
    python3 escribir_agents_md.py

Output esperado:

    OK AGENTS.md escrito en: /home/TU_USUARIO/.tinyclaw/heartware/AGENTS.md
    OK Checksum de SOUL.md guardado

Si ves ese output, los seeds cargaron correctamente.

---

## PARTE 3 — Modificaciones al codigo fuente de TinyClaw

IMPORTANTE: Estas 3 modificaciones son obligatorias. Sin ellas,
el pipeline multiagente no funcionara correctamente.

### Modificacion 1 — Threshold del filtro SHIELD

El filtro de seguridad SHIELD bloquea alertas de red por defecto.
Hay que subir el threshold para que las alertas pasen correctamente:

    sed -i 's/const CONFIDENCE_THRESHOLD = 0.85/const CONFIDENCE_THRESHOLD = 0.97/'       ~/tinyclaw/packages/shield/src/engine.ts

Verificar que el cambio quedo aplicado:

    grep "CONFIDENCE_THRESHOLD" ~/tinyclaw/packages/shield/src/engine.ts

Debe mostrar: const CONFIDENCE_THRESHOLD = 0.97;

### Modificacion 2 — Unificacion del userId en el Web UI

El Web UI usaba un userId diferente al del CLI, causando que los
resultados de los sub-agentes nunca llegaran al chat. Esta modificacion
los unifica:

    sed -i "s/const ownerId = 'web:owner'/const ownerId = 'cli:owner'/"       ~/tinyclaw/src/web/src/server.ts

    sed -i "s/|| 'web:owner'/|| 'cli:owner'/g"       ~/tinyclaw/src/web/src/server.ts

Verificar:

    grep "ownerId\|cli:owner\|web:owner" ~/tinyclaw/src/web/src/server.ts |       grep "const ownerId\|owner"

Debe mostrar: const ownerId = 'cli:owner';

### Modificacion 3 — Registro del canal CLI en el gateway

Los sub-agentes intentan entregar resultados via canal 'cli' pero el
gateway solo tenia registrado el canal 'web'. Hay que agregar el canal
'cli' apuntando al mismo sender del Web UI.

Primero encontrar la linea exacta:

    grep -n "gateway.register" ~/tinyclaw/src/cli/src/commands/start.ts

Vera algo como:

    1118:  gateway.register('web', webUI.getChannelSender());

Agregar el canal 'cli' justo despues con este comando:

    sed -i "s/gateway.register('web', webUI.getChannelSender());/gateway.register('web', webUI.getChannelSender());
  gateway.register('cli', webUI.getChannelSender());/"       ~/tinyclaw/src/cli/src/commands/start.ts

Verificar que quedaron las dos lineas:

    grep "gateway.register" ~/tinyclaw/src/cli/src/commands/start.ts | head -5

Debe mostrar tanto 'web' como 'cli'.

### Compilar todos los cambios

Despues de las 3 modificaciones, compilar el proyecto completo:

    cd ~/tinyclaw
    bun run build

Este proceso tarda varios minutos. Al final debe mostrar:

    Bundled 181 modules in Xms

---

## PARTE 4 — Configuracion de Gemini como Provider

### Paso 10 — Compilar el plugin de OpenAI

TinyClaw usa un plugin compatible con OpenAI para conectar Gemini:

    cd ~/tinyclaw
    bun run build:plugins

### Paso 11 — Habilitar el plugin en la base de datos

Reemplaza TU_USUARIO con tu nombre de usuario de Linux
(el que aparece en la terminal antes del @):

    sqlite3 ~/.tinyclaw/data/config.db "UPDATE config SET value =     '{"enabled":["/home/TU_USUARIO/tinyclaw/plugins/provider/plugin-provider-openai/dist/index.js"]}'     WHERE key = 'plugins';"

Para saber tu usuario exacto:

    echo $USER

### Paso 12 — Configurar el routing de providers

Este comando hace que las tareas complejas (como el pipeline de agentes)
usen Gemini, y las tareas simples usen Ollama Cloud gratuito:

    sqlite3 ~/.tinyclaw/data/config.db "UPDATE config SET value =     '{"simple":"ollama-cloud","moderate":"ollama-cloud",    "complex":"openai","reasoning":"openai"}' WHERE key = 'routing';"

Verificar que quedo bien:

    sqlite3 ~/.tinyclaw/data/config.db "SELECT value FROM config WHERE key = 'routing';"

### Paso 13 — Arrancar MAHORAGA

    cd ~/tinyclaw
    bun run cli start

En los logs, verificar que NO aparece este warning:

    [WARN] Primary provider "OpenAI" unavailable, falling back to built-in

Si ese warning NO aparece, Gemini esta conectado. Si aparece, continuar
con el Paso 14 para configurar la API key.

### Paso 14 — Configurar la API key de Gemini

Abrir el dashboard en http://localhost:3000 y en el chat de Spark
enviar este mensaje. Reemplazar TU_API_KEY con tu key de Google AI Studio:

    Use the openai_pair tool with apiKey: TU_API_KEY and model: gemini-2.0-flash

Spark deberia responder confirmando que el provider fue configurado.

En los logs de la terminal deberia aparecer que el tools count sube de 39 a 41.

### Paso 15 — Reiniciar para aplicar los cambios

En el chat de localhost:3000 enviar:

    Use the tinyclaw_restart tool now.

Spark reiniciara el sistema automaticamente.

---

## PARTE 5 — Verificacion del Sistema

### Paso 16 — Verificar que el pipeline cargo correctamente

En el chat de localhost:3000 enviar:

    Describe el pipeline MAHORAGA y los roles de cada agente.

Spark debe responder describiendo los cuatro agentes:
- Oracle — orquestador
- SENTINEL — triage de alertas
- ATLAS — correlacion MITRE ATT&CK
- AEGIS — asesor de respuesta

Si Spark describe correctamente el pipeline, la instalacion fue exitosa.

### Paso 17 — Probar el pipeline con una alerta de prueba

En la terminal ejecutar:

    cd ~/tinyclaw
    python3 mahoraga_suricata.py --test

Copiar el output completo (el bloque que dice ALERTA DE SEGURIDAD)
y enviarlo al chat de localhost:3000 con este prefijo:

    Analiza esta alerta con el pipeline MAHORAGA:
    [pegar aqui el bloque ALERTA DE SEGURIDAD]

El sistema debe procesar la alerta con SENTINEL, ATLAS y AEGIS,
y entregar un reporte consolidado automaticamente.

---

## PARTE 6 — Instalacion de Suricata (IDS)

### Paso 18 — Instalar Suricata

    sudo apt-get install -y suricata

### Paso 19 — Identificar la interfaz de red

    ip link show | grep -E "wlan|wlp|eth|enp" | head -5

Anota el nombre de tu interfaz (ejemplo: wlp3s0, eth0, enp3s0).

### Paso 20 — Configurar Suricata

Reemplaza INTERFAZ con el nombre de tu interfaz:

    sudo sed -i '581s/interface: eth0/interface: INTERFAZ/' /etc/suricata/suricata.yaml
    sudo sed -i '661s/interface: eth0/interface: INTERFAZ/' /etc/suricata/suricata.yaml

Agregar las reglas al archivo de configuracion:

    sudo sed -i 's/^rule-files:$/rule-files:
  - \/var\/lib\/suricata\/rules\/suricata.rules/'       /etc/suricata/suricata.yaml

### Paso 21 — Descargar reglas de deteccion

    sudo suricata-update

Debe cargar alrededor de 50,000 reglas de Emerging Threats.

### Paso 22 — Configurar Suricata en modo pcap

Crear el override del servicio systemd:

    sudo systemctl edit suricata

En el editor agregar exactamente esto (reemplazando INTERFAZ):

    [Service]
    ExecStart=
    ExecStart=/usr/bin/suricata -D --pcap=INTERFAZ -c /etc/suricata/suricata.yaml --pidfile /run/suricata.pid

Guardar con Ctrl+O, Enter, Ctrl+X.

### Paso 23 — Iniciar Suricata

    sudo systemctl daemon-reload
    sudo systemctl start suricata
    sudo systemctl enable suricata

Verificar que esta corriendo:

    sudo systemctl status suricata | head -5

Debe mostrar: Active: active (running)

Verificar que las reglas cargaron:

    sudo tail -3 /var/log/suricata/suricata.log

Debe mostrar: X signatures processed

---

## Solucion a errores comunes

### Error: "bun start" no funciona
Usar siempre el comando completo:

    bun run cli start

### Error: modelo requiere suscripcion de pago (403)
Cambiar al modelo gratuito:

    bun run cli config model builtin gpt-oss:120b-cloud

### Error: plugin no encontrado por nombre de paquete
Usar ruta absoluta en la DB (ver Paso 11).
Asegurarse de reemplazar TU_USUARIO con el usuario correcto.

### Error: sub-agentes no entregan resultados
Verificar que las 3 modificaciones al codigo fuente esten aplicadas
y que se haya ejecutado bun run build despues de los cambios:

    grep "CONFIDENCE_THRESHOLD" ~/tinyclaw/packages/shield/src/engine.ts
    grep "cli:owner" ~/tinyclaw/src/web/src/server.ts | head -3
    grep "gateway.register" ~/tinyclaw/src/cli/src/commands/start.ts

### Error: SHIELD bloquea alertas con confianza 0.88
El threshold debe estar en 0.97. Verificar con:

    grep "CONFIDENCE_THRESHOLD" ~/tinyclaw/packages/shield/src/engine.ts

Si muestra 0.85, aplicar la Modificacion 1 y recompilar.

### Error: Gemini no conecta al reiniciar
La API key se guarda en el secrets engine. Si se pierde, repetir el Paso 14.

### Error: Suricata no genera alertas
Verificar que esta en modo pcap y no af-packet:

    sudo tail -3 /var/log/suricata/suricata.log

Debe decir "PCAP" y no "AFP capture threads".

---

## Referencia rapida de comandos

| Accion | Comando |
|--------|---------|
| Arrancar MAHORAGA | bun run cli start |
| Arrancar con logs detallados | bun run cli start --verbose |
| Compilar todo | bun run build |
| Compilar solo plugins | bun run build:plugins |
| Ver modelo activo | bun run cli config model |
| Ver provider primario | bun run cli config model primary |
| Ver soul seed | bun run cli seed |
| Actualizar reglas Suricata | sudo suricata-update |
| Ver alertas Suricata en vivo | sudo tail -f /var/log/suricata/fast.log |
| Ver estado de Suricata | sudo systemctl status suricata |

---

## Archivos importantes del sistema

| Archivo | Ubicacion | Descripcion |
|---------|-----------|-------------|
| AGENTS.md | ~/.tinyclaw/heartware/ | Definicion activa de agentes — NO editar manualmente |
| SHIELD.md | ~/.tinyclaw/heartware/ | Politica de seguridad |
| SOUL.md | ~/.tinyclaw/heartware/ | Soul del agente — NO modificar |
| SOUL.md.checksum | ~/.tinyclaw/heartware/ | Checksum de integridad |
| config.db | ~/.tinyclaw/data/ | Configuracion del sistema |
| agent.db | ~/.tinyclaw/data/ | Base de datos de agentes y tareas |
| engine.ts | ~/tinyclaw/packages/shield/src/ | Threshold SHIELD (modificado a 0.97) |
| server.ts | ~/tinyclaw/src/web/src/ | userId Web UI (modificado a cli:owner) |
| start.ts | ~/tinyclaw/src/cli/src/commands/ | Gateway con canal CLI registrado |
| eve.json | /var/log/suricata/ | Alertas de Suricata en formato JSON |

---

## Contacto

Para dudas tecnicas sobre el pipeline de MAHORAGA, el schema de SENTINEL,
o el comportamiento de los agentes, contactar a Alejandro quien tiene
el conocimiento completo del motor.

MAHORAGA | Ingenieria en Ciberseguridad | Mayo 2026
