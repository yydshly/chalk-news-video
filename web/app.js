/* Chalk News Video Studio — CP15.6 app.js */

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
  const btnRefreshHistory = document.getElementById("btn-refresh-history");
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
  const historyList = document.getElementById("history-list");
  const selectLlmProvider = document.getElementById("select-llm-provider");
  const selectTtsProvider = document.getElementById("select-tts-provider");
  const llmProviderStatus = document.getElementById("llm-provider-status");
  const ttsProviderStatus = document.getElementById("tts-provider-status");
  const checkRepair = document.getElementById("check-repair");
  const recommendedHint = document.getElementById("recommended-hint");
  const recommendedConfigText = document.getElementById("recommended-config-text");
  const ttsUpgradeHint = document.getElementById("tts-upgrade-hint");
  const autoPreviewBanner = document.getElementById("auto-preview-banner");
  const audioPlayerWrap = document.getElementById("audio-player-wrap");
  const previewAudio = document.getElementById("preview-audio");
  const btnPlayAudio = document.getElementById("btn-play-audio");

  // ---------- state ----------
  let lastResult = null;
  let currentEventSource = null;
  let llmProviders = [];
  let ttsProviders = [];
  let latestSucceededJob = null;

  // ---------- init ----------
  async function init() {
    setStatus("加载主题列表...", "info");

    // Load providers (CP15)
    await loadProviders();

    try {
      const resp = await fetch("/api/themes");
      if (!resp.ok) throw new Error("Failed to load themes");
      const data = await resp.json();

      selectTheme.innerHTML = "";
      data.themes.forEach(function (theme) {
        const opt = document.createElement("option");
        opt.value = theme;
        opt.textContent = theme;
        selectTheme.appendChild(opt);
      });

      if (data.default_theme) {
        selectTheme.value = data.default_theme;
      }

      setStatus("就绪", "success");
    } catch (e) {
      setStatus("加载主题失败: " + e.message, "error");
    }

    // Load history on startup and auto-preview latest succeeded
    await loadHistoryAndAutoPreview();
  }

  // ---------- load providers (CP15) ----------
  async function loadProviders() {
    try {
      const resp = await fetch("/api/providers");
      if (!resp.ok) throw new Error("Failed to load providers");
      const data = await resp.json();

      llmProviders = data.llm || [];
      ttsProviders = data.tts || [];

      // Populate LLM provider select
      selectLlmProvider.innerHTML = "";
      llmProviders.forEach(function (p) {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.name;
        selectLlmProvider.appendChild(opt);
      });

      // Populate TTS provider select
      selectTtsProvider.innerHTML = "";
      ttsProviders.forEach(function (p) {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.name;
        selectTtsProvider.appendChild(opt);
      });

      // Set defaults
      selectLlmProvider.value = "mock";
      selectTtsProvider.value = "mock_dialogue";
      updateProviderStatus();
      updateRecommendedHint();

    } catch (e) {
      console.error("Failed to load providers:", e);
    }
  }

  function updateProviderStatus() {
    const llmId = selectLlmProvider.value;
    const ttsId = selectTtsProvider.value;

    const llm = llmProviders.find(function (p) { return p.id === llmId; });
    const tts = ttsProviders.find(function (p) { return p.id === ttsId; });

    if (llm) {
      if (llm.ready) {
        llmProviderStatus.textContent = "✓ Ready";
        llmProviderStatus.className = "provider-status status-ready";
      } else {
        const missing = (llm.missing_env || []).join(", ");
        llmProviderStatus.textContent = "⚠ Missing: " + missing;
        llmProviderStatus.className = "provider-status status-warning";
      }
    }

    if (tts) {
      if (tts.ready) {
        ttsProviderStatus.textContent = "✓ Ready";
        ttsProviderStatus.className = "provider-status status-ready";
      } else {
        const missing = (tts.missing_env || []).join(", ");
        ttsProviderStatus.textContent = "⚠ Missing: " + missing;
        ttsProviderStatus.className = "provider-status status-warning";
      }
    }
  }

  function updateRecommendedHint() {
    // Update recommended config text based on current selection
    const llmId = selectLlmProvider.value;
    const ttsId = selectTtsProvider.value;
    const llm = llmProviders.find(function (p) { return p.id === llmId; });
    const tts = ttsProviders.find(function (p) { return p.id === ttsId; });

    let cfgText = "";
    if (llmId === "mock") {
      cfgText = "示例新闻 + mock LLM + mock_dialogue（本地无需 API key）";
    } else if (llm && llm.name) {
      cfgText = "热门 AI 新闻 + research_desk + " + llm.name + " + mock_dialogue + 不导出 MP4";
    } else {
      cfgText = "热门 AI 新闻 + research_desk + " + llmId + " + mock_dialogue + 不导出 MP4";
    }
    recommendedConfigText.textContent = cfgText;

    // Show upgrade hint if minimax_dialogue ready
    const minimaxReady = ttsProviders.some(function (p) {
      return p.id === "minimax_dialogue" && p.ready;
    });
    ttsUpgradeHint.style.display = minimaxReady ? "block" : "none";
  }

  // Provider select change handlers
  if (selectLlmProvider) {
    selectLlmProvider.addEventListener("change", function () {
      updateProviderStatus();
      updateRecommendedHint();
    });
  }
  if (selectTtsProvider) {
    selectTtsProvider.addEventListener("change", function () {
      updateProviderStatus();
      updateRecommendedHint();
    });
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

      if (tabId === "history") {
        loadHistory();
      }
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
      mock: selectLlmProvider.value === "mock",
      no_export: noExport,
      llm_provider: selectLlmProvider.value,
      tts_provider: selectTtsProvider.value,
      repair: checkRepair.checked,
      repair_attempts: 2,
    };

    if (mode === "text") {
      payload.title = title;
      payload.news_text = newsText;
    }

    try {
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
      appendJobLog("[任务已创建] " + data.job_id);

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
          // CP15.6: Auto-jump to preview tab and show result
          showPreview(d.result, true);
          loadArtifacts(d.result);
          // Refresh history and auto-preview after job completes
          loadHistoryAndAutoPreview(d.result);
        } else {
          setStatus("生成结果异常", "error");
          appendJobLog("[错误] 未收到结果");
        }
        btnGenerate.disabled = false;
      });

      currentEventSource.addEventListener("error", function (e) {
        let errorMsg = "生成失败";
        try {
          const d = JSON.parse(e.data);
          errorMsg = d.error || "生成失败";
        } catch (err) {}
        currentEventSource.close();
        currentEventSource = null;
        setStatus("错误: " + errorMsg, "error");
        appendJobLog("[失败] " + errorMsg);
        loadHistory();
        btnGenerate.disabled = false;
      });

      currentEventSource.onerror = function () {
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

  // ---------- history with auto-preview (CP15.6) ----------
  btnRefreshHistory.addEventListener("click", function () {
    loadHistory();
  });

  async function loadHistoryAndAutoPreview(resultFromJob) {
    await loadHistory();
    if (resultFromJob) {
      // Auto-preview the job that just succeeded
      showPreview(resultFromJob, true);
    } else if (latestSucceededJob) {
      // Auto-preview the latest succeeded job on page load
      showPreviewForJob(latestSucceededJob);
    }
  }

  async function loadHistory() {
    if (!historyList) return;
    historyList.innerHTML = '<div class="history-loading">加载中...</div>';

    try {
      const resp = await fetch("/api/history");
      const data = await resp.json();

      if (!data.ok) {
        historyList.innerHTML = '<div class="history-empty">加载失败</div>';
        return;
      }

      const items = data.items || [];

      if (items.length === 0) {
        historyList.innerHTML = '<div class="history-empty">暂无历史作品</div>';
        return;
      }

      historyList.innerHTML = "";

      // CP15.6: Track latest succeeded job for auto-preview
      latestSucceededJob = null;

      items.forEach(function (job) {
        if (job.status === "succeeded" && !latestSucceededJob) {
          latestSucceededJob = job;
        }
        const item = createHistoryItem(job);
        historyList.appendChild(item);
      });
    } catch (e) {
      historyList.innerHTML = '<div class="history-empty">加载失败: ' + e.message + '</div>';
    }
  }

  function createHistoryItem(job) {
    const div = document.createElement("div");
    div.className = "history-item";
    if (job.status === "succeeded") {
      div.classList.add("history-item-succeeded");
    } else if (job.status === "failed") {
      div.classList.add("history-item-failed");
    }

    const statusClass = job.status === "succeeded" ? "status-success" :
                        job.status === "failed" ? "status-error" : "status-pending";

    const exportedLabel = job.exported ? "已导出" : "未导出";
    const dialogueLabel = job.dialogue ? "对话" : "单人";
    const llmLabel = job.llm_provider || "mock";
    const ttsLabel = job.tts_provider || "mock";

    const dateStr = job.created_at ? job.created_at.replace("T", " ").slice(0, 19) : "";

    // Build action buttons for succeeded jobs
    let linksHtml = "";
    if (job.status === "succeeded") {
      if (job.animation_html) {
        linksHtml += '<button class="btn-history-action" data-action="preview" data-job="' + job.job_id + '">🎬 预览动画</button> ';
      }
      if (job.output_mp4) {
        linksHtml += '<button class="btn-history-action" data-action="video" data-job="' + job.job_id + '">▶ 预览 MP4</button> ';
      }
      if (job.dialogue_audio) {
        linksHtml += '<button class="btn-history-action" data-action="audio" data-job="' + job.job_id + '">🔊 播放音频</button> ';
      }
      linksHtml += '<button class="btn-history-action" data-action="artifacts" data-job="' + job.job_id + '">📋 查看脚本</button>';
    }

    // Title from job (CP15.6)
    const jobTitle = job.title || job.summary || "";

    div.innerHTML =
      '<div class="history-item-header">' +
        '<span class="history-job-id">' + job.job_id + '</span>' +
        '<span class="history-badge ' + statusClass + '">' + job.status + '</span>' +
      '</div>' +
      (jobTitle ? '<div class="history-item-title">' + escapeHtml(jobTitle.slice(0, 80)) + '</div>' : '') +
      '<div class="history-item-meta">' +
        '<span>' + (job.theme ? '主题: ' + job.theme : '') + '</span> ' +
        '<span>' + dialogueLabel + '</span> ' +
        '<span>LLM: ' + llmLabel + '</span> ' +
        '<span>TTS: ' + ttsLabel + '</span>' +
        (job.duration ? '<span class="history-item-duration">' + job.duration.toFixed(1) + 's</span>' : '') +
        '<span>' + exportedLabel + '</span>' +
      '</div>' +
      '<div class="history-item-time">' + dateStr + '</div>' +
      (job.error ? '<div class="history-item-error-collapsed" data-job="' + job.job_id + '">' + escapeHtml(job.error.slice(0, 80)) + '</div>' : '') +
      '<div class="history-item-actions">' + linksHtml + '</div>';

    // Attach event listeners
    div.querySelectorAll(".btn-history-action").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const action = btn.getAttribute("data-action");
        const jobId = btn.getAttribute("data-job");
        handleHistoryAction(action, jobId, job);
      });
    });

    // CP15.6: Collapsible failed job error
    const errorCollapsed = div.querySelector(".history-item-error-collapsed");
    if (errorCollapsed && job.status === "failed") {
      errorCollapsed.style.cursor = "pointer";
      errorCollapsed.addEventListener("click", function () {
        const existing = div.querySelector(".history-item-error-expanded");
        if (existing) {
          existing.remove();
          errorCollapsed.style.display = "block";
        } else {
          errorCollapsed.style.display = "none";
          const expanded = document.createElement("div");
          expanded.className = "history-item-error-expanded";
          expanded.textContent = job.error || "(无错误信息)";
          div.insertBefore(expanded, div.querySelector(".history-item-actions"));
        }
      });
    }

    return div;
  }

  function handleHistoryAction(action, jobId, job) {
    if (action === "preview") {
      showPreviewForJob(job);

    } else if (action === "video") {
      if (job.output_mp4) {
        previewVideo.src = job.output_mp4 + "?t=" + Date.now();
        previewHtml.src = job.animation_html ? job.animation_html + "?t=" + Date.now() : "about:blank";
        downloadLinks.innerHTML = "";
        if (job.animation_html) {
          addDownloadLink(job.animation_html, "📄 animation.html");
        }
        addDownloadLink(job.output_mp4, "🎬 output.mp4");
        setExportHint(true);
        switchToPreviewTab();
      }

    } else if (action === "audio") {
      if (job.dialogue_audio) {
        previewAudio.src = job.dialogue_audio + "?t=" + Date.now();
        audioPlayerWrap.style.display = "block";
        previewAudio.style.display = "block";
        btnPlayAudio.style.display = "none";
        switchToPreviewTab();
      }

    } else if (action === "artifacts") {
      loadJobArtifacts(job);
      switchToPreviewTab();
      // Switch to semantic_ir tab to show scripts
      tabBtns.forEach(function (b) { b.classList.remove("active"); });
      tabContents.forEach(function (c) { c.classList.remove("active"); });
      document.querySelector('[data-tab="semantic_ir"]').classList.add("active");
      document.getElementById("tab-semantic_ir").classList.add("active");
      // Actually show render_ir which has title/summary
      tabBtns.forEach(function (b) { b.classList.remove("active"); });
      tabContents.forEach(function (c) { c.classList.remove("active"); });
      document.querySelector('[data-tab="render_ir"]').classList.add("active");
      document.getElementById("tab-render_ir").classList.add("active");
    }
  }

  function showPreviewForJob(job) {
    autoPreviewBanner.style.display = "none";
    const ts = "?t=" + Date.now();

    if (job.animation_html) {
      previewHtml.src = job.animation_html + ts;
    }

    if (job.output_mp4) {
      previewVideo.src = job.output_mp4 + ts;
    } else {
      previewVideo.src = "about:blank";
    }

    // Audio
    if (job.dialogue_audio) {
      previewAudio.src = job.dialogue_audio + ts;
      audioPlayerWrap.style.display = "block";
      previewAudio.style.display = "block";
      btnPlayAudio.style.display = "none";
    } else {
      audioPlayerWrap.style.display = "none";
    }

    // Download links
    downloadLinks.innerHTML = "";
    if (job.animation_html) {
      addDownloadLink(job.animation_html, "📄 animation.html");
    }
    if (job.output_mp4) {
      addDownloadLink(job.output_mp4, "🎬 output.mp4");
    }
    if (job.dialogue_audio) {
      addDownloadLink(job.dialogue_audio, "🔊 dialogue.wav");
    }

    setExportHint(job.exported);
    switchToPreviewTab();
  }

  async function loadJobArtifacts(job) {
    const jobId = job.job_id;
    const artifacts = [
      { name: "render_ir", el: jsonRenderIr },
      { name: "semantic_ir", el: jsonSemanticIr },
      { name: "dialogue_script", el: jsonDialogueScript },
    ];

    for (const art of artifacts) {
      try {
        const resp = await fetch("/api/jobs/" + jobId + "/artifacts/" + art.name);
        if (resp.ok) {
          const data = await resp.json();
          art.el.textContent = JSON.stringify(data, null, 2);
        } else {
          art.el.textContent = "(未生成)";
        }
      } catch (e) {
        art.el.textContent = "(加载失败)";
      }
    }
  }

  // Audio play button
  if (btnPlayAudio) {
    btnPlayAudio.addEventListener("click", function () {
      if (previewAudio.src) {
        previewAudio.play().catch(function () {});
        btnPlayAudio.style.display = "none";
      }
    });
  }

  // ---------- helpers ----------
  function switchToPreviewTab() {
    tabBtns.forEach(function (b) { b.classList.remove("active"); });
    tabContents.forEach(function (c) { c.classList.remove("active"); });
    document.querySelector('[data-tab="preview"]').classList.add("active");
    document.getElementById("tab-preview").classList.add("active");
  }

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
    setExportHint(null);
    audioPlayerWrap.style.display = "none";
    autoPreviewBanner.style.display = "none";
  }

  function clearJobLog() {
    if (jobLog) {
      jobLog.textContent = "";
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

  function appendJobLog(msg) {
    if (jobLog) {
      const ts = new Date().toLocaleTimeString();
      jobLog.textContent += "[" + ts + "] " + msg + "\n";
      jobLog.scrollTop = jobLog.scrollHeight;
    }
  }

  function showPreview(result, autoPreview) {
    const ts = "?t=" + Date.now();

    if (autoPreview) {
      autoPreviewBanner.style.display = "block";
      autoPreviewBanner.textContent = "最近成功作品";
    }

    if (result.animation_html) {
      previewHtml.src = result.animation_html + ts;
    }

    if (result.exported === true && result.output_mp4) {
      previewVideo.src = result.output_mp4 + ts;
      downloadLinks.innerHTML = "";
      addDownloadLink(result.animation_html, "📄 animation.html");
      addDownloadLink(result.output_mp4, "🎬 output.mp4");
      setExportHint(true);
    } else {
      previewVideo.src = "about:blank";
      downloadLinks.innerHTML = "";
      if (result.animation_html) {
        addDownloadLink(result.animation_html, "📄 animation.html");
      }
      setExportHint(false);
    }

    // Audio
    if (result.dialogue_audio) {
      previewAudio.src = result.dialogue_audio + ts;
      audioPlayerWrap.style.display = "block";
      previewAudio.style.display = "block";
      btnPlayAudio.style.display = "none";
      addDownloadLink(result.dialogue_audio, "🔊 dialogue.wav");
    } else {
      audioPlayerWrap.style.display = "none";
    }

    switchToPreviewTab();
  }

  function setExportHint(exported) {
    if (!exportHint) return;
    if (exported === true) {
      exportHint.textContent = "已导出 MP4";
    } else if (exported === false) {
      exportHint.textContent = "本次未导出 MP4，仅生成 animation.html 预览";
    } else {
      exportHint.textContent = "";
    }
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
      if (!art.url) {
        art.el.textContent = "(未生成)";
        return Promise.resolve();
      }
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

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // ---------- start ----------
  init();
})();
