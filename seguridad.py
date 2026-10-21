import hashlib
import hmac
import secrets


# Hash de contraseñas con PBKDF2-SHA256. Formato guardado: "salt$hash".


def generar_hash(contrasena, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    resultado = hashlib.pbkdf2_hmac(
        "sha256",
        contrasena.encode("utf-8"),
        bytes.fromhex(salt),
        600_000
    )

    return f"{salt}${resultado.hex()}"


def verificar_hash(contrasena, hash_guardado):
    try:
        salt, hash_original = hash_guardado.split("$", 1)
        hash_nuevo = generar_hash(contrasena, salt)
        return hmac.compare_digest(
            hash_nuevo.split("$", 1)[1],
            hash_original
        )
    except (ValueError, TypeError):
        return False
