// NTK.Ai.Metatrader - High-Performance Terminal Frontend Logic
// Developed by Ali Karavi (https://alikaravi.com/)

let currentSymbol = 'EURUSD';
let currentTimeframe = 'M15';
let isScalpMode = false;
let latestAIResult = null;
let priceChart = null;
let pollInterval = null;
let activeMainView = 'trading';
let soundEnabled = true;
let audioCtx = null;
let ws = null;

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    setupEventListeners();
    initResizableDeckSplitter();
    restoreUserUIPreferences();
    fetchTerminalAndAccount();
    fetchAiTelemetry();
    fetchMarketData();
    fetchPositions();
    fetchAIAnalysis();
    fetchConfluence();
    fetchStrategies();
    fetchMatrixAnalytics();
    loadSettingsIntoModal();
    initWebSocket();
    // Secondary Poller for non-streaming history views & AI Telemetry
    pollInterval = setInterval(() => {
        fetchAiTelemetry();
        if (activeMainView === 'fleet') {
            fetchSignalsFeed();
        } else if (activeMainView === 'decisions') {
            fetchDecisionsHistory();
        }
    }, 4000);
});

// Sound Alert Effects (Web Audio API)
function playSoundAlert(type = 'chime') {
    if (!soundEnabled) return;
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);

        if (type === 'signal') {
            osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
            osc.frequency.setValueAtTime(880.00, audioCtx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.35);
        } else if (type === 'trade') {
            osc.frequency.setValueAtTime(523.25, audioCtx.currentTime);
            osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.08);
            osc.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.16);
            gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.45);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.45);
        }
    } catch (e) {}
}

function toggleAudioAlerts() {
    soundEnabled = !soundEnabled;
    const iconElem = document.getElementById('sound-icon');
    if (iconElem) {
        iconElem.setAttribute('data-lucide', soundEnabled ? 'volume-2' : 'volume-x');
        if (window.lucide) lucide.createIcons();
    }
    showToast(soundEnabled ? 'هشدارهای صوتی فعال شد.' : 'هشدارهای صوتی بی‌صدا شد.', 'info');
}

// WebSocket Live Stream Connection with Exponential Backoff
let wsReconnectDelay = 2000;
let wsReconnectTimeout = null;

function initWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.host}/ws/live`;

    try {
        if (ws) {
            try { ws.close(); } catch(e) {}
        }
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('⚡ WebSocket Live Stream connected!');
            wsReconnectDelay = 2000;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'TICK_UPDATE') {
                    handleLiveTick(data);
                }
            } catch (e) {}
        };

        ws.onclose = () => {
            clearTimeout(wsReconnectTimeout);
            wsReconnectTimeout = setTimeout(initWebSocket, wsReconnectDelay);
            wsReconnectDelay = Math.min(wsReconnectDelay * 1.5, 10000);
        };
        ws.onerror = () => {
            try { ws.close(); } catch(e) {}
        };
    } catch (e) {}
}

window.addEventListener('beforeunload', () => {
    clearInterval(pollInterval);
    clearTimeout(wsReconnectTimeout);
    if (ws) {
        try { ws.close(); } catch(e) {}
    }
});

function handleLiveTick(data) {
    if (data.symbol === currentSymbol || currentSymbol === 'EURUSD') {
        const askElem = document.getElementById('live-ask');
        const bidElem = document.getElementById('live-bid');
        const spElem = document.getElementById('live-spread');

        if (askElem && data.ask) {
            const oldAsk = parseFloat(askElem.innerText) || 0;
            askElem.innerText = data.ask.toFixed(5);
            askElem.classList.remove('flash-up', 'flash-down');
            void askElem.offsetWidth;
            if (data.ask > oldAsk) {
                askElem.classList.add('flash-up');
            } else if (data.ask < oldAsk) {
                askElem.classList.add('flash-down');
            }
        }

        if (bidElem && data.bid) {
            bidElem.innerText = data.bid.toFixed(5);
        }

        if (spElem && data.spread_points !== undefined) {
            spElem.innerText = `${data.spread_points} پوینت (${(data.spread_points / 10).toFixed(1)} پیپ)`;
        }
    }

    // Live HUD updates
    if (data.account && data.account.balance) {
        const balElem = document.getElementById('hud-balance');
        const eqElem = document.getElementById('hud-equity');
        const profElem = document.getElementById('hud-profit');
        const freeMargElem = document.getElementById('hud-free-margin');

        if (balElem) balElem.innerText = `$${data.account.balance.toLocaleString()}`;
        if (eqElem) eqElem.innerText = `$${data.account.equity.toLocaleString()}`;
        if (freeMargElem) freeMargElem.innerText = `$${data.account.margin_free.toLocaleString()}`;
        
        if (profElem) {
            profElem.innerText = `${data.account.profit >= 0 ? '+' : ''}$${data.account.profit.toFixed(2)}`;
            profElem.className = `font-bold text-xs ${data.account.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
        }
    }

    if (data.positions) {
        renderPositions(data.positions);
    }
}

// Left Dock Switcher
function switchMainView(view) {
    activeMainView = view;
    try { localStorage.setItem('ntk_main_view', view); } catch (e) {}
    document.querySelectorAll('.dock-btn').forEach(btn => btn.classList.remove('active'));

    const activeDock = document.getElementById(`dock-btn-${view}`);
    if (activeDock) activeDock.classList.add('active');

    const views = ['trading', 'decisions', 'history', 'fleet', 'intel', 'matrix', 'strategies', 'ailogs', 'portfolio'];
    views.forEach(v => {
        const elem = document.getElementById(`view-${v}`);
        if (elem) elem.classList.add('hidden');
    });

    const activeContainer = document.getElementById(`view-${view}`);
    if (activeContainer) activeContainer.classList.remove('hidden');

    if (view === 'decisions') {
        fetchDecisionsHistory();
    } else if (view === 'history') {
        fetchTradesHistory();
        fetchPerformanceSummary();
        fetchAiTradeInsights();
    } else if (view === 'fleet') {
        fetchFleetAgents();
        fetchSignalsFeed();
    } else if (view === 'intel') {
        fetchMarketIntel();
        fetchEconomicCalendar();
    } else if (view === 'matrix') {
        fetchMatrixAnalytics();
    } else if (view === 'strategies') {
        fetchStrategies();
    } else if (view === 'ailogs') {
        fetchAiAuditLogs();
    } else if (view === 'portfolio') {
        fetchPortfolioPairsAnalysis();
    } else if (view === 'trading') {
        fetchMarketData(true);
        fetchPositions();
        fetchConfluence();
    }
}

// Right Deck Switcher
function switchDeckTab(tab) {
    try { localStorage.setItem('ntk_deck_tab', tab); } catch (e) {}
    ['ai', 'scalp', 'manual', 'auto'].forEach(t => {
        const btn = document.getElementById(`deck-tab-${t}`);
        const panel = document.getElementById(`deck-panel-${t}`);
        if (btn) {
            btn.classList.remove('active');
            if (t === 'scalp') btn.classList.add('text-amber-300');
        }
        if (panel) panel.classList.add('hidden');
    });

    const activeBtn = document.getElementById(`deck-tab-${tab}`);
    const activePanel = document.getElementById(`deck-panel-${tab}`);
    if (activeBtn) activeBtn.classList.add('active');
    if (activePanel) activePanel.classList.remove('hidden');

    if (tab === 'scalp') {
        fetchActiveScalps();
    }
}

// Bottom Table Switcher
function switchBottomTab(tab) {
    try { localStorage.setItem('ntk_bottom_tab', tab); } catch (e) {}
    ['positions', 'history', 'logs'].forEach(t => {
        const btn = document.getElementById(`btn-btab-${t}`);
        const panel = document.getElementById(`panel-${t}`);
        if (btn) btn.classList.remove('active');
        if (panel) panel.classList.add('hidden');
    });

    const activeBtn = document.getElementById(`btn-btab-${tab}`);
    const activePanel = document.getElementById(`panel-${tab}`);
    if (activeBtn) activeBtn.classList.add('active');
    if (activePanel) activePanel.classList.remove('hidden');

    if (tab === 'history') fetchBottomHistory();
    if (tab === 'logs') fetchBottomLogs();
}

// Toast Notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-msg flex items-center space-x-2 space-x-reverse px-3.5 py-2.5 rounded-xl shadow-xl text-xs font-semibold text-white transition ${
        type === 'success' ? 'bg-emerald-600 border border-emerald-500' :
        type === 'error' ? 'bg-rose-600 border border-rose-500' :
        type === 'warning' ? 'bg-amber-600 border border-amber-500' :
        'bg-blue-600 border border-blue-500'
    }`;

    const icon = type === 'success' ? 'check-circle' :
                 type === 'error' ? 'alert-triangle' :
                 type === 'warning' ? 'alert-circle' : 'info';

    toast.innerHTML = `
        <i data-lucide="${icon}" class="w-4 h-4"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 250);
    }, 3500);
}

// --- Unified Custom Modal Dialogs (No native browser alerts/prompts) ---

function showCustomConfirm(title, message, isDanger = false) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-confirm-modal');
        const titleElem = document.getElementById('confirm-modal-title');
        const msgElem = document.getElementById('confirm-modal-msg');
        const okBtn = document.getElementById('confirm-modal-ok-btn');
        const cancelBtn = document.getElementById('confirm-modal-cancel-btn');

        if (!modal || !okBtn || !cancelBtn) {
            resolve(true);
            return;
        }

        if (titleElem) titleElem.innerText = title;
        if (msgElem) msgElem.innerText = message;

        if (isDanger) {
            okBtn.className = 'flex-1 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl transition shadow-md shadow-rose-600/20';
        } else {
            okBtn.className = 'flex-1 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition shadow-md shadow-blue-600/20';
        }

        modal.classList.remove('hidden');

        const cleanup = (val) => {
            modal.classList.add('hidden');
            okBtn.onclick = null;
            cancelBtn.onclick = null;
            resolve(val);
        };

        okBtn.onclick = () => cleanup(true);
        cancelBtn.onclick = () => cleanup(false);
    });
}

function showCustomPrompt(title, label, defaultValue = '') {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-prompt-modal');
        const titleElem = document.getElementById('prompt-modal-title');
        const labelElem = document.getElementById('prompt-modal-label');
        const inputElem = document.getElementById('prompt-modal-input');
        const okBtn = document.getElementById('prompt-modal-ok-btn');

        if (!modal || !inputElem || !okBtn) {
            resolve(defaultValue);
            return;
        }

        if (titleElem) titleElem.innerText = title;
        if (labelElem) labelElem.innerText = label;
        inputElem.value = defaultValue;

        modal.classList.remove('hidden');
        inputElem.focus();

        const cleanup = (val) => {
            modal.classList.add('hidden');
            okBtn.onclick = null;
            inputElem.onkeydown = null;
            resolve(val);
        };

        okBtn.onclick = () => cleanup(inputElem.value.trim());
        inputElem.onkeydown = (e) => {
            if (e.key === 'Enter') cleanup(inputElem.value.trim());
            if (e.key === 'Escape') cleanup(null);
        };

        window.closeCustomPrompt = (val) => cleanup(val);
    });
}

async function fetchAiTelemetry() {
    try {
        const res = await fetch('/api/stats/header-telemetry');
        const data = await res.json();
        
        // Header Telemetry Hub
        const ai = data.ai_telemetry || {};
        const sentElem = document.getElementById('hdr-ai-sent');
        const pendElem = document.getElementById('hdr-ai-pending');
        const succElem = document.getElementById('hdr-ai-success');
        const failElem = document.getElementById('hdr-ai-failed');
        const pendDot = document.getElementById('hdr-ai-pending-dot');

        if (sentElem) sentElem.innerText = ai.sent || 0;
        if (pendElem) pendElem.innerText = ai.pending || 0;
        if (succElem) succElem.innerText = ai.success || 0;
        if (failElem) failElem.innerText = ai.failed || 0;

        if (pendDot) {
            pendDot.className = (ai.pending > 0) ? 'w-2 h-2 rounded-full bg-amber-400 animate-pulse' : 'w-2 h-2 rounded-full bg-slate-500';
        }

        // Live Stats Strip Bar
        const statOpen = document.getElementById('stat-open-count');
        const statMax = document.getElementById('stat-max-allowed');
        const statProfit = document.getElementById('stat-open-profit-badge');
        const stat1h = document.getElementById('stat-1h-trades');
        const stat1hWins = document.getElementById('stat-1h-wins-badge');
        const stat24h = document.getElementById('stat-24h-trades');
        const stat24hWins = document.getElementById('stat-24h-wins-badge');
        const stat7d = document.getElementById('stat-7d-trades');
        const stat7dWins = document.getElementById('stat-7d-wins-badge');
        const statAiSent = document.getElementById('stat-ai-sent');
        const statAiSucc = document.getElementById('stat-ai-success');
        const statAiFail = document.getElementById('stat-ai-failed');

        if (statOpen) statOpen.innerText = data.open_positions_count || 0;
        if (statMax) statMax.innerText = data.max_allowed_positions || 10;
        if (statProfit) {
            const pnl = data.open_positions_profit || 0.0;
            statProfit.innerText = `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`;
            statProfit.className = `text-[10px] px-1.5 py-0.2 rounded font-mono font-bold ${pnl >= 0 ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60' : 'bg-rose-950/80 text-rose-400 border border-rose-800/60'}`;
        }

        // 1h
        if (stat1h && data.last_1h) {
            stat1h.innerText = `${data.last_1h.total || 0} معامله`;
            if (stat1hWins) stat1hWins.innerText = `${data.last_1h.wins || 0} موفق (${data.last_1h.win_rate || 0}%)`;
        }

        // 24h
        if (stat24h && data.last_24h) {
            stat24h.innerText = `${data.last_24h.total || 0} معامله`;
            if (stat24hWins) stat24hWins.innerText = `${data.last_24h.wins || 0} موفق (${data.last_24h.win_rate || 0}%)`;
        }

        // 7d
        if (stat7d && data.last_7d) {
            stat7d.innerText = `${data.last_7d.total || 0} معامله`;
            if (stat7dWins) stat7dWins.innerText = `${data.last_7d.wins || 0} موفق (${data.last_7d.win_rate || 0}%)`;
        }

        // Strip AI Telemetry
        if (statAiSent) statAiSent.innerText = ai.sent || 0;
        if (statAiSucc) statAiSucc.innerText = ai.success || 0;
        if (statAiFail) statAiFail.innerText = ai.failed || 0;

    } catch (e) {}
}


// Chart.js Setup
function initChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'قیمت پایانی (Close)',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.06)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.15,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                },
                {
                    label: 'EMA 9',
                    data: [],
                    borderColor: '#10b981',
                    borderWidth: 1.2,
                    fill: false,
                    pointRadius: 0,
                    borderDash: [2, 2],
                },
                {
                    label: 'EMA 21',
                    data: [],
                    borderColor: '#f59e0b',
                    borderWidth: 1.2,
                    fill: false,
                    pointRadius: 0,
                    borderDash: [3, 3],
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#64748b',
                        font: { family: 'Vazirmatn', size: 10 },
                        boxWidth: 12
                    }
                },
                tooltip: {
                    backgroundColor: '#0f172a',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#1e293b',
                    borderWidth: 1,
                    padding: 6,
                    bodyFont: { family: 'JetBrains Mono', size: 11 }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(30, 41, 59, 0.4)' },
                    ticks: { color: '#475569', maxTicksLimit: 7, font: { size: 9 } }
                },
                y: {
                    position: 'right',
                    grid: { color: 'rgba(30, 41, 59, 0.4)' },
                    ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
                }
            }
        }
    });
}

// Setup Event Listeners
function setupEventListeners() {
    const symbolSelect = document.getElementById('select-symbol');
    if (symbolSelect) {
        symbolSelect.addEventListener('change', (e) => {
            currentSymbol = e.target.value;
            try { localStorage.setItem('ntk_symbol', currentSymbol); } catch (err) {}
            fetchMarketData(true);
            fetchAIAnalysis();
            fetchConfluence();
        });
    }

    document.querySelectorAll('.tf-pill').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tf-pill').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentTimeframe = e.target.getAttribute('data-tf');
            try { localStorage.setItem('ntk_timeframe', currentTimeframe); } catch (err) {}
            fetchMarketData(true);
            fetchAIAnalysis();
        });
    });

    const refreshBtn = document.getElementById('btn-refresh-market');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            fetchMarketData(true);
            fetchConfluence();
            showToast('داده‌ها به‌روزرسانی شد.', 'info');
        });
    }

    const aiBtn = document.getElementById('btn-request-ai');
    if (aiBtn) aiBtn.addEventListener('click', () => fetchAIAnalysis());

    const execAiBtn = document.getElementById('btn-execute-ai-trade');
    if (execAiBtn) execAiBtn.addEventListener('click', () => executeAITrade());

    const buyBtn = document.getElementById('btn-manual-buy');
    if (buyBtn) buyBtn.addEventListener('click', () => executeManualTrade('BUY'));

    const sellBtn = document.getElementById('btn-manual-sell');
    if (sellBtn) sellBtn.addEventListener('click', () => executeManualTrade('SELL'));

    const closeAllBtn = document.getElementById('btn-close-all');
    if (closeAllBtn) closeAllBtn.addEventListener('click', () => closeAllPositions());

    const autoBtn = document.getElementById('btn-toggle-auto');
    if (autoBtn) autoBtn.addEventListener('click', () => toggleAutoTrader());

    const scalpToggleBtn = document.getElementById('btn-toggle-scalper');
    if (scalpToggleBtn) scalpToggleBtn.addEventListener('click', () => toggleScalperEngine());
}

// Fetch Terminal and Account Info
async function fetchTerminalAndAccount() {
    try {
        const [termRes, accRes] = await Promise.all([
            fetch('/api/terminal/status'),
            fetch('/api/account')
        ]);

        const termData = await termRes.json();
        const accData = await accRes.json();

        const mt5Dot = document.getElementById('hud-mt5-dot');
        const mt5Text = document.getElementById('hud-mt5-text');

        if (termData.connected) {
            if (mt5Dot) mt5Dot.className = 'w-2 h-2 rounded-full bg-emerald-500 animate-pulse';
            if (mt5Text) mt5Text.innerText = 'MT5: آنلاین';
        } else {
            if (mt5Dot) mt5Dot.className = 'w-2 h-2 rounded-full bg-rose-500';
            if (mt5Text) mt5Text.innerText = 'MT5: قطع';
        }

        if (accData && accData.login) {
            const balElem = document.getElementById('hud-balance');
            const eqElem = document.getElementById('hud-equity');
            const profElem = document.getElementById('hud-profit');
            const freeMargElem = document.getElementById('hud-free-margin');

            if (balElem) balElem.innerText = `$${accData.balance.toLocaleString()}`;
            if (eqElem) eqElem.innerText = `$${accData.equity.toLocaleString()}`;
            if (freeMargElem) freeMargElem.innerText = `$${accData.margin_free.toLocaleString()}`;
            
            if (profElem) {
                profElem.innerText = `${accData.profit >= 0 ? '+' : ''}$${accData.profit.toFixed(2)}`;
                profElem.className = `font-bold text-xs ${accData.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
            }
        }
        syncAutoTraderStatus();
    } catch (e) {}
}
// Chart Type Switcher
let currentChartType = 'line'; // 'line' or 'candle'

function setChartType(type, persist = true) {
    currentChartType = type;
    if (persist) {
        try { localStorage.setItem('ntk_chart_mode', type); } catch (e) {}
    }
    const btnLine = document.getElementById('btn-chart-mode-line');
    const btnCandle = document.getElementById('btn-chart-mode-candle');
    if (type === 'line') {
        if (btnLine) btnLine.className = 'px-2.5 py-1 rounded text-cyan-400 bg-cyan-950/80 font-bold border border-cyan-800/80 transition';
        if (btnCandle) btnCandle.className = 'px-2.5 py-1 rounded text-slate-400 hover:text-white transition';
    } else {
        if (btnCandle) btnCandle.className = 'px-2.5 py-1 rounded text-amber-400 bg-amber-950/80 font-bold border border-amber-800/80 transition';
        if (btnLine) btnLine.className = 'px-2.5 py-1 rounded text-slate-400 hover:text-white transition';
    }
    fetchMarketData(true);
}

// --- Resizable Deck Splitter & UI Preferences Persistence ---

function initResizableDeckSplitter() {
    const handle = document.getElementById('deck-resizer-handle');
    const deck = document.getElementById('right-action-deck');
    if (!handle || !deck) return;

    let isDragging = false;
    let startX = 0;
    let startWidth = 0;

    handle.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.clientX;
        startWidth = deck.getBoundingClientRect().width;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const delta = startX - e.clientX;
        let newWidth = startWidth + delta;
        newWidth = Math.max(280, Math.min(720, newWidth));
        deck.style.width = `${newWidth}px`;
    });

    document.addEventListener('mouseup', () => {
        if (!isDragging) return;
        isDragging = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        const finalWidth = parseInt(deck.style.width, 10);
        if (finalWidth >= 280 && finalWidth <= 720) {
            try { localStorage.setItem('ntk_deck_width', finalWidth); } catch (e) {}
        }
    });

    // Touch support for touchscreens
    handle.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            isDragging = true;
            startX = e.touches[0].clientX;
            startWidth = deck.getBoundingClientRect().width;
        }
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
        if (!isDragging || e.touches.length !== 1) return;
        const delta = startX - e.touches[0].clientX;
        let newWidth = Math.max(280, Math.min(720, startWidth + delta));
        deck.style.width = `${newWidth}px`;
    }, { passive: true });

    document.addEventListener('touchend', () => {
        if (!isDragging) return;
        isDragging = false;
        const finalWidth = parseInt(deck.style.width, 10);
        if (finalWidth >= 280 && finalWidth <= 720) {
            try { localStorage.setItem('ntk_deck_width', finalWidth); } catch (e) {}
        }
    });
}

function restoreUserUIPreferences() {
    try {
        // 1. Restore Deck Width
        const savedWidth = localStorage.getItem('ntk_deck_width');
        const deck = document.getElementById('right-action-deck');
        if (deck && savedWidth) {
            const w = parseInt(savedWidth, 10);
            if (w >= 280 && w <= 720) {
                deck.style.width = `${w}px`;
            }
        }

        // 2. Restore Symbol
        const savedSymbol = localStorage.getItem('ntk_symbol');
        if (savedSymbol) {
            currentSymbol = savedSymbol;
            const symSelect = document.getElementById('select-symbol');
            if (symSelect) symSelect.value = savedSymbol;
        }

        // 3. Restore Timeframe
        const savedTf = localStorage.getItem('ntk_timeframe');
        if (savedTf) {
            currentTimeframe = savedTf;
            document.querySelectorAll('.tf-pill').forEach(b => {
                if (b.getAttribute('data-tf') === savedTf) {
                    b.classList.add('active');
                } else {
                    b.classList.remove('active');
                }
            });
        }

        // 4. Restore Chart Mode
        const savedChartMode = localStorage.getItem('ntk_chart_mode');
        if (savedChartMode) {
            setChartType(savedChartMode, false);
        }

        // 5. Restore Deck Tab
        const savedDeckTab = localStorage.getItem('ntk_deck_tab');
        if (savedDeckTab) {
            switchDeckTab(savedDeckTab);
        }

        // 6. Restore Bottom Tab
        const savedBottomTab = localStorage.getItem('ntk_bottom_tab');
        if (savedBottomTab) {
            switchBottomTab(savedBottomTab);
        }

        // 7. Restore Main View
        const savedMainView = localStorage.getItem('ntk_main_view');
        if (savedMainView && savedMainView !== 'trading') {
            switchMainView(savedMainView);
        }
    } catch (e) {
        console.warn('Preferences restore:', e);
    }
}
// Fetch Market & Technical Indicator Data
async function fetchMarketData(updateChart = true) {
    try {
        const [ovRes, techRes] = await Promise.all([
            fetch(`/api/symbol/${currentSymbol}/overview`),
            fetch(`/api/symbol/${currentSymbol}/technical?timeframe=${currentTimeframe}`)
        ]);

        const ov = await ovRes.json();
        const tech = await techRes.json();

        if (ov && ov.ask) {
            const askElem = document.getElementById('live-ask');
            const bidElem = document.getElementById('live-bid');
            const spElem = document.getElementById('live-spread');
            if (askElem) askElem.innerText = ov.ask.toFixed(ov.digits || 5);
            if (bidElem) bidElem.innerText = ov.bid.toFixed(ov.digits || 5);
            if (spElem) spElem.innerText = `${ov.spread_points} پوینت (${(ov.spread_points / 10).toFixed(1)} پیپ)`;
        }

        if (tech && tech.trend) {
            const trendElem = document.getElementById('tech-trend');
            const rsiElem = document.getElementById('tech-rsi');
            const suppElem = document.getElementById('tech-support');
            const resElem = document.getElementById('tech-resistance');
            const e9Elem = document.getElementById('tech-ema9');

            if (trendElem) trendElem.innerText = tech.trend;
            if (rsiElem) rsiElem.innerText = tech.rsi;
            if (suppElem) suppElem.innerText = tech.support;
            if (resElem) resElem.innerText = tech.resistance;
            if (e9Elem) e9Elem.innerText = tech.atr;

            if (updateChart && priceChart && tech.candles) {
                const labels = tech.candles.map(c => new Date(c.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
                
                if (currentChartType === 'candle') {
                    // Candlestick / Bar representation with Bullish/Bearish colors
                    priceChart.data.labels = labels;
                    priceChart.data.datasets[0].type = 'bar';
                    priceChart.data.datasets[0].label = 'کندل (Open-Close)';
                    priceChart.data.datasets[0].data = tech.candles.map(c => [Math.min(c.open, c.close), Math.max(c.open, c.close)]);
                    priceChart.data.datasets[0].backgroundColor = tech.candles.map(c => c.close >= c.open ? 'rgba(16, 185, 129, 0.85)' : 'rgba(244, 63, 94, 0.85)');
                    priceChart.data.datasets[0].borderColor = tech.candles.map(c => c.close >= c.open ? '#10b981' : '#f43f5e');
                    priceChart.data.datasets[0].borderWidth = 1;
                } else {
                    // Smooth Line Chart
                    const closes = tech.candles.map(c => c.close);
                    priceChart.data.labels = labels;
                    priceChart.data.datasets[0].type = 'line';
                    priceChart.data.datasets[0].label = 'قیمت پایانی (Close)';
                    priceChart.data.datasets[0].data = closes;
                    priceChart.data.datasets[0].borderColor = '#3b82f6';
                    priceChart.data.datasets[0].backgroundColor = 'rgba(59, 130, 246, 0.06)';
                    priceChart.data.datasets[0].borderWidth = 2;
                }
                priceChart.update('none');
            }
        }
    } catch (e) {}
}

// Confluence Fetcher
async function fetchConfluence() {
    try {
        const res = await fetch(`/api/analyze/confluence/${currentSymbol}`);
        const data = await res.json();
        const badge = document.getElementById('confluence-badge');
        if (badge) {
            badge.innerText = data.confluence_score || '---';
            badge.className = `font-bold text-[11px] ${
                data.overall_action === 'BUY' ? 'text-emerald-400' :
                data.overall_action === 'SELL' ? 'text-rose-400' : 'text-slate-400'
            }`;
        }
    } catch (e) {}
}

// Quick Risk Calculator
async function quickSetRisk(pct) {
    try {
        const slInput = document.getElementById('manual-sl');
        const slPips = slInput && slInput.value ? parseFloat(slInput.value) : 25.0;

        const res = await fetch(`/api/tools/risk-calc?risk_percent=${pct}&sl_pips=${slPips}&symbol=${currentSymbol}`);
        const data = await res.json();
        const lotInput = document.getElementById('manual-lot');
        if (lotInput && data.lot_size) {
            lotInput.value = data.lot_size;
            showToast(`حجم محاسبه شد: ${data.lot_size} لات (${pct}% ریسک = $${data.risk_amount})`, 'success');
        }
    } catch (e) {}
}

// Positions Rendering with 1-Click Break-Even & Inline Edit
function renderPositions(positions) {
    const countElem = document.getElementById('acc-pos-count');
    if (countElem) countElem.innerText = positions.length;

    const tbody = document.getElementById('positions-table-body');
    if (!tbody) return;

    if (!positions || positions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="11" class="py-6 text-center text-slate-500 font-sans">هیچ معامله بازی وجود ندارد.</td></tr>`;
        return;
    }

    tbody.innerHTML = positions.map(p => {
        const ai = p.ai_check || {};
        const secAgo = ai.seconds_ago !== undefined ? ai.seconds_ago : -1;
        const secText = ai.seconds_ago_formatted || (secAgo >= 0 ? `${secAgo} ثانیه پیش` : 'در صف بررسی...');
        const recText = ai.recommendation_fa || 'حفظ پوزیشن';
        const statusColor = ai.status_color || 'blue';
        const dotColor = statusColor === 'emerald' ? 'bg-emerald-400' :
                         (statusColor === 'rose' ? 'bg-rose-400' :
                         (statusColor === 'cyan' ? 'bg-cyan-400 animate-pulse' : 'bg-blue-400'));

        return `
            <tr class="hover:bg-slate-800/30 transition text-xs">
                <td class="py-2.5 pr-2 text-slate-400">#${p.ticket}</td>
                <td class="py-2.5 font-bold text-white">${p.symbol}</td>
                <td class="py-2.5 font-bold ${p.type === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}">${p.type}</td>
                <td class="py-2.5 font-mono">${p.volume}</td>
                <td class="py-2.5 font-mono">${p.open_price}</td>
                <td class="py-2.5 font-mono">${p.current_price}</td>
                <td class="py-2.5 font-mono text-rose-300">${p.sl || '-'}</td>
                <td class="py-2.5 font-mono text-emerald-300">${p.tp || '-'}</td>
                <td class="py-2.5 font-mono font-bold ${p.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${p.profit >= 0 ? '+' : ''}$${p.profit.toFixed(2)}</td>
                <td class="py-2 px-1 text-center font-sans">
                    <div class="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[#0b101c] border border-slate-800/90 text-[10px]">
                        <span class="w-2 h-2 rounded-full ${dotColor}"></span>
                        <span class="font-mono text-cyan-300 font-bold">${secText}</span>
                        <span class="text-slate-500 font-sans text-[9px]">•</span>
                        <span class="text-slate-200 font-medium truncate max-w-[140px]">${recText}</span>
                        <button onclick="reanalyzePositionWithAiAction(${p.ticket})" title="تحلیل مجدد فوری توسط هوش مصنوعی" class="px-1.5 py-0.5 rounded bg-[#151c2e] hover:bg-blue-900 border border-slate-700 text-blue-300 hover:text-white transition text-[9px]">
                            🤖 تحلیل
                        </button>
                    </div>
                </td>
                <td class="py-2.5 text-center">
                    <div class="flex items-center justify-center gap-1">
                        <button onclick="setBreakEven(${p.ticket})" title="انتقال حد ضرر به نقطه ورود (ریسک‌فری)" class="px-1.5 py-0.5 rounded bg-amber-950/80 hover:bg-amber-900 border border-amber-800/80 text-amber-300 text-[10px] font-bold">
                            BE
                        </button>
                        <button onclick="promptModifyPosition(${p.ticket}, ${p.sl || 0}, ${p.tp || 0})" title="تغییر حد ضرر و سود" class="px-1.5 py-0.5 rounded bg-blue-950/80 hover:bg-blue-900 border border-blue-800/80 text-blue-300 text-[10px]">
                            ✏️
                        </button>
                        <button onclick="closePosition(${p.ticket})" title="بستن فوری معامله" class="px-2 py-0.5 rounded bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-300 text-[10px]">
                            بستن
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function reanalyzePositionWithAiAction(ticket) {
    showToast(`در حال ارزیابی مجدد معامله #${ticket} با هوش مصنوعی...`, 'info');
    try {
        const res = await fetch(`/api/position/${ticket}/reanalyze`, { method: 'POST' });
        const data = await res.json();
        if (data.success && data.check) {
            showToast(`توصیه هوش مصنوعی برای #${ticket}: ${data.check.recommendation_fa}`, 'success');
            fetchPositions();
        } else {
            showToast(data.error || 'خطا در ارزیابی موقعیت', 'error');
        }
    } catch (e) {
        showToast(`خطا در ارسال درخواست: ${e.message}`, 'error');
    }
}

async function setBreakEven(ticket) {
    try {
        const res = await fetch(`/api/position/${ticket}/breakeven`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(`پوزیشن #${ticket} با موفقیت ریسک‌فری شد.`, 'success');
            fetchPositions();
        } else {
            showToast(data.error || 'خطا در اعمال ریسک‌فری', 'error');
        }
    } catch (e) {
        showToast('خطا در برقراری ارتباط با سرور', 'error');
    }
}

async function promptModifyPosition(ticket, currentSl, currentTp) {
    const sl = await showCustomPrompt(`ویرایش حد ضرر (SL) پوزیشن #${ticket}`, 'حد ضرر جدید را وارد کنید:', currentSl || '');
    if (sl === null) return;
    const tp = await showCustomPrompt(`ویرایش حد سود (TP) پوزیشن #${ticket}`, 'حد سود جدید را وارد کنید:', currentTp || '');
    if (tp === null) return;
    try {
        const res = await fetch(`/api/position/${ticket}/modify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sl: sl ? parseFloat(sl) : null,
                tp: tp ? parseFloat(tp) : null
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`حد سود/ضرر پوزیشن #${ticket} با موفقیت ویرایش شد.`, 'success');
            fetchPositions();
        } else {
            showToast(data.error || 'خطا در ویرایش پوزیشن', 'error');
        }
    } catch (e) {
        showToast('خطا در ارسال درخواست', 'error');
    }
}

async function fetchPositions() {
    try {
        const res = await fetch('/api/positions');
        const positions = await res.json();
        renderPositions(positions);
    } catch (e) {}
}

async function fetchAiTradeInsights() {
    try {
        const res = await fetch('/api/ai/trade-insights?limit=20');
        const data = await res.json();

        const summaryElem = document.getElementById('ai-journal-summary');
        if (summaryElem) {
            summaryElem.innerHTML = `
                <div class="flex items-center justify-between mb-1.5 font-bold">
                    <span class="text-purple-300 font-sans">خلاصه ارزیابی هوش مصنوعی (AI Debrief):</span>
                    <span class="font-mono text-emerald-400">سود خالص: ${data.total_pnl >= 0 ? '+' : ''}$${data.total_pnl} | وین‌ریت: ${data.win_rate}% | فاکتور سود: ${data.profit_factor}</span>
                </div>
                <p class="text-slate-300 leading-relaxed font-sans">${data.summary_fa || 'اطلاعات در دسترس نیست.'}</p>
            `;
        }

        const tipsContainer = document.getElementById('ai-journal-tips');
        if (tipsContainer && data.actionable_tips) {
            tipsContainer.innerHTML = data.actionable_tips.map(tip => `
                <div class="bg-[#0b101c] p-2.5 rounded-lg border border-slate-800/80 text-[11px] text-slate-300 flex items-start space-x-1.5 space-x-reverse">
                    <span class="text-amber-400 font-bold shrink-0">💡</span>
                    <span class="leading-relaxed">${tip}</span>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Error fetching AI trade insights:', e);
    }
}
// AI Analysis
async function fetchAIAnalysis(forceRefresh = true) {
    const aiBtn = document.getElementById('btn-request-ai');
    const aiBtnText = document.getElementById('ai-btn-text');
    if (aiBtn) aiBtn.disabled = true;
    if (aiBtnText) aiBtnText.innerText = 'در حال تحلیل با هوش مصنوعی...';

    const actionBadge = document.getElementById('ai-action-badge');
    const confElem = document.getElementById('ai-confidence');
    const entryElem = document.getElementById('ai-entry');
    const slElem = document.getElementById('ai-sl');
    const tpElem = document.getElementById('ai-tp');
    const reasonElem = document.getElementById('ai-reasoning');

    if (reasonElem) reasonElem.innerText = 'هوش مصنوعی در حال پردازش شاخص‌ها و اخبار زنده بازار...';

    try {
        const res = await fetch(`/api/analyze/${currentSymbol}?timeframe=${currentTimeframe}&force_refresh=${forceRefresh ? 'true' : 'false'}`);
        const data = await res.json();
        latestAIResult = data;

        if (actionBadge) {
            actionBadge.innerText = data.action;
            actionBadge.className = `text-2xl font-black mt-0.5 ${
                data.action === 'BUY' ? 'text-emerald-400' :
                data.action === 'SELL' ? 'text-rose-400' : 'text-amber-400'
            }`;
        }
        const symbolBadge = document.getElementById('ai-symbol-badge');
        if (symbolBadge) symbolBadge.innerText = `${data.symbol || currentSymbol} (${data.timeframe || currentTimeframe})`;
        
        const actionSymbol = document.getElementById('ai-action-symbol');
        if (actionSymbol) actionSymbol.innerText = data.symbol || currentSymbol;

        if (confElem) confElem.innerText = `${data.confidence || 0}%`;
        if (entryElem) entryElem.innerText = data.current_price || '---';
        if (slElem) slElem.innerText = data.suggested_sl || '---';
        if (tpElem) tpElem.innerText = data.suggested_tp || '---';
        if (reasonElem) reasonElem.innerText = data.rationale || 'تحلیل تکمیل شد.';
        // Render Weighted Probabilities Summary
        // Render Weighted Probabilities Summary & Vote Counts
        if (data.weighted_probabilities) {
            const wp = data.weighted_probabilities;
            const buyElem = document.getElementById('ai-prob-buy');
            const sellElem = document.getElementById('ai-prob-sell');
            const buyBar = document.getElementById('ai-bar-buy');
            const sellBar = document.getElementById('ai-bar-sell');

            if (buyElem) buyElem.innerText = `${wp.buy_probability}%`;
            if (sellElem) sellElem.innerText = `${wp.sell_probability}%`;
            if (buyBar) buyBar.style.width = `${Math.max(5, Math.min(95, wp.buy_probability))}%`;
            if (sellBar) sellBar.style.width = `${Math.max(5, Math.min(95, wp.sell_probability))}%`;

            // Render Raw Vote Counts (بدون ضریب)
            if (wp.raw_votes) {
                const rawBuy = document.getElementById('raw-votes-buy');
                const rawSell = document.getElementById('raw-votes-sell');
                const rawHold = document.getElementById('raw-votes-hold');
                if (rawBuy) rawBuy.innerText = `${wp.raw_votes.buy} رای`;
                if (rawSell) rawSell.innerText = `${wp.raw_votes.sell} رای`;
                if (rawHold) rawHold.innerText = `${wp.raw_votes.hold} رای`;
            }

            // Render Weighted Vote Scores (با ضریب)
            if (wp.weighted_votes) {
                const wBuy = document.getElementById('weighted-votes-buy');
                const wSell = document.getElementById('weighted-votes-sell');
                const wHold = document.getElementById('weighted-votes-hold');
                if (wBuy) wBuy.innerText = `${wp.weighted_votes.buy_weight}x`;
                if (wSell) wSell.innerText = `${wp.weighted_votes.sell_weight}x`;
                if (wHold) wHold.innerText = `${wp.weighted_votes.hold_weight}x`;
            }
        }
        // Render Strategy Breakdown List
        if (data.strategy_breakdown) {
            const listElem = document.getElementById('active-strat-probs-list');
            if (listElem) {
                listElem.innerHTML = data.strategy_breakdown.map((sb, idx) => {
                    const actionColor = sb.action === 'BUY' ? 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60' :
                                        (sb.action === 'SELL' ? 'text-rose-400 bg-rose-950/60 border-rose-800/60' : 'text-slate-400 bg-slate-900 border-slate-800');
                    return `
                        <div class="flex items-center justify-between p-1.5 rounded bg-[#101726]/60 border border-slate-800/50 hover:border-slate-700 transition text-[11px]">
                            <div class="flex items-center space-x-1.5 space-x-reverse truncate max-w-[200px]">
                                <span class="font-mono text-[9px] text-slate-500">#${idx + 1}</span>
                                <span class="text-slate-200 font-sans truncate font-medium">${sb.title_fa || sb.name}</span>
                                <span class="text-cyan-400 font-mono text-[10px] font-bold">(${sb.weight}x)</span>
                            </div>
                            <div class="flex items-center gap-2 shrink-0 font-mono">
                                <span class="px-1.5 py-0.5 rounded text-[9px] font-bold border ${actionColor}">
                                    ${sb.action}
                                </span>
                                <span class="font-bold text-slate-300 w-10 text-left">${sb.probability}%</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
        if (data.action && data.action !== 'HOLD') {
            playSoundAlert('signal');
        }
    } catch (e) {
        if (reasonElem) reasonElem.innerText = `خطا در دریافت تحلیل: ${e.message}`;
    } finally {
        if (aiBtn) aiBtn.disabled = false;
        if (aiBtnText) aiBtnText.innerText = 'تحلیل مجدد بازار';
    }
}

function toggleStrategyBreakdown() {
    const container = document.getElementById('active-strat-probs-container');
    const chevron = document.getElementById('icon-strat-chevron');
    if (!container) return;
    
    const isHidden = container.classList.contains('hidden');
    if (isHidden) {
        container.classList.remove('hidden');
        if (chevron) chevron.style.transform = 'rotate(180deg)';
    } else {
        container.classList.add('hidden');
        if (chevron) chevron.style.transform = 'rotate(0deg)';
    }
}

function openStrategyBreakdownModal() {
    const modal = document.getElementById('strat-breakdown-modal');
    if (!modal) return;
    modal.classList.remove('hidden');

    if (latestAIResult && latestAIResult.weighted_probabilities) {
        const wp = latestAIResult.weighted_probabilities;
        const mBuy = document.getElementById('modal-prob-buy');
        const mSell = document.getElementById('modal-prob-sell');
        if (mBuy) mBuy.innerText = `${wp.buy_probability}%`;
        if (mSell) mSell.innerText = `${wp.sell_probability}%`;
    }

    const tbody = document.getElementById('modal-strat-table-body');
    if (tbody && latestAIResult && latestAIResult.strategy_breakdown) {
        tbody.innerHTML = latestAIResult.strategy_breakdown.map((sb, idx) => {
            const actionColor = sb.action === 'BUY' ? 'text-emerald-400 bg-emerald-950/60 border-emerald-800' :
                                (sb.action === 'SELL' ? 'text-rose-400 bg-rose-950/60 border-rose-800' : 'text-slate-400 bg-slate-900 border-slate-800');
            return `
                <tr class="hover:bg-slate-800/30 transition text-xs">
                    <td class="p-2.5 text-slate-500 font-mono">#${idx + 1}</td>
                    <td class="p-2.5 font-bold text-white font-sans">${sb.title_fa || sb.name}</td>
                    <td class="p-2.5 text-slate-400 font-sans">${sb.category || 'تکنیکال'}</td>
                    <td class="p-2.5 text-cyan-400 font-bold font-mono">${sb.weight}x</td>
                    <td class="p-2.5">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${actionColor}">
                            ${sb.action}
                        </span>
                    </td>
                    <td class="p-2.5 font-bold font-mono ${sb.action === 'BUY' ? 'text-emerald-400' : (sb.action === 'SELL' ? 'text-rose-400' : 'text-slate-300')}">
                        ${sb.probability}%
                    </td>
                    <td class="p-2.5 font-mono text-purple-300">${sb.win_rate || 75.0}%</td>
                </tr>
            `;
        }).join('');
    }
}

// --- AI Communications & Payload Audit Logs Center ---

let activeAiLogContext = 'all';

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.innerText || el.textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('محتوا با موفقیت در کلیپ‌بورد کپی شد.', 'success');
    }).catch(() => {
        showToast('خطا در دسترسی به کلیپ‌بورد', 'error');
    });
}

function filterAiLogsContext(contextType) {
    activeAiLogContext = contextType;
    document.querySelectorAll('.ailog-tab').forEach(b => {
        b.classList.remove('active', 'border-slate-700', 'bg-blue-950/80', 'text-blue-300', 'font-bold');
        b.classList.add('border-slate-800', 'bg-[#0b101c]', 'text-slate-300');
    });

    const activeBtn = document.getElementById(`btn-ailog-tab-${contextType}`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'border-slate-700', 'bg-blue-950/80', 'text-blue-300', 'font-bold');
        activeBtn.classList.remove('border-slate-800', 'bg-[#0b101c]', 'text-slate-300');
    }

    fetchAiAuditLogs();
}

async function fetchAiAuditLogs() {
    const container = document.getElementById('ailogs-feed-container');
    if (!container) return;

    try {
        const queryParam = activeAiLogContext === 'all' ? '' : `?context_type=${activeAiLogContext}`;
        const res = await fetch(`/api/ai/logs${queryParam}`);
        const data = await res.json();
        const logs = data.logs || [];
        const summary = data.summary || {};

        // Update counts on tabs
        if (summary.total_logs !== undefined) {
            const allCount = document.getElementById('ailog-count-all');
            if (allCount) allCount.innerText = summary.total_logs;
        }
        if (summary.contexts) {
            Object.entries(summary.contexts).forEach(([ctx, meta]) => {
                const countElem = document.getElementById(`ailog-count-${ctx}`);
                if (countElem) countElem.innerText = meta.count || 0;
            });
        }

        renderAiAuditLogs(logs);
    } catch (e) {
        container.innerHTML = `<div class="card-pro p-6 text-center text-rose-400 font-sans">خطا در دریافت لاگ‌های هوش مصنوعی: ${e.message}</div>`;
    }
}

function renderAiAuditLogs(logs) {
    const container = document.getElementById('ailogs-feed-container');
    if (!container) return;

    if (!logs || logs.length === 0) {
        container.innerHTML = `
            <div class="card-pro p-8 text-center text-slate-500 font-sans space-y-2">
                <i data-lucide="inbox" class="w-8 h-8 text-slate-600 mx-auto"></i>
                <p>هیچ لاگ یا درخواستی برای این کانتکس ثبت نشده است.</p>
                <p class="text-xs text-slate-600">با ارسال پیام در چت یا اجرای تحلیل بازار، لاگ‌های ارسال و دریافت در اینجا ذخیره می‌شوند.</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    container.innerHTML = logs.map(l => {
        const isSuccess = l.status === 'SUCCESS';
        const isFallback = l.status === 'FALLBACK';
        const statusBadge = isSuccess 
            ? '<span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-bold">🟢 موفق (200 OK)</span>'
            : (isFallback ? '<span class="px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 text-[10px] font-bold">🟡 فال‌بک تحلیلی</span>'
                          : '<span class="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800 text-[10px] font-bold">🔴 خطا</span>');
        
        const contextNames = {
            'market_analysis': '📊 تحلیل جامع بازار',
            'scalper': '⚡ اسکالپینگ سریع M1',
            'chat': '🤖 دستیار گفتگو',
            'fleet': '🌐 ناوگان ایجنت‌ها',
            'news_intel': '📰 اخبار و سنتیمنت'
        };
        const ctxLabel = contextNames[l.context_type] || l.context_type;
        const promptId = `prompt-code-${l.id}`;
        const respId = `resp-code-${l.id}`;

        return `
            <div class="card-pro p-4 space-y-3 transition border-slate-800 hover:border-slate-700">
                <!-- Header Info Row -->
                <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5 text-xs">
                    <div class="flex items-center space-x-2 space-x-reverse">
                        <span class="font-bold text-white">${ctxLabel}</span>
                        <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-[#151c2e] text-cyan-400 border border-slate-700">مدل: ${l.model} (${l.provider || 'OmniRoute'})</span>
                        <span class="text-[10px] font-mono text-slate-400">${l.symbol || 'EURUSD'} • ${l.timeframe || 'M15'}</span>
                    </div>
                    <div class="flex items-center space-x-2 space-x-reverse font-mono text-[11px]">
                        <span class="text-amber-400 font-bold">⚡ ${l.latency_ms || 0}ms</span>
                        ${statusBadge}
                        <span class="text-slate-500 text-[10px]">${l.created_at}</span>
                    </div>
                </div>

                <!-- Parsed Decision Outcome Strip -->
                <div class="bg-[#0b101c] p-2 rounded-lg border border-slate-800/80 flex items-center justify-between text-xs font-mono">
                    <div class="flex items-center space-x-2 space-x-reverse">
                        <span class="text-slate-400 font-sans text-[11px]">سیگنال استخراج‌شده:</span>
                        <span class="font-bold ${l.parsed_action === 'BUY' ? 'text-emerald-400' : (l.parsed_action === 'SELL' ? 'text-rose-400' : 'text-amber-400')}">${l.parsed_action}</span>
                    </div>
                    <div class="flex items-center space-x-2 space-x-reverse">
                        <span class="text-slate-400 font-sans text-[11px]">ضریب اطمینان:</span>
                        <span class="font-bold text-cyan-400">${l.confidence || 50}%</span>
                    </div>
                </div>

                <!-- Sent & Received Payloads Grid (2 Columns) -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 text-xs">
                    <!-- Sent Prompt Box -->
                    <div class="bg-[#0b101c] rounded-xl border border-slate-800/90 flex flex-col overflow-hidden">
                        <div class="flex items-center justify-between px-3 py-2 bg-[#0e1422] border-b border-slate-800 text-[11px]">
                            <span class="font-bold text-cyan-400 flex items-center gap-1">
                                <span>📤 پرامپت و کانتکس ارسالی</span>
                            </span>
                            <button onclick="copyToClipboard('${promptId}')" class="text-[10px] text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 transition flex items-center gap-1 font-sans">
                                <span>📋 کپی پرامپت</span>
                            </button>
                        </div>
                        <pre id="${promptId}" class="p-3 text-[11px] font-mono text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap text-left dir-ltr select-all">${escapeHtml(l.prompt_sent)}</pre>
                    </div>

                    <!-- Received Response Box -->
                    <div class="bg-[#0b101c] rounded-xl border border-slate-800/90 flex flex-col overflow-hidden">
                        <div class="flex items-center justify-between px-3 py-2 bg-[#0e1422] border-b border-slate-800 text-[11px]">
                            <span class="font-bold text-emerald-400 flex items-center gap-1">
                                <span>📥 پاسخ دریافتی خام از هوش مصنوعی</span>
                            </span>
                            <button onclick="copyToClipboard('${respId}')" class="text-[10px] text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 transition flex items-center gap-1 font-sans">
                                <span>📋 کپی پاسخ</span>
                            </button>
                        </div>
                        <pre id="${respId}" class="p-3 text-[11px] font-mono text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap text-right dir-rtl select-all">${escapeHtml(l.response_received)}</pre>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

async function clearAiAuditLogsAction() {
    const confirmed = await showCustomConfirm('پاک‌سازی لاگ‌ها', 'آیا از پاک‌سازی تمام لاگ‌های ارسال و دریافت هوش مصنوعی اطمینان دارید؟', true);
    if (!confirmed) return;
    try {
        const res = await fetch('/api/ai/logs', { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showToast('تمام لاگ‌های هوش مصنوعی پاک‌سازی شدند.', 'success');
            fetchAiAuditLogs();
        }
    } catch (e) {
        showToast('خطا در پاک‌سازی لاگ‌ها', 'error');
    }
}

function closeStrategyBreakdownModal() {
    const modal = document.getElementById('strat-breakdown-modal');
    if (modal) modal.classList.add('hidden');
}

// 1-Click AI Execution with visible loading indicator
async function executeAITrade() {
    if (!latestAIResult || !latestAIResult.action || latestAIResult.action === 'HOLD') {
        showToast('سیگنال فعلی HOLD است.', 'warning');
        return;
    }

    const btn = document.getElementById('btn-execute-ai-trade');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block"></span><span>در حال ثبت معامله...</span>';
    }

    const payload = {
        symbol: currentSymbol,
        order_type: latestAIResult.action,
        volume: 0.01,
        sl: latestAIResult.suggested_sl,
        tp: latestAIResult.suggested_tp,
        comment: isScalpMode ? 'OmniRoute MicroScalp' : 'OmniRoute AI Signal'
    };

    try {
        const res = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('trade');
            showToast(`سفارش ${payload.order_type} با موفقیت اجرا شد (تیکت: #${data.order_ticket})`, 'success');
            fetchPositions();
            fetchTerminalAndAccount();
        } else {
            showToast(`خطا در ثبت معامله: ${data.error || 'نامشخص'}`, 'error');
        }
    } catch (e) {
        showToast(`خطای شبکه: ${e.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="zap" class="w-4 h-4"></i><span>⚡ روش دستی: اجرای فوری این سیگنال</span>';
            if (window.lucide) lucide.createIcons();
        }
    }
}
function setDirectLot(vol) {
    const input = document.getElementById('manual-lot');
    if (input) input.value = vol;
}
// Direct Trade Execution with loading state
async function executeManualTrade(orderType) {
    const durElem = document.getElementById('scalp-max-duration');
    const maxDur = durElem ? parseInt(durElem.value) || 0 : 0;

    if (maxDur > 0) {
        return executeInstantScalpAction(orderType);
    }

    const btn = document.getElementById(orderType === 'BUY' ? 'btn-manual-buy' : 'btn-manual-sell');
    const origText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin inline-block"></span><span>ارسال ${orderType}...</span>`;
    }

    const volInput = document.getElementById('manual-lot');
    const slInput = document.getElementById('manual-sl');
    const tpInput = document.getElementById('manual-tp');

    const payload = {
        symbol: currentSymbol,
        order_type: orderType,
        volume: parseFloat(volInput ? volInput.value : 0.01) || 0.01,
        sl: slInput && slInput.value ? parseFloat(slInput.value) : null,
        tp: tpInput && tpInput.value ? parseFloat(tpInput.value) : null,
        comment: 'Manual Web Order'
    };

    try {
        const res = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('trade');
            showToast(`سفارش مستقیم ${orderType} ثبت شد (تیکت: #${data.order_ticket})`, 'success');
            fetchPositions();
            fetchTerminalAndAccount();
        } else {
            showToast(`خطا: ${data.error || 'سفارش انجام نشد'}`, 'error');
        }
    } catch (e) {
        showToast(`خطای ارتباط: ${e.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origText;
            if (window.lucide) lucide.createIcons();
        }
    }
}
async function closePosition(ticket) {
    const confirmed = await showCustomConfirm('بستن معامله', `آیا از بستن پوزیشن #${ticket} اطمینان دارید؟`, true);
    if (!confirmed) return;
    try {
        const res = await fetch(`/api/position/${ticket}/close`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(`پوزیشن #${ticket} بسته شد.`, 'success');
            fetchPositions();
            fetchTerminalAndAccount();
        } else {
            showToast(`خطا: ${data.error}`, 'error');
        }
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    }
}

// Close All Positions
async function closeAllPositions() {
    const confirmed = await showCustomConfirm('بستن تمام معاملات', 'آیا از بستن تمام معاملات فعال اطمینان دارید؟', true);
    if (!confirmed) return;
    try {
        const res = await fetch('/api/positions/close-all', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'عملیات بستن انجام شد.', data.success ? 'success' : 'warning');
        fetchPositions();
        fetchTerminalAndAccount();
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    }
}
// Toggle Auto-Trader Mode with loading spinner and button state feedback
async function toggleAutoTrader() {
    const badge = document.getElementById('auto-engine-badge');
    const btn = document.getElementById('btn-toggle-auto');
    const isRunning = badge && badge.classList.contains('bg-emerald-500');

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin inline-block"></span><span>صبر کنید...</span>';
    }

    try {
        if (!isRunning) {
            const intervalVal = isScalpMode ? 15 : parseInt(document.getElementById('auto-interval')?.value || 60);
            const tf = isScalpMode ? 'M1' : currentTimeframe;
            
            const res = await fetch('/api/autotrade/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbols: [currentSymbol],
                    timeframe: tf,
                    interval_seconds: intervalVal,
                    auto_execute: true,
                    min_confidence: isScalpMode ? 70.0 : 75.0
                })
            });
            const data = await res.json();
            if (data.success) {
                if (badge) badge.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500 animate-pulse';
                if (btn) {
                    btn.className = 'px-3 py-1.5 rounded-lg font-bold text-xs bg-rose-600 hover:bg-rose-500 text-white transition shadow-sm';
                    btn.innerHTML = '<span id="auto-btn-text">توقف خودکار</span>';
                }
                showToast(`روش خودکار (${isScalpMode ? 'اسکالپینگ M1' : 'استاندارد M15'}) فعال شد.`, 'success');
            } else {
                showToast(`خطا در فعال‌سازی: ${data.message}`, 'warning');
            }
        } else {
            const res = await fetch('/api/autotrade/stop', { method: 'POST' });
            const data = await res.json();
            if (badge) badge.className = 'w-2.5 h-2.5 rounded-full bg-slate-500';
            if (btn) {
                btn.className = 'px-3 py-1.5 rounded-lg font-bold text-xs bg-blue-600 hover:bg-blue-500 text-white transition shadow-sm';
                btn.innerHTML = '<span id="auto-btn-text">فعال‌سازی</span>';
            }
            showToast('روش خودکار متوقف شد.', 'info');
        }
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    } finally {
        if (btn) btn.disabled = false;
        syncAutoTraderStatus();
    }
}

async function syncAutoTraderStatus() {
    try {
        const res = await fetch('/api/autotrade/status');
        const data = await res.json();
        const badge = document.getElementById('auto-engine-badge');
        const btn = document.getElementById('btn-toggle-auto');

        if (data && data.is_running) {
            if (badge) badge.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500 animate-pulse';
            if (btn) {
                btn.className = 'px-3 py-1.5 rounded-lg font-bold text-xs bg-rose-600 hover:bg-rose-500 text-white transition shadow-sm';
                btn.innerHTML = '<span id="auto-btn-text">توقف خودکار</span>';
            }
        } else {
            if (badge) badge.className = 'w-2.5 h-2.5 rounded-full bg-slate-500';
            if (btn) {
                btn.className = 'px-3 py-1.5 rounded-lg font-bold text-xs bg-blue-600 hover:bg-blue-500 text-white transition shadow-sm';
                btn.innerHTML = '<span id="auto-btn-text">فعال‌سازی</span>';
            }
        }
    } catch (e) {}
}

function setStrategyMode(isScalp) {
    isScalpMode = isScalp;
    const modeNormal = document.getElementById('mode-normal-btn');
    const modeScalp = document.getElementById('mode-scalp-btn');
    const subtitle = document.getElementById('auto-mode-subtitle');
    const durElem = document.getElementById('scalp-max-duration');

    if (isScalp) {
        if (modeScalp) modeScalp.className = 'px-2.5 py-1 rounded bg-amber-500 text-slate-950 font-bold transition flex items-center gap-1';
        if (modeNormal) modeNormal.className = 'px-2.5 py-1 rounded text-slate-400 hover:text-white transition';
        if (subtitle) subtitle.innerText = 'معامله خودکار اسکالپینگ (M1)';
        if (durElem) durElem.value = "10";
        showToast('حالت سیگنال روی اسکالپینگ M1 تنظیم شد.', 'info');
    } else {
        if (modeNormal) modeNormal.className = 'px-2.5 py-1 rounded bg-blue-600 text-white transition';
        if (modeScalp) modeScalp.className = 'px-2.5 py-1 rounded text-slate-400 hover:text-amber-300 transition flex items-center gap-1';
        if (subtitle) subtitle.innerText = 'معامله خودکار استاندارد (M15)';
        if (durElem) durElem.value = "0";
    }
    fetchAIAnalysis();
}
// Toggle Scalper Engine
async function toggleScalperEngine() {
    const textElem = document.getElementById('scalper-mode-text');
    const badgeElem = document.getElementById('scalper-status-badge');
    const isRunning = textElem && textElem.innerText.includes('فعال');

    try {
        if (!isRunning) {
            const res = await fetch('/api/scalp/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbols: [currentSymbol], timeframe: 'M1', interval_seconds: 15, max_spread: 1.8 })
            });
            const data = await res.json();
            if (data.success) {
                if (textElem) textElem.innerText = 'اسکالپینگ: فعال ⚡';
                if (badgeElem) {
                    badgeElem.innerText = 'روشن';
                    badgeElem.className = 'text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40';
                }
                showToast('موتور اسکالپینگ با فرکانس بالا روشن شد.', 'success');
            }
        } else {
            const res = await fetch('/api/scalp/stop', { method: 'POST' });
            if (textElem) textElem.innerText = 'اسکالپینگ: خاموش';
            if (badgeElem) {
                badgeElem.innerText = 'خاموش';
                badgeElem.className = 'text-[10px] px-2 py-0.5 rounded-full bg-[#0b101c] text-slate-400 border border-slate-800';
            }
            showToast('موتور اسکالپینگ متوقف گردید.', 'info');
        }
    } catch (e) {
        showToast(`خطای اسکالپر: ${e.message}`, 'error');
    }
}

// Decisions History
async function fetchDecisionsHistory() {
    const container = document.getElementById('decisions-timeline-container');
    if (!container) return;

    try {
        const res = await fetch('/api/history/decisions?limit=20');
        const data = await res.json();
        const decisions = data.decisions || [];

        if (decisions.length === 0) {
            container.innerHTML = '<div class="text-xs text-slate-500 text-center py-8">هنوز تصمیمی در دیتابیس ثبت نشده است.</div>';
            return;
        }

        container.innerHTML = decisions.map(d => `
            <div class="bg-[#0b101c] p-4 rounded-xl border border-slate-800 space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2 space-x-reverse">
                        <span class="w-6 h-6 rounded bg-blue-500/10 text-blue-400 font-bold flex items-center justify-center text-[10px] font-mono">#${d.id}</span>
                        <span class="font-bold text-xs text-white">${d.symbol} (${d.timeframe})</span>
                        <span class="text-[10px] text-slate-500 font-mono">[${d.timestamp}]</span>
                    </div>
                    <span class="px-2.5 py-0.5 rounded text-[11px] font-black ${
                        d.action === 'BUY' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                        d.action === 'SELL' ? 'bg-rose-950 text-rose-400 border border-rose-800' : 'bg-slate-800 text-slate-300'
                    }">سیگنال: ${d.action} (${d.confidence}%)</span>
                </div>
                <div class="bg-[#151c2e] p-3 rounded-lg border border-slate-800 text-[11px] text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">${d.thinking_process}</div>
            </div>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (e) {}
}

// Trades History (Bottom & View)
async function fetchBottomHistory() {
    const tbody = document.getElementById('history-bottom-body');
    if (!tbody) return;

    try {
        const res = await fetch('/api/history/trades?limit=30');
        const data = await res.json();
        const trades = data.trades || [];

        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="py-6 text-center text-slate-500 font-sans">هیچ معامله‌ای در دیتابیس ثبت نشده است.</td></tr>';
            return;
        }

        tbody.innerHTML = trades.map(t => `
            <tr class="hover:bg-slate-800/30 transition">
                <td class="py-2.5 pr-2 text-slate-400">#${t.ticket}</td>
                <td class="py-2.5 font-bold text-white">${t.symbol}</td>
                <td class="py-2.5 font-bold ${t.type === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}">${t.type}</td>
                <td class="py-2.5 font-mono">${t.volume}</td>
                <td class="py-2.5 font-mono">${t.open_price}</td>
                <td class="py-2.5 font-mono">${t.close_price || '-'}</td>
                <td class="py-2.5"><span class="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">${t.strategy}</span></td>
                <td class="py-2.5 font-bold font-mono ${t.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${t.profit >= 0 ? '+' : ''}$${t.profit.toFixed(2)}</td>
                <td class="py-2.5 text-slate-400 text-[10px] font-mono">${t.close_time || t.open_time}</td>
            </tr>
        `).join('');
    } catch (e) {}
}

async function fetchTradesHistory() {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    try {
        const res = await fetch('/api/history/trades?limit=50');
        const data = await res.json();
        const trades = data.trades || [];

        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="py-6 text-center text-slate-500 font-sans">هیچ معامله‌ای در دیتابیس ثبت نشده است.</td></tr>';
            return;
        }

        tbody.innerHTML = trades.map(t => `
            <tr class="hover:bg-slate-800/30 transition">
                <td class="py-2.5 pr-2 text-slate-400">#${t.ticket}</td>
                <td class="py-2.5 font-bold text-white">${t.symbol}</td>
                <td class="py-2.5 font-bold ${t.type === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}">${t.type}</td>
                <td class="py-2.5 font-mono">${t.volume}</td>
                <td class="py-2.5 font-mono">${t.open_price}</td>
                <td class="py-2.5 font-mono">${t.close_price || '-'}</td>
                <td class="py-2.5"><span class="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">${t.strategy}</span></td>
                <td class="py-2.5 font-bold font-mono ${t.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${t.profit >= 0 ? '+' : ''}$${t.profit.toFixed(2)}</td>
                <td class="py-2.5 text-slate-400 text-[10px] font-mono">${t.close_time || t.open_time}</td>
            </tr>
        `).join('');
    } catch (e) {}
}

async function fetchPerformanceSummary() {
    try {
        const res = await fetch('/api/history/performance');
        const data = await res.json();

        const wrElem = document.getElementById('perf-winrate');
        const wlElem = document.getElementById('perf-win-loss-count');
        const npElem = document.getElementById('perf-net-profit');
        const pfElem = document.getElementById('perf-profit-factor');
        const ttElem = document.getElementById('perf-total-trades');

        if (wrElem) wrElem.innerText = `${data.win_rate || 0.0}%`;
        if (wlElem) wlElem.innerText = `${data.winning_trades || 0} برد / ${data.losing_trades || 0} باخت`;
        if (npElem) {
            npElem.innerText = `${data.net_pnl >= 0 ? '+' : ''}$${(data.net_pnl || 0.0).toFixed(2)}`;
            npElem.className = `text-xl font-bold font-mono mt-0.5 ${data.net_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
        }
        if (pfElem) pfElem.innerText = data.profit_factor || '1.00';
        if (ttElem) ttElem.innerText = data.total_trades || 0;
    } catch (e) {}
}

// Bottom Logs
async function fetchBottomLogs() {
    const container = document.getElementById('logs-bottom-container');
    if (!container) return;

    try {
        const res = await fetch('/api/autotrade/logs?limit=30');
        const logs = await res.json();
        if (!logs || logs.length === 0) {
            container.innerHTML = '<div class="text-slate-500 font-sans">هیچ لاگی ثبت نشده است.</div>';
            return;
        }

        container.innerHTML = logs.map(l => `
            <div class="flex items-start space-x-2 space-x-reverse ${l.level.includes('ERROR') ? 'text-rose-400' : l.level.includes('SUCCESS') ? 'text-emerald-400' : l.level.includes('WARN') ? 'text-amber-400' : 'text-slate-300'}">
                <span class="text-slate-500 shrink-0">[${l.timestamp}]</span>
                <span class="font-bold shrink-0">[${l.level}]</span>
                <span>${l.message}</span>
            </div>
        `).join('');
    } catch (e) {}
}

// Fleet & Signals
async function fetchFleetAgents() {
    const container = document.getElementById('fleet-agents-container');
    if (!container) return;

    try {
        const res = await fetch('/api/agents/fleet');
        const data = await res.json();
        const agents = data.agents || [];

        container.innerHTML = agents.map(a => `
            <div class="bg-[#0b101c] p-3.5 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div class="flex items-center space-x-2.5 space-x-reverse">
                    <div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center">
                        <i data-lucide="${a.avatar || 'bot'}" class="w-4 h-4"></i>
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <h4 class="font-bold text-xs text-white">${a.name}</h4>
                            <span class="text-[9px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 font-mono">وین‌ریت: ${a.win_rate}%</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">${a.description}</p>
                    </div>
                </div>
                <button onclick="followAgent(${a.id})" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition">
                    کپی ترید
                </button>
            </div>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (e) {}
}

async function followAgent(agentId) {
    try {
        const res = await fetch('/api/signals/follow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ leader_id: agentId, auto_copy: true, copy_ratio: 1.0 })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            fetchFleetAgents();
        }
    } catch (e) {}
}

async function fetchSignalsFeed() {
    const container = document.getElementById('signals-feed-container');
    if (!container) return;

    try {
        const res = await fetch('/api/signals/feed');
        const data = await res.json();
        const signals = data.signals || [];

        if (signals.length === 0) {
            container.innerHTML = '<div class="text-xs text-slate-500 text-center py-6">سیگنالی ثبت نشده است.</div>';
            return;
        }

        container.innerHTML = signals.map(s => `
            <div class="bg-[#0b101c] p-3 rounded-xl border border-slate-800 space-y-1.5 text-xs">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-white">${s.agent_name}</span>
                    <span class="px-2 py-0.5 rounded font-bold ${s.type === 'BUY' ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'}">${s.type} ${s.symbol}</span>
                </div>
                <p class="text-slate-300 text-[11px]">${s.content}</p>
            </div>
        `).join('');
    } catch (e) {}
}

// Economic Calendar & Market Intel
async function fetchEconomicCalendar() {
    const container = document.getElementById('calendar-events-container');
    if (!container) return;

    try {
        const res = await fetch('/api/market-intel/calendar');
        const data = await res.json();
        const events = data.events || [];

        container.innerHTML = events.map(ev => `
            <div class="bg-[#0b101c] p-3 rounded-xl border border-slate-800 space-y-1.5">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-200 text-xs">${ev.title_fa}</span>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 font-mono">⏳ ${ev.countdown_formatted}</span>
                </div>
                <p class="text-[11px] text-slate-400 leading-relaxed">${ev.description_fa}</p>
            </div>
        `).join('');
    } catch (e) {}
}
async function fetchMarketIntel() {
    try {
        const [macroRes, newsRes, etfRes, termRes, accRes] = await Promise.all([
            fetch('/api/market-intel/macro-signals'),
            fetch('/api/market-intel/news?limit=10'),
            fetch('/api/market-intel/etf-flows'),
            fetch('/api/terminal/status'),
            fetch('/api/account')
        ]);

        const macroData = await macroRes.json();
        const newsData = await newsRes.json();
        const etfData = await etfRes.json();
        const termData = await termRes.json();
        const accData = await accRes.json();

        // Populate Technical Specs
        if (termData) {
            const specName = document.getElementById('spec-term-name');
            const specPath = document.getElementById('spec-path');
            const specAlgo = document.getElementById('spec-algo');
            const specStatus = document.getElementById('intel-term-status');

            if (specName) specName.innerText = `${termData.name || 'MetaTrader 5'} (Build ${termData.build || 6198})`;
            if (specPath) specPath.innerText = termData.path || 'C:\\Program Files\\MetaTrader 5';
            if (specAlgo) specAlgo.innerText = termData.trade_allowed ? 'فعال و مجاز' : 'غیرفعال در تنظیمات ترمینال';
            if (specStatus) {
                specStatus.innerText = termData.connected ? 'آنلاین' : 'قطع ارتباط';
                specStatus.className = `text-[10px] px-2 py-0.5 rounded font-bold border ${termData.connected ? 'bg-emerald-950 text-emerald-400 border-emerald-800' : 'bg-rose-950 text-rose-400 border-rose-800'}`;
            }
        }

        if (accData) {
            const specBroker = document.getElementById('spec-broker');
            const specAccount = document.getElementById('spec-account');
            const specLev = document.getElementById('spec-leverage');

            if (specBroker) specBroker.innerText = `${accData.server || 'MetaQuotes-Demo'} (${accData.company || 'MetaQuotes Ltd.'})`;
            if (specAccount) specAccount.innerText = `#${accData.login || '---'} (${accData.trade_mode || 'Demo'})`;
            if (specLev) specLev.innerText = `${accData.currency || 'USD'} / 1:${accData.leverage || 100}`;
        }

        // Render Macro Signals
        const macroContainer = document.getElementById('macro-signals-container');
        if (macroContainer && macroData.signals) {
            macroContainer.innerHTML = macroData.signals.map(m => `
                <div class="bg-[#0b101c] p-2.5 rounded-lg border border-slate-800/80 flex items-center justify-between text-xs">
                    <span class="font-bold text-slate-200">${m.indicator}</span>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${m.signal.includes('Bullish') ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'}">${m.signal}</span>
                </div>
            `).join('');
        }

        // Render ETF Flows
        const etfContainer = document.getElementById('etf-flows-container');
        const etfSummary = document.getElementById('intel-etf-summary');
        if (etfSummary && etfData.summary) etfSummary.innerText = etfData.summary;
        if (etfContainer && etfData.etfs) {
            etfContainer.innerHTML = etfData.etfs.map(e => `
                <div class="bg-[#0b101c] p-2 rounded-lg border border-slate-800/80 flex items-center justify-between font-mono text-[11px]">
                    <span class="text-slate-300 font-sans text-xs">${e.name}</span>
                    <span class="font-bold text-emerald-400">${e.flow}</span>
                </div>
            `).join('');
        }

        // Render News
        const newsContainer = document.getElementById('market-news-container');
        if (newsContainer && newsData.news) {
            newsContainer.innerHTML = newsData.news.map(n => `
                <div class="bg-[#0b101c] p-2.5 rounded-lg border border-slate-800 space-y-1 text-xs">
                    <div class="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                        <span>${n.source}</span>
                        <span>${n.time}</span>
                    </div>
                    <h4 class="font-bold text-slate-200 text-[11px] leading-relaxed">${n.title}</h4>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Error fetching market intel:', e);
    }
}

async function createNewChatSessionPrompt() {
    const title = await showCustomPrompt('گفتگوی جدید با هوش مصنوعی', 'عنوان گفتگوی جدید را وارد کنید:', 'استراتژی و تحلیل جدید');
    if (!title) return;
    try {
        const res = await fetch('/api/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title || 'گفتگوی جدید' })
        });
        const data = await res.json();
        if (data.session) {
            currentChatSessionId = data.session.id;
            await fetchChatSessions();
            loadChatSessionMessages(currentChatSessionId);
            showToast('گفتگوی جدید ایجاد شد.', 'success');
        }
    } catch (e) {
        showToast('خطا در ساخت گفتگوی جدید', 'error');
    }
}

async function deleteCurrentChatSession() {
    const confirmed = await showCustomConfirm('حذف گفتگو', 'آیا از حذف یا پاک‌سازی این گفتگو اطمینان دارید؟', true);
    if (!confirmed) return;
    try {
        await fetch(`/api/chat/sessions/${currentChatSessionId}`, { method: 'DELETE' });
        showToast('گفتگو پاک‌سازی / حذف شد.', 'info');
        currentChatSessionId = 'default';
        await fetchChatSessions();
        loadChatSessionMessages('default');
    } catch (e) {}
}

function onChatSessionSelectChange(sessionId) {
    currentChatSessionId = sessionId;
    loadChatSessionMessages(sessionId);
}

async function loadChatSessionMessages(sessionId) {
    const container = document.getElementById('drawerChatMessages');
    if (!container) return;

    container.innerHTML = '<div class="text-slate-500 text-center py-4 text-xs">در حال بارگذاری گفتگو...</div>';

    try {
        const res = await fetch(`/api/chat/sessions/${sessionId}/messages`);
        const data = await res.json();
        const messages = data.messages || [];

        if (messages.length === 0) {
            container.innerHTML = `
                <div class="bg-[#151c2e] p-3 rounded-xl border border-slate-800 text-slate-200 leading-relaxed text-xs">
                    سلام! من دستیار هوشمند معاملاتی شما در متاتریدر هستم. این یک گفتگوی جدید و با کانتکست مستقل است. هر سوال یا تحلیلی دارید بفرمایید.
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        messages.forEach(m => renderChatMessageBubble(m.role, m.content, false));
        container.scrollTop = container.scrollHeight;
    } catch (e) {
        container.innerHTML = '<div class="text-rose-400 text-center py-4 text-xs">خطا در دریافت پیام‌ها</div>';
    }
}

function copyMessageText(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        showToast('متن پیام با موفقیت کپی شد! 📋', 'success');
    }).catch(() => {
        showToast('عدم دسترسی به کلیپ‌بورد', 'error');
    });
}

function resendMessage(text) {
    const input = document.getElementById('drawerChatInput');
    if (input) {
        input.value = text;
        sendDrawerChatMessage();
    }
}

function renderChatMessageBubble(role, content, shouldScroll = true) {
    const container = document.getElementById('drawerChatMessages');
    if (!container) return;

    const wrapper = document.createElement('div');
    wrapper.className = `flex flex-col group ${role === 'user' ? 'items-start' : 'items-end'} space-y-1`;

    const bubble = document.createElement('div');
    bubble.className = role === 'user' 
        ? 'bg-blue-600 text-white p-3 rounded-xl text-xs leading-relaxed max-w-[88%] break-words whitespace-pre-wrap shadow-sm'
        : 'bg-[#151c2e] text-slate-200 p-3 rounded-xl border border-slate-800 text-xs leading-relaxed max-w-[88%] break-words whitespace-pre-wrap';
    bubble.innerText = content;

    const actionToolbar = document.createElement('div');
    actionToolbar.className = 'flex items-center gap-2 text-[10px] text-slate-500 opacity-60 group-hover:opacity-100 transition px-1';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'hover:text-blue-400 flex items-center gap-1 transition';
    copyBtn.innerHTML = '📋 کپی';
    copyBtn.onclick = () => copyMessageText(content);
    actionToolbar.appendChild(copyBtn);

    if (role === 'user') {
        const resendBtn = document.createElement('button');
        resendBtn.className = 'hover:text-cyan-400 flex items-center gap-1 transition';
        resendBtn.innerHTML = '🔄 ارسال مجدد';
        resendBtn.onclick = () => resendMessage(content);
        actionToolbar.appendChild(resendBtn);
    }

    wrapper.appendChild(bubble);
    wrapper.appendChild(actionToolbar);
    container.appendChild(wrapper);

    if (shouldScroll) {
        container.scrollTop = container.scrollHeight;
    }
}

async function sendDrawerChatMessage() {
    const input = document.getElementById('drawerChatInput');
    const text = input ? input.value.trim() : '';
    if (!text) return;

    input.value = '';
    renderChatMessageBubble('user', text);

    const container = document.getElementById('drawerChatMessages');
    const aiThinkingWrapper = document.createElement('div');
    aiThinkingWrapper.className = 'flex flex-col items-end space-y-1';
    
    const aiBubble = document.createElement('div');
    aiBubble.className = 'bg-[#151c2e] text-slate-300 p-3 rounded-xl border border-slate-800 text-xs leading-relaxed max-w-[88%] flex items-center gap-2';
    aiBubble.innerHTML = '<span class="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span><span>در حال پردازش و استدلال...</span>';
    
    aiThinkingWrapper.appendChild(aiBubble);
    container.appendChild(aiThinkingWrapper);
    container.scrollTop = container.scrollHeight;

    const sendBtn = document.getElementById('btn-drawer-send');
    if (sendBtn) sendBtn.disabled = true;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, session_id: currentChatSessionId })
        });
        const data = await res.json();
        aiThinkingWrapper.remove();
        
        if (res.ok) {
            renderChatMessageBubble('assistant', data.response);
            fetchChatSessions();
        } else {
            renderChatMessageBubble('assistant', `⚠️ ${data.detail || 'خطا در دریافت پاسخ'}`);
        }
    } catch (e) {
        aiThinkingWrapper.remove();
        renderChatMessageBubble('assistant', `⚠️ خطای ارتباط: ${e.message}`);
    } finally {
        if (sendBtn) sendBtn.disabled = false;
    }
}
// Settings Modal
function openSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.classList.remove('hidden');
    loadSettingsIntoModal();
}

function closeSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.classList.add('hidden');
}

async function loadSettingsIntoModal() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        if (data.custom_url) document.getElementById('cfg-ai-url').value = data.custom_url;
        if (data.api_key) document.getElementById('cfg-ai-key').value = data.api_key;
        if (data.custom_model) document.getElementById('cfg-ai-model').value = data.custom_model;
        if (data.account_login) document.getElementById('cfg-mt5-login').value = data.account_login;
        if (data.account_password) document.getElementById('cfg-mt5-pass').value = data.account_password;
        if (data.broker_server_name) document.getElementById('cfg-mt5-server').value = data.broker_server_name;
        if (data.max_open_positions) document.getElementById('cfg-max-positions').value = data.max_open_positions;
        if (data.ai_position_monitor_enabled !== undefined) {
            const chk = document.getElementById('cfg-ai-pos-enabled');
            if (chk) chk.checked = data.ai_position_monitor_enabled;
        }
        if (data.ai_position_monitor_interval) {
            const inp = document.getElementById('cfg-ai-pos-interval');
            if (inp) inp.value = data.ai_position_monitor_interval;
        }
    } catch (e) {}
}

function setScalpLot(vol) {
    const lotInput = document.getElementById('scalp-lot');
    if (lotInput) lotInput.value = vol;
}

async function executeInstantScalpAction(orderType) {
    const volInput = document.getElementById('scalp-lot');
    const tpInput = document.getElementById('scalp-tp-pips');
    const slInput = document.getElementById('scalp-sl-pips');
    const durInput = document.getElementById('scalp-max-duration');

    const vol = parseFloat(volInput ? volInput.value : 0.01) || 0.01;
    const tpPips = parseFloat(tpInput ? tpInput.value : 10) || 10.0;
    const slPips = parseFloat(slInput ? slInput.value : 7) || 7.0;
    const maxMinutes = parseInt(durInput ? durInput.value : 10) || 10;

    const payload = {
        symbol: currentSymbol,
        order_type: orderType,
        volume: vol,
        target_pips: tpPips,
        sl_pips: slPips,
        max_hold_minutes: maxMinutes
    };

    try {
        const res = await fetch('/api/scalp/trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('trade');
            showToast(`⚡ معامله اسکالپ ${orderType} باز شد (تیکت: #${data.order_ticket} | حداکثر زمان: ${maxMinutes} دقیقه)`, 'success');
            fetchPositions();
            fetchTerminalAndAccount();
            fetchActiveScalps();
        } else {
            showToast(`خطا در ثبت اسکالپ: ${data.error || 'نامشخص'}`, 'error');
        }
    } catch (e) {
        showToast(`خطای ارتباط: ${e.message}`, 'error');
    }
}

async function fetchActiveScalps() {
    const container = document.getElementById('active-scalps-list');
    const countElem = document.getElementById('active-scalps-count');
    if (!container) return;

    try {
        const res = await fetch('/api/scalp/active');
        const data = await res.json();
        const scalps = data.active_scalps || [];

        if (countElem) countElem.innerText = scalps.length;

        if (scalps.length === 0) {
            container.innerHTML = '<div class="text-[11px] text-slate-500 text-center py-2 font-sans">هیچ معامله اسکالپی در جریان نیست.</div>';
            return;
        }

        container.innerHTML = scalps.map(s => `
            <div class="bg-[#0b101c] p-2.5 rounded-lg border border-amber-500/30 flex items-center justify-between font-mono text-[11px]">
                <div class="flex items-center gap-1.5 font-sans">
                    <span class="font-bold ${s.order_type === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}">${s.order_type} ${s.symbol}</span>
                    <span class="text-slate-500">#${s.ticket}</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-slate-400">TP: +${s.tp}</span>
                    <span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-bold border border-amber-500/30">⏳ ${s.remaining_formatted}</span>
                </div>
            </div>
        `).join('');
    } catch (e) {}
}

async function testAiSettings() {
    const box = document.getElementById('cfg-ai-test-feedback');
    box.className = 'text-[11px] p-2 rounded-lg block text-right rtl-text bg-slate-800 text-slate-300';
    box.innerText = '⏳ در حال تست اتصال هوش مصنوعی...';

    const payload = {
        provider: 'OpenAI',
        custom_url: document.getElementById('cfg-ai-url').value,
        api_key: document.getElementById('cfg-ai-key').value,
        custom_model: document.getElementById('cfg-ai-model').value,
    };

    try {
        const res = await fetch('/api/test-ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        box.className = `text-[11px] p-2 rounded-lg block text-right rtl-text ${data.ok ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'}`;
        box.innerText = (data.ok ? '✅ ' : '❌ ') + data.message;
    } catch (e) {
        box.className = 'text-[11px] p-2 rounded-lg block text-right rtl-text bg-rose-950 text-rose-300 border border-rose-800';
        box.innerText = '❌ خطای شبکه: ' + e.message;
    }
}

async function testMt5Settings() {
    const box = document.getElementById('cfg-mt5-test-feedback');
    box.className = 'text-[11px] p-2 rounded-lg block text-right rtl-text bg-slate-800 text-slate-300';
    box.innerText = '⏳ در حال بررسی لاگین متاتریدر ۵...';

    const payload = {
        account_login: parseInt(document.getElementById('cfg-mt5-login').value) || 0,
        account_password: document.getElementById('cfg-mt5-pass').value,
        broker_server_name: document.getElementById('cfg-mt5-server').value,
    };

    try {
        const res = await fetch('/api/test-mt5', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        box.className = `text-[11px] p-2 rounded-lg block text-right rtl-text ${data.ok ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'}`;
        box.innerText = (data.ok ? '✅ ' : '❌ ') + data.message;
    } catch (e) {
        box.className = 'text-[11px] p-2 rounded-lg block text-right rtl-text bg-rose-950 text-rose-300 border border-rose-800';
        box.innerText = '❌ خطای شبکه: ' + e.message;
    }
}

async function saveAllSettingsModal() {
    const payload = {
        provider: 'OpenAI',
        custom_url: document.getElementById('cfg-ai-url').value,
        api_key: document.getElementById('cfg-ai-key').value,
        custom_model: document.getElementById('cfg-ai-model').value,
        account_login: parseInt(document.getElementById('cfg-mt5-login').value) || 0,
        account_password: document.getElementById('cfg-mt5-pass').value,
        broker_server_name: document.getElementById('cfg-mt5-server').value,
        max_open_positions: parseInt(document.getElementById('cfg-max-positions')?.value) || 10,
        ai_position_monitor_enabled: document.getElementById('cfg-ai-pos-enabled') ? document.getElementById('cfg-ai-pos-enabled').checked : true,
        ai_position_monitor_interval: parseInt(document.getElementById('cfg-ai-pos-interval')?.value) || 20,
    };
    try {
        const res = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        showToast('تنظیمات با موفقیت ذخیره و اعمال شد.', 'success');
        closeSettingsModal();
        fetchTerminalAndAccount();
        fetchAIAnalysis();
        fetchConfluence();
    } catch (e) {
        showToast(`خطا در ذخیره تنظیمات: ${e.message}`, 'error');
    }
}

// --- Quantitative Attribution & Prediction Matrix Logic ---

async function fetchMatrixAnalytics() {
    try {
        const [symbolsRes, matrixRes] = await Promise.all([
            fetch('/api/analytics/symbols'),
            fetch('/api/analytics/strategies')
        ]);

        const symbolsData = await symbolsRes.json();
        const matrixData = await matrixRes.json();

        // Render Pair Recommendations Cards
        const recContainer = document.getElementById('pair-recommendations-container');
        if (recContainer && symbolsData.symbols) {
            if (symbolsData.symbols.length === 0) {
                recContainer.innerHTML = '<div class="col-span-3 text-slate-500 text-center py-4 text-xs font-sans">معامله بسته‌شده‌ای جهت تحلیل هوشمند استراتژی‌ها یافت نشد.</div>';
            } else {
                recContainer.innerHTML = symbolsData.symbols.map(s => `
                    <div class="bg-[#0b101c] p-3.5 rounded-xl border border-slate-800 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-sm text-white font-mono">${s.symbol}</span>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold font-mono ${s.win_rate >= 70 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'}">وین‌ریت: ${s.win_rate}%</span>
                        </div>
                        <p class="text-[11px] text-slate-300 leading-relaxed font-sans">${s.recommendation_fa}</p>
                        <div class="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/60 font-mono">
                            <span>تعداد کل: <b>${s.total_trades}</b></span>
                            <span>سود کل: <b class="${s.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}">+$${s.total_pnl}</b></span>
                            <span>میانگین اطمینان: <b>${s.avg_confidence}%</b></span>
                        </div>
                    </div>
                `).join('');
            }
        }

        // Render Strategy Matrix Table
        const matrixBody = document.getElementById('matrix-table-body');
        if (matrixBody && matrixData.matrix) {
            if (matrixData.matrix.length === 0) {
                matrixBody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-500 font-sans">هیچ داده‌ای در ماتریس ثبت نشده است.</td></tr>';
            } else {
                matrixBody.innerHTML = matrixData.matrix.map(m => `
                    <tr class="hover:bg-slate-800/30 transition font-mono">
                        <td class="py-2.5 pr-2 font-bold text-white">${m.symbol}</td>
                        <td class="py-2.5 font-sans font-medium text-slate-200">${m.strategy_tag}</td>
                        <td class="py-2.5">${m.total_trades} (${m.win_count}W / ${m.loss_count}L)</td>
                        <td class="py-2.5">${m.avg_confidence}%</td>
                        <td class="py-2.5 font-bold ${m.win_rate >= 70 ? 'text-emerald-400' : m.win_rate >= 50 ? 'text-cyan-400' : 'text-rose-400'}">${m.win_rate}%</td>
                        <td class="py-2.5 font-bold ${m.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${m.total_pnl >= 0 ? '+' : ''}$${m.total_pnl}</td>
                        <td class="py-2.5 font-sans"><span class="px-2 py-0.5 rounded text-[10px] ${m.win_rate >= 70 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-slate-800 text-slate-400'}">${m.effectiveness}</span></td>
                    </tr>
                `).join('');
            }
        }

        // Also fetch full prediction audit log
        fetchPredictionsAudit('');
    } catch (e) {
        console.error('Error fetching matrix analytics:', e);
    }
}

async function fetchPredictionsAudit(symbolFilter = '') {
    const tbody = document.getElementById('predictions-audit-body');
    if (!tbody) return;

    try {
        const url = symbolFilter ? `/api/analytics/predictions?symbol=${symbolFilter}` : '/api/analytics/predictions';
        const res = await fetch(url);
        const data = await res.json();
        const predictions = data.predictions || [];

        if (predictions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-500 font-sans">هیچ پیش‌بینی در تاریخچه یافت نشد.</td></tr>';
            return;
        }

        tbody.innerHTML = predictions.map(p => `
            <tr class="hover:bg-slate-800/30 transition text-xs">
                <td class="py-2.5 pr-2 text-slate-400 font-mono">#${p.ticket}</td>
                <td class="py-2.5 font-bold text-white font-mono">${p.symbol}</td>
                <td class="py-2.5 font-sans text-slate-300">${p.prediction_title || p.strategy}</td>
                <td class="py-2.5 font-mono text-cyan-400 font-bold">${p.confidence || 75}%</td>
                <td class="py-2.5 font-sans font-bold">
                    <span class="px-2 py-0.5 rounded text-[10px] ${
                        p.prediction_outcome === 'WIN' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                        p.prediction_outcome === 'LOSS' ? 'bg-rose-950 text-rose-400 border border-rose-800' :
                        'bg-amber-950 text-amber-400 border border-amber-800'
                    }">
                        ${p.prediction_outcome === 'WIN' ? '✅ درست (WIN)' : (p.prediction_outcome === 'LOSS' ? '❌ نادرست (LOSS)' : '⏳ در جریان')}
                    </span>
                </td>
                <td class="py-2.5 font-mono font-bold ${p.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
                    ${p.profit >= 0 ? '+' : ''}$${(p.profit || 0).toFixed(2)}
                </td>
                <td class="py-2.5 font-sans text-slate-300 text-[11px] leading-relaxed text-right">
                    ${p.prediction_reason || 'تحلیل بر مبنای آرایش EMAها و اندیکاتور RSI'}
                </td>
            </tr>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (e) {
        console.error('Error fetching prediction audit:', e);
    }
}

// --- Strategies Catalog & Management Logic ---

let cachedStrategiesList = [];
let activeStrategyCategory = 'all';

async function fetchStrategies() {
    const container = document.getElementById('strategies-grid-container');
    const badge = document.getElementById('active-strategies-count-badge');
    if (!container) return;

    try {
        const res = await fetch('/api/strategies');
        const data = await res.json();
        cachedStrategiesList = data.strategies || [];

        const activeCount = cachedStrategiesList.filter(s => s.is_active).length;
        if (badge) {
            badge.innerText = `${activeCount} / ${cachedStrategiesList.length} فعال`;
            badge.className = `px-3 py-1 rounded-xl text-xs font-bold font-mono ${
                activeCount > 0 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
            }`;
        }

        renderStrategiesList();
    } catch (e) {
        console.error('Error fetching strategies:', e);
    }
}

function filterStrategiesByCategory(cat) {
    activeStrategyCategory = cat;
    document.querySelectorAll('.strat-filter-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-blue-600', 'text-white');
        btn.classList.add('bg-[#0b101c]', 'text-slate-400');
        if (btn.innerText.includes(cat) || (cat === 'all' && btn.innerText.includes('همه'))) {
            btn.classList.add('active', 'bg-blue-600', 'text-white');
            btn.classList.remove('bg-[#0b101c]', 'text-slate-400');
        }
    });
    renderStrategiesList();
}

function renderStrategiesList() {
    const container = document.getElementById('strategies-grid-container');
    if (!container) return;

    let filtered = cachedStrategiesList;
    if (activeStrategyCategory !== 'all') {
        filtered = cachedStrategiesList.filter(s => s.category.includes(activeStrategyCategory));
    }

    if (filtered.length === 0) {
        container.innerHTML = '<div class="col-span-2 text-slate-500 text-center py-6 text-xs font-sans">هیچ استراتژی در این دسته‌بندی یافت نشد.</div>';
        return;
    }

    container.innerHTML = filtered.map(s => {
        const isActive = Boolean(s.is_active);
        return `
            <div class="p-4 rounded-2xl border transition ${
                isActive ? 'bg-[#0b101c] border-slate-700 hover:border-emerald-500/50 shadow-md shadow-emerald-500/5' : 'bg-[#090d16]/60 border-slate-800/60 opacity-60'
            } space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2.5 space-x-reverse">
                        <div class="w-8 h-8 rounded-xl ${isActive ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500'} flex items-center justify-center">
                            <i data-lucide="${s.icon || 'trending-up'}" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-xs text-white">${s.title_fa}</h3>
                            <span class="text-[10px] text-slate-400 font-mono">${s.name}</span>
                        </div>
                    </div>

                    <!-- iOS Style Toggle Switch -->
                    <button onclick="toggleStrategyAction('${s.id}', ${isActive})" class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        isActive ? 'bg-emerald-600' : 'bg-slate-700'
                    }">
                        <span class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                            isActive ? '-translate-x-5' : 'translate-x-0'
                        }"></span>
                    </button>
                </div>

                <!-- Description -->
                <p class="text-[11px] text-slate-300 leading-relaxed font-sans">${s.description_fa}</p>

                <!-- Metadata Badges & Weight Stepper -->
                <div class="flex flex-wrap items-center justify-between gap-2 text-[10px] pt-2 border-t border-slate-800/80 font-mono">
                    <div class="flex items-center gap-1.5">
                        <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-sans">${s.category}</span>
                        <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300">TF: ${s.timeframe_default}</span>
                        <span class="text-emerald-400 font-bold">وین‌ریت: ${s.win_rate}%</span>
                    </div>
                    <div class="flex items-center gap-2 font-sans">
                        <div class="flex items-center gap-1">
                            <span class="text-slate-400">ضریب:</span>
                            <select onchange="updateStrategyWeightAction('${s.id}', this.value)" class="bg-[#090d16] border border-slate-700 rounded px-1.5 py-0.5 text-[10px] text-cyan-400 font-mono font-bold focus:outline-none focus:border-blue-500">
                                <option value="0.5" ${s.weight == 0.5 ? 'selected' : ''}>0.5x</option>
                                <option value="1.0" ${s.weight == 1.0 ? 'selected' : ''}>1.0x (عادی)</option>
                                <option value="1.5" ${s.weight == 1.5 ? 'selected' : ''}>1.5x</option>
                                <option value="2.0" ${s.weight == 2.0 ? 'selected' : ''}>2.0x (بالا)</option>
                                <option value="3.0" ${s.weight == 3.0 ? 'selected' : ''}>3.0x</option>
                                <option value="5.0" ${s.weight == 5.0 ? 'selected' : ''}>5.0x (ویژه)</option>
                            </select>
                        </div>
                        <span class="${s.risk_level === 'کم' ? 'text-cyan-400' : s.risk_level === 'متوسط' ? 'text-amber-400' : 'text-rose-400'}">ریسک: ${s.risk_level}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

async function updateStrategyWeightAction(strategyId, weight) {
    try {
        const res = await fetch(`/api/strategies/${strategyId}/weight`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weight: parseFloat(weight) })
        });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('signal');
            showToast(data.message || 'ضریب اهمیت استراتژی با موفقیت تنظیم شد.', 'success');
            await fetchStrategies();
            fetchAIAnalysis(); // Recalculate weighted probability consensus
        }
    } catch (e) {
        showToast(`خطا در تغییر ضریب: ${e.message}`, 'error');
    }
}

async function toggleStrategyAction(strategyId, currentStatus) {
    const newStatus = !currentStatus;
    try {
        const res = await fetch(`/api/strategies/${strategyId}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('signal');
            showToast(data.message || 'وضعیت استراتژی با موفقیت تغییر کرد.', 'success');
            await fetchStrategies();
            fetchAIAnalysis(); // Refresh AI analysis to apply newly active strategies
        }
    } catch (e) {
        showToast(`خطا در تغییر استراتژی: ${e.message}`, 'error');
    }
}

// --- Multi-Pair Portfolio Hub & Master AI Supervisor Logic ---

let portfolioPairsData = [];
let isPortfolioAnalyzing = false;

async function fetchPortfolioPairsAnalysis(forceRefresh = false) {
    const tbody = document.getElementById('portfolio-table-body');
    if (!tbody) return;

    try {
        const res = await fetch(`/api/portfolio/pairs?force_refresh=${forceRefresh ? 'true' : 'false'}`);
        const data = await res.json();
        portfolioPairsData = data.pairs || [];

        // Update metric chips
        const mEnabled = document.getElementById('port-metric-enabled');
        const mApproved = document.getElementById('port-metric-approved');
        const mLots = document.getElementById('port-metric-lots');
        const mTime = document.getElementById('port-metric-time');
        const supDot = document.getElementById('portfolio-supervisor-dot');
        const supText = document.getElementById('portfolio-supervisor-text');

        if (mEnabled) mEnabled.innerText = `${data.enabled_pairs || 0} / ${data.total_pairs || 0}`;
        if (mApproved) mApproved.innerText = `${data.approved_count || 0} جفت‌ارز`;
        if (mLots) mLots.innerText = `${data.total_lot_size || 0} Lot`;
        if (mTime) mTime.innerText = data.updated_at || 'چند لحظه پیش';

        if (data.is_supervisor_active) {
            if (supDot) supDot.className = 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse';
            if (supText) supText.innerText = '🤖 ناظر خودکار سبدی: فعال';
        } else {
            if (supDot) supDot.className = 'w-2 h-2 rounded-full bg-slate-500';
            if (supText) supText.innerText = '🤖 ناظر خودکار سبدی: غیرفعال';
        }
        renderPortfolioPairsTable(portfolioPairsData);
        fetchPortfolioCorrelation();
        fetchPortfolioExposure();
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="8" class="py-6 text-center text-rose-400 font-sans">خطا در بارگذاری سبد پورتفوی: ${e.message}</td></tr>`;
    }
}

async function analyzeAllPortfolioPairsAction() {
    const btn = document.getElementById('btn-portfolio-analyze-all');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block"></span><span>در حال تحلیل همزمان پورتفوی با هوش مصنوعی...</span>';
    }
    showToast('در حال اجرای تحلیل همزمان و ارزیابی اجماع روی تمام جفت‌ارزها...', 'info');
    try {
        await fetchPortfolioPairsAnalysis(true);
        playSoundAlert('signal');
        showToast('تحلیل سبد پورتفوی با موفقیت به پایان رسید.', 'success');
    } catch (e) {
        showToast(`خطا در تحلیل سبد: ${e.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="sparkles" class="w-4 h-4"></i><span>🔍 تحلیل همزمان تمام جفت‌ارزها</span>';
            if (window.lucide) lucide.createIcons();
        }
    }
}

function renderPortfolioPairsTable(pairs) {
    const tbody = document.getElementById('portfolio-table-body');
    if (!tbody) return;

    if (!pairs || pairs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="py-8 text-center text-slate-500 font-sans">هیچ جفت‌ارزی در سبد تعریف نشده است.</td></tr>`;
        return;
    }

    tbody.innerHTML = pairs.map(p => {
        const isBuy = p.action === 'BUY';
        const isSell = p.action === 'SELL';
        const actionBadge = isBuy ? 'text-emerald-400 bg-emerald-950/80 border-emerald-800' :
                            (isSell ? 'text-rose-400 bg-rose-950/80 border-rose-800' : 'text-slate-400 bg-slate-900 border-slate-800');
        
        const wp = p.weighted_probabilities || {};
        const buyProb = wp.buy_probability || 50;
        const sellProb = wp.sell_probability || 50;

        const isApproved = p.is_approved;
        const isAlreadyOpen = p.is_already_open;

        let statusBadge = '';
        if (isAlreadyOpen) {
            statusBadge = `<span class="px-2 py-0.5 rounded bg-blue-950 text-cyan-300 border border-blue-800 text-[10px] font-bold">🔵 معامله باز (${p.open_trade_profit >= 0 ? '+' : ''}$${p.open_trade_profit.toFixed(2)})</span>`;
        } else if (isApproved) {
            statusBadge = `<span class="px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-bold animate-pulse">🟢 واجد شرایط ورود</span>`;
        } else {
            statusBadge = `<span class="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 text-[10px]">⚪ در انتظار تایید</span>`;
        }

        return `
            <tr class="hover:bg-slate-800/40 transition text-xs ${isApproved ? 'bg-emerald-950/10' : ''}">
                <!-- Checkbox (Enable in basket) -->
                <td class="p-2.5 text-center">
                    <input type="checkbox" ${p.is_enabled ? 'checked' : ''} onchange="togglePortfolioPairEnabled('${p.symbol}', this.checked)" class="w-4 h-4 rounded bg-slate-800 border-slate-700 text-amber-500 focus:ring-0 cursor-pointer">
                </td>

                <!-- Symbol & Live Prices -->
                <td class="p-2.5">
                    <div class="flex items-center space-x-2 space-x-reverse">
                        <div>
                            <div class="font-bold text-white text-sm">${p.symbol}</div>
                            <div class="text-[10px] text-slate-400 font-sans">${p.title_fa}</div>
                        </div>
                        <div class="text-[10px] font-mono text-slate-400 border-r border-slate-800 pr-2 mr-2">
                            <div>Bid: <span class="text-rose-300">${p.bid.toFixed(p.digits)}</span></div>
                            <div>Ask: <span class="text-emerald-300">${p.ask.toFixed(p.digits)}</span></div>
                            <div class="text-cyan-400">اسپرد: ${p.spread_pips.toFixed(1)}p</div>
                        </div>
                    </div>
                </td>

                <!-- Active Open Positions Count -->
                <td class="p-2.5 text-center font-mono">
                    ${p.open_positions_count > 0 ? `
                        <span class="px-2 py-0.5 rounded bg-blue-950/90 text-cyan-300 border border-blue-800 text-[10px] font-bold">
                            🔵 ${p.open_positions_count} معامله (${p.open_positions_profit >= 0 ? '+' : ''}$${p.open_positions_profit.toFixed(2)})
                        </span>
                    ` : `
                        <span class="text-slate-500 font-sans text-[10px]">بدون معامله</span>
                    `}
                </td>

                <!-- Historical Win Rate from Past Trades -->
                <td class="p-2.5 text-center font-mono">
                    <div class="space-y-0.5">
                        <span class="text-purple-300 font-bold text-xs">${p.historical_win_rate}%</span>
                        <div class="text-[9px] text-slate-400 font-sans">
                            ${p.historical_trades > 0 ? `${p.historical_trades} معامله (${p.historical_pnl >= 0 ? '+' : ''}$${p.historical_pnl})` : 'مبنای الگو'}
                        </div>
                    </div>
                </td>

                <!-- AI Signal & Confidence -->
                <td class="p-2.5">
                    <div class="flex items-center gap-1.5">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${actionBadge}">
                            ${p.action}
                        </span>
                        <span class="font-bold font-mono text-sm ${isBuy ? 'text-emerald-400' : (isSell ? 'text-rose-400' : 'text-slate-300')}">${p.confidence}%</span>
                    </div>
                </td>

                <!-- 52 Strategies Probabilities Bar -->
                <td class="p-2.5 min-w-[130px]">
                    <div class="space-y-1 font-mono text-[10px]">
                        <div class="flex justify-between">
                            <span class="text-emerald-400">خرید: ${buyProb}%</span>
                            <span class="text-rose-400">فروش: ${sellProb}%</span>
                        </div>
                        <div class="w-full bg-slate-900 rounded-full h-1.5 flex overflow-hidden">
                            <div class="bg-emerald-500 h-full" style="width: ${buyProb}%"></div>
                            <div class="bg-rose-500 h-full" style="width: ${sellProb}%"></div>
                        </div>
                    </div>
                </td>

                <!-- Min Confidence Threshold Slider / Input -->
                <td class="p-2.5 text-center">
                    <div class="inline-flex items-center gap-1 font-mono">
                        <input type="number" value="${p.min_confidence}" min="50" max="95" step="1" onchange="updatePortfolioPairMinConf('${p.symbol}', this.value)" class="w-14 bg-[#151c2e] border border-slate-700 text-center rounded px-1.5 py-1 text-xs text-amber-300 font-bold">
                        <span class="text-slate-500">%</span>
                    </div>
                </td>

                <!-- Lot Size Input -->
                <td class="p-2.5 text-center">
                    <input type="number" value="${p.lot_size}" min="0.01" max="10" step="0.01" onchange="updatePortfolioPairLot('${p.symbol}', this.value)" class="w-16 bg-[#151c2e] border border-slate-700 text-center rounded px-1.5 py-1 text-xs text-white font-mono">
                </td>

                <!-- Qualification Status Badge -->
                <td class="p-2.5 text-center">
                    ${statusBadge}
                </td>

                <!-- Single Pair Actions -->
                <td class="p-2.5 text-center">
                    <div class="flex items-center justify-center gap-1">
                        ${isApproved && !isAlreadyOpen ? `
                            <button onclick="executeSinglePairTrade('${p.symbol}', '${p.action}', ${p.lot_size}, ${p.suggested_sl || 0}, ${p.suggested_tp || 0}, ${p.confidence})" title="اجرای فوری معامله" class="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold transition">
                                ⚡ ورود
                            </button>
                        ` : ''}
                        <button onclick="reanalyzeSinglePortfolioPair('${p.symbol}')" title="تحلیل مجدد این جفت‌ارز" class="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition">
                            <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
                        </button>
                        <button onclick="removePortfolioPairAction('${p.symbol}')" title="حذف از سبد" class="p-1 rounded bg-rose-950/80 hover:bg-rose-900 text-rose-300 transition">
                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

async function togglePortfolioPairEnabled(symbol, isEnabled) {
    try {
        await fetch(`/api/portfolio/pairs/${symbol}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_enabled: isEnabled })
        });
        showToast(`جفت‌ارز ${symbol} ${isEnabled ? 'در سبد فعال شد' : 'از سبد غیرفعال شد'}.`, 'info');
        fetchPortfolioPairsAnalysis();
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    }
}

async function updatePortfolioPairMinConf(symbol, minConf) {
    try {
        await fetch(`/api/portfolio/pairs/${symbol}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ min_confidence: parseFloat(minConf) })
        });
        showToast(`حد نصاب اطمینان ${symbol} روی ${minConf}% تنظیم شد.`, 'success');
        fetchPortfolioPairsAnalysis();
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    }
}

async function updatePortfolioPairLot(symbol, lot) {
    try {
        await fetch(`/api/portfolio/pairs/${symbol}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lot_size: parseFloat(lot) })
        });
        showToast(`حجم معامله ${symbol} به ${lot} لات تغییر یافت.`, 'success');
        fetchPortfolioPairsAnalysis();
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    }
}

async function removePortfolioPairAction(symbol) {
    const confirmed = await showCustomConfirm('حذف جفت‌ارز از سبد', `آیا از حذف نماد ${symbol} از سبد پورتفوی اطمینان دارید؟`, true);
    if (!confirmed) return;
    try {
        const res = await fetch(`/api/portfolio/pairs/${symbol}`, { method: 'DELETE' });
        const data = await res.json();
        showToast(data.message || 'نماد حذف شد.', 'info');
        fetchPortfolioPairsAnalysis();
    } catch (e) {
        showToast(`خطا در حذف نماد: ${e.message}`, 'error');
    }
}

async function reanalyzeSinglePortfolioPair(symbol) {
    showToast(`در حال تحلیل هوشمند ${symbol}...`, 'info');
    try {
        await fetch(`/api/analyze/${symbol}?timeframe=M15&force_refresh=true`);
        fetchPortfolioPairsAnalysis();
        showToast(`تحلیل ${symbol} تکمیل شد.`, 'success');
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    }
}

async function executeSinglePairTrade(symbol, action, lot, sl, tp, conf) {
    const confirmed = await showCustomConfirm('اجرای معامله سبدی', `آیا از باز کردن معامله ${action} روی نماد ${symbol} به حجم ${lot} لات اطمینان دارید؟`);
    if (!confirmed) return;
    try {
        const res = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: symbol,
                order_type: action,
                volume: lot,
                sl: sl,
                tp: tp,
                comment: 'Portfolio Single Trade'
            })
        });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('trade');
            showToast(`معامله ${action} ${symbol} با موفقیت ثبت شد (تیکت: #${data.order_ticket}).`, 'success');
            fetchPositions();
            fetchPortfolioPairsAnalysis();
        } else {
            showToast(data.error || 'خطا در ثبت معامله', 'error');
        }
    } catch (e) {
        showToast(`خطا در ارسال دستور: ${e.message}`, 'error');
    }
}

async function executePortfolioBasketAction() {
    const btn = document.getElementById('btn-portfolio-exec-basket');
    const confirmed = await showCustomConfirm('اجرای سبد پورتفوی', 'آیا از باز کردن همزمان معاملات روی تمام جفت‌ارزهای واجد شرایط سبد پورتفوی اطمینان دارید؟');
    if (!confirmed) return;
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block"></span><span>در حال ثبت معاملات سبدی...</span>';
    }

    try {
        const res = await fetch('/api/portfolio/execute-basket', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('trade');
            showToast(data.message || `تعداد ${data.executed_count} معامله سبدی با موفقیت باز شد.`, 'success');
            fetchPositions();
            fetchPortfolioPairsAnalysis();
        } else {
            showToast(data.message || 'هیچ معامله‌ای ثبت نشد.', 'warning');
        }
    } catch (e) {
        showToast(`خطای ارتباط: ${e.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="zap" class="w-4 h-4"></i><span>⚡ اجرای سبدی معاملات تاییدشده</span>';
            if (window.lucide) lucide.createIcons();
        }
    }
}

async function togglePortfolioSupervisorAction() {
    const statusRes = await fetch('/api/portfolio/supervisor/status');
    const statusData = await statusRes.json();
    const isCurrentlyRunning = statusData.is_running;

    try {
        if (isCurrentlyRunning) {
            const res = await fetch('/api/portfolio/supervisor/stop', { method: 'POST' });
            const data = await res.json();
            showToast(data.message || 'ناظر خودکار سبدی متوقف شد.', 'info');
        } else {
            const res = await fetch('/api/portfolio/supervisor/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interval_seconds: 30 })
            });
            const data = await res.json();
            showToast(data.message || 'ناظر خودکار سبدی فعال شد.', 'success');
        }
        fetchPortfolioPairsAnalysis();
    } catch (e) {
        showToast(`خطا در تغییر وضعیت ناظر: ${e.message}`, 'error');
    }
}

function openAddPortfolioPairModal() {
    const modal = document.getElementById('add-portfolio-pair-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeAddPortfolioPairModal() {
    const modal = document.getElementById('add-portfolio-pair-modal');
    if (modal) modal.classList.add('hidden');
}

async function submitAddPortfolioPairAction() {
    const symInput = document.getElementById('add-port-symbol');
    const titleInput = document.getElementById('add-port-title');
    const minConfInput = document.getElementById('add-port-minconf');
    const lotInput = document.getElementById('add-port-lot');

    const sym = symInput ? symInput.value.trim().toUpperCase() : '';
    if (!sym) {
        showToast('لطفاً نماد معاملاتی را وارد کنید.', 'warning');
        return;
    }

    const payload = {
        symbol: sym,
        title_fa: titleInput ? titleInput.value.trim() : `جفت‌ارز ${sym}`,
        min_confidence: parseFloat(minConfInput ? minConfInput.value : 70) || 70.0,
        lot_size: parseFloat(lotInput ? lotInput.value : 0.01) || 0.01,
        timeframe: 'M15'
    };

    try {
        const res = await fetch('/api/portfolio/pairs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        showToast(data.message || 'جفت‌ارز به سبد افزوده شد.', 'success');
        closeAddPortfolioPairModal();
        if (symInput) symInput.value = '';
        if (titleInput) titleInput.value = '';
        fetchPortfolioPairsAnalysis();
    } catch (e) {
        showToast(`خطا در افزودن نماد: ${e.message}`, 'error');
    }
}

async function closeProfitablePositionsAction() {
    const confirmed = await showCustomConfirm('بستن معاملات سودده', 'آیا از بستن تمام معاملات دارای سود مثبت برای ذخیره و سیو سود اطمینان دارید؟');
    if (!confirmed) return;
    try {
        const res = await fetch('/api/positions/close-profitable', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('trade');
            showToast(data.message || `سود ${data.closed_count} معامله با موفقیت ذخیره شد.`, 'success');
            fetchPositions();
            fetchTerminalAndAccount();
            fetchPortfolioPairsAnalysis();
        } else {
            showToast(data.message || 'خطا در بستن معاملات سودده', 'warning');
        }
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    }
}

async function fetchPortfolioCorrelation() {
    const container = document.getElementById('correlation-matrix-container');
    if (!container) return;

    try {
        const res = await fetch('/api/portfolio/correlation?timeframe=H1');
        const data = await res.json();
        const symbols = data.symbols || [];
        const matrix = data.matrix || [];

        if (!symbols || symbols.length === 0) {
            container.innerHTML = `<div class="text-center py-6 text-slate-500 font-sans text-xs">داده‌های کافی برای محاسبه ماتریس همبستگی یافت نشد.</div>`;
            return;
        }

        container.innerHTML = `
            <table class="w-full text-center text-[10px] font-mono border-collapse">
                <thead>
                    <tr class="text-slate-400 border-b border-slate-800">
                        <th class="p-1.5 text-right font-sans">جفت‌ارز</th>
                        ${symbols.map(s => `<th class="p-1.5 font-bold">${s}</th>`).join('')}
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/40">
                    ${matrix.map(row => `
                        <tr>
                            <td class="p-1.5 font-bold text-white text-right">${row.symbol}</td>
                            ${row.correlations.map(c => {
                                const val = c.correlation;
                                const isSelf = row.symbol === c.target;
                                let colorClass = 'text-slate-400 bg-slate-900/40';
                                if (isSelf) {
                                    colorClass = 'text-slate-500 bg-slate-900 font-bold';
                                } else if (val >= 0.75) {
                                    colorClass = 'text-rose-300 bg-rose-950/60 font-bold border border-rose-900/50';
                                } else if (val <= -0.6) {
                                    colorClass = 'text-emerald-300 bg-emerald-950/60 font-bold border border-emerald-900/50';
                                } else if (Math.abs(val) < 0.3) {
                                    colorClass = 'text-cyan-300 bg-cyan-950/30';
                                }
                                return `<td class="p-1.5 rounded ${colorClass}" title="${row.symbol} با ${c.target}: همبستگی ${val} (${c.strength})">${isSelf ? '1.00' : (val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2))}</td>`;
                            }).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (e) {
        container.innerHTML = `<div class="text-center py-4 text-rose-400 text-xs">خطا در دریافت ماتریس: ${e.message}</div>`;
    }
}

async function fetchPortfolioExposure() {
    const summaryElem = document.getElementById('portfolio-exposure-summary-text');
    const barsContainer = document.getElementById('portfolio-exposure-bars-container');
    if (!barsContainer) return;

    try {
        const res = await fetch('/api/portfolio/exposure');
        const data = await res.json();

        if (summaryElem && data.risk_assessment_fa) {
            summaryElem.innerHTML = `
                <div class="flex items-center justify-between font-bold mb-1">
                    <span>مجموع حجم کل پورتفوی:</span>
                    <span class="font-mono text-cyan-300">${data.total_lots || 0} Lot</span>
                </div>
                <div>${data.risk_assessment_fa}</div>
            `;
        }

        const list = data.net_exposure || [];
        if (list.length === 0) {
            barsContainer.innerHTML = `<div class="text-center py-4 text-slate-500 font-sans text-xs">هیچ معامله بازی در حال حاضر وجود ندارد.</div>`;
            return;
        }

        const maxLot = Math.max(0.01, ...list.map(e => Math.abs(e.net_lots)));
        barsContainer.innerHTML = list.map(e => {
            const pct = Math.min(100, Math.round((Math.abs(e.net_lots) / maxLot) * 100));
            const isLong = e.net_lots > 0;
            return `
                <div class="bg-[#101726] p-2 rounded-lg border border-slate-800/80 text-xs font-mono space-y-1">
                    <div class="flex items-center justify-between text-[11px]">
                        <div class="flex items-center space-x-1.5 space-x-reverse">
                            <span class="font-bold text-white">${e.currency}</span>
                            <span class="text-[10px] text-slate-400 font-sans">(${e.direction})</span>
                        </div>
                        <span class="font-bold ${isLong ? 'text-emerald-400' : 'text-rose-400'}">${e.net_lots > 0 ? '+' : ''}${e.net_lots} Lot</span>
                    </div>
                    <div class="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                        <div class="${isLong ? 'bg-emerald-500' : 'bg-rose-500'} h-full rounded-full" style="width: ${pct}%"></div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        barsContainer.innerHTML = `<div class="text-center py-2 text-rose-400 text-xs">خطا: ${e.message}</div>`;
    }
}

async function autoOptimizeStrategyWeightsAction() {
    const confirmed = await showCustomConfirm(
        'بهینه‌سازی ضرایب با هوش مصنوعی',
        'آیا مایلید تمام ضرایب وزنی ۵۰ استراتژی بر اساس سوابق تاریخی وین‌ریت و یادگیری تقویتی بهینه‌سازی شوند؟'
    );
    if (!confirmed) return;

    const btn = document.getElementById('btn-auto-opt-strats');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block"></span><span>در حال بهینه‌سازی ضرایب...</span>';
    }

    try {
        const res = await fetch('/api/strategies/auto-optimize', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            playSoundAlert('signal');
            showToast(data.message || 'ضرایب استراتژی‌ها با موفقیت بهینه‌سازی شدند.', 'success');
            await fetchStrategies();
            fetchAIAnalysis(true);
        } else {
            showToast('خطا در بهینه‌سازی ضرایب استراتژی‌ها', 'error');
        }
    } catch (e) {
        showToast(`خطا: ${e.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="sparkles" class="w-4 h-4"></i><span>🤖 بهینه‌سازی خودکار ضرایب با AI</span>';
            if (window.lucide) lucide.createIcons();
        }
    }
}
