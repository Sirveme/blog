/* tablas.js — vuelve interactiva cualquier <table> del artículo.
   Sin librerías y sin sintaxis especial en el Markdown: el .md escribe una
   tabla normal y aquí se le añade orden, filtro, scroll y copiado. */
(function () {
  "use strict";

  var FILAS_PARA_FILTRO = 8;   // filtro solo si la tabla supera este número
  var MESES = {
    ene: 1, feb: 2, mar: 3, abr: 4, may: 5, jun: 6,
    jul: 7, ago: 8, set: 9, sep: 9, oct: 10, nov: 11, dic: 12
  };

  /* ---------- Detección de tipo -------------------------------------- */

  // Fechas: 2026-08-28 · 28/08/2026 · 28-08-2026 · 28 de agosto de 2026
  function aFecha(txt) {
    var s = txt.trim().toLowerCase();
    var m = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
    if (m) return Date.UTC(+m[1], +m[2] - 1, +m[3]);
    m = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/);
    if (m) return Date.UTC(+m[3], +m[2] - 1, +m[1]);
    m = s.match(/^(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})/);
    if (m) {
      var mes = MESES[m[2].slice(0, 3)];
      if (mes) return Date.UTC(+m[3], mes - 1, +m[1]);
    }
    return null;
  }

  // Números: 1,234.56 · 1.234,56 · S/ 8 500 · 12% · -3,5
  function aNumero(txt) {
    var s = txt.trim().replace(/^[^\d\-+.,]*/, "").replace(/[^\d\-+.,]*$/, "");
    if (!s || !/\d/.test(s)) return null;
    if (/^-?\d{1,3}(\.\d{3})+(,\d+)?$/.test(s)) {          // formato europeo
      s = s.replace(/\./g, "").replace(",", ".");
    } else {
      s = s.replace(/,/g, "");                              // 1,234.56
    }
    var n = parseFloat(s);
    return isNaN(n) ? null : n;
  }

  function texto(celda) {
    return (celda ? celda.textContent : "").replace(/\s+/g, " ").trim();
  }

  /* Decide el tipo de una columna mirando sus valores no vacíos: si todos son
     números -> numero; si todos son fechas -> fecha; si no -> texto. Así los
     números no se ordenan como cadenas (100 antes que 9). */
  function tipoColumna(filas, i) {
    var vistos = 0, numeros = 0, fechas = 0;
    for (var f = 0; f < filas.length; f++) {
      var t = texto(filas[f].cells[i]);
      if (!t) continue;
      vistos++;
      if (aNumero(t) !== null) numeros++;
      if (aFecha(t) !== null) fechas++;
    }
    if (!vistos) return "texto";
    if (fechas === vistos) return "fecha";
    if (numeros === vistos) return "numero";
    return "texto";
  }

  function valor(fila, i, tipo) {
    var t = texto(fila.cells[i]);
    if (!t) return null;
    if (tipo === "numero") return aNumero(t);
    if (tipo === "fecha") return aFecha(t);
    return t.toLocaleLowerCase("es-PE");
  }

  /* ---------- Orden ---------------------------------------------------- */

  function ordenar(tabla, tbody, i, dir, tipo) {
    var filas = Array.prototype.slice.call(tbody.rows);
    // Orden estable: se guarda la posición original como desempate.
    filas.forEach(function (fila, n) { fila._n = n; });
    filas.sort(function (a, b) {
      var va = valor(a, i, tipo), vb = valor(b, i, tipo);
      if (va === null && vb === null) return a._n - b._n;
      if (va === null) return 1;      // vacíos siempre al final
      if (vb === null) return -1;
      var c;
      if (tipo === "texto") c = va.localeCompare(vb, "es-PE", { numeric: true });
      else c = va < vb ? -1 : va > vb ? 1 : 0;
      return (dir === "desc" ? -c : c) || a._n - b._n;
    });
    filas.forEach(function (fila) { tbody.appendChild(fila); });
  }

  /* ---------- Filtro --------------------------------------------------- */

  function filtrar(tbody, termino, nota) {
    var q = termino.trim().toLocaleLowerCase("es-PE");
    var visibles = 0;
    Array.prototype.forEach.call(tbody.rows, function (fila) {
      var coincide = !q || fila.textContent.toLocaleLowerCase("es-PE").indexOf(q) !== -1;
      fila.classList.toggle("oculta", !coincide);
      if (coincide) visibles++;
    });
    if (nota) {
      nota.textContent = q
        ? visibles + " de " + tbody.rows.length + " filas"
        : tbody.rows.length + " filas";
    }
  }

  /* ---------- Copiar en TSV (pegable en Excel) -------------------------- */

  function tsv(tabla, tbody) {
    var lineas = [];
    var cabeceras = tabla.tHead ? tabla.tHead.rows[0].cells : [];
    if (cabeceras.length) {
      lineas.push(Array.prototype.map.call(cabeceras, texto).join("\t"));
    }
    Array.prototype.forEach.call(tbody.rows, function (fila) {
      if (fila.classList.contains("oculta")) return;   // se copia lo que se ve
      lineas.push(Array.prototype.map.call(fila.cells, texto).join("\t"));
    });
    return lineas.join("\r\n");
  }

  function copiar(txt) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(txt);
    }
    return new Promise(function (ok, mal) {          // http local / navegadores viejos
      var ta = document.createElement("textarea");
      ta.value = txt;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      var bien = false;
      try { bien = document.execCommand("copy"); } catch (e) { bien = false; }
      document.body.removeChild(ta);
      bien ? ok() : mal(new Error("sin portapapeles"));
    });
  }

  function confirmar(boton, textoOk) {
    var original = boton.dataset.original || boton.textContent;
    boton.dataset.original = original;
    boton.textContent = textoOk;
    boton.classList.add("hecho");
    clearTimeout(boton._t);
    boton._t = setTimeout(function () {
      boton.textContent = original;
      boton.classList.remove("hecho");
    }, 1800);
  }

  /* ---------- Montaje --------------------------------------------------- */

  function montar(tabla, indice) {
    if (!tabla.tHead || !tabla.tBodies.length) return;
    var tbody = tabla.tBodies[0];
    if (!tbody.rows.length) return;

    var envoltura = document.createElement("div");
    envoltura.className = "tabla-envoltura";
    tabla.parentNode.insertBefore(envoltura, tabla);

    var barra = document.createElement("div");
    barra.className = "tabla-barra";
    envoltura.appendChild(barra);

    var caja = document.createElement("div");
    caja.className = "tabla-caja";
    caja.setAttribute("tabindex", "0");            // scroll con teclado
    caja.setAttribute("role", "region");
    caja.setAttribute("aria-label", "Tabla de datos " + (indice + 1));
    envoltura.appendChild(caja);
    caja.appendChild(tabla);

    var nota = document.createElement("p");
    nota.className = "tabla-nota";
    nota.textContent = tbody.rows.length + " filas";
    envoltura.appendChild(nota);

    // Filtro solo cuando hay suficientes filas para que sirva.
    if (tbody.rows.length > FILAS_PARA_FILTRO) {
      var filtro = document.createElement("input");
      filtro.type = "search";
      filtro.className = "tabla-filtro";
      filtro.placeholder = "Filtrar en la tabla…";
      filtro.setAttribute("aria-label", "Filtrar filas de la tabla");
      filtro.addEventListener("input", function () { filtrar(tbody, filtro.value, nota); });
      barra.appendChild(filtro);
    }

    var btnCopiar = document.createElement("button");
    btnCopiar.type = "button";
    btnCopiar.className = "tabla-btn";
    btnCopiar.textContent = "Copiar tabla";
    btnCopiar.addEventListener("click", function () {
      copiar(tsv(tabla, tbody))
        .then(function () { confirmar(btnCopiar, "Copiado"); })
        .catch(function () { confirmar(btnCopiar, "No se pudo"); });
    });
    barra.appendChild(btnCopiar);

    // Cabeceras ordenables. El tipo se calcula una vez, al montar.
    var ths = tabla.tHead.rows[0].cells;
    var tipos = [];
    Array.prototype.forEach.call(ths, function (th, i) {
      tipos[i] = tipoColumna(tbody.rows, i);
      if (tipos[i] === "numero") {
        Array.prototype.forEach.call(tbody.rows, function (fila) {
          if (fila.cells[i]) fila.cells[i].classList.add("num");
        });
      }
      th.classList.add("ordenable");
      th.setAttribute("tabindex", "0");
      th.setAttribute("role", "columnheader");
      th.setAttribute("aria-sort", "none");
      th.title = "Ordenar por " + texto(th);

      function alternar() {
        var dir = th.getAttribute("aria-sort") === "ascending" ? "desc" : "asc";
        Array.prototype.forEach.call(ths, function (otro) {
          otro.setAttribute("aria-sort", "none");
        });
        th.setAttribute("aria-sort", dir === "asc" ? "ascending" : "descending");
        ordenar(tabla, tbody, i, dir, tipos[i]);
      }
      th.addEventListener("click", alternar);
      th.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); alternar(); }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var cuerpo = document.getElementById("cuerpo");
    if (!cuerpo) return;
    Array.prototype.forEach.call(cuerpo.querySelectorAll("table"), montar);
  });
})();
