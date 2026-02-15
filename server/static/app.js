window.App = (function(){
  const qs = sel => document.querySelector(sel);
  const qsa = sel => Array.from(document.querySelectorAll(sel));

  async function fetchJSON(url, opts={}){
    const resp = await fetch(url, opts);
    if(!resp.ok) {
      const err = await resp.json().catch(()=>({detail: resp.statusText}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    return await resp.json();
  }

  let refreshTimer = null;

  function formatNumber(n){
    try{
      return new Intl.NumberFormat('zh-Hant', {maximumFractionDigits: 2}).format(n);
    }catch(e){ return n; }
  }

  function saveToken(t){ try{ localStorage.setItem('sg_token', t); }catch(e){} }
  function getToken(){ try{ return localStorage.getItem('sg_token') || ''; }catch(e){ return ''; } }

  function show(el, on=true){ if(el) el.style.display = on ? '' : 'none'; }
  function setText(sel, txt){ const el = qs(sel); if(el) el.textContent = txt; }

  // --- Tabs ---
  function openTab(tabName) {
    qsa('.tab-content').forEach(t => t.classList.remove('active'));
    qsa('.tab-btn').forEach(b => b.classList.remove('active'));
    qs(`#tab-${tabName}`).classList.add('active');
    qs(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');

    // Load specific tab data if needed
    if(tabName === 'market') loadMarketItems();
    if(tabName === 'inventory') loadInventory();
    if(tabName === 'company') loadBusinesses();
  }

  // --- Auth ---
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
      show(qs('#login-section'), false);
      show(qs('#game-section'), true);
      await loadState();
      startAutoRefresh();
    }catch(e){ status.textContent = `登入失敗: ${e.message}`; }
  }

  // --- Game State ---
  async function loadState(){
    const token = getToken();
    if(!token){ return; }
    const data = await fetchJSON(`/game/state?token=${encodeURIComponent(token)}`);
    setText('#u-name', data.username);
    setText('#u-days', data.days);
    setText('#u-cash', '$' + formatNumber(data.cash));
    setText('#u-bank', '$' + formatNumber(data.bank_balance));
    setText('#u-loan', '$' + formatNumber(data.loan));
    setText('#u-dist', formatNumber(data.travel_distance));
    setText('#u-net', '$' + formatNumber(data.net_worth));

    renderStockPrices(data.prices);
    renderHoldings(data.holdings, data.prices);
  }

  function renderStockPrices(prices){
    const tb = qs('#tbl-prices tbody');
    if(!tb) return;
    tb.innerHTML = '';
    Object.entries(prices).sort().forEach(([sym, p]) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${sym}</td>
        <td>$${formatNumber(p)}</td>
        <td><button onclick="App.tradeStock('${sym}', 'buy')">買入</button></td>
      `;
      tb.appendChild(tr);
    });
  }

  function renderHoldings(holdings, prices){
    const tb = qs('#tbl-holdings tbody');
    if(!tb) return;
    tb.innerHTML = '';
    holdings.forEach(h => {
      const curPrice = prices[h.symbol] || 0;
      const profit = (curPrice - h.avg_cost) * h.qty;
      const profitClass = profit >= 0 ? 'gain' : 'loss';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${h.symbol}</td>
        <td>${formatNumber(h.qty)}</td>
        <td>$${formatNumber(h.avg_cost)}</td>
        <td>$${formatNumber(curPrice)}</td>
        <td class="${profitClass}">$${formatNumber(profit)}</td>
        <td><button onclick="App.tradeStock('${h.symbol}', 'sell')">賣出</button></td>
      `;
      tb.appendChild(tr);
    });
  }

  // --- Bank ---
  async function bankAction(action){
    const token = getToken();
    const amount = parseFloat(qs('#bank-amount').value || 0);
    if(amount <= 0) return alert('請輸入大於 0 的金額');
    try {
      await fetchJSON(`/bank/${action}`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ token, amount })
      });
      await loadState();
      qs('#bank-amount').value = '';
    } catch(e) { alert(e.message); }
  }

  // --- Stocks ---
  async function tradeStock(symbol, action){
    const token = getToken();
    const qtyInput = prompt(`要${action === 'buy' ? '買入' : '賣出'}多少股 ${symbol}?`, "10");
    const qty = parseFloat(qtyInput);
    if(isNaN(qty) || qty <= 0) return;
    try {
      await fetchJSON(`/stocks/${action}`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ token, symbol, qty })
      });
      await loadState();
    } catch(e) { alert(e.message); }
  }

  // --- Market ---
  async function loadMarketItems(){
    try {
      const data = await fetchJSON('/market/items');
      const tb = qs('#tbl-market-items tbody');
      tb.innerHTML = '';
      data.items.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${item.name}</td>
          <td>${item.category}</td>
          <td>$${formatNumber(item.price)}</td>
          <td><button onclick="App.buyItem('${item.item_id}')">買入</button></td>
        `;
        tb.appendChild(tr);
      });
    } catch(e) { console.error(e); }
  }

  async function buyItem(item_id){
    const token = getToken();
    try {
      await fetchJSON('/market/buy', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ token, item_id, qty: 1 })
      });
      alert('購買成功');
      await loadState();
    } catch(e) { alert(e.message); }
  }

  // --- Inventory ---
  async function loadInventory(){
    try {
      const token = getToken();
      const data = await fetchJSON(`/inventory/list?token=${encodeURIComponent(token)}`);
      const tb = qs('#tbl-inventory tbody');
      tb.innerHTML = '';
      data.inventory.forEach(i => {
        const profit = (i.current_price - i.purchase_price) * i.qty;
        const profitClass = profit >= 0 ? 'gain' : 'loss';
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${i.name}</td>
          <td>${i.category}</td>
          <td>${i.qty}</td>
          <td>$${formatNumber(i.purchase_price)}</td>
          <td>$${formatNumber(i.current_price)}</td>
          <td class="${profitClass}">$${formatNumber(profit)}</td>
          <td><button onclick="App.sellItem('${i.item_id}')">賣出</button></td>
        `;
        tb.appendChild(tr);
      });
    } catch(e) { console.error(e); }
  }

  async function sellItem(item_id){
    const token = getToken();
    try {
      await fetchJSON('/market/sell', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ token, item_id, qty: 1 })
      });
      await loadInventory();
      await loadState();
    } catch(e) { alert(e.message); }
  }

  // --- Company ---
  async function loadBusinesses(){
    try {
      const token = getToken();
      const data = await fetchJSON(`/business/list?token=${encodeURIComponent(token)}`);
      const tb = qs('#tbl-businesses tbody');
      tb.innerHTML = '';
      data.businesses.forEach(b => {
        const net = b.revenue - b.cost;
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${b.name}</td>
          <td>Lv.${b.level}</td>
          <td>$${formatNumber(b.revenue)}</td>
          <td>$${formatNumber(b.cost)}</td>
          <td class="${net >= 0 ? 'gain' : 'loss'}">$${formatNumber(net)}</td>
          <td><button onclick="App.upgradeBusiness(${b.id})">升級</button></td>
        `;
        tb.appendChild(tr);
      });
    } catch(e) { console.error(e); }
  }

  async function startBusiness(){
    const token = getToken();
    const name = qs('#biz-name').value.trim();
    if(!name) return alert('請輸入事業名稱');
    try {
      await fetchJSON('/business/start', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ token, name })
      });
      qs('#biz-name').value = '';
      await loadBusinesses();
      await loadState();
    } catch(e) { alert(e.message); }
  }

  async function upgradeBusiness(business_id){
    const token = getToken();
    try {
      await fetchJSON(`/business/upgrade?token=${encodeURIComponent(token)}&business_id=${business_id}`, {
        method: 'POST'
      });
      await loadBusinesses();
      await loadState();
    } catch(e) { alert(e.message); }
  }

  // --- Core Actions ---
  async function advance(){
    const token = getToken();
    const status = qs('#advance-status');
    status.textContent = '結算中...';
    try{
      await fetchJSON('/tick/advance', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ token })
      });
      status.textContent = '已推進一天，利息與營收已結算';
      await loadState();
      // Reload active tab data
      const activeTab = qs('.tab-btn.active').dataset.tab;
      openTab(activeTab);
    }catch(e){ status.textContent = `失敗: ${e.message}`; }
  }

  async function submitLeaderboard(){
    const token = getToken();
    const status = qs('#advance-status');
    status.textContent = '提交中...';
    try{
      const res = await fetchJSON('/leaderboard/submit_web', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ token })
      });
      status.textContent = `已提交，資產=${formatNumber(res.asset)}，天數=${res.days}`;
      alert(`已提交排行榜！\n資產: $${formatNumber(res.asset)}\n天數: ${res.days}`);
    }catch(e){ alert(e.message); }
  }

  function startAutoRefresh(){
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(() => {
      loadState().catch(()=>{});
    }, 5000);
  }

  function wireDashboard(){
    qs('#btn-login')?.addEventListener('click', login);
    qs('#btn-advance')?.addEventListener('click', advance);
    qs('#btn-deposit')?.addEventListener('click', () => bankAction('deposit'));
    qs('#btn-withdraw')?.addEventListener('click', () => bankAction('withdraw'));
    qs('#btn-loan')?.addEventListener('click', () => bankAction('loan'));
    qs('#btn-repay')?.addEventListener('click', () => bankAction('repay'));
    qs('#btn-start-biz')?.addEventListener('click', startBusiness);
    qs('#btn-submit-lb')?.addEventListener('click', submitLeaderboard);

    qsa('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => openTab(btn.dataset.tab));
    });
  }

  async function initDashboard(){
    wireDashboard();
    const token = getToken();
    if(token){
      show(qs('#login-section'), false);
      show(qs('#game-section'), true);
      await loadState();
      startAutoRefresh();
    }
  }

  return { initDashboard, tradeStock, buyItem, sellItem, upgradeBusiness };
})();
