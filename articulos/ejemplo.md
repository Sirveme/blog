---
titulo: "Artículo de ejemplo: cómo se ve y cómo se escribe"
resumen: "Plantilla de referencia del blog. Muestra encabezados, tablas ordenables, citas, listas y notas al pie tal como se verán publicados."
fecha: 2026-09-06
actualizado: 2026-09-06
autor: "Duilio Restuccia Eslava"
categoria: "Tecnología"
tags: ["plantilla", "redacción"]
imagen: "/static/og/por-defecto.png"
destacado: true
derivados:
  - "LinkedIn: post de lanzamiento del blog"
  - "Video corto: 90 segundos"
---

Este archivo existe para dos cosas: servir de plantilla al escribir un artículo
nuevo y comprobar visualmente que todo renderiza como debe. Se puede borrar el
día que haya artículos reales.

## Cómo se publica

Publicar es escribir un archivo y hacer push. No hay base de datos, ni panel de
administración, ni formulario. Los pasos:

1. Copiar este archivo a `articulos/<slug>.md`. El nombre del archivo **es** la
   URL: `articulos/pcge-2026.md` se publica en `/pcge-2026`.
2. Completar el frontmatter. `titulo`, `resumen` y `fecha` son obligatorios.
3. Escribir el cuerpo en Markdown.
4. `git push`. Railway despliega y el artículo queda en línea.

El tiempo de lectura no se escribe: se calcula a partir del número de palabras,
a razón de 200 por minuto.

### Las seis categorías

Son fijas: Contabilidad, Tributación, Gestión Empresarial, Tecnología,
Inteligencia Artificial y Sector Público. Si el frontmatter trae una categoría
que no está en esa lista, el artículo se publica igual —sin categoría— y el
error queda en el log del servidor. Un typo no tumba el sitio.[^1]

En el índice solo aparecen las categorías que ya tienen al menos un artículo.

## Tablas

Cualquier tabla de Markdown se vuelve interactiva sola, sin sintaxis especial.
Se puede ordenar por cualquier columna, filtrar cuando pasa de ocho filas y
copiarla al portapapeles en un formato que Excel pega en celdas separadas.

Los datos de abajo son ficticios y están solo para probar el ordenamiento:

| Concepto            | Monto (S/) | Vencimiento | Días | Estado      |
|---------------------|-----------:|-------------|-----:|-------------|
| Alfa Contratistas   |   12,450.00 | 2026-01-15  |   30 | Pagado      |
| Beta Servicios      |    3,120.50 | 2026-02-28  |   45 | Pendiente   |
| Gamma Importaciones |   87,900.00 | 2026-03-10  |   15 | Pagado      |
| Delta Consultores   |      980.75 | 2026-04-02  |   60 | Observado   |
| Épsilon Logística   |   45,300.20 | 2026-04-30  |   30 | Pendiente   |
| Zeta Manufactura    |  103,750.00 | 2026-05-18  |   90 | Pagado      |
| Eta Distribuciones  |    7,640.10 | 2026-06-05  |   30 | Pendiente   |
| Theta Ingeniería    |   26,015.90 | 2026-06-22  |   45 | Pagado      |
| Iota Transportes    |    1,205.00 | 2026-07-08  |   15 | Observado   |
| Kappa Agroindustria |   64,880.40 | 2026-07-25  |   60 | Pendiente   |
| Lambda Retail       |    9,470.00 | 2026-08-11  |   30 | Pagado      |
| Mu Tecnología       |  158,200.65 | 2026-08-29  |   90 | Pendiente   |

Nótese que la columna de montos se ordena como número, no como texto: 9,470.00
va antes que 12,450.00, y no al revés. Lo mismo con las fechas.

## Citas y datos

Una cita en bloque se marca con `>` y sale con una barra ámbar al costado:

> Toda norma tiene dos vidas: la que dice el texto y la que ocurre cuando la
> aplican quinientas empresas al mismo tiempo. La segunda es la que interesa.

Las cifras y los códigos van en `mono`: la cuenta `10 Efectivo y equivalentes
de efectivo`, el formulario `PDT 621`, el `18%` del IGV.

### Lo que este blog todavía no tiene

Y es deliberado:

- Valoración con estrellas ni captura de opiniones.
- Comentarios —LinkedIn tampoco permite comentar desde una web externa—.
- Comparativas descargables ni panel de administración.
- Buscador.

Cada una de esas piezas entra después, cuando haya artículos que la justifiquen.
Publicar hoy vale más que publicar completo.

[^1]: El detalle queda registrado en el log de Railway con el nombre del archivo
y la categoría inválida, para poder corregirlo en el siguiente push.
