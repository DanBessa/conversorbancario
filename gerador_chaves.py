from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# --- IMPORTANTE: Escolha uma senha forte para proteger sua chave privada ---
SENHA_DA_CHAVE = b"85957176Ca@"

# Gera a chave privada
chave_privada = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Salva a chave privada em um arquivo, criptografada com sua senha
with open("chave_privada.pem", "wb") as f:
    f.write(
        chave_privada.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(SENHA_DA_CHAVE),
        )
    )

# Gera e salva a chave pública correspondente
chave_publica = chave_privada.public_key()
with open("chave_publica.pem", "wb") as f:
    f.write(
        chave_publica.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

print("✅ Chaves geradas com sucesso.")
print("!!! GUARDE O ARQUIVO 'chave_privada.pem' E SUA SENHA EM UM LUGAR SEGURO !!!")
