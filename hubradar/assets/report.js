(() => {
  "use strict";
  const all = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const announce = text => { document.getElementById("notice").textContent = text; };
  const themeButton = document.getElementById("theme");
  function setTheme(dark) {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    themeButton.textContent = dark ? "浅色模式" : "深色模式";
    themeButton.setAttribute("aria-pressed", String(dark));
  }
  try { setTheme(localStorage.getItem("hubradar-theme") === "dark"); } catch (_) { setTheme(false); }
  themeButton.addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme !== "dark";
    setTheme(dark);
    try { localStorage.setItem("hubradar-theme", dark ? "dark" : "light"); } catch (_) {}
    requestDiagramRender();
  });
  const expand = document.getElementById("expand");
  expand.addEventListener("click", () => {
    const open = expand.getAttribute("aria-pressed") !== "true";
    all("article details").forEach(detail => { detail.open = open; });
    expand.setAttribute("aria-pressed", String(open));
    expand.textContent = open ? "收起详情" : "展开详情";
  });
  document.getElementById("print").addEventListener("click", () => window.print());
  let printState = [];
  window.addEventListener("beforeprint", () => {
    printState = all("article details").map(node => [node, node.open]);
    printState.forEach(([node]) => { node.open = true; });
  });
  window.addEventListener("afterprint", () => printState.forEach(([node, open]) => { node.open = open; }));
  all("pre").forEach(pre => {
    const code = pre.querySelector("code");
    if (!code) return;
    const button = document.createElement("button");
    button.type = "button"; button.className = "copy-code"; button.textContent = "复制";
    button.addEventListener("click", async () => {
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(code.textContent);
        } else {
          const input = document.createElement("textarea");
          input.value = code.textContent; input.className = "sr-only";
          document.body.append(input); input.select();
          const copied = document.execCommand("copy"); input.remove();
          if (!copied) throw new Error("copy unavailable");
          button.focus();
        }
        button.textContent = "已复制"; announce("代码已复制");
        setTimeout(() => { button.textContent = "复制"; }, 1800);
      } catch (_) { button.textContent = "请选中复制"; announce("无法自动复制，请选中代码复制"); }
    });
    pre.append(button);
  });
  const radarRows = [];
  all("article table").forEach(table => {
    const wrap = document.createElement("div");
    wrap.className = "table-wrap"; wrap.tabIndex = 0;
    wrap.setAttribute("aria-label", "可横向滚动的数据表");
    table.before(wrap); wrap.append(table);
    const headers = all("th", table);
    const isRadar = headers.some(th => th.textContent.trim() === "仓库");
    if (isRadar) {
      table.classList.add("radar-table");
      all("tbody tr", table).forEach(row => {
        radarRows.push(row);
        const cell = row.cells[0], text = cell.textContent.trim(), badge = document.createElement("span");
        badge.className = "tier" + (text === "爆发" ? " tier-burst" : text === "新星" ? " tier-new" : text === "基石" ? " tier-base" : "");
        badge.textContent = text; cell.textContent = ""; cell.append(badge);
      });
    }
    headers.forEach((th, index) => {
      const button = document.createElement("button");
      button.type = "button"; button.className = "sort-button"; button.textContent = th.textContent;
      th.textContent = ""; th.append(button); th.setAttribute("aria-sort", "none");
      button.addEventListener("click", () => {
        const sign = th.getAttribute("aria-sort") === "ascending" ? -1 : 1;
        headers.forEach(other => other.setAttribute("aria-sort", "none"));
        th.setAttribute("aria-sort", sign === 1 ? "ascending" : "descending");
        const text = row => row.cells[index].textContent.trim();
        const number = value => /^-?[\d,.]+(?:\/月| 依赖方)?$/.test(value) ? Number(value.replace(/,/g, "").split(/[ /]/)[0]) : null;
        const rows = all("tbody tr", table).sort((a, b) => {
          const x = text(a), y = text(b), nx = number(x), ny = number(y);
          return sign * (nx !== null && ny !== null ? nx - ny : x.localeCompare(y, "zh-CN", { numeric: true }));
        });
        rows.forEach(row => table.tBodies[0].append(row));
      });
    });
  });
  if (radarRows.length) {
    document.querySelector(".filter-bar").hidden = false;
    const search = document.getElementById("table-search"), count = document.getElementById("row-count");
    const filter = () => {
      const query = search.value.trim().toLocaleLowerCase();
      radarRows.forEach(row => { row.hidden = !row.textContent.toLocaleLowerCase().includes(query); });
      count.textContent = `${radarRows.filter(row => !row.hidden).length} / ${radarRows.length} 项`;
    };
    search.addEventListener("input", filter); filter();
  }
  const diagramCards = all(".diagram-card");
  let renderQueue = Promise.resolve(), renderGeneration = 0, diagramSerial = 0;
  const fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif';
  function diagramConfig(dark) {
    const surface = dark ? "#172236" : "#f8fafc";
    const text = dark ? "#e2e8f0" : "#0f172a";
    const stroke = dark ? "#94a3b8" : "#64748b";
    return {
      startOnLoad: false, securityLevel: "strict", suppressErrorRendering: true,
      theme: "base", look: "classic", layout: "dagre", fontFamily, fontSize: 16,
      htmlLabels: false, maxTextSize: 100000, maxEdges: 500,
      // User-authored diagrams cannot replace the report's security or theme.
      secure: ["securityLevel", "startOnLoad", "suppressErrorRendering", "maxTextSize", "maxEdges",
        "theme", "themeCSS", "themeVariables", "fontFamily", "fontSize", "htmlLabels", "flowchart", "state", "layout", "look"],
      flowchart: { htmlLabels: false, useMaxWidth: false, curve: "step", padding: 16,
        nodeSpacing: 32, rankSpacing: 42, diagramPadding: 24, wrappingWidth: 180 },
      state: { useMaxWidth: false, padding: 20, nodeSpacing: 36, rankSpacing: 48,
        fontSize: 16, radius: 10, defaultRenderer: "dagre-wrapper" },
      sequence: { useMaxWidth: false, wrap: true, diagramMarginX: 24, diagramMarginY: 24 },
      themeVariables: {
        darkMode: dark, background: surface, fontFamily, fontSize: "16px",
        primaryColor: dark ? "#213654" : "#eff6ff",
        primaryBorderColor: dark ? "#7097c7" : "#93b4dd",
        primaryTextColor: text, secondaryColor: dark ? "#34294c" : "#faf5ff",
        secondaryTextColor: text, secondaryBorderColor: dark ? "#a78bca" : "#c4b5db",
        tertiaryColor: dark ? "#203c36" : "#ecfdf5", tertiaryTextColor: text,
        lineColor: stroke, textColor: text, edgeLabelBackground: surface,
        mainBkg: dark ? "#213654" : "#eff6ff", nodeTextColor: text,
        noteBkgColor: dark ? "#3a3425" : "#fffbeb", noteTextColor: text,
        labelColor: text, labelBoxBkgColor: surface,
      },
      themeCSS: `.node rect, .statediagram-state rect { rx: 10px; ry: 10px; }
        .edgeLabel rect, .edgeLabel .label-container { fill: ${surface} !important; opacity: 1 !important; }
        .edgeLabel text { fill: ${text}; }
        .nodeLabel, .edgeLabel, text { font-family: ${fontFamily}; }`,
    };
  }
  function availableWidth(card) {
    return Math.max(180, card.querySelector(".diagram-scroll").clientWidth - 32);
  }
  function sizeDiagram(svg, scale) {
    const width = Number(svg.dataset.width);
    svg.dataset.scale = String(scale);
    svg.style.width = `${width * scale}px`;
    svg.style.maxWidth = "none";
    svg.style.height = "auto";
  }
  function fitDiagram(card) {
    const svg = card.querySelector(".mermaid-target svg");
    if (svg) sizeDiagram(svg, Math.min(1, availableWidth(card) / Number(svg.dataset.width)));
  }
  function includeRenderedBounds(svg) {
    // Mermaid owns all layout. Expand only its viewport, using measured SVG
    // geometry plus marker/stroke padding so self-loop labels cannot be cropped.
    const bounds = svg.getBBox();
    if (![bounds.x, bounds.y, bounds.width, bounds.height].every(Number.isFinite) || bounds.width <= 0 || bounds.height <= 0) {
      throw new Error("Mermaid 未产生有效图形边界");
    }
    const padding = 24;
    const width = bounds.width + padding * 2, height = bounds.height + padding * 2;
    svg.setAttribute("viewBox", `${bounds.x - padding} ${bounds.y - padding} ${width} ${height}`);
    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
    svg.setAttribute("preserveAspectRatio", "xMidYMin meet");
    svg.dataset.width = String(width);
    svg.dataset.height = String(height);
  }
  async function renderOne(card, source) {
    const target = card.querySelector(".mermaid-target");
    const stage = document.createElement("div");
    stage.className = "mermaid-staging";
    stage.style.width = `${availableWidth(card)}px`;
    document.body.append(stage);
    try {
      const result = await window.mermaid.render(`hubradar-diagram-${++diagramSerial}`, source, stage);
      // Mermaid's strict renderer sanitizes the SVG; the raw Markdown source is
      // never assigned as HTML, and diagram callbacks are intentionally unused.
      target.innerHTML = result.svg;
      const svg = target.querySelector("svg");
      if (!svg) throw new Error("Mermaid 未返回 SVG");
      includeRenderedBounds(svg);
      return svg;
    } finally {
      stage.remove();
    }
  }
  function requestDiagramRender() {
    const generation = ++renderGeneration;
    document.documentElement.dataset.diagramsReady = "false";
    renderQueue = renderQueue.catch(() => {}).then(async () => {
      if (generation !== renderGeneration) return;
      if (document.fonts) await document.fonts.ready;
      const dark = document.documentElement.dataset.theme === "dark";
      if (diagramCards.length && window.mermaid) window.mermaid.initialize(diagramConfig(dark));
      for (const card of diagramCards) {
        if (card.classList.contains("dsh-architecture")) continue;
        if (generation !== renderGeneration) return;
        const target = card.querySelector(".mermaid-target"), status = card.querySelector(".diagram-status");
        target.setAttribute("aria-busy", "true");
        card.dataset.diagramStatus = "pending";
        status.textContent = "正在排版…";
        try {
          if (!window.mermaid) throw new Error("内置 Mermaid 内核未加载");
          const source = card.querySelector(".diagram-source code").textContent;
          let svg = await renderOne(card, source);
          let adapted = false;
          // Presentation-only reflow. Preserve the original source and expose
          // an explicit control to restore its LR/RL direction.
          if (card.querySelector(".diagram-layout").value === "auto"
              && Number(svg.dataset.width) > availableWidth(card) * 1.3
              && /^\s*(?:flowchart|graph)\s+(?:LR|RL)\b/m.test(source)) {
            svg = await renderOne(card, source.replace(/^(\s*(?:flowchart|graph)\s+)(?:LR|RL)\b/m, "$1TB"));
            adapted = true;
          }
          if (generation !== renderGeneration) return;
          card.dataset.diagramStatus = "ready";
          card.dataset.diagramTheme = dark ? "dark" : "light";
          card.dataset.layout = adapted ? "vertical" : "original";
          status.textContent = adapted ? "Mermaid · 纵向适配，原文不变" : "Mermaid · 原始方向";
          fitDiagram(card);
        } catch (error) {
          target.replaceChildren();
          card.dataset.diagramStatus = "error";
          status.textContent = "图形未生成，已保留源码";
          const message = document.createElement("p");
          message.className = "diagram-error";
          message.textContent = `Mermaid：${String(error.message || error).slice(0, 300)}`;
          target.append(message);
          card.querySelector(".diagram-source").open = true;
        } finally {
          target.setAttribute("aria-busy", "false");
        }
      }
      if (generation === renderGeneration) {
        document.documentElement.dataset.diagramsReady = "true";
        document.dispatchEvent(new CustomEvent("hubradar:diagrams-ready"));
      }
    });
    window.hubradarDiagramsReady = renderQueue;
    return renderQueue;
  }
  all("[data-zoom]").forEach(button => button.addEventListener("click", () => {
    const card = button.closest(".diagram-card"), svg = card.querySelector(".mermaid-target svg, .dsh-svg-target svg, svg");
    if (!svg) return;
    if (!svg.dataset.width) {
      const vb = (svg.getAttribute("viewBox") || "").trim().split(/\s+/);
      svg.dataset.width = vb[2] || "1000";
    }
    const delta = Number(button.dataset.zoom);
    if (delta === 0) fitDiagram(card);
    else sizeDiagram(svg, Math.max(.1, Math.min(3, (Number(svg.dataset.scale) || 1) + delta)));
  }));
  all(".diagram-layout").forEach(select => select.addEventListener("change", requestDiagramRender));
  let resizeTimer, previousWidth = window.innerWidth;
  window.addEventListener("resize", () => {
    if (window.innerWidth === previousWidth) return;
    previousWidth = window.innerWidth;
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(requestDiagramRender, 150);
  });
  requestDiagramRender();
  const progress = () => {
    const length = document.documentElement.scrollHeight - window.innerHeight;
    document.querySelector(".reading-progress").style.width = `${length > 0 ? window.scrollY / length * 100 : 0}%`;
  };
  window.addEventListener("scroll", progress, { passive: true }); progress();
})();
