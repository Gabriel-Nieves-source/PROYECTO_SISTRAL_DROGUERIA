from pwdlib import PasswordHash
from sqlalchemy import text

from app.database import engine


password_hash = PasswordHash.recommended()

hash_admin = password_hash.hash("admin123")
hash_farmaceuta = password_hash.hash("farm123")


with engine.begin() as connection:

    connection.execute(
        text("""
            UPDATE usuario
            SET password = :password
            WHERE usuario = 'admin'
        """),
        {"password": hash_admin}
    )

    connection.execute(
        text("""
            UPDATE usuario
            SET password = :password
            WHERE usuario = 'farmaceuta'
        """),
        {"password": hash_farmaceuta}
    )


print("Contraseñas actualizadas correctamente.")