// GovContractFinder - Client Application Logic

const API_BASE_URL = 'https://consoling-king-confining.ngrok-free.dev';

let state = {
  opportunities: [],
  activeTier: 'ALL',
  onlyFavorites: false,
  searchQuery: '',
  setAsideFilter: 'ALL',
  minScoreFilter: 0,
  currentModalNoticeId: null,
  currentModalOpp: null,
  secondsUntilNextRun: null,
  countdownIntervalId: null,
};

// Initialize application on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  loadInitialData();
  startSchedulePolling();
});

async function loadInitialData() {
  await Promise.all([
    fetchOpportunities(),
    fetchStats(),
    fetchScheduleInfo(),
    checkSettingsStatus()
  ]);
}

// --- Opportunities API & Rendering ---

async function fetchOpportunities() {
  const loading = document.getElementById('loadingIndicator');
  const emptyState = document.getElementById('emptyState');
  const list = document.getElementById('opportunitiesList');

  if (loading) loading.classList.remove('hidden');
  if (emptyState) emptyState.classList.add('hidden');

  try {
    const params = new URLSearchParams();
    if (state.searchQuery) params.append('query', state.searchQuery);
    if (state.activeTier !== 'ALL') params.append('tier', state.activeTier);
    if (state.onlyFavorites) params.append('only_favorites', 'true');
    if (state.setAsideFilter !== 'ALL') params.append('set_aside', state.setAsideFilter);
    if (state.minScoreFilter > 0) params.append('min_score', state.minScoreFilter);

    const res = await fetch(`${API_BASE_URL}/api/opportunities?${params.toString()}`);
    const data = await res.json();
    state.opportunities = data.results || [];

    renderOpportunities(state.opportunities);
  } catch (err) {
    console.error('Failed to fetch opportunities:', err);
    showToast('Failed to load solicitations', 'error');
  } finally {
    if (loading) loading.classList.add('hidden');
  }
}

function renderOpportunities(items) {
  const list = document.getElementById('opportunitiesList');
  const emptyState = document.getElementById('emptyState');

  if (!items || items.length === 0) {
    list.innerHTML = '';
    emptyState.classList.remove('hidden');
    return;
  }

  emptyState.classList.add('hidden');
  list.innerHTML = items.map(opp => createOpportunityCardHtml(opp)).join('');

  if (window.lucide) {
    lucide.createIcons();
  }
}

function createOpportunityCardHtml(opp) {
  const score = opp.overall_score || 0;
  const tier = (opp.tier || 'LOW').toUpperCase();
  const isFav = opp.is_favorite === 1;

  // Styling based on score tier
  let tierBadgeBg, tierBadgeBorder, tierBadgeText, scoreColor;
  if (tier === 'HIGH') {
    tierBadgeBg = 'bg-emerald-50';
    tierBadgeBorder = 'border-emerald-200';
    tierBadgeText = 'text-emerald-700';
    scoreColor = 'bg-emerald-600 text-white';
  } else if (tier === 'MODERATE') {
    tierBadgeBg = 'bg-amber-50';
    tierBadgeBorder = 'border-amber-200';
    tierBadgeText = 'text-amber-700';
    scoreColor = 'bg-amber-500 text-white';
  } else {
    tierBadgeBg = 'bg-slate-50';
    tierBadgeBorder = 'border-slate-200';
    tierBadgeText = 'text-slate-600';
    scoreColor = 'bg-slate-500 text-white';
  }

  // Calculate days remaining
  let deadlineBadge = '';
  if (opp.response_date) {
    try {
      const respDate = new Date(opp.response_date);
      const diffDays = Math.ceil((respDate - new Date()) / (1000 * 60 * 60 * 24));
      if (diffDays > 0) {
        deadlineBadge = `<span class="inline-flex items-center text-[11px] font-medium text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-100">
          <i data-lucide="clock" class="w-3 h-3 mr-1"></i> ${diffDays}d left (${opp.response_date})
        </span>`;
      } else {
        deadlineBadge = `<span class="inline-flex items-center text-[11px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded">Due: ${opp.response_date}</span>`;
      }
    } catch (e) {
      deadlineBadge = `<span class="text-[11px] text-slate-500">Due: ${opp.response_date}</span>`;
    }
  }

  // Matched keyword chips (up to 4)
  const matchedKeywords = (opp.matched_keywords || []).slice(0, 4);
  const keywordChips = matchedKeywords.map(kw => 
    `<span class="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[11px] font-medium">#${escapeHtml(kw)}</span>`
  ).join('');

  // Primary Domain
  const primaryDomain = opp.feasibility_analysis?.primary_domain || 'Technology & Software';

  return `
    <article class="opportunity-card bg-white rounded-xl border border-slate-200/90 shadow-sm p-4 md:p-5 relative transition">
      
      <!-- Top Meta Row -->
      <div class="flex items-start justify-between gap-3 mb-2">
        <div class="flex flex-wrap items-center gap-1.5">
          <!-- Score Pill -->
          <div class="score-pill inline-flex items-center px-2.5 py-1 rounded-lg font-bold text-xs ${scoreColor} shadow-sm">
            <span>${score}% Match</span>
          </div>

          <!-- Tier Badge -->
          <span class="px-2 py-0.5 text-[11px] font-bold uppercase rounded ${tierBadgeBg} ${tierBadgeBorder} ${tierBadgeText} border">
            ${tier === 'HIGH' ? 'High Executable Work' : (tier === 'MODERATE' ? 'Moderate Match' : 'Low Match')}
          </span>

          <!-- Domain -->
          <span class="hidden sm:inline-block px-2 py-0.5 text-[11px] font-medium text-indigo-700 bg-indigo-50 rounded border border-indigo-100">
            ${escapeHtml(primaryDomain)}
          </span>
        </div>

        <!-- Favorite Button -->
        <button onclick="toggleFavorite('${opp.notice_id}', event)" class="p-1.5 text-slate-400 hover:text-yellow-500 rounded-lg transition active:scale-90" title="Bookmark">
          <i data-lucide="star" class="w-5 h-5 ${isFav ? 'text-yellow-500 fill-yellow-400' : ''}"></i>
        </button>
      </div>

      <!-- Title & Sol Number -->
      <div class="mb-2">
        <h3 class="text-sm md:text-base font-bold text-slate-900 leading-snug cursor-pointer hover:text-blue-600 transition"
            onclick="openScorecardModal('${opp.notice_id}')">
          ${escapeHtml(opp.title)}
        </h3>
        <div class="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1 text-xs text-slate-500">
          <span class="font-mono text-[11px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">${escapeHtml(opp.sol_number || opp.notice_id)}</span>
          <span>•</span>
          <span class="font-medium text-slate-700">${escapeHtml(opp.agency || 'Federal Agency')}</span>
          ${opp.office ? `<span class="hidden md:inline">• ${escapeHtml(opp.office)}</span>` : ''}
        </div>
      </div>

      <!-- Executive Work Summary -->
      <p class="text-xs text-slate-600 leading-relaxed mb-3 line-clamp-2 md:line-clamp-3">
        ${escapeHtml(opp.summary || opp.description || 'No work summary available.')}
      </p>

      <!-- Keywords & Deliverable Highlights -->
      <div class="flex flex-wrap items-center gap-1.5 mb-3.5">
        ${keywordChips}
        ${(opp.matched_keywords || []).length > 4 ? `<span class="text-[10px] text-slate-400 font-medium">+${opp.matched_keywords.length - 4} more</span>` : ''}
      </div>

      <!-- Bottom Actions Bar -->
      <div class="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
        <div class="flex flex-wrap items-center gap-2">
          ${deadlineBadge}
          ${opp.set_aside ? `<span class="px-2 py-0.5 text-[11px] font-medium bg-purple-50 text-purple-700 rounded border border-purple-100">${escapeHtml(opp.set_aside)}</span>` : ''}
        </div>

        <div class="flex items-center space-x-2 w-full sm:w-auto justify-end">
          <button onclick="openScorecardModal('${opp.notice_id}')"
            class="flex-1 sm:flex-none flex items-center justify-center space-x-1 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-sm transition">
            <i data-lucide="bar-chart-2" class="w-3.5 h-3.5"></i>
            <span>Scorecard</span>
          </button>

          <a href="${opp.ui_link || `https://sam.gov/opp/${opp.notice_id}/view`}" target="_blank" rel="noopener noreferrer"
            class="flex items-center justify-center space-x-1 px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded-lg border border-blue-200 transition"
            title="View original on SAM.gov">
            <span>SAM.gov</span>
            <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        </div>
      </div>

    </article>
  `;
}

// --- KPI Stats API ---

async function fetchStats() {
  try {
    const res = await fetch(API_BASE_URL + '/api/stats');
    const stats = await res.json();
    document.getElementById('statTotal').innerText = stats.total_solicitations || 0;
    document.getElementById('statHigh').innerText = stats.high_match_count || 0;
    document.getElementById('statModerate').innerText = stats.moderate_match_count || 0;
    document.getElementById('statFavorites').innerText = stats.favorites_count || 0;
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

// --- Schedule & Countdown ---

async function fetchScheduleInfo() {
  try {
    const res = await fetch(API_BASE_URL + '/api/schedule');
    const data = await res.json();
    if (data.seconds_until_next_run !== undefined && data.seconds_until_next_run !== null) {
      state.secondsUntilNextRun = data.seconds_until_next_run;
      updateCountdownDisplay();
    }
  } catch (err) {
    console.error('Failed to load schedule info:', err);
  }
}

function startSchedulePolling() {
  if (state.countdownIntervalId) clearInterval(state.countdownIntervalId);

  state.countdownIntervalId = setInterval(() => {
    if (state.secondsUntilNextRun !== null && state.secondsUntilNextRun > 0) {
      state.secondsUntilNextRun--;
      updateCountdownDisplay();
    } else {
      // Re-fetch when countdown reaches zero
      fetchScheduleInfo();
    }
  }, 1000);
}

function updateCountdownDisplay() {
  if (state.secondsUntilNextRun === null) return;

  const totalSecs = state.secondsUntilNextRun;
  const hours = Math.floor(totalSecs / 3600);
  const minutes = Math.floor((totalSecs % 3600) / 60);
  const seconds = totalSecs % 60;

  const formatted = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  
  const timerElem = document.getElementById('countdownTimer');
  const timerMobileElem = document.getElementById('countdownTimerMobile');
  if (timerElem) timerElem.innerText = formatted;
  if (timerMobileElem) timerMobileElem.innerText = formatted;
}

// --- Manual Sync ---

async function triggerManualSync() {
  const syncBtn = document.getElementById('btnSyncNow');
  const syncIcon = document.getElementById('syncIcon');

  if (syncIcon) syncIcon.classList.add('animate-spin');
  if (syncBtn) syncBtn.disabled = true;

  showToast('Connecting to SAM.gov and calculating scorecards...', 'info');

  try {
    const res = await fetch(API_BASE_URL + '/api/sync', { method: 'POST' });
    const result = await res.json();

    if (result.status === 'SUCCESS') {
      showToast(`Sync complete! ${result.found_count} opportunities evaluated (${result.new_count} new).`, 'success');
      await Promise.all([
        fetchOpportunities(),
        fetchStats(),
        fetchScheduleInfo()
      ]);
    } else if (result.status === 'in_progress') {
      showToast('A sync is currently running in the background.', 'info');
    } else {
      showToast(result.message || 'Sync failed. Check settings.', 'error');
    }
  } catch (err) {
    console.error('Sync failed:', err);
    showToast('Failed to trigger SAM.gov sync.', 'error');
  } finally {
    if (syncIcon) syncIcon.classList.remove('animate-spin');
    if (syncBtn) syncBtn.disabled = false;
  }
}

// --- Favorites & User Interactions ---

async function toggleFavorite(noticeId, event) {
  if (event) event.stopPropagation();

  const opp = state.opportunities.find(o => o.notice_id === noticeId);
  const newFavStatus = opp ? (opp.is_favorite === 1 ? false : true) : true;

  // Optimistic update
  if (opp) opp.is_favorite = newFavStatus ? 1 : 0;
  renderOpportunities(state.opportunities);
  fetchStats();

  try {
    await fetch(`/api/opportunities/${noticeId}/interaction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_favorite: newFavStatus })
    });
    showToast(newFavStatus ? 'Added to favorites' : 'Removed from favorites', 'success');
  } catch (err) {
    console.error('Failed to update favorite status:', err);
    showToast('Failed to update bookmark', 'error');
  }
}

async function toggleCurrentModalFavorite() {
  if (!state.currentModalNoticeId) return;
  await toggleFavorite(state.currentModalNoticeId);

  // Update modal bookmark label
  const opp = state.opportunities.find(o => o.notice_id === state.currentModalNoticeId);
  const isFav = opp?.is_favorite === 1;
  const favIcon = document.getElementById('modalFavIcon');
  const favLabel = document.getElementById('modalFavLabel');

  if (favIcon) {
    if (isFav) {
      favIcon.classList.add('text-yellow-500', 'fill-yellow-400');
    } else {
      favIcon.classList.remove('text-yellow-500', 'fill-yellow-400');
    }
  }
  if (favLabel) favLabel.innerText = isFav ? 'Bookmarked' : 'Bookmark';
}

// --- Scorecard Deep-Dive Modal ---

async function openScorecardModal(noticeId) {
  state.currentModalNoticeId = noticeId;
  const modal = document.getElementById('scorecardModal');

  let opp = state.opportunities.find(o => o.notice_id === noticeId);
  if (!opp) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/opportunities/${noticeId}`);
      opp = await res.json();
    } catch (e) {
      showToast('Could not load solicitation detail', 'error');
      return;
    }
  }

  state.currentModalOpp = opp;

  // Populate Modal Fields
  document.getElementById('modalNoticeId').innerText = `Notice ID: ${opp.notice_id}`;
  document.getElementById('modalTitle').innerText = opp.title || 'Untitled Solicitation';
  document.getElementById('modalAgency').innerText = opp.agency || 'Federal Government';
  document.getElementById('modalSetAside').innerText = opp.set_aside || 'Unrestricted';
  document.getElementById('modalDeadline').innerText = opp.response_date ? `Deadline: ${opp.response_date}` : 'No deadline stated';
  
  // Link to SAM.gov
  const samLink = opp.ui_link || `https://sam.gov/opp/${opp.notice_id}/view`;
  const samBtn = document.getElementById('modalSamLinkBtn');
  samBtn.href = samLink;

  // Score Banner & Tier
  const score = opp.overall_score || 0;
  const tier = (opp.tier || 'LOW').toUpperCase();
  const scoreCircle = document.getElementById('modalScoreCircle');
  const tierBadge = document.getElementById('modalTierBadge');
  const scoreBanner = document.getElementById('modalScoreBanner');

  scoreCircle.innerText = `${score}%`;

  if (tier === 'HIGH') {
    scoreBanner.className = 'p-4 rounded-xl border bg-emerald-50/70 border-emerald-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3';
    scoreCircle.className = 'w-14 h-14 rounded-full flex items-center justify-center font-black text-xl shadow-inner bg-emerald-600 text-white';
    tierBadge.className = 'inline-block px-2 py-0.5 text-xs font-bold rounded uppercase tracking-wider mb-1 bg-emerald-200/60 text-emerald-800';
    tierBadge.innerText = 'HIGH MATCH • EXECUTABLE WORK';
  } else if (tier === 'MODERATE') {
    scoreBanner.className = 'p-4 rounded-xl border bg-amber-50/70 border-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3';
    scoreCircle.className = 'w-14 h-14 rounded-full flex items-center justify-center font-black text-xl shadow-inner bg-amber-500 text-white';
    tierBadge.className = 'inline-block px-2 py-0.5 text-xs font-bold rounded uppercase tracking-wider mb-1 bg-amber-200/60 text-amber-800';
    tierBadge.innerText = 'MODERATE MATCH • PARTIAL FIT';
  } else {
    scoreBanner.className = 'p-4 rounded-xl border bg-slate-50 border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3';
    scoreCircle.className = 'w-14 h-14 rounded-full flex items-center justify-center font-black text-xl shadow-inner bg-slate-500 text-white';
    tierBadge.className = 'inline-block px-2 py-0.5 text-xs font-bold rounded uppercase tracking-wider mb-1 bg-slate-200 text-slate-700';
    tierBadge.innerText = 'LOW MATCH • OUT OF SCOPE';
  }

  // Executive Summary
  document.getElementById('modalSummary').innerText = opp.summary || opp.description || 'No work summary available.';

  // Category Match Breakdown
  const catContainer = document.getElementById('modalCategoryBreakdown');
  const catScores = opp.category_scores || {};
  catContainer.innerHTML = Object.entries(catScores).map(([catId, catScore]) => {
    let catDisplayName = catId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    if (catId === 'software_development') catDisplayName = 'Software Development';
    if (catId === 'data_analysis') catDisplayName = 'Data Analysis & AI/ML';
    if (catId === 'technology') catDisplayName = 'Technology & Cloud Infrastructure';

    let barColor = catScore >= 70 ? 'bg-emerald-500' : (catScore >= 40 ? 'bg-amber-500' : 'bg-slate-400');

    return `
      <div>
        <div class="flex justify-between items-center text-xs font-medium text-slate-700 mb-1">
          <span>${escapeHtml(catDisplayName)}</span>
          <span class="font-bold text-slate-900">${catScore}%</span>
        </div>
        <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
          <div class="${barColor} h-2 rounded-full transition-all duration-500" style="width: ${catScore}%"></div>
        </div>
      </div>
    `;
  }).join('');

  // Key Deliverables List
  const delivContainer = document.getElementById('modalDeliverablesList');
  const deliverables = opp.deliverables || [];
  if (deliverables.length > 0) {
    delivContainer.innerHTML = deliverables.map(d => 
      `<li class="flex items-start space-x-2">
        <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600 mt-0.5 flex-shrink-0"></i>
        <span>${escapeHtml(d)}</span>
      </li>`
    ).join('');
  } else {
    delivContainer.innerHTML = `<li class="text-slate-500">Refer to the official SOW attached to the SAM.gov solicitation package.</li>`;
  }

  // Matched Keywords Chips
  const kwContainer = document.getElementById('modalMatchedKeywords');
  const keywords = opp.matched_keywords || [];
  if (keywords.length > 0) {
    kwContainer.innerHTML = keywords.map(kw => 
      `<span class="px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg text-xs font-medium">
        ${escapeHtml(kw)}
      </span>`
    ).join('');
  } else {
    kwContainer.innerHTML = `<span class="text-slate-400 text-xs italic">No direct skill keywords matched</span>`;
  }

  // Technical Metadata
  const naicsDesc = opp.feasibility_analysis?.naics_description || '';
  document.getElementById('modalNaics').innerText = opp.naics_code ? `${opp.naics_code} ${naicsDesc ? `(${naicsDesc})` : ''}` : 'N/A';
  document.getElementById('modalPsc').innerText = opp.psc_code || 'N/A';
  document.getElementById('modalPop').innerText = opp.place_of_performance || 'Not Specified / Remote Eligible';
  document.getElementById('modalType').innerText = opp.type || 'Solicitation';

  // Bookmark Button in Modal
  const isFav = opp.is_favorite === 1;
  const favIcon = document.getElementById('modalFavIcon');
  const favLabel = document.getElementById('modalFavLabel');
  if (favIcon) {
    if (isFav) {
      favIcon.classList.add('text-yellow-500', 'fill-yellow-400');
    } else {
      favIcon.classList.remove('text-yellow-500', 'fill-yellow-400');
    }
  }
  if (favLabel) favLabel.innerText = isFav ? 'Bookmarked' : 'Bookmark';

  if (window.lucide) lucide.createIcons();

  modal.showModal();
}

function closeScorecardModal() {
  const modal = document.getElementById('scorecardModal');
  modal.close();
  state.currentModalNoticeId = null;
  state.currentModalOpp = null;
}

// --- Skill Sets File Modal ---

async function openSkillsModal() {
  const modal = document.getElementById('skillsModal');
  const editor = document.getElementById('skillsJsonEditor');
  const errorElem = document.getElementById('skillsJsonError');
  errorElem.classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE_URL}/api/skills`);
    const config = await res.json();
    editor.value = JSON.stringify(config, null, 2);
    modal.showModal();
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Failed to load skills:', err);
    showToast('Failed to load skill sets file', 'error');
  }
}

function closeSkillsModal() {
  document.getElementById('skillsModal').close();
}

async function saveSkillsConfig() {
  const editor = document.getElementById('skillsJsonEditor');
  const errorElem = document.getElementById('skillsJsonError');
  const btn = document.getElementById('btnSaveSkills');

  let parsedConfig;
  try {
    parsedConfig = JSON.parse(editor.value);
  } catch (err) {
    errorElem.innerText = `Invalid JSON syntax: ${err.message}`;
    errorElem.classList.remove('hidden');
    return;
  }

  errorElem.classList.add('hidden');
  btn.disabled = true;
  btn.innerText = 'Recalculating...';

  try {
    const res = await fetch(`${API_BASE_URL}/api/skills?recalculate=true`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsedConfig)
    });
    const result = await res.json();

    if (result.status === 'success') {
      showToast(result.message, 'success');
      closeSkillsModal();
      await Promise.all([fetchOpportunities(), fetchStats()]);
    } else {
      showToast(result.detail || 'Failed to update skills config', 'error');
    }
  } catch (err) {
    console.error('Failed to save skills config:', err);
    showToast('Error saving skills configuration', 'error');
  } finally {
    btn.disabled = false;
    btn.innerText = 'Save & Recalculate';
  }
}

async function resetSkillsToDefault() {
  if (!confirm('Reset skill sets file to default (Technology, Data Analysis, Software Development)?')) return;
  
  // Re-fetch default or load standard template
  const defaultSkills = {
    "name": "Default Skill Sets Configuration",
    "version": "1.0",
    "categories": [
      {
        "id": "software_development",
        "name": "Software Development",
        "weight": 0.40,
        "keywords": ["software development", "web application", "mobile application", "api", "restful", "microservices", "python", "javascript", "typescript", "react", "fastapi", "docker", "kubernetes", "ci/cd", "devsecops", "agile", "scrum"],
        "naics": ["541511", "541512", "541519"]
      },
      {
        "id": "data_analysis",
        "name": "Data Analysis & AI",
        "weight": 0.35,
        "keywords": ["data analysis", "data analytics", "business intelligence", "data science", "data visualization", "dashboard", "power bi", "tableau", "sql", "predictive modeling", "machine learning", "artificial intelligence", "nlp", "etl", "data pipeline"],
        "naics": ["541512", "518210", "541715", "541990"]
      },
      {
        "id": "technology",
        "name": "Technology & Infrastructure",
        "weight": 0.25,
        "keywords": ["information technology", "it modernization", "cloud computing", "cloud migration", "aws", "azure", "google cloud", "cybersecurity", "zero trust", "fedramp", "nist 800-53", "saas", "infrastructure"],
        "naics": ["541513", "541519", "518210"]
      }
    ],
    "scoring_parameters": {
      "keyword_density_weight": 0.40,
      "naics_code_weight": 0.25,
      "title_relevance_weight": 0.20,
      "deliverable_clarity_weight": 0.15,
      "disqualifier_penalty": 35,
      "disqualifying_keywords": ["janitorial", "custodial", "lawn care", "roofing", "plumbing", "catering", "ammunition"],
      "deliverable_markers": ["statement of work", "sow", "deliverables", "milestones", "sprint", "prototype", "dashboard"],
      "thresholds": { "high_match": 70, "moderate_match": 40, "low_match": 0 }
    }
  };

  document.getElementById('skillsJsonEditor').value = JSON.stringify(defaultSkills, null, 2);
}

// --- Settings Modal & API Key ---

async function checkSettingsStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/settings/status`);
    const data = await res.json();
    const banner = document.getElementById('apiKeyStatusBanner');
    const title = document.getElementById('apiKeyStatusTitle');
    const desc = document.getElementById('apiKeyStatusDesc');

    if (data.has_sam_api_key) {
      if (banner) banner.className = 'p-3 rounded-xl border bg-emerald-50 border-emerald-200 text-emerald-800 flex items-start space-x-2.5';
      if (title) title.innerText = 'SAM.gov Live API Connected';
      if (desc) desc.innerText = 'Your API key is active. Daily 5:00 PM EST queries pull live government solicitations.';
    } else {
      if (banner) banner.className = 'p-3 rounded-xl border bg-amber-50 border-amber-200 text-amber-800 flex items-start space-x-2.5';
      if (title) title.innerText = 'Test & Simulation Feed Active';
      if (desc) desc.innerText = 'Running with realistic mock solicitations. Enter a SAM.gov API key below to enable live data queries.';
    }
  } catch (err) {
    console.error('Failed to get settings status:', err);
  }
}

function openSettingsModal() {
  checkSettingsStatus();
  document.getElementById('settingsModal').showModal();
  if (window.lucide) lucide.createIcons();
}

function closeSettingsModal() {
  document.getElementById('settingsModal').close();
}

async function saveApiKey() {
  const input = document.getElementById('settingsApiKeyInput');
  const key = input.value.trim();
  const btn = document.getElementById('btnSaveApiKey');

  btn.disabled = true;
  btn.innerText = 'Saving...';

  try {
    const res = await fetch(`${API_BASE_URL}/api/settings/apikey`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key })
    });
    const result = await res.json();
    if (result.status === 'success') {
      showToast('SAM.gov API Key saved!', 'success');
      await checkSettingsStatus();
      closeSettingsModal();
    } else {
      showToast('Failed to save API key', 'error');
    }
  } catch (err) {
    console.error('Failed to save key:', err);
    showToast('Failed to save API key', 'error');
  } finally {
    btn.disabled = false;
    btn.innerText = 'Save API Key';
  }
}

// --- Filters & Search Controls ---

let searchDebounceTimeout = null;
function debounceSearch() {
  clearTimeout(searchDebounceTimeout);
  const input = document.getElementById('searchInput');
  const clearBtn = document.getElementById('searchClearBtn');

  if (input.value) {
    clearBtn.classList.remove('hidden');
  } else {
    clearBtn.classList.add('hidden');
  }

  searchDebounceTimeout = setTimeout(() => {
    state.searchQuery = input.value.trim();
    fetchOpportunities();
  }, 300);
}

function clearSearch() {
  const input = document.getElementById('searchInput');
  input.value = '';
  document.getElementById('searchClearBtn').classList.add('hidden');
  state.searchQuery = '';
  fetchOpportunities();
}

function setFilterTier(tier) {
  state.activeTier = tier;
  state.onlyFavorites = false;

  // Update pill active classes
  const pills = ['filterBtnAll', 'filterBtnHigh', 'filterBtnModerate', 'filterBtnLow', 'filterBtnFavs'];
  pills.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('bg-slate-900', 'text-white', 'shadow-sm');
      el.classList.add('bg-slate-100', 'text-slate-600');
    }
  });

  let activeBtnId = 'filterBtnAll';
  if (tier === 'HIGH') activeBtnId = 'filterBtnHigh';
  if (tier === 'MODERATE') activeBtnId = 'filterBtnModerate';
  if (tier === 'LOW') activeBtnId = 'filterBtnLow';

  const activeBtn = document.getElementById(activeBtnId);
  if (activeBtn) {
    activeBtn.classList.remove('bg-slate-100', 'text-slate-600');
    activeBtn.classList.add('bg-slate-900', 'text-white', 'shadow-sm');
  }

  fetchOpportunities();
}

function toggleFavoritesOnly() {
  state.onlyFavorites = !state.onlyFavorites;
  state.activeTier = 'ALL';

  const pills = ['filterBtnAll', 'filterBtnHigh', 'filterBtnModerate', 'filterBtnLow', 'filterBtnFavs'];
  pills.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('bg-slate-900', 'text-white', 'shadow-sm');
      el.classList.add('bg-slate-100', 'text-slate-600');
    }
  });

  if (state.onlyFavorites) {
    const favBtn = document.getElementById('filterBtnFavs');
    if (favBtn) {
      favBtn.classList.remove('bg-slate-100', 'text-slate-600');
      favBtn.classList.add('bg-slate-900', 'text-white', 'shadow-sm');
    }
  } else {
    const allBtn = document.getElementById('filterBtnAll');
    if (allBtn) {
      allBtn.classList.remove('bg-slate-100', 'text-slate-600');
      allBtn.classList.add('bg-slate-900', 'text-white', 'shadow-sm');
    }
  }

  fetchOpportunities();
}

function toggleFilterDrawer() {
  const drawer = document.getElementById('filterDrawer');
  drawer.classList.toggle('hidden');
}

function updateMinScoreLabel(val) {
  document.getElementById('minScoreLabel').innerText = `${val}%`;
}

function applyFilters() {
  state.setAsideFilter = document.getElementById('filterSetAside').value;
  state.minScoreFilter = parseInt(document.getElementById('filterMinScore').value, 10);
  fetchOpportunities();
}

function resetAllFilters() {
  state.activeTier = 'ALL';
  state.onlyFavorites = false;
  state.searchQuery = '';
  state.setAsideFilter = 'ALL';
  state.minScoreFilter = 0;

  document.getElementById('searchInput').value = '';
  document.getElementById('searchClearBtn').classList.add('hidden');
  document.getElementById('filterSetAside').value = 'ALL';
  document.getElementById('filterMinScore').value = 0;
  document.getElementById('minScoreLabel').innerText = '0%';

  setFilterTier('ALL');
}

// --- Utilities ---

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  let bg = 'bg-slate-900 text-white';
  let icon = 'info';

  if (type === 'success') {
    bg = 'bg-emerald-600 text-white';
    icon = 'check-circle';
  } else if (type === 'error') {
    bg = 'bg-rose-600 text-white';
    icon = 'alert-circle';
  }

  toast.className = `${bg} px-4 py-3 rounded-xl shadow-xl text-xs font-semibold flex items-center space-x-2 transition-all transform duration-300 translate-y-2 opacity-0 pointer-events-auto max-w-sm`;
  toast.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4 flex-shrink-0"></i><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
