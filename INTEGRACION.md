# Cómo integrar esto al repositorio de SITRAL

1. **Copiar carpetas** a la raíz del repo: `app/auth/`, `app/core/security.py`,
   `app/core/config.py`, `app/middleware/`, `app/domain/lotes.py` (si no tienen
   reglas de lotes propias), `tests/`, `scripts/`, `.github/`,
   `sonar-project.properties`, `.env.example`.
2. **Base de datos**: si SITRAL ya tiene `database.py`, borre `app/core/database.py`
   y cambie los imports `from app.core.database import ...` por los suyos.
   La tabla `usuarios` se crea sola con `Base.metadata.create_all`; si usan
   Alembic, generen una migración.
3. **main.py existente**: agregar
   ```python
   from app.auth.router import router as auth_router
   from app.middleware.security_headers import SecurityHeadersMiddleware
   app.add_middleware(SecurityHeadersMiddleware)
   app.include_router(auth_router)
   ```
4. **Proteger sus endpoints actuales** (A01): en cada router de SITRAL añadir
   `Depends(require_roles("ADMIN"))` a crear/editar/eliminar lotes y
   `Depends(require_roles("USER", "ADMIN"))` a las consultas.
5. **Crear usuarios iniciales** (una sola vez, en consola Python):
   ```python
   from app.core.database import SessionLocal
   from app.auth.models import Usuario
   from app.core.security import hash_password
   db = SessionLocal()
   db.add(Usuario(email="admin@sitral.co", hashed_password=hash_password("ClaveSegura#2026"), rol="ADMIN"))
   db.commit()
   ```
6. **SonarCloud**: poner `sonar.organization` y `sonar.projectKey` reales y
   desactivar "Automatic Analysis" en SonarCloud (Administration → Analysis Method),
   porque ahora el análisis lo hace el pipeline.
7. **Mutation testing sobre su código real**: si sus reglas de negocio están en
   otro archivo, cambie `paths_to_mutate` en `pyproject.toml`.
8. Hacer commit, push, y verificar que los 3 jobs queden en verde.
