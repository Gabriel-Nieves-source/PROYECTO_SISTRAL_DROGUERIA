from app.rate_limit import LoginRateLimiter


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_bloquea_al_llegar_al_maximo():
    r = LoginRateLimiter(3, 60, reloj=Reloj())
    r.registrar_fallo("k")
    r.registrar_fallo("k")
    assert r.bloqueado("k") is False
    r.registrar_fallo("k")
    assert r.bloqueado("k") is True


def test_desbloquea_al_pasar_la_ventana():
    reloj = Reloj()
    r = LoginRateLimiter(2, 60, reloj=reloj)
    r.registrar_fallo("k")
    r.registrar_fallo("k")
    reloj.t += 59
    assert r.bloqueado("k") is True
    reloj.t += 1
    assert r.bloqueado("k") is False


def test_reiniciar():
    r = LoginRateLimiter(1, 60, reloj=Reloj())
    r.registrar_fallo("k")
    r.reiniciar("k")
    assert r.bloqueado("k") is False
    r.reiniciar("no-existe")


def test_claves_independientes():
    r = LoginRateLimiter(1, 60, reloj=Reloj())
    r.registrar_fallo("a")
    assert r.bloqueado("a") is True
    assert r.bloqueado("b") is False
