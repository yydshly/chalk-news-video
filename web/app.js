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
  const genPlanRecommendRow = document.getElementById("gen-plan-recommend-row");
  const genPlanRecommend = document.getElementById("gen-plan-recommend");
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

  // CP32: Episode HTML artifact history DOM refs
  const episodeHtmlHistorySection = document.getElementById("episode-html-history-section");
  const episodeHtmlHistoryListEl = document.getElementById("episode-html-history-list");

  // CP35: Episode preview style selector DOM ref
  const selectEpisodePreviewStyle = document.getElementById("select-episode-preview-style");

  // ---------- state ----------
  let lastResult = null;
  let currentEventSource = null;
  let llmProviders = [];
  let ttsProviders = [];
  let latestSucceededJob = null;
  let selectedNews = null;       // CP19: user-selected hot news item
  let hotNewsItems = [];         // CP19: list of hot news candidates
  let episodeItemList = [];       // CP23: episode playlist items
  let latestEpisodePlan = null;    // CP24: most recent episode plan
  let latestEpisodeScript = null;  // CP25: most recent episode script
  let latestEpisodeAudioManifest = null;  // CP26: most recent audio manifest
  let latestEpisodeRenderIr = null;        // CP27: most recent render IR
  let latestEpisodePreviewUrl = null;      // CP28: Blob URL for mock HTML preview
  let latestEpisodeHtmlArtifact = null;    // CP31: saved episode HTML artifact
  let episodeHtmlHistoryList = [];        // CP32: episode HTML artifact history
  let latestEpisodeTemplateContract = null;  // CP34: most recent episode template contract
  let currentEpisodePreviewStyle = "timeline_daily_v1";  // CP35: current episode visual style
  let currentStyleRecommendations = [];    // CP30: current style recommendations

  // CP20/CG29: Expanded theme showcase data — video style gallery
  const THEME_SHOWCASES = {
    news_card_v1: {
      id: "news_card_v1",
      name: "新闻卡片风",
      category: "新闻快讯",
      desc: "适合快讯、产品发布、公司动态、热点新闻",
      best_for: "快讯、产品发布、公司动态、热点新闻",
      tags: ["推荐", "新闻感强", "当前主推"],
      recommended: true,
      visual_density: "high",
      motion_level: "subtle",
      sample_url: "/examples/theme_samples/news_card_v1.html",
    },
    research_desk_v2: {
      id: "research_desk_v2",
      name: "AI 研究室风",
      category: "技术解读",
      desc: "适合技术解读、研究报告、模型能力分析",
      best_for: "技术解读、研究报告、模型能力分析",
      tags: ["深度解读", "技术感"],
      recommended: false,
      visual_density: "medium",
      motion_level: "subtle",
      sample_url: "/examples/theme_samples/research_desk_v2.html",
    },
    causal_map_v1: {
      id: "causal_map_v1",
      name: "因果链地图",
      category: "逻辑分析",
      desc: "适合解释事件原因、影响链条、监管变化",
      best_for: "事件原因、影响链条、监管变化",
      tags: ["逻辑分析", "结构化"],
      recommended: false,
      visual_density: "medium",
      motion_level: "subtle",
      sample_url: "/examples/theme_samples/causal_map_v1.html",
    },
    timeline_brief_v1: {
      id: "timeline_brief_v1",
      name: "时间线快报",
      category: "多新闻日报",
      desc: "适合多事件串联、日报、事件进展梳理",
      best_for: "多事件串联、日报、事件进展",
      tags: ["日报", "时间线", "多新闻"],
      recommended: false,
      visual_density: "high",
      motion_level: "subtle",
      sample_url: "/examples/theme_samples/timeline_brief_v1.html",
    },
    data_dashboard_v1: {
      id: "data_dashboard_v1",
      name: "数据仪表盘",
      category: "数据图表",
      desc: "适合融资、榜单、模型分数、用户量等数据展示",
      best_for: "融资、榜单、模型分数、用户量",
      tags: ["数据", "图表", "榜单"],
      recommended: false,
      visual_density: "high",
      motion_level: "none",
      sample_url: "/examples/theme_samples/data_dashboard_v1.html",
    },
    breaking_news_v1: {
      id: "breaking_news_v1",
      name: "突发新闻快讯",
      category: "新闻快讯",
      desc: "适合重大发布、政策变化、突发事件",
      best_for: "重大发布、政策变化、突发事件",
      tags: ["突发", "紧急", "重点标记"],
      recommended: false,
      visual_density: "high",
      motion_level: "active",
      sample_url: "/examples/theme_samples/breaking_news_v1.html",
    },
    product_launch_v1: {
      id: "product_launch_v1",
      name: "产品发布会",
      category: "产品发布",
      desc: "适合新产品、新模型、新功能发布的展示",
      best_for: "新产品、新模型、新功能发布",
      tags: ["产品", "发布", "新功能"],
      recommended: false,
      visual_density: "high",
      motion_level: "active",
      sample_url: "/examples/theme_samples/product_launch_v1.html",
    },
    paper_digest_v1: {
      id: "paper_digest_v1",
      name: "论文速读",
      category: "技术解读",
      desc: "适合 arXiv 论文、技术报告、学术解读",
      best_for: "arXiv、论文、技术报告",
      tags: ["论文", "学术", "arXiv"],
      recommended: false,
      visual_density: "medium",
      motion_level: "subtle",
      sample_url: "/examples/theme_samples/paper_digest_v1.html",
    },
    podcast_cards_v1: {
      id: "podcast_cards_v1",
      name: "双人观点卡",
      category: "观点解读",
      desc: "适合双人解读、争议话题、观点对照",
      best_for: "双人解读、争议话题、观点对照",
      tags: ["双人", "观点", "对照"],
      recommended: false,
      visual_density: "medium",
      motion_level: "subtle",
      sample_url: "/examples/theme_samples/podcast_cards_v1.html",
    },
    dev_terminal_v1: {
      id: "dev_terminal_v1",
      name: "开发者终端风",
      category: "开发者技术",
      desc: "适合 GitHub、开源项目、开发工具",
      best_for: "GitHub、开源项目、开发工具",
      tags: ["开发者", "终端", "代码感"],
      recommended: false,
      visual_density: "low",
      motion_level: "none",
      sample_url: "/examples/theme_samples/dev_terminal_v1.html",
    },
    magazine_cover_v1: {
      id: "magazine_cover_v1",
      name: "杂志封面风",
      category: "专题封面",
      desc: "适合日报封面、专题合集、强标题视觉",
      best_for: "日报封面、专题合集、强标题视觉",
      tags: ["封面", "专题", "视觉强"],
      recommended: false,
      visual_density: "high",
      motion_level: "none",
      sample_url: "/examples/theme_samples/magazine_cover_v1.html",
    },
    opinion_column_v1: {
      id: "opinion_column_v1",
      name: "观点评论风",
      category: "观点解读",
      desc: "适合事件评论、趋势判断、影响分析",
      best_for: "事件评论、趋势判断、影响分析",
      tags: ["评论", "观点", "分析"],
      recommended: false,
      visual_density: "medium",
      motion_level: "subtle",
      sample_url: "/examples/theme_samples/opinion_column_v1.html",
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
      // CP29.1: Sync showcase themes into selectTheme before rendering
      syncThemeSelectWithShowcases();
      renderThemeShowcase();

      setStatus("就绪", "success");
    } catch (e) {
      setStatus("加载主题失败: " + e.message, "error");
      // CP29.1: Still sync showcase themes and render even if API fails
      syncThemeSelectWithShowcases();
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

    // CP32: Load episode HTML artifact history
    loadEpisodeHtmlHistory();
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
  // CP30: News-aware style recommendation
  function recommendStylesForNews(newsItem) {
    if (!newsItem) return [];

    var text = [
      newsItem.title || "",
      newsItem.summary || "",
      newsItem.source || "",
    ].join(" ").toLowerCase();

    var score = newsItem.final_score || 0;
    var points = newsItem.points || 0;

    var picked = [];

    // 1. Product launch / release
    if (/\b(launch|launches|release|releases|announces|unveils|introduces|product|app |feature |api |model)\b/.test(text)) {
      picked.push({ theme_id: "product_launch_v1", reason: "产品发布类新闻，适合产品发布会风格" });
      picked.push({ theme_id: "news_card_v1", reason: "热点新闻，适合新闻卡片快速讲清" });
    }

    // 2. Paper / research
    if (/\b(paper|arxiv|research|study|benchmark|eval|dataset|method|reasoning)\b/.test(text)) {
      picked.push({ theme_id: "paper_digest_v1", reason: "论文研究类，适合论文速读风格" });
      picked.push({ theme_id: "research_desk_v2", reason: "技术深度解读，适合研究室风格" });
    }

    // 3. Developer / open source
    if (/\b(github|open source|repo|library|framework|sdk|cli|terminal|developer)\b/.test(text)) {
      picked.push({ theme_id: "dev_terminal_v1", reason: "开发者类，适合终端风格" });
      picked.push({ theme_id: "research_desk_v2", reason: "技术解读，适合研究室风格" });
    }

    // 4. Data / funding / leaderboard
    if (/\b(funding|raises|valuation|revenue|users|benchmark|score|ranking|leaderboard|downloads)\b/.test(text)) {
      picked.push({ theme_id: "data_dashboard_v1", reason: "数据榜单类，适合仪表盘风格" });
      picked.push({ theme_id: "news_card_v1", reason: "热点数据，适合新闻卡片" });
    }

    // 5. Breaking / regulation
    if (/\b(breaking|ban|regulation|lawsuit|outage|security|policy|government|antitrust)\b/.test(text)) {
      picked.push({ theme_id: "breaking_news_v1", reason: "突发重大新闻，适合突发快讯风格" });
      picked.push({ theme_id: "causal_map_v1", reason: "重大变化因果分析，适合因果链地图" });
    }

    // 6. Causal / opinion / analysis
    if (/\b(why|because|impact|effect|risk|concern|debate|controversy|backlash)\b/.test(text)) {
      picked.push({ theme_id: "causal_map_v1", reason: "因果分析类，适合因果链地图" });
      picked.push({ theme_id: "opinion_column_v1", reason: "观点评论类，适合评论风" });
    }

    // 7. Multi-news / episode mode
    if (episodeItemList.length >= 2) {
      picked.push({ theme_id: "timeline_brief_v1", reason: "多新闻合集，适合时间线快报" });
      picked.push({ theme_id: "magazine_cover_v1", reason: "多新闻封面，适合杂志封面风" });
    }

    // 8. High-score news gets news_card / breaking
    if (score >= 8.0 || points >= 200) {
      if (!picked.some(function (p) { return p.theme_id === "news_card_v1"; })) {
        picked.push({ theme_id: "news_card_v1", reason: "高热度新闻，适合新闻卡片" });
      }
    }
    if (score >= 8.5) {
      if (!picked.some(function (p) { return p.theme_id === "breaking_news_v1"; })) {
        picked.push({ theme_id: "breaking_news_v1", reason: "极高分新闻，适合突发快讯" });
      }
    }

    // Deduplicate by theme_id, keep first occurrence (highest priority)
    var seen = {};
    var unique = [];
    picked.forEach(function (p) {
      if (!seen[p.theme_id]) {
        seen[p.theme_id] = true;
        unique.push(p);
      }
    });

    // CP30.1: Fallback — ensure at least 2 recommendations
    var FALLBACK_THEMES = [
      { theme_id: "news_card_v1", reason: "通用推荐，适合大多数新闻" },
      { theme_id: "research_desk_v2", reason: "技术解读通用风格" },
      { theme_id: "opinion_column_v1", reason: "观点评论通用风格" },
    ];

    if (unique.length < 2) {
      FALLBACK_THEMES.forEach(function (fb) {
        if (unique.length >= 3) return;
        if (!seen[fb.theme_id]) {
          seen[fb.theme_id] = true;
          unique.push(fb);
        }
      });
    }

    return unique.slice(0, 3);
  }

  // CP30.2: Unified active state sync for all style recommendation tags
  // Covers both hot-news card tags (.style-recommend-tag) and gen-plan tags (.gen-plan-recommend-tag).
  // Does NOT re-render any DOM — only toggles .active class.
  function updateStyleRecommendationActiveStates() {
    var currentTheme = selectTheme.value;
    // Hot news card tags
    if (hotNewsList) {
      var cardTags = hotNewsList.querySelectorAll(".style-recommend-tag");
      cardTags.forEach(function (tag) {
        tag.classList.toggle("active", tag.getAttribute("data-theme-id") === currentTheme);
      });
    }
    // Gen plan panel tags
    if (genPlanRecommend) {
      var planTags = genPlanRecommend.querySelectorAll(".gen-plan-recommend-tag");
      planTags.forEach(function (tag) {
        tag.classList.toggle("active", tag.getAttribute("data-theme-id") === currentTheme);
      });
    }
  }

  // CP30.1: Keep old name as wrapper for backward compatibility
  function updateHotNewsRecommendationActiveStates() {
    updateStyleRecommendationActiveStates();
  }

  // CP30: Update UI with current style recommendations
  function updateStyleRecommendations() {
    var newsItem = selectedNews;
    currentStyleRecommendations = recommendStylesForNews(newsItem);

    // Update gen plan panel recommendation row
    if (genPlanRecommendRow && genPlanRecommend) {
      if (!selectedNews || currentStyleRecommendations.length === 0) {
        genPlanRecommendRow.style.display = "none";
        genPlanRecommend.innerHTML = "";
      } else {
        genPlanRecommendRow.style.display = "flex";
        genPlanRecommend.innerHTML = "";
        currentStyleRecommendations.forEach(function (rec) {
          var theme = THEME_SHOWCASES[rec.theme_id];
          if (!theme) return;
          var isActive = selectTheme.value === rec.theme_id;
          var btn = document.createElement("button");
          btn.className = "gen-plan-recommend-tag" + (isActive ? " active" : "");
          btn.textContent = theme.name;
          btn.setAttribute("data-theme-id", rec.theme_id);
          btn.setAttribute("title", rec.reason);
          btn.addEventListener("click", function () {
            var t = THEME_SHOWCASES[rec.theme_id];
            if (t) {
              ensureThemeOption(t);
              // renderThemeShowcase + updateStyleRecommendationActiveStates fired by selectTheme "change" listener
              updateStyleRecommendations();
              updateGenerationPlan();
            }
          });
          genPlanRecommend.appendChild(btn);
        });
        // CP30.2: Sync active states after building new tags
        updateStyleRecommendationActiveStates();
      }
    }
  }

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
        '<div class="style-recommend-tags"></div>' +
        '<div class="hot-news-item-actions-row">' +
          '<button class="hot-news-item-select-btn" type="button">选择这条</button>' +
          '<button class="hot-news-item-join-btn ' + joinBtnClass + '" type="button" data-episode-item-id="' + (item.id || "") + '">' + joinBtnText + '</button>' +
        '</div>';

      // CP30: Add style recommendation tags to this card
      var recTagsContainer = div.querySelector(".style-recommend-tags");
      var recs = recommendStylesForNews(item);
      recs.forEach(function (rec) {
        var theme = THEME_SHOWCASES[rec.theme_id];
        if (!theme) return;
        var isActive = selectTheme.value === rec.theme_id;
        var btn = document.createElement("button");
        btn.className = "style-recommend-tag" + (isActive ? " active" : "");
        btn.textContent = theme.name;
        btn.setAttribute("data-theme-id", rec.theme_id);
        btn.setAttribute("title", rec.reason);
        btn.addEventListener("click", function (ev) {
          ev.stopPropagation();
          var t = THEME_SHOWCASES[rec.theme_id];
          if (t) {
            ensureThemeOption(t);
            // renderThemeShowcase + updateHotNewsRecommendationActiveStates fired by selectTheme "change" listener
            updateStyleRecommendations();
            updateGenerationPlan();
          }
        });
        recTagsContainer.appendChild(btn);
      });

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
    updateStyleRecommendations();
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

    // CP30: Update style recommendations
    updateStyleRecommendations();

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

    // Determine lead: highest final_score wins; if tied, first in list wins
    const leadSource = episodeItemList.reduce(function (best, item) {
      if (!best) return item;
      const bestScore = best.final_score || 0;
      const itemScore = item.final_score || 0;
      if (itemScore > bestScore) return item;
      return best;
    }, null);

    const items = episodeItemList.map(function (item, index) {
      return {
        order: index + 1,
        id: item.id,
        title: item.title,
        url: item.url,
        source: item.source,
        final_score: item.final_score,
        points: item.points,
        comments: item.comments,
        role: (leadSource && item.id === leadSource.id) ? "lead" : "supporting",
      };
    });

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
        closing: leadSource ? {
          type: "summary",
          focus_news_id: leadSource.id,
          focus_title: leadSource.title,
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

    // Role validation: exactly one lead
    var leadCount = 0;
    var leadItem = null;
    plan.items.forEach(function (item, i) {
      if (!item.id) errors.push("第 " + (i + 1) + " 条新闻缺少 id");
      if (!item.title) errors.push("第 " + (i + 1) + " 条新闻缺少 title");
      if (item.order !== i + 1) errors.push("第 " + (i + 1) + " 条新闻 order 序号不连续");
      if (item.role === "lead") {
        leadCount++;
        leadItem = item;
      }
    });

    if (leadCount !== 1) {
      errors.push("必须有且只有 1 个 lead，当前有 " + leadCount + " 个");
    }

    if (plan.structure && plan.structure.closing) {
      var closingId = plan.structure.closing.focus_news_id;
      var exists = plan.items.some(function (item) { return item.id === closingId; });
      if (!exists) errors.push("结尾推荐的新闻 ID 不在列表中");
      // closing.focus_news_id must match lead item
      if (leadItem && closingId !== leadItem.id) {
        errors.push("结尾 focus_news_id 必须与 lead item 的 id 一致");
      }
    }

    return {
      ok: errors.length === 0,
      warnings: warnings,
      errors: errors,
    };
  }

  // CP25: Build episode script from episode plan (mock rules, no real LLM)
  function buildEpisodeScriptFromPlan(plan) {
    if (!plan || !plan.items || plan.items.length === 0) {
      return null;
    }

    var leadItem = null;
    plan.items.forEach(function (item) {
      if (item.role === "lead") leadItem = item;
    });

    var segments = plan.items.map(function (item, index) {
      var isLead = item.role === "lead";
      var beats = [
        {
          type: "headline",
          text: "第 " + (index + 1) + " 条，" + item.title + "。",
        },
        {
          type: "context",
          text: isLead
            ? "这条是今天的主线新闻，热度和讨论度都比较高。"
            : "这条可以作为补充观察，帮助我们理解今天的 AI 动向。",
        },
        {
          type: "takeaway",
          text: "后续值得关注它是否会带来产品、模型或市场层面的变化。",
        },
      ];
      return {
        order: item.order,
        type: "news_segment",
        news_id: item.id,
        headline: item.title,
        role: item.role,
        beats: beats,
        duration_hint_sec: 35,
      };
    });

    var transitions = [];
    for (var i = 0; i < plan.items.length - 1; i++) {
      transitions.push({
        after_order: plan.items[i].order,
        text: "接着看下一条。",
      });
    }

    var script = {
      version: "episode_script_v1",
      episode_title: plan.title || "今日 AI 前沿速览",
      theme: plan.theme,
      generation_mode: plan.generation_mode,
      estimated_duration_sec: 180,
      opening: {
        type: "opening",
        text: "今天我们快速看几条值得关注的 AI 新闻。",
        duration_hint_sec: 12,
      },
      segments: segments,
      transitions: transitions,
      closing: leadItem ? {
        type: "closing",
        focus_news_id: leadItem.id,
        text: "今天最值得关注的是：" + leadItem.title + "。",
      } : null,
      constraints: {
        min_segments: 2,
        max_segments: 5,
        target_duration_sec: 180,
        tone: "清晰、克制、新闻解说",
      },
    };

    return script;
  }

  // CP25: Validate episode script
  function validateEpisodeScript(script) {
    var warnings = [];
    var errors = [];

    if (!script) {
      errors.push("脚本为空");
      return { ok: false, warnings: warnings, errors: errors };
    }

    if (script.version !== "episode_script_v1") {
      errors.push("version 必须为 episode_script_v1");
    }

    if (!script.opening || !script.opening.text) {
      errors.push("opening.text 不能为空");
    }

    if (!script.segments || script.segments.length < 1) {
      errors.push("至少需要 1 个 segment");
    }

    if (script.segments && script.segments.length > 5) {
      errors.push("最多支持 5 个 segment");
    }

    var leadCount = 0;
    var leadSegment = null;
    script.segments && script.segments.forEach(function (seg, i) {
      if (!seg.news_id) errors.push("第 " + (i + 1) + " 个 segment 缺少 news_id");
      if (!seg.headline) errors.push("第 " + (i + 1) + " 个 segment 缺少 headline");
      if (!seg.beats || seg.beats.length < 3) {
        errors.push("第 " + (i + 1) + " 个 segment 至少需要 3 个 beats");
      }
      if (seg.role === "lead") {
        leadCount++;
        leadSegment = seg;
      }
    });

    if (leadCount !== 1) {
      errors.push("必须有且只有 1 个 lead segment，当前有 " + leadCount + " 个");
    }

    if (script.closing && leadSegment) {
      if (script.closing.focus_news_id !== leadSegment.news_id) {
        errors.push("closing.focus_news_id 必须等于 lead segment 的 news_id");
      }
    }

    // No API key / voice_id leakage check
    var scriptStr = JSON.stringify(script);
    if (/api[_-]?key/i.test(scriptStr) || /voice[_-]?id/i.test(scriptStr)) {
      errors.push("脚本中不允许出现 API key 或 voice_id");
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

    // CP24: Save latest plan
    latestEpisodePlan = plan;

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

  // CP25: Show episode script preview
  function showEpisodeScript() {
    if (episodeItemList.length === 0) {
      setStatus("请先加入新闻，再生成栏目脚本", "error");
      return;
    }

    var plan = buildEpisodePlan();
    var planResult = validateEpisodePlan(plan);

    // If plan has errors, block script generation
    if (!planResult.ok) {
      setStatus("栏目计划有误，无法生成脚本：" + planResult.errors.join("；"), "error");
      return;
    }

    var script = buildEpisodeScriptFromPlan(plan);
    var scriptResult = validateEpisodeScript(script);

    // CP25: Save latest script
    latestEpisodeScript = script;

    // Switch to episode_script tab
    tabBtns.forEach(function (b) { b.classList.remove("active"); });
    tabContents.forEach(function (c) { c.classList.remove("active"); });
    var tabBtn = document.querySelector('[data-tab="episode_script"]');
    var tabContent = document.getElementById("tab-episode_script");
    if (tabBtn) tabBtn.classList.add("active");
    if (tabContent) tabContent.classList.add("active");

    var jsonEl = document.getElementById("json-episode_script");
    if (jsonEl) {
      var output = JSON.stringify({ script: script, validation: scriptResult }, null, 2);
      jsonEl.textContent = output;
    }

    if (!scriptResult.ok) {
      setStatus("栏目脚本有误：" + scriptResult.errors.join("；"), "error");
    } else if (scriptResult.warnings.length > 0) {
      setStatus("栏目脚本已生成（" + scriptResult.warnings.join("；") + "）", "info");
    } else {
      setStatus("栏目脚本草案已生成", "success");
    }
  }

  // CP26: Build episode audio manifest from episode script (mock, no real TTS)
  function buildEpisodeAudioManifestFromScript(script) {
    if (!script) {
      return null;
    }

    var clips = [];
    var order = 1;

    // Opening clip
    if (script.opening) {
      clips.push({
        clip_id: "opening_001",
        order: order++,
        section: "opening",
        speaker: "host_a",
        text: script.opening.text,
        duration_hint_sec: 12,
        audio_path: null,
      });
    }

    // Per-segment clips
    if (script.segments) {
      script.segments.forEach(function (seg) {
        var segIdx = seg.segment_order || seg.order;
        var segPrefix = "seg_" + String(segIdx).padStart(3, "0");

        if (seg.beats) {
          seg.beats.forEach(function (beat) {
            var beatType = beat.type; // headline | context | takeaway
            var speaker = "host_a";
            var durHint = 10;
            if (beatType === "headline") { speaker = "host_a"; durHint = 8; }
            else if (beatType === "context") { speaker = "host_b"; durHint = 14; }
            else if (beatType === "takeaway") { speaker = "host_a"; durHint = 10; }

            clips.push({
              clip_id: segPrefix + "_" + beatType,
              order: order++,
              section: "segment",
              segment_order: seg.order,
              news_id: seg.news_id,
              beat_type: beatType,
              speaker: speaker,
              text: beat.text,
              duration_hint_sec: durHint,
              audio_path: null,
            });
          });
        }

        // Transition after this segment (if not last)
        var segIdx2 = seg.order || seg.segment_order;
        if (segIdx2 < script.segments.length) {
          clips.push({
            clip_id: "transition_after_" + String(segIdx2).padStart(3, "0"),
            order: order++,
            section: "transition",
            speaker: "host_b",
            text: "接着看下一条。",
            duration_hint_sec: 4,
            audio_path: null,
          });
        }
      });
    }

    // Closing clip
    if (script.closing) {
      clips.push({
        clip_id: "closing_001",
        order: order++,
        section: "closing",
        speaker: "host_a",
        text: script.closing.text,
        duration_hint_sec: 12,
        audio_path: null,
      });
    }

    var totalDuration = clips.reduce(function (sum, c) {
      return sum + (c.duration_hint_sec || 0);
    }, 0);

    var manifest = {
      version: "episode_audio_manifest_v1",
      episode_title: script.episode_title || "今日 AI 前沿速览",
      source_script_version: "episode_script_v1",
      voice_mode: "dual_speaker",
      estimated_duration_sec: totalDuration,
      clips: clips,
      mixing: {
        format: "wav",
        sample_rate: 32000,
        channels: 1,
        silence_between_clips_sec: 0.25,
      },
      constraints: {
        no_real_tts: true,
        audio_paths_are_placeholders: true,
      },
    };

    return manifest;
  }

  // CP26: Validate episode audio manifest
  function validateEpisodeAudioManifest(manifest) {
    var warnings = [];
    var errors = [];

    if (!manifest) {
      errors.push("manifest 为空");
      return { ok: false, warnings: warnings, errors: errors };
    }

    if (manifest.version !== "episode_audio_manifest_v1") {
      errors.push("version 必须为 episode_audio_manifest_v1");
    }

    if (!manifest.clips || manifest.clips.length < 1) {
      errors.push("至少需要 1 个 clip");
    }

    var clipIds = {};
    manifest.clips && manifest.clips.forEach(function (clip, i) {
      if (clip.order !== i + 1) {
        errors.push("第 " + (i + 1) + " 个 clip 的 order 不连续");
      }
      if (!clip.clip_id) {
        errors.push("第 " + (i + 1) + " 个 clip 缺少 clip_id");
      } else if (clipIds[clip.clip_id]) {
        errors.push("clip_id 必须唯一，当前重复：" + clip.clip_id);
      } else {
        clipIds[clip.clip_id] = true;
      }
      if (clip.speaker !== "host_a" && clip.speaker !== "host_b") {
        errors.push("第 " + (i + 1) + " 个 clip 的 speaker 必须是 host_a 或 host_b");
      }
      if (!clip.text) {
        errors.push("第 " + (i + 1) + " 个 clip 的 text 不能为空");
      }
      if (clip.audio_path !== null) {
        errors.push("第 " + (i + 1) + " 个 clip 的 audio_path 必须为 null");
      }
    });

    if (!manifest.estimated_duration_sec || manifest.estimated_duration_sec <= 0) {
      errors.push("estimated_duration_sec 必须大于 0");
    }

    // No API key / voice_id leakage
    var manifestStr = JSON.stringify(manifest);
    if (/api[_-]?key/i.test(manifestStr) || /voice[_-]?id/i.test(manifestStr)) {
      errors.push("manifest 中不允许出现 API key 或 voice_id");
    }

    return {
      ok: errors.length === 0,
      warnings: warnings,
      errors: errors,
    };
  }

  // CP26: Show episode audio manifest preview
  function showEpisodeAudioManifest() {
    if (episodeItemList.length === 0) {
      setStatus("请先加入新闻，再生成音频计划", "error");
      return;
    }

    // Build or reuse latest script
    var plan = buildEpisodePlan();
    var planResult = validateEpisodePlan(plan);
    if (!planResult.ok) {
      setStatus("栏目计划有误：" + planResult.errors.join("；"), "error");
      return;
    }

    var script = buildEpisodeScriptFromPlan(plan);
    var scriptResult = validateEpisodeScript(script);
    if (!scriptResult.ok) {
      setStatus("栏目脚本有误：" + scriptResult.errors.join("；"), "error");
      return;
    }

    var manifest = buildEpisodeAudioManifestFromScript(script);
    var manifestResult = validateEpisodeAudioManifest(manifest);

    // CP26: Save latest manifest
    latestEpisodeAudioManifest = manifest;

    // Switch to audio_manifest tab
    tabBtns.forEach(function (b) { b.classList.remove("active"); });
    tabContents.forEach(function (c) { c.classList.remove("active"); });
    var tabBtn = document.querySelector('[data-tab="audio_manifest"]');
    var tabContent = document.getElementById("tab-audio_manifest");
    if (tabBtn) tabBtn.classList.add("active");
    if (tabContent) tabContent.classList.add("active");

    var jsonEl = document.getElementById("json-audio_manifest");
    if (jsonEl) {
      var output = JSON.stringify({ manifest: manifest, validation: manifestResult }, null, 2);
      jsonEl.textContent = output;
    }

    if (!manifestResult.ok) {
      setStatus("音频计划有误：" + manifestResult.errors.join("；"), "error");
    } else if (manifestResult.warnings.length > 0) {
      setStatus("音频计划已生成（" + manifestResult.warnings.join("；") + "）", "info");
    } else {
      setStatus("音频计划已生成", "success");
    }
  }

  // CP27: Build episode render IR from plan/script/audio manifest (mock, no real render)
  function buildEpisodeRenderIrFromContracts(plan, script, audioManifest) {
    if (!plan || !script || !audioManifest) {
      return null;
    }

    var sections = [];
    var segIdx = 0;

    // Opening section
    var openingClip = null;
    if (audioManifest.clips) {
      audioManifest.clips.forEach(function (clip) {
        if (clip.section === "opening") openingClip = clip;
      });
    }
    sections.push({
      section_id: "opening",
      type: "opening",
      start_order: 1,
      duration_hint_sec: openingClip ? openingClip.duration_hint_sec : 12,
      audio_clip_ids: ["opening_001"],
      visual: {
        layout: "title_card",
        title: plan.title || "今日 AI 前沿速览",
        subtitle: plan.subtitle || "多条热门 AI 新闻合集",
      },
    });

    // News segment sections
    var segOrder = 1;
    if (script.segments) {
      script.segments.forEach(function (seg) {
        var isLead = seg.role === "lead";
        var segPrefix = "seg_" + String(segOrder).padStart(3, "0");
        var audioClipIds = [];
        if (audioManifest.clips) {
          audioManifest.clips.forEach(function (clip) {
            if (clip.section === "segment" && clip.segment_order === seg.order) {
              audioClipIds.push(clip.clip_id);
            }
          });
        }
        var durHint = 0;
        if (audioManifest.clips) {
          audioManifest.clips.forEach(function (clip) {
            if (clip.section === "segment" && clip.segment_order === seg.order) {
              durHint += clip.duration_hint_sec || 0;
            }
          });
        }

        // Layout based on theme
        var themeId = plan.theme || "news_card_v1";
        var layout = "news_card_stack";
        if (themeId === "research_desk" || themeId === "research_desk_v2") {
          layout = "research_desk_panel";
        } else if (themeId === "causal_map" || themeId === "causal_map_v1") {
          layout = "causal_chain_panel";
        } else if (themeId === "timeline_brief_v1") {
          layout = "timeline_panel";
        } else if (themeId === "data_dashboard_v1") {
          layout = "dashboard_panel";
        } else if (themeId === "breaking_news_v1") {
          layout = "breaking_news_panel";
        } else if (themeId === "product_launch_v1") {
          layout = "product_launch_panel";
        } else if (themeId === "paper_digest_v1") {
          layout = "paper_digest_panel";
        } else if (themeId === "podcast_cards_v1") {
          layout = "podcast_cards_panel";
        } else if (themeId === "dev_terminal_v1") {
          layout = "terminal_panel";
        } else if (themeId === "magazine_cover_v1") {
          layout = "magazine_cover_panel";
        } else if (themeId === "opinion_column_v1") {
          layout = "opinion_column_panel";
        }

        sections.push({
          section_id: "segment_" + String(segOrder).padStart(3, "0"),
          type: "news_segment",
          news_id: seg.news_id,
          order: seg.order,
          role: seg.role,
          duration_hint_sec: durHint || 32,
          audio_clip_ids: audioClipIds,
          visual: {
            layout: layout,
            headline: seg.headline,
            source: seg.news_id,
            badges: isLead ? ["Lead", "Hot AI"] : ["AI News"],
            emphasis: isLead ? "primary" : "secondary",
          },
        });

        // Transition section after this segment (if not last)
        if (segOrder < script.segments.length) {
          sections.push({
            section_id: "transition_after_" + String(segOrder).padStart(3, "0"),
            type: "transition",
            duration_hint_sec: 4,
            audio_clip_ids: ["transition_after_" + String(segOrder).padStart(3, "0")],
            visual: {
              layout: "simple_transition",
              text: "接着看下一条。",
            },
          });
        }

        segOrder++;
      });
    }

    // Closing section
    sections.push({
      section_id: "closing",
      type: "closing",
      duration_hint_sec: 12,
      audio_clip_ids: ["closing_001"],
      visual: {
        layout: "summary_card",
        focus_news_id: script.closing ? script.closing.focus_news_id : null,
        title: "今天最值得关注的是...",
      },
    });

    var totalDuration = sections.reduce(function (sum, s) {
      return sum + (s.duration_hint_sec || 0);
    }, 0);

    var renderIr = {
      version: "episode_render_ir_v1",
      episode_title: plan.title || "今日 AI 前沿速览",
      theme: plan.theme || "news_card_v1",
      canvas: {
        width: 1280,
        height: 720,
        fps: 30,
        background: "dark_newsroom",
      },
      timeline: {
        estimated_duration_sec: totalDuration,
        sections: sections,
      },
      style: {
        theme_id: plan.theme || "news_card_v1",
        motion: "subtle",
        density: "medium",
      },
      constraints: {
        no_real_render: true,
        no_export: true,
        render_paths_are_placeholders: true,
      },
    };

    return renderIr;
  }

  // CP27: Validate episode render IR
  function validateEpisodeRenderIr(renderIr) {
    var warnings = [];
    var errors = [];

    if (!renderIr) {
      errors.push("renderIr 为空");
      return { ok: false, warnings: warnings, errors: errors };
    }

    if (renderIr.version !== "episode_render_ir_v1") {
      errors.push("version 必须为 episode_render_ir_v1");
    }

    if (!renderIr.canvas || !renderIr.canvas.width || !renderIr.canvas.height || !renderIr.canvas.fps) {
      errors.push("canvas.width/height/fps 必须合法");
    }

    if (!renderIr.timeline || !renderIr.timeline.sections || renderIr.timeline.sections.length < 1) {
      errors.push("至少需要 1 个 section");
    }

    var sectionIds = {};
    var hasOpening = false;
    var hasClosing = false;
    var hasNewsSegment = false;

    renderIr.timeline && renderIr.timeline.sections && renderIr.timeline.sections.forEach(function (sec, i) {
      if (!sec.section_id) {
        errors.push("第 " + (i + 1) + " 个 section 缺少 section_id");
      } else if (sectionIds[sec.section_id]) {
        errors.push("section_id 必须唯一，当前重复：" + sec.section_id);
      } else {
        sectionIds[sec.section_id] = true;
      }

      if (!sec.type) errors.push("第 " + (i + 1) + " 个 section 缺少 type");
      if (!sec.duration_hint_sec || sec.duration_hint_sec <= 0) {
        errors.push("第 " + (i + 1) + " 个 section 的 duration_hint_sec 必须大于 0");
      }
      if (!sec.audio_clip_ids || sec.audio_clip_ids.length === 0) {
        errors.push("第 " + (i + 1) + " 个 section 的 audio_clip_ids 不能为空");
      }
      if (!sec.visual) errors.push("第 " + (i + 1) + " 个 section 缺少 visual");

      if (sec.type === "opening") hasOpening = true;
      if (sec.type === "closing") hasClosing = true;
      if (sec.type === "news_segment") hasNewsSegment = true;
    });

    if (!hasOpening) errors.push("必须包含 opening section");
    if (!hasClosing) errors.push("必须包含 closing section");
    if (!hasNewsSegment) errors.push("必须至少包含 1 个 news_segment section");

    if (!renderIr.constraints || renderIr.constraints.no_real_render !== true) {
      errors.push("constraints.no_real_render 必须为 true");
    }
    if (!renderIr.constraints || renderIr.constraints.no_export !== true) {
      errors.push("constraints.no_export 必须为 true");
    }

    // No API key / voice_id leakage
    var irStr = JSON.stringify(renderIr);
    if (/api[_-]?key/i.test(irStr) || /voice[_-]?id/i.test(irStr)) {
      errors.push("renderIr 中不允许出现 API key 或 voice_id");
    }

    return {
      ok: errors.length === 0,
      warnings: warnings,
      errors: errors,
    };
  }

  // CP27: Show episode render IR preview
  function showEpisodeRenderIr() {
    if (episodeItemList.length === 0) {
      setStatus("请先加入新闻，再生成视觉计划", "error");
      return;
    }

    var plan = buildEpisodePlan();
    var planResult = validateEpisodePlan(plan);
    if (!planResult.ok) {
      setStatus("栏目计划有误：" + planResult.errors.join("；"), "error");
      return;
    }

    var script = buildEpisodeScriptFromPlan(plan);
    var scriptResult = validateEpisodeScript(script);
    if (!scriptResult.ok) {
      setStatus("栏目脚本有误：" + scriptResult.errors.join("；"), "error");
      return;
    }

    var manifest = buildEpisodeAudioManifestFromScript(script);
    var manifestResult = validateEpisodeAudioManifest(manifest);
    if (!manifestResult.ok) {
      setStatus("音频计划有误：" + manifestResult.errors.join("；"), "error");
      return;
    }

    var renderIr = buildEpisodeRenderIrFromContracts(plan, script, manifest);
    var renderIrResult = validateEpisodeRenderIr(renderIr);

    // CP27: Save latest render IR
    latestEpisodeRenderIr = renderIr;

    // Switch to visual_plan tab
    tabBtns.forEach(function (b) { b.classList.remove("active"); });
    tabContents.forEach(function (c) { c.classList.remove("active"); });
    var tabBtn = document.querySelector('[data-tab="visual_plan"]');
    var tabContent = document.getElementById("tab-visual_plan");
    if (tabBtn) tabBtn.classList.add("active");
    if (tabContent) tabContent.classList.add("active");

    var jsonEl = document.getElementById("json-visual_plan");
    if (jsonEl) {
      var output = JSON.stringify({ render_ir: renderIr, validation: renderIrResult }, null, 2);
      jsonEl.textContent = output;
    }

    if (!renderIrResult.ok) {
      setStatus("视觉计划有误：" + renderIrResult.errors.join("；"), "error");
    } else if (renderIrResult.warnings.length > 0) {
      setStatus("视觉计划已生成（" + renderIrResult.warnings.join("；") + "）", "info");
    } else {
      setStatus("视觉计划已生成", "success");
    }
  }

  // CP34: Format seconds to MM:SS timecode string
  function formatTimecode(seconds) {
    var m = Math.floor(seconds / 60);
    var s = seconds % 60;
    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
  }

  // CP34: Build episode template contract from renderIr — episode_template_v1
  function buildEpisodeTemplateContract(renderIr) {
    if (!renderIr) return null;

    var sections = renderIr.timeline && renderIr.timeline.sections ? renderIr.timeline.sections : [];
    var newsSegs = sections.filter(function (s) { return s.type === "news_segment"; });
    var transitions = sections.filter(function (s) { return s.type === "transition"; });
    var openingSec = sections.find(function (s) { return s.type === "opening"; });
    var closingSec = sections.find(function (s) { return s.type === "closing"; });
    var totalDuration = renderIr.timeline && renderIr.timeline.estimated_duration_sec ? renderIr.timeline.estimated_duration_sec : 0;

    var themeName = (THEME_SHOWCASES[renderIr.theme] && THEME_SHOWCASES[renderIr.theme].name) ? THEME_SHOWCASES[renderIr.theme].name : (renderIr.theme || "");
    var leadCount = newsSegs.filter(function (s) { return s.role === "lead"; }).length || 1;

    // CP34.1: Shared helper — get transition duration after a given segment index
    // Used by both timeline markers and news card time_range so they stay consistent
    function getTransitionDurationAfterIndex(index) {
      var trans = transitions[index];
      return trans && trans.duration_hint_sec ? trans.duration_hint_sec : 4;
    }

    // Build timeline markers
    var markers = [];
    var cursor = 0;

    // Opening marker
    var openingDur = openingSec ? (openingSec.duration_hint_sec || 12) : 12;
    markers.push({
      type: "opening",
      label: "开场",
      timecode: formatTimecode(cursor),
      role: null,
      section_id: openingSec ? openingSec.section_id : null
    });
    cursor += openingDur;

    // Per-segment markers + transitions
    newsSegs.forEach(function (seg, i) {
      var segDur = seg.duration_hint_sec || 32;
      var isLead = seg.role === "lead";
      markers.push({
        type: "news_segment",
        label: (isLead ? "主线 " : "补充 ") + (i + 1),
        timecode: formatTimecode(cursor),
        role: seg.role,
        section_id: seg.section_id
      });
      cursor += segDur;

      if (i < newsSegs.length - 1) {
        var transDur = getTransitionDurationAfterIndex(i);
        var trans = transitions[i];
        markers.push({
          type: "transition",
          label: "转场",
          timecode: formatTimecode(cursor),
          role: null,
          section_id: trans ? trans.section_id : null
        });
        cursor += transDur;
      }
    });

    // Closing marker
    var closingDur = closingSec ? (closingSec.duration_hint_sec || 12) : 12;
    markers.push({
      type: "closing",
      label: "结尾",
      timecode: formatTimecode(cursor),
      role: null,
      section_id: closingSec ? closingSec.section_id : null
    });

    // Build news cards data
    var newsCards = [];
    newsSegs.forEach(function (seg, index) {
      var isLead = seg.role === "lead";
      var badges = seg.visual && seg.visual.badges ? seg.visual.badges : [];
      var durHint = seg.duration_hint_sec || 32;
      var roleLabel = isLead ? "主线" : "补充";

      // Calculate pseudo time range — uses same transition duration logic as markers
      var cardCursor = 0;
      cardCursor += openingSec ? (openingSec.duration_hint_sec || 12) : 12;
      for (var j = 0; j < index; j++) {
        cardCursor += newsSegs[j].duration_hint_sec || 32;
        if (j < newsSegs.length - 1) cardCursor += getTransitionDurationAfterIndex(j);
      }
      var startOffset = cardCursor;
      var endOffset = startOffset + durHint;
      var timeRange = formatTimecode(startOffset) + " – " + formatTimecode(endOffset);

      newsCards.push({
        section_id: seg.section_id,
        order: index + 1,
        role: seg.role,
        headline: seg.visual && seg.visual.headline ? seg.visual.headline : "",
        layout: seg.visual && seg.visual.layout ? seg.visual.layout : "",
        emphasis: seg.visual && seg.visual.emphasis ? seg.visual.emphasis : "",
        badges: badges,
        audio_clip_count: seg.audio_clip_ids ? seg.audio_clip_ids.length : 0,
        duration_hint_sec: durHint,
        time_range: timeRange,
        is_lead: isLead,
        section_type: "news_segment"
      });
    });

    // Build transitions data
    var transitionRows = [];
    newsSegs.forEach(function (seg, index) {
      var segOrder = seg.order || (index + 1);
      var trans = transitions.find(function (t) {
        return t.type === "transition" && t.section_id && t.section_id.includes(String(segOrder).padStart(3, "0"));
      });
      var transText = (trans && trans.visual && trans.visual.text) ? trans.visual.text : "接着看下一条";
      transitionRows.push({
        after_order: index + 1,
        text: transText
      });
    });

    return {
      schema_version: "episode_template_v1",
      template_id: currentEpisodePreviewStyle,
      episode: {
        title: renderIr.episode_title || "今日 AI 前沿速览",
        subtitle: renderIr.subtitle || "多条热门 AI 新闻合集",
        theme_id: renderIr.theme || "",
        theme_name: themeName,
        estimated_duration_sec: totalDuration,
        news_count: newsSegs.length,
        lead_count: leadCount
      },
      timeline: {
        markers: markers
      },
      sections: {
        opening: {
          title: openingSec && openingSec.visual && openingSec.visual.title ? openingSec.visual.title : "今日 AI 前沿速览",
          subtitle: renderIr.subtitle || "多条热门 AI 新闻合集",
          duration_hint_sec: openingSec ? (openingSec.duration_hint_sec || 12) : 12
        },
        news_cards: newsCards,
        transitions: transitionRows,
        closing: {
          title: closingSec && closingSec.visual ? (closingSec.visual.title || "今天最值得关注的是...") : "今天最值得关注的是...",
          focus_news_id: closingSec && closingSec.visual && closingSec.visual.focus_news_id ? closingSec.visual.focus_news_id : null
        }
      },
      constraints: {
        no_external_assets: true,
        no_script: true,
        no_real_render: true,
        no_audio: true,
        no_mp4: true
      }
    };
  }

  // CP34: Validate episode template contract
  function validateEpisodeTemplateContract(contract) {
    var warnings = [];
    var errors = [];

    if (!contract || typeof contract !== "object") {
      errors.push("Contract 必须是一个对象");
      return { ok: false, warnings: warnings, errors: errors };
    }

    if (contract.schema_version !== "episode_template_v1") {
      errors.push('Contract schema_version 必须为 "episode_template_v1"');
    }

    var validTemplateIds = [
      "timeline_daily_v1",
      "breaking_news_v1",
      "data_dashboard_v1",
      "research_briefing_v1",
      "podcast_cards_v1"
    ];
    if (validTemplateIds.indexOf(contract.template_id) === -1) {
      errors.push('Contract template_id 必须是以下之一: ' + validTemplateIds.join(", "));
    }

    if (!contract.episode || !contract.episode.title) {
      errors.push("Contract episode.title 必填");
    }

    if (!contract.timeline || !Array.isArray(contract.timeline.markers) || contract.timeline.markers.length === 0) {
      errors.push("Contract timeline.markers 非空数组必填");
    }

    if (!contract.sections || !Array.isArray(contract.sections.news_cards) || contract.sections.news_cards.length === 0) {
      errors.push("Contract sections.news_cards 非空数组必填");
    }

    // Check each news_card has required fields
    if (contract.sections && Array.isArray(contract.sections.news_cards)) {
      contract.sections.news_cards.forEach(function (card, i) {
        if (!card.section_id) errors.push("news_card[" + i + "] section_id 必填");
        if (!card.headline) errors.push("news_card[" + i + "] headline 必填");
        if (!card.time_range) errors.push("news_card[" + i + "] time_range 必填");
      });
    }

    // Check constraints
    if (!contract.constraints) {
      errors.push("Contract constraints 必填");
    } else {
      if (contract.constraints.no_external_assets !== true) errors.push("constraints.no_external_assets 必须为 true");
      if (contract.constraints.no_script !== true) errors.push("constraints.no_script 必须为 true");
      if (contract.constraints.no_audio !== true) errors.push("constraints.no_audio 必须为 true");
      if (contract.constraints.no_mp4 !== true) errors.push("constraints.no_mp4 必须为 true");
    }

    // Security: no API key / voice_id in JSON
    var contractStr = JSON.stringify(contract);
    if (/api[_-]?key/i.test(contractStr)) {
      errors.push("Contract 中不允许出现 API key");
    }
    if (/voice[_-]?id/i.test(contractStr)) {
      errors.push("Contract 中不允许出现 voice_id");
    }

    return { ok: errors.length === 0, warnings: warnings, errors: errors };
  }

  // CP35: Episode style theme configuration
  function getEpisodeStyleTheme(templateId) {
    var t = {
      bodyBg: "#0f172a",
      heroBg: "linear-gradient(135deg,#0f172a 0%,#1e293b 100%)",
      heroBorder: "#1e3a5f",
      cardBg: "#111827",
      cardBgLead: "#1a1a2e",
      cardBorder: "#2d3748",
      cardBorderLead: "#f59e0b",
      accentBlue: "#38bdf8",
      accentAmber: "#f59e0b",
      accentGreen: "#4ade80",
      accentText: "#94a3b8",
      metaText: "#475569",
      dotOpening: "#38bdf8",
      dotLead: "#f59e0b",
      dotSupport: "#334155",
      dotTrans: "#334155",
      dotClosing: "#4ade80",
      statColor: "#38bdf8",
      badgeBg: "#f59e0b",
      badgeColor: "#0f172a",
      sectionDivider: "#1e293b",
      cardLayoutTagColor: "#38bdf8",
      cardEmphasisColor: "#fbbf24",
      cardBadgeBg: "#1e293b",
      footerBg: "#0f172a",
      footerText: "#475569",
      heroGridOpacity: "0.3",
      headlineGradient: "linear-gradient(90deg,#f9fafb,#94a3b8)",
      openingBg: "linear-gradient(135deg,#1e293b,#0f172a)",
      closingBg: "linear-gradient(135deg,#1e293b,#0f172a)",
      closingBadgeBg: "#4ade80",
      closingBadgeColor: "#0f172a",
      podcastTransitionBg: "#2d1a0a"
    };

    if (templateId === "breaking_news_v1") {
      t.bodyBg = "#0a0000";
      t.heroBg = "linear-gradient(135deg,#1a0000 0%,#2d0000 100%)";
      t.heroBorder = "#4a0000";
      t.cardBg = "#1a0000";
      t.cardBgLead = "#2a0000";
      t.cardBorder = "#3a0000";
      t.cardBorderLead = "#dc2626";
      t.dotOpening = "#dc2626";
      t.dotLead = "#dc2626";
      t.dotClosing = "#dc2626";
      t.statColor = "#dc2626";
      t.badgeBg = "#dc2626";
      t.heroGridOpacity = "0.1";
      t.openingBg = "linear-gradient(135deg,#2d0000,#1a0000)";
      t.closingBg = "linear-gradient(135deg,#2d0000,#1a0000)";
      t.closingBadgeBg = "#dc2626";
    } else if (templateId === "data_dashboard_v1") {
      t.bodyBg = "#0a0f1a";
      t.heroBg = "linear-gradient(135deg,#0a0f1a 0%,#0f172a 100%)";
      t.heroBorder = "#164e63";
      t.cardBg = "#0f172a";
      t.cardBgLead = "#0c1a24";
      t.cardBorder = "#164e63";
      t.cardBorderLead = "#06b6d4";
      t.accentBlue = "#06b6d4";
      t.dotOpening = "#06b6d4";
      t.dotLead = "#06b6d4";
      t.dotClosing = "#06b6d4";
      t.statColor = "#06b6d4";
      t.badgeBg = "#06b6d4";
      t.cardLayoutTagColor = "#06b6d4";
      t.sectionDivider = "#164e63";
      t.heroGridOpacity = "0.15";
      t.openingBg = "linear-gradient(135deg,#0f172a,#0a0f1a)";
      t.closingBg = "linear-gradient(135deg,#0f172a,#0a0f1a)";
      t.closingBadgeBg = "#06b6d4";
    } else if (templateId === "research_briefing_v1") {
      t.bodyBg = "#0d1117";
      t.heroBg = "linear-gradient(135deg,#0d1117 0%,#161b22 100%)";
      t.heroBorder = "#30363d";
      t.cardBg = "#161b22";
      t.cardBgLead = "#1c2128";
      t.cardBorder = "#30363d";
      t.cardBorderLead = "#c9d1d9";
      t.accentBlue = "#c9d1d9";
      t.accentAmber = "#c9d1d9";
      t.accentGreen = "#c9d1d9";
      t.accentText = "#8b949e";
      t.metaText = "#8b949e";
      t.dotOpening = "#c9d1d9";
      t.dotLead = "#c9d1d9";
      t.dotSupport = "#30363d";
      t.dotClosing = "#c9d1d9";
      t.statColor = "#c9d1d9";
      t.badgeBg = "#30363d";
      t.badgeColor = "#c9d1d9";
      t.sectionDivider = "#30363d";
      t.cardLayoutTagColor = "#c9d1d9";
      t.cardEmphasisColor = "#c9d1d9";
      t.cardBadgeBg = "#21262d";
      t.heroGridOpacity = "0.2";
      t.headlineGradient = "none";
      t.openingBg = "linear-gradient(135deg,#161b22,#0d1117)";
      t.closingBg = "linear-gradient(135deg,#161b22,#0d1117)";
      t.closingBadgeBg = "#c9d1d9";
      t.closingBadgeColor = "#0d1117";
      t.footerBg = "#0d1117";
    } else if (templateId === "podcast_cards_v1") {
      t.bodyBg = "#1a1209";
      t.heroBg = "linear-gradient(135deg,#1a1209 0%,#231810 100%)";
      t.heroBorder = "#78350f";
      t.cardBg = "#231810";
      t.cardBgLead = "#2d1a0a";
      t.cardBorder = "#78350f";
      t.cardBorderLead = "#f59e0b";
      t.dotOpening = "#f59e0b";
      t.dotLead = "#f59e0b";
      t.dotClosing = "#f59e0b";
      t.statColor = "#f59e0b";
      t.badgeBg = "#f59e0b";
      t.heroGridOpacity = "0.15";
      t.openingBg = "linear-gradient(135deg,#231810,#1a1209)";
      t.closingBg = "linear-gradient(135deg,#231810,#1a1209)";
      t.closingBadgeBg = "#f59e0b";
    }

    return t;
  }

  // CP35.1: Dispatch to per-style layout renderer
  function renderEpisodeTemplateHtml(contract) {
    if (!contract) return "";
    var templateId = contract.template_id || "timeline_daily_v1";
    var st = getEpisodeStyleTheme(templateId);
    if (templateId === "breaking_news_v1") return renderBreakingNewsEpisodeHtml(contract, st);
    if (templateId === "data_dashboard_v1") return renderDataDashboardEpisodeHtml(contract, st);
    if (templateId === "research_briefing_v1") return renderResearchBriefingEpisodeHtml(contract, st);
    if (templateId === "podcast_cards_v1") return renderPodcastCardsEpisodeHtml(contract, st);
    return renderTimelineDailyEpisodeHtml(contract, st);
  }

  // CP35.1: Shared helpers used by all layout renderers
  function renderSharedTimelineMarkersHtml(timeline, st) {
    if (!timeline || !timeline.markers) return "";
    var htmlParts = [];
    timeline.markers.forEach(function (marker) {
      var dotClass = "tl-dot";
      if (marker.type === "opening") dotClass = "tl-dot tl-dot-opening";
      else if (marker.type === "news_segment") dotClass = "tl-dot " + (marker.role === "lead" ? "tl-dot-lead" : "tl-dot-supporting");
      else if (marker.type === "transition") dotClass = "tl-dot tl-dot-trans";
      else if (marker.type === "closing") dotClass = "tl-dot tl-dot-closing";
      htmlParts.push('<div class="tl-marker">' +
        '<div class="' + dotClass + '"></div>' +
        '<div class="tl-label"><span class="tl-time">' + marker.timecode + '</span><span class="tl-name">' + escapeHtml(marker.label) + '</span></div>' +
        '</div>');
    });
    return htmlParts.join("");
  }

  function getSharedCss(st) {
    return '<style>\n' +
      '*{margin:0;padding:0;box-sizing:border-box}\n' +
      'body{background:' + st.bodyBg + ';color:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;' +
      'display:flex;flex-direction:column;min-height:100vh;padding:0}\n' +
      '.hero{background:' + st.heroBg + ';padding:32px 40px;border-bottom:1px solid ' + st.heroBorder + ';position:relative;overflow:hidden;}\n' +
      '.hero::before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:repeating-linear-gradient(90deg,transparent,transparent 40px,' + st.heroBorder + ' 40px,' + st.heroBorder + ' 41px);opacity:' + st.heroGridOpacity + ';pointer-events:none;}\n' +
      '.hero-content{position:relative;z-index:1;}\n' +
      '.hero-eyebrow{display:flex;gap:12px;align-items:center;margin-bottom:12px;}\n' +
      '.hero-badge{background:' + st.badgeBg + ';color:' + st.badgeColor + ';padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:0.5px;}\n' +
      '.hero-theme{color:' + st.accentBlue + ';font-size:12px;background:' + st.heroBorder + ';padding:3px 10px;border-radius:20px;}\n' +
      '.hero-badge-dur{color:' + st.metaText + ';font-size:12px;}\n' +
      '.hero h1{font-size:28px;font-weight:800;margin-bottom:8px;}\n' +
      '.hero-subtitle{color:' + st.accentText + ';font-size:14px;margin-bottom:16px;}\n' +
      '.hero-stats{display:flex;gap:20px;}\n' +
      '.hero-stat{text-align:center;}\n' +
      '.hero-stat-num{font-size:20px;font-weight:700;color:' + st.statColor + ';}\n' +
      '.hero-stat-label{font-size:11px;color:' + st.metaText + ';}\n' +
      '.tl-rail{background:' + st.bodyBg + ';padding:16px 40px;border-bottom:1px solid ' + st.heroBorder + ';overflow-x:auto;}\n' +
      '.tl-track{display:flex;align-items:center;gap:0;min-width:600px;position:relative;padding:8px 0;}\n' +
      '.tl-track::before{content:"";position:absolute;left:0;right:0;top:50%;height:2px;background:' + st.heroBorder + ';transform:translateY(-50%);z-index:0;}\n' +
      '.tl-marker{display:flex;flex-direction:column;align-items:center;position:relative;z-index:1;flex:1;min-width:60px;}\n' +
      '.tl-dot{width:12px;height:12px;border-radius:50%;border:2px solid ' + st.dotSupport + ';background:' + st.bodyBg + ';position:relative;}\n' +
      '.tl-dot-opening{background:' + st.dotOpening + ';border-color:' + st.dotOpening + ';animation:pulseLine 2s infinite;}\n' +
      '.tl-dot-lead{background:' + st.dotLead + ';border-color:' + st.dotLead + ';box-shadow:0 0 8px ' + st.dotLead + '80;}\n' +
      '.tl-dot-supporting{background:' + st.dotSupport + ';border-color:' + st.dotSupport + ';}\n' +
      '.tl-dot-trans{background:' + st.dotTrans + ';border-color:' + st.dotTrans + ';width:8px;height:8px;}\n' +
      '.tl-dot-closing{background:' + st.dotClosing + ';border-color:' + st.dotClosing + ';animation:pulseLine 2s infinite;}\n' +
      '.tl-label{text-align:center;margin-top:4px;}\n' +
      '.tl-time{color:' + st.metaText + ';font-size:10px;font-family:monospace;display:block;}\n' +
      '.tl-name{color:' + st.accentText + ';font-size:10px;display:block;white-space:nowrap;}\n' +
      '.tl-marker-trans .tl-name{color:' + st.metaText + ';}\n' +
      '.content{padding:24px 40px;flex:1;max-width:900px;margin:0 auto;width:100%;}\n' +
      '.section-label{color:' + st.metaText + ';font-size:11px;text-transform:uppercase;letter-spacing:1.5px;margin:20px 0 8px 0;display:flex;align-items:center;gap:10px;}\n' +
      '.section-label::after{content:"";flex:1;height:1px;background:' + st.sectionDivider + ';}\n' +
      '.mock-news-card-lead{border-left:3px solid ' + st.cardBorderLead + '!important;}\n' +
      '.card-lead-badge{background:' + st.badgeBg + ';color:' + st.badgeColor + ';padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;margin-left:6px;}\n' +
      '.footer-bar{background:' + st.footerBg + ';padding:12px 40px;border-top:1px solid ' + st.heroBorder + ';font-size:11px;color:' + st.footerText + ';display:flex;justify-content:space-between;align-items:center;}\n' +
      '@keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}\n' +
      '@keyframes pulseLine{0%,100%{opacity:1;}50%{opacity:0.5;}}\n' +
      '@keyframes shimmer{0%{background-position:-200% 0;}100%{background-position:200% 0;}}\n' +
      '</style>\n';
  }

  // CP35.1: Layout 1 — timeline_daily_v1 (standard vertical news cards — the baseline)
  function renderTimelineDailyEpisodeHtml(contract, st) {
    var episode = contract.episode;
    var timeline = contract.timeline;
    var sections = contract.sections;
    var totalTimeStr = formatTimecode(episode.estimated_duration_sec);
    var themeName = episode.theme_name || "";
    var hlStyle = st.headlineGradient !== "none"
      ? 'background:' + st.headlineGradient + ';-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'
      : 'color:#f9fafb;';

    function cardHtml(card) {
      var isLead = card.is_lead;
      var bc = isLead ? st.cardBorderLead : st.cardBorder;
      var bg = isLead ? st.cardBgLead : st.cardBg;
      var leadBadge = isLead ? '<span class="card-lead-badge">★ 主线</span>' : '';
      var empTag = card.emphasis ? '<span style="color:' + st.cardEmphasisColor + ';font-size:11px;background:' + st.cardBadgeBg + ';padding:2px 6px;border-radius:3px;">' + escapeHtml(card.emphasis) + '</span>' : '';
      var badges = card.badges.map(function (b) { return '<span class="card-badge">' + escapeHtml(b) + '</span>'; }).join("");
      return '<div class="mock-news-card' + (isLead ? ' mock-news-card-lead' : '') + '" data-section-type="news_segment" style="background:' + bg + ';border:1px solid ' + bc + ';border-radius:12px;padding:20px;margin:10px 0;animation:fadeUp 0.4s ease-out both;">' +
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">' +
        '<span style="background:' + st.cardBadgeBg + ';color:' + st.metaText + ';border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700;">#' + card.order + '</span>' +
        '<span style="color:' + st.metaText + ';font-size:11px;font-family:monospace;">' + card.time_range + '</span>' +
        '<span style="color:' + st.metaText + ';font-size:11px;">' + card.duration_hint_sec + 's</span>' + leadBadge + '</div>' +
        '<div style="color:#f9fafb;font-size:16px;font-weight:600;margin-bottom:8px;line-height:1.4;' + hlStyle + '">' + escapeHtml(card.headline) + '</div>' +
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">' +
        '<span style="color:' + st.cardLayoutTagColor + ';font-size:11px;background:' + st.cardBadgeBg + ';padding:2px 6px;border-radius:3px;">' + escapeHtml(card.layout) + '</span>' + empTag + badges + '</div>' +
        '<div style="color:' + st.metaText + ';font-size:11px;margin-top:8px;">🎙 ' + card.audio_clip_count + ' 片段 &nbsp;📋 ' + (isLead ? '主线' : '补充') + '</div></div>';
    }

    function transHtml(row) {
      return '<div style="display:flex;align-items:center;gap:12px;padding:8px 16px;margin:4px 0;color:' + st.metaText + ';font-size:12px;">' +
        '<span style="flex:1;height:1px;background:' + st.sectionDivider + ';"></span>' +
        '<span style="white-space:nowrap;">→ ' + escapeHtml(row.text) + ' →</span>' +
        '<span style="flex:1;height:1px;background:' + st.sectionDivider + ';"></span></div>';
    }

    var cards = [];
    sections.news_cards.forEach(function (card, i) {
      cards.push(cardHtml(card));
      if (i < sections.news_cards.length - 1 && sections.transitions && sections.transitions[i]) {
        cards.push(transHtml(sections.transitions[i]));
      }
    });

    return '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>' + escapeHtml(episode.title) + '</title>\n' + getSharedCss(st) + '</head>\n<body>\n' +
      '<div class="hero">\n<div class="hero-content">' +
      '<div class="hero-eyebrow"><span class="hero-badge">🔥 合集</span><span class="hero-theme">' + escapeHtml(themeName) + '</span><span class="hero-badge-dur">⏱ ' + totalTimeStr + '</span></div>' +
      '<h1 style="' + hlStyle + '">' + escapeHtml(episode.title) + '</h1>' +
      '<div class="hero-subtitle">' + escapeHtml(episode.subtitle) + '</div>' +
      '<div class="hero-stats"><div class="hero-stat"><div class="hero-stat-num">' + sections.news_cards.length + '</div><div class="hero-stat-label">条新闻</div></div>' +
      '<div class="hero-stat"><div class="hero-stat-num">' + totalTimeStr + '</div><div class="hero-stat-label">总时长</div></div>' +
      '<div class="hero-stat"><div class="hero-stat-num">' + episode.lead_count + '</div><div class="hero-stat-label">主线</div></div></div></div>\n</div>\n' +
      '<div class="tl-rail"><div class="tl-track">' + renderSharedTimelineMarkersHtml(timeline, st) + '</div></div>\n' +
      '<div class="content">' +
      '<div class="section-label">开场</div>' +
      '<div style="background:' + st.openingBg + ';border-radius:12px;padding:20px;margin-bottom:8px;border:1px solid ' + st.heroBorder + ';">' +
      '<div style="font-size:15px;color:#e2e8f0;font-weight:600;margin-bottom:4px;">' + escapeHtml(sections.opening.title) + '</div>' +
      '<div style="color:' + st.metaText + ';font-size:12px;">' + escapeHtml(sections.opening.subtitle) + '</div></div>\n' +
      '<div class="section-label">新闻列表</div>\n' + cards.join("") +
      '<div class="section-label">结尾</div>' +
      '<div style="background:' + st.closingBg + ';border-radius:12px;padding:20px;border:1px solid ' + st.heroBorder + ';">' +
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><span style="background:' + st.closingBadgeBg + ';color:' + st.closingBadgeColor + ';padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">重点回看</span></div>' +
      '<div style="color:#f9fafb;font-size:14px;font-weight:600;margin-bottom:4px;">' + escapeHtml(sections.closing.title) + '</div>' +
      (sections.closing.focus_news_id ? '<div style="color:' + st.metaText + ';font-size:11px;">📋 主线新闻 ID: ' + escapeHtml(sections.closing.focus_news_id) + '</div>' : '') + '</div>\n' +
      '</div>\n<div class="footer-bar"><span>Mock Timeline Preview · ' + escapeHtml(themeName) + ' · no real render</span><span>' + escapeHtml(episode.title) + '</span></div>\n</body>\n</html>';
  }

  // CP35.1: Layout 2 — breaking_news_v1 (news channel big-screen: big lead card + compact supporting grid)
  function renderBreakingNewsEpisodeHtml(contract, st) {
    var episode = contract.episode;
    var timeline = contract.timeline;
    var sections = contract.sections;
    var totalTimeStr = formatTimecode(episode.estimated_duration_sec);
    var themeName = episode.theme_name || "";

    var leadCard = null;
    var supportCards = [];
    sections.news_cards.forEach(function (card) {
      if (card.is_lead && !leadCard) leadCard = card;
      else supportCards.push(card);
    });
    if (!leadCard && sections.news_cards.length > 0) {
      leadCard = sections.news_cards[0];
      supportCards = sections.news_cards.slice(1);
    }

    function supportCardHtml(card, idx) {
      return '<div class="mock-news-card" data-section-type="news_segment" style="background:' + st.cardBg + ';border:1px solid ' + st.cardBorder + ';border-radius:8px;padding:14px;margin:6px 0;">' +
        '<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">' +
        '<span style="background:' + st.cardBorder + ';color:' + st.metaText + ';border-radius:3px;padding:1px 6px;font-size:10px;font-weight:700;">#' + card.order + '</span>' +
        '<span style="color:' + st.metaText + ';font-size:10px;font-family:monospace;">' + card.time_range + '</span></div>' +
        '<div style="color:#f9fafb;font-size:13px;font-weight:600;line-height:1.3;">' + escapeHtml(card.headline) + '</div>' +
        '<div style="display:flex;gap:4px;margin-top:6px;flex-wrap:wrap;">' +
        '<span style="color:' + st.cardLayoutTagColor + ';font-size:10px;background:' + st.cardBadgeBg + ';padding:1px 5px;border-radius:3px;">' + escapeHtml(card.layout) + '</span></div></div>';
    }

    function breakingTransHtml(row) {
      var texts = ["继续关注", "最新进展", "下一条快讯", "更多详情"];
      var t = row && row.text ? row.text : texts[Math.floor(Math.random() * texts.length)];
      return '<div style="text-align:center;padding:6px 0;color:' + st.metaText + ';font-size:11px;font-weight:600;letter-spacing:1px;">— ' + escapeHtml(t) + ' —</div>';
    }

    var leadHtml = "";
    if (leadCard) {
      leadHtml = '<div style="background:' + st.cardBgLead + ';border:2px solid ' + st.cardBorderLead + ';border-radius:12px;padding:24px;margin:16px 0;animation:fadeUp 0.4s ease-out both;">' +
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">' +
        '<span style="background:' + st.badgeBg + ';color:' + st.badgeColor + ';padding:3px 10px;border-radius:4px;font-size:11px;font-weight:900;letter-spacing:1px;">★ 主线</span>' +
        '<span style="color:' + st.metaText + ';font-size:11px;font-family:monospace;">' + leadCard.time_range + '</span>' +
        '<span style="color:' + st.metaText + ';font-size:11px;">' + leadCard.duration_hint_sec + 's</span></div>' +
        '<div style="color:#f9fafb;font-size:22px;font-weight:900;line-height:1.3;margin-bottom:12px;">' + escapeHtml(leadCard.headline) + '</div>' +
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">' +
        '<span style="color:' + st.cardLayoutTagColor + ';font-size:11px;background:' + st.cardBadgeBg + ';padding:2px 8px;border-radius:4px;">' + escapeHtml(leadCard.layout) + '</span>' +
        (leadCard.emphasis ? '<span style="color:' + st.cardEmphasisColor + ';font-size:11px;background:' + st.cardBadgeBg + ';padding:2px 8px;border-radius:4px;">' + escapeHtml(leadCard.emphasis) + '</span>' : '') + '</div>' +
        '<div style="color:' + st.metaText + ';font-size:11px;">🎙 ' + leadCard.audio_clip_count + ' 音频片段</div></div>';
    }

    var supportGridHtml = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;">';
    supportCards.forEach(function (card) {
      supportGridHtml += supportCardHtml(card);
    });
    if (supportCards.length === 0) supportGridHtml = "";
    else if (supportCards.length === 1) supportGridHtml = supportGridHtml.replace('grid-template-columns:1fr 1fr;', 'grid-template-columns:1fr;');

    return '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>' + escapeHtml(episode.title) + '</title>\n' + getSharedCss(st) + '</head>\n<body>\n' +
      '<div style="background:' + st.breakingBannerBg + ';color:#ffffff;text-align:center;padding:10px;font-size:16px;font-weight:900;letter-spacing:3px;">🔴 BREAKING NEWS — ' + escapeHtml(episode.title) + '</div>\n' +
      '<div class="hero">\n<div class="hero-content">' +
      '<div class="hero-eyebrow"><span class="hero-badge">🔥 合集</span><span class="hero-theme">' + escapeHtml(themeName) + '</span><span class="hero-badge-dur">⏱ ' + totalTimeStr + '</span></div>' +
      '<h1 style="color:#ffffff;">' + escapeHtml(episode.title) + '</h1>' +
      '<div class="hero-subtitle">' + escapeHtml(episode.subtitle) + '</div>' +
      '<div class="hero-stats"><div class="hero-stat"><div class="hero-stat-num">' + sections.news_cards.length + '</div><div class="hero-stat-label">条新闻</div></div>' +
      '<div class="hero-stat"><div class="hero-stat-num">' + totalTimeStr + '</div><div class="hero-stat-label">总时长</div></div>' +
      '<div class="hero-stat"><div class="hero-stat-num">' + episode.lead_count + '</div><div class="hero-stat-label">主线</div></div></div></div>\n</div>\n' +
      '<div class="tl-rail"><div class="tl-track">' + renderSharedTimelineMarkersHtml(timeline, st) + '</div></div>\n' +
      '<div class="content">' +
      '<div class="section-label">头条</div>' + leadHtml +
      (supportCards.length > 0 ? '<div class="section-label">其他快讯</div>' + supportGridHtml + '</div>' : '') +
      '<div class="section-label">重点回看</div>' +
      '<div style="background:' + st.closingBg + ';border-radius:12px;padding:20px;border:1px solid ' + st.heroBorder + ';">' +
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><span style="background:' + st.closingBadgeBg + ';color:' + st.closingBadgeColor + ';padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">重点回看</span></div>' +
      '<div style="color:#f9fafb;font-size:14px;font-weight:600;margin-bottom:4px;">' + escapeHtml(sections.closing.title) + '</div>' +
      (sections.closing.focus_news_id ? '<div style="color:' + st.metaText + ';font-size:11px;">📋 主线新闻 ID: ' + escapeHtml(sections.closing.focus_news_id) + '</div>' : '') + '</div>\n' +
      '</div>\n<div class="footer-bar"><span>Mock Timeline Preview · ' + escapeHtml(themeName) + ' · no real render</span><span>' + escapeHtml(episode.title) + '</span></div>\n</body>\n</html>';
  }

  // CP35.1: Layout 3 — data_dashboard_v1 (monitoring dashboard with metric panels and 2-col grid)
  function renderDataDashboardEpisodeHtml(contract, st) {
    var episode = contract.episode;
    var timeline = contract.timeline;
    var sections = contract.sections;
    var totalTimeStr = formatTimecode(episode.estimated_duration_sec);
    var themeName = episode.theme_name || "";
    var totalAudio = sections.news_cards.reduce(function (s, c) { return s + (c.audio_clip_count || 0); }, 0);

    function metricChip(label, value, unit) {
      return '<div style="background:' + st.cardBg + ';border:1px solid ' + st.cardBorder + ';border-radius:8px;padding:16px;text-align:center;flex:1;">' +
        '<div style="font-size:22px;font-weight:900;color:' + st.statColor + ';font-family:monospace;">' + value + '</div>' +
        '<div style="font-size:11px;color:' + st.metaText + ';margin-top:4px;">' + label + (unit ? ' (' + unit + ')' : '') + '</div></div>';
    }

    function dashCardHtml(card) {
      var isLead = card.is_lead;
      var bc = isLead ? st.cardBorderLead : st.cardBorder;
      var bg = isLead ? st.cardBgLead : st.cardBg;
      return '<div class="mock-news-card' + (isLead ? ' mock-news-card-lead' : '') + '" data-section-type="news_segment" style="background:' + bg + ';border:1px solid ' + bc + ';border-radius:8px;padding:16px;margin:6px 0;animation:fadeUp 0.4s ease-out both;">' +
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">' +
        '<div style="display:flex;align-items:center;gap:6px;">' +
        '<span style="background:' + st.statColor + ';color:' + st.bodyBg + ';border-radius:4px;padding:2px 8px;font-size:11px;font-weight:900;">#' + card.order + '</span>' +
        '<span style="color:' + st.metaText + ';font-size:10px;font-family:monospace;">' + card.time_range + '</span></div>' +
        '<span style="color:' + st.metaText + ';font-size:10px;">' + card.duration_hint_sec + 's</span></div>' +
        '<div style="color:#f9fafb;font-size:14px;font-weight:700;margin-bottom:8px;line-height:1.3;">' + escapeHtml(card.headline) + '</div>' +
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">' +
        '<span style="color:' + st.statColor + ';font-size:10px;background:' + st.cardBorder + ';padding:2px 6px;border-radius:3px;font-family:monospace;">' + escapeHtml(card.layout) + '</span>' +
        (card.emphasis ? '<span style="color:' + st.cardEmphasisColor + ';font-size:10px;background:' + st.cardBorder + ';padding:2px 6px;border-radius:3px;">' + escapeHtml(card.emphasis) + '</span>' : '') + '</div>' +
        '<div style="display:flex;gap:12px;color:' + st.metaText + ';font-size:10px;font-family:monospace;">' +
        '<span>🎙 ' + card.audio_clip_count + '</span><span>📋 ' + (isLead ? '主线' : '补充') + '</span></div></div>';
    }

    var dashCardsHtml = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
    sections.news_cards.forEach(function (card) {
      dashCardsHtml += dashCardHtml(card);
    });
    dashCardsHtml += '</div>';

    return '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>' + escapeHtml(episode.title) + '</title>\n' + getSharedCss(st) + '</head>\n<body>\n' +
      '<div class="hero" style="border-bottom:2px solid ' + st.statColor + ';">\n<div class="hero-content">' +
      '<div class="hero-eyebrow"><span class="hero-badge" style="background:' + st.statColor + ';color:' + st.bodyBg + ';">📊 数据仪表盘</span><span class="hero-theme">' + escapeHtml(themeName) + '</span><span class="hero-badge-dur">⏱ ' + totalTimeStr + '</span></div>' +
      '<h1 style="color:' + st.statColor + ';">' + escapeHtml(episode.title) + '</h1>' +
      '<div class="hero-subtitle">' + escapeHtml(episode.subtitle) + '</div>' +
      '<div style="display:flex;gap:12px;margin-top:12px;flex-wrap:wrap;">' +
      metricChip('条新闻', sections.news_cards.length, '') +
      metricChip('主线', episode.lead_count, '') +
      metricChip('总时长', totalTimeStr, '') +
      metricChip('音频片段', totalAudio, '片段') +
      '</div></div>\n</div>\n' +
      '<div class="tl-rail" style="padding:10px 40px;"><div class="tl-track" style="min-width:400px;">' + renderSharedTimelineMarkersHtml(timeline, st) + '</div></div>\n' +
      '<div class="content">' +
      '<div class="section-label">新闻面板</div>\n' + dashCardsHtml +
      '<div class="section-label">结语</div>' +
      '<div style="background:' + st.closingBg + ';border-radius:8px;padding:20px;border:1px solid ' + st.statColor + ';">' +
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><span style="background:' + st.closingBadgeBg + ';color:' + st.closingBadgeColor + ';padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">INSIGHT</span></div>' +
      '<div style="color:#f9fafb;font-size:14px;font-weight:600;margin-bottom:4px;">' + escapeHtml(sections.closing.title) + '</div>' +
      (sections.closing.focus_news_id ? '<div style="color:' + st.metaText + ';font-size:11px;font-family:monospace;">📋 ' + escapeHtml(sections.closing.focus_news_id) + '</div>' : '') + '</div>\n' +
      '</div>\n<div class="footer-bar"><span>Mock Dashboard Preview · ' + escapeHtml(themeName) + ' · no real render</span><span>' + escapeHtml(episode.title) + '</span></div>\n</body>\n</html>';
  }

  // CP35.1: Layout 4 — research_briefing_v1 (research memo / briefing note format)
  function renderResearchBriefingEpisodeHtml(contract, st) {
    var episode = contract.episode;
    var timeline = contract.timeline;
    var sections = contract.sections;
    var totalTimeStr = formatTimecode(episode.estimated_duration_sec);
    var themeName = episode.theme_name || "";

    function briefCardHtml(card, idx) {
      var isLead = card.is_lead;
      var bc = isLead ? st.cardBorderLead : st.cardBorder;
      var bg = isLead ? st.cardBgLead : st.cardBg;
      var prefix = isLead ? '◆ KEY FINDING' : '○ OBSERVATION ' + (idx + 1);
      return '<div class="mock-news-card' + (isLead ? ' mock-news-card-lead' : '') + '" data-section-type="news_segment" style="background:' + bg + ';border:1px solid ' + bc + ';border-radius:4px;padding:20px;margin:8px 0;border-left:3px solid ' + bc + ';animation:fadeUp 0.4s ease-out both;">' +
        '<div style="color:' + st.metaText + ';font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">' + prefix + '</div>' +
        '<div style="color:#f9fafb;font-size:15px;font-weight:600;margin-bottom:10px;line-height:1.5;">' + escapeHtml(card.headline) + '</div>' +
        '<div style="border-top:1px solid ' + st.sectionDivider + ';padding-top:8px;margin-top:8px;">' +
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px;">' +
        '<span style="color:' + st.cardLayoutTagColor + ';font-size:10px;background:' + st.cardBadgeBg + ';padding:2px 6px;border-radius:2px;">📋 ' + escapeHtml(card.layout) + '</span>' +
        (card.emphasis ? '<span style="color:' + st.cardEmphasisColor + ';font-size:10px;background:' + st.cardBadgeBg + ';padding:2px 6px;border-radius:2px;">⚡ ' + escapeHtml(card.emphasis) + '</span>' : '') +
        (card.badges || []).map(function (b) { return '<span style="color:' + st.accentText + ';font-size:10px;background:' + st.cardBadgeBg + ';padding:2px 6px;border-radius:2px;">' + escapeHtml(b) + '</span>'; }).join('') + '</div>' +
        '<div style="color:' + st.metaText + ';font-size:10px;">⏱ ' + card.duration_hint_sec + 's &nbsp; 🎙 ' + card.audio_clip_count + ' clip(s) &nbsp; #' + card.order + '</div></div></div>';
    }

    function briefTransHtml(row) {
      return '<div style="text-align:center;padding:4px 0;border-top:1px dashed ' + st.sectionDivider + ';border-bottom:1px dashed ' + st.sectionDivider + ';margin:4px 0;color:' + st.metaText + ';font-size:10px;font-style:italic;letter-spacing:0.5px;">— ' + escapeHtml(row && row.text ? row.text : "接着看下一条") + ' —</div>';
    }

    var briefItems = [];
    sections.news_cards.forEach(function (card, i) {
      briefItems.push(briefCardHtml(card, i));
      if (i < sections.news_cards.length - 1 && sections.transitions && sections.transitions[i]) {
        briefItems.push(briefTransHtml(sections.transitions[i]));
      }
    });

    return '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Research Briefing — ' + escapeHtml(episode.title) + '</title>\n' + getSharedCss(st) + '</head>\n<body>\n' +
      '<div class="hero" style="border-bottom:2px solid ' + st.cardBorder + ';">\n<div class="hero-content">' +
      '<div style="color:' + st.metaText + ';font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">📄 RESEARCH BRIEFING</div>' +
      '<h1 style="color:' + st.accentText + ';font-size:24px;">' + escapeHtml(episode.title) + '</h1>' +
      '<div style="color:' + st.metaText + ';font-size:13px;margin-bottom:12px;line-height:1.5;">' + escapeHtml(episode.subtitle) + '</div>' +
      '<div style="display:flex;gap:20px;font-size:11px;color:' + st.metaText + ';font-family:monospace;">' +
      '<span>📰 ' + sections.news_cards.length + ' observations</span>' +
      '<span>⏱ ' + totalTimeStr + '</span>' +
      '<span>◆ ' + episode.lead_count + ' key findings</span></div></div>\n</div>\n' +
      '<div style="background:' + st.bodyBg + ';padding:0 40px;border-bottom:1px solid ' + st.sectionDivider + ';"><div style="display:flex;gap:24px;padding:8px 0;font-size:10px;color:' + st.metaText + ';overflow-x:auto;white-space:nowrap;">' +
      '<span>📍 开场</span>' +
      (sections.news_cards.map(function (c, i) { return '<span>#' + (i + 1) + ' ' + escapeHtml(c.headline).substring(0, 20) + '...</span>'; }).join(' → ')) +
      '<span>📍 结尾</span></div></div>\n' +
      '<div class="content" style="max-width:700px;">' +
      '<div style="background:' + st.openingBg + ';border-left:3px solid ' + st.cardBorder + ';border-radius:4px;padding:16px;margin-bottom:16px;">' +
      '<div style="color:' + st.metaText + ';font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">📋 OVERVIEW</div>' +
      '<div style="color:#f9fafb;font-size:14px;font-weight:600;margin-bottom:4px;">' + escapeHtml(sections.opening.title) + '</div>' +
      '<div style="color:' + st.metaText + ';font-size:12px;">' + escapeHtml(sections.opening.subtitle) + '</div></div>\n' +
      '<div class="section-label">Key Findings & Observations</div>\n' + briefItems.join("") +
      '<div style="background:' + st.closingBg + ';border-left:3px solid ' + st.cardBorder + ';border-radius:4px;padding:16px;margin-top:16px;">' +
      '<div style="color:' + st.metaText + ';font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">🔬 CLOSING TAKEAWAY</div>' +
      '<div style="color:#f9fafb;font-size:14px;font-weight:600;margin-bottom:4px;">' + escapeHtml(sections.closing.title) + '</div>' +
      (sections.closing.focus_news_id ? '<div style="color:' + st.metaText + ';font-size:11px;margin-top:6px;">📋 ID: ' + escapeHtml(sections.closing.focus_news_id) + '</div>' : '') + '</div>\n' +
      '</div>\n<div class="footer-bar"><span>Research Briefing · ' + escapeHtml(themeName) + ' · no real render</span><span>' + escapeHtml(episode.title) + '</span></div>\n</body>\n</html>';
  }

  // CP35.1: Layout 5 — podcast_cards_v1 (podcast episode format with chapters and warm topic cards)
  function renderPodcastCardsEpisodeHtml(contract, st) {
    var episode = contract.episode;
    var timeline = contract.timeline;
    var sections = contract.sections;
    var totalTimeStr = formatTimecode(episode.estimated_duration_sec);
    var themeName = episode.theme_name || "";

    function topicCardHtml(card, idx) {
      var isLead = card.is_lead;
      var bc = isLead ? st.cardBorderLead : st.cardBorder;
      var bg = isLead ? st.cardBgLead : st.cardBg;
      var epNum = String(idx + 1).padStart(2, '0');
      return '<div class="mock-news-card' + (isLead ? ' mock-news-card-lead' : '') + '" data-section-type="news_segment" style="background:' + bg + ';border:1px solid ' + bc + ';border-radius:16px;padding:20px;margin:10px 0;animation:fadeUp 0.4s ease-out both;">' +
        '<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:12px;">' +
        '<div style="background:' + st.badgeBg + ';color:' + st.badgeColor + ';border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900;flex-shrink:0;">' + epNum + '</div>' +
        '<div style="flex:1;">' +
        '<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">' +
        '<span style="color:' + st.cardLayoutTagColor + ';font-size:11px;font-weight:600;">' + escapeHtml(card.layout) + '</span>' +
        (isLead ? '<span style="background:' + st.badgeBg + ';color:' + st.badgeColor + ';padding:1px 6px;border-radius:10px;font-size:9px;font-weight:700;">★ 主线</span>' : '') + '</div>' +
        '<div style="color:' + st.metaText + ';font-size:10px;font-family:monospace;">' + card.time_range + ' · ' + card.duration_hint_sec + 's</div></div></div>' +
        '<div style="color:#f9fafb;font-size:15px;font-weight:600;line-height:1.5;margin-bottom:10px;">' + escapeHtml(card.headline) + '</div>' +
        (card.emphasis ? '<div style="background:' + st.podcastTransitionBg + ';border-radius:8px;padding:8px 12px;margin-bottom:8px;color:' + st.accentText + ';font-size:12px;font-style:italic;">💬 ' + escapeHtml(card.emphasis) + '</div>' : '') +
        '<div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px;">' +
        (card.badges || []).map(function (b) { return '<span style="background:' + st.cardBadgeBg + ';color:' + st.accentText + ';font-size:10px;padding:2px 6px;border-radius:10px;">' + escapeHtml(b) + '</span>'; }).join('') + '</div>' +
        '<div style="color:' + st.metaText + ';font-size:10px;">🎙 ' + card.audio_clip_count + ' clips &nbsp; ' + (isLead ? '📌 主线' : '📎 补充') + '</div></div>';
    }

    function hostTransHtml(row) {
      var texts = ["好，咱们接着聊", "来，看看下一条", "下个话题", "继续"];
      var t = row && row.text ? row.text : texts[Math.floor(Math.random() * texts.length)];
      return '<div style="text-align:center;padding:10px 20px;margin:4px 20px;background:' + st.podcastTransitionBg + ';border-radius:20px;color:' + st.accentText + ';font-size:12px;font-style:italic;">🎙️ ' + escapeHtml(t) + '</div>';
    }

    var epNum = Math.floor(Math.random() * 90) + 10;
    var cards = [];
    sections.news_cards.forEach(function (card, i) {
      cards.push(topicCardHtml(card, i));
      if (i < sections.news_cards.length - 1 && sections.transitions && sections.transitions[i]) {
        cards.push(hostTransHtml(sections.transitions[i]));
      }
    });

    return '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Ep.' + epNum + ' — ' + escapeHtml(episode.title) + '</title>\n' + getSharedCss(st) + '</head>\n<body>\n' +
      '<div style="background:' + st.heroBg + ';padding:40px;text-align:center;border-bottom:1px solid ' + st.heroBorder + ';">' +
      '<div style="display:inline-block;background:' + st.badgeBg + ';color:' + st.badgeColor + ';padding:4px 16px;border-radius:20px;font-size:11px;font-weight:700;margin-bottom:16px;">🎙️ EPISODE ' + epNum + '</div>' +
      '<h1 style="color:#f9fafb;font-size:26px;font-weight:800;margin-bottom:8px;line-height:1.3;">' + escapeHtml(episode.title) + '</h1>' +
      '<div style="color:' + st.accentText + ';font-size:14px;margin-bottom:16px;">' + escapeHtml(episode.subtitle) + '</div>' +
      '<div style="display:flex;justify-content:center;gap:24px;font-size:12px;color:' + st.metaText + ';">' +
      '<span>📰 ' + sections.news_cards.length + ' topics</span>' +
      '<span>⏱ ' + totalTimeStr + '</span>' +
      '<span>◆ ' + episode.lead_count + ' featured</span></div></div>\n' +
      '<div style="background:' + st.bodyBg + ';padding:16px 40px;border-bottom:1px solid ' + st.heroBorder + ';"><div style="display:flex;gap:20px;overflow-x:auto;padding:4px 0;">' +
      '<span style="color:' + st.metaText + ';font-size:11px;font-weight:700;white-space:nowrap;padding:4px 0;">📑 CHAPTERS:</span>' +
      '<span style="color:' + st.accentText + ';font-size:11px;white-space:nowrap;padding:4px 8px;background:' + st.cardBadgeBg + ';border-radius:10px;">🎙️ 开场</span>' +
      sections.news_cards.map(function (c, i) {
        return '<span style="color:' + st.metaText + ';font-size:11px;white-space:nowrap;padding:4px 8px;">#' + (i + 1) + ' ' + escapeHtml(c.headline).substring(0, 15) + '...</span>';
      }).join('') +
      '<span style="color:' + st.accentText + ';font-size:11px;white-space:nowrap;padding:4px 8px;background:' + st.cardBadgeBg + ';border-radius:10px;">📍 结尾</span></div></div>\n' +
      '<div class="content" style="max-width:700px;margin:0 auto;">' +
      '<div style="text-align:center;padding:20px;color:' + st.metaText + ';font-size:13px;font-style:italic;border-bottom:1px solid ' + st.sectionDivider + ';margin-bottom:16px;">' +
      '🎙️ ' + escapeHtml(sections.opening.title) + ' — ' + escapeHtml(sections.opening.subtitle) + '</div>\n' +
      cards.join("") +
      '<div style="background:' + st.closingBg + ';border-radius:16px;padding:24px;text-align:center;margin-top:16px;">' +
      '<div style="color:' + st.accentText + ';font-size:11px;font-weight:700;letter-spacing:1px;margin-bottom:8px;">📍 本期回顾</div>' +
      '<div style="color:#f9fafb;font-size:15px;font-weight:600;margin-bottom:8px;">' + escapeHtml(sections.closing.title) + '</div>' +
      (sections.closing.focus_news_id ? '<div style="color:' + st.metaText + ';font-size:11px;">📋 主线新闻 ID: ' + escapeHtml(sections.closing.focus_news_id) + '</div>' : '') +
      '<div style="margin-top:12px;color:' + st.metaText + ';font-size:11px;">— End of Episode ' + epNum + ' —</div></div>\n' +
      '</div>\n<div class="footer-bar"><span>🎙️ Podcast Preview · ' + escapeHtml(themeName) + ' · no real render</span><span>' + escapeHtml(episode.title) + '</span></div>\n</body>\n</html>';
  }

  // CP34: Thin wrapper — buildMockEpisodeHtml delegates to contract pipeline
  function buildMockEpisodeHtml(renderIr) {
    var contract = buildEpisodeTemplateContract(renderIr);
    if (!contract) return "";
    return renderEpisodeTemplateHtml(contract);
  }

  // CP28: Validate mock episode HTML
  function validateMockEpisodeHtml(html) {
    var warnings = [];
    var errors = [];

    if (!html || html.length === 0) {
      errors.push("HTML 为空");
      return { ok: false, warnings: warnings, errors: errors };
    }

    if (html.indexOf("<!DOCTYPE html>") === -1 && html.indexOf("<html") === -1) {
      errors.push("HTML 必须包含 <!DOCTYPE html> 或 <html>");
    }

    // CP31: Must contain mock-news-card
    if (html.indexOf("mock-news-card") === -1) {
      errors.push("HTML 必须包含 mock-news-card");
    }

    // CP31.1: Must have opening section (strict)
    if (html.indexOf("section-title") === -1 && html.indexOf("开场") === -1) {
      errors.push("HTML 必须包含开场");
    }

    // CP31.1: Must have closing section (strict)
    if (html.indexOf("结尾") === -1 && html.indexOf("closing") === -1) {
      errors.push("HTML 必须包含结尾");
    }

    // No API key / voice_id
    if (/api[_-]?key/i.test(html) || /voice[_-]?id/i.test(html)) {
      errors.push("HTML 中不允许出现 API key 或 voice_id");
    }

    // No external http links
    if (/https?:\/\//.test(html) && !/https?:\/\/localhost/.test(html)) {
      errors.push("HTML 中不允许出现外部 http 链接");
    }

    // CP33.1: Must contain data-section-type="news_segment"
    if (html.indexOf('data-section-type="news_segment"') === -1) {
      errors.push('HTML 必须包含 data-section-type="news_segment"');
    }

    // CP33.1: Must contain timeline rail
    if (html.indexOf("tl-rail") === -1 && html.indexOf("tl-track") === -1) {
      errors.push("HTML 必须包含 timeline rail (tl-rail 或 tl-track)");
    }

    // CP33.1: Must contain pseudo timecode
    if (html.indexOf("tl-time") === -1) {
      errors.push("HTML 必须包含伪时间码 (tl-time)");
    }

    // CP33.1: Explicitly reject script tags
    if (/<script\b/i.test(html)) {
      errors.push("HTML 不允许包含 script 标签");
    }

    // CP33.1: Reject img with remote links
    if (/<img[^>]*src=["']?https?:\/\//i.test(html)) {
      errors.push("HTML 不允许 img 标签包含外部链接");
    }

    return {
      ok: errors.length === 0,
      warnings: warnings,
      errors: errors,
    };
  }

  // CP28: Preview mock episode HTML in iframe
  function previewMockEpisodeHtml() {
    if (episodeItemList.length === 0) {
      setStatus("请先加入新闻，再预览合集画面", "error");
      return;
    }

    var plan = buildEpisodePlan();
    var planResult = validateEpisodePlan(plan);
    if (!planResult.ok) {
      setStatus("栏目计划有误：" + planResult.errors.join("；"), "error");
      return;
    }

    var script = buildEpisodeScriptFromPlan(plan);
    var scriptResult = validateEpisodeScript(script);
    if (!scriptResult.ok) {
      setStatus("栏目脚本有误：" + scriptResult.errors.join("；"), "error");
      return;
    }

    var manifest = buildEpisodeAudioManifestFromScript(script);
    var manifestResult = validateEpisodeAudioManifest(manifest);
    if (!manifestResult.ok) {
      setStatus("音频计划有误：" + manifestResult.errors.join("；"), "error");
      return;
    }

    var renderIr = buildEpisodeRenderIrFromContracts(plan, script, manifest);
    var renderIrResult = validateEpisodeRenderIr(renderIr);
    if (!renderIrResult.ok) {
      setStatus("视觉计划有误：" + renderIrResult.errors.join("；"), "error");
      return;
    }

    // CP34: Build and validate template contract
    var contract = buildEpisodeTemplateContract(renderIr);
    var contractResult = validateEpisodeTemplateContract(contract);
    if (!contractResult.ok) {
      setStatus("模板契约有误：" + contractResult.errors.join("；"), "error");
      return;
    }
    latestEpisodeTemplateContract = contract;

    var html = buildMockEpisodeHtml(renderIr);
    var htmlResult = validateMockEpisodeHtml(html);
    if (!htmlResult.ok) {
      setStatus("Mock HTML 有误：" + htmlResult.errors.join("；"), "error");
      return;
    }

    // Revoke previous Blob URL to avoid memory leak
    if (latestEpisodePreviewUrl) {
      URL.revokeObjectURL(latestEpisodePreviewUrl);
      latestEpisodePreviewUrl = null;
    }

    // Create Blob and set iframe src
    var blob = new Blob([html], { type: "text/html" });
    latestEpisodePreviewUrl = URL.createObjectURL(blob);
    previewHtml.src = latestEpisodePreviewUrl;

    // Show preview tab
    switchToPreviewTab();
    setPreviewMode("html");

    // Show banner
    autoPreviewBanner.style.display = "block";
    autoPreviewBanner.textContent = "多新闻合集 Mock 预览";

    setStatus("Mock 预览已生成", "success");
  }

  // CP31: Save mock episode HTML to server artifact
  function saveMockEpisodeHtml() {
    if (episodeItemList.length === 0) {
      setStatus("请先加入新闻，再保存合集 HTML", "error");
      return;
    }

    var plan = buildEpisodePlan();
    var planResult = validateEpisodePlan(plan);
    if (!planResult.ok) {
      setStatus("栏目计划有误：" + planResult.errors.join("；"), "error");
      return;
    }

    var script = buildEpisodeScriptFromPlan(plan);
    var scriptResult = validateEpisodeScript(script);
    if (!scriptResult.ok) {
      setStatus("栏目脚本有误：" + scriptResult.errors.join("；"), "error");
      return;
    }

    var manifest = buildEpisodeAudioManifestFromScript(script);
    var manifestResult = validateEpisodeAudioManifest(manifest);
    if (!manifestResult.ok) {
      setStatus("音频计划有误：" + manifestResult.errors.join("；"), "error");
      return;
    }

    var renderIr = buildEpisodeRenderIrFromContracts(plan, script, manifest);
    var renderIrResult = validateEpisodeRenderIr(renderIr);
    if (!renderIrResult.ok) {
      setStatus("视觉计划有误：" + renderIrResult.errors.join("；"), "error");
      return;
    }

    // CP34: Build and validate template contract
    var contract = buildEpisodeTemplateContract(renderIr);
    var contractResult = validateEpisodeTemplateContract(contract);
    if (!contractResult.ok) {
      setStatus("模板契约有误：" + contractResult.errors.join("；"), "error");
      return;
    }
    latestEpisodeTemplateContract = contract;

    var html = buildMockEpisodeHtml(renderIr);
    var htmlResult = validateMockEpisodeHtml(html);
    if (!htmlResult.ok) {
      setStatus("Mock HTML 校验失败：" + htmlResult.errors.join("；"), "error");
      return;
    }

    setStatus("正在保存合集 HTML...", "info");

    fetch("/api/episode/mock-html", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        html: html,
        episode_title: plan.title || "今日 AI 前沿速览",
      }),
    })
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (!data.ok) {
          setStatus("保存失败：" + (data.error || "未知错误"), "error");
          return;
        }

        latestEpisodeHtmlArtifact = {
          path: data.path,
          file_path: data.file_path,
          created_at: data.created_at,
        };

        // Revoke previous Blob URL
        if (latestEpisodePreviewUrl) {
          URL.revokeObjectURL(latestEpisodePreviewUrl);
          latestEpisodePreviewUrl = null;
        }

        // Load saved file in preview iframe
        previewHtml.src = data.path;

        switchToPreviewTab();
        setPreviewMode("html");

        autoPreviewBanner.style.display = "block";
        autoPreviewBanner.textContent = "已保存的合集 HTML 预览";

        // CP31.1: Show open and download links (no absolute paths)
        downloadLinks.innerHTML = "";
        var openLink = document.createElement("a");
        openLink.href = data.path;
        openLink.target = "_blank";
        openLink.rel = "noopener";
        openLink.className = "download-link";
        openLink.textContent = "🔗 打开已保存 HTML";
        downloadLinks.appendChild(openLink);

        var downloadLink = document.createElement("a");
        downloadLink.href = data.path;
        downloadLink.download = "";
        downloadLink.className = "download-link";
        downloadLink.textContent = "💾 下载 HTML";
        downloadLinks.appendChild(downloadLink);

        // CP32: Refresh history so the new artifact appears immediately
        loadEpisodeHtmlHistory();

        setStatus("合集 HTML 已保存至 artifact", "success");
      })
      .catch(function (err) {
        setStatus("保存失败：" + err.message, "error");
      });
  }

  // CP32: Load episode HTML artifact history from server
  function loadEpisodeHtmlHistory() {
    fetch("/api/episode/html-history")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (!data.ok) {
          renderEpisodeHtmlHistory([]);
          return;
        }
        episodeHtmlHistoryList = data.items || [];
        renderEpisodeHtmlHistory(episodeHtmlHistoryList);
      })
      .catch(function () {
        episodeHtmlHistoryList = [];
        renderEpisodeHtmlHistory([]);
      });
  }

  // CP32: Render episode HTML artifact history list
  function renderEpisodeHtmlHistory(items) {
    if (!episodeHtmlHistoryListEl) return;

    if (!items || items.length === 0) {
      episodeHtmlHistoryListEl.innerHTML = '<div class="episode-html-history-empty">暂无已保存合集 HTML</div>';
      return;
    }

    episodeHtmlHistoryListEl.innerHTML = "";
    items.forEach(function (item) {
      var itemEl = document.createElement("div");
      itemEl.className = "episode-html-history-item";

      var sizeKB = Math.round((item.size || 0) / 1024);
      var timeStr = item.created_at ? item.created_at.replace("T", " ").slice(0, 19) : "";

      itemEl.innerHTML =
        '<div class="episode-html-history-item-name" title="' + escapeHtml(item.filename || "") + '">' +
          escapeHtml(item.filename || "") +
        '</div>' +
        '<div class="episode-html-history-item-meta">' +
          (timeStr ? escapeHtml(timeStr) : "") +
          (sizeKB > 0 ? " · " + sizeKB + " KB" : "") +
        '</div>' +
        '<div class="episode-html-history-item-actions">' +
          '<button class="episode-html-history-item-btn" data-action="open">打开</button>' +
          '<button class="episode-html-history-item-btn" data-action="download">下载</button>' +
        '</div>';

      itemEl.querySelectorAll(".episode-html-history-item-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var action = btn.getAttribute("data-action");
          openEpisodeHtmlArtifact(item, action);
        });
      });

      episodeHtmlHistoryListEl.appendChild(itemEl);
    });
  }

  // CP32: Open or download a history artifact
  function openEpisodeHtmlArtifact(item, action) {
    if (!item || !item.path) return;

    if (action === "download") {
      // Trigger download via a temporary anchor
      var a = document.createElement("a");
      a.href = item.path;
      a.download = item.filename || "episode.html";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      return;
    }

    // Open in iframe
    previewHtml.src = item.path;
    switchToPreviewTab();
    setPreviewMode("html");

    autoPreviewBanner.style.display = "block";
    autoPreviewBanner.textContent = "历史合集 HTML 预览";

    // Show download link
    downloadLinks.innerHTML = "";
    var openLink = document.createElement("a");
    openLink.href = item.path;
    openLink.target = "_blank";
    openLink.rel = "noopener";
    openLink.className = "download-link";
    openLink.textContent = "🔗 打开已保存 HTML";
    downloadLinks.appendChild(openLink);

    var downloadLink = document.createElement("a");
    downloadLink.href = item.path;
    downloadLink.download = "";
    downloadLink.className = "download-link";
    downloadLink.textContent = "💾 下载 HTML";
    downloadLinks.appendChild(downloadLink);
  }

  // CP29.1: Sync theme showcase themes into hidden selectTheme
  // Ensures all 12 showcase theme IDs are available as options even if
  // /api/themes (from config/themes.yaml) doesn't include them yet.
  function syncThemeSelectWithShowcases() {
    if (!selectTheme) return;
    // Collect existing option values
    var existingValues = {};
    Array.from(selectTheme.querySelectorAll("option")).forEach(function (opt) {
      existingValues[opt.value] = true;
    });
    // Append any showcase theme missing from selectTheme
    Object.values(THEME_SHOWCASES).forEach(function (theme) {
      if (!existingValues[theme.id]) {
        var opt = document.createElement("option");
        opt.value = theme.id;
        opt.textContent = theme.name;
        selectTheme.appendChild(opt);
        existingValues[theme.id] = true; // prevent duplicates within this run
      }
    });
  }

  // CP29.1: Ensure a theme option exists in selectTheme, then set value.
  // Returns true if selectTheme.value equals the theme.id after operation.
  function ensureThemeOption(theme) {
    if (!selectTheme || !theme) return false;
    // Check if option already exists
    var existingOpt = selectTheme.querySelector('option[value="' + theme.id + '"]');
    if (!existingOpt) {
      var opt = document.createElement("option");
      opt.value = theme.id;
      opt.textContent = theme.name;
      selectTheme.appendChild(opt);
    }
    selectTheme.value = theme.id;
    // Dispatch change so listeners (renderThemeShowcase, updateGenerationPlan) react
    selectTheme.dispatchEvent(new Event("change"));
    return selectTheme.value === theme.id;
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
          (theme.category ? '<span class="theme-showcase-category">' + escapeHtml(theme.category) + '</span>' : '') +
        '</div>' +
        '<div class="theme-showcase-desc">' + escapeHtml(theme.desc) + '</div>' +
        (theme.best_for ? '<div class="theme-showcase-bestfor">适用：' + escapeHtml(theme.best_for) + '</div>' : '') +
        '<div class="theme-showcase-tags">' + tagsHtml + '</div>' +
        '<button class="theme-showcase-sample-btn" type="button">查看样例</button>';

      // Theme selection click (on card background)
      div.addEventListener("click", function (ev) {
        if (ev.target.classList.contains("theme-showcase-sample-btn")) return;
        // CP29.1: Use ensureThemeOption to guarantee the option exists
        var ok = ensureThemeOption(theme);
        if (!ok) {
          setStatus("主题选择失败: " + theme.id, "error");
          return;
        }
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
      updateHotNewsRecommendationActiveStates();
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

  // CP25: View episode script button
  var btnViewEpisodeScript = document.getElementById("btn-view-episode-script");
  if (btnViewEpisodeScript) {
    btnViewEpisodeScript.addEventListener("click", function () {
      showEpisodeScript();
    });
  }

  // CP26: View audio manifest button
  var btnViewAudioManifest = document.getElementById("btn-view-audio-manifest");
  if (btnViewAudioManifest) {
    btnViewAudioManifest.addEventListener("click", function () {
      showEpisodeAudioManifest();
    });
  }

  // CP27: View visual plan button
  var btnViewVisualPlan = document.getElementById("btn-view-visual-plan");
  if (btnViewVisualPlan) {
    btnViewVisualPlan.addEventListener("click", function () {
      showEpisodeRenderIr();
    });
  }

  // CP28: Preview mock episode HTML button
  var btnPreviewEpisode = document.getElementById("btn-preview-episode");
  if (btnPreviewEpisode) {
    btnPreviewEpisode.addEventListener("click", function () {
      previewMockEpisodeHtml();
    });
  }

  // CP31: Save mock episode HTML button
  var btnSaveEpisodeHtml = document.getElementById("btn-save-episode-html");
  if (btnSaveEpisodeHtml) {
    btnSaveEpisodeHtml.addEventListener("click", function () {
      saveMockEpisodeHtml();
    });
  }

  // CP35: Episode preview style selector
  if (selectEpisodePreviewStyle) {
    selectEpisodePreviewStyle.addEventListener("change", function () {
      currentEpisodePreviewStyle = selectEpisodePreviewStyle.value || "timeline_daily_v1";
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
