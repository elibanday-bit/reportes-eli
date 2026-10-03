# Reporte ventas

Para generar la página web (requiere Python con pandas y openpyxl):

    pip install pandas openpyxl
    python scripts/build_web.py

Para usar una base nueva, reemplaza `data/ANALISIS_ESTADO-PROYECCION.xlsx` o pasa la ruta del archivo nuevo:

    python scripts/build_web.py ruta/a/nueva_base.xlsx

El resultado se guarda en `output/estatus-comisiones-s37-s40.html`. Ábrelo en el navegador.

## Sitio con inicio de sesión (Planificación Comercial)

El sitio publicable está en `site/`: inicio de sesión, panel "Mis reportes" y visor. Los reportes van cifrados (AES-GCM) y solo se abren en el navegador con un usuario válido.

    pip install cryptography
    python scripts/build_site.py

- **Reportes del panel**: se agregan o editan en `reportes.json` (título, descripción, periodo, estado, archivo HTML).
- **Usuarios y contraseñas**: en `config/usuarios.json`. Este archivo **no se sube al repo**. Si no existe, el script lo crea con contraseñas nuevas. Para cambiar una contraseña o agregar a alguien, edítalo y vuelve a correr el script.
- Cada vez que se corre el script, las sesiones abiertas se cierran y hay que volver a entrar.
- **Publicar**: en Netlify o Cloudflare Pages, conecta el repo y publica la carpeta `site/` (ya está configurado en `netlify.toml`, sin comando de build). Tiene que abrirse con https.
