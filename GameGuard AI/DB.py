"""
GameGuard AI - Módulo de base de datos y generador de datos
Archivo: db.py

Incluye:
 - Clase Database: conexión y queries reutilizables
 - Función seed_data(): genera datos simulados realistas para pruebas
"""

import random
import datetime
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Tuple, Optional

# CONFIGURACIÓN — ajusta estos valores
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "gameguard_user",
    "password": "una_clave_segura",
    "database": "gameguard",
    "charset": "utf8mb4",
}

class Database:
    """Gestiona la conexión y operaciones sobre MySQL."""

    def __init__(self, config: Dict = DB_CONFIG):
        self.config = config
        self.conn = None
        self.cursor = None

    def conectar(self):
        """Establece conexión con MySQL."""
        try:
            self.conn = mysql.connector.connect(**self.config)  
            self.cursor = self.conn.cursor(dictionary=True)
            print("✓ Conexión a MySQL exitosa")
        except Error as e:
            print(f"✗ Error al conectar: {e}")
            raise

    def desconectar(self):
        """Cierra conexión de forma segura."""
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print("✓ Conexión cerrada")

    def ejecutar(self, sql: str, params: Optional[Tuple] = None) -> int:
        """Ejecuta INSERT/UPDATE/DELETE. Devuelve lastrowid o 0."""
        try:
            params = params or ()
            self.cursor.execute(sql, params) 
            self.conn.commit()
            return self.cursor.lastrowid or 0
        except Error as e:
            print(f"✗ Error ejecutando SQL: {e}")
            self.conn.rollback()
            return 0

    def consultar(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Ejecuta SELECT. Devuelve lista de dicts."""
        try:
            params = params or ()
            self.cursor.execute(sql, params)  
            return self.cursor.fetchall()
        except Error as e:
            print(f"✗ Error consultando: {e}")
            return []

    # Queries de dominio
    def obtener_usuarios_riesgo(self) -> List[Dict]:
        """Usuarios de nivel alto o crítico para el dashboard."""
        return self.consultar("SELECT * FROM vista_usuarios_riesgo")

    def obtener_alertas_pendientes(self) -> List[Dict]:
        return self.consultar("""
            SELECT a.*, u.username 
            FROM alertas a 
            JOIN usuarios u ON u.id = a.usuario_id 
            WHERE a.estado = 'pendiente' 
            ORDER BY a.score_ia DESC
        """)

    def guardar_alerta(self, usuario_id: int, tipo: str, score: float, descripcion: str) -> int:
        """Guarda una alerta generada por la IA."""
        sql = """
            INSERT INTO alertas (usuario_id, tipo_amenaza, score_ia, descripcion_ia)
            VALUES (%s, %s, %s, %s)
        """
        alerta_id = self.ejecutar(sql, (usuario_id, tipo, score, descripcion))

        # Actualiza el score_riesgo del usuario
        nivel = (
            "critico" if score >= 80 else
            "alto" if score >= 60 else
            "medio" if score >= 40 else
            "normal"
        )
        self.ejecutar(
            "UPDATE usuarios SET score_riesgo=%s, nivel_riesgo=%s WHERE id=%s",
            (score, nivel, usuario_id)
        )
        return alerta_id

    def registrar_evento(self, sesion_id: int, usuario_id: int, tipo: str, 
                        valor: Optional[float] = None, descripcion: str = "", 
                        es_anomalia: bool = False) -> int:
        sql = """
            INSERT INTO eventos_comportamiento
            (sesion_id, usuario_id, tipo_evento, valor_metrica, descripcion, es_anomalia)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.ejecutar(sql, (
            sesion_id, usuario_id, tipo, valor, descripcion, int(es_anomalia)
        ))

    def estadisticas_dashboard(self) -> Dict:
        """Métricas principales para las tarjetas del dashboard."""
        row = self.consultar("""
            SELECT
                COUNT(*) AS total_usuarios,
                SUM(CASE WHEN nivel_riesgo IN ('alto','critico') THEN 1 ELSE 0 END) AS usuarios_riesgo,
                SUM(CASE WHEN nivel_riesgo = 'critico' THEN 1 ELSE 0 END) AS criticos
            FROM usuarios
        """)[0] if self.consultar("SELECT 1") else {"total_usuarios": 0, "usuarios_riesgo": 0, "criticos": 0}

        alertas = self.consultar(
            "SELECT COUNT(*) AS pendientes FROM alertas WHERE estado='pendiente'"
        )
        pendientes = alertas[0]["pendientes"] if alertas else 0

        return {
            "total_usuarios": row["total_usuarios"],
            "usuarios_riesgo": row["usuarios_riesgo"],
            "criticos": row["criticos"],
            "alertas_pend": pendientes,
        }

# GENERADOR DE DATOS SIMULADOS 
NOMBRES_USUARIO = [
    "Nk0_L33t", "TomoChan99", "Pachi_Zero", "MiiClone_X", "FriendBot3",
    "Sakura_Mii", "HibachiGo", "Luna_Tomo", "ByteRunner", "GhostMii",
    "ProxyFox", "CloneWarz", "ZeroPing_X", "AutoPlay9", "ShadowHand",
    "NormalUser1", "Gamer_Jose", "Ana_Plays", "TechnoMii", "QuietBird",
]

IPS_VPN = ["185.234.12.44", "45.142.88.10", "103.21.55.99", "91.108.4.20"]
IPS_NORMALES = ["201.19.44.120", "98.45.22.180", "191.100.55.44", "200.75.30.90"]
TIPOS_AMENAZA = ["bot_detectado", "multicuenta", "velocidad_anomala", "ip_sospechosa", "patron_sospechoso"]

def _ip_aleatoria(sospechosa: bool) -> str:
    pool = IPS_VPN if sospechosa else IPS_NORMALES
    base = random.choice(pool)
    parts = base.split(".")
    parts[-1] = str(random.randint(1, 254))
    return ".".join(parts)

def _fecha_reciente(dias_atras: int = 7) -> datetime.datetime:
    delta = datetime.timedelta(
        days=random.randint(0, dias_atras),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return datetime.datetime.now() - delta

def seed_data(db: Database, n_usuarios: int = 20):
    """
    Inserta usuarios, sesiones, eventos y alertas de prueba OPTIMIZADO.
    Usa INSERT IGNORE y batch processing para mayor velocidad.
    """
    print(f"\n→ Generando {n_usuarios} usuarios de prueba...")

    usuarios_creados = []
    
    # Generar todos los usuarios primero (batch)
    for i, nombre in enumerate(NOMBRES_USUARIO[:n_usuarios]):
        sospechoso = random.random() < 0.4
        score_base = random.uniform(60, 99) if sospechoso else random.uniform(0, 35)
        nivel = (
            "critico" if score_base >= 80 else
            "alto" if score_base >= 60 else
            "medio" if score_base >= 40 else
            "normal"
        )
        ip_reg = _ip_aleatoria("sospechosa")

        usuario_id = db.ejecutar(
            """INSERT IGNORE INTO usuarios
               (username, email, ip_registro, pais, score_riesgo, nivel_riesgo)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                nombre,
                f"{nombre.lower()}@mail.com",
                ip_reg,
                random.choice(["Panama", "Mexico", "Colombia", "Argentina", "España"]),
                round(score_base, 2),
                nivel,
            ),
        )

        if usuario_id > 0:  # ← Solo si se creó nuevo usuario
            usuarios_creados.append({
                'id': usuario_id, 'nombre': nombre, 'sospechoso': sospechoso,
                'score': score_base, 'n_sesiones': random.randint(8, 60) if sospechoso else random.randint(1, 6)
            })

    print(f"✓ {len(usuarios_creados)} usuarios nuevos creados")

    # Procesar sesiones y eventos por lotes
    total_sesiones = 0
    for usuario in usuarios_creados:
        usuario_id = usuario['id']
        n_sesiones = usuario['n_sesiones']
        sospechoso = usuario['sospechoso']

        for _ in range(n_sesiones):
            inicio = _fecha_reciente()
            fin = inicio + datetime.timedelta(minutes=random.randint(5, 240))

            sesion_id = db.ejecutar(
                """INSERT INTO sesiones
                   (usuario_id, ip_sesion, inicio, fin, acciones_total, dispositivo)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    usuario_id,
                    _ip_aleatoria(sospechoso),
                    inicio, fin,
                    random.randint(200, 2000) if sospechoso else random.randint(10, 150),
                    random.choice(["Nintendo Switch", "PC", "Mobile"]),
                ),
            )
            total_sesiones += 1

            # Eventos (reducidos para velocidad)
            if sospechoso:
                db.registrar_evento(
                    sesion_id, usuario_id, "velocidad_anormal",
                    valor=round(random.uniform(0.01, 0.05), 3),
                    descripcion="Tiempo de respuesta imposible para humano",
                    es_anomalia=True,
                )
            else:
                db.registrar_evento(
                    sesion_id, usuario_id, "accion_juego",
                    valor=round(random.uniform(0.3, 2.5), 2),
                    descripcion="Tiempo de respuesta humano normal",
                )

        # Alerta si es sospechoso
        if sospechoso and usuario['score'] >= 40:
            tipo = random.choice(TIPOS_AMENAZA)
            db.guardar_alerta(
                usuario_id, tipo, round(usuario['score'], 2),
                f"Usuario detectado por análisis de comportamiento. Patrón: {tipo.replace('_', ' ')}. Score: {round(usuario['score'], 2)}/100."
            )

    print(f"✓ Datos insertados: {len(usuarios_creados)} usuarios, {total_sesiones} sesiones\n")

# PUNTO DE ENTRADA — CORREGIDO
if __name__ == "__main__":
    db = Database()
    db.conectar() 

    print("\n=== GameGuard AI — Setup inicial ===")
    seed_data(db, 20) 

    print("=== Estadísticas actuales ===")
    stats = db.estadisticas_dashboard()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n=== Usuarios de alto riesgo ===")
    usuarios_riesgo = db.obtener_usuarios_riesgo()
    for u in usuarios_riesgo[:5]:  # Solo primeros 5 para no saturar
        print(f"  [{u['nivel_riesgo'].upper()}] {u['username']} — score {u['score_riesgo']}")

    db.desconectar()