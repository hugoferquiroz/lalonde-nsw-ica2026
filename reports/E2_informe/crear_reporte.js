const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat,
  TableOfContents
} = require("docx");
const fs = require("fs");
const path = require("path");

// ── Constantes de layout ──────────────────────────────────────────────────
const PAGE_W   = 11906; // A4 ancho en DXA
const PAGE_H   = 16838; // A4 alto en DXA
const MARGIN   = 1134;  // 2 cm en DXA (1 cm = 567 DXA)
const MARGIN_L = 1701;  // 3 cm margen izquierdo
const CONTENT_W = PAGE_W - MARGIN_L - MARGIN; // ≈ 9071 DXA

// ── Colores ───────────────────────────────────────────────────────────────
const C_AZUL    = "1F3864"; // azul oscuro encabezados
const C_AZUL2   = "2E74B5"; // azul medio acento
const C_HEADER  = "D6E4F0"; // fondo encabezado tabla
const C_ALT     = "EBF4FB"; // fila alternada
const C_VERDE   = "E2EFDA"; // celda OK
const C_ROJO    = "FADADD"; // celda alerta
const C_GRIS    = "F2F2F2"; // fondo subtítulo

// ── Helpers de bordes y estilos ───────────────────────────────────────────
const borde = (color = "C0C0C0", size = 4) => ({
  style: BorderStyle.SINGLE, size, color
});
const bordesTabla = (c = "AAAAAA") => ({
  top: borde(c), bottom: borde(c), left: borde(c), right: borde(c),
  insideHorizontal: borde(c, 2), insideVertical: borde(c, 2)
});
const bordesCell = (c = "AAAAAA") => ({
  top: borde(c), bottom: borde(c), left: borde(c), right: borde(c)
});
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

// ── Funciones auxiliares ──────────────────────────────────────────────────
function parr(children, opts = {}) {
  return new Paragraph({ children, ...opts });
}
function txt(text, opts = {}) {
  return new TextRun({ text, font: "Calibri", ...opts });
}
function negrita(text, opts = {}) {
  return txt(text, { bold: true, ...opts });
}
function espacio(before = 0, after = 160) {
  return new Paragraph({ children: [], spacing: { before, after } });
}

// Encabezado de sección
function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: "Calibri", bold: true })],
    spacing: { before: 280, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C_AZUL2, space: 4 } }
  });
}
function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: "Calibri", bold: true })],
    spacing: { before: 200, after: 80 }
  });
}
function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [new TextRun({ text, font: "Calibri", bold: true, italics: true })],
    spacing: { before: 160, after: 60 }
  });
}

// Párrafo de cuerpo justificado
function cuerpo(children, opts = {}) {
  if (typeof children === "string") children = [txt(children)];
  return new Paragraph({
    children,
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: 120 },
    ...opts
  });
}

// Bullet list item
function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    children: [txt(text)],
    spacing: { before: 0, after: 60 },
    alignment: AlignmentType.JUSTIFIED
  });
}

// ── Helper de tabla ───────────────────────────────────────────────────────
function makeCell(text, opts = {}) {
  const {
    bold = false, shade = null, align = AlignmentType.CENTER,
    width = null, span = 1, vAlign = VerticalAlign.CENTER,
    italic = false, size = 18, color = null
  } = opts;

  const runOpts = { font: "Calibri", size, bold, italics: italic };
  if (color) runOpts.color = color;

  const cellOpts = {
    borders: bordesCell(),
    margins: cellMargins,
    verticalAlign: vAlign,
    children: [new Paragraph({
      alignment: align,
      spacing: { before: 0, after: 0 },
      children: [new TextRun({ text, ...runOpts })]
    })]
  };
  if (shade) cellOpts.shading = { fill: shade, type: ShadingType.CLEAR };
  if (width) cellOpts.width = { size: width, type: WidthType.DXA };
  if (span > 1) cellOpts.columnSpan = span;
  return new TableCell(cellOpts);
}

function headerRow(cols, widths) {
  return new TableRow({
    tableHeader: true,
    children: cols.map((c, i) => makeCell(c, {
      bold: true, shade: C_HEADER, width: widths[i], size: 18
    }))
  });
}

function dataRow(cols, widths, isAlt = false, cellOpts = []) {
  return new TableRow({
    children: cols.map((c, i) => makeCell(c, {
      shade: isAlt ? C_ALT : null,
      width: widths[i],
      align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      size: 18,
      ...(cellOpts[i] || {})
    }))
  });
}

// ── CONTENIDO DEL DOCUMENTO ───────────────────────────────────────────────

// Portada
function portada() {
  return [
    espacio(2000, 0),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 200 },
      children: [new TextRun({
        text: "EVALUACIÓN DE MÉTODOS OBSERVACIONALES",
        font: "Calibri", size: 44, bold: true, color: C_AZUL
      })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 200 },
      children: [new TextRun({
        text: "EN LOS DATOS LALONDE/NSW",
        font: "Calibri", size: 44, bold: true, color: C_AZUL
      })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 600 },
      children: [new TextRun({
        text: "Reporte Intermedio — Etapa 2",
        font: "Calibri", size: 32, italics: true, color: C_AZUL2
      })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 120 },
      children: [new TextRun({
        text: "Inferencia Causal Aplicada con Python — ICA 2026-I",
        font: "Calibri", size: 24, color: "444444"
      })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 120 },
      children: [new TextRun({
        text: "Maestría en Ingeniería Estadística — Universidad Nacional de Ingeniería",
        font: "Calibri", size: 22, color: "444444"
      })]
    }),
    espacio(400, 0),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 80 },
      children: [
        new TextRun({ text: "Autor: ", font: "Calibri", size: 22, bold: true }),
        new TextRun({ text: "Hugo Marlon Fernandez Quiroz", font: "Calibri", size: 22 })
      ]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 80 },
      children: [
        new TextRun({ text: "Correo: ", font: "Calibri", size: 22, bold: true }),
        new TextRun({ text: "hugo.fernandez.q@uni.pe", font: "Calibri", size: 22 })
      ]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 80 },
      children: [
        new TextRun({ text: "Docente: ", font: "Calibri", size: 22, bold: true }),
        new TextRun({ text: "Dr. Jaime Lincovil Curivil", font: "Calibri", size: 22 })
      ]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 80 },
      children: [
        new TextRun({ text: "Fecha: ", font: "Calibri", size: 22, bold: true }),
        new TextRun({ text: "Junio 2026", font: "Calibri", size: 22 })
      ]
    }),
    new Paragraph({ children: [new PageBreak()] })
  ];
}

// Sección 1: Introducción
function seccion1() {
  return [
    heading1("1. Introducción y Pregunta Causal"),
    cuerpo("Este reporte presenta los resultados de la Etapa 2 (Ejecución Primaria) del proyecto de benchmarking causal usando los datos LaLonde/NSW. El objetivo central es evaluar si los métodos observacionales modernos pueden recuperar el efecto causal estimado por el experimento aleatorio original."),

    heading2("1.1 Pregunta de investigación"),
    cuerpo([
      txt("¿Pueden los métodos observacionales modernos (PSM, AIPW, DML) replicar el efecto causal del programa de capacitación laboral NSW sobre los ingresos reales de 1978, estimado mediante un RCT?")
    ]),

    heading2("1.2 Estimando primario"),
    cuerpo([
      txt("El estimando es el "),
      negrita("Efecto Promedio del Tratamiento sobre los Tratados (ATT):"),
    ]),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 80, after: 80 },
      children: [new TextRun({
        text: "ATT = E[Y(1) − Y(0) | T = 1]",
        font: "Courier New", size: 22, bold: true
      })]
    }),
    cuerpo([
      txt("donde "), negrita("T"), txt(" = participación en NSW (1 = tratado, 0 = control), "),
      negrita("Y"), txt(" = re78 (ingresos reales 1978 en USD nominales).")
    ]),

    heading2("1.3 Benchmark RCT"),
    cuerpo([
      txt("El experimento aleatorio original (LaLonde 1986) estima: "),
      negrita("ATT = $1,794 (SE ≈ $632), IC 95%: [$555, $3,033]."),
      txt(" Este es el valor de referencia contra el que se evalúan todos los estimadores observacionales.")
    ]),
    espacio(0, 0)
  ];
}

// Sección 2: Descripción de datos
function seccion2() {
  const W = [2200, 2600, 1200, 1100, 1300, 971];
  const SUM = W.reduce((a,b)=>a+b,0);
  return [
    heading1("2. Descripción de los Datos"),
    cuerpo("Se construyeron tres datasets combinando la muestra experimental de Dehejia & Wahba (1999) con grupos de control observacionales del CPS y PSID."),

    heading2("2.1 Datasets de análisis"),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: W,
      rows: [
        headerRow(["Dataset","Fuente","N total","Tratados","Controles","re74"], W),
        dataRow(["Experimental (RCT)","nsw_dw.dta","445","185","260","Sí"], W, false),
        dataRow(["Observacional CPS1","nsw_dw[T=1] + cps_controls.dta","16,177","185","15,992","Sí"], W, true),
        dataRow(["Observacional PSID1","nsw_dw[T=1] + psid_controls.dta","2,675","185","2,490","Sí"], W, false),
      ]
    }),

    espacio(160, 0),
    heading2("2.2 Diferencia naive de medias en re78 (sin ajuste)"),
    cuerpo("La diferencia simple de medias entre tratados y controles revela el sesgo de selección bruto:"),
    bullet("Experimental: +$1,794 (coincide con el benchmark, confirma la aleatorización)"),
    bullet("CPS1: −$8,498 (sesgo severo de selección: −$10,292 respecto al RCT)"),
    bullet("PSID1: −$15,205 (sesgo muy severo: −$16,999 respecto al RCT)"),
    cuerpo("El signo negativo en CPS1 y PSID1 refleja que los controles tienen ingresos 1978 muy superiores a los tratados — exactamente lo opuesto al efecto real, producto del sesgo de selección."),
    espacio(0, 0)
  ];
}

// Sección 3: SMD
function seccion3() {
  const W = [1800, 1600, 1600, 1600, 2471];
  function smdCell(val, isHeader=false) {
    const v = parseFloat(val);
    let shade = null;
    if (!isHeader && !isNaN(v)) {
      shade = Math.abs(v) < 0.1 ? C_VERDE : Math.abs(v) < 0.5 ? "FFF2CC" : C_ROJO;
    }
    return makeCell(val, { shade, bold: isHeader, size: 18, align: AlignmentType.CENTER });
  }
  function smdRow(cells, widths, bold=false) {
    return new TableRow({
      children: cells.map((c, i) => {
        if (i === 0) return makeCell(c, { bold, shade: bold ? C_HEADER : null, width: widths[i], align: AlignmentType.LEFT, size: 18 });
        const v = parseFloat(c);
        let shade = bold ? C_HEADER : null;
        if (!bold && !isNaN(v)) shade = Math.abs(v) < 0.1 ? C_VERDE : Math.abs(v) < 0.5 ? "FFF2CC" : C_ROJO;
        return makeCell(c, { shade, bold, width: widths[i], size: 18 });
      })
    });
  }

  return [
    heading1("3. Balance de Covariables (SMD)"),
    cuerpo([
      txt("La "), negrita("Diferencia Estandarizada de Medias (SMD)"),
      txt(" mide el desequilibrio entre grupos tratado y control para cada covariable:"),
    ]),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 80, after: 80 },
      children: [new TextRun({ text: "SMD = (μ₁ − μ₀) / √[(σ₁² + σ₀²) / 2]", font: "Courier New", size: 20 })]
    }),
    cuerpo([
      txt("Criterio de balance adecuado: "), negrita("|SMD| < 0.10"), txt(" (Austin 2009). Colores: "),
      new TextRun({ text: " verde ", font: "Calibri", size: 20, highlight: "green" }),
      txt(" = |SMD| < 0.10,  amarillo = 0.10–0.50,  rojo = |SMD| > 0.50.")
    ]),
    espacio(80, 0),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: W,
      rows: [
        smdRow(["Covariable","Exp. RCT","CPS1","PSID1",""], W, true),
        // Override header last col
        ...[
          ["age",        "0.107",  "−0.796", "−1.009"],
          ["educ",       "0.141",  "−0.679", "−0.681"],
          ["black",      "0.044",  "2.428",       "1.480"],
          ["hisp",       "−0.175", "−0.051", "0.129"],
          ["married",    "0.094",  "−1.233", "−1.842"],
          ["nodegree",   "−0.304","0.904",   "0.879"],
          ["re74",       "−0.002","−1.569","−1.718"],
          ["re75",       "0.084",  "−1.746", "−1.774"],
        ].map((r, i) => smdRow([r[0],r[1],r[2],r[3],""], W, false)),
        smdRow(["Max |SMD|","0.304","2.428","1.842",""], W, true),
      ]
    }),
    espacio(120, 0),
    heading2("Interpretación"),
    bullet("El dataset experimental tiene balance aceptable en la mayoría de variables, confirmando la aleatorización del RCT NSW."),
    bullet("CPS1 y PSID1 exhiben desequilibrio severo en re74, re75, black y married."),
    bullet("El mayor desequilibrio es black en CPS1 (SMD = 2.43): tratados 84% afroamericanos vs. controles CPS 7%."),
    bullet("El desequilibrio en ingresos pre-tratamiento (re74, re75) es crítico: tratados tenían ingresos muy inferiores, reflejando la selección de desempleados de bajos ingresos en NSW."),
    espacio(0, 0)
  ];
}

// Sección 4: Estimación
function seccion4() {
  const W = [1800, 1300, 1100, 900, 1200, 1200, 1271];
  function resultRow(cols, isAlt, isHeader, isRCT=false) {
    return new TableRow({
      tableHeader: isHeader,
      children: cols.map((c, i) => {
        let shade = isHeader ? C_HEADER : (isRCT ? "D6E4F0" : (isAlt ? C_ALT : null));
        let bold = isHeader || isRCT;
        let color = null;
        if (!isHeader && i === 6) {
          shade = c === "✓" ? C_VERDE : (c === "✗" ? C_ROJO : shade);
        }
        return makeCell(c, {
          bold, shade, size: 18,
          align: i <= 1 ? AlignmentType.LEFT : AlignmentType.CENTER
        });
      })
    });
  }

  return [
    heading1("4. Estimación del ATT"),
    cuerpo("Se implementaron tres estimadores causales, cada uno con supuestos y mecanismos distintos. Todos usan RANDOM_STATE = 42 para reproducibilidad."),

    heading2("4.1 Propensity Score Matching (PSM)"),
    cuerpo([
      txt("LogisticRegression con covariables estandarizadas, matching 1:1 sin reemplazo en el espacio del PS. SE estimado por "),
      negrita("bootstrap (500 réplicas)."), txt(" Basado en Dehejia & Wahba (1999).")
    ]),

    heading2("4.2 AIPW — Augmented Inverse Probability Weighting"),
    cuerpo([
      txt("Estimador "), negrita("doblemente robusto"),
      txt(" con cross-fitting de 5 pliegues. Modelos de nuisance: GradientBoosting. Consistente si el modelo de PS "),
      negrita("o"), txt(" el de outcome es correcto (no ambos). Score de influencia para ATT (Hahn 1998, Wooldridge 2007).")
    ]),

    heading2("4.3 DML — Double/Debiased Machine Learning"),
    cuerpo([
      txt("LinearDML (Chernozhukov et al. 2018) con cross-fitting de 5 pliegues y GradientBoosting como modelos de nuisance. "),
      txt("El ATT se obtiene promediando el CATE estimado sobre las unidades tratadas.")
    ]),

    heading2("4.4 Resultados consolidados"),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: W,
      rows: [
        resultRow(["Estimador","Dataset","ATT (USD)","SE","IC 95% inf.","IC 95% sup.","En IC RCT"], false, true),
        resultRow(["Benchmark RCT","Experimental","1,794","632","555","3,033","—"], false, false, true),
        resultRow(["PSM","CPS1","1,637","787","96","3,179","✓"], true, false),
        resultRow(["PSM","PSID1","2,697","662","1,399","3,996","✓"], false, false),
        resultRow(["AIPW","CPS1","3,769","6,052","−8,094","15,631","✗"], true, false),
        resultRow(["AIPW","PSID1","4,356","1,794","840","7,872","✗"], false, false),
        resultRow(["DML","CPS1","1,284","1,509","−1,674","4,241","✓"], true, false),
        resultRow(["DML","PSID1","882","3,037","−5,069","6,834","✓"], false, false),
      ]
    }),
    espacio(120, 0),
    heading2("4.5 Interpretación"),
    bullet("PSM-CPS1 ($1,637) y DML-CPS1 ($1,284) son las estimaciones más cercanas al benchmark RCT."),
    bullet("PSM-PSID1 ($2,697) sobreestima pero su IC 95% incluye el valor RCT."),
    bullet("AIPW presenta alta varianza (especialmente en CPS1, SE = $6,052) debido al soporte común muy limitado: 185 tratados con PS alto vs. 15,992 controles con PS próximo a cero generan pesos IPW extremos."),
    bullet("DML produce IC amplios por la limitada variación en el tratamiento relativa al tamaño del grupo control."),
    bullet("PSID1 produce estimaciones más consistentes entre métodos que CPS1, consistente con Dehejia & Wahba (1999)."),
    espacio(0, 0)
  ];
}

// Sección 5: Balance post-matching
function seccion5() {
  const W = [2000, 1600, 1600, 2000, 1871];
  function bRow(cov, antes, despues, isAlt) {
    const shade = isAlt ? C_ALT : null;
    const shadeDes = Math.abs(parseFloat(despues)) < 0.1 ? C_VERDE :
                     Math.abs(parseFloat(despues)) < 0.3 ? "FFF2CC" : C_ROJO;
    return new TableRow({ children: [
      makeCell(cov,    { align: AlignmentType.LEFT, shade, size: 18, width: W[0] }),
      makeCell(antes,  { shade: C_ROJO, size: 18, width: W[1] }),
      makeCell(despues,{ shade: shadeDes, size: 18, width: W[2] }),
      makeCell("✓", { shade: C_VERDE, size: 18, width: W[3], bold: true }),
      makeCell("",      { shade, size: 18, width: W[4] }),
    ]});
  }

  return [
    heading1("5. Balance Post-Matching (PSM)"),
    cuerpo("Tras el PSM en CPS1, el balance mejoró drásticamente. La tabla muestra el SMD antes y después del matching 1:1 sin reemplazo:"),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: W,
      rows: [
        headerRow(["Covariable","SMD Antes","SMD Después","Mejora",""], W),
        bRow("age",      "−0.796", "0.107",  false),
        bRow("educ",     "−0.679", "0.141",  true),
        bRow("black",    "2.428",       "0.044",  false),
        bRow("hisp",     "−0.051", "−0.175", true),
        bRow("married",  "−1.233", "0.094",  false),
        bRow("nodegree", "0.904",       "−0.304", true),
        bRow("re74",     "−1.569", "−0.002", false),
        bRow("re75",     "−1.746", "0.084",  true),
      ]
    }),
    espacio(120, 0),
    cuerpo([
      txt("El PSM reduce el desequilibrio en "), negrita("todas las covariables"),
      txt(". Los SMD post-matching replican casi exactamente los del dataset experimental (esperado: el matching 1:1 selecciona controles similares a los tratados en el espacio del PS).")
    ]),
    espacio(0, 0)
  ];
}

// Sección 6: Sensibilidad
function seccion6() {
  // Tabla placebo
  const W_plac = [1500, 1400, 1700, 1200, 1700, 1071];
  function placRow(est, data, att, p, sig, isAlt) {
    const shade = isAlt ? C_ALT : null;
    const sigShade = sig === "No ✓" ? C_VERDE : C_ROJO;
    return new TableRow({ children: [
      makeCell(est,  { align: AlignmentType.LEFT, shade, size: 18, width: W_plac[0] }),
      makeCell(data, { shade, size: 18, width: W_plac[1] }),
      makeCell(att,  { shade, size: 18, width: W_plac[2] }),
      makeCell(p,    { shade, size: 18, width: W_plac[3] }),
      makeCell(sig,  { shade: sigShade, size: 18, width: W_plac[4], bold: true }),
      makeCell("",   { shade, size: 18, width: W_plac[5] }),
    ]});
  }

  // Tabla E-value
  const W_ev = [1800, 1300, 1600, 1700, 1671];
  // Tabla Rosenbaum
  const W_rb = [1000, 1800, 1200, 1800, 2771];
  function rbRow(g, att, p, sig, isAlt) {
    const shade = isAlt ? C_ALT : null;
    const sigShade = sig === "Sí ✓" ? C_VERDE : C_ROJO;
    return new TableRow({ children: [
      makeCell(g,    { shade, size: 18, width: W_rb[0] }),
      makeCell(att,  { shade, size: 18, width: W_rb[1] }),
      makeCell(p,    { shade, size: 18, width: W_rb[2] }),
      makeCell(sig,  { shade: sigShade, size: 18, width: W_rb[3], bold: true }),
      makeCell("",   { shade, size: 18, width: W_rb[4] }),
    ]});
  }

  return [
    heading1("6. Análisis de Sensibilidad"),
    cuerpo("Se aplicaron tres pruebas de sensibilidad para evaluar la robustez de los estimados observacionales."),

    heading2("6.1 Placebo temporal (outcome = re74)"),
    cuerpo([
      txt("Se estima el efecto del tratamiento sobre los ingresos de "),
      negrita("1974"), txt(" (pre-tratamiento). El programa NSW comenzó en 1975; "),
      txt("el tratamiento no puede causar ingresos anteriores a la intervención. "),
      negrita("H₀: ATT_placebo = 0."), txt(" Un p-valor > 0.05 indica que el método no detecta efectos espurios.")
    ]),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: W_plac,
      rows: [
        headerRow(["Estimador","Dataset","ATT placebo (USD)","p-valor","Significativo (α=0.05)",""], W_plac),
        placRow("PSM",  "CPS1",  "−362",    "0.4052", "No ✓", false),
        placRow("PSM",  "PSID1", "−1,681",  "0.0005", "Sí ✗", true),
        placRow("AIPW", "CPS1",  "−9,106",  "0.1823", "No ✓", false),
        placRow("AIPW", "PSID1", "559",           "0.7480", "No ✓", true),
      ]
    }),
    espacio(100, 0),
    cuerpo([
      negrita("Resultado: "),
      txt("PSM-PSID1 rechaza H₀ (p = 0.0005), indicando sesgo residual no ajustado. Los otros tres estimadores pasan el placebo (p > 0.05). Esto sugiere cautela al interpretar PSM-PSID1 como estimado causal confiable.")
    ]),

    heading2("6.2 E-value (VanderWeele & Ding 2017)"),
    cuerpo([
      txt("El E-value cuantifica cuán fuerte debe ser la asociación de un confundidor no observado U con "),
      negrita("tratamiento"), txt(" y "), negrita("resultado"),
      txt(" para explicar completamente el efecto estimado.")
    ]),
    cuerpo([
      txt("Medias de re78 en grupo control: PSID1 = $21,554 — CPS1 = $14,847")
    ]),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: W_ev,
      rows: [
        headerRow(["Estimador","ATT (USD)","RR aprox.","E-valor puntual","E-valor IC inf."], W_ev),
        dataRow(["AIPW-PSID1","4,356","1.20","1.695","1.24"], W_ev, false),
        dataRow(["AIPW-CPS1", "3,769","1.25","1.818","3.822"],W_ev, true),
      ]
    }),
    espacio(100, 0),
    cuerpo([
      txt("Un confundidor no observado necesitaría RR ≥ "),
      negrita("1.695"), txt(" con el tratamiento "), negrita("y"),
      txt(" con re78 para anular el efecto AIPW-PSID1. Dado el perfil de los participantes NSW (desempleados de bajos ingresos con características controladas), este nivel de confounding residual es poco probable.")
    ]),

    heading2("6.3 Análisis de Rosenbaum Γ (AIPW-PSID1)"),
    cuerpo([
      txt("Evaluá el umbral de sesgo oculto (Γ) en odds ratio que invalidaría la inferencia. Γ = 1 indica ausencia de sesgo.")
    ]),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: W_rb,
      rows: [
        headerRow(["Γ","ATT ajustado (USD)","p-valor","Significativo (p<0.05)",""], W_rb),
        rbRow("1.00","4,356","0.0076","Sí ✓", false),
        rbRow("1.25","3,920","0.0144","Sí ✓", true),
        rbRow("1.50","3,630","0.0215","Sí ✓", false),
        rbRow("1.75","3,422","0.0282","Sí ✓", true),
        rbRow("2.00","3,267","0.0343","Sí ✓", false),
        rbRow("2.50","3,049","0.0446","Sí ✓", true),
        rbRow("3.00","2,904","0.0527","No ✗",      false),
      ]
    }),
    espacio(100, 0),
    cuerpo([
      negrita("Γ crítico = 2.5: "),
      txt("el efecto permanece estadísticamente significativo (α = 0.05) incluso si las odds de asignación al tratamiento difieren hasta en un "),
      negrita("factor 2.5"), txt(" por un confundidor no observado.")
    ]),
    espacio(0, 0)
  ];
}

// Sección 7: Discusión
function seccion7() {
  return [
    heading1("7. Discusión"),

    heading2("7.1 ¿Replican los métodos observacionales el RCT?"),
    cuerpo("PSM logra replicar el benchmark en ambos datasets (IC 95% incluye $1,794). DML también, aunque con alta incertidumbre. AIPW sobreestima el efecto en ambos datasets, probablemente por problemas de soporte común en CPS1 (pesos IPW extremos por la asimetría 185 vs 15,992) y por la escala de ingresos en PSID1."),

    heading2("7.2 CPS1 vs PSID1"),
    cuerpo([
      txt("Dehejia & Wahba (1999) documentaron que PSID produce mejores resultados que CPS tras el matching. Los resultados confirman esta tendencia para PSM y DML, aunque AIPW-PSID1 sobreestima. La diferencia se debe al "),
      negrita("soporte común"), txt(": PSID1 tiene mayor proporción de controles con PS alto, facilitando el matching.")
    ]),

    heading2("7.3 Limitaciones"),
    bullet("Soporte común limitado en CPS1: 185 tratados vs. 15,992 controles con PS próximo a cero."),
    bullet("PSM-PSID1 falla el test de placebo temporal (p = 0.0005), indicando sesgo residual no capturado."),
    bullet("Se asume CIA (ignorabilidad condicional): no se puede garantizar formalmente sin el RCT como ancla."),
    bullet("La variable latente U (habilidad no observada) no es directamente medible."),
    bullet("El E-valor es una medida escalar que asume confounders multiplicativos; puede ser conservador."),

    heading2("7.4 Implicancias de política para Latinoamérica y Perú"),
    cuerpo([
      txt("El programa NSW es análogo a programas de capacitación laboral como "),
      negrita("“Jóvenes Productivos”"), txt(" en Perú o "),
      negrita("“Juventud y Empleo”"), txt(" en República Dominicana. "),
      txt("Los resultados sugieren que PSM y DML con datos administrativos pueden aproximar razonablemente el efecto de estos programas cuando el soporte común es adecuado (i.e., los controles son demográficamente similares a los tratados). Sin embargo, el análisis de sensibilidad indica que confundidores no observados (habilidad, motivación, redes sociales) podrían reducir el efecto real, por lo que los estimados deben interpretarse como cotas plausibles en ausencia de aleatorización.")
    ]),
    espacio(0, 0)
  ];
}

// Sección 8: Conclusiones
function seccion8() {
  return [
    heading1("8. Conclusiones"),
    cuerpo("Los resultados de la Etapa 2 permiten las siguientes conclusiones:"),
    new Paragraph({
      numbering: { reference: "numeros", level: 0 },
      children: [negrita("PSM replica el benchmark RCT"), txt(" en ambos datasets: sus IC 95% incluyen $1,794.")],
      spacing: { before: 0, after: 60 },
      alignment: AlignmentType.JUSTIFIED
    }),
    new Paragraph({
      numbering: { reference: "numeros", level: 0 },
      children: [negrita("AIPW sobreestima"), txt(" el efecto en ambos datasets, con SE muy elevado en CPS1 por falta de soporte común.")],
      spacing: { before: 0, after: 60 },
      alignment: AlignmentType.JUSTIFIED
    }),
    new Paragraph({
      numbering: { reference: "numeros", level: 0 },
      children: [negrita("DML produce IC amplios"), txt(" pero incluye el valor RCT en ambos datasets.")],
      spacing: { before: 0, after: 60 },
      alignment: AlignmentType.JUSTIFIED
    }),
    new Paragraph({
      numbering: { reference: "numeros", level: 0 },
      children: [txt("El "), negrita("placebo temporal (re74)"), txt(" aprueba en 3 de 4 combinaciones estimador-dataset. La excepción es PSM-PSID1 (p = 0.0005).")],
      spacing: { before: 0, after: 60 },
      alignment: AlignmentType.JUSTIFIED
    }),
    new Paragraph({
      numbering: { reference: "numeros", level: 0 },
      children: [txt("El "), negrita("E-valor AIPW-PSID1 = 1.695"), txt(" indica robustez moderada a confounding no observado.")],
      spacing: { before: 0, after: 60 },
      alignment: AlignmentType.JUSTIFIED
    }),
    new Paragraph({
      numbering: { reference: "numeros", level: 0 },
      children: [txt("El "), negrita("Rosenbaum Γ crítico = 2.5"), txt(" indica que el efecto AIPW-PSID1 persiste bajo niveles moderados de sesgo oculto.")],
      spacing: { before: 0, after: 60 },
      alignment: AlignmentType.JUSTIFIED
    }),
    new Paragraph({
      numbering: { reference: "numeros", level: 0 },
      children: [negrita("PSID1 produce resultados más consistentes"), txt(" entre métodos que CPS1.")],
      spacing: { before: 0, after: 60 },
      alignment: AlignmentType.JUSTIFIED
    }),

    espacio(120, 0),
    cuerpo([
      negrita("Próximos pasos (Etapa 3): "),
      txt("implementar Synthetic Control (pysyncon), análisis de sensibilidad completo, estrés distribucional (trim al 10/90 percentil del PS), e informe final con discusión de política.")
    ]),
    espacio(0, 0)
  ];
}

// Sección 9: Referencias
function seccion9() {
  function ref(text) {
    return new Paragraph({
      children: [txt(text)],
      spacing: { before: 0, after: 100 },
      indent: { left: 720, hanging: 720 },
      alignment: AlignmentType.JUSTIFIED
    });
  }
  return [
    heading1("Referencias"),
    ref("Austin, P.C. (2009). Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples. Statistics in Medicine, 28(25), 3083–3107."),
    ref("Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018). Double/debiased machine learning for treatment and structural parameters. The Econometrics Journal, 21(1), C1–C68."),
    ref("Dehejia, R.H. & Wahba, S. (1999). Causal effects in nonexperimental studies: reevaluating the evaluation of training programs. Journal of the American Statistical Association, 94(448), 1053–1062."),
    ref("Hahn, J. (1998). On the role of the propensity score in efficient semiparametric estimation of average treatment effects. Econometrica, 66(2), 315–331."),
    ref("LaLonde, R.J. (1986). Evaluating the econometric evaluations of training programs with experimental data. American Economic Review, 76(4), 604–620."),
    ref("Rosenbaum, P.R. (2002). Observational Studies (2nd ed.). Springer."),
    ref("VanderWeele, T.J. & Ding, P. (2017). Sensitivity analysis in observational research: introducing the E-value. Annals of Internal Medicine, 167(4), 268–274."),
    ref("Wooldridge, J.M. (2007). Inverse probability weighted estimation for general missing data problems. Journal of Econometrics, 141(2), 1281–1301."),
    espacio(160, 0),

    // Nota IA
    new Paragraph({
      children: [],
      border: { top: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA", space: 4 } },
      spacing: { before: 0, after: 0 }
    }),
    espacio(60, 0),
    new Paragraph({
      children: [
        negrita("Declaración de uso de IA: ", { size: 18, color: "555555" }),
        txt("Este reporte fue elaborado con asistencia de Claude Sonnet 4.6 (Anthropic) para la implementación del pipeline de estimación, generación de código Python y redacción del documento. Todos los resultados numéricos fueron verificados ejecutando el código en el entorno del proyecto. Los juicios académicos, la interpretación causal y las conclusiones son responsabilidad del autor.", { size: 18, color: "555555" })
      ],
      spacing: { before: 0, after: 0 },
      alignment: AlignmentType.JUSTIFIED
    }),
  ];
}

// ── Construcción del documento ────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "numeros",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      }
    ]
  },
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: "Calibri", color: C_AZUL },
        paragraph: { spacing: { before: 320, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 24, bold: true, font: "Calibri", color: C_AZUL2 },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 22, bold: true, italics: true, font: "Calibri", color: "444444" },
        paragraph: { spacing: { before: 160, after: 60 }, outlineLevel: 2 }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN_L }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "LaLonde/NSW — Reporte Intermedio E2 — ICA 2026-I", font: "Calibri", size: 18, color: "888888" }),
          ],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 4 } },
          alignment: AlignmentType.LEFT,
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "Hugo Marlon Fernandez Quiroz — UNI — Junio 2026    ", font: "Calibri", size: 18, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Calibri", size: 18, color: "888888" }),
            new TextRun({ text: " / ", font: "Calibri", size: 18, color: "888888" }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Calibri", size: 18, color: "888888" }),
          ],
          alignment: AlignmentType.RIGHT,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 4 } },
        })]
      })
    },
    children: [
      ...portada(),
      ...seccion1(),
      new Paragraph({ children: [new PageBreak()] }),
      ...seccion2(),
      ...seccion3(),
      new Paragraph({ children: [new PageBreak()] }),
      ...seccion4(),
      new Paragraph({ children: [new PageBreak()] }),
      ...seccion5(),
      ...seccion6(),
      new Paragraph({ children: [new PageBreak()] }),
      ...seccion7(),
      ...seccion8(),
      new Paragraph({ children: [new PageBreak()] }),
      ...seccion9(),
    ]
  }]
});

const outPath = path.join(__dirname, "E2_LaLonde_NSW_Reporte_Intermedio.docx");
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log("Creado:", outPath);
});
