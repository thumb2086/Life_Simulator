/**
 * Life Simulator — Phaser 3 Frontend
 * Top-down 2D town with buildings, character, and API-driven gameplay.
 */

const API = 'http://127.0.0.1:8000';

// ── Building definitions ────────────────────────────────────────────
const BUILDINGS = [
  { id: 'bank',    label: '銀行',     x: 400, y: 120, w: 160, h: 100, color: 0x2196F3, icon: '💰' },
  { id: 'home',    label: '家',       x: 400, y: 450, w: 160, h: 100, color: 0x8BC34A, icon: '🏠' },
  { id: 'gym',     label: '健身房',   x: 100, y: 280, w: 140, h: 90,  color: 0xFF9800, icon: '💪' },
  { id: 'school',  label: '學校',     x: 700, y: 280, w: 140, h: 90,  color: 0x9C27B0, icon: '📚' },
  { id: 'office',  label: '公司',     x: 700, y: 120, w: 140, h: 90,  color: 0x607D8B, icon: '🏢' },
  { id: 'stock',   label: '證券所',   x: 100, y: 120, w: 140, h: 90,  color: 0xE91E63, icon: '📈' },
  { id: 'park',    label: '公園',     x: 250, y: 280, w: 120, h: 80,  color: 0x4CAF50, icon: '🌳' },
  { id: 'cafe',    label: '咖啡廳',   x: 550, y: 280, w: 120, h: 80,  color: 0x795548, icon: '☕' },
  { id: 'market',  label: '市場',     x: 400, y: 280, w: 100, h: 70,  color: 0xFFC107, icon: '🛒' },
];

// ── Game state ──────────────────────────────────────────────────────
let gameState = null;
let selectedBuilding = null;
let characterSprite = null;
let buildingSprites = [];
let targetPos = null;
let hudTexts = {};

// ── API helper ──────────────────────────────────────────────────────
async function api(endpoint, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API}${endpoint}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

async function refreshState() {
  try {
    gameState = await api('/api/state');
    updatePanel();
  } catch (e) {
    console.warn('API not reachable:', e.message);
  }
}

async function doAction(endpoint, body = null) {
  try {
    const result = await api(endpoint, 'POST', body);
    gameState = result.state;
    showEvent(result.message);
    updatePanel();
    return result;
  } catch (e) {
    showError(e.message);
    throw e;
  }
}

// ── Panel UI ────────────────────────────────────────────────────────
function updatePanel() {
  if (!gameState) return;
  const s = gameState;

  // Stats
  document.getElementById('stats-section').innerHTML = `
    <div class="section-title">📊 狀態總覽</div>
    <div class="stat-row"><span class="stat-label">📅 天數</span><span class="stat-value">${s.days}</span></div>
    <div class="stat-row"><span class="stat-label">💵 現金</span><span class="stat-value green">$${fmt(s.cash)}</span></div>
    <div class="stat-row"><span class="stat-label">🏦 存款</span><span class="stat-value green">$${fmt(s.balance)}</span></div>
    <div class="stat-row"><span class="stat-label">💳 貸款</span><span class="stat-value">$${fmt(s.loan)}</span></div>
    <div class="stat-row"><span class="stat-label">💰 總資產</span><span class="stat-value gold">$${fmt(s.total_assets)}</span></div>

    <div class="section-title">❤️ 健康</div>
    <div class="stat-row"><span class="stat-label">⚡ 體力</span><span class="stat-value">${bar(s.health.energy, 100)}</span></div>
    <div class="stat-row"><span class="stat-label">😊 心情</span><span class="stat-value">${bar(s.health.mood, 100)}</span></div>
    <div class="stat-row"><span class="stat-label">😰 壓力</span><span class="stat-value">${bar(s.health.stress, 100)}</span></div>
    <div class="stat-row"><span class="stat-label">💪 體能</span><span class="stat-value">${bar(s.health.fitness, 100)}</span></div>

    <div class="section-title">🏠 住房</div>
    <div class="stat-row"><span class="stat-label">類型</span><span class="stat-value">${s.housing.type}</span></div>
    <div class="stat-row"><span class="stat-label">舒適度</span><span class="stat-value">${bar(s.housing.comfort, 100)}</span></div>
    <div class="stat-row"><span class="stat-label">設施</span><span class="stat-value">${s.housing.facilities.length > 0 ? s.housing.facilities.join(', ') : '無'}</span></div>

    <div class="section-title">📚 教育</div>
    <div class="stat-row"><span class="stat-label">學歷</span><span class="stat-value">${s.education.degree}</span></div>
    <div class="stat-row"><span class="stat-label">職稱</span><span class="stat-value">${s.education.job_title}</span></div>
    <div class="stat-row"><span class="stat-label">技能</span><span class="stat-value">${Object.keys(s.education.skills).length} 項</span></div>

    <div class="section-title">👥 社交</div>
    <div class="stat-row"><span class="stat-label">聲望</span><span class="stat-value">${s.social.reputation}</span></div>
    <div class="stat-row"><span class="stat-label">人脈</span><span class="stat-value">${s.social.network_size}</span></div>
    <div class="stat-row"><span class="stat-label">影響力</span><span class="stat-value">${s.social.influence}</span></div>

    ${s.btc_balance > 0 ? `
    <div class="section-title">₿ 比特幣</div>
    <div class="stat-row"><span class="stat-label">持有</span><span class="stat-value gold">${s.btc_balance.toFixed(4)} BTC</span></div>
    <div class="stat-row"><span class="stat-label">算力</span><span class="stat-value">${s.btc_hashrate} kh</span></div>
    ` : ''}
  `;
}

function showBuildingActions(building) {
  selectedBuilding = building;
  const title = document.getElementById('building-title');
  const actions = document.getElementById('actions-section');
  title.style.display = 'block';
  title.textContent = `${building.icon} ${building.label}`;

  const btns = {
    bank: `
      <button class="action-btn success" onclick="doAction('/api/bank/deposit',{amount:1000})">存入 $1,000</button>
      <button class="action-btn success" onclick="doAction('/api/bank/deposit',{amount:5000})">存入 $5,000</button>
      <button class="action-btn" onclick="doAction('/api/bank/withdraw',{amount:1000})">領出 $1,000</button>
      <button class="action-btn" onclick="doAction('/api/bank/withdraw',{amount:5000})">領出 $5,000</button>
      <button class="action-btn" onclick="doAction('/api/bank/loan',{amount:10000})">貸款 $10,000</button>
      <button class="action-btn danger" onclick="doAction('/api/bank/repay',{amount:10000})">償還 $10,000</button>
    `,
    home: `
      <button class="action-btn success" onclick="doAction('/api/housing/rent')">租屋</button>
      <button class="action-btn success" onclick="doAction('/api/housing/buy',{property_type:'小套房'})">買小套房</button>
      <button class="action-btn success" onclick="doAction('/api/housing/buy',{property_type:'公寓'})">買公寓</button>
      <button class="action-btn success" onclick="doAction('/api/housing/buy',{property_type:'透天'})">買透天</button>
      <button class="action-btn" onclick="doAction('/api/housing/facility',{name:'冷氣'})">安裝冷氣</button>
      <button class="action-btn" onclick="doAction('/api/housing/facility',{name:'按摩椅'})">安裝按摩椅</button>
      <button class="action-btn danger" onclick="doAction('/api/housing/sell')">賣房</button>
    `,
    gym: `
      <button class="action-btn success" onclick="doAction('/api/health/exercise')">運動</button>
      <button class="action-btn success" onclick="doAction('/api/health/rest')">休息</button>
      <button class="action-btn" onclick="doAction('/api/health/meditate')">冥想</button>
      <button class="action-btn" onclick="doAction('/api/health/gym',{level:1})">加入健身房 $500</button>
    `,
    school: `
      <button class="action-btn success" onclick="doAction('/api/edu/study',{skill:'程式'})">學程式</button>
      <button class="action-btn success" onclick="doAction('/api/edu/study',{skill:'技術'})">學技術</button>
      <button class="action-btn success" onclick="doAction('/api/edu/study',{skill:'管理'})">學管理</button>
      <button class="action-btn success" onclick="doAction('/api/edu/study',{skill:'金融'})">學金融</button>
      <button class="action-btn" onclick="doAction('/api/edu/degree',{degree:'大學'})">讀大學</button>
      <button class="action-btn" onclick="doAction('/api/edu/degree',{degree:'碩士'})">讀碩士</button>
      <button class="action-btn" onclick="doAction('/api/edu/cert',{cert:'PMP'})">考 PMP 證照</button>
    `,
    office: `
      <button class="action-btn success" onclick="doAction('/api/edu/job',{job_title:'實習生'})">應徵實習生</button>
      <button class="action-btn success" onclick="doAction('/api/edu/job',{job_title:'工程師'})">應徵工程師</button>
      <button class="action-btn success" onclick="doAction('/api/edu/job',{job_title:'資深工程師'})">應徵資深工程師</button>
      <button class="action-btn" onclick="doAction('/api/edu/job',{job_title:'經理'})">應徵經理</button>
    `,
    stock: `
      <div class="section-title" style="font-size:13px">股票交易</div>
      ${gameState ? Object.entries(gameState.stocks).filter(([k]) => k !== 'BTC').map(([code, s]) => `
        <div class="stat-row" style="font-size:12px">
          <span>${s.name} $${fmt(s.price)}</span>
          <span>持有 ${s.owned}</span>
        </div>
        <button class="action-btn success" onclick="doAction('/api/stock/buy',{code:'${code}',shares:1})">買 1 股</button>
        <button class="action-btn danger" onclick="doAction('/api/stock/sell',{code:'${code}',shares:1})">賣 1 股</button>
      `).join('') : ''}
      <div class="section-title" style="font-size:13px;margin-top:12px">₿ 比特幣</div>
      <div class="stat-row" style="font-size:12px">
        <span>BTC</span>
        <span>$${gameState ? fmt(gameState.stocks.BTC.price) : '---'}</span>
      </div>
      <button class="action-btn success" onclick="doAction('/api/btc/buy',{usd_amount:10000})">買 $10,000 BTC</button>
      <button class="action-btn danger" onclick="doAction('/api/btc/sell',{usd_amount:10000})">賣 $10,000 BTC</button>
      <button class="action-btn" onclick="doAction('/api/btc/miner',{count:1})">買礦機 $50,000</button>
    `,
    park: `
      <button class="action-btn success" onclick="doAction('/api/health/rest')">散步休息</button>
      <button class="action-btn success" onclick="doAction('/api/health/meditate')">冥想放鬆</button>
      <button class="action-btn success" onclick="doAction('/api/social/volunteer')">志工服務</button>
    `,
    cafe: `
      <button class="action-btn success" onclick="doAction('/api/health/eat',{quality:1})">吃便當 $50</button>
      <button class="action-btn success" onclick="doAction('/api/health/eat',{quality:2})">吃大餐 $150</button>
      <button class="action-btn success" onclick="doAction('/api/health/eat',{quality:3})">高級料理 $400</button>
      <button class="action-btn" onclick="doAction('/api/social/network')">社交聚會</button>
      <button class="action-btn" onclick="doAction('/api/social/event')">參加活動</button>
    `,
    market: `
      <button class="action-btn success" onclick="doAction('/api/health/eat',{quality:1})">買食材 $50</button>
      <button class="action-btn success" onclick="doAction('/api/social/gift',{target:'朋友'})">買禮物送朋友</button>
      <button class="action-btn" onclick="doAction('/api/social/gift',{target:'同事'})">買禮物送同事</button>
    `,
  };

  actions.innerHTML = btns[building.id] || '<p style="color:#889">無可用動作</p>';
}

function showEvent(msg) {
  const section = document.getElementById('events-section');
  const cls = msg.includes('+') || msg.includes('利息') || msg.includes('薪資') || msg.includes('配息') ? 'income' : 'expense';
  section.innerHTML = `
    <div class="section-title">📋 事件紀錄</div>
    <div class="event-log">
      <div class="${cls}">${new Date().toLocaleTimeString()} ${msg}</div>
      ${section.querySelector('.event-log') ? section.querySelector('.event-log').innerHTML : ''}
    </div>
  `;
}

function showError(msg) {
  showEvent(`❌ ${msg}`);
}

function fmt(n) { return Number(n).toLocaleString(); }
function bar(val, max) {
  const pct = Math.round((val / max) * 100);
  const filled = Math.round(val / max * 10);
  return '█'.repeat(filled) + '░'.repeat(10 - filled) + ` ${Math.round(val)}`;
}

// ── Phaser Game ─────────────────────────────────────────────────────
const config = {
  type: Phaser.AUTO,
  parent: 'game-container',
  width: 900,
  height: 600,
  backgroundColor: '#2d5016',
  scene: { preload, create, update },
  physics: { default: 'arcade', arcade: { debug: false } },
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
};

const game = new Phaser.Game(config);

function preload() {
  // Nothing to load — all graphics are procedural
}

function create() {
  const scene = this;
  const W = 900, H = 600;

  // ── Ground ────────────────────────────────────────────────
  const graphics = scene.add.graphics();

  // Grass background
  graphics.fillStyle(0x3d7a1e, 1);
  graphics.fillRect(0, 0, W, H);

  // Roads (horizontal and vertical)
  graphics.fillStyle(0x555555, 1);
  graphics.fillRect(0, 200, W, 50);   // horizontal road
  graphics.fillRect(0, 370, W, 50);   // horizontal road 2
  graphics.fillRect(370, 0, 50, H);   // vertical road
  graphics.fillRect(570, 0, 50, H);   // vertical road 2

  // Road stripes
  graphics.lineStyle(2, 0xFFFF00, 0.5);
  for (let x = 0; x < W; x += 30) {
    graphics.lineBetween(x, 224, x + 15, 224);
    graphics.lineBetween(x, 394, x + 15, 394);
  }

  // Sidewalks
  graphics.fillStyle(0x888888, 0.5);
  graphics.fillRect(0, 195, W, 5);
  graphics.fillRect(0, 250, W, 5);
  graphics.fillRect(0, 365, W, 5);
  graphics.fillRect(0, 420, W, 5);

  // ── Buildings ────────────────────────────────────────────
  buildingSprites = [];
  BUILDINGS.forEach(b => {
    const container = scene.add.container(b.x, b.y);

    // Shadow
    const shadow = scene.add.graphics();
    shadow.fillStyle(0x000000, 0.2);
    shadow.fillRoundedRect(-b.w / 2 + 4, -b.h / 2 + 4, b.w, b.h, 8);
    container.add(shadow);

    // Building body
    const body = scene.add.graphics();
    body.fillStyle(b.color, 1);
    body.fillRoundedRect(-b.w / 2, -b.h / 2, b.w, b.h, 8);
    body.lineStyle(2, 0xffffff, 0.3);
    body.strokeRoundedRect(-b.w / 2, -b.h / 2, b.w, b.h, 8);
    container.add(body);

    // Roof accent
    const roof = scene.add.graphics();
    roof.fillStyle(b.color, 0.7);
    roof.fillRoundedRect(-b.w / 2, -b.h / 2, b.w, 15, { tl: 8, tr: 8, bl: 0, br: 0 });
    container.add(roof);

    // Icon
    const icon = scene.add.text(0, -10, b.icon, { fontSize: '28px' }).setOrigin(0.5);
    container.add(icon);

    // Label
    const label = scene.add.text(0, 18, b.label, {
      fontSize: '13px', fontFamily: 'Microsoft JhengHei, sans-serif',
      color: '#ffffff', fontStyle: 'bold',
      stroke: '#000000', strokeThickness: 2,
    }).setOrigin(0.5);
    container.add(label);

    // Interactive zone
    const hitArea = scene.add.zone(0, 0, b.w, b.h).setInteractive({ useHandCursor: true });
    hitArea.on('pointerover', () => {
      body.clear();
      body.fillStyle(b.color, 1);
      body.fillRoundedRect(-b.w / 2 - 2, -b.h / 2 - 2, b.w + 4, b.h + 4, 10);
      body.lineStyle(3, 0xe94560, 1);
      body.strokeRoundedRect(-b.w / 2 - 2, -b.h / 2 - 2, b.w + 4, b.h + 4, 10);
    });
    hitArea.on('pointerout', () => {
      body.clear();
      body.fillStyle(b.color, 1);
      body.fillRoundedRect(-b.w / 2, -b.h / 2, b.w, b.h, 8);
      body.lineStyle(2, 0xffffff, 0.3);
      body.strokeRoundedRect(-b.w / 2, -b.h / 2, b.w, b.h, 8);
    });
    hitArea.on('pointerdown', () => {
      targetPos = { x: b.x, y: b.y + b.h / 2 + 20 };
      selectedBuilding = b;
      showBuildingActions(b);
    });
    container.add(hitArea);
    container.setDepth(1);

    buildingSprites.push({ data: b, container, body });
  });

  // ── Character ─────────────────────────────────────────────
  const charGfx = scene.add.graphics();
  // Body
  charGfx.fillStyle(0x3498db, 1);
  charGfx.fillCircle(0, 5, 10);
  // Head
  charGfx.fillStyle(0xf5cba7, 1);
  charGfx.fillCircle(0, -10, 8);
  // Eyes
  charGfx.fillStyle(0x000000, 1);
  charGfx.fillCircle(-3, -11, 1.5);
  charGfx.fillCircle(3, -11, 1.5);

  characterSprite = scene.add.sprite(450, 480, '__DEFAULT');
  characterSprite.setVisible(false);  // hide default

  // Use graphics as character
  charGfx.setPosition(450, 480);
  charGfx.setDepth(10);
  scene.charGraphics = charGfx;

  // Name tag
  const nameTag = scene.add.text(450, 460, '主角', {
    fontSize: '11px', fontFamily: 'Microsoft JhengHei, sans-serif',
    color: '#ffffff', stroke: '#000000', strokeThickness: 2,
  }).setOrigin(0.5).setDepth(11);
  scene.nameTag = nameTag;

  // ── HUD (top bar) ────────────────────────────────────────
  const hudBg = scene.add.graphics();
  hudBg.fillStyle(0x0f3460, 0.9);
  hudBg.fillRect(0, 0, W, 36);
  hudBg.setDepth(20);

  hudTexts.days = scene.add.text(10, 9, '📅 Day 0', {
    fontSize: '14px', color: '#e0e0e0', fontFamily: 'sans-serif'
  }).setDepth(21);

  hudTexts.cash = scene.add.text(120, 9, '💵 $1,000', {
    fontSize: '14px', color: '#4ecca3', fontFamily: 'sans-serif'
  }).setDepth(21);

  hudTexts.assets = scene.add.text(280, 9, '💰 Total: $1,000', {
    fontSize: '14px', color: '#f0c040', fontFamily: 'sans-serif'
  }).setDepth(21);

  hudTexts.health = scene.add.text(480, 9, '❤️ 80/100', {
    fontSize: '14px', color: '#e94560', fontFamily: 'sans-serif'
  }).setDepth(21);

  // Day advance button
  const advBtn = scene.add.graphics();
  advBtn.fillStyle(0xe94560, 1);
  advBtn.fillRoundedRect(W - 120, 5, 110, 26, 6);
  advBtn.setDepth(21);

  const advText = scene.add.text(W - 65, 18, '▶ 進入下一天', {
    fontSize: '12px', color: '#ffffff', fontFamily: 'sans-serif', fontStyle: 'bold'
  }).setOrigin(0.5).setDepth(22);

  const advZone = scene.add.zone(W - 65, 18, 110, 26).setInteractive({ useHandCursor: true }).setDepth(23);
  advZone.on('pointerdown', async () => {
    advBtn.clear();
    advBtn.fillStyle(0xb33050, 1);
    advBtn.fillRoundedRect(W - 120, 5, 110, 26, 6);
    try {
      const result = await doAction('/api/advance');
      if (result.events) {
        result.events.forEach(e => showEvent(e));
      }
    } catch (e) {}
    advBtn.clear();
    advBtn.fillStyle(0xe94560, 1);
    advBtn.fillRoundedRect(W - 120, 5, 110, 26, 6);
  });

  // ── Trees decoration ─────────────────────────────────────
  const treePositions = [
    [50, 340], [830, 340], [50, 480], [830, 480],
    [200, 500], [600, 500], [150, 460], [650, 460],
    [300, 100], [550, 100], [300, 500], [550, 500],
  ];
  treePositions.forEach(([tx, ty]) => {
    const tree = scene.add.graphics();
    tree.fillStyle(0x2d5016, 1);
    tree.fillCircle(tx, ty - 10, 12);
    tree.fillCircle(tx - 8, ty - 5, 10);
    tree.fillCircle(tx + 8, ty - 5, 10);
    tree.fillStyle(0x8B4513, 1);
    tree.fillRect(tx - 2, ty, 4, 8);
    tree.setDepth(0);
  });

  // ── Interaction: click ground to move ─────────────────────
  scene.input.on('pointerdown', (pointer) => {
    if (pointer.x > 0 && pointer.x < W && pointer.y > 36 && pointer.y < H) {
      // Check if clicking on a building (handled by zone)
      // Otherwise move character
      if (!selectedBuilding || Math.abs(pointer.x - selectedBuilding.x) > 100) {
        targetPos = { x: pointer.x, y: Math.max(40, pointer.y) };
      }
    }
  });

  // ── Initial state ────────────────────────────────────────
  refreshState();

  // Poll state every 10s
  scene.time.addEvent({
    delay: 10000,
    loop: true,
    callback: refreshState,
  });
}

function update(time, delta) {
  const scene = this;
  if (!scene.charGraphics) return;

  const char = scene.charGraphics;
  const tag = scene.nameTag;

  if (targetPos) {
    const dx = targetPos.x - char.x;
    const dy = targetPos.y - char.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > 3) {
      const speed = 2.5;
      char.x += (dx / dist) * speed;
      char.y += (dy / dist) * speed;
      tag.x = char.x;
      tag.y = char.y - 20;
    } else {
      targetPos = null;
    }
  }

  // Update HUD from gameState
  if (gameState) {
    hudTexts.days.setText(`📅 Day ${gameState.days}`);
    hudTexts.cash.setText(`💵 $${fmt(gameState.cash)}`);
    hudTexts.assets.setText(`💰 Total: $${fmt(gameState.total_assets)}`);
    hudTexts.health.setText(`❤️ ${Math.round(gameState.health.energy)}/100`);
  }
}
