"""
GameGuard AI - Analizador de comportamiento con IA
===================================================
Archivo: analyzer.py

Conecta los datos de la BD con la API de Claude para generar:
  - Score de riesgo (0-100)
  - Tipo de amenaza detectada
  - Explicación en lenguaje natural
  - Recomendación de acción

Uso:
    python analyzer.py
"""

import json
import urllib.request
import urllib.error
from DB import Database

# CONFIGURACIÓN
ANTHROPIC_API_KEY = "sk-ant-XXXXXXXXXXXX" # ← pon tu API key aquí
CLAUDE_MODEL      = "claude-sonnet-4-20250514"
API_URL           = "https://api.anthropic.com/v1/messages"

# CLIENTE CLAUDE (sin librerías externas)

def llamar_claude(prompt_sistema: str, prompt_usuario: str) -> str:
    """
    Llama a la API de Claude y devuelve el texto de respuesta.
    Usa solo urllib (ya viene con Python, no necesitas instalar nada).
    """
    payload = json.dumps({
        "model":      CLAUDE_MODEL,
        "max_tokens": 1024,
        "system":     prompt_sistema,
        "messages":   [{"role": "user", "content": prompt_usuario}],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Error HTTP {e.code}: {error_body}")


# PROMPTS

SISTEMA = """Eres un motor de análisis de ciberseguridad especializado en 
detección de comportamiento malicioso en videojuegos online.

Tu tarea es analizar métricas de comportamiento de un jugador y devolver 
ÚNICAMENTE un JSON válido con esta estructura exacta, sin texto adicional:

{
  "score": <número entero 0-100>,
  "nivel_riesgo": <"normal" | "medio" | "alto" | "critico">,
  "tipo_amenaza": <"bot_detectado" | "multicuenta" | "velocidad_anomala" | "ip_sospechosa" | "patron_sospechoso" | "ninguna">,
  "resumen": <string, máximo 2 oraciones explicando por qué>,
  "recomendacion": <"sin_accion" | "monitoreo" | "revision_manual" | "bloqueo_inmediato">
}

Criterios de score:
- 0-39:  normal    → comportamiento humano esperado
- 40-59: medio     → señales leves, requiere monitoreo
- 60-79: alto      → señales claras de actividad sospechosa
- 80-100: critico  → altamente probable que sea bot o fraude
"""


def construir_prompt_usuario(username: str, datos: dict) -> str:
    return f"""Analiza al jugador "{username}" con las siguientes métricas:

- Sesiones en las últimas 24h: {datos['sesiones_24h']}
- Sesiones totales: {datos['sesiones_total']}
- Velocidad promedio de acciones (segundos): {datos['velocidad_promedio']}
- Acciones totales registradas: {datos['acciones_total']}
- IP de registro: {datos['ip_registro']}
- IPs únicas usadas: {datos['ips_unicas']}
- Anomalías detectadas por reglas: {datos['anomalias']}
- País de registro: {datos['pais']}
- Días desde registro: {datos['dias_registro']}
"""

# RECOLECTOR DE MÉTRICAS DESDE LA BD

def obtener_metricas_usuario(db: Database, usuario_id: int, username: str) -> dict:
    """Consulta la BD y construye el perfil de métricas del usuario."""

    sesiones = db.consultar("""
        SELECT COUNT(*) AS total,
               SUM(acciones_total) AS acciones,
               COUNT(DISTINCT ip_sesion) AS ips_unicas,
               SUM(inicio >= NOW() - INTERVAL 1 DAY) AS sesiones_24h
        FROM sesiones WHERE usuario_id = %s
    """, (usuario_id,))[0]

    anomalias = db.consultar("""
        SELECT COUNT(*) AS total,
               AVG(valor_metrica) AS velocidad_prom
        FROM eventos_comportamiento
        WHERE usuario_id = %s AND es_anomalia = 1
    """, (usuario_id,))[0]

    usuario = db.consultar(
        "SELECT ip_registro, pais, fecha_registro FROM usuarios WHERE id = %s",
        (usuario_id,)
    )[0]

    import datetime
    dias = (datetime.datetime.now() - usuario["fecha_registro"]).days

    return {
        "sesiones_total":    sesiones["total"] or 0,
        "sesiones_24h":      sesiones["sesiones_24h"] or 0,
        "acciones_total":    sesiones["acciones"] or 0,
        "ips_unicas":        sesiones["ips_unicas"] or 1,
        "anomalias":         anomalias["total"] or 0,
        "velocidad_promedio": round(anomalias["velocidad_prom"] or 1.5, 3),
        "ip_registro":       usuario["ip_registro"],
        "pais":              usuario["pais"],
        "dias_registro":     dias,
    }

# ANALIZADOR PRINCIPAL

def analizar_usuario(db: Database, usuario_id: int, username: str) -> dict:
    """
    Orquesta el análisis completo:
    1. Recolecta métricas de la BD
    2. Envía a Claude
    3. Parsea la respuesta
    4. Guarda la alerta si aplica
    """
    print(f"  → Analizando {username}...", end=" ", flush=True)

    metricas = obtener_metricas_usuario(db, usuario_id, username)
    prompt   = construir_prompt_usuario(username, metricas)
    respuesta_raw = llamar_claude(SISTEMA, prompt)

    # Parsear JSON de Claude
    try:
        resultado = json.loads(respuesta_raw.strip())
    except json.JSONDecodeError:
        # Si Claude añadió texto extra, extraer el JSON
        inicio = respuesta_raw.find("{")
        fin    = respuesta_raw.rfind("}") + 1
        resultado = json.loads(respuesta_raw[inicio:fin])

    score  = resultado["score"]
    nivel  = resultado["nivel_riesgo"]
    tipo   = resultado["tipo_amenaza"]

    # Guardar alerta en BD si hay riesgo
    if score >= 40 and tipo != "ninguna":
        db.guardar_alerta(
            usuario_id, tipo, score,
            resultado["resumen"]
        )
    else:
        # Actualizar score aunque no sea amenaza
        db.ejecutar(
            "UPDATE usuarios SET score_riesgo=%s, nivel_riesgo=%s, revisado_por_ia=1 WHERE id=%s",
            (score, nivel, usuario_id)
        )

    print(f"score {score} [{nivel.upper()}] — {resultado['recomendacion']}")
    return resultado


def analizar_todos(db: Database):
    """Analiza todos los usuarios que no han sido revisados por IA."""
    usuarios = db.consultar(
        "SELECT id, username FROM usuarios WHERE revisado_por_ia = 0 ORDER BY score_riesgo DESC"
    )

    if not usuarios:
        print("✓ Todos los usuarios ya fueron analizados por IA")
        return

    print(f"\n→ Analizando {len(usuarios)} usuarios con Claude...\n")
    resultados = {"critico": [], "alto": [], "medio": [], "normal": []}

    for u in usuarios:
        try:
            r = analizar_usuario(db, u["id"], u["username"])
            resultados[r["nivel_riesgo"]].append(u["username"])
        except Exception as e:
            print(f"  ✗ Error con {u['username']}: {e}")

    print("\n=== Resumen del análisis IA ===")
    for nivel, nombres in resultados.items():
        if nombres:
            print(f"  [{nivel.upper()}] {', '.join(nombres)}")

# PUNTO DE ENTRADA

if __name__ == "__main__":
    db = Database()
    db.conectar()

    analizar_todos(db)

    print("\n=== Alertas generadas ===")
    for a in db.obtener_alertas_pendientes():
        print(f"  [{a['score_ia']:.0f}] {a['username']} — {a['tipo_amenaza']}")
        print(f"       {a['descripcion_ia'][:80]}...")

    db.desconectar()