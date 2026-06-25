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

  // CP40.4: Episode export DOM refs
  const btnExportEpisodeMp4 = document.getElementById("btn-export-episode-mp4");
  const episodeExportPanel = document.getElementById("episode-export-panel");
  const episodeExportStatus = document.getElementById("episode-export-status");
  const episodeExportDownload = document.getElementById("episode-export-download");

  // CP40.5: Episode export history DOM refs
  const episodeExportHistoryPanel = document.getElementById("episode-export-history-panel");
  const episodeExportHistoryListEl = document.getElementById("episode-export-history-list");
  const btnRefreshEpisodeExports = document.getElementById("btn-refresh-episode-exports");
  const btnCleanupEpisodeExports = document.getElementById("btn-cleanup-episode-exports");

  // CP40.6: Audio mux DOM refs
  const checkEpisodeExportAudio = document.getElementById("check-episode-export-audio");
  const episodeExportAudioHint = document.getElementById("episode-export-audio-hint");

  // CP40.7: Episode export style picker DOM refs
  const selectEpisodeExportStyle = document.getElementById("select-episode-export-style");
  const episodeExportStyleHint = document.getElementById("episode-export-style-hint");

  // CP41.2: Empty state DOM refs
  const previewEmptyState = document.getElementById("preview-empty-state");
  const episodePlanEmpty = document.getElementById("episode-plan-empty");
  const episodeScriptEmpty = document.getElementById("episode-script-empty");
  const audioManifestEmpty = document.getElementById("audio-manifest-empty");
  const visualPlanEmpty = document.getElementById("visual-plan-empty");
  const historyEmptyState = document.getElementById("history-empty-state");

  // CP41.3: First-run guide DOM refs
  const firstRunGuide = document.getElementById("first-run-guide");
  const btnCollapseFirstRunGuide = document.getElementById("btn-collapse-first-run-guide");

  // CP43: Source contract panel DOM refs
  const btnBuildContractFromSample = document.getElementById("btn-build-contract-from-sample");
  const btnBuildContractFromInline = document.getElementById("btn-build-contract-from-inline");
  const sourceInlineText = document.getElementById("source-inline-text");
  const sourceContractStatus = document.getElementById("source-contract-status");
  // CP43.1: Source contract inspector DOM refs
  const sourceContractInspector = document.getElementById("source-contract-inspector");
  const sourceContractInspectorSummary = document.getElementById("source-contract-inspector-summary");
  const sourceEpisodeItemsList = document.getElementById("source-episode-items-list");
  const sourceNewsItemsList = document.getElementById("source-news-items-list");
  const btnApplySourceContractToPlanner = document.getElementById("btn-apply-source-contract-to-planner");
  // CP44: URL input DOM refs
  const sourceUrlSourceSelect = document.getElementById("source-url-source-select");
  const sourceUrlInput = document.getElementById("source-url-input");
  const sourceUrlTitle = document.getElementById("source-url-title");
  const sourceUrlSummary = document.getElementById("source-url-summary");
  const btnBuildContractFromUrl = document.getElementById("btn-build-contract-from-url");
  const btnFetchArticleFromUrl = document.getElementById("btn-fetch-article-from-url");

  // CP46: URL Draft Basket DOM refs
  const urlDraftNewUrl = document.getElementById("url-draft-new-url");
  const btnAddUrlDraft = document.getElementById("btn-add-url-draft");
  const btnClearUrlDrafts = document.getElementById("btn-clear-url-drafts");
  const urlDraftList = document.getElementById("url-draft-list");
  const btnBuildContractFromUrlDrafts = document.getElementById("btn-build-contract-from-url-drafts");

  // CP47: Source Collection DOM refs
  const sourceCollectionName = document.getElementById("source-collection-name");
  const btnSaveSourceCollection = document.getElementById("btn-save-source-collection");
  const btnClearSourceCollections = document.getElementById("btn-clear-source-collections");
  const sourceCollectionList = document.getElementById("source-collection-list");

  // CP48: Production Workflow DOM refs
  const productionWorkflowPanel = document.getElementById("production-workflow-panel");
  const productionWorkflowSteps = document.getElementById("production-workflow-steps");
  const productionWorkflowSummary = document.getElementById("production-workflow-summary");
  const productionReadinessBadge = document.getElementById("production-readiness-badge");

  // CP49: Publish Package DOM refs
  const btnGeneratePublishPackage = document.getElementById("btn-generate-publish-package");
  const publishPackageStatus = document.getElementById("publish-package-status");
  const publishPackageContent = document.getElementById("publish-package-content");
  const publishTitle = document.getElementById("publish-title");
  const publishDescription = document.getElementById("publish-description");
  const publishPlatformCopy = document.getElementById("publish-platform-copy");
  const publishTags = document.getElementById("publish-tags");
  const publishCoverPrompt = document.getElementById("publish-cover-prompt");
  const publishAssetLinks = document.getElementById("publish-asset-links");
  const publishSourceSummary = document.getElementById("publish-source-summary");

  // CP50: Export Publish Package DOM refs
  const btnExportPublishPackageJson = document.getElementById("btn-export-publish-package-json");
  const btnExportPublishPackageMd = document.getElementById("btn-export-publish-package-md");

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

  // CP40.4: Episode export polling state
  let currentEpisodeExportId = null;
  let currentEpisodeExportPollTimer = null;
  let currentEpisodeExportMp4Url = null;   // set from POST response for use in completed state

  // CP40.7: Episode export capabilities (loaded from backend)
  let episodeExportCapabilities = null;

  // CP43: Source contract state
  let latestSourceContract = null;      // most recent source-generated contract
  let latestSourceNewsItems = [];       // news items from source pipeline
  let latestSourceEpisodeItems = [];     // episode items from source pipeline
  let reliableSources = [];              // CP44: reliable source registry

  // CP46: URL Draft Basket state
  let urlDraftItems = [];               // URL draft basket items
  const MAX_URL_DRAFT_ITEMS = 5;        // maximum number of URL drafts

  // CP47: Source Collection state
  const SOURCE_COLLECTION_STORAGE_KEY = "chalk_source_collections_v1";
  const MAX_SOURCE_COLLECTIONS = 20;
  let sourceCollections = [];           // saved source collections

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

  // ---------- CP40.4: Episode export functions ----------

  // CP40.7: Load export capabilities from backend
  async function loadEpisodeExportCapabilities() {
    try {
      var resp = await fetch("/api/episode/export/capabilities");
      if (!resp.ok) throw new Error("Failed to load export capabilities");
      var data = await resp.json();
      episodeExportCapabilities = data;
      renderEpisodeExportStyleOptions(data);
      updateCapabilityDashboard(data);
    } catch (e) {
      console.warn("Could not load export capabilities:", e.message);
      // Fall back to a minimal default so the UI still works
      episodeExportCapabilities = {
        default_style_id: "breaking_news_v1",
        supported_styles: [{ id: "breaking_news_v1", name: "快讯大屏风" }],
        unsupported_styles: [],
      };
      renderEpisodeExportStyleOptions(episodeExportCapabilities);
      updateCapabilityDashboard(episodeExportCapabilities);
    }
  }

  // CP40.7: Populate the export style selector based on capabilities
  function renderEpisodeExportStyleOptions(capabilities) {
    if (!selectEpisodeExportStyle) return;

    var supported = capabilities.supported_styles || [];
    var unsupported = capabilities.unsupported_styles || [];

    selectEpisodeExportStyle.innerHTML = "";

    supported.forEach(function (style) {
      var opt = document.createElement("option");
      opt.value = style.id;
      opt.textContent = (style.name || style.id) + "（支持导出）";
      selectEpisodeExportStyle.appendChild(opt);
    });

    unsupported.forEach(function (style) {
      var opt = document.createElement("option");
      opt.value = style.id;
      opt.textContent = (style.name || style.id) + "（暂不支持 MP4 导出）";
      opt.disabled = true;
      selectEpisodeExportStyle.appendChild(opt);
    });

    // Default to the backend's declared default
    selectEpisodeExportStyle.value = capabilities.default_style_id || "breaking_news_v1";

    updateEpisodeExportStyleHint();
  }

  // CP40.7: Show a warning when preview style differs from export style
  function updateEpisodeExportStyleHint() {
    if (!episodeExportStyleHint) return;

    var previewStyle = selectEpisodePreviewStyle ? selectEpisodePreviewStyle.value : null;
    var exportStyle = getCurrentEpisodeExportStyleId();

    if (previewStyle && previewStyle !== exportStyle) {
      episodeExportStyleHint.textContent =
        "注意：当前预览为 " + previewStyle + "，MP4 导出将使用 " + exportStyle + "。";
      episodeExportStyleHint.className = "episode-export-style-hint is-warning";
    } else {
      episodeExportStyleHint.textContent = "当前 MP4 导出样式：" + exportStyle;
      episodeExportStyleHint.className = "episode-export-style-hint";
    }
  }

  // CP41: Update the capability dashboard summary from the capabilities API response
  function updateCapabilityDashboard(capabilities) {
    var capStyleEl = document.getElementById("cap-summary-style");
    var capAudioEl = document.getElementById("cap-summary-audio");

    if (capStyleEl && capabilities) {
      var supported = capabilities.supported_styles || [];
      var unsupported = capabilities.unsupported_styles || [];
      if (supported.length === 1) {
        capStyleEl.textContent = supported[0].name || supported[0].id;
        capStyleEl.style.color = "#4ade80";
      } else {
        capStyleEl.textContent = supported.map(function (s) { return s.name || s.id; }).join(", ");
      }
    }

    if (capAudioEl && capabilities) {
      var audioSupport = capabilities.audio && capabilities.audio.supports_audio_mux;
      if (audioSupport) {
        capAudioEl.textContent = "支持（仅 /outputs/ 下音频）";
        capAudioEl.style.color = "#4ade80";
      } else {
        capAudioEl.textContent = "不支持";
        capAudioEl.style.color = "#f87171";
      }
    }
  }

  function getCurrentEpisodeExportStyleId() {
    // Use the explicit export style selector (CP40.7)
    if (selectEpisodeExportStyle && selectEpisodeExportStyle.value) {
      return selectEpisodeExportStyle.value;
    }
    return "breaking_news_v1";
  }

  function renderEpisodeExportStatus(statusData) {
    if (!statusData || !statusData.status) return;

    var status = statusData.status;
    var progress = statusData.progress != null ? statusData.progress : 0;
    var message = statusData.message || "";
    var errorMsg = statusData.error_message || "";

    episodeExportStatus.className = "episode-export-status";

    if (status === "pending") {
      episodeExportStatus.classList.add("is-pending");
      episodeExportStatus.textContent = "已加入导出队列...";
    } else if (status === "running") {
      episodeExportStatus.classList.add("is-running");
      episodeExportStatus.textContent = "正在导出 · " + progress + "% · " + message;
    } else if (status === "completed") {
      episodeExportStatus.classList.add("is-completed");
      episodeExportStatus.textContent = "导出完成";
    } else if (status === "failed") {
      episodeExportStatus.classList.add("is-failed");
      episodeExportStatus.textContent = "导出失败" + (errorMsg ? " · " + errorMsg : "");
    } else {
      episodeExportStatus.textContent = message || status;
    }
  }

  function stopEpisodeExportPolling() {
    if (currentEpisodeExportPollTimer !== null) {
      clearInterval(currentEpisodeExportPollTimer);
      currentEpisodeExportPollTimer = null;
    }
  }

  function setEpisodeExportButtonState(state) {
    if (!btnExportEpisodeMp4) return;
    if (state === "idle") {
      btnExportEpisodeMp4.disabled = false;
      btnExportEpisodeMp4.textContent = "导出 MP4";
    } else if (state === "running") {
      btnExportEpisodeMp4.disabled = true;
      btnExportEpisodeMp4.textContent = "导出中...";
    } else if (state === "done") {
      btnExportEpisodeMp4.disabled = false;
      btnExportEpisodeMp4.textContent = "重新导出 MP4";
    } else if (state === "failed") {
      btnExportEpisodeMp4.disabled = false;
      btnExportEpisodeMp4.textContent = "重新导出 MP4";
    }
  }

  async function pollEpisodeExportStatus(statusUrl) {
    try {
      var resp = await fetch(statusUrl);
      if (!resp.ok) {
        renderEpisodeExportStatus({ status: "failed", error_message: "状态查询失败" });
        stopEpisodeExportPolling();
        setEpisodeExportButtonState("failed");
        return;
      }
      var statusData = await resp.json();
      renderEpisodeExportStatus(statusData);

      if (statusData.status === "completed") {
        stopEpisodeExportPolling();
        setEpisodeExportButtonState("done");
        // Show download link
        var mp4Url = null;
        if (statusData.result && statusData.result.mp4_url) {
          mp4Url = statusData.result.mp4_url;
        } else if (currentEpisodeExportMp4Url) {
          mp4Url = currentEpisodeExportMp4Url;
        }
        if (mp4Url) {
          episodeExportDownload.href = mp4Url;
          episodeExportDownload.style.display = "inline-block";
        }
        // CP40.5: refresh export history
        loadEpisodeExportHistory();
      } else if (statusData.status === "failed") {
        stopEpisodeExportPolling();
        setEpisodeExportButtonState("failed");
      }
      // else: keep polling
    } catch (e) {
      renderEpisodeExportStatus({ status: "failed", error_message: "网络错误" });
      stopEpisodeExportPolling();
      setEpisodeExportButtonState("failed");
    }
  }

  function startEpisodeExportPolling(statusUrl) {
    stopEpisodeExportPolling();
    currentEpisodeExportPollTimer = setInterval(function () {
      pollEpisodeExportStatus(statusUrl);
    }, 1000);
  }

  // CP56: most recently generated real-TTS narration URL for the current episode
  var latestEpisodeTtsAudioUrl = null;

  // CP40.6 / CP56: Get current audio URL for episode export
  function getCurrentEpisodeAudioUrlForExport() {
    if (!checkEpisodeExportAudio || !checkEpisodeExportAudio.checked) return null;

    // CP56: prefer freshly generated real-TTS narration
    if (latestEpisodeTtsAudioUrl) return latestEpisodeTtsAudioUrl;

    // Fall back to currently loaded preview audio if it is a /outputs/ URL
    var audioEl = document.getElementById("preview-audio");
    if (!audioEl) return null;
    var src = audioEl.getAttribute("src");
    if (!src) return null;

    // Strip origin if browser expanded it
    try {
      var url = new URL(src, window.location.origin);
      if (url.origin !== window.location.origin) return null;
      if (!url.pathname.startsWith("/outputs/")) return null;
      return url.pathname;
    } catch (e) {
      return null;
    }
  }

  async function startEpisodeMp4Export() {
    // Guard: need a contract
    if (!latestEpisodeTemplateContract) {
      setStatus("请先生成合集预览，再导出 MP4", "error");
      setEpisodeExportButtonState("idle");
      return;
    }

    // CP40.7: Get style from explicit export style selector
    var exportStyleId = getCurrentEpisodeExportStyleId();

    // Guard: ensure selected style is supported (belt-and-suspenders since disabled options exist)
    var supportedStyleIds = (episodeExportCapabilities && episodeExportCapabilities.supported_styles
      ? episodeExportCapabilities.supported_styles.map(function (s) { return s.id; })
      : []);
    if (supportedStyleIds.length && !supportedStyleIds.includes(exportStyleId)) {
      setStatus("当前导出样式暂不支持 MP4 导出", "error");
      setEpisodeExportButtonState("idle");
      return;
    }

    // Stop any existing polling
    stopEpisodeExportPolling();

    // Get audio URL if checkbox is checked
    var audioUrl = getCurrentEpisodeAudioUrlForExport();

    // Update UI: set button to running, clear old state
    setEpisodeExportButtonState("running");
    episodeExportPanel.style.display = "block";
    episodeExportStatus.className = "episode-export-status is-pending";
    episodeExportStatus.textContent = "已加入导出队列...";
    episodeExportDownload.style.display = "none";
    episodeExportDownload.href = "#";

    setStatus(audioUrl ? "正在提交导出任务（含音频）..." : "正在提交导出任务...", "info");

    try {
      var resp = await fetch("/api/episode/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contract: latestEpisodeTemplateContract,
          style_id: exportStyleId,
          width: 720,
          height: 1280,
          fps: 30,
          audio_url: audioUrl,
        }),
      });

      var data = await resp.json();

      if (!resp.ok || data.status === "failed") {
        throw new Error(data.message || "导出任务创建失败");
      }

      // resp.status should be 202
      var exportId = data.export_id;
      var statusUrl = data.status_url;
      currentEpisodeExportId = exportId;
      currentEpisodeExportMp4Url = data.mp4_url || null;

      setStatus(audioUrl ? "导出任务已创建，正在生成 MP4（含音频）..." : "导出任务已创建，正在生成 MP4...", "info");

      // Start polling
      startEpisodeExportPolling(statusUrl);

    } catch (e) {
      renderEpisodeExportStatus({ status: "failed", error_message: e.message });
      setEpisodeExportButtonState("failed");
      setStatus("导出失败：" + e.message, "error");
    }
  }

  // CP56: Generate real TTS narration for the current episode contract
  async function generateEpisodeTts() {
    var statusEl = document.getElementById("episode-tts-status");
    var audioEl = document.getElementById("episode-tts-audio");
    var scriptWrap = document.getElementById("episode-tts-script-wrap");
    var scriptEl = document.getElementById("episode-tts-script");
    var btn = document.getElementById("btn-generate-episode-tts");

    if (!latestEpisodeTemplateContract) {
      if (statusEl) { statusEl.className = "episode-tts-status is-error"; statusEl.textContent = "请先生成合集预览，再生成口播"; }
      return;
    }

    if (btn) { btn.disabled = true; }
    if (statusEl) { statusEl.className = "episode-tts-status is-pending"; statusEl.textContent = "正在用 MiniMax 合成真实口播，请稍候…"; }
    setStatus("正在生成真实口播音频…", "info");

    try {
      var resp = await fetch("/api/episode/tts-audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract: latestEpisodeTemplateContract }),
      });
      var data = await resp.json();
      if (!resp.ok || data.status === "failed") {
        throw new Error(data.message || "口播生成失败");
      }

      latestEpisodeTtsAudioUrl = data.audio_url;

      // Load into the inline player so the user can hear it immediately
      if (audioEl) {
        audioEl.src = data.audio_url;
        audioEl.style.display = "block";
        audioEl.load();
      }
      // Show the script
      if (scriptEl && scriptWrap) {
        scriptEl.textContent = data.script || "";
        scriptWrap.style.display = "block";
      }
      // Auto-enable "export with audio"
      if (checkEpisodeExportAudio) { checkEpisodeExportAudio.checked = true; }

      var dur = data.duration ? data.duration.toFixed(1) + "s" : "";
      var voice = data.voice || data.provider || "";
      if (statusEl) {
        statusEl.className = "episode-tts-status is-ok";
        statusEl.textContent = "✅ 口播已生成（" + dur + (voice ? " · " + voice : "") + "），已自动勾选随 MP4 导出";
      }
      setStatus("真实口播已生成，可试听或直接导出 MP4", "success");
    } catch (e) {
      latestEpisodeTtsAudioUrl = null;
      if (statusEl) { statusEl.className = "episode-tts-status is-error"; statusEl.textContent = "口播生成失败：" + e.message; }
      setStatus("口播生成失败：" + e.message, "error");
    } finally {
      if (btn) { btn.disabled = false; }
    }
  }

  var btnGenerateEpisodeTts = document.getElementById("btn-generate-episode-tts");
  if (btnGenerateEpisodeTts) {
    btnGenerateEpisodeTts.addEventListener("click", function () {
      generateEpisodeTts();
    });
  }

  // CP59: build an episode template contract from the current selection (1 or N).
  // Returns the contract (also caches it in latestEpisodeTemplateContract) or null.
  function buildCurrentEpisodeContractFromSelection() {
    if (episodeItemList.length === 0) return null;
    var plan = buildEpisodePlan();
    if (!validateEpisodePlan(plan).ok) return null;
    var script = buildEpisodeScriptFromPlan(plan);
    if (!validateEpisodeScript(script).ok) return null;
    var manifest = buildEpisodeAudioManifestFromScript(script);
    if (!validateEpisodeAudioManifest(manifest).ok) return null;
    var renderIr = buildEpisodeRenderIrFromContracts(plan, script, manifest);
    if (!validateEpisodeRenderIr(renderIr).ok) return null;
    var contract = buildEpisodeTemplateContract(renderIr);
    if (!validateEpisodeTemplateContract(contract).ok) return null;
    latestEpisodeTemplateContract = contract;
    return contract;
  }

  // CP59: single rendering path — render a contract+style via the server (the SAME
  // Python renderer used for MP4 export) and load it into the preview iframe.
  // persist=false → ephemeral live preview; persist=true → saved artifact (history).
  async function loadStyledPreview(contract, styleId, opts) {
    opts = opts || {};
    var resp = await fetch("/api/episode/preview-html", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contract: contract, style_id: styleId, persist: !!opts.persist }),
    });
    var data = await resp.json();
    if (!resp.ok || !data.ok) {
      throw new Error(data.error || "预览渲染失败");
    }
    previewHtml.src = data.path + "?t=" + Date.now();
    switchToPreviewTab();
    setPreviewMode("html");
    if (typeof setTabEmptyState === "function") setTabEmptyState("preview", false);
    return data;
  }

  // CP59: preview the SELECTED export style — pixel-identical to the exported MP4.
  async function previewExportStyle() {
    if (episodeItemList.length === 0) {
      setStatus("请先在候选中选择新闻（选 1 条=单条，选多条=合集）", "error");
      return;
    }
    var contract = buildCurrentEpisodeContractFromSelection();
    if (!contract) {
      setStatus("无法生成预览契约，请检查所选新闻", "error");
      return;
    }
    setStatus("正在渲染所选风格预览…", "info");
    try {
      await loadStyledPreview(contract, getCurrentEpisodeExportStyleId());
      if (autoPreviewBanner) {
        autoPreviewBanner.style.display = "block";
        var n = episodeItemList.length;
        autoPreviewBanner.textContent = "风格预览（" + (n === 1 ? "单条" : n + " 条合集") + "）· 与导出一致";
      }
      setStatus("已渲染所选风格预览，效果与导出 MP4 一致", "success");
    } catch (e) {
      setStatus("预览失败：" + e.message, "error");
    }
  }

  var btnPreviewEpisodeStyle = document.getElementById("btn-preview-episode-style");
  if (btnPreviewEpisodeStyle) {
    btnPreviewEpisodeStyle.addEventListener("click", function () {
      previewExportStyle();
    });
  }

  // Wire up the export button
  if (btnExportEpisodeMp4) {
    btnExportEpisodeMp4.addEventListener("click", function () {
      startEpisodeMp4Export();
    });
  }

  // Wire up export history buttons
  if (btnRefreshEpisodeExports) {
    btnRefreshEpisodeExports.addEventListener("click", function () {
      loadEpisodeExportHistory();
    });
  }

  if (btnCleanupEpisodeExports) {
    btnCleanupEpisodeExports.addEventListener("click", function () {
      cleanupEpisodeExports();
    });
  }

  // CP40.5: Episode export history functions
  async function loadEpisodeExportHistory() {
    try {
      var resp = await fetch("/api/episode/exports?limit=50");
      var data = await resp.json();
      if (!data.ok) {
        if (episodeExportHistoryListEl) {
          episodeExportHistoryListEl.innerHTML = '<div class="episode-export-history-empty">加载失败</div>';
        }
        return;
      }
      episodeExportHistoryPanel.style.display = "block";
      renderEpisodeExportHistory(data.items || []);
    } catch (e) {
      if (episodeExportHistoryListEl) {
        episodeExportHistoryListEl.innerHTML = '<div class="episode-export-history-empty">加载失败</div>';
      }
    }
  }

  function renderEpisodeExportHistory(items) {
    if (!episodeExportHistoryListEl) return;

    if (!items || items.length === 0) {
      episodeExportHistoryListEl.innerHTML = '<div class="episode-export-history-empty">暂无导出记录</div>';
      return;
    }

    var html = "";
    items.forEach(function (item) {
      var exportId = item.export_id || "";
      var shortId = exportId.replace("episode_export_", "").slice(-8);
      var status = item.status || "unknown";
      var sizeBytes = item.mp4_size_bytes || 0;
      var sizeStr = formatBytes(sizeBytes);
      var updatedAt = item.updated_at || item.created_at || "";
      var shortTime = updatedAt ? updatedAt.slice(0, 16).replace("T", " ") : "";

      var statusClass = status;
      var statusLabel = status;
      if (status === "completed") statusLabel = "已完成";
      else if (status === "failed") statusLabel = "失败";
      else if (status === "running") statusLabel = "导出中";
      else if (status === "pending") statusLabel = "等待中";
      else statusLabel = "未知";

      var mp4Url = item.mp4_url || "#";
      var htmlUrl = item.html_url || "#";

      var canDelete = status !== "running" && status !== "pending";

      html += '<div class="episode-export-history-item" data-export-id="' + exportId + '">';
      html += '<div class="episode-export-history-main">';
      html += '<span class="episode-export-history-id">' + shortId + '</span>';
      html += '<span class="episode-export-history-status ' + statusClass + '">' + statusLabel + '</span>';
      html += '<span class="episode-export-history-size">' + sizeStr + '</span>';
      if (shortTime) html += '<span class="episode-export-history-size">' + shortTime + '</span>';
      html += '</div>';
      html += '<div class="episode-export-history-actions">';
      if (item.has_mp4) {
        html += '<a href="' + mp4Url + '" target="_blank" rel="noopener">打开 MP4</a>';
      }
      if (item.has_html) {
        html += '<a href="' + htmlUrl + '" target="_blank" rel="noopener">打开 HTML</a>';
      }
      if (canDelete) {
        html += '<button class="btn-delete-export" data-export-id="' + exportId + '">删除</button>';
      }
      html += '</div>';
      html += '</div>';
    });

    episodeExportHistoryListEl.innerHTML = html;

    // Wire up delete buttons
    episodeExportHistoryListEl.querySelectorAll(".btn-delete-export").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var eid = btn.getAttribute("data-export-id");
        if (eid) deleteEpisodeExport(eid);
      });
    });
  }

  async function deleteEpisodeExport(exportId) {
    if (!confirm("确定删除这个导出吗？")) return;
    try {
      var resp = await fetch("/api/episode/exports/" + exportId, { method: "DELETE" });
      var data = await resp.json();
      if (!data.ok) {
        setStatus("删除失败：" + (data.error || "未知错误"), "error");
        return;
      }
      setStatus("导出已删除", "info");
      loadEpisodeExportHistory();
    } catch (e) {
      setStatus("删除失败：" + e.message, "error");
    }
  }

  async function cleanupEpisodeExports() {
    if (!confirm("将保留最近 30 个导出，删除更旧的已完成/失败导出。确定继续？")) return;
    try {
      var resp = await fetch("/api/episode/exports/cleanup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keep_latest: 30, dry_run: false }),
      });
      var data = await resp.json();
      if (!data.ok) {
        setStatus("清理失败：" + (data.error || "未知错误"), "error");
        return;
      }
      var count = data.deleted_count || 0;
      setStatus("已清理 " + count + " 个旧导出", "info");
      loadEpisodeExportHistory();
    } catch (e) {
      setStatus("清理失败：" + e.message, "error");
    }
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "—";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  // CP41.3: First-run guide collapse button
  function initFirstRunGuide() {
    if (!firstRunGuide || !btnCollapseFirstRunGuide) return;

    var collapsed = localStorage.getItem("chalk_first_run_guide_collapsed") === "1";
    firstRunGuide.classList.toggle("is-collapsed", collapsed);
    btnCollapseFirstRunGuide.textContent = collapsed ? "展开引导" : "收起引导";

    btnCollapseFirstRunGuide.addEventListener("click", function () {
      var nextCollapsed = !firstRunGuide.classList.contains("is-collapsed");
      firstRunGuide.classList.toggle("is-collapsed", nextCollapsed);
      localStorage.setItem("chalk_first_run_guide_collapsed", nextCollapsed ? "1" : "0");
      btnCollapseFirstRunGuide.textContent = nextCollapsed ? "展开引导" : "收起引导";
    });
  }

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

    // CP41.3: Init first-run guide collapse state
    initFirstRunGuide();

    // CP32: Load episode HTML artifact history
    loadEpisodeHtmlHistory();

    // CP40.5: Load episode export history
    loadEpisodeExportHistory();

    // CP40.7.1: Load episode export capabilities for style picker
    loadEpisodeExportCapabilities();

    // CP41.2.1: Ensure initial active preview tab shows an empty state
    updateTabEmptyState("preview");

    // CP48: Initialize production workflow panel
    renderProductionWorkflowPanel();
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

      // CP57: surface fallback notice (sample candidates loaded) without looking like a hard error
      if (data.fallback && data.note) {
        hotNewsError.style.display = "block";
        hotNewsError.textContent = "ℹ️ " + data.note;
        hotNewsError.style.color = "#fbbf24";
        hotNewsError.style.borderColor = "#78600f";
      } else {
        hotNewsError.style.display = "none";
        hotNewsError.style.color = "";
        hotNewsError.style.borderColor = "";
      }
    } catch (e) {
      hotNewsError.style.display = "block";
      hotNewsError.style.color = "";
      hotNewsError.style.borderColor = "";
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
      div.className = isInEpisode ? "hot-news-item selected" : "hot-news-item";
      div.setAttribute("data-index", index);

      // CP57: unified single-select pool — one toggle per card, no dual buttons
      const pickBtnClass = isInEpisode ? "hot-news-item-pick-btn is-picked" : "hot-news-item-pick-btn";
      const pickBtnText = isInEpisode ? "✓ 已选入" : "＋ 选入视频";

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
          '<button class="' + pickBtnClass + '" type="button" data-episode-item-id="' + (item.id || "") + '">' + pickBtnText + '</button>' +
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

      // CP57: clicking the card or the toggle adds/removes from the unified pool
      function togglePick(ev) {
        if (ev) ev.stopPropagation();
        if (episodeItemList.some(function (e) { return e.id === item.id; })) {
          removeNewsFromEpisode(item.id);
        } else {
          addNewsToEpisode(item);
        }
      }
      div.querySelector(".hot-news-item-pick-btn").addEventListener("click", togglePick);
      div.addEventListener("click", togglePick);

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
    syncSelectionFromPool();
    renderEpisodePlanner();
    renderHotNews(); // Update toggle button states
  }

  function removeNewsFromEpisode(id) {
    episodeItemList = episodeItemList.filter(function (e) { return e.id !== id; });
    syncSelectionFromPool();
    renderEpisodePlanner();
    renderHotNews(); // Update toggle button states
  }

  // CP57: keep legacy single-news state derived from the unified pool.
  // 1 selected = single video; N selected = collection. selectedNews stays as the
  // lead item so the single-news pipeline and style recommendations keep working.
  function syncSelectionFromPool() {
    selectedNews = episodeItemList.length ? episodeItemList[0] : null;
    if (hotNewsSelected && selectedNewsTitleEl) {
      if (episodeItemList.length === 0) {
        hotNewsSelected.style.display = "none";
      } else {
        hotNewsSelected.style.display = "block";
        var label = episodeItemList.length === 1
          ? "单条视频：" + (episodeItemList[0].title || "")
          : episodeItemList.length + " 条合集（" + (episodeItemList[0].title || "") + " …）";
        selectedNewsTitleEl.textContent = label;
      }
    }
    updateStyleRecommendations();
    updateGenModeUI();
    updateGenerationPlan();
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

    var _n = episodeItemList.length;
    episodeCount.textContent = _n === 0 ? "未选" : (_n === 1 ? "单条视频" : _n + " 条 · 合集");

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

    // CP41.2: Hide empty state
    setTabEmptyState("episode_plan", false);

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

    // CP41.2: Hide empty state
    setTabEmptyState("episode_script", false);

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

    // CP41.2: Hide empty state
    setTabEmptyState("audio_manifest", false);

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

    // CP41.2: Hide empty state
    setTabEmptyState("visual_plan", false);

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

  // CP59: save the current selection's HTML using the SAME server renderer as export.
  async function saveMockEpisodeHtml() {
    if (episodeItemList.length === 0) {
      setStatus("请先选择新闻，再保存 HTML", "error");
      return;
    }
    var contract = buildCurrentEpisodeContractFromSelection();
    if (!contract) {
      setStatus("无法生成契约，请检查所选新闻", "error");
      return;
    }
    var styleId = getCurrentEpisodeExportStyleId();
    setStatus("正在渲染并保存 HTML...", "info");
    try {
      var data = await loadStyledPreview(contract, styleId, { persist: true });

      latestEpisodeHtmlArtifact = {
        path: data.path,
        file_path: data.file_path,
        created_at: data.created_at,
      };

      if (autoPreviewBanner) {
        autoPreviewBanner.style.display = "block";
        autoPreviewBanner.textContent = "已保存的 HTML 预览（" + styleId + "）";
      }

      // Show open and download links (no absolute paths)
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

      // Refresh history so the new artifact appears immediately
      loadEpisodeHtmlHistory();

      setStatus("HTML 已保存到历史", "success");
    } catch (e) {
      setStatus("保存失败：" + e.message, "error");
    }
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

  // CP59: "预览画面" now renders the selected style via the same Python renderer
  // as MP4 export, so preview == export (single style picker).
  var btnPreviewEpisode = document.getElementById("btn-preview-episode");
  if (btnPreviewEpisode) {
    btnPreviewEpisode.addEventListener("click", function () {
      previewExportStyle();
    });
  }

  // CP31: Save mock episode HTML button
  var btnSaveEpisodeHtml = document.getElementById("btn-save-episode-html");
  if (btnSaveEpisodeHtml) {
    btnSaveEpisodeHtml.addEventListener("click", function () {
      saveMockEpisodeHtml();
    });
  }

  // CP35: Episode preview style selector — also update export style hint (CP40.7)
  if (selectEpisodePreviewStyle) {
    selectEpisodePreviewStyle.addEventListener("change", function () {
      currentEpisodePreviewStyle = selectEpisodePreviewStyle.value || "timeline_daily_v1";
      updateEpisodeExportStyleHint();
    });
  }

  // CP40.7.1: Episode export style selector change — update hint when user picks a different export style
  if (selectEpisodeExportStyle) {
    selectEpisodeExportStyle.addEventListener("change", function () {
      updateEpisodeExportStyleHint();
    });
  }

  // CP40.7: Load export capabilities and populate the style picker
  loadEpisodeExportCapabilities();

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

      // CP41.2: Update empty state based on whether content already exists
      updateTabEmptyState(tabId);
    });
  });

  // CP41.2.2: Check whether the preview tab has actual content loaded
  function hasPreviewContent() {
    var htmlSrc = previewHtml ? previewHtml.getAttribute("src") : "";
    var videoSrc = previewVideo ? previewVideo.getAttribute("src") : "";

    return Boolean(
      (htmlSrc && htmlSrc !== "about:blank") ||
      (videoSrc && videoSrc !== "about:blank")
    );
  }

  // CP41.2: Update empty state visibility based on existing content
  function updateTabEmptyState(tabId) {
    var contentElMap = {
      "episode_plan": document.getElementById("json-episode_plan"),
      "episode_script": document.getElementById("json-episode_script"),
      "audio_manifest": document.getElementById("json-audio_manifest"),
      "visual_plan": document.getElementById("json-visual_plan"),
      "render_ir": document.getElementById("json-render_ir"),
      "semantic_ir": document.getElementById("json-semantic_ir"),
      "dialogue_script": document.getElementById("json-dialogue_script"),
    };
    var emptyElMap = {
      "preview": previewEmptyState,
      "episode_plan": episodePlanEmpty,
      "episode_script": episodeScriptEmpty,
      "audio_manifest": audioManifestEmpty,
      "visual_plan": visualPlanEmpty,
    };

    var emptyEl = emptyElMap[tabId];
    if (!emptyEl) return;

    var hasContent = false;

    if (tabId === "preview") {
      // CP41.2.2: Preview content lives in iframe src or video src, not textContent
      hasContent = hasPreviewContent();
    } else {
      var contentEl = contentElMap[tabId];
      hasContent = contentEl && contentEl.textContent && contentEl.textContent.trim().length > 0;
    }

    emptyEl.style.display = hasContent ? "none" : "block";
  }

  // CP41.2: Empty state helper
  function setTabEmptyState(tabId, isEmpty) {
    var map = {
      "preview": previewEmptyState,
      "episode_plan": episodePlanEmpty,
      "episode_script": episodeScriptEmpty,
      "audio_manifest": audioManifestEmpty,
      "visual_plan": visualPlanEmpty,
      "history": historyEmptyState,
    };
    var el = map[tabId];
    if (el) {
      el.style.display = isEmpty ? "block" : "none";
    }
  }

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
        // CP41.2: Show history empty state
        if (historyEmptyState) historyEmptyState.style.display = "block";
        return;
      }

      const items = data.items || [];

      if (items.length === 0) {
        historyList.innerHTML = '<div class="history-empty">暂无历史作品</div>';
        // CP41.2: Show history empty state
        if (historyEmptyState) historyEmptyState.style.display = "block";
        return;
      }

      historyList.innerHTML = "";
      // CP41.2: Hide history empty state
      if (historyEmptyState) historyEmptyState.style.display = "none";

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
      // CP41.2: Show history empty state
      if (historyEmptyState) historyEmptyState.style.display = "block";
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
    // CP41.2.1: Hide preview empty state when content is shown from history
    setTabEmptyState("preview", false);
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
    // CP41.2: Show preview empty state when cleared
    setTabEmptyState("preview", true);
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

    // CP41.2: Hide preview empty state when content is shown
    setTabEmptyState("preview", false);

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

  // ---------- CP43: Source contract functions ----------

  function setSourceContractStatus(message, type) {
    if (!sourceContractStatus) return;
    sourceContractStatus.textContent = message || "";
    sourceContractStatus.className = "source-contract-status " + (type || "");
  }

  // CP59: show a source-generated contract via the server renderer (same as export).
  function showSourceContractPreview(contract) {
    if (!contract) return;
    // Store as the current episode template contract so export can use it
    latestEpisodeTemplateContract = contract;
    latestEpisodeTtsAudioUrl = null;  // CP56: invalidate stale narration on new preview
    loadStyledPreview(contract, getCurrentEpisodeExportStyleId()).catch(function (e) {
      setStatus("预览失败：" + e.message, "error");
    });
  }

  // CP43.1: Render the source contract result inspector
  function renderSourceContractInspector(data) {
    if (!sourceContractInspector) return;

    var newsItems = data.news_items || [];
    var episodeItems = data.episode_items || [];
    var contract = data.contract || {};
    var episode = contract.episode || {};

    sourceContractInspector.style.display = "block";

    if (sourceContractInspectorSummary) {
      sourceContractInspectorSummary.textContent =
        "source_type: " + (data.source_type || "-") +
        " · news_items: " + newsItems.length +
        " · episode_items: " + episodeItems.length +
        " · schema: " + (contract.schema_version || "-") +
        " · title: " + (episode.title || "-");
    }

    renderSourceEpisodeItems(episodeItems);
    renderSourceNewsItems(newsItems);
  }

  // CP43.1: Render episode_items (selected news for the episode)
  function renderSourceEpisodeItems(items) {
    if (!sourceEpisodeItemsList) return;

    if (!items || items.length === 0) {
      sourceEpisodeItemsList.innerHTML = '<div class="source-contract-empty">暂无入选新闻</div>';
      return;
    }

    sourceEpisodeItemsList.innerHTML = "";

    items.forEach(function (item) {
      var div = document.createElement("div");
      div.className = "source-episode-item" + (item.role === "lead" ? " is-lead" : "");

      var roleLabel = item.role === "lead" ? "主线" : "补充";
      var tags = (item.tags || []).slice(0, 4).map(function (tag) {
        return '<span class="source-tag">#' + escapeHtml(String(tag)) + '</span>';
      }).join("");

      // CP44: URL and trust level
      var urlHtml = "";
      if (item.url) {
        urlHtml = '<div class="source-item-url"><a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener">来源链接</a></div>';
      }
      var trustLevel = item.trust_level || "unknown";
      var trustBadgeClass = "source-trust-badge " + trustLevel;
      var trustLabel = trustLevel === "official" ? "官方" : trustLevel === "research" ? "研究" : trustLevel === "manual" ? "手动" : "未知";

      div.innerHTML =
        '<div class="source-item-topline">' +
          '<span class="source-role-badge">' + roleLabel + '</span>' +
          '<span class="' + trustBadgeClass + '">' + trustLabel + '</span>' +
          '<span class="source-score">score ' + escapeHtml(String(item.final_score || 0)) + '</span>' +
        '</div>' +
        urlHtml +
        '<div class="source-item-title">' + escapeHtml(item.title || "") + '</div>' +
        '<div class="source-item-summary">' + escapeHtml(item.summary || "") + '</div>' +
        '<div class="source-item-meta">' +
          escapeHtml(item.source || "Manual") +
          ' · ' + escapeHtml(String(item.points || 0)) + ' points' +
          ' · ' + escapeHtml(String(item.comments || 0)) + ' comments' +
        '</div>' +
        '<div class="source-tags">' + tags + '</div>';

      sourceEpisodeItemsList.appendChild(div);
    });
  }

  // CP43.1: Render news_items (raw news from source pipeline)
  function renderSourceNewsItems(items) {
    if (!sourceNewsItemsList) return;

    if (!items || items.length === 0) {
      sourceNewsItemsList.innerHTML = '<div class="source-contract-empty">暂无原始新闻项</div>';
      return;
    }

    sourceNewsItemsList.innerHTML = "";

    items.forEach(function (item) {
      var div = document.createElement("div");
      div.className = "source-news-item";

      var tags = (item.tags || []).slice(0, 4).map(function (tag) {
        return '<span class="source-tag">#' + escapeHtml(String(tag)) + '</span>';
      }).join("");

      // CP44: URL and trust level
      var urlHtml = "";
      if (item.url) {
        urlHtml = '<div class="source-item-url"><a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener">来源链接</a></div>';
      }
      var trustLevel = item.trust_level || "unknown";
      var trustBadgeClass = "source-trust-badge " + trustLevel;
      var trustLabel = trustLevel === "official" ? "官方" : trustLevel === "research" ? "研究" : trustLevel === "manual" ? "手动" : "未知";

      div.innerHTML =
        urlHtml +
        '<div class="source-item-title">' + escapeHtml(item.title || "") + '</div>' +
        '<div class="source-item-meta">' +
          '<span class="' + trustBadgeClass + '">' + trustLabel + '</span>' +
          ' ' + escapeHtml(item.source || "Manual") +
          ' · score ' + escapeHtml(String(item.final_score || 0)) +
          ' · ' + escapeHtml(item.source_type || "-") +
        '</div>' +
        '<div class="source-tags">' + tags + '</div>';

      sourceNewsItemsList.appendChild(div);
    });
  }

  // CP43.1: Apply source contract episode_items to the Episode Planner
  function applySourceContractToPlanner() {
    if (!latestSourceEpisodeItems || latestSourceEpisodeItems.length === 0) {
      setSourceContractStatus("没有可应用到合集的栏目新闻", "error");
      return;
    }

    // Map CP42 source pipeline items into the existing episodeItemList shape.
    episodeItemList = latestSourceEpisodeItems.map(function (item) {
      return {
        id: item.id || ("source_" + String(item.order || "")),
        title: item.title || item.headline || "",
        summary: item.summary || item.description || "",
        source: item.source || "Source Pipeline",
        url: item.url || "",
        points: item.points || 0,
        comments: item.comments || 0,
        final_score: item.final_score || 0,
        rank_reason: item.role === "lead" ? "CP42 source pipeline lead item" : "CP42 source pipeline supporting item",
        role: item.role || "supporting",
        tags: item.tags || [],
      };
    });

    // Reset derived planner outputs so they are rebuilt from the applied items.
    latestEpisodePlan = null;
    latestEpisodeScript = null;
    latestEpisodeAudioManifest = null;
    latestEpisodeRenderIr = null;

    // Refresh the Episode Planner UI
    if (typeof renderEpisodePlanner === "function") {
      renderEpisodePlanner();
    }

    // CP48: Update production workflow panel
    renderProductionWorkflowPanel();

    setSourceContractStatus(
      "已应用 " + episodeItemList.length + " 条新闻到当前合集。现在可以继续使用左侧「规划 / 预览 / 导出」。",
      "success"
    );
  }

  // CP45: Fetch article from URL and auto-fill title/summary
  async function fetchArticleIntoUrlForm() {
    var url = sourceUrlInput.value.trim();
    if (!url) {
      setSourceContractStatus("请先输入 URL", "error");
      return;
    }

    setSourceContractStatus("正在抽取 URL 内容...", "info");

    try {
      var resp = await fetch("/api/article/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      });
      var data = await resp.json();
      if (!data.ok) {
        setSourceContractStatus("抽取失败：" + (data.error || "未知错误") + "。可以手动填写标题和摘要。", "error");
        return;
      }

      var article = data.article || {};
      if (sourceUrlTitle && article.title) {
        sourceUrlTitle.value = article.title;
      }
      if (sourceUrlSummary && article.description) {
        sourceUrlSummary.value = article.description;
      }

      setSourceContractStatus('已抽取标题和摘要，请确认后点击"从 URL 生成栏目"。', "success");
    } catch (e) {
      setSourceContractStatus("抽取失败：" + e.message + "。可以手动填写标题和摘要。", "error");
    }
  }

  // CP44: Load reliable sources from API and populate the select dropdown
  async function loadReliableSources() {
    try {
      var resp = await fetch("/api/reliable-sources");
      var data = await resp.json();
      if (data.ok && data.items) {
        reliableSources = data.items;
        renderReliableSourceOptions(reliableSources);
      }
    } catch (e) {
      // Silently fail — the select will just show the default option
    }
  }

  function renderReliableSourceOptions(items) {
    if (!sourceUrlSourceSelect) return;
    // Keep the first default option
    sourceUrlSourceSelect.innerHTML = '<option value="">自动识别 / 手动来源</option>';
    items.forEach(function (source) {
      var opt = document.createElement("option");
      opt.value = source.id;
      opt.textContent = source.name + " (" + source.trust_level + ")";
      sourceUrlSourceSelect.appendChild(opt);
    });
  }

  async function buildSourceContract(payload) {
    setSourceContractStatus("正在生成...", "info");
    try {
      var resp = await fetch("/api/episode/source-contract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      var data = await resp.json();
      if (!data.ok) {
        setSourceContractStatus("生成失败：" + (data.error || "未知错误"), "error");
        return;
      }
      // Store results
      latestSourceContract = data.contract;
      latestSourceNewsItems = data.news_items || [];
      latestSourceEpisodeItems = data.episode_items || [];
      var newsCount = latestSourceNewsItems.length;
      var itemCount = latestSourceEpisodeItems.length;
      var sourceLabel = (function () {
        if (payload.source_type === "sample_pack") return "样例新闻包";
        if (payload.source_type === "inline_text") return "粘贴文本";
        if (payload.source_type === "url_input") return "可靠 URL";
        if (payload.source_type === "url_fetch") return "URL 抽取";
        if (payload.source_type === "manual_items") return "手动新闻项";
        return payload.source_type || "新闻源";
      })();
      setSourceContractStatus(
        "已从" + sourceLabel + "生成 " + newsCount + " 条新闻，并生成 episode_template_v1 contract。可在右侧预览，也可以导出 MP4。",
        "success"
      );
      // Show preview
      showSourceContractPreview(data.contract);
      // CP43.1: Also show the result inspector
      renderSourceContractInspector(data);
      // CP48: Update production workflow panel
      renderProductionWorkflowPanel();
    } catch (e) {
      setSourceContractStatus("生成失败：" + e.message, "error");
    }
  }

  // ---------- CP46: URL Draft Basket functions ----------

  function createUrlDraftId() {
    return "url_draft_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 7);
  }

  function addUrlDraft(url) {
    url = (url || "").trim();
    if (!url) {
      setSourceContractStatus("请先输入要加入草稿篮的 URL", "error");
      return;
    }
    if (urlDraftItems.length >= MAX_URL_DRAFT_ITEMS) {
      setSourceContractStatus("URL 草稿篮最多支持 " + MAX_URL_DRAFT_ITEMS + " 条", "error");
      return;
    }
    if (urlDraftItems.some(function (item) { return item.url === url; })) {
      setSourceContractStatus("该 URL 已在草稿篮中", "error");
      return;
    }

    urlDraftItems.push({
      id: createUrlDraftId(),
      url: url,
      title: "",
      summary: "",
      source_id: sourceUrlSourceSelect ? (sourceUrlSourceSelect.value || "") : "",
      source: "",
      final_score: 0,
      tags: [],
      status: "draft",
      error: ""
    });

    if (urlDraftNewUrl) urlDraftNewUrl.value = "";
    renderUrlDraftBasket();
    renderProductionWorkflowPanel();
    setSourceContractStatus("已加入 URL 草稿，可逐条抽取或手动填写标题摘要", "success");
  }

  function removeUrlDraft(id) {
    urlDraftItems = urlDraftItems.filter(function (item) { return item.id !== id; });
    renderUrlDraftBasket();
    renderProductionWorkflowPanel();
  }

  function clearUrlDrafts() {
    urlDraftItems = [];
    renderUrlDraftBasket();
    renderProductionWorkflowPanel();
    setSourceContractStatus("已清空 URL 草稿篮", "info");
  }

  function renderUrlDraftBasket() {
    if (!urlDraftList) return;

    if (!urlDraftItems.length) {
      urlDraftList.innerHTML = '<div class="source-contract-empty">暂无 URL 草稿</div>';
      return;
    }

    urlDraftList.innerHTML = "";

    urlDraftItems.forEach(function (item) {
      var card = document.createElement("div");
      card.className = "url-draft-card url-draft-status-" + item.status;
      card.setAttribute("data-id", item.id);

      card.innerHTML =
        '<div class="url-draft-card-head">' +
          '<div class="url-draft-url">' + escapeHtml(item.url) + '</div>' +
          '<span class="url-draft-status">' + escapeHtml(item.status) + '</span>' +
        '</div>' +
        '<label class="source-contract-label">标题</label>' +
        '<input class="source-url-input url-draft-title-input" type="text" value="' + escapeHtml(item.title || "") + '" placeholder="新闻标题" />' +
        '<label class="source-contract-label">摘要</label>' +
        '<textarea class="source-inline-text url-draft-summary-input" rows="2" placeholder="新闻摘要">' + escapeHtml(item.summary || "") + '</textarea>' +
        (item.error ? '<div class="url-draft-error">' + escapeHtml(item.error) + '</div>' : '') +
        '<div class="url-draft-actions">' +
          '<button class="btn-small url-draft-extract-btn" type="button">抽取</button>' +
          '<button class="btn-small url-draft-remove-btn" type="button">移除</button>' +
        '</div>';

      var titleInput = card.querySelector(".url-draft-title-input");
      var summaryInput = card.querySelector(".url-draft-summary-input");

      titleInput.addEventListener("input", function () {
        item.title = titleInput.value;
        if (item.title.trim()) {
          item.status = "ready";
          item.error = "";
        } else if (item.status === "ready") {
          item.status = "draft";
        }
        renderProductionWorkflowPanel();
      });

      summaryInput.addEventListener("input", function () {
        item.summary = summaryInput.value;
        renderProductionWorkflowPanel();
      });

      card.querySelector(".url-draft-extract-btn").addEventListener("click", function () {
        extractUrlDraft(item.id);
      });

      card.querySelector(".url-draft-remove-btn").addEventListener("click", function () {
        removeUrlDraft(item.id);
      });

      urlDraftList.appendChild(card);
    });
  }

  async function extractUrlDraft(id) {
    var item = urlDraftItems.find(function (x) { return x.id === id; });
    if (!item) return;

    item.status = "extracting";
    item.error = "";
    renderUrlDraftBasket();

    try {
      var resp = await fetch("/api/article/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: item.url })
      });
      var data = await resp.json();

      if (!data.ok) {
        item.status = "failed";
        item.error = data.error || "抽取失败";
        renderUrlDraftBasket();
        renderProductionWorkflowPanel();
        return;
      }

      var article = data.article || {};
      item.title = article.title || item.title || "";
      item.summary = article.description || item.summary || article.body_text || "";
      if (item.summary.length > 500) item.summary = item.summary.slice(0, 500);
      item.status = item.title ? "ready" : "failed";
      item.error = item.title ? "" : "未抽取到标题，请手动填写";
      renderUrlDraftBasket();
      renderProductionWorkflowPanel();
    } catch (e) {
      item.status = "failed";
      item.error = e.message;
      renderUrlDraftBasket();
      renderProductionWorkflowPanel();
    }
  }

  function buildContractFromUrlDrafts() {
    if (!urlDraftItems.length) {
      setSourceContractStatus("请先添加 URL 草稿", "error");
      return;
    }

    var readyItems = urlDraftItems.filter(function (item) {
      return item.title && item.title.trim();
    });

    if (!readyItems.length) {
      setSourceContractStatus("至少需要 1 条带标题的 URL 草稿", "error");
      return;
    }

    var manualItems = readyItems.slice(0, MAX_URL_DRAFT_ITEMS).map(function (item, index) {
      return {
        id: item.id,
        title: item.title.trim(),
        summary: (item.summary || "").trim(),
        source: "URL Draft",
        url: item.url,
        final_score: 7.0 + Math.max(0, 4 - index) * 0.2,
        points: 0,
        comments: 0,
        tags: ["url", "draft"]
      };
    });

    buildSourceContract({
      source_type: "manual_items",
      items: manualItems,
      limit: Math.min(manualItems.length, MAX_URL_DRAFT_ITEMS),
      template_id: "breaking_news_v1",
      episode_title: "URL 草稿快讯",
      episode_subtitle: "多来源 URL 汇总生成"
    });
  }

  // ---------- CP47: Source Collection functions ----------

  function createSourceCollectionId() {
    return "source_collection_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 7);
  }

  function cloneUrlDraftItem(item) {
    return {
      id: item.id || createUrlDraftId(),
      url: item.url || "",
      title: item.title || "",
      summary: item.summary || "",
      source_id: item.source_id || "",
      source: item.source || "",
      final_score: Number(item.final_score || 0),
      tags: Array.isArray(item.tags) ? item.tags.slice(0, 10) : [],
      status: item.status || "draft",
      error: item.error || ""
    };
  }

  function loadSourceCollections() {
    try {
      var raw = localStorage.getItem(SOURCE_COLLECTION_STORAGE_KEY);
      if (!raw) {
        sourceCollections = [];
        return;
      }
      var parsed = JSON.parse(raw);
      sourceCollections = Array.isArray(parsed) ? parsed.slice(0, MAX_SOURCE_COLLECTIONS) : [];
    } catch (e) {
      sourceCollections = [];
    }
  }

  function persistSourceCollections() {
    try {
      localStorage.setItem(
        SOURCE_COLLECTION_STORAGE_KEY,
        JSON.stringify(sourceCollections.slice(0, MAX_SOURCE_COLLECTIONS))
      );
    } catch (e) {
      setSourceContractStatus("保存来源集合失败：" + e.message, "error");
    }
  }

  function saveCurrentSourceCollection() {
    if (!urlDraftItems.length) {
      setSourceContractStatus("当前 URL 草稿篮为空，无法保存集合", "error");
      return;
    }

    var name = sourceCollectionName && sourceCollectionName.value.trim()
      ? sourceCollectionName.value.trim()
      : "未命名来源集合";

    var now = new Date().toISOString();
    var collection = {
      id: createSourceCollectionId(),
      name: name.slice(0, 80),
      created_at: now,
      updated_at: now,
      item_count: urlDraftItems.length,
      items: urlDraftItems.map(cloneUrlDraftItem)
    };

    sourceCollections.unshift(collection);
    sourceCollections = sourceCollections.slice(0, MAX_SOURCE_COLLECTIONS);
    persistSourceCollections();

    if (sourceCollectionName) sourceCollectionName.value = "";
    renderSourceCollections();
    renderProductionWorkflowPanel();

    setSourceContractStatus("已保存来源集合：" + collection.name, "success");
  }

  function restoreSourceCollection(id) {
    var collection = sourceCollections.find(function (x) { return x.id === id; });
    if (!collection) {
      setSourceContractStatus("未找到来源集合", "error");
      return;
    }

    urlDraftItems = (collection.items || []).slice(0, MAX_URL_DRAFT_ITEMS).map(cloneUrlDraftItem);
    renderUrlDraftBasket();
    renderProductionWorkflowPanel();
    setSourceContractStatus("已恢复来源集合：" + collection.name, "success");
  }

  function deleteSourceCollection(id) {
    sourceCollections = sourceCollections.filter(function (x) { return x.id !== id; });
    persistSourceCollections();
    renderSourceCollections();
    renderProductionWorkflowPanel();
    setSourceContractStatus("已删除来源集合", "info");
  }

  function clearSourceCollections() {
    sourceCollections = [];
    persistSourceCollections();
    renderSourceCollections();
    renderProductionWorkflowPanel();
    setSourceContractStatus("已清空已保存来源集合", "info");
  }

  function renderSourceCollections() {
    if (!sourceCollectionList) return;

    if (!sourceCollections.length) {
      sourceCollectionList.innerHTML = '<div class="source-contract-empty">暂无已保存来源集合</div>';
      return;
    }

    sourceCollectionList.innerHTML = "";

    sourceCollections.forEach(function (collection) {
      var card = document.createElement("div");
      card.className = "source-collection-card";
      card.setAttribute("data-id", collection.id);

      var firstUrl = collection.items && collection.items[0] ? collection.items[0].url : "";
      var created = collection.created_at ? new Date(collection.created_at).toLocaleString() : "";

      card.innerHTML =
        '<div class="source-collection-card-head">' +
          '<div>' +
            '<div class="source-collection-name">' + escapeHtml(collection.name || "未命名来源集合") + '</div>' +
            '<div class="source-collection-meta">' + escapeHtml(String(collection.item_count || 0)) + ' 条 · ' + escapeHtml(created) + '</div>' +
          '</div>' +
        '</div>' +
        (firstUrl ? '<div class="source-collection-first-url">' + escapeHtml(firstUrl) + '</div>' : '') +
        '<div class="source-collection-card-actions">' +
          '<button class="btn-small source-collection-restore-btn" type="button">恢复到草稿篮</button>' +
          '<button class="btn-small source-collection-delete-btn" type="button">删除</button>' +
        '</div>';

      card.querySelector(".source-collection-restore-btn").addEventListener("click", function () {
        restoreSourceCollection(collection.id);
      });

      card.querySelector(".source-collection-delete-btn").addEventListener("click", function () {
        deleteSourceCollection(collection.id);
      });

      sourceCollectionList.appendChild(card);
    });
  }

  // Wire up source contract buttons
  if (btnBuildContractFromSample) {
    btnBuildContractFromSample.addEventListener("click", function () {
      buildSourceContract({
        source_type: "sample_pack",
        limit: 4,
        template_id: "breaking_news_v1",
        title: "今日 AI 前沿速览",
        subtitle: "样例新闻栏目",
      });
    });
  }

  if (btnBuildContractFromInline) {
    btnBuildContractFromInline.addEventListener("click", function () {
      var text = sourceInlineText.value.trim();
      if (!text) {
        setSourceContractStatus("请先粘贴新闻文本", "error");
        return;
      }
      buildSourceContract({
        source_type: "inline_text",
        text: text,
        source: "Manual",
        url: "",
        limit: 1,
        template_id: "breaking_news_v1",
        title: "单条新闻快讯",
        subtitle: "粘贴文本生成",
      });
    });
  }

  // CP43.1: Wire apply-to-planner button
  if (btnApplySourceContractToPlanner) {
    btnApplySourceContractToPlanner.addEventListener("click", applySourceContractToPlanner);
  }

  // CP44: Wire URL input button and load reliable sources
  if (btnBuildContractFromUrl) {
    btnBuildContractFromUrl.addEventListener("click", function () {
      var url = sourceUrlInput.value.trim();
      var newsTitle = sourceUrlTitle.value.trim();
      var newsSummary = sourceUrlSummary.value.trim();
      var sourceId = sourceUrlSourceSelect.value || "";

      if (!url) {
        setSourceContractStatus("请先输入 URL", "error");
        return;
      }
      if (!newsTitle) {
        setSourceContractStatus("请先输入新闻标题", "error");
        return;
      }

      buildSourceContract({
        source_type: "url_input",
        url: url,
        news_title: newsTitle,
        news_summary: newsSummary,
        source_id: sourceId || null,
        tags: [],
        limit: 1,
        template_id: "breaking_news_v1",
        episode_title: "官方来源快讯",
        episode_subtitle: "URL 输入生成",
      });
    });
  }

  // CP45: Wire article fetch button
  if (btnFetchArticleFromUrl) {
    btnFetchArticleFromUrl.addEventListener("click", fetchArticleIntoUrlForm);
  }

  // Load reliable sources for the URL input dropdown
  loadReliableSources();

  // CP46: Wire up URL draft basket buttons
  if (btnAddUrlDraft) {
    btnAddUrlDraft.addEventListener("click", function () {
      addUrlDraft(urlDraftNewUrl.value);
    });
  }

  if (btnClearUrlDrafts) {
    btnClearUrlDrafts.addEventListener("click", clearUrlDrafts);
  }

  if (btnBuildContractFromUrlDrafts) {
    btnBuildContractFromUrlDrafts.addEventListener("click", buildContractFromUrlDrafts);
  }

  // CP46: Initialize URL draft basket render
  renderUrlDraftBasket();

  // ---------- CP49: Publish Package functions ----------
  let latestPublishPackage = null;

  function getCurrentPublishSourceItems() {
    if (Array.isArray(latestSourceEpisodeItems) && latestSourceEpisodeItems.length) {
      return latestSourceEpisodeItems;
    }
    if (Array.isArray(episodeItemList) && episodeItemList.length) {
      return episodeItemList;
    }
    return [];
  }

  function collectPublishTags(items) {
    var tagMap = {};
    ["AI", "科技", "前沿", "新闻"].forEach(function (tag) {
      tagMap[tag] = true;
    });
    items.forEach(function (item) {
      (item.tags || []).forEach(function (tag) {
        if (tag && String(tag).trim()) {
          tagMap[String(tag).trim()] = true;
        }
      });
    });
    return Object.keys(tagMap).slice(0, 10);
  }

  function buildPublishPackage() {
    var items = getCurrentPublishSourceItems();
    var lead = items[0] || {};
    var contractEpisode = latestSourceContract && latestSourceContract.episode ? latestSourceContract.episode : null;

    var titleBase = contractEpisode && contractEpisode.title
      ? contractEpisode.title
      : lead.title || lead.headline || "今日 AI 前沿速览";

    var title = titleBase;
    if (title.length > 40) title = title.slice(0, 40) + "…";

    var description = lead.summary || lead.description || "整理今日值得关注的 AI 前沿动态，用短视频快速看懂重点。";
    if (description.length > 120) description = description.slice(0, 120) + "…";

    var tags = collectPublishTags(items);

    var platformCopy =
      title + "\n\n" +
      description + "\n\n" +
      "本期看点：\n" +
      items.slice(0, 4).map(function (item, idx) {
        return (idx + 1) + ". " + (item.title || item.headline || "未命名新闻");
      }).join("\n") +
      "\n\n" +
      tags.map(function (tag) { return "#" + tag; }).join(" ");

    var coverPrompt =
      "9:16 竖版新闻视频封面，主题：" + title +
      "。卡通新闻主播，科技感演播室，AI 前沿新闻氛围，清晰大标题，低饱和蓝紫色，干净信息卡片布局。";

    var mp4Url = currentEpisodeExportMp4Url || "";
    var assetLinks = mp4Url
      ? "MP4: " + mp4Url
      : "MP4: 尚未检测到导出链接，请先完成 MP4 导出。";

    var sourceSummary = items.length
      ? items.slice(0, 6).map(function (item, idx) {
          var src = item.source || item.source_id || item.url || "未知来源";
          return (idx + 1) + ". " + (item.title || item.headline || "未命名新闻") + " — " + src;
        }).join("\n")
      : "暂无来源。请先生成栏目或应用到 Episode Planner。";

    return {
      title: title,
      description: description,
      platform_copy: platformCopy,
      tags: tags,
      cover_prompt: coverPrompt,
      asset_links: assetLinks,
      source_summary: sourceSummary,
      generated_at: new Date().toISOString()
    };
  }

  function renderPublishPackage(pkg) {
    if (!pkg) return;
    latestPublishPackage = pkg;

    if (publishTitle) publishTitle.value = pkg.title || "";
    if (publishDescription) publishDescription.value = pkg.description || "";
    if (publishPlatformCopy) publishPlatformCopy.value = pkg.platform_copy || "";
    if (publishTags) publishTags.value = (pkg.tags || []).map(function (tag) { return "#" + tag; }).join(" ");
    if (publishCoverPrompt) publishCoverPrompt.value = pkg.cover_prompt || "";
    if (publishAssetLinks) publishAssetLinks.value = pkg.asset_links || "";
    if (publishSourceSummary) publishSourceSummary.value = pkg.source_summary || "";

    if (publishPackageContent) publishPackageContent.style.display = "block";
    if (publishPackageStatus) {
      publishPackageStatus.textContent = "发布素材包已生成，可复制到目标平台手动发布。";
      publishPackageStatus.className = "publish-package-status is-ready";
    }
  }

  function generatePublishPackage() {
    var pkg = buildPublishPackage();
    renderPublishPackage(pkg);
    if (typeof renderProductionWorkflowPanel === "function") {
      renderProductionWorkflowPanel();
    }
  }

  function copyTextFromElementId(id) {
    var el = document.getElementById(id);
    if (!el) return;
    var text = el.value || el.textContent || "";
    if (!text.trim()) {
      setSourceContractStatus("没有可复制的内容", "error");
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        setSourceContractStatus("已复制：" + id, "success");
      }).catch(function () {
        fallbackCopyText(text, id);
      });
    } else {
      fallbackCopyText(text, id);
    }
  }

  function fallbackCopyText(text, id) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "readonly");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand("copy");
      setSourceContractStatus("已复制：" + id, "success");
    } catch (e) {
      setSourceContractStatus("复制失败：" + e.message, "error");
    }
    document.body.removeChild(textarea);
  }

  // ---------- CP50: Export Publish Package functions ----------

  function sanitizePublishFilename(input) {
    var raw = String(input || "publish_package").trim();
    var cleaned = raw
      .replace(/[\\/:*?"<>|]/g, "_")
      .replace(/\s+/g, "_")
      .replace(/_+/g, "_")
      .slice(0, 60);
    return cleaned || "publish_package";
  }

  function getPublishPackageFilename(ext) {
    var pkg = latestPublishPackage || buildPublishPackage();
    var title = pkg && pkg.title ? pkg.title : "publish_package";
    var date = new Date().toISOString().slice(0, 10);
    return sanitizePublishFilename(date + "_" + title) + "." + ext;
  }

  function downloadTextFile(filename, content, mimeType) {
    var blob = new Blob([content], { type: mimeType || "text/plain;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1000);
  }

  function ensurePublishPackage() {
    if (!latestPublishPackage) {
      latestPublishPackage = buildPublishPackage();
      renderPublishPackage(latestPublishPackage);
    }
    return latestPublishPackage;
  }

  function buildPublishPackageMarkdown(pkg) {
    var lines = [];
    var tags = (pkg.tags || []).map(function (tag) { return "#" + tag; }).join(" ");

    lines.push("# " + (pkg.title || "发布素材包"));
    lines.push("");
    lines.push("> Generated by chalk-news-video · " + new Date().toISOString());
    lines.push("");
    lines.push("## 短简介");
    lines.push("");
    lines.push(pkg.description || "");
    lines.push("");
    lines.push("## 平台文案");
    lines.push("");
    lines.push(pkg.platform_copy || "");
    lines.push("");
    lines.push("## 标签");
    lines.push("");
    lines.push(tags || "暂无标签");
    lines.push("");
    lines.push("## 封面提示词");
    lines.push("");
    lines.push(pkg.cover_prompt || "");
    lines.push("");
    lines.push("## MP4 / 素材链接");
    lines.push("");
    lines.push(pkg.asset_links || "");
    lines.push("");
    lines.push("## 来源摘要");
    lines.push("");
    lines.push(pkg.source_summary || "");
    lines.push("");
    lines.push("## 边界说明");
    lines.push("");
    lines.push("- 本文件是发布素材包，不代表已发布。");
    lines.push("- 未调用任何抖音/B站/YouTube API。");
    lines.push("- 未上传文件。");
    lines.push("- 文案为规则生成，不是 real LLM 生成。");

    return lines.join("\n");
  }

  function exportPublishPackageJson() {
    var pkg = ensurePublishPackage();
    var payload = {
      schema: "chalk_publish_package_v1",
      generated_at: new Date().toISOString(),
      title: pkg.title || "",
      description: pkg.description || "",
      platform_copy: pkg.platform_copy || "",
      tags: pkg.tags || [],
      cover_prompt: pkg.cover_prompt || "",
      asset_links: pkg.asset_links || "",
      source_summary: pkg.source_summary || "",
      metadata: {
        has_mp4: !!currentEpisodeExportMp4Url,
        mp4_url: currentEpisodeExportMp4Url || "",
        source_item_count: getCurrentPublishSourceItems().length,
        workflow_ready: getProductionWorkflowState ? getProductionWorkflowState().ready : false
      }
    };

    downloadTextFile(
      getPublishPackageFilename("json"),
      JSON.stringify(payload, null, 2),
      "application/json;charset=utf-8"
    );

    if (publishPackageStatus) {
      publishPackageStatus.textContent = "已导出 publish_package.json。";
      publishPackageStatus.className = "publish-package-status is-ready";
    }
  }

  function exportPublishPackageMarkdown() {
    var pkg = ensurePublishPackage();
    var markdown = buildPublishPackageMarkdown(pkg);

    downloadTextFile(
      getPublishPackageFilename("md"),
      markdown,
      "text/markdown;charset=utf-8"
    );

    if (publishPackageStatus) {
      publishPackageStatus.textContent = "已导出 publish_package.md。";
      publishPackageStatus.className = "publish-package-status is-ready";
    }
  }

  // ---------- CP48: Production Workflow functions ----------

  function getProductionWorkflowState() {
    var hasUrlDrafts = Array.isArray(urlDraftItems) && urlDraftItems.length > 0;
    var hasReadyUrlDrafts = hasUrlDrafts && urlDraftItems.some(function (item) {
      return item.title && item.title.trim();
    });

    var hasCollections = Array.isArray(sourceCollections) && sourceCollections.length > 0;
    var hasSourceContract = !!latestSourceContract;
    var hasSourceItems = Array.isArray(latestSourceEpisodeItems) && latestSourceEpisodeItems.length > 0;
    var hasPlannerItems = Array.isArray(episodeItemList) && episodeItemList.length > 0;
    var hasPreview = !!latestEpisodePreviewUrl || !!latestEpisodeTemplateContract;
    var hasExport = !!currentEpisodeExportMp4Url || !!latestSucceededJob;

    var steps = [
      {
        id: "source",
        label: "来源准备",
        desc: hasUrlDrafts || hasCollections ? "已有 URL 草稿或来源集合" : "添加 URL、粘贴文本或使用样例新闻",
        done: hasUrlDrafts || hasCollections || hasSourceItems
      },
      {
        id: "drafts",
        label: "草稿确认",
        desc: hasReadyUrlDrafts ? "至少 1 条 URL 草稿已有标题" : "抽取或手动填写标题摘要",
        done: hasReadyUrlDrafts || hasSourceItems
      },
      {
        id: "contract",
        label: "栏目合约",
        desc: hasSourceContract ? "已生成 episode_template_v1 contract" : "从样例、文本、URL 或草稿篮生成栏目",
        done: hasSourceContract
      },
      {
        id: "inspect",
        label: "结果检查",
        desc: hasSourceItems ? "inspector 中已有入选新闻" : "生成 contract 后检查入选新闻",
        done: hasSourceItems
      },
      {
        id: "planner",
        label: "应用到合集",
        desc: hasPlannerItems ? "Episode Planner 已有新闻项" : "点击应用到当前合集",
        done: hasPlannerItems
      },
      {
        id: "preview",
        label: "预览",
        desc: hasPreview ? "已有可预览的 9:16 视频舞台" : "生成预览确认画面",
        done: hasPreview
      },
      {
        id: "export",
        label: "MP4 导出",
        desc: hasExport ? "已有导出结果或成功任务" : "导出 MP4 后可发布",
        done: hasExport
      }
    ];

    var doneCount = steps.filter(function (step) { return step.done; }).length;
    var ready = hasPlannerItems && hasPreview && hasExport;

    return {
      steps: steps,
      doneCount: doneCount,
      total: steps.length,
      ready: ready,
      hasSourceContract: hasSourceContract,
      hasPlannerItems: hasPlannerItems,
      hasPreview: hasPreview,
      hasExport: hasExport
    };
  }

  function getNextProductionWorkflowHint(state) {
    var next = state.steps.find(function (step) { return !step.done; });
    return next ? next.desc : "检查导出结果并准备发布";
  }

  function renderProductionWorkflowPanel() {
    if (!productionWorkflowSteps) return;

    var state = getProductionWorkflowState();

    productionWorkflowSteps.innerHTML = "";

    state.steps.forEach(function (step, index) {
      var node = document.createElement("div");
      node.className = "production-workflow-step " + (step.done ? "is-done" : "is-pending");
      node.innerHTML =
        '<div class="production-workflow-step-index">' + (step.done ? "✓" : String(index + 1)) + "</div>" +
        '<div class="production-workflow-step-body">' +
          '<div class="production-workflow-step-label">' + escapeHtml(step.label) + "</div>" +
          '<div class="production-workflow-step-desc">' + escapeHtml(step.desc) + "</div>" +
        "</div>";
      productionWorkflowSteps.appendChild(node);
    });

    if (productionReadinessBadge) {
      productionReadinessBadge.className = "production-readiness-badge " + (state.ready ? "is-ready" : "is-blocked");
      productionReadinessBadge.textContent = state.ready ? "可发布" : "待补齐";
    }

    if (productionWorkflowSummary) {
      if (state.ready) {
        productionWorkflowSummary.textContent = "当前视频已经完成核心生产链路：已应用到合集、已预览、已导出 MP4。可以进入发布或复盘。";
      } else {
        productionWorkflowSummary.textContent =
          "当前进度：" + state.doneCount + "/" + state.total +
          "。建议下一步：" + getNextProductionWorkflowHint(state);
      }
    }
  }

  // CP47: Wire up Source Collection buttons
  if (btnSaveSourceCollection) {
    btnSaveSourceCollection.addEventListener("click", saveCurrentSourceCollection);
  }

  if (btnClearSourceCollections) {
    btnClearSourceCollections.addEventListener("click", clearSourceCollections);
  }

  // CP47: Initialize Source Collections
  loadSourceCollections();
  renderSourceCollections();

  // CP49: Wire up Publish Package buttons
  if (btnGeneratePublishPackage) {
    btnGeneratePublishPackage.addEventListener("click", generatePublishPackage);
  }

  document.querySelectorAll("[data-copy-target]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      copyTextFromElementId(btn.getAttribute("data-copy-target"));
    });
  });

  // CP50: Wire up Export Publish Package buttons
  if (btnExportPublishPackageJson) {
    btnExportPublishPackageJson.addEventListener("click", exportPublishPackageJson);
  }

  if (btnExportPublishPackageMd) {
    btnExportPublishPackageMd.addEventListener("click", exportPublishPackageMarkdown);
  }

  // ---------- start ----------
  init();
})();
