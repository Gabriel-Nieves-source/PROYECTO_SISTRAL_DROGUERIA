from pwdlib import PasswordHash
from sqlalchemy import text

from app.database import engine


password_hash = PasswordHash.recommended()

with engine.connect() as connection:
    resultado = connection.execute(
        text("""
            SELECT usuario, password
            FROM usuario
            WHERE usuario = 'admin'
        """)
    ).fetchone()

if resultado:
    usuario, hash_guardado = resultado

    print("Usuario:", usuario)
    print("Longitud del hash:", len(hash_guardado))
    print("Inicio del hash:", hash_guardado[:20])
    print("¿La contraseña coincide?:", password_hash.verify("admin123", hash_guardado))
else:
    print("No se encontró el usuario admin")