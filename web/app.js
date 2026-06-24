/* Chalk News Video Studio — CP12 app.js */

(function () {
  "use strict";

  // ---------- DOM refs ----------
  const modeRadios = document.querySelectorAll('input[name="mode"]');
  const textInputFields = document.getElementById("text-input-fields");
  const inputTitle = document.getElementById("input-title");
  const inputNews = document.getElementById("input-news");
  const selectTheme = document.getElementById("select-theme");
  const checkDialogue = document.getElementById("check-dialogue");
  const checkExport = document.getElementById("check-export");
  const btnGenerate = document.getElementById("btn-generate");
  const statusMsg = document.getElementById("status-msg");
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const previewHtml = document.getElementById("preview-html");
  const previewVideo = document.getElementById("preview-video");
  const downloadLinks = document.getElementById("download-links");
  const jsonRenderIr = document.getElementById("json-render_ir");
  const jsonSemanticIr = document.getElementById("json-semantic_ir");
  const jsonDialogueScript = document.getElementById("json-dialogue_script");

  // ---------- state ----------
  let lastResult = null;

  // ---------- init ----------
  async function init() {
    setStatus("加载主题列表...", "info");
    try {
      const resp = await fetch("/api/themes");
      if (!resp.ok) throw new Error("Failed to load themes");
      const data = await resp.json();

      // Populate theme select
      selectTheme.innerHTML = "";
      data.themes.forEach(function (theme) {
        const opt = document.createElement("option");
        opt.value = theme;
        opt.textContent = theme;
        selectTheme.appendChild(opt);
      });

      // Set default
      if (data.default_theme) {
        selectTheme.value = data.default_theme;
      }

      setStatus("就绪", "success");
    } catch (e) {
      setStatus("加载主题失败: " + e.message, "error");
    }
  }

  // ---------- mode toggle ----------
  modeRadios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      if (radio.value === "text") {
        textInputFields.classList.remove("hidden");
      } else {
        textInputFields.classList.add("hidden");
      }
    });
  });

  // ---------- tabs ----------
  tabBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const tabId = btn.getAttribute("data-tab");

      tabBtns.forEach(function (b) { b.classList.remove("active"); });
      tabContents.forEach(function (c) { c.classList.remove("active"); });

      btn.classList.add("active");
      const content = document.getElementById("tab-" + tabId);
      if (content) content.classList.add("active");
    });
  });

  // ---------- generate ----------
  btnGenerate.addEventListener("click", async function () {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const theme = selectTheme.value;
    const dialogue = checkDialogue.checked;
    const noExport = !checkExport.checked;
    const title = inputTitle.value.trim();
    const newsText = inputNews.value.trim();

    if (mode === "text" && !newsText) {
      setStatus("请输入新闻正文", "error");
      return;
    }

    btnGenerate.disabled = true;
    setStatus("生成中，请稍候...", "info");
    clearPreview();

    const payload = {
      mode: mode,
      theme: theme,
      dialogue: dialogue,
      mock: true,
      no_export: noExport,
    };

    if (mode === "text") {
      payload.title = title;
      payload.news_text = newsText;
    }

    try {
      const resp = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await resp.json();

      if (!result.ok) {
        setStatus("错误: " + (result.error || "生成失败"), "error");
        btnGenerate.disabled = false;
        return;
      }

      lastResult = result;
      setStatus("生成成功！", "success");
      showPreview(result);
      await loadArtifacts(result);
    } catch (e) {
      setStatus("请求失败: " + e.message, "error");
    } finally {
      btnGenerate.disabled = false;
    }
  });

  // ---------- helpers ----------
  function setStatus(msg, type) {
    statusMsg.textContent = msg;
    statusMsg.className = "status-msg " + (type || "");
  }

  function clearPreview() {
    const ts = Date.now();
    previewHtml.src = "about:blank";
    previewVideo.src = "about:blank";
    downloadLinks.innerHTML = "";
    jsonRenderIr.textContent = "";
    jsonSemanticIr.textContent = "";
    jsonDialogueScript.textContent = "";
  }

  function showPreview(result) {
    const ts = "t=" + Date.now();

    // iframe
    previewHtml.src = result.animation_html + "?" + ts;

    // video (only if exported)
    if (!result.output_mp4.includes("no_export")) {
      previewVideo.src = result.output_mp4 + "?" + ts;
    }

    // download links
    downloadLinks.innerHTML = "";
    addDownloadLink(result.animation_html, "📄 animation.html");
    if (result.output_mp4) {
      addDownloadLink(result.output_mp4, "🎬 output.mp4");
    }

    // Switch to preview tab
    tabBtns.forEach(function (b) { b.classList.remove("active"); });
    tabContents.forEach(function (c) { c.classList.remove("active"); });
    document.querySelector('[data-tab="preview"]').classList.add("active");
    document.getElementById("tab-preview").classList.add("active");
  }

  function addDownloadLink(href, label) {
    const a = document.createElement("a");
    a.href = href + "?t=" + Date.now();
    a.className = "download-link";
    a.textContent = label;
    a.download = "";
    downloadLinks.appendChild(a);
  }

  async function loadArtifacts(result) {
    const artifacts = [
      { url: result.render_ir, el: jsonRenderIr, name: "render_ir" },
      { url: result.semantic_ir, el: jsonSemanticIr, name: "semantic_ir" },
    ];

    if (result.dialogue_script) {
      artifacts.push({ url: result.dialogue_script, el: jsonDialogueScript, name: "dialogue_script" });
    }

    await Promise.all(artifacts.map(function (art) {
      return fetch(art.url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
          art.el.textContent = JSON.stringify(data, null, 2);
        })
        .catch(function () {
          art.el.textContent = "(未生成)";
        });
    }));
  }

  // ---------- start ----------
  init();
})();
