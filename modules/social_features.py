import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from game_data import GameData
from unified_data_manager import UnifiedDataManager


class FriendRequestStatus(Enum):
    """好友請求狀態"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class GuildRole(Enum):
    """公會角色"""
    LEADER = "leader"
    OFFICER = "officer"
    MEMBER = "member"
    RECRUIT = "recruit"


class GuildPermission(Enum):
    """公會權限"""
    INVITE_MEMBERS = "invite_members"
    KICK_MEMBERS = "kick_members"
    MANAGE_EVENTS = "manage_events"
    EDIT_GUILD = "edit_guild"
    VIEW_FINANCES = "view_finances"


class SocialEventType(Enum):
    """社交事件類型"""
    GUILD_CHALLENGE = "guild_challenge"
    FRIEND_TRADE = "friend_trade"
    ACHIEVEMENT_SHARE = "achievement_share"
    MARKET_PREDICTION = "market_prediction"
    PORTFOLIO_SHOWCASE = "portfolio_showcase"


@dataclass
class FriendRequest:
    """好友請求"""
    request_id: str
    from_username: str
    to_username: str
    message: str
    status: FriendRequestStatus
    created_at: datetime
    responded_at: Optional[datetime] = None


@dataclass
class Friend:
    """好友關係"""
    username1: str
    username2: str
    friendship_level: int  # 1-10
    established_date: datetime
    last_interaction: datetime
    shared_achievements: List[str]
    mutual_friends: List[str]


@dataclass
class Guild:
    """公會"""
    guild_id: str
    name: str
    description: str
    leader_username: str
    members: Dict[str, GuildRole]  # username -> role
    max_members: int
    level: int
    experience: int
    treasury: float
    created_at: datetime
    settings: Dict[str, Any]
    achievements: List[str]


@dataclass
class GuildEvent:
    """公會事件"""
    event_id: str
    guild_id: str
    type: SocialEventType
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    participants: List[str]
    rewards: Dict[str, Any]
    status: str  # upcoming, active, completed, cancelled


@dataclass
class SocialMessage:
    """社交訊息"""
    message_id: str
    from_username: str
    to_username: str
    content: str
    message_type: str  # friend, guild, system
    created_at: datetime
    is_read: bool = False


@dataclass
class SocialLeaderboard:
    """社交排行榜"""
    leaderboard_id: str
    name: str
    type: str  # wealth, achievements, trading, social
    period: str  # daily, weekly, monthly, all_time
    entries: List[Dict[str, Any]]
    last_updated: datetime


class SocialFeaturesManager:
    """
    社交功能管理系統
    包含好友、公會、排行榜和社交互動功能
    """

    def __init__(self, data_manager: UnifiedDataManager, db_path: str = None):
        self.data_manager = data_manager
        self.db_path = db_path
        self.friends: Dict[str, List[Friend]] = {}  # username -> friends list
        self.friend_requests: Dict[str, List[FriendRequest]] = {}  # username -> requests
        self.guilds: Dict[str, Guild] = {}
        self.guild_events: Dict[str, List[GuildEvent]] = {}  # guild_id -> events
        self.social_messages: Dict[str, List[SocialMessage]] = {}  # username -> messages
        self.leaderboards: Dict[str, SocialLeaderboard] = {}
        self.user_social_stats: Dict[str, Dict[str, Any]] = {}  # username -> stats

        # 初始化資料庫結構
        self._init_social_db_schema()

    def _init_social_db_schema(self):
        """初始化社交功能資料庫結構"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # 好友關係表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS friends (
                    username1 TEXT NOT NULL,
                    username2 TEXT NOT NULL,
                    friendship_level INTEGER DEFAULT 1,
                    established_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (username1, username2)
                )
            """)

            # 好友請求表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS friend_requests (
                    request_id TEXT PRIMARY KEY,
                    from_username TEXT NOT NULL,
                    to_username TEXT NOT NULL,
                    message TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded_at TIMESTAMP
                )
            """)

            # 公會表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS guilds (
                    guild_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    leader_username TEXT NOT NULL,
                    max_members INTEGER DEFAULT 50,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    treasury REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT
                )
            """)

            # 公會成員表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS guild_members (
                    guild_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, username)
                )
            """)

            # 社交訊息表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS social_messages (
                    message_id TEXT PRIMARY KEY,
                    from_username TEXT NOT NULL,
                    to_username TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'friend',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE
                )
            """)

            # 社交統計表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS social_stats (
                    username TEXT PRIMARY KEY,
                    friends_count INTEGER DEFAULT 0,
                    guilds_joined INTEGER DEFAULT 0,
                    messages_sent INTEGER DEFAULT 0,
                    achievements_shared INTEGER DEFAULT 0,
                    social_score INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            logging.warning(f"初始化社交資料庫失敗: {e}")

    # ===== 好友系統 =====

    def send_friend_request(self, from_username: str, to_username: str, message: str = "") -> str:
        """
        發送好友請求

        Args:
            from_username: 發送者用戶名
            to_username: 接收者用戶名
            message: 請求訊息

        Returns:
            請求ID
        """
        request_id = f"friend_req_{int(datetime.now().timestamp())}_{from_username}_{to_username}"

        request = FriendRequest(
            request_id=request_id,
            from_username=from_username,
            to_username=to_username,
            message=message,
            status=FriendRequestStatus.PENDING,
            created_at=datetime.now()
        )

        # 儲存到接收者的請求列表
        if to_username not in self.friend_requests:
            self.friend_requests[to_username] = []
        self.friend_requests[to_username].append(request)

        # 儲存到資料庫
        self._save_friend_request(request)

        logging.info(f"用戶 {from_username} 向 {to_username} 發送好友請求")
        return request_id

    def respond_friend_request(self, request_id: str, username: str, accept: bool) -> bool:
        """
        回應好友請求

        Args:
            request_id: 請求ID
            username: 回應者用戶名
            accept: 是否接受

        Returns:
            是否成功處理
        """
        # 查找請求
        request = None
        for requests in self.friend_requests.values():
            for req in requests:
                if req.request_id == request_id and req.to_username == username:
                    request = req
                    break
            if request:
                break

        if not request:
            return False

        # 更新請求狀態
        if accept:
            request.status = FriendRequestStatus.ACCEPTED
            # 建立好友關係
            self._create_friendship(request.from_username, request.to_username)
            # 發送系統訊息
            self.send_system_message(request.from_username, f"用戶 {username} 接受了你的好友請求！")
        else:
            request.status = FriendRequestStatus.DECLINED

        request.responded_at = datetime.now()

        # 更新資料庫
        self._update_friend_request(request)

        return True

    def _create_friendship(self, username1: str, username2: str):
        """建立好友關係"""
        friend = Friend(
            username1=username1,
            username2=username2,
            friendship_level=1,
            established_date=datetime.now(),
            last_interaction=datetime.now(),
            shared_achievements=[],
            mutual_friends=[]
        )

        # 添加到雙方的好友列表
        for username in [username1, username2]:
            if username not in self.friends:
                self.friends[username] = []
            self.friends[username].append(friend)

        # 儲存到資料庫
        self._save_friendship(friend)

    def get_friends_list(self, username: str) -> List[Dict[str, Any]]:
        """獲取用戶的好友列表"""
        if username not in self.friends:
            return []

        friends_list = []
        for friend in self.friends[username]:
            friend_username = friend.username2 if friend.username1 == username else friend.username1
            friends_list.append({
                'username': friend_username,
                'friendship_level': friend.friendship_level,
                'established_date': friend.established_date.isoformat(),
                'last_interaction': friend.last_interaction.isoformat(),
                'shared_achievements_count': len(friend.shared_achievements)
            })

        return friends_list

    def get_pending_requests(self, username: str) -> List[Dict[str, Any]]:
        """獲取待處理的好友請求"""
        if username not in self.friend_requests:
            return []

        return [{
            'request_id': req.request_id,
            'from_username': req.from_username,
            'message': req.message,
            'created_at': req.created_at.isoformat()
        } for req in self.friend_requests[username] if req.status == FriendRequestStatus.PENDING]

    # ===== 公會系統 =====

    def create_guild(self, leader_username: str, name: str, description: str = "",
                    max_members: int = 50) -> str:
        """
        建立公會

        Args:
            leader_username: 公會領導者
            name: 公會名稱
            description: 公會描述
            max_members: 最大成員數

        Returns:
            公會ID
        """
        guild_id = f"guild_{int(datetime.now().timestamp())}_{leader_username}"

        guild = Guild(
            guild_id=guild_id,
            name=name,
            description=description,
            leader_username=leader_username,
            members={leader_username: GuildRole.LEADER},
            max_members=max_members,
            level=1,
            experience=0,
            treasury=0.0,
            created_at=datetime.now(),
            settings={},
            achievements=[]
        )

        self.guilds[guild_id] = guild
        self.guild_events[guild_id] = []

        # 儲存到資料庫
        self._save_guild(guild)

        logging.info(f"用戶 {leader_username} 建立公會: {name}")
        return guild_id

    def join_guild(self, username: str, guild_id: str) -> bool:
        """
        加入公會

        Args:
            username: 用戶名
            guild_id: 公會ID

        Returns:
            是否成功加入
        """
        if guild_id not in self.guilds:
            return False

        guild = self.guilds[guild_id]

        if len(guild.members) >= guild.max_members:
            return False

        if username in guild.members:
            return False

        guild.members[username] = GuildRole.MEMBER

        # 儲存到資料庫
        self._save_guild_member(guild_id, username, GuildRole.MEMBER)

        # 發送加入訊息
        self.send_guild_message(guild_id, "system", f"歡迎新成員 {username} 加入公會！")

        logging.info(f"用戶 {username} 加入公會 {guild.name}")
        return True

    def leave_guild(self, username: str, guild_id: str) -> bool:
        """
        離開公會

        Args:
            username: 用戶名
            guild_id: 公會ID

        Returns:
            是否成功離開
        """
        if guild_id not in self.guilds:
            return False

        guild = self.guilds[guild_id]

        if username not in guild.members:
            return False

        # 如果是領導者，無法直接離開
        if guild.members[username] == GuildRole.LEADER:
            return False

        del guild.members[username]

        # 從資料庫刪除
        self._remove_guild_member(guild_id, username)

        # 發送離開訊息
        self.send_guild_message(guild_id, "system", f"成員 {username} 離開了公會。")

        logging.info(f"用戶 {username} 離開公會 {guild.name}")
        return True

    def get_guild_info(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """獲取公會資訊"""
        if guild_id not in self.guilds:
            return None

        guild = self.guilds[guild_id]
        return {
            'guild_id': guild.guild_id,
            'name': guild.name,
            'description': guild.description,
            'leader_username': guild.leader_username,
            'members_count': len(guild.members),
            'max_members': guild.max_members,
            'level': guild.level,
            'experience': guild.experience,
            'treasury': guild.treasury,
            'created_at': guild.created_at.isoformat(),
            'members': {username: role.value for username, role in guild.members.items()}
        }

    def get_user_guild(self, username: str) -> Optional[str]:
        """獲取用戶所在的公會"""
        for guild_id, guild in self.guilds.items():
            if username in guild.members:
                return guild_id
        return None

    def send_guild_message(self, guild_id: str, from_username: str, content: str):
        """發送公會訊息"""
        if guild_id not in self.guilds:
            return

        guild = self.guilds[guild_id]

        # 向所有公會成員發送訊息
        for member_username in guild.members.keys():
            self.send_message(from_username, member_username, content, "guild")

    # ===== 訊息系統 =====

    def send_message(self, from_username: str, to_username: str, content: str,
                    message_type: str = "friend") -> str:
        """
        發送訊息

        Args:
            from_username: 發送者
            to_username: 接收者
            content: 訊息內容
            message_type: 訊息類型

        Returns:
            訊息ID
        """
        message_id = f"msg_{int(datetime.now().timestamp())}_{from_username}_{to_username}"

        message = SocialMessage(
            message_id=message_id,
            from_username=from_username,
            to_username=to_username,
            content=content,
            message_type=message_type,
            created_at=datetime.now()
        )

        # 儲存到接收者的訊息列表
        if to_username not in self.social_messages:
            self.social_messages[to_username] = []
        self.social_messages[to_username].append(message)

        # 儲存到資料庫
        self._save_message(message)

        return message_id

    def send_system_message(self, username: str, content: str) -> str:
        """發送系統訊息"""
        return self.send_message("system", username, content, "system")

    def get_messages(self, username: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """獲取用戶的訊息"""
        if username not in self.social_messages:
            return []

        messages = self.social_messages[username]

        if unread_only:
            messages = [msg for msg in messages if not msg.is_read]

        return [{
            'message_id': msg.message_id,
            'from_username': msg.from_username,
            'content': msg.content,
            'message_type': msg.message_type,
            'created_at': msg.created_at.isoformat(),
            'is_read': msg.is_read
        } for msg in messages]

    def mark_message_read(self, username: str, message_id: str) -> bool:
        """標記訊息為已讀"""
        if username not in self.social_messages:
            return False

        for message in self.social_messages[username]:
            if message.message_id == message_id:
                message.is_read = True
                self._update_message_read_status(message_id, True)
                return True

        return False

    # ===== 排行榜系統 =====

    def create_leaderboard(self, name: str, type: str, period: str = "all_time") -> str:
        """
        建立排行榜

        Args:
            name: 排行榜名稱
            type: 排行榜類型
            period: 時間週期

        Returns:
            排行榜ID
        """
        leaderboard_id = f"leaderboard_{int(datetime.now().timestamp())}_{type}_{period}"

        leaderboard = SocialLeaderboard(
            leaderboard_id=leaderboard_id,
            name=name,
            type=type,
            period=period,
            entries=[],
            last_updated=datetime.now()
        )

        self.leaderboards[leaderboard_id] = leaderboard
        return leaderboard_id

    def update_leaderboard(self, leaderboard_id: str):
        """更新排行榜"""
        if leaderboard_id not in self.leaderboards:
            return

        leaderboard = self.leaderboards[leaderboard_id]

        # 根據排行榜類型更新資料
        if leaderboard.type == "wealth":
            entries = self._get_wealth_leaderboard_entries()
        elif leaderboard.type == "achievements":
            entries = self._get_achievements_leaderboard_entries()
        elif leaderboard.type == "social":
            entries = self._get_social_leaderboard_entries()
        else:
            entries = []

        leaderboard.entries = entries
        leaderboard.last_updated = datetime.now()

    def _get_wealth_leaderboard_entries(self) -> List[Dict[str, Any]]:
        """獲取財富排行榜項目"""
        entries = []

        # 這裡需要整合遊戲資料來計算財富
        # 簡化版本，實際實現會從 data_manager 獲取資料

        return entries

    def _get_achievements_leaderboard_entries(self) -> List[Dict[str, Any]]:
        """獲取成就排行榜項目"""
        entries = []

        # 這裡需要整合成就系統
        # 簡化版本

        return entries

    def _get_social_leaderboard_entries(self) -> List[Dict[str, Any]]:
        """獲取社交排行榜項目"""
        entries = []

        for username, stats in self.user_social_stats.items():
            entries.append({
                'username': username,
                'score': stats.get('social_score', 0),
                'friends_count': stats.get('friends_count', 0),
                'guilds_count': stats.get('guilds_joined', 0)
            })

        # 按社交分數排序
        entries.sort(key=lambda x: x['score'], reverse=True)
        return entries

    # ===== 資料庫操作方法 =====

    def _save_friend_request(self, request: FriendRequest):
        """儲存好友請求到資料庫"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR REPLACE INTO friend_requests
                (request_id, from_username, to_username, message, status, created_at, responded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                request.request_id,
                request.from_username,
                request.to_username,
                request.message,
                request.status.value,
                request.created_at.isoformat(),
                request.responded_at.isoformat() if request.responded_at else None
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"儲存好友請求失敗: {e}")

    def _update_friend_request(self, request: FriendRequest):
        """更新好友請求"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                UPDATE friend_requests
                SET status=?, responded_at=?
                WHERE request_id=?
            """, (
                request.status.value,
                request.responded_at.isoformat() if request.responded_at else None,
                request.request_id
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"更新好友請求失敗: {e}")

    def _save_friendship(self, friend: Friend):
        """儲存好友關係"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR REPLACE INTO friends
                (username1, username2, friendship_level, established_date, last_interaction)
                VALUES (?, ?, ?, ?, ?)
            """, (
                friend.username1,
                friend.username2,
                friend.friendship_level,
                friend.established_date.isoformat(),
                friend.last_interaction.isoformat()
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"儲存好友關係失敗: {e}")

    def _save_guild(self, guild: Guild):
        """儲存公會"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR REPLACE INTO guilds
                (guild_id, name, description, leader_username, max_members, level,
                 experience, treasury, created_at, settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guild.guild_id,
                guild.name,
                guild.description,
                guild.leader_username,
                guild.max_members,
                guild.level,
                guild.experience,
                guild.treasury,
                guild.created_at.isoformat(),
                json.dumps(guild.settings)
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"儲存公會失敗: {e}")

    def _save_guild_member(self, guild_id: str, username: str, role: GuildRole):
        """儲存公會成員"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT OR REPLACE INTO guild_members
                (guild_id, username, role)
                VALUES (?, ?, ?)
            """, (guild_id, username, role.value))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"儲存公會成員失敗: {e}")

    def _remove_guild_member(self, guild_id: str, username: str):
        """移除公會成員"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                DELETE FROM guild_members
                WHERE guild_id=? AND username=?
            """, (guild_id, username))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"移除公會成員失敗: {e}")

    def _save_message(self, message: SocialMessage):
        """儲存訊息"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO social_messages
                (message_id, from_username, to_username, content, message_type, created_at, is_read)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message.message_id,
                message.from_username,
                message.to_username,
                message.content,
                message.message_type,
                message.created_at.isoformat(),
                message.is_read
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"儲存訊息失敗: {e}")

    def _update_message_read_status(self, message_id: str, is_read: bool):
        """更新訊息已讀狀態"""
        if not self.db_path:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                UPDATE social_messages
                SET is_read=?
                WHERE message_id=?
            """, (is_read, message_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"更新訊息狀態失敗: {e}")
