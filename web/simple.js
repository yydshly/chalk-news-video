(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var newsEl = $("news");
  var stylesEl = $("styles");
  var statusEl = $("status");
  var resultEl = $("result");
  var previewEl = $("preview");
  var videoEl = $("video");
  var resultActions = $("result-actions");
  var optTts = $("opt-tts");

  var selectedStyle = null;
  var pollTimer = null;

  // ratio → export dimensions + preview iframe size
  var RATIOS = {
    portrait:  { w: 720,  h: 1280, pw: 360, ph: 640 },
    square:    { w: 1080, h: 1080, pw: 460, ph: 460 },
    landscape: { w: 1280, h: 720,  pw: 600, ph: 338 },
  };
  var selectedRatio = "landscape";  // CP60: 16:9 landscape is the default

  function applyPreviewSize() {
    var r = RATIOS[selectedRatio];
    previewEl.style.width = r.pw + "px";
    previewEl.style.height = r.ph + "px";
    videoEl.style.width = r.pw + "px";
  }

  Array.prototype.forEach.call(document.querySelectorAll(".ratio-btn"), function (btn) {
    btn.addEventListener("click", function () {
      selectedRatio = btn.getAttribute("data-ratio");
      Array.prototype.forEach.call(document.querySelectorAll(".ratio-btn"), function (b) {
        b.classList.toggle("selected", b === btn);
      });
      applyPreviewSize();
      var note = document.getElementById("ratio-note");
      if (note) {
        note.textContent = (selectedStyle === "breaking_news_v1" && selectedRatio !== "portrait")
          ? "提示：快讯大屏风专为 9:16 设计，非竖屏会有留白。" : "";
      }
    });
  });

  var STYLE_DESC = {
    breaking_news_v1: "深红突发快讯，大屏标题 + 卡通主播",
    timeline_daily_v1: "浅色日报，竖向时间线，头条高亮",
    data_dashboard_v1: "深色仪表盘，统计磁贴 + 条形图",
    podcast_cards_v1: "紫色播客，双人席 + 波形 + 待讨论",
    research_briefing_v1: "学术简报，摘要 + 编号要点",
  };

  function setStatus(msg, kind) {
    statusEl.textContent = msg || "";
    statusEl.className = "status" + (kind ? " " + kind : "");
  }

  // ---- load styles from capabilities ----
  function loadStyles() {
    fetch("/api/episode/export/capabilities")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var supported = (d && d.supported_styles) || [];
        stylesEl.innerHTML = "";
        supported.forEach(function (s, i) {
          var card = document.createElement("div");
          card.className = "style-card";
          card.setAttribute("data-style", s.id);
          card.innerHTML =
            '<span class="sc-check">✓</span>' +
            '<div class="sc-name">' + (s.name || s.id) + "</div>" +
            '<div class="sc-desc">' + (STYLE_DESC[s.id] || "") + "</div>";
          card.addEventListener("click", function () { selectStyle(s.id); });
          stylesEl.appendChild(card);
        });
        var def = (d && d.default_style_id) || (supported[0] && supported[0].id);
        if (def) selectStyle(def);
      })
      .catch(function () {
        stylesEl.innerHTML = '<span class="muted">风格加载失败，请刷新</span>';
      });
  }

  function selectStyle(id) {
    selectedStyle = id;
    Array.prototype.forEach.call(stylesEl.querySelectorAll(".style-card"), function (c) {
      c.classList.toggle("selected", c.getAttribute("data-style") === id);
    });
  }

  // ---- fill from hot news ----
  $("btn-hot").addEventListener("click", function () {
    var hs = $("hot-status");
    hs.textContent = "正在获取今日热点…";
    fetch("/api/hot-ai-news")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var items = (d && d.items) || [];
        if (!items.length) { hs.textContent = "暂无热点"; return; }
        var top = items[0];
        var body = top.summary && top.summary.length > 10 ? top.summary : top.title;
        newsEl.value = top.title + "\n" + body;
        hs.textContent = d.fallback ? "已填充示例新闻（实时源不可用）" : "已填充热点：" + top.title;
      })
      .catch(function () { hs.textContent = "获取失败"; });
  });

  // ---- build contract from pasted news ----
  function buildContract() {
    var text = (newsEl.value || "").trim();
    if (!text) return Promise.reject(new Error("请先粘贴新闻内容"));
    var title = text.split("\n")[0].slice(0, 80);
    return fetch("/api/episode/source-contract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_type: "inline_text", text: text, episode_title: title }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok || !d.contract) throw new Error(d.error || "生成契约失败");
      return d.contract;
    });
  }

  function ensureStyle() {
    if (!selectedStyle) throw new Error("请先选择一种风格");
    return selectedStyle;
  }

  function showResult() {
    resultEl.style.display = "block";
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ---- fast preview (styled HTML) ----
  $("btn-preview").addEventListener("click", function () {
    setStatus("正在生成预览…", "work");
    Promise.resolve().then(ensureStyle).then(buildContract).then(function (contract) {
      return fetch("/api/episode/preview-html", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract: contract, style_id: selectedStyle, persist: false }),
      }).then(function (r) { return r.json(); });
    }).then(function (d) {
      if (!d.ok) throw new Error(d.error || "预览失败");
      videoEl.style.display = "none";
      previewEl.style.display = "block";
      previewEl.src = d.path + "?t=" + Date.now();
      resultActions.innerHTML = "";
      showResult();
      setStatus("预览已生成（即为导出效果）", "ok");
    }).catch(function (e) { setStatus(e.message, "err"); });
  });

  // ---- generate MP4 ----
  $("btn-generate").addEventListener("click", function () {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    setStatus("① 准备内容…", "work");
    var theContract = null;
    Promise.resolve().then(ensureStyle).then(buildContract).then(function (contract) {
      theContract = contract;
      // optional TTS narration
      if (!optTts.checked) return null;
      setStatus("② 生成真人口播旁白…", "work");
      return fetch("/api/episode/tts-audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract: contract }),
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (!d.ok && d.status !== "completed") return null; // narration optional; continue silent on failure
        return d.audio_url || null;
      }).catch(function () { return null; });
    }).then(function (audioUrl) {
      setStatus("③ 渲染并导出 MP4（约 20–40 秒）…", "work");
      var dim = RATIOS[selectedRatio];
      return fetch("/api/episode/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract: theContract, style_id: selectedStyle, width: dim.w, height: dim.h, fps: 30, audio_url: audioUrl }),
      }).then(function (r) { return r.json(); });
    }).then(function (d) {
      if (d.status === "failed") throw new Error(d.message || "导出失败");
      pollExport(d.status_url, d.mp4_url);
    }).catch(function (e) { setStatus(e.message, "err"); });
  });

  function pollExport(statusUrl, mp4Url) {
    showResult();
    pollTimer = setInterval(function () {
      fetch(statusUrl).then(function (r) { return r.json(); }).then(function (s) {
        if (s.status === "completed") {
          clearInterval(pollTimer); pollTimer = null;
          var url = (s.result && s.result.mp4_url) || mp4Url;
          previewEl.style.display = "none";
          videoEl.style.display = "block";
          videoEl.src = url + "?t=" + Date.now();
          resultActions.innerHTML =
            '<a class="dl" href="' + url + '" download>💾 下载 MP4</a>' +
            '<a href="' + url + '" target="_blank" rel="noopener">↗ 新窗口打开</a>';
          setStatus("✅ 视频已生成", "ok");
        } else if (s.status === "failed") {
          clearInterval(pollTimer); pollTimer = null;
          setStatus("导出失败：" + (s.error_message || "未知错误"), "err");
        } else {
          var p = s.progress != null ? " " + s.progress + "%" : "";
          setStatus("③ 导出中" + p + "…（" + (s.message || s.status) + "）", "work");
        }
      }).catch(function () { /* keep polling */ });
    }, 1200);
  }

  loadStyles();
  applyPreviewSize();
})();
