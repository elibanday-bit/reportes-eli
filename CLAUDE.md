# Reporte ventas — contexto del proyecto

## Qué es
Reporte de estatus de ventas y comisiones de asesores (periodo S37–S40) para presentar a dirección.
Responde cuatro preguntas: cómo vamos por pool, cuánto se proyecta, quiénes activan comisión y cuánto se proyecta en gasto. También identifica qué pool tiene más desfase.
El usuario trabaja en español y prefiere ver los entregables como **página web**, no en Excel.

## Estructura
- `data/ANALISIS_ESTADO-PROYECCION.xlsx`: base original. Tiene la hoja `base` (263 asesores) y la hoja `tablas` (niveles y aceleradores).
- `scripts/build_web.py`: calcula todo con pandas y genera `output/estatus-comisiones-s37-s40.html`. **Es el flujo principal.**
- `scripts/build_excel.py`: genera el modelo Excel con fórmulas, como respaldo.
- `web/template.html`: plantilla de la página. El marcador `__DATA__` se reemplaza con el detalle por asesor.
- `output/`: entregables generados.
- `scripts/build_site.py` + `web/sitio/`: sitio publicable del equipo **Soporte Variables** (logo Laureate). Login con usuario y contraseña, panel "Mis reportes" y visor. Los reportes de `reportes.json` se cifran con una llave maestra, y cada usuario de `config/usuarios.json` (fuera del repo) la abre con su contraseña (PBKDF2 600k + AES-GCM). Salida: `site/`.

## Reglas de cálculo (validadas con el usuario)
- **PM** = UG + WA + CAD + RN de S37 a S40, contra `META PM TOTAL`.
- **CM** = MOD B, contra `META CM`. MOD B solo está completo en S37–S38: S39 es parcial y S40 no tiene dato.
- **Proyección de CM en S39 y S40** = ritmo de S37–S38 por semana activa (MOD B S37+S38 entre Vac S37+Vac S38) × Vac de cada semana. Si el dato real es mayor, se usa el real.
- **Columnas Vac S37–S40**: factor de disponibilidad semanal (1 = semana completa). El HC es su promedio.
- **Cumplimiento** = 0.7 × %PM + 0.3 × %CM.
- **Nivel y acelerador** según la hoja `tablas`: N1 desde 80% (0.3x), N2 desde 90% (0.9x), N3 desde 100% (1x), N4 desde 110% (1.3x), N5 desde 120% (1.5x) y N6 desde 130% (2x). Bajo 80% no activa.
- **Estado**: Activa (80% o más), Cerca (70% a 80%), No activa (menos de 70%).
- **Gasto** = CARTA × acelerador. CARTA = TARGET × % cuota.
- Usar una tolerancia de 1e-9 en los umbrales: hay casos de exactamente 80%.

## Resultados base (para verificar después de cualquier cambio)
263 asesores. Cumplimiento hoy 45.2% y proyectado 54.7%. Activan 76, cerca 14 y no activan 173.
Gasto proyectado S/ 95,987 sobre una carta de S/ 248,917. Gasto con el CM cargado hoy: S/ 49,192.
El pool con más desfase es ReiNew (8.8%).
Escenarios: tope de CM en 120% → 46 activan y S/ 48,952; piso de PM de 60% → 49 y S/ 64,012; piso de PM de 70% → 43 y S/ 56,032.
Auditoría del 3 oct.: los 9 pools del arreglo `POOLS` cuadran con la base.

## Funciones de la página
Encabezado con las cuatro respuestas, avance por pool (línea de hoy a proyectado con la marca de 80%), activación, gasto, desfase, propuesta de escenarios (tope de CM en 120% y piso de PM de 60% o 70%), detalle por asesor y supuestos.
El detalle por asesor se puede filtrar por pool, estado y código o líder, y ordenar por columna.
El **factor de proyección PM** (por ejemplo, 1.2) recalcula la tabla de detalle y muestra el resultado total frente a la base.

## Pendientes
- Los bloques por pool, los escenarios y el encabezado están escritos a mano en `web/template.html` (arreglo `POOLS` y textos). Hay que volverlos dinámicos, calculados desde los datos, para que se actualicen con cada base nueva.
- Que el factor de proyección PM recalcule toda la página, no solo el detalle.
- Validar con dirección:
  - Lima Sur no tiene TARGET ni % cuota.
  - ReiNew no tiene ventas MOD B.
  - La columna TOTAL VENTA de la base no cuadra con el detalle semanal (123 de 263 filas; ninguna combinación de columnas la reproduce).
  - Lima Sur tampoco tiene HC ni PESO PM/CM (se usa 0.7/0.3).
  - Dos asesores de Counter (70682386-2 y 70525424-4) tienen CARTA distinta de TARGET × % cuota y un HC que no es el promedio de Vac.
- Quitar la etiqueta "Borrador para revisión" cuando el usuario apruebe.

## Recordarle al usuario (sitio en pausa, retomarlo cuando el informe esté cuadrado)
El sitio de login está terminado y en pausa por decisión del usuario. Primero se cuadra el informe. Al cerrar el trabajo del informe, recordarle:
- **Pasar el repo a privado** (hoy es público y contiene la base y el reporte sin cifrar). Es lo más urgente.
- Guardar las contraseñas de `config/usuarios.json` (usuarios `eli` y `jefe`) fuera del contenedor.
- Cambiar el logo provisional (SVG en `web/sitio/app.js`) por el archivo original de Laureate.
- Publicar `site/` en Netlify o Cloudflare Pages (https).
- Volver a correr `python scripts/build_site.py` después de cada cambio del informe para que el sitio lleve la versión nueva.
