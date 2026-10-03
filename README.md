# Reporte ventas

Para generar la página web (requiere Python con pandas y openpyxl):

    pip install pandas openpyxl
    python scripts/build_web.py

Para usar una base nueva, reemplaza `data/ANALISIS_ESTADO-PROYECCION.xlsx` o pasa la ruta del archivo nuevo:

    python scripts/build_web.py ruta/a/nueva_base.xlsx

El resultado se guarda en `output/estatus-comisiones-s37-s40.html`. Ábrelo en el navegador.
