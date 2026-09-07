/* compartir.js — compartir, copiar y citar.
   LinkedIn retiró de su API la posibilidad de comentar desde una web externa:
   aquí solo se comparte. No hay comentarios de LinkedIn ni los habrá. */
(function () {
  "use strict";

  var art = document.querySelector(".articulo");
  if (!art) return;

  var URL_ART = art.dataset.url || location.href;
  var TITULO = art.dataset.titulo || document.title;
  var RESUMEN = art.dataset.resumen || "";
  var CITA = art.dataset.cita || (TITULO + " " + URL_ART);

  var e = encodeURIComponent;

  var enlaces = {
    "a-linkedin": "https://www.linkedin.com/sharing/share-offsite/?url=" + e(URL_ART),
    "a-whatsapp": "https://wa.me/?text=" + e(TITULO + " " + URL_ART),
    "a-facebook": "https://www.facebook.com/sharer/sharer.php?u=" + e(URL_ART)
  };
  Object.keys(enlaces).forEach(function (id) {
    var a = document.getElementById(id);
    if (a) a.href = enlaces[id];
  });

  // Lo que copia cada botón.
  var textos = {
    url: URL_ART,
    // Pensado para pegar directo en un post: resumen + enlace.
    resumen: (RESUMEN ? RESUMEN + "\n\n" : "") + URL_ART,
    cita: CITA
  };

  function copiar(txt) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(txt);
    }
    return new Promise(function (ok, mal) {
      var ta = document.createElement("textarea");
      ta.value = txt;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      var bien = false;
      try { bien = document.execCommand("copy"); } catch (err) { bien = false; }
      document.body.removeChild(ta);
      bien ? ok() : mal(new Error("sin portapapeles"));
    });
  }

  function confirmar(boton, mensaje) {
    var et = boton.querySelector(".et");
    if (!et) return;
    if (!boton.dataset.original) boton.dataset.original = et.textContent;
    et.textContent = mensaje;
    boton.classList.add("hecho");
    clearTimeout(boton._t);
    boton._t = setTimeout(function () {
      et.textContent = boton.dataset.original;
      boton.classList.remove("hecho");
    }, 1800);
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-copiar]"),
    function (boton) {
      boton.addEventListener("click", function () {
        var txt = textos[boton.dataset.copiar];
        if (!txt) return;
        copiar(txt)
          .then(function () { confirmar(boton, "Copiado"); })
          .catch(function () { confirmar(boton, "No se pudo"); });
      });
    }
  );
})();
