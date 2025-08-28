import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from game_data import GameData
from unified_stock_manager import UnifiedStockManager


class NewsCategory(Enum):
    """新聞分類"""
    ECONOMIC = "economic"
    TECHNOLOGICAL = "technological"
    POLITICAL = "political"
    NATURAL = "natural"
    CORPORATE = "corporate"
    GLOBAL = "global"


class EventType(Enum):
    """事件類型"""
    MARKET_CRASH = "market_crash"
    BULL_MARKET = "bull_market"
    INDUSTRY_BOOM = "industry_boom"
    REGULATORY_CHANGE = "regulatory_change"
    NATURAL_DISASTER = "natural_disaster"
    TECHNOLOGICAL_BREAKTHROUGH = "technological_breakthrough"
    MERGER_ACQUISITION = "merger_acquisition"
    DIVIDEND_ANNOUNCEMENT = "dividend_announcement"


class NewsImpact(Enum):
    """新聞影響程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MarketNews:
    """市場新聞"""
    news_id: str
    title: str
    content: str
    category: NewsCategory
    impact: NewsImpact
    affected_stocks: List[str]
    price_changes: Dict[str, float]  # 股票代碼 -> 價格變化百分比
    duration_hours: int  # 影響持續時間
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


@dataclass
class MarketEvent:
    """市場事件"""
    event_id: str
    type: EventType
    title: str
    description: str
    severity: NewsImpact
    affected_industries: List[str]
    global_impact: Dict[str, Any]  # 整體市場影響
    stock_impacts: Dict[str, Dict[str, Any]]  # 股票代碼 -> 影響詳情
    duration_days: int
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


class NewsGenerator:
    """新聞生成器"""

    def __init__(self):
        self.templates = self._load_news_templates()
        self.company_names = self._load_company_names()
        self.event_templates = self._load_event_templates()

    def _load_news_templates(self) -> Dict[str, List[str]]:
        """載入新聞模板"""
        return {
            NewsCategory.ECONOMIC: [
                "{company} 公布 {quarter} 財報，{performance} 超出預期",
                "央行宣布 {policy} 政策，影響市場 {impact}",
                "GDP 成長率 {change}，經濟學家 {reaction}",
                "失業率 {change} 至 {rate}%，勞動市場 {trend}"
            ],
            NewsCategory.TECHNOLOGICAL: [
                "{company} 推出革命性 {product} 產品",
                "人工智慧技術 {advancement}，業界 {reaction}",
                "{company} 完成 {milestone} 里程碑",
                "區塊鏈技術應用 {expansion}，市場 {response}"
            ],
            NewsCategory.POLITICAL: [
                "政府宣布 {policy} 新政策",
                "{country} 與 {country2} 達成 {agreement} 協議",
                "監管機構 {action} {company} 相關規定",
                "國際貿易 {development}，影響全球市場"
            ],
            NewsCategory.NATURAL: [
                "{region} 發生 {disaster}，影響 {industry} 行業",
                "氣候變化導致 {impact}，農業產量 {change}",
                "{event} 天氣影響 {sector} 供應鏈",
                "自然災害造成 {damage}，保險業 {response}"
            ],
            NewsCategory.CORPORATE: [
                "{company} CEO {action}，股價 {reaction}",
                "{company} 宣布 {strategy} 策略轉型",
                "併購消息：{company} 收購 {target}",
                "{company} 股東大會通過 {decision}"
            ],
            NewsCategory.GLOBAL: [
                "全球經濟 {trend}，投資者 {sentiment}",
                "國際貨幣基金組織 {forecast} 經濟前景",
                "{continent} 市場 {performance}，投資機會 {assessment}",
                "地緣政治風險 {change}，避險資產 {response}"
            ]
        }

    def _load_company_names(self) -> List[str]:
        """載入公司名稱"""
        return [
            "台積電", "鴻海", "聯發科", "台塑", "中鋼", "中華電信",
            "國泰金控", "富邦金控", "玉山金", "兆豐金", "第一金",
            "大立光", "聯電", "南亞", "台化", "台泥"
        ]

    def _load_event_templates(self) -> Dict[str, Dict[str, Any]]:
        """載入事件模板"""
        return {
            EventType.MARKET_CRASH: {
                "title": "市場重挫！投資者信心崩潰",
                "description": "股市出現重大跌幅，投資者紛紛拋售持股",
                "global_impact": {"volatility": 0.15, "trend": "bearish"}
            },
            EventType.BULL_MARKET: {
                "title": "牛市來臨！市場一片看好",
                "description": "經濟數據優於預期，市場信心大幅提升",
                "global_impact": {"volatility": 0.05, "trend": "bullish"}
            },
            EventType.INDUSTRY_BOOM: {
                "title": "{industry} 行業蓬勃發展",
                "description": "新技術應用帶動行業快速成長",
                "global_impact": {"volatility": 0.08, "trend": "bullish"}
            },
            EventType.TECHNOLOGICAL_BREAKTHROUGH: {
                "title": "科技突破！{technology} 技術取得重大進展",
                "description": "新技術將改變整個行業格局",
                "global_impact": {"volatility": 0.10, "trend": "bullish"}
            },
            EventType.NATURAL_DISASTER: {
                "title": "天災影響！{region} 遭受 {disaster}",
                "description": "自然災害造成供應鏈中斷",
                "global_impact": {"volatility": 0.12, "trend": "bearish"}
            }
        }

    def generate_news(self, category: NewsCategory, impact: NewsImpact = NewsImpact.MEDIUM) -> MarketNews:
        """生成新聞"""
        news_id = f"news_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"

        # 隨機選擇模板
        template = random.choice(self.templates[category])

        # 生成新聞內容
        title, content = self._fill_template(template, category)

        # 決定受影響的股票
        affected_stocks = self._determine_affected_stocks(category, impact)

        # 計算價格變化
        price_changes = self._calculate_price_changes(affected_stocks, impact)

        # 設定持續時間
        duration_hours = self._calculate_duration(impact)

        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=duration_hours)

        return MarketNews(
            news_id=news_id,
            title=title,
            content=content,
            category=category,
            impact=impact,
            affected_stocks=affected_stocks,
            price_changes=price_changes,
            duration_hours=duration_hours,
            created_at=created_at,
            expires_at=expires_at
        )

    def generate_event(self, event_type: EventType, severity: NewsImpact = NewsImpact.MEDIUM) -> MarketEvent:
        """生成市場事件"""
        event_id = f"event_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"

        template = self.event_templates[event_type]

        # 填入模板變數
        title = self._fill_event_title(template["title"], event_type)
        description = self._fill_event_description(template["description"], event_type)

        # 決定受影響的行業
        affected_industries = self._determine_affected_industries(event_type)

        # 計算整體影響
        global_impact = template["global_impact"].copy()
        global_impact.update(self._calculate_event_impact(event_type, severity))

        # 計算個別股票影響
        stock_impacts = self._calculate_stock_impacts(event_type, affected_industries, severity)

        # 設定持續時間
        duration_days = self._calculate_event_duration(severity)

        created_at = datetime.now()
        expires_at = created_at + timedelta(days=duration_days)

        return MarketEvent(
            event_id=event_id,
            type=event_type,
            title=title,
            description=description,
            severity=severity,
            affected_industries=affected_industries,
            global_impact=global_impact,
            stock_impacts=stock_impacts,
            duration_days=duration_days,
            created_at=created_at,
            expires_at=expires_at
        )

    def _fill_template(self, template: str, category: NewsCategory) -> Tuple[str, str]:
        """填入新聞模板"""
        # 根據分類填入適當的變數
        if category == NewsCategory.ECONOMIC:
            company = random.choice(self.company_names)
            quarter = random.choice(["Q1", "Q2", "Q3", "Q4"])
            performance = random.choice(["營收", "獲利", "EPS"])
            impact = random.choice(["正面", "負面"])

            title = f"{company} {quarter} 財報亮眼，股價 {random.choice(['上漲', '下跌'])}"
            content = f"{company} 公布 {quarter} 財報，{performance} 表現 {random.choice(['優於', '低於'])} 預期，市場反應 {impact}。"

        elif category == NewsCategory.TECHNOLOGICAL:
            company = random.choice(self.company_names)
            product = random.choice(["AI 晶片", "5G 設備", "新能源技術", "量子電腦"])
            advancement = random.choice(["重大突破", "創新應用", "技術升級"])

            title = f"{company} 推出 {product}，科技股受惠"
            content = f"{company} 宣布 {advancement}，預計將帶動相關供應鏈業績成長。"

        elif category == NewsCategory.CORPORATE:
            company = random.choice(self.company_names)
            action = random.choice(["宣布退休", "加入新公司", "策略調整"])
            reaction = random.choice(["上漲 5%", "下跌 3%", "維持平盤"])

            title = f"{company} 高層異動，股價 {reaction}"
            content = f"{company} CEO {action}，市場反應 {reaction}。"

        else:
            # 通用模板
            title = f"市場新聞：{category.value} 類相關消息"
            content = f"近期 {category.value} 領域出現新發展，影響相關投資標的。"

        return title, content

    def _fill_event_title(self, template: str, event_type: EventType) -> str:
        """填入事件標題"""
        if event_type == EventType.NATURAL_DISASTER:
            regions = ["台灣東部", "美國西岸", "日本九州", "歐洲中部"]
            disasters = ["地震", "颱風", "洪水", "火山爆發"]
            return template.format(
                region=random.choice(regions),
                disaster=random.choice(disasters)
            )
        elif event_type == EventType.TECHNOLOGICAL_BREAKTHROUGH:
            technologies = ["人工智慧", "量子運算", "新能源", "生物科技"]
            return template.format(technology=random.choice(technologies))
        elif event_type == EventType.INDUSTRY_BOOM:
            industries = ["半導體", "電動車", "生技醫療", "綠能科技"]
            return template.format(industry=random.choice(industries))
        else:
            return template

    def _fill_event_description(self, template: str, event_type: EventType) -> str:
        """填入事件描述"""
        return template  # 簡化版，直接返回模板

    def _determine_affected_stocks(self, category: NewsCategory, impact: NewsImpact) -> List[str]:
        """決定受影響的股票"""
        # 根據新聞分類決定受影響的股票
        industry_map = {
            NewsCategory.ECONOMIC: ["台積電", "台塑", "中鋼"],
            NewsCategory.TECHNOLOGICAL: ["台積電", "聯發科", "聯電"],
            NewsCategory.CORPORATE: ["台積電", "鴻海", "國泰金控"],
            NewsCategory.POLITICAL: ["中華電信", "台泥", "台化"],
            NewsCategory.NATURAL: ["台塑", "台化", "台泥"],
            NewsCategory.GLOBAL: ["台積電", "鴻海", "台塑"]
        }

        base_stocks = industry_map.get(category, ["台積電"])
        num_stocks = {"low": 1, "medium": 2, "high": 3, "critical": 4}[impact.value]

        return random.sample(base_stocks, min(num_stocks, len(base_stocks)))

    def _determine_affected_industries(self, event_type: EventType) -> List[str]:
        """決定受影響的行業"""
        industry_map = {
            EventType.MARKET_CRASH: ["科技業", "金融業", "服務業"],
            EventType.BULL_MARKET: ["科技業", "金融業", "服務業"],
            EventType.INDUSTRY_BOOM: ["科技業"],
            EventType.TECHNOLOGICAL_BREAKTHROUGH: ["科技業"],
            EventType.NATURAL_DISASTER: ["一級產業", "服務業"]
        }

        return industry_map.get(event_type, ["科技業"])

    def _calculate_price_changes(self, stocks: List[str], impact: NewsImpact) -> Dict[str, float]:
        """計算價格變化"""
        impact_multipliers = {
            NewsImpact.LOW: 0.02,
            NewsImpact.MEDIUM: 0.05,
            NewsImpact.HIGH: 0.10,
            NewsImpact.CRITICAL: 0.15
        }

        multiplier = impact_multipliers[impact]
        changes = {}

        for stock in stocks:
            # 正面或負面影響
            direction = 1 if random.random() > 0.3 else -1  # 70% 機會正面
            change_percent = direction * multiplier * random.uniform(0.5, 1.5)
            changes[stock] = change_percent

        return changes

    def _calculate_duration(self, impact: NewsImpact) -> int:
        """計算影響持續時間"""
        duration_map = {
            NewsImpact.LOW: (4, 8),
            NewsImpact.MEDIUM: (8, 16),
            NewsImpact.HIGH: (16, 24),
            NewsImpact.CRITICAL: (24, 48)
        }

        min_hours, max_hours = duration_map[impact]
        return random.randint(min_hours, max_hours)

    def _calculate_event_impact(self, event_type: EventType, severity: NewsImpact) -> Dict[str, Any]:
        """計算事件影響"""
        base_impacts = {
            EventType.MARKET_CRASH: {"market_drop": 0.05},
            EventType.BULL_MARKET: {"market_rise": 0.03},
            EventType.INDUSTRY_BOOM: {"industry_boost": 0.08},
            EventType.TECHNOLOGICAL_BREAKTHROUGH: {"tech_boost": 0.06},
            EventType.NATURAL_DISASTER: {"supply_disruption": 0.04}
        }

        severity_multipliers = {
            NewsImpact.LOW: 0.5,
            NewsImpact.MEDIUM: 1.0,
            NewsImpact.HIGH: 1.5,
            NewsImpact.CRITICAL: 2.0
        }

        base_impact = base_impacts.get(event_type, {})
        multiplier = severity_multipliers[severity]

        return {key: value * multiplier for key, value in base_impact.items()}

    def _calculate_stock_impacts(self, event_type: EventType, industries: List[str],
                               severity: NewsImpact) -> Dict[str, Dict[str, Any]]:
        """計算個別股票影響"""
        # 簡化版：返回空的影響字典
        # 在實際實現中，這裡會根據事件類型和行業計算具體股票影響
        return {}

    def _calculate_event_duration(self, severity: NewsImpact) -> int:
        """計算事件持續時間"""
        duration_map = {
            NewsImpact.LOW: (1, 3),
            NewsImpact.MEDIUM: (3, 7),
            NewsImpact.HIGH: (7, 14),
            NewsImpact.CRITICAL: (14, 30)
        }

        min_days, max_days = duration_map[severity]
        return random.randint(min_days, max_days)


class MarketNewsEventManager:
    """
    市場新聞和事件管理系統
    動態生成新聞和事件，影響市場波動
    """

    def __init__(self, stock_manager: UnifiedStockManager, db_path: str = None):
        self.stock_manager = stock_manager
        self.db_path = db_path
        self.news_generator = NewsGenerator()
        self.active_news: List[MarketNews] = []
        self.active_events: List[MarketEvent] = []
        self.news_history: List[MarketNews] = []
        self.event_history: List[MarketEvent] = []

        # 載入現有新聞和事件
        self._load_persistent_data()

        # 啟動新聞生成器
        self._start_news_generator()

    def _start_news_generator(self):
        """啟動新聞生成器"""
        # 每隔一段時間自動生成新聞
        pass  # 在實際實現中會啟動定時任務

    def generate_random_news(self, category: Optional[NewsCategory] = None,
                           impact: Optional[NewsImpact] = None) -> MarketNews:
        """生成隨機新聞"""
        if not category:
            category = random.choice(list(NewsCategory))

        if not impact:
            impact = random.choice(list(NewsImpact))

        news = self.news_generator.generate_news(category, impact)
        self.active_news.append(news)

        # 應用新聞影響到市場
        self._apply_news_impact(news)

        logging.info(f"生成新聞: {news.title}")
        return news

    def generate_random_event(self, event_type: Optional[EventType] = None,
                            severity: Optional[NewsImpact] = None) -> MarketEvent:
        """生成隨機事件"""
        if not event_type:
            event_type = random.choice(list(EventType))

        if not severity:
            severity = random.choice(list(NewsImpact))

        event = self.news_generator.generate_event(event_type, severity)
        self.active_events.append(event)

        # 應用事件影響到市場
        self._apply_event_impact(event)

        logging.info(f"生成事件: {event.title}")
        return event

    def _apply_news_impact(self, news: MarketNews):
        """應用新聞影響到市場"""
        current_prices = self.stock_manager.sync_prices_from_database()

        updated_prices = current_prices.copy()

        # 應用價格變化
        for stock, change_percent in news.price_changes.items():
            if stock in updated_prices:
                old_price = updated_prices[stock]
                new_price = old_price * (1 + change_percent)
                updated_prices[stock] = max(0.01, new_price)  # 確保價格不為負

        # 更新市場價格
        self.stock_manager.sync_prices_to_database(updated_prices)

    def _apply_event_impact(self, event: MarketEvent):
        """應用事件影響到市場"""
        # 根據事件類型應用不同的影響
        if event.type == EventType.MARKET_CRASH:
            self._apply_market_crash(event)
        elif event.type == EventType.BULL_MARKET:
            self._apply_bull_market(event)
        elif event.type == EventType.INDUSTRY_BOOM:
            self._apply_industry_boom(event, event.affected_industries[0] if event.affected_industries else "科技業")

    def _apply_market_crash(self, event: MarketEvent):
        """應用市場崩盤影響"""
        current_prices = self.stock_manager.sync_prices_from_database()

        # 所有股票下跌
        crash_severity = event.global_impact.get("volatility", 0.05)
        updated_prices = {}

        for stock, price in current_prices.items():
            drop_percent = random.uniform(crash_severity * 0.5, crash_severity * 1.5)
            updated_prices[stock] = max(0.01, price * (1 - drop_percent))

        self.stock_manager.sync_prices_to_database(updated_prices)

    def _apply_bull_market(self, event: MarketEvent):
        """應用牛市影響"""
        current_prices = self.stock_manager.sync_prices_from_database()

        # 所有股票上漲
        bull_strength = event.global_impact.get("volatility", 0.03)
        updated_prices = {}

        for stock, price in current_prices.items():
            rise_percent = random.uniform(bull_strength * 0.5, bull_strength * 1.5)
            updated_prices[stock] = price * (1 + rise_percent)

        self.stock_manager.sync_prices_to_database(updated_prices)

    def _apply_industry_boom(self, event: MarketEvent, industry: str):
        """應用行業繁榮影響"""
        industry_stocks = self.stock_manager.get_industry_stocks(industry)
        current_prices = self.stock_manager.sync_prices_from_database()

        # 行業相關股票上漲
        boom_strength = event.global_impact.get("volatility", 0.08)
        updated_prices = current_prices.copy()

        for stock in industry_stocks:
            if stock in updated_prices:
                rise_percent = random.uniform(boom_strength * 0.7, boom_strength * 1.3)
                updated_prices[stock] = updated_prices[stock] * (1 + rise_percent)

        self.stock_manager.sync_prices_to_database(updated_prices)

    def get_active_news(self) -> List[Dict[str, Any]]:
        """獲取活躍新聞"""
        # 檢查過期新聞
        self._cleanup_expired_news()

        return [{
            'news_id': news.news_id,
            'title': news.title,
            'content': news.content,
            'category': news.category.value,
            'impact': news.impact.value,
            'affected_stocks': news.affected_stocks,
            'price_changes': news.price_changes,
            'created_at': news.created_at.isoformat(),
            'expires_at': news.expires_at.isoformat()
        } for news in self.active_news]

    def get_active_events(self) -> List[Dict[str, Any]]:
        """獲取活躍事件"""
        # 檢查過期事件
        self._cleanup_expired_events()

        return [{
            'event_id': event.event_id,
            'type': event.type.value,
            'title': event.title,
            'description': event.description,
            'severity': event.severity.value,
            'affected_industries': event.affected_industries,
            'global_impact': event.global_impact,
            'created_at': event.created_at.isoformat(),
            'expires_at': event.expires_at.isoformat()
        } for event in self.active_events]

    def _cleanup_expired_news(self):
        """清理過期新聞"""
        now = datetime.now()
        expired_news = [news for news in self.active_news if news.expires_at < now]

        for news in expired_news:
            self.active_news.remove(news)
            self.news_history.append(news)

    def _cleanup_expired_events(self):
        """清理過期事件"""
        now = datetime.now()
        expired_events = [event for event in self.active_events if event.expires_at < now]

        for event in expired_events:
            self.active_events.remove(event)
            self.event_history.append(event)

    def get_market_sentiment(self) -> Dict[str, Any]:
        """獲取市場情緒"""
        # 分析近期新聞和事件來判斷市場情緒
        recent_news = [news for news in self.active_news
                      if (datetime.now() - news.created_at).total_seconds() < 3600]  # 最近1小時

        positive_news = sum(1 for news in recent_news if any(change > 0 for change in news.price_changes.values()))
        negative_news = sum(1 for news in recent_news if any(change < 0 for change in news.price_changes.values()))

        total_news = len(recent_news)

        if total_news == 0:
            sentiment = "neutral"
            confidence = 0.5
        else:
            positive_ratio = positive_news / total_news
            if positive_ratio > 0.6:
                sentiment = "bullish"
                confidence = positive_ratio
            elif positive_ratio < 0.4:
                sentiment = "bearish"
                confidence = 1 - positive_ratio
            else:
                sentiment = "neutral"
                confidence = 0.5

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'recent_news_count': total_news,
            'positive_news': positive_news,
            'negative_news': negative_news,
            'active_events': len(self.active_events)
        }

    def _load_persistent_data(self):
        """載入持久化資料"""
        # 在實際實現中，這裡會從資料庫載入新聞和事件歷史
        pass

    def _save_persistent_data(self):
        """儲存持久化資料"""
        # 在實際實現中，這裡會將新聞和事件歷史儲存到資料庫
        pass
