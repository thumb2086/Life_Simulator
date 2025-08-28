"""
Life Simulator Server - 市場新聞事件模組
處理市場新聞、事件生成和市場影響
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel


class NewsCategory(Enum):
    """新聞分類"""
    ECONOMIC = "economic"
    TECHNOLOGICAL = "technological"
    POLITICAL = "political"
    NATURAL = "natural"
    CORPORATE = "corporate"
    GLOBAL = "global"


class EventImpact(Enum):
    """事件影響程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TournamentType(Enum):
    """比賽類型"""
    WEALTH = "wealth"
    ACHIEVEMENTS = "achievements"
    TRADING = "trading"
    SOCIAL = "social"


@dataclass
class MarketNews:
    """市場新聞"""
    news_id: str
    title: str
    content: str
    category: NewsCategory
    impact: EventImpact
    affected_stocks: List[str]
    sentiment_score: float  # -1 到 1，負數表示利空，正數表示利多
    published_at: datetime
    expires_at: Optional[datetime]


@dataclass
class MarketEvent:
    """市場事件"""
    event_id: str
    title: str
    description: str
    event_type: str
    severity: EventImpact
    affected_sectors: List[str]
    price_changes: Dict[str, float]  # 股票代碼 -> 價格變化百分比
    duration_hours: int
    triggered_at: datetime


@dataclass
class Tournament:
    """比賽"""
    tournament_id: str
    name: str
    description: str
    type: TournamentType
    start_time: datetime
    end_time: datetime
    prize_pool: float
    rules: Dict[str, Any]
    participants: List[str]
    status: str  # upcoming, active, completed


class NewsGenerationPayload(BaseModel):
    """新聞生成請求載荷"""
    category: Optional[str] = None
    impact: Optional[str] = None


class EventGenerationPayload(BaseModel):
    """事件生成請求載荷"""
    event_type: Optional[str] = None
    severity: Optional[str] = None


class TournamentPayload(BaseModel):
    """比賽創建請求載荷"""
    name: str
    description: str
    start_time: str
    end_time: str
    prize_pool: float
    rules: Optional[Dict[str, Any]] = None


class JoinTournamentPayload(BaseModel):
    """加入比賽請求載荷"""
    username: str
    tournament_id: str


class MarketNewsEventManager:
    """
    市場新聞事件管理器
    負責新聞生成、事件觸發和市場影響處理
    """

    def __init__(self, stock_manager, db_path: str):
        self.stock_manager = stock_manager
        self.db_path = db_path
        self._init_market_database()
        self._load_news_templates()

    def _init_market_database(self):
        """初始化市場資料庫"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()

            # 新聞表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS market_news (
                    news_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    affected_stocks TEXT,
                    sentiment_score REAL NOT NULL,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)

            # 市場事件表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS market_events (
                    event_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    affected_sectors TEXT,
                    price_changes TEXT,
                    duration_hours INTEGER NOT NULL,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)

            # 比賽表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    tournament_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    type TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    prize_pool REAL NOT NULL,
                    rules TEXT,
                    participants TEXT,
                    status TEXT DEFAULT 'upcoming'
                )
            """)

            conn.commit()

        finally:
            conn.close()

    def _load_news_templates(self):
        """載入新聞模板"""
        self.news_templates = {
            NewsCategory.ECONOMIC: [
                {
                    "title": "經濟數據意外強勁，{sector}板塊受惠",
                    "content": "最新經濟數據顯示{signal}，市場分析師認為這將利好{sector}相關企業。",
                    "impact": EventImpact.MEDIUM,
                    "sentiment": 0.3
                },
                {
                    "title": "{sector}行業面臨成本壓力",
                    "content": "原材料價格上漲導致{sector}企業成本增加，利潤空間受到擠壓。",
                    "impact": EventImpact.MEDIUM,
                    "sentiment": -0.2
                }
            ],
            NewsCategory.TECHNOLOGICAL: [
                {
                    "title": "科技巨頭宣布重大投資計劃",
                    "content": "知名科技公司宣布在{sector}領域投入巨額資金，預計將帶動相關產業鏈。",
                    "impact": EventImpact.HIGH,
                    "sentiment": 0.4
                },
                {
                    "title": "新技術突破或改變遊戲規則",
                    "content": "{sector}領域出現重大技術創新，業界預期將帶來革命性改變。",
                    "impact": EventImpact.CRITICAL,
                    "sentiment": 0.5
                }
            ],
            NewsCategory.CORPORATE: [
                {
                    "title": "公司季度業績超預期",
                    "content": "知名企業公布季度財報，營收和淨利均大幅超過市場預期。",
                    "impact": EventImpact.HIGH,
                    "sentiment": 0.4
                },
                {
                    "title": "企業併購傳聞發酵",
                    "content": "市場傳聞多家企業正在洽談併購事宜，相關股票受到關注。",
                    "impact": EventImpact.MEDIUM,
                    "sentiment": 0.2
                }
            ],
            NewsCategory.GLOBAL: [
                {
                    "title": "國際貿易協定取得進展",
                    "content": "多國就貿易協定達成共識，預計將利好全球經濟。",
                    "impact": EventImpact.HIGH,
                    "sentiment": 0.3
                },
                {
                    "title": "地緣政治緊張局勢升級",
                    "content": "國際局勢出現新變化，市場避險情緒升溫。",
                    "impact": EventImpact.CRITICAL,
                    "sentiment": -0.4
                }
            ]
        }

    def generate_market_news(self, category: Optional[NewsCategory] = None,
                           impact: Optional[EventImpact] = None) -> MarketNews:
        """
        生成市場新聞

        Args:
            category: 新聞分類
            impact: 影響程度

        Returns:
            市場新聞對象
        """
        import uuid

        # 隨機選擇分類和模板
        if not category:
            category = random.choice(list(self.news_templates.keys()))

        templates = self.news_templates.get(category, [])
        if not templates:
            # 返回通用新聞
            template = {
                "title": "市場出現新動態",
                "content": "市場分析師注意到一些值得關注的變化。",
                "impact": EventImpact.LOW,
                "sentiment": 0.0
            }
        else:
            template = random.choice(templates)

        # 生成具體內容
        sectors = ["科技", "金融", "醫療", "能源", "消費", "工業", "地產"]
        signals = ["GDP增長超出預期", "失業率創歷史新低", "通膨數據溫和", "貿易數據改善"]

        sector = random.choice(sectors)
        signal = random.choice(signals)

        title = template["title"].format(sector=sector, signal=signal)
        content = template["content"].format(sector=sector, signal=signal)

        # 確定受影響股票
        affected_stocks = self._get_related_stocks(sector)

        # 調整影響程度
        final_impact = impact or template["impact"]
        sentiment = template["sentiment"]

        # 建立新聞對象
        news = MarketNews(
            news_id=str(uuid.uuid4()),
            title=title,
            content=content,
            category=category,
            impact=final_impact,
            affected_stocks=affected_stocks,
            sentiment_score=sentiment,
            published_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )

        # 儲存新聞
        self._save_news(news)

        # 應用市場影響
        self._apply_news_impact(news)

        return news

    def _get_related_stocks(self, sector: str) -> List[str]:
        """獲取相關股票"""
        sector_stocks = {
            "科技": ["TSMC", "MTK"],
            "金融": ["BANK_A", "BANK_B"],
            "醫療": ["PHARMA_A", "PHARMA_B"],
            "能源": ["OIL_A", "GAS_B"],
            "消費": ["RETAIL_A", "FOOD_B"],
            "工業": ["IND_A", "MANU_B"],
            "地產": ["PROP_A", "CONST_B"]
        }

        return sector_stocks.get(sector, ["TSMC"])

    def _save_news(self, news: MarketNews):
        """儲存新聞"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO market_news
                (news_id, title, content, category, impact, affected_stocks,
                 sentiment_score, published_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                news.news_id,
                news.title,
                news.content,
                news.category.value,
                news.impact.value,
                json.dumps(news.affected_stocks),
                news.sentiment_score,
                news.published_at,
                news.expires_at
            ))

            conn.commit()

        finally:
            conn.close()

    def _apply_news_impact(self, news: MarketNews):
        """應用新聞對市場的影響"""
        if not news.affected_stocks:
            return

        # 計算價格變化
        base_change = news.sentiment_score * 0.05  # 基礎變化幅度

        for stock in news.affected_stocks:
            # 應用隨機變化
            change = base_change * (0.8 + random.random() * 0.4)  # ±20% 隨機性
            self.stock_manager.apply_price_change(stock, change)

    def generate_market_event(self, event_type: Optional[str] = None,
                            severity: Optional[EventImpact] = None) -> MarketEvent:
        """
        生成市場事件

        Args:
            event_type: 事件類型
            severity: 嚴重程度

        Returns:
            市場事件對象
        """
        import uuid

        # 事件類型定義
        event_types = {
            "market_crash": {
                "title": "市場崩盤",
                "description": "股市出現重大下跌，多個板塊受重創",
                "severity": EventImpact.CRITICAL,
                "affected_sectors": ["all"],
                "price_changes": {"*": -0.15}  # 所有股票下跌15%
            },
            "bull_market": {
                "title": "多頭行情啟動",
                "description": "市場信心回暖，多數股票上漲",
                "severity": EventImpact.HIGH,
                "affected_sectors": ["all"],
                "price_changes": {"*": 0.10}  # 所有股票上漲10%
            },
            "industry_boom": {
                "title": "行業景氣循環",
                "description": "特定行業出現投資熱潮",
                "severity": EventImpact.MEDIUM,
                "affected_sectors": ["tech", "finance"],
                "price_changes": {"TSMC": 0.08, "MTK": 0.08}
            },
            "economic_crisis": {
                "title": "經濟危機警報",
                "description": "經濟數據惡化，市場恐慌情緒蔓延",
                "severity": EventImpact.CRITICAL,
                "affected_sectors": ["all"],
                "price_changes": {"*": -0.20}
            }
        }

        # 隨機選擇事件類型
        if not event_type:
            event_type = random.choice(list(event_types.keys()))

        event_data = event_types.get(event_type)
        if not event_data:
            # 返回通用事件
            event_data = {
                "title": "市場波動",
                "description": "市場出現正常波動",
                "severity": EventImpact.LOW,
                "affected_sectors": [],
                "price_changes": {}
            }

        # 調整嚴重程度
        final_severity = severity or event_data["severity"]

        # 建立事件對象
        event = MarketEvent(
            event_id=str(uuid.uuid4()),
            title=event_data["title"],
            description=event_data["description"],
            event_type=event_type,
            severity=final_severity,
            affected_sectors=event_data["affected_sectors"],
            price_changes=event_data["price_changes"],
            duration_hours=24,  # 預設24小時
            triggered_at=datetime.now()
        )

        # 儲存事件
        self._save_event(event)

        # 應用事件影響
        self._apply_event_impact(event)

        return event

    def _save_event(self, event: MarketEvent):
        """儲存市場事件"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO market_events
                (event_id, title, description, event_type, severity, affected_sectors,
                 price_changes, duration_hours, triggered_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.title,
                event.description,
                event.event_type,
                event.severity.value,
                json.dumps(event.affected_sectors),
                json.dumps(event.price_changes),
                event.duration_hours,
                event.triggered_at,
                event.triggered_at + timedelta(hours=event.duration_hours)
            ))

            conn.commit()

        finally:
            conn.close()

    def _apply_event_impact(self, event: MarketEvent):
        """應用事件對市場的影響"""
        for stock, change in event.price_changes.items():
            if stock == "*":  # 所有股票
                # 這裡需要實現全市場價格調整
                pass
            else:
                self.stock_manager.apply_price_change(stock, change)

    def create_tournament(self, name: str, description: str, tournament_type: TournamentType,
                        start_time: datetime, end_time: datetime, prize_pool: float,
                        rules: Optional[Dict[str, Any]] = None) -> str:
        """
        創建比賽

        Args:
            name: 比賽名稱
            description: 比賽描述
            tournament_type: 比賽類型
            start_time: 開始時間
            end_time: 結束時間
            prize_pool: 獎金池
            rules: 比賽規則

        Returns:
            比賽ID
        """
        import uuid

        tournament = Tournament(
            tournament_id=str(uuid.uuid4()),
            name=name,
            description=description,
            type=tournament_type,
            start_time=start_time,
            end_time=end_time,
            prize_pool=prize_pool,
            rules=rules or {},
            participants=[],
            status="upcoming"
        )

        # 儲存比賽
        self._save_tournament(tournament)

        return tournament.tournament_id

    def _save_tournament(self, tournament: Tournament):
        """儲存比賽"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO tournaments
                (tournament_id, name, description, type, start_time, end_time,
                 prize_pool, rules, participants, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tournament.tournament_id,
                tournament.name,
                tournament.description,
                tournament.type.value,
                tournament.start_time,
                tournament.end_time,
                tournament.prize_pool,
                json.dumps(tournament.rules),
                json.dumps(tournament.participants),
                tournament.status
            ))

            conn.commit()

        finally:
            conn.close()

    def get_active_news(self) -> List[Dict[str, Any]]:
        """獲取活躍新聞"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT * FROM market_news
                WHERE expires_at > ?
                ORDER BY published_at DESC
            """, (datetime.now(),))

            news_list = []
            for row in cur.fetchall():
                news_list.append({
                    'news_id': row['news_id'],
                    'title': row['title'],
                    'content': row['content'],
                    'category': row['category'],
                    'impact': row['impact'],
                    'affected_stocks': json.loads(row['affected_stocks'] or '[]'),
                    'sentiment_score': row['sentiment_score'],
                    'published_at': row['published_at']
                })

            return news_list

        finally:
            conn.close()

    def get_active_events(self) -> List[Dict[str, Any]]:
        """獲取活躍事件"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT * FROM market_events
                WHERE expires_at > ?
                ORDER BY triggered_at DESC
            """, (datetime.now(),))

            events_list = []
            for row in cur.fetchall():
                events_list.append({
                    'event_id': row['event_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'event_type': row['event_type'],
                    'severity': row['severity'],
                    'affected_sectors': json.loads(row['affected_sectors'] or '[]'),
                    'price_changes': json.loads(row['price_changes'] or '{}'),
                    'triggered_at': row['triggered_at']
                })

            return events_list

        finally:
            conn.close()

    def get_upcoming_tournaments(self) -> List[Dict[str, Any]]:
        """獲取即將開始的比賽"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT * FROM tournaments
                WHERE start_time > ? AND status = 'upcoming'
                ORDER BY start_time ASC
            """, (datetime.now(),))

            tournaments = []
            for row in cur.fetchall():
                tournaments.append({
                    'tournament_id': row['tournament_id'],
                    'name': row['name'],
                    'description': row['description'],
                    'type': row['type'],
                    'start_time': row['start_time'],
                    'end_time': row['end_time'],
                    'prize_pool': row['prize_pool'],
                    'rules': json.loads(row['rules'] or '{}'),
                    'status': row['status']
                })

            return tournaments

        finally:
            conn.close()

    def simulate_market_impact(self, news_count: int = 3, event_probability: float = 0.1):
        """
        模擬市場影響

        Args:
            news_count: 新聞數量
            event_probability: 事件發生概率
        """
        # 生成新聞
        for _ in range(news_count):
            self.generate_market_news()

        # 可能生成事件
        if random.random() < event_probability:
            self.generate_market_event()
