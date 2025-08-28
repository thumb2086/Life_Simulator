window.App = (function(){
  const qs = sel => document.querySelector(sel);
  const qsa = sel => Array.from(document.querySelectorAll(sel));

  async function fetchJSON(url, opts={}){
    const resp = await fetch(url, opts);
    if(!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  }

  // 儀表板自動刷新計時器
  let refreshTimer = null;

  function renderTable(tbody, rows, columns){
    tbody.innerHTML = '';
    rows.forEach((r, idx) => {
      const tr = document.createElement('tr');
      const rank = idx + 1;
      const cells = [rank, ...columns.map(c => r[c] ?? '')];
      cells.forEach(v => {
        const td = document.createElement('td');
        td.textContent = typeof v === 'number' ? formatNumber(v) : v;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  function formatNumber(n){
    try{
      return new Intl.NumberFormat('zh-Hant', {maximumFractionDigits: 2}).format(n);
    }catch(e){
      return n;
    }
  }

  async function loadLeaderboard(){
    const status = qs('#status');
    try{
      const asset = await fetchJSON('/leaderboard/top');
      const casino = await fetchJSON('/casino/top');
      renderTable(qs('#asset-table tbody'), asset.records || [], ['username','asset','days']);
      renderTable(qs('#casino-table tbody'), casino.records || [], ['username','casino_win']);
      const now = new Date();
      status.textContent = `更新於 ${now.toLocaleTimeString()}`;
    }catch(e){
      status.textContent = `讀取失敗: ${e.message}`;
    }
  }

  function initLeaderboard({refreshMs=10000}={}){
    loadLeaderboard();
    setInterval(loadLeaderboard, refreshMs);
    registerSW();
  }

  // --- Dashboard ---
  function saveToken(t){ try{ localStorage.setItem('sg_token', t); }catch(e){} }
  function getToken(){ try{ return localStorage.getItem('sg_token') || ''; }catch(e){ return ''; } }

  function show(el, on=true){ if(el) el.style.display = on ? '' : 'none'; }
  function setText(sel, txt){ const el = qs(sel); if(el) el.textContent = txt; }

  async function login(){
    const username = qs('#username').value.trim();
    const status = qs('#login-status');
    status.textContent = '登入中...';
    try{
      const data = await fetchJSON('/auth/login', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username })
      });
      saveToken(data.token);
      status.textContent = '登入成功';
      await loadState();
      show(qs('#login-section'), false);
      show(qs('#game-section'), true);
      // 登入後啟動自動刷新
      startAutoRefresh();
    }catch(e){
      status.textContent = `登入失敗: ${e.message}`;
    }
  }

  async function loadState(){
    const token = getToken();
    if(!token){ return; }
    const data = await fetchJSON(`/game/state?token=${encodeURIComponent(token)}`);
    setText('#u-name', data.username);
    setText('#u-cash', formatNumber(data.cash));
    setText('#u-days', data.days);
    if (typeof data.net_worth !== 'undefined') {
      setText('#u-net', formatNumber(data.net_worth));
    }
    // holdings
    const tbHold = qs('#tbl-holdings tbody');
    if(tbHold){
      tbHold.innerHTML = '';
      (data.holdings || []).forEach(h => {
        const tr = document.createElement('tr');
        [['symbol'], ['qty'], ['avg_cost']].forEach(col => {
          const td = document.createElement('td');
          const key = col[0];
          const val = h[key];
          td.textContent = typeof val === 'number' ? formatNumber(val) : val;
          tr.appendChild(td);
        });
        tbHold.appendChild(tr);
      });
    }
    // prices
    const tbPrice = qs('#tbl-prices tbody');
    if(tbPrice){
      tbPrice.innerHTML = '';
      const entries = Object.entries(data.prices || {});
      entries.sort((a,b) => a[0].localeCompare(b[0]));
      entries.forEach(([sym, p]) => {
        const tr = document.createElement('tr');
        const td1 = document.createElement('td'); td1.textContent = sym;
        const td2 = document.createElement('td'); td2.textContent = formatNumber(p);
        tr.appendChild(td1); tr.appendChild(td2);
        tbPrice.appendChild(tr);
      });
    }
  }

  async function buy(){
    const token = getToken();
    const symbol = (qs('#buy-symbol').value||'').trim();
    const qty = parseFloat(qs('#buy-qty').value||'0');
    const status = qs('#buy-status');
    status.textContent = '下單中...';
    try{
      await fetchJSON('/stocks/buy', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ token, symbol, qty }) });
      status.textContent = '買入成功';
      await loadState();
    }catch(e){ status.textContent = `買入失敗: ${e.message}`; }
  }

  async function sell(){
    const token = getToken();
    const symbol = (qs('#sell-symbol').value||'').trim();
    const qty = parseFloat(qs('#sell-qty').value||'0');
    const status = qs('#sell-status');
    status.textContent = '下單中...';
    try{
      await fetchJSON('/stocks/sell', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ token, symbol, qty }) });
      status.textContent = '賣出成功';
      await loadState();
    }catch(e){ status.textContent = `賣出失敗: ${e.message}`; }
  }

  async function advance(){
    const token = getToken();
    const status = qs('#advance-status');
    status.textContent = '推進中...';
    try{
      await fetchJSON('/tick/advance', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ token }) });
      status.textContent = '已推進一天';
      await loadState();
    }catch(e){ status.textContent = `失敗: ${e.message}`; }
  }

  async function submitLeaderboard(){
    const token = getToken();
    const status = qs('#submit-status');
    status.textContent = '提交中...';
    try{
      const res = await fetchJSON('/leaderboard/submit_web', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ token }) });
      status.textContent = `已提交，資產=${formatNumber(res.asset)}，天數=${res.days}`;
    }catch(e){
      status.textContent = `提交失敗: ${e.message}`;
    }
  }

  function wireDashboard(){
    const btnLogin = qs('#btn-login'); if(btnLogin) btnLogin.addEventListener('click', login);
    const btnBuy = qs('#btn-buy'); if(btnBuy) btnBuy.addEventListener('click', buy);
    const btnSell = qs('#btn-sell'); if(btnSell) btnSell.addEventListener('click', sell);
    const btnAdv = qs('#btn-advance'); if(btnAdv) btnAdv.addEventListener('click', advance);
    const btnSubmit = qs('#btn-submit-lb'); if(btnSubmit) btnSubmit.addEventListener('click', submitLeaderboard);
  }

  async function initDashboard(){
    wireDashboard();
    registerSW();
    const token = getToken();
    if(token){
      // auto show game section if token exists
      show(qs('#login-section'), false);
      show(qs('#game-section'), true);
      try{ await loadState(); }catch(e){ /* ignore */ }
      // 若已登入過，啟動自動刷新
      startAutoRefresh();
    }
  }

  function startAutoRefresh(refreshMs = 5000){
    try{ if (refreshTimer) clearInterval(refreshTimer); }catch(e){}
    refreshTimer = setInterval(() => {
      // 靜默刷新使用者狀態（持倉/價格）
      loadState().catch(() => {});
    }, refreshMs);
  }

  function stopAutoRefresh(){
    try{ if (refreshTimer) clearInterval(refreshTimer); }catch(e){}
    refreshTimer = null;
  }

  // 清理
  window.addEventListener('beforeunload', stopAutoRefresh);

  async function registerSW(){
    if ('serviceWorker' in navigator) {
      try{
        await navigator.serviceWorker.register('/static/sw.js');
      }catch(e){
        // ignore
      }
    }
  }

  return { initLeaderboard, initDashboard };
})();
