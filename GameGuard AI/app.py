"""
GameGuard AI — Servidor Flask
==============================
Ejecutar: python app.py
Abre: http://localhost:5000
"""

from flask import Flask, jsonify, render_template, request
from DB import Database
import datetime

app = Flask(__name__)
db = Database()

@app.before_request
def abrir_conexion():
    db.conectar()

@app.teardown_request
def cerrar_conexion(exc):
    db.desconectar()

# ── Página principal ──────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── API: métricas del dashboard ───────────────
@app.route("/api/stats")
def stats():
    data = db.estadisticas_dashboard()
    return jsonify(data)

# ── API: usuarios de alto riesgo ──────────────
@app.route("/api/usuarios")
def usuarios():
    nivel = request.args.get("nivel", "all")
    if nivel == "all":
        rows = db.consultar("""
            SELECT u.id, u.username, u.nivel_riesgo, u.score_riesgo,
                   u.estado, u.ip_registro, u.pais,
                   COUNT(DISTINCT s.id) AS sesiones,
                   COUNT(DISTINCT a.id) AS alertas
            FROM usuarios u
            LEFT JOIN sesiones s ON s.usuario_id = u.id
            LEFT JOIN alertas a ON a.usuario_id = u.id
            GROUP BY u.id
            ORDER BY u.score_riesgo DESC
        """)
    else:
        rows = db.consultar("""
            SELECT u.id, u.username, u.nivel_riesgo, u.score_riesgo,
                   u.estado, u.ip_registro, u.pais,
                   COUNT(DISTINCT s.id) AS sesiones,
                   COUNT(DISTINCT a.id) AS alertas
            FROM usuarios u
            LEFT JOIN sesiones s ON s.usuario_id = u.id
            LEFT JOIN alertas a ON a.usuario_id = u.id
            WHERE u.nivel_riesgo = %s
            GROUP BY u.id
            ORDER BY u.score_riesgo DESC
        """, (nivel,))
    return jsonify(rows)

# ── API: alertas pendientes ───────────────────
@app.route("/api/alertas")
def alertas():
    rows = db.consultar("""
        SELECT a.id, a.tipo_amenaza, a.score_ia,
               a.descripcion_ia, a.estado, a.fecha_creacion,
               u.username, u.nivel_riesgo
        FROM alertas a
        JOIN usuarios u ON u.id = a.usuario_id
        ORDER BY a.score_ia DESC
        LIMIT 20
    """)
    # Convertir datetime a string
    for r in rows:
        if isinstance(r.get("fecha_creacion"), datetime.datetime):
            r["fecha_creacion"] = r["fecha_creacion"].strftime("%Y-%m-%d %H:%M")
    return jsonify(rows)

# ── API: actividad por hora ───────────────────
@app.route("/api/actividad")
def actividad():
    rows = db.consultar("""
        SELECT HOUR(timestamp_evento) AS hora,
               COUNT(*) AS total,
               SUM(es_anomalia) AS anomalias
        FROM eventos_comportamiento
        WHERE timestamp_evento >= NOW() - INTERVAL 7 DAY
        GROUP BY HOUR(timestamp_evento)
        ORDER BY hora
    """)
    return jsonify(rows)

# ── API: bloquear usuario ─────────────────────
@app.route("/api/bloquear/<int:uid>", methods=["POST"])
def bloquear(uid):
    db.ejecutar(
        "UPDATE usuarios SET estado='baneado' WHERE id=%s", (uid,)
    )
    db.ejecutar(
        "UPDATE alertas SET estado='confirmada' WHERE usuario_id=%s", (uid,)
    )
    return jsonify({"ok": True, "msg": "Usuario baneado"})

# ── API: marcar falso positivo ────────────────
@app.route("/api/falso-positivo/<int:uid>", methods=["POST"])
def falso_positivo(uid):
    db.ejecutar(
        "UPDATE usuarios SET nivel_riesgo='normal', score_riesgo=0 WHERE id=%s", (uid,)
    )
    db.ejecutar(
        "UPDATE alertas SET estado='falso_positivo' WHERE usuario_id=%s", (uid,)
    )
    return jsonify({"ok": True, "msg": "Marcado como falso positivo"})

if __name__ == "__main__":
    print("\n🛡️  GameGuard AI corriendo en http://localhost:5000\n")
    app.run(debug=True, port=5000)