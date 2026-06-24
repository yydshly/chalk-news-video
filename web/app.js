/* Chalk News Video Studio — CP13 app.js */

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
  const exportHint = document.getElementById("export-hint");
  const progressBar = document.getElementById("progress-bar");
  const progressText = document.getElementById("progress-text");
  const jobLog = document.getElementById("job-log");

  // ---------- state ----------
  let lastResult = null;
  let currentEventSource = null;

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

  // ---------- generate (async job) ----------
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

    // Stop any existing event source
    if (currentEventSource) {
      currentEventSource.close();
      currentEventSource = null;
    }

    btnGenerate.disabled = true;
    setStatus("正在创建任务...", "info");
    clearPreview();
    clearJobLog();
    resetProgress();

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
      // Create async job
      const resp = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await resp.json();

      if (!data.ok) {
        setStatus("错误: " + (data.error || "创建任务失败"), "error");
        btnGenerate.disabled = false;
        return;
      }

      const jobId = data.job_id;
      const eventsUrl = data.events_url;

      setStatus("生成中...", "info");
      appendJobLog("[任务已创建] " + data.message);

      // Open SSE connection
      currentEventSource = new EventSource(eventsUrl);

      currentEventSource.addEventListener("progress", function (e) {
        const d = JSON.parse(e.data);
        updateProgress(d.progress, d.message);
        appendJobLog("[" + d.stage + "] " + d.message);
      });

      currentEventSource.addEventListener("done", function (e) {
        const d = JSON.parse(e.data);
        currentEventSource.close();
        currentEventSource = null;

        if (d.result) {
          lastResult = d.result;
          setStatus("生成成功！", "success");
          updateProgress(100, "完成");
          appendJobLog("[完成] 生成成功");
          showPreview(d.result);
          loadArtifacts(d.result);
        } else {
          setStatus("生成结果异常", "error");
          appendJobLog("[错误] 未收到结果");
        }
        btnGenerate.disabled = false;
      });

      currentEventSource.addEventListener("error", function (e) {
        const d = JSON.parse(e.data);
        currentEventSource.close();
        currentEventSource = null;
        setStatus("错误: " + (d.error || "生成失败"), "error");
        appendJobLog("[失败] " + (d.error || "未知错误"));
        btnGenerate.disabled = false;
      });

      currentEventSource.onerror = function () {
        // Only close if not reconnecting
        if (currentEventSource && currentEventSource.readyState === EventSource.CLOSED) {
          currentEventSource.close();
          currentEventSource = null;
        }
      };

    } catch (e) {
      setStatus("请求失败: " + e.message, "error");
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
    if (exportHint) {
      exportHint.textContent = "";
    }
  }

  function clearJobLog() {
    if (jobLog) {
      jobLog.textContent = "";
    }
  }

  function appendJobLog(msg) {
    if (jobLog) {
      const ts = new Date().toLocaleTimeString();
      jobLog.textContent += "[" + ts + "] " + msg + "\n";
      // Auto-scroll to bottom
      jobLog.scrollTop = jobLog.scrollHeight;
    }
  }

  function resetProgress() {
    if (progressBar) {
      progressBar.style.width = "0%";
    }
    if (progressText) {
      progressText.textContent = "";
    }
  }

  function updateProgress(progress, message) {
    if (progressBar) {
      progressBar.style.width = Math.min(100, Math.max(0, progress)) + "%";
    }
    if (progressText) {
      progressText.textContent = message || "";
    }
  }

  function showPreview(result) {
    const ts = "t=" + Date.now();

    // iframe: always show animation.html
    if (result.animation_html) {
      previewHtml.src = result.animation_html + "?" + ts;
    }

    // Clear export hint
    if (exportHint) {
      exportHint.textContent = "";
    }

    // video and download links based on exported flag
    if (result.exported === true && result.output_mp4) {
      // MP4 was exported
      previewVideo.src = result.output_mp4 + "?" + ts;
      downloadLinks.innerHTML = "";
      addDownloadLink(result.animation_html, "📄 animation.html");
      addDownloadLink(result.output_mp4, "🎬 output.mp4");
      if (exportHint) {
        exportHint.textContent = "已导出 MP4";
      }
    } else {
      // No MP4 exported
      previewVideo.src = "about:blank";
      downloadLinks.innerHTML = "";
      if (result.animation_html) {
        addDownloadLink(result.animation_html, "📄 animation.html");
      }
      if (exportHint) {
        exportHint.textContent = "本次未导出 MP4，仅生成 animation.html 预览";
      }
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
