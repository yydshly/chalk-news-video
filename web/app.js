/* Chalk News Video Studio — CP15.6 app.js */

(function () {
  "use strict";

  // ---------- DOM refs ----------
  const modeRadios = document.querySelectorAll('input[name="mode"]');
  const genModeRadios = document.querySelectorAll('input[name="gen_mode"]');
  const genModeHint = document.getElementById("gen-mode-hint");
  const labelCheckExport = document.getElementById("label-check-export");
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
  // CP19: Hot news DOM refs
  const hotNewsSection = document.getElementById("hot-news-section");
  const hotNewsLoading = document.getElementById("hot-news-loading");
  const hotNewsError = document.getElementById("hot-news-error");
  const hotNewsList = document.getElementById("hot-news-list");
  const hotNewsSelected = document.getElementById("hot-news-selected");
  const selectedNewsTitleEl = document.getElementById("selected-news-title");
  const btnRefreshHotNews = document.getElementById("btn-refresh-hot-news");

  // CP20: Theme showcase DOM refs
  const themeShowcaseSection = document.getElementById("theme-showcase-section");
  const themeShowcaseList = document.getElementById("theme-showcase-list");

  // CP21: Generation plan panel DOM refs
  const genPlanNews = document.getElementById("gen-plan-news");
  const genPlanTheme = document.getElementById("gen-plan-theme");
  const genPlanMode = document.getElementById("gen-plan-mode");
  const genPlanOutputs = document.getElementById("gen-plan-outputs");
  const genPlanTime = document.getElementById("gen-plan-time");
  const genPlanStatus = document.getElementById("gen-plan-status");
  const genPlanStatusRow = document.getElementById("gen-plan-status-row");

  // CP23: Episode planner DOM refs
  const episodePlanner = document.getElementById("episode-planner");
  const episodeItemsList = document.getElementById("episode-items");
  const episodeCount = document.getElementById("episode-count");
  const episodeEmpty = document.getElementById("episode-empty");
  const episodeStructure = document.getElementById("episode-structure");

  // ---------- state ----------
  let lastResult = null;
  let currentEventSource = null;
  let llmProviders = [];
  let ttsProviders = [];
  let latestSucceededJob = null;
  let selectedNews = null;       // CP19: user-selected hot news item
  let hotNewsItems = [];         // CP19: list of hot news candidates
  let episodeItemList = [];       // CP23: episode playlist items

  // CP20: Theme showcase data
  const THEME_SHOWCASES = {
    news_card_v1: {
      id: "news_card_v1",
      name: "新闻卡片风",
      desc: "适合快讯、产品发布、公司动态、热点新闻",
      tags: ["推荐", "新闻感强", "当前主推"],
      recommended: true,
      sample_url: "/examples/theme_samples/news_card_v1.html",
    },
    research_desk_v2: {
      id: "research_desk_v2",
      name: "AI 研究室风",
      desc: "适合技术解读、研究报告、模型能力分析",
      tags: ["深度解读", "技术感"],
      recommended: false,
      sample_url: "/examples/theme_samples/research_desk_v2.html",
    },
    causal_map_v1: {
      id: "causal_map_v1",
      name: "因果链地图",
      desc: "适合解释事件原因、影响链条、监管变化",
      tags: ["逻辑分析", "结构化"],
      recommended: false,
      sample_url: "/examples/theme_samples/causal_map_v1.html",
    },
  };

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
        opt.value = theme.id;
        opt.textContent = theme.name;
        selectTheme.appendChild(opt);
      });

      if (data.default_theme) {
        selectTheme.value = data.default_theme;
      }

      // CP20: Force default to news_card_v1 if available in the list
      const themeOptions = Array.from(selectTheme.querySelectorAll("option")).map(function (o) { return o.value; });
      if (themeOptions.includes("news_card_v1")) {
        selectTheme.value = "news_card_v1";
      }

      // CP20: Render theme showcase cards
      renderThemeShowcase();

      setStatus("就绪", "success");
    } catch (e) {
      setStatus("加载主题失败: " + e.message, "error");
      // Still render showcase even if API fails
      renderThemeShowcase();
    }

    // CP18.5: Initialize generation mode UI
    updateGenModeUI();

    // CP21: Initialize generation plan panel
    updateGenerationPlan();

    // CP19: Auto-load hot news if mode is hot_ai
    tryAutoLoadHotNews();

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

    const themeId = selectTheme.value;
    const themeName = (THEME_SHOWCASES[themeId] && THEME_SHOWCASES[themeId].name) ? THEME_SHOWCASES[themeId].name : themeId;

    let cfgText = "";
    if (llmId === "mock") {
      cfgText = "示例新闻 + " + themeName + " + mock LLM + mock_dialogue（本地无需 API key）";
    } else if (llm && llm.name) {
      cfgText = "热门 AI 新闻 + " + themeName + " + " + llm.name + " + mock_dialogue + 不导出 MP4";
    } else {
      cfgText = "热门 AI 新闻 + " + themeName + " + " + llmId + " + mock_dialogue + 不导出 MP4";
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
      updateGenerationPlan();
    });
  });

  // Update generation plan when text input changes
  if (inputNews) {
    inputNews.addEventListener("input", function () {
      updateGenerationPlan();
    });
  }

  // CP18.5: generation mode toggle
  genModeRadios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      updateGenModeUI();
      updateGenerationPlan();
    });
  });

  // ---------- hot news board (CP19) ----------
  async function loadHotNews() {
    hotNewsLoading.style.display = "block";
    hotNewsError.style.display = "none";
    hotNewsList.innerHTML = "";
    hotNewsSelected.style.display = "none";
    selectedNews = null;

    try {
      const resp = await fetch("/api/hot-ai-news");
      const data = await resp.json();

      if (!data.ok) {
        throw new Error(data.error || "加载失败");
      }

      hotNewsItems = data.items || [];
      renderHotNews();
    } catch (e) {
      hotNewsError.style.display = "block";
      hotNewsError.textContent = "新闻加载失败，请重试";
      hotNewsLoading.style.display = "none";
    }
  }

  function renderHotNews() {
    hotNewsLoading.style.display = "none";

    if (hotNewsItems.length === 0) {
      hotNewsError.style.display = "block";
      hotNewsError.textContent = "暂无合适新闻，请点击刷新重试";
      return;
    }

    hotNewsList.innerHTML = "";
    hotNewsItems.forEach(function (item, index) {
      const isInEpisode = episodeItemList.some(function (e) { return e.id === item.id; });
      const div = document.createElement("div");
      div.className = "hot-news-item";
      div.setAttribute("data-index", index);

      const joinBtnClass = isInEpisode ? "hot-news-item-select-btn hot-news-item-joined-btn" : "hot-news-item-select-btn";
      const joinBtnText = isInEpisode ? "已加入" : "加入合集";

      div.innerHTML =
        '<span class="hot-news-item-rank">#' + (index + 1) + '</span>' +
        '<div class="hot-news-item-title">' + escapeHtml(item.title || "") + '</div>' +
        '<div class="hot-news-item-meta">' +
          '<span>' + escapeHtml(item.source || "") + '</span> ' +
          '<span class="hot-news-item-score">★ ' + (item.final_score || 0).toFixed(1) + '</span> ' +
          '<span>' + (item.points || 0) + ' pts</span> ' +
          '<span>' + (item.comments || 0) + ' comments</span>' +
        '</div>' +
        '<div class="hot-news-item-actions-row">' +
          '<button class="hot-news-item-select-btn" type="button">选择这条</button>' +
          '<button class="hot-news-item-join-btn ' + joinBtnClass + '" type="button" data-episode-item-id="' + (item.id || "") + '">' + joinBtnText + '</button>' +
        '</div>';

      div.querySelector(".hot-news-item-select-btn").addEventListener("click", function (ev) {
        ev.stopPropagation();
        selectHotNewsItem(index);
      });

      div.addEventListener("click", function () {
        selectHotNewsItem(index);
      });

      const joinBtn = div.querySelector(".hot-news-item-join-btn");
      joinBtn.addEventListener("click", function (ev) {
        ev.stopPropagation();
        if (!isInEpisode) {
          addNewsToEpisode(item);
        }
      });

      hotNewsList.appendChild(div);
    });

    // Update generate button text based on selection state
    updateGenModeUI();
    updateGenerationPlan();
  }

  function selectHotNewsItem(index) {
    const item = hotNewsItems[index];
    if (!item) return;

    selectedNews = item;

    // Highlight selected item
    hotNewsList.querySelectorAll(".hot-news-item").forEach(function (el, i) {
      el.classList.toggle("selected", i === index);
    });

    // Show selected banner
    hotNewsSelected.style.display = "block";
    selectedNewsTitleEl.textContent = item.title || "";

    // Update generate button text
    updateGenModeUI();
    updateGenerationPlan();
  }

  // ---------- episode planner (CP23) ----------
  const MAX_EPISODE_ITEMS = 5;

  function addNewsToEpisode(item) {
    if (episodeItemList.length >= MAX_EPISODE_ITEMS) {
      setStatus("当前最多支持 " + MAX_EPISODE_ITEMS + " 条新闻", "error");
      return;
    }
    if (episodeItemList.some(function (e) { return e.id === item.id; })) {
      return; // Already in episode
    }
    episodeItemList.push({
      id: item.id,
      title: item.title,
      url: item.url,
      source: item.source,
      final_score: item.final_score,
      points: item.points,
      comments: item.comments,
    });
    renderEpisodePlanner();
    renderHotNews(); // Update join button states
  }

  function removeNewsFromEpisode(id) {
    episodeItemList = episodeItemList.filter(function (e) { return e.id !== id; });
    renderEpisodePlanner();
    renderHotNews(); // Update join button states
  }

  function moveEpisodeItem(id, direction) {
    const idx = episodeItemList.findIndex(function (e) { return e.id === id; });
    if (idx === -1) return;
    const newIdx = idx + direction;
    if (newIdx < 0 || newIdx >= episodeItemList.length) return;
    const item = episodeItemList.splice(idx, 1)[0];
    episodeItemList.splice(newIdx, 0, item);
    renderEpisodePlanner();
  }

  function renderEpisodePlanner() {
    if (!episodeItemsList) return;

    episodeCount.textContent = episodeItemList.length + " 条";

    if (episodeItemList.length === 0) {
      episodeItemsList.style.display = "none";
      episodeEmpty.style.display = "block";
      episodeStructure.innerHTML = "";
    } else {
      episodeEmpty.style.display = "none";
      episodeItemsList.style.display = "flex";

      episodeItemsList.innerHTML = "";
      episodeItemList.forEach(function (item, index) {
        const div = document.createElement("div");
        div.className = "episode-item";

        div.innerHTML =
          '<span class="episode-item-rank">#' + (index + 1) + '</span>' +
          '<span class="episode-item-title" title="' + escapeHtml(item.title || "") + '">' + escapeHtml(item.title || "") + '</span>' +
          '<span class="episode-item-meta">' + escapeHtml(item.source || "") + ' ★' + (item.final_score || 0).toFixed(1) + '</span>' +
          '<div class="episode-item-actions">' +
            (index > 0 ? '<button class="episode-item-btn" data-action="up" data-id="' + (item.id || "") + '">↑</button>' : '<button class="episode-item-btn" disabled>↑</button>') +
            (index < episodeItemList.length - 1 ? '<button class="episode-item-btn" data-action="down" data-id="' + (item.id || "") + '">↓</button>' : '<button class="episode-item-btn" disabled>↓</button>') +
            '<button class="episode-item-btn remove" data-action="remove" data-id="' + (item.id || "") + '">移除</button>' +
          '</div>';

        div.querySelectorAll(".episode-item-btn").forEach(function (btn) {
          btn.addEventListener("click", function () {
            const action = btn.getAttribute("data-action");
            const id = btn.getAttribute("data-id");
            if (action === "up") moveEpisodeItem(id, -1);
            else if (action === "down") moveEpisodeItem(id, 1);
            else if (action === "remove") removeNewsFromEpisode(id);
          });
        });

        episodeItemsList.appendChild(div);
      });

      // Render episode structure preview
      renderEpisodeStructure();
    }
  }

  function renderEpisodeStructure() {
    if (episodeItemList.length === 0) {
      episodeStructure.innerHTML = "";
      return;
    }

    const topNews = episodeItemList.reduce(function (best, item) {
      return (!best || (item.final_score || 0) > (best.final_score || 0)) ? item : best;
    }, null);

    let html = '<div class="episode-structure-title">📋 栏目结构</div>';
    html += '<div style="color:#64748b;margin-bottom:4px">开场：今日 AI 前沿速览</div>';
    episodeItemList.forEach(function (item, i) {
      html += '<div class="episode-structure-news">' + (i + 1) + '. ' + escapeHtml(item.title || "") + '</div>';
    });
    if (topNews) {
      html += '<div class="episode-structure-closing">结尾：今天最值得关注的是：' + escapeHtml(topNews.title || "") + '</div>';
    }

    episodeStructure.innerHTML = html;
  }

  // ---------- episode plan contract (CP24) ----------
  function buildEpisodePlan() {
    const theme = selectTheme.value;
    const genMode = document.querySelector('input[name="gen_mode"]:checked').value;

    const items = episodeItemList.map(function (item, index) {
      const isLead = index === 0 || (item.final_score || 0) >= (episodeItemList.reduce(function (max, i) {
        return (i.final_score || 0) > (max.final_score || 0) ? i : max;
      }, episodeItemList[0] || {}).final_score || 0) && index === 0;
      return {
        order: index + 1,
        id: item.id,
        title: item.title,
        url: item.url,
        source: item.source,
        final_score: item.final_score,
        points: item.points,
        comments: item.comments,
        role: isLead ? "lead" : "supporting",
      };
    });

    // Re-determine lead: highest score or first
    if (items.length > 0) {
      const maxScoreItem = items.reduce(function (best, item) {
        return (!best || (item.final_score || 0) > (best.final_score || 0)) ? item : best;
      }, null);
      if (maxScoreItem) {
        maxScoreItem.role = "lead";
      }
      // Only first item can be lead if scores are tied or first has highest
      items.forEach(function (item, i) {
        if (i > 0 && item.id === maxScoreItem.id) {
          item.role = "supporting";
        }
      });
    }

    const topNews = episodeItemList.reduce(function (best, item) {
      return (!best || (item.final_score || 0) > (best.final_score || 0)) ? item : best;
    }, null);

    const segments = items.map(function (item) {
      return {
        order: item.order,
        type: "news_segment",
        news_id: item.id,
        headline: item.title,
      };
    });

    const plan = {
      version: "episode_plan_v1",
      title: "今日 AI 前沿速览",
      subtitle: "多条热门 AI 新闻合集",
      theme: theme,
      generation_mode: genMode,
      items: items,
      structure: {
        opening: "今日 AI 前沿速览",
        segments: segments,
        closing: topNews ? {
          type: "summary",
          focus_news_id: topNews.id,
          focus_title: topNews.title,
        } : null,
      },
      constraints: {
        min_items: 2,
        max_items: 5,
        recommended_items: "2-4",
        target_duration_sec: 180,
      },
    };

    return plan;
  }

  function validateEpisodePlan(plan) {
    var warnings = [];
    var errors = [];

    if (!plan.items || plan.items.length === 0) {
      errors.push("至少需要 1 条新闻才能生成栏目计划");
      return { ok: false, warnings: warnings, errors: errors };
    }

    if (plan.items.length < 2) {
      warnings.push("建议至少加入 2 条新闻形成栏目");
    }

    if (plan.items.length > 5) {
      errors.push("最多支持 5 条新闻");
    }

    plan.items.forEach(function (item, i) {
      if (!item.id) errors.push("第 " + (i + 1) + " 条新闻缺少 id");
      if (!item.title) errors.push("第 " + (i + 1) + " 条新闻缺少 title");
      if (item.order !== i + 1) errors.push("第 " + (i + 1) + " 条新闻 order 序号不连续");
    });

    if (plan.structure && plan.structure.closing) {
      var closingId = plan.structure.closing.focus_news_id;
      var exists = plan.items.some(function (item) { return item.id === closingId; });
      if (!exists) errors.push("结尾推荐的新闻 ID 不在列表中");
    }

    return {
      ok: errors.length === 0,
      warnings: warnings,
      errors: errors,
    };
  }

  // Show episode plan in the episode_plan tab
  function showEpisodePlan() {
    if (episodeItemList.length === 0) {
      setStatus("请先加入新闻，再查看栏目计划", "error");
      return;
    }

    var plan = buildEpisodePlan();
    var result = validateEpisodePlan(plan);

    // Switch to episode_plan tab
    tabBtns.forEach(function (b) { b.classList.remove("active"); });
    tabContents.forEach(function (c) { c.classList.remove("active"); });
    var tabBtn = document.querySelector('[data-tab="episode_plan"]');
    var tabContent = document.getElementById("tab-episode_plan");
    if (tabBtn) tabBtn.classList.add("active");
    if (tabContent) tabContent.classList.add("active");

    var jsonEl = document.getElementById("json-episode_plan");
    if (jsonEl) {
      var output = JSON.stringify({ plan: plan, validation: result }, null, 2);
      jsonEl.textContent = output;
    }

    // Show validation status in status msg
    if (!result.ok) {
      setStatus("栏目计划有误：" + result.errors.join("；"), "error");
    } else if (result.warnings.length > 0) {
      setStatus("栏目计划已生成（" + result.warnings.join("；") + "）", "info");
    } else {
      setStatus("栏目计划已生成，可进入下一步", "success");
    }
  }

  // ---------- theme showcase (CP20) ----------
  function renderThemeShowcase() {
    if (!themeShowcaseList) return;
    themeShowcaseList.innerHTML = "";

    Object.values(THEME_SHOWCASES).forEach(function (theme) {
      const isSelected = selectTheme.value === theme.id;
      const div = document.createElement("div");
      div.className = "theme-showcase-card" + (isSelected ? " selected" : "");
      div.setAttribute("data-theme-id", theme.id);

      let tagsHtml = theme.tags.map(function (tag) {
        const isRecommend = tag === "推荐";
        return '<span class="theme-showcase-tag' + (isRecommend ? " tag-recommend" : "") + '">' + escapeHtml(tag) + '</span>';
      }).join("");

      div.innerHTML =
        '<div class="theme-showcase-header">' +
          '<span class="theme-showcase-name">' + escapeHtml(theme.name) + '</span>' +
          (theme.recommended ? '<span class="theme-showcase-recommended">★ 推荐</span>' : '') +
        '</div>' +
        '<div class="theme-showcase-desc">' + escapeHtml(theme.desc) + '</div>' +
        '<div class="theme-showcase-tags">' + tagsHtml + '</div>' +
        '<button class="theme-showcase-sample-btn" type="button">查看样例</button>';

      // Theme selection click (on card background)
      div.addEventListener("click", function (ev) {
        if (ev.target.classList.contains("theme-showcase-sample-btn")) return;
        selectTheme.value = theme.id;
        selectTheme.dispatchEvent(new Event("change"));
        renderThemeShowcase();
        updateRecommendedHint();
      });

      // Sample preview click (does NOT change theme selection)
      const sampleBtn = div.querySelector(".theme-showcase-sample-btn");
      if (sampleBtn) {
        sampleBtn.addEventListener("click", function (ev) {
          ev.stopPropagation();
          previewThemeSample(theme.id);
        });
      }

      themeShowcaseList.appendChild(div);
    });
  }

  // CP22: Preview theme sample in iframe without creating a job
  function previewThemeSample(themeId) {
    const theme = THEME_SHOWCASES[themeId];
    if (!theme || !theme.sample_url) return;

    // Switch to preview tab
    switchToPreviewTab();

    // Clear previous preview
    clearPreview();

    // Load sample HTML in iframe
    previewHtml.src = theme.sample_url + "?t=" + Date.now();

    // Show sample preview banner
    autoPreviewBanner.style.display = "block";
    autoPreviewBanner.textContent = "🎨 主题样例预览：" + theme.name;

    // Hide download links and audio player for sample preview
    downloadLinks.innerHTML = "";
    audioPlayerWrap.style.display = "none";

    // Switch to HTML preview mode
    setPreviewMode("html");
  }

  // Sync theme showcase selection when selectTheme changes programmatically
  if (selectTheme) {
    selectTheme.addEventListener("change", function () {
      renderThemeShowcase();
      updateGenerationPlan();
    });
  }

  // ---------- generation plan panel (CP21) ----------
  function updateGenerationPlan() {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const genMode = document.querySelector('input[name="gen_mode"]:checked').value;
    const themeId = selectTheme.value;
    const themeName = (THEME_SHOWCASES[themeId] && THEME_SHOWCASES[themeId].name) ? THEME_SHOWCASES[themeId].name : themeId;
    const isGenerating = btnGenerate.disabled;

    // News
    if (mode === "hot_ai") {
      if (selectedNews && selectedNews.title) {
        genPlanNews.textContent = selectedNews.title;
        genPlanNews.classList.remove("gen-plan-news-empty");
      } else {
        genPlanNews.textContent = "请选择一条热门 AI 新闻";
        genPlanNews.classList.add("gen-plan-news-empty");
      }
    } else if (mode === "text") {
      const text = inputNews.value.trim();
      if (text) {
        genPlanNews.textContent = "已输入新闻文本";
        genPlanNews.classList.remove("gen-plan-news-empty");
      } else {
        genPlanNews.textContent = "请输入新闻文本";
        genPlanNews.classList.add("gen-plan-news-empty");
      }
    } else {
      genPlanNews.textContent = "使用示例新闻";
      genPlanNews.classList.remove("gen-plan-news-empty");
    }

    // Theme
    genPlanTheme.textContent = themeName;

    // Gen mode info
    const modeInfo = {
      fast: { name: "快速预览", outputs: "animation.html", time: "较快", hint: "适合先看结构和画面" },
      voice: { name: "语音预览", outputs: "animation.html + dialogue.wav", time: "中等", hint: "适合听真实双人播报" },
      export: { name: "最终导出 MP4", outputs: "animation.html + dialogue.wav + output.mp4", time: "较慢", hint: "适合生成最终成片" },
    };
    const info = modeInfo[genMode] || modeInfo.fast;
    genPlanMode.textContent = info.name;
    genPlanOutputs.textContent = info.outputs;
    genPlanTime.textContent = info.time;

    // Status
    if (isGenerating) {
      genPlanStatus.textContent = "⟳ 正在生成...";
      genPlanStatus.className = "gen-plan-value gen-plan-status-working";
    } else if (mode === "hot_ai" && !selectedNews) {
      genPlanStatus.textContent = "⚠ 请先选择新闻";
      genPlanStatus.className = "gen-plan-value gen-plan-status-warning";
    } else if (mode === "text" && !inputNews.value.trim() && document.querySelector('input[name="mode"]:checked').value === "text") {
      genPlanStatus.textContent = "⚠ 请输入新闻文本";
      genPlanStatus.className = "gen-plan-value gen-plan-status-warning";
    } else {
      genPlanStatus.textContent = "✓ 已就绪";
      genPlanStatus.className = "gen-plan-value gen-plan-status-ready";
    }
  }

  // Load hot news when switching to hot_ai mode
  modeRadios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      if (radio.value === "hot_ai") {
        loadHotNews();
      }
      updateGenModeUI();
      updateGenerationPlan();
    });
  });

  // Refresh button
  if (btnRefreshHotNews) {
    btnRefreshHotNews.addEventListener("click", function () {
      loadHotNews();
    });
  }

  // CP24: View episode plan button
  var btnViewEpisodePlan = document.getElementById("btn-view-episode-plan");
  if (btnViewEpisodePlan) {
    btnViewEpisodePlan.addEventListener("click", function () {
      showEpisodePlan();
    });
  }

  // Auto-load hot news on init if mode is hot_ai
  function tryAutoLoadHotNews() {
    const checkedMode = document.querySelector('input[name="mode"]:checked');
    if (checkedMode && checkedMode.value === "hot_ai") {
      loadHotNews();
    }
  }

  function updateGenModeUI() {
    const genMode = document.querySelector('input[name="gen_mode"]:checked').value;
    const hasSelectedNews = selectedNews && selectedNews.title;
    const currentMode = document.querySelector('input[name="mode"]:checked').value;
    const isHotAiMode = currentMode === "hot_ai";

    // Update hint text
    if (genMode === "fast") {
      genModeHint.textContent = "最快，只生成动画预览，不调用真实 TTS，不导出 MP4。";
      checkExport.checked = false;
      labelCheckExport.classList.add("checkbox-export-hidden");
      if (isHotAiMode) {
        btnGenerate.textContent = hasSelectedNews ? "生成所选新闻快速预览" : "请先选择一条新闻";
      } else {
        btnGenerate.textContent = hasSelectedNews ? "生成所选新闻快速预览" : "生成快速预览";
      }
    } else if (genMode === "voice") {
      genModeHint.textContent = "生成真实双人语音，但不导出 MP4。";
      checkExport.checked = false;
      labelCheckExport.classList.add("checkbox-export-hidden");
      if (isHotAiMode) {
        btnGenerate.textContent = hasSelectedNews ? "生成所选新闻语音预览" : "请先选择一条新闻";
      } else {
        btnGenerate.textContent = hasSelectedNews ? "生成所选新闻语音预览" : "生成语音预览";
      }
    } else {
      genModeHint.textContent = "生成完整 MP4，耗时较长，请耐心等待。";
      checkExport.checked = true;
      labelCheckExport.classList.add("checkbox-export-hidden");
      if (isHotAiMode) {
        btnGenerate.textContent = hasSelectedNews ? "导出所选新闻 MP4 成片" : "请先选择一条新闻";
      } else {
        btnGenerate.textContent = hasSelectedNews ? "导出所选新闻 MP4 成片" : "导出 MP4 成片";
      }
    }
  }

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
    const title = inputTitle.value.trim();
    const newsText = inputNews.value.trim();

    if (mode === "text" && !newsText) {
      setStatus("请输入新闻正文", "error");
      return;
    }

    // CP19.1: Block generation in hot_ai mode without news selection
    if (mode === "hot_ai" && !selectedNews) {
      setStatus("请先选择一条新闻，或点击刷新重新加载候选", "error");
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

    // CP18.5: Build payload based on generation mode
    const genMode = document.querySelector('input[name="gen_mode"]:checked').value;

    // TTS provider: mock if fast, user-selected otherwise
    const effectiveTts = (genMode === "fast") ? "mock_dialogue" : selectTtsProvider.value;

    // no_export: true for fast and voice, false for export
    const effectiveNoExport = (genMode !== "export");

    const payload = {
      mode: mode,
      theme: theme,
      dialogue: dialogue,
      mock: selectLlmProvider.value === "mock",
      no_export: effectiveNoExport,
      llm_provider: selectLlmProvider.value,
      tts_provider: effectiveTts,
      repair: checkRepair.checked,
      repair_attempts: 2,
      target_duration_sec: 45,
      // CP19: user-selected hot news
      selected_news_id: selectedNews ? (selectedNews.id || null) : null,
      selected_news_title: selectedNews ? (selectedNews.title || null) : null,
      selected_news_url: selectedNews ? (selectedNews.url || null) : null,
      selected_news_source: selectedNews ? (selectedNews.source || null) : null,
      max_turns: 10,
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
        updateGenerationPlan();
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
        updateGenerationPlan();
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
      updateGenerationPlan();
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
        setPreviewMode("video");
        previewVideo.src = job.output_mp4 + "?t=" + Date.now();
        previewVideo.play().catch(function () {});
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

    // CP18.3.1: Set preview mode first — video takes priority over animation
    if (job.output_mp4) {
      setPreviewMode("video");
      previewVideo.src = job.output_mp4 + ts;
      previewVideo.play().catch(function () {});
    } else {
      setPreviewMode("html");
      if (job.animation_html) {
        previewHtml.src = job.animation_html + ts;
      }
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

  // CP18.3.1: Preview mode toggle (animation.html vs MP4 video)
  function setPreviewMode(mode) {
    if (mode === "video") {
      document.body.classList.add("preview-mode-video");
      document.body.classList.remove("preview-mode-html");
    } else {
      document.body.classList.add("preview-mode-html");
      document.body.classList.remove("preview-mode-video");
    }
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
    // CP18.3.1: Reset to HTML preview mode as default
    setPreviewMode("html");
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

    // CP18.3.1: Set preview mode before loading content
    if (result.exported === true && result.output_mp4) {
      setPreviewMode("video");
      previewVideo.src = result.output_mp4 + ts;
      // Auto-play MP4 when loaded
      previewVideo.play().catch(function () {});
      downloadLinks.innerHTML = "";
      addDownloadLink(result.animation_html, "📄 animation.html");
      addDownloadLink(result.output_mp4, "🎬 output.mp4");
      setExportHint(true);
    } else {
      setPreviewMode("html");
      previewVideo.src = "about:blank";
      downloadLinks.innerHTML = "";
      if (result.animation_html) {
        previewHtml.src = result.animation_html + ts;
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
