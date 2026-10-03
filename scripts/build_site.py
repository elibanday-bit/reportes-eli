"""Genera el sitio publicable con inicio de sesión: los reportes se guardan cifrados (AES-GCM)
y solo se abren en el navegador con un usuario y contraseña válidos.
Uso: python scripts/build_site.py
Entradas: reportes.json (lista de reportes) y config/usuarios.json (usuarios y contraseñas, no se sube al repo).
Salida: carpeta site/, lista para publicar como sitio estático (Netlify, Cloudflare Pages).
Requiere: pip install cryptography"""
import base64, datetime, hashlib, json, os, secrets, shutil
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROOT = Path(__file__).resolve().parents[1]
USERS = ROOT / "config" / "usuarios.json"
SITE = ROOT / "site"
ITER = 600_000  # PBKDF2-SHA256: hace lento probar contraseñas a la fuerza
ALFABETO = "abcdefghjkmnpqrstuvwxyz23456789"

b64 = lambda b: base64.b64encode(b).decode()

def cifrar(key, data):
    iv = os.urandom(12)
    return {"iv": b64(iv), "ct": b64(AESGCM(key).encrypt(iv, data, None))}

def derivar(clave, salt):
    return PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(clave.encode())

def id_usuario(u):
    return hashlib.sha256(u.strip().lower().encode()).hexdigest()

def nueva_clave():
    return "-".join("".join(secrets.choice(ALFABETO) for _ in range(4)) for _ in range(3))

if not USERS.exists():
    USERS.parent.mkdir(exist_ok=True)
    inicial = [{"usuario": "eli", "nombre": "Eli", "clave": nueva_clave()},
               {"usuario": "jefe", "nombre": "Jefe", "clave": nueva_clave()}]
    USERS.write_text(json.dumps(inicial, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Se creó {USERS.relative_to(ROOT)} con contraseñas nuevas:")
    for u in inicial:
        print(f"  {u['usuario']}: {u['clave']}")

usuarios = json.loads(USERS.read_text(encoding="utf-8"))
reportes = json.loads((ROOT / "reportes.json").read_text(encoding="utf-8"))

# Llave maestra nueva en cada publicación: cifra los reportes y la lista; cada usuario guarda una copia
# envuelta con su contraseña.
K = AESGCM.generate_key(256)
if SITE.exists():
    shutil.rmtree(SITE)
(SITE / "r").mkdir(parents=True)
for f in (ROOT / "web" / "sitio").iterdir():
    shutil.copy(f, SITE / f.name)

manifest = []
for rep in reportes:
    archivo = ROOT / rep["archivo"]
    token = secrets.token_hex(8)
    (SITE / "r" / f"{token}.json").write_text(json.dumps(cifrar(K, archivo.read_bytes())), encoding="utf-8")
    fecha = rep.get("actualizado") or datetime.date.fromtimestamp(archivo.stat().st_mtime).isoformat()
    manifest.append({k: rep.get(k, "") for k in ("id", "titulo", "descripcion", "periodo", "estado")}
                    | {"actualizado": fecha, "token": token})

vault = {"v": 1, "iter": ITER, "users": {}, "manifest": cifrar(K, json.dumps(manifest, ensure_ascii=False).encode())}
for u in usuarios:
    salt = os.urandom(16)
    payload = json.dumps({"k": b64(K), "nombre": u.get("nombre") or u["usuario"]}, ensure_ascii=False).encode()
    vault["users"][id_usuario(u["usuario"])] = {"salt": b64(salt)} | cifrar(derivar(u["clave"], salt), payload)
(SITE / "vault.json").write_text(json.dumps(vault), encoding="utf-8")

print(f"Sitio generado en site/ | Reportes: {len(manifest)} | Usuarios: {len(usuarios)}")
