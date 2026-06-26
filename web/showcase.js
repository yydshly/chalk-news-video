(function () {
  "use strict";
  var capsEl = document.getElementById("caps");
  var ratioNote = document.getElementById("ratio-note");
  var galleryEl = document.getElementById("gallery");

  function tile(k, v, cls) {
    return '<div class="cap-tile"><div class="k">' + k + '</div><div class="v ' + (cls || "") + '">' + v + "</div></div>";
  }

  // 1) Capabilities matrix
  fetch("/api/episode/export/capabilities")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var sup = (d.supported_styles || []).map(function (s) { return s.name || s.id; });
      var lim = d.limits || {};
      var w = lim.width || {}, h = lim.height || {}, fps = lim.fps || {};
      var audio = d.audio || {};
      capsEl.innerHTML =
        tile("可出片风格", sup.length + " 种") +
        tile("默认尺寸", (w.default || 1280) + "×" + (h.default || 720) + "（16:9 横屏）") +
        tile("尺寸范围", (w.min || 360) + "–" + (w.max || 1080) + " × " + (h.min || 640) + "–" + (h.max || 1920)) +
        tile("帧率", (fps.default || 30) + " fps（上限 " + (fps.max || 30) + "）") +
        tile("真人口播 (MiniMax)", "实验能力", "") +
        tile("音频混流", audio.supports_audio_mux ? "支持" : "不支持", audio.supports_audio_mux ? "yes" : "no");
      ratioNote.textContent = "注：默认 16:9 横屏；5 种风格均为铺满式弹性布局，可切 9:16 竖屏 / 1:1 方形。";
      buildGallery(d.supported_styles || []);
    })
    .catch(function () { capsEl.innerHTML = '<span class="muted">能力加载失败</span>'; });

  // 2) Live sample gallery — build one sample contract, render every style
  function buildGallery(styles) {
    fetch("/api/episode/source-contract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_type: "sample_pack" }),
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok || !d.contract) throw new Error("样例契约失败");
        galleryEl.innerHTML = "";
        styles.forEach(function (s) {
          var box = document.createElement("div");
          box.className = "shot";
          box.innerHTML =
            "<h3>" + (s.name || s.id) + '<span class="tag">● 可出片</span></h3>' +
            '<div class="loading" data-style="' + s.id + '">渲染中…</div>';
          galleryEl.appendChild(box);
          renderStyle(box, d.contract, s.id);
        });
      })
      .catch(function () { galleryEl.innerHTML = '<span class="muted">样例生成失败</span>'; });
  }

  function renderStyle(box, contract, styleId) {
    fetch("/api/episode/preview-html", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contract: contract, style_id: styleId, persist: false }),
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok) throw new Error("render failed");
        var iframe = document.createElement("iframe");
        iframe.setAttribute("scrolling", "no");
        iframe.src = d.path + "?t=" + Date.now();
        var loading = box.querySelector(".loading");
        if (loading) loading.replaceWith(iframe);
      })
      .catch(function () {
        var loading = box.querySelector(".loading");
        if (loading) loading.textContent = "渲染失败";
      });
  }
})();
