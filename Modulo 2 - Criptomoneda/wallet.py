# Empezaremos generando la clave privada
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

# Utilizaremos el método "generate_private_key"
# para generar nuestra clave
# asignamos algunos parametros
private_key = rsa.generate_private_key(
     public_exponent=65537,
     key_size=2048,
     backend=default_backend()
)
# Ahora generaremos la clave pública
public_key = private_key.public_key()

print(public_key.public_bytes(encoding='utf-8', format=str))