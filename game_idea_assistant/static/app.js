const ideaInput = document.getElementById("ideaInput");
const generateBtn = document.getElementById("generateBtn");
const sampleBtn = document.getElementById("sampleBtn");
const statusText = document.getElementById("statusText");
const scoreGrid = document.getElementById("scoreGrid");
const issuesBox = document.getElementById("issuesBox");
const retrievalList = document.getElementById("retrievalList");
const planCards = document.getElementById("planCards");
const jsonOutput = document.getElementById("jsonOutput");
const generatorMode = document.getElementById("generatorMode");
const historyList = document.getElementById("historyList");
const logFile = document.getElementById("logFile");
const metaGrid = document.getElementById("metaGrid");
const metaMessage = document.getElementById("metaMessage");
const settingsSummary = document.getElementById("settingsSummary");
const apiKeyStatus = document.getElementById("apiKeyStatus");
const heroModePill = document.getElementById("heroModePill");
const modeSelect = document.getElementById("modeSelect");
const modelInput = document.getElementById("modelInput");
const baseUrlInput = document.getElementById("baseUrlInput");
const apiKeyInput = document.getElementById("apiKeyInput");
const temperatureInput = document.getElementById("temperatureInput");
const timeoutInput = document.getElementById("timeoutInput");
const maxTokensInput = document.getElementById("maxTokensInput");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const clearKeyBtn = document.getElementById("clearKeyBtn");

sampleBtn.addEventListener("click", () => {
  ideaInput.value = "做一个二次元塔防游戏，面向轻度玩家，强调爽感和养成。";
});

saveSettingsBtn.addEventListener("click", async () => {
  await saveSettings({ showStatus: true, clearApiKey: false });
});

clearKeyBtn.addEventListener("click", async () => {
  apiKeyInput.value = "";
  await saveSettings({ showStatus: true, clearApiKey: true });
});

generateBtn.addEventListener("click", async () => {
  const idea = ideaInput.value.trim();
  if (!idea) {
    statusText.textContent = "先输入一句游戏创意。";
    return;
  }

  generateBtn.disabled = true;
  statusText.textContent = "正在同步设置、检索案例并生成方案...";

  try {
    await saveSettings({ showStatus: false, clearApiKey: false });
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "请求失败");
    }

    renderPayload(payload);
    statusText.textContent = `完成，生成时间 ${payload.generated_at}`;
    loadHistory();
    loadSettings();
  } catch (error) {
    statusText.textContent = `生成失败：${error.message}`;
  } finally {
    generateBtn.disabled = false;
  }
});

async function loadSettings() {
  try {
    const response = await fetch("/api/settings");
    const payload = await response.json();
    const settings = payload.settings;
    modeSelect.value = settings.mode;
    modelInput.value = settings.model;
    baseUrlInput.value = settings.base_url;
    temperatureInput.value = settings.temperature;
    timeoutInput.value = settings.timeout_seconds;
    maxTokensInput.value = settings.max_output_tokens;
    apiKeyInput.value = "";
    const keyText = settings.api_key_present ? "已保存 Key" : "未保存 Key";
    apiKeyStatus.textContent = keyText;
    settingsSummary.textContent = `${settings.mode} · ${settings.model}`;
    heroModePill.textContent = `当前模式：${settings.mode}`;
  } catch (error) {
    settingsSummary.textContent = "设置读取失败";
    apiKeyStatus.textContent = "无法确认 Key 状态";
  }
}

async function saveSettings({ showStatus, clearApiKey }) {
  const payload = {
    mode: modeSelect.value,
    model: modelInput.value.trim(),
    base_url: baseUrlInput.value.trim(),
    temperature: Number(temperatureInput.value),
    timeout_seconds: Number(timeoutInput.value),
    max_output_tokens: Number(maxTokensInput.value),
  };

  const apiKey = apiKeyInput.value.trim();
  if (apiKey) {
    payload.api_key = apiKey;
  }
  if (clearApiKey) {
    payload.clear_api_key = true;
  }

  const response = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || "设置保存失败");
  }

  const settings = result.settings;
  apiKeyInput.value = "";
  const keyText = settings.api_key_present ? "已保存 Key" : "未保存 Key";
  apiKeyStatus.textContent = keyText;
  settingsSummary.textContent = `${settings.mode} · ${settings.model}`;
  heroModePill.textContent = `当前模式：${settings.mode}`;
  if (showStatus) {
    statusText.textContent = "设置已保存。";
  }
}

function renderPayload(payload) {
  generatorMode.textContent = payload.meta.generator_mode;
  logFile.textContent = payload.meta.log_file || "";
  jsonOutput.textContent = JSON.stringify(payload, null, 2);
  renderScores(payload.evaluation);
  renderRetrieval(payload.retrieval);
  renderPlan(payload.plan);
  renderMeta(payload.meta);
}

function renderMeta(meta) {
  const cards = [
    ["生成模式", meta.generator_mode],
    ["模型", meta.requested_model || meta.generator_detail || "--"],
    ["Provider", meta.provider || "--"],
    ["Base URL", meta.request_base_url || meta.settings?.base_url || "--"],
    ["延迟", meta.latency_ms ? `${meta.latency_ms} ms` : "--"],
    ["回退", meta.fallback_used ? "是" : "否"],
  ];
  metaGrid.innerHTML = cards
    .map(
      ([label, value]) => `
        <article class="meta-card">
          <span>${label}</span>
          <strong>${value}</strong>
        </article>
      `,
    )
    .join("");

  if (meta.fallback_used) {
    metaMessage.textContent = `当前请求发生回退：${meta.fallback_reason || "未知原因"}`;
  } else {
    metaMessage.textContent = "当前输出使用了目标生成模式，没有触发回退。";
  }
}

function renderScores(evaluation) {
  const cards = [
    { label: "总分", value: evaluation.overall_score },
    ...evaluation.checks.map((item) => ({ label: item.name, value: item.score })),
  ];
  scoreGrid.innerHTML = cards
    .map(
      (item) => `
        <article class="score-card">
          <span>${item.label}</span>
          <strong>${item.value}</strong>
        </article>
      `,
    )
    .join("");

  issuesBox.innerHTML = evaluation.issues.length
    ? evaluation.issues.map((issue) => `<div>${issue}</div>`).join("")
    : "本次输出没有触发明显问题。";
}

function renderRetrieval(items) {
  if (!items.length) {
    retrievalList.className = "retrieval-list empty-state";
    retrievalList.textContent = "没有检索结果。";
    return;
  }

  retrievalList.className = "retrieval-list";
  retrievalList.innerHTML = items
    .map(
      (item) => `
        <article class="retrieval-card">
          <h3>${item.title}</h3>
          <div class="history-meta">${item.genre} · ${item.audience} · score ${item.score}</div>
          <p>${item.snippet}</p>
          <div class="token-row">
            ${item.matched_tokens.map((token) => `<span>${token}</span>`).join("")}
          </div>
        </article>
      `,
    )
    .join("");
}

function renderPlan(plan) {
  const sections = [
    ["一句话卖点", plan.one_sentence_pitch],
    ["目标玩家", plan.target_players],
    ["美术与音频", plan.art_and_audio_direction],
    ["局时设计", plan.session_design],
    ["运营抓手", plan.monetization_or_live_ops],
    ["核心循环", plan.core_gameplay_loop],
    ["成长系统", plan.progression_system],
    ["内容支柱", plan.content_pillars],
    ["MVP 范围", plan.mvp_scope],
    ["风险点", plan.risks],
    ["自我修正", plan.self_revision],
  ];

  planCards.className = "plan-cards";
  planCards.innerHTML = `
    <article class="plan-card featured-card">
      <h3>${plan.project_title}</h3>
      <p>${plan.one_sentence_pitch}</p>
      <div class="reference-list">
        ${plan.references.map((item) => `<span>${item.title}</span>`).join("")}
      </div>
    </article>
    ${sections
      .map(([title, value]) => {
        if (Array.isArray(value)) {
          return `
            <article class="plan-card">
              <h3>${title}</h3>
              <div class="bullet-list">${value.map((entry) => `<span>${entry}</span>`).join("")}</div>
            </article>
          `;
        }
        return `
          <article class="plan-card">
            <h3>${title}</h3>
            <p>${value}</p>
          </article>
        `;
      })
      .join("")}
  `;
}

async function loadHistory() {
  try {
    const response = await fetch("/api/logs");
    const payload = await response.json();
    if (!payload.items.length) {
      historyList.className = "history-list empty-state";
      historyList.textContent = "暂无历史记录。";
      return;
    }

    historyList.className = "history-list";
    historyList.innerHTML = payload.items
      .map(
        (item) => `
          <article class="history-card">
            <div class="history-meta">${item.generated_at} · ${item.generator_mode} · ${item.model || "--"}</div>
            <strong>${item.idea}</strong>
            <div class="history-meta">${item.latency_ms ? `${item.latency_ms} ms` : "--"} · ${item.log_file}</div>
          </article>
        `,
      )
      .join("");
  } catch (error) {
    historyList.className = "history-list empty-state";
    historyList.textContent = "历史记录读取失败。";
  }
}

loadSettings();
loadHistory();
