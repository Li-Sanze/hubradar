/* Injected by browser_smoke.py after the two product scripts. */
(async () => {
  const checks = {}, metrics = {};
  const all = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const check = (name, condition) => { checks[name] = Boolean(condition); };
  const rect = element => element.getBoundingClientRect();
  const overlaps = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 2
    && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 2;
  const inBounds = (inner, outer) => inner.left >= outer.left - 1 && inner.top >= outer.top - 1
    && inner.right <= outer.right + 1 && inner.bottom <= outer.bottom + 1;
  try {
    await window.hubradarDiagramsReady;
    const cards = all(".diagram-card"), options = window.hubradarTestOptions;
    const mermaidCards = cards.filter(card => card.querySelector(".mermaid-target"));
    const dshCards = cards.filter(card => card.querySelector(".dsh-svg-target"));
    check("mermaid_loaded_when_needed", mermaidCards.length
      ? typeof window.mermaid?.render === "function" : typeof window.mermaid === "undefined");
    if (options.kind === "readme") {
      check("readme_has_no_diagram_runtime", cards.length === 0);
      const workflow = all("article table").find(table => table.textContent.includes("Agent 提炼"));
      check("four_workflow_stages", workflow?.tBodies[0].rows.length === 4);
      check("workflow_fits_desktop", innerWidth < 640 || workflow.scrollWidth <= workflow.parentElement.clientWidth + 1);
    }
    if (options.kind === "invalid") {
      check("syntax_failure_visible", cards.some(card => card.dataset.diagramStatus === "error"
        && card.querySelector(".diagram-source").open && card.querySelector(".diagram-error").textContent.length));
    } else {
      check("all_diagrams_ready", cards.every(card => card.dataset.diagramStatus === "ready"));
    }
    if (options.kind === "hono") check("dsh_and_three_mermaid_diagrams", dshCards.length === 1 && mermaidCards.length === 3);
    if (options.kind === "hubradar") check("dsh_and_mermaid_diagrams", dshCards.length === 1 && mermaidCards.length === 1);
    for (const card of dshCards) {
      check("dsh_source_anchors", all("a.card-anchor", card).length === 8);
      check("dsh_full_card_titles", all("g[data-card-id]", card).every(group => {
        const title = group.querySelector(":scope > title")?.textContent || "";
        const labels = [".card-title", ".card-desc", ".code-pill"]
          .map(selector => group.querySelector(selector)).filter(Boolean);
        return title.length > 0 && group.firstElementChild.localName === "title"
          && labels.every(text => title.includes(text.textContent.replace(/…$/, "")));
      }));
      if (options.kind === "hubradar") check("digraph_token_complete",
        card.querySelector('[data-card-id="prepare"] .code-pill').textContent.includes("DiGraph()"));
      check("dsh_text_inside_cards", all("g[data-card-id]", card).every(group =>
        all("text", group).every(text => inBounds(rect(text), rect(group.querySelector(".card-rect"))))));
    }
    if (options.kind === "extended") check("extended_diagrams", cards.length === 3 && cards.every(card => card.querySelector("svg")));
    const measure = theme => {
      const values = cards.filter(card => card.dataset.diagramStatus === "ready").map(card => {
        const svg = card.querySelector(".mermaid-target svg, .dsh-svg-target svg");
        if (!svg) return null;
        const bounds = rect(svg), scroll = card.querySelector(".diagram-scroll");
        const labels = all("text, foreignObject", svg).filter(el => rect(el).width > 0 && rect(el).height > 0);
        const shapes = all("g.node", svg).map(rect);
        const edgeLabels = all("g.edgeLabel", svg).filter(el => all("text", el).some(text => rect(text).width > 0));
        const edgeLabelRects = edgeLabels.flatMap(label => all("text", label)).map(rect);
        const allMarks = all("path, rect, circle, ellipse, polygon, polyline, line", svg)
          .filter(el => !el.closest("defs") && rect(el).width + rect(el).height > 0);
        const clippedLabels = labels.filter(el => !inBounds(rect(el), bounds));
        const collisions = edgeLabelRects.filter(label => shapes.some(node => overlaps(label, node)));
        check(`${theme}_label_bounds_${valuesIndex++}`, clippedLabels.length === 0);
        check(`${theme}_shape_bounds_${shapesIndex++}`, allMarks.every(el => inBounds(rect(el), bounds)));
        check(`${theme}_node_label_separation_${collisionIndex++}`, collisions.length === 0);
        check(`${theme}_edge_label_background_${backgroundIndex++}`, edgeLabels.every(label =>
          all("rect", label).some(background => {
            const style = getComputedStyle(background), bounds = rect(background);
            return bounds.width > 0 && bounds.height > 0 && style.fill !== "none"
              && style.fill !== "rgba(0, 0, 0, 0)" && Number(style.opacity) >= .95
              && all("text", label).every(text => inBounds(rect(text), bounds));
          })));
        check(`${theme}_fits_container_${fitIndex++}`, bounds.width <= scroll.clientWidth - 28 + 1);
        return { naturalWidth: Number(svg.dataset.width), naturalHeight: Number(svg.dataset.height),
          displayWidth: bounds.width, displayHeight: bounds.height, layout: card.dataset.layout,
          texts: labels.length, clippedLabels: clippedLabels.length, labelNodeCollisions: collisions.length,
          edgeBackgrounds: edgeLabels.map(label => all("rect", label).map(bg => ({
            fill: getComputedStyle(bg).fill, opacity: getComputedStyle(bg).opacity,
            width: rect(bg).width, height: rect(bg).height,
          }))) };
      });
      metrics[theme] = values;
    };
    let valuesIndex = 0, shapesIndex = 0, collisionIndex = 0, backgroundIndex = 0, fitIndex = 0;
    if (options.kind !== "invalid") measure("light");
    const fill = () => document.querySelector(".mermaid-target svg .node rect")
      ? getComputedStyle(document.querySelector(".mermaid-target svg .node rect")).fill : null;
    const originalFill = fill();
    document.getElementById("theme").click();
    await window.hubradarDiagramsReady;
    check("theme_dark", document.documentElement.dataset.theme === "dark");
    if (originalFill) check("svg_theme_changed", fill() !== originalFill);
    if (options.kind !== "invalid") measure("dark");
    document.getElementById("theme").click();
    await window.hubradarDiagramsReady;
    check("theme_light", document.documentElement.dataset.theme === "light");
    if (options.kind === "hono") {
      const flow = mermaidCards[0];
      const compact = element => element.textContent.replace(/\s/g, "");
      check("state_self_loop_labels_complete",
        compact(mermaidCards[1].querySelector("svg")).includes("add()→抛错")
        && compact(mermaidCards[2].querySelector("svg")).includes("header()→克隆Response再改"));
      check("flow_not_overwide", Number(flow.querySelector("svg").dataset.width) < 1200);
      const originalSource = flow.querySelector(".diagram-source code").textContent;
      const select = flow.querySelector(".diagram-layout");
      select.value = "original"; select.dispatchEvent(new Event("change"));
      await window.hubradarDiagramsReady;
      check("original_direction_available", flow.dataset.layout === "original");
      select.value = "auto"; select.dispatchEvent(new Event("change"));
      await window.hubradarDiagramsReady;
      check("source_unchanged", flow.querySelector(".diagram-source code").textContent === originalSource);
    }
    const svg = document.querySelector(".mermaid-target svg, .dsh-svg-target svg");
    if (svg) {
      const card = svg.closest(".diagram-card");
      const oldWidth = rect(svg).width;
      card.querySelector('[data-zoom="0.2"]').click();
      check("zoom", rect(svg).width > oldWidth);
      card.querySelector('[data-zoom="0"]').click();
      check("fit", rect(svg).width <= svg.closest(".diagram-scroll").clientWidth);
    }
    const details = all("article details");
    if (details.length && options.kind !== "invalid") {
      document.getElementById("expand").click();
      check("expand", details.every(detail => detail.open));
      document.getElementById("expand").click();
      check("collapse", details.every(detail => !detail.open));
    }
    const radar = document.querySelector(".radar-table");
    if (radar) {
      const search = document.getElementById("table-search"), rows = all("tbody tr", radar);
      search.value = "repomix"; search.dispatchEvent(new Event("input"));
      check("radar_filter", rows.some(row => !row.hidden) && rows.some(row => row.hidden));
      search.value = ""; search.dispatchEvent(new Event("input"));
      radar.tHead.rows[0].cells[2].querySelector("button").click();
      const counts = all("tbody tr", radar).map(row => Number(row.cells[2].textContent.replace(/,/g, "")));
      check("numeric_sort", counts.every((count, index) => !index || counts[index - 1] <= count));
    }
    check("toc_targets", all(".toc-grid a").every(link => document.getElementById(link.hash.slice(1))));
    check("no_page_overflow", document.documentElement.scrollWidth <= innerWidth);
    check("no_script_errors", window.hubradarTestErrors.length === 0);
    const externalResources = performance.getEntriesByType("resource").filter(entry => /^https?:/i.test(entry.name));
    check("zero_network_calls", window.hubradarTestNetwork.length === 0 && externalResources.length === 0);
    check("no_csp_violations", window.hubradarTestCSP.length === 0);
    metrics.networkCalls = window.hubradarTestNetwork;
    metrics.externalResources = externalResources.map(entry => entry.name);
    metrics.csp = window.hubradarTestCSP;
    if (options.theme === "dark") {
      document.getElementById("theme").click();
      await window.hubradarDiagramsReady;
    }
    document.documentElement.style.scrollBehavior = "auto";
    const focus = options.capture === "workflow" ? all("h3").find(heading => heading.textContent === "四阶段工作流")
      : options.capture === "states" ? document.getElementById("section-3")
      : options.capture === "flow" ? document.getElementById("section-2") : null;
    if (focus) window.scrollTo({ top: focus.getBoundingClientRect().top + window.scrollY - 12, behavior: "instant" });
    await new Promise(resolve => setTimeout(resolve, 200));
  } catch (error) {
    checks.browser_check_completed = false;
    window.hubradarTestErrors.push(String(error.stack || error));
  }
  const output = document.createElement("output");
  output.id = "hubradar-browser-result"; output.hidden = true;
  output.textContent = JSON.stringify({ viewport: innerWidth, checks, metrics, errors: window.hubradarTestErrors });
  document.body.append(output);
})();
