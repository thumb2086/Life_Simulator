"""
Life Simulator Server - 社交功能模組
處理好友、公會、訊息和社交互動
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from fastapi import HTTPException
from pydantic import BaseModel


@dataclass
class Friend:
    """好友資訊"""
    username: str
    friend_username: str
    added_at: datetime
    status: str  # active, blocked


@dataclass
class FriendRequest:
    """好友請求"""
    request_id: str
    from_username: str
    to_username: str
    message: str
    status: str  # pending, accepted, rejected
    created_at: datetime


@dataclass
class Guild:
    """公會資訊"""
    guild_id: str
    name: str
    description: str
    leader_username: str
    created_at: datetime
    max_members: int
    level: int
    experience: int


@dataclass
class GuildMember:
    """公會成員"""
    guild_id: str
    username: str
    role: str  # leader, officer, member
    joined_at: datetime
    contribution: int


@dataclass
class Message:
    """訊息"""
    message_id: str
    from_username: str
    to_username: str
    content: str
    message_type: str  # friend, guild, system
    sent_at: datetime
    is_read: bool


class FriendRequestPayload(BaseModel):
    """好友請求載荷"""
    from_username: str
    to_username: str
    message: Optional[str] = ""


class FriendResponsePayload(BaseModel):
    """好友回應載荷"""
    request_id: str
    username: str
    accept: bool


class GuildCreationPayload(BaseModel):
    """公會創建載荷"""
    leader_username: str
    name: str
    description: Optional[str] = ""
    max_members: Optional[int] = 50


class GuildJoinPayload(BaseModel):
    """公會加入載荷"""
    username: str
    guild_id: str


class MessagePayload(BaseModel):
    """訊息載荷"""
    from_username: str
    to_username: str
    content: str
    message_type: Optional[str] = "friend"


class SocialFeaturesManager:
    """
    社交功能管理器
    負責好友、公會、訊息等社交功能的實現
    """

    def __init__(self, data_manager, db_path: str):
        self.data_manager = data_manager
        self.db_path = db_path
        self._init_social_database()

    def _init_social_database(self):
        """初始化社交資料庫"""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 好友表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS friends (
                    username TEXT NOT NULL,
                    friend_username TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    PRIMARY KEY (username, friend_username)
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 公會表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS guilds (
                    guild_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    leader_username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    max_members INTEGER DEFAULT 50,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0
                )
            """)

            # 公會成員表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS guild_members (
                    guild_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contribution INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, username),
                    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id)
                )
            """)

            # 訊息表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    from_username TEXT NOT NULL,
                    to_username TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'friend',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE
                )
            """)

            # 社交統計表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS social_stats (
                    username TEXT PRIMARY KEY,
                    total_friends INTEGER DEFAULT 0,
                    total_messages_sent INTEGER DEFAULT 0,
                    total_messages_received INTEGER DEFAULT 0,
                    guild_joined_at TIMESTAMP,
                    social_points INTEGER DEFAULT 0,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

        finally:
            conn.close()

    def _get_db_connection(self) -> sqlite3.Connection:
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
        import uuid

        # 檢查是否已經是好友
        if self.are_friends(from_username, to_username):
            raise HTTPException(status_code=400, detail="已經是好友")

        # 檢查是否已有待處理的請求
        if self.has_pending_request(from_username, to_username):
            raise HTTPException(status_code=400, detail="已有待處理的好友請求")

        request_id = str(uuid.uuid4())

        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO friend_requests
                (request_id, from_username, to_username, message, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
            """, (request_id, from_username, to_username, message, datetime.now()))

            conn.commit()

        finally:
            conn.close()

        return request_id

    def respond_to_friend_request(self, request_id: str, username: str, accept: bool) -> bool:
        """
        回應好友請求

        Args:
            request_id: 請求ID
            username: 回應者用戶名
            accept: 是否接受

        Returns:
            操作是否成功
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 獲取請求資訊
            cur.execute("""
                SELECT from_username, to_username FROM friend_requests
                WHERE request_id = ? AND status = 'pending'
            """, (request_id,))

            request = cur.fetchone()
            if not request:
                return False

            from_username = request['from_username']
            to_username = request['to_username']

            # 驗證用戶權限
            if username != to_username:
                return False

            if accept:
                # 接受請求 - 建立雙向好友關係
                cur.execute("""
                    INSERT OR REPLACE INTO friends
                    (username, friend_username, added_at, status)
                    VALUES (?, ?, ?, 'active')
                """, (from_username, to_username, datetime.now()))

                cur.execute("""
                    INSERT OR REPLACE INTO friends
                    (username, friend_username, added_at, status)
                    VALUES (?, ?, ?, 'active')
                """, (to_username, from_username, datetime.now()))

                # 更新社交統計
                self._update_social_stats(from_username, friend_added=True)
                self._update_social_stats(to_username, friend_added=True)

            # 更新請求狀態
            cur.execute("""
                UPDATE friend_requests
                SET status = ?
                WHERE request_id = ?
            """, ('accepted' if accept else 'rejected', request_id))

            conn.commit()
            return True

        finally:
            conn.close()

    def get_friend_requests(self, username: str) -> List[Dict[str, Any]]:
        """
        獲取用戶的好友請求

        Args:
            username: 用戶名

        Returns:
            好友請求列表
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT request_id, from_username, message, created_at
                FROM friend_requests
                WHERE to_username = ? AND status = 'pending'
                ORDER BY created_at DESC
            """, (username,))

            requests = []
            for row in cur.fetchall():
                requests.append({
                    'request_id': row['request_id'],
                    'from_username': row['from_username'],
                    'message': row['message'],
                    'created_at': row['created_at']
                })

            return requests

        finally:
            conn.close()

    def get_friends_list(self, username: str) -> List[Dict[str, Any]]:
        """
        獲取好友列表

        Args:
            username: 用戶名

        Returns:
            好友列表
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT f.friend_username, f.added_at, ss.social_points
                FROM friends f
                LEFT JOIN social_stats ss ON f.friend_username = ss.username
                WHERE f.username = ? AND f.status = 'active'
                ORDER BY f.added_at DESC
            """, (username,))

            friends = []
            for row in cur.fetchall():
                friends.append({
                    'username': row['friend_username'],
                    'added_at': row['added_at'],
                    'social_points': row['social_points'] or 0
                })

            return friends

        finally:
            conn.close()

    def remove_friend(self, username: str, friend_username: str) -> bool:
        """
        移除好友

        Args:
            username: 用戶名
            friend_username: 好友用戶名

        Returns:
            操作是否成功
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 移除雙向好友關係
            cur.execute("""
                UPDATE friends
                SET status = 'removed'
                WHERE (username = ? AND friend_username = ?) OR (username = ? AND friend_username = ?)
            """, (username, friend_username, friend_username, username))

            # 更新社交統計
            self._update_social_stats(username, friend_removed=True)
            self._update_social_stats(friend_username, friend_removed=True)

            conn.commit()
            return True

        finally:
            conn.close()

    def are_friends(self, username1: str, username2: str) -> bool:
        """
        檢查兩用戶是否為好友

        Args:
            username1: 用戶名1
            username2: 用戶名2

        Returns:
            是否為好友
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT COUNT(*) FROM friends
                WHERE username = ? AND friend_username = ? AND status = 'active'
            """, (username1, username2))

            return cur.fetchone()[0] > 0

        finally:
            conn.close()

    def has_pending_request(self, from_username: str, to_username: str) -> bool:
        """
        檢查是否有待處理的好友請求

        Args:
            from_username: 發送者
            to_username: 接收者

        Returns:
            是否有待處理請求
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT COUNT(*) FROM friend_requests
                WHERE from_username = ? AND to_username = ? AND status = 'pending'
            """, (from_username, to_username))

            return cur.fetchone()[0] > 0

        finally:
            conn.close()

    # ===== 公會系統 =====

    def create_guild(self, leader_username: str, name: str, description: str = "", max_members: int = 50) -> str:
        """
        創建公會

        Args:
            leader_username: 會長用戶名
            name: 公會名稱
            description: 公會描述
            max_members: 最大成員數

        Returns:
            公會ID
        """
        import uuid

        # 檢查用戶是否已在公會中
        if self.get_user_guild(leader_username):
            raise HTTPException(status_code=400, detail="用戶已經在公會中")

        guild_id = str(uuid.uuid4())

        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 創建公會
            cur.execute("""
                INSERT INTO guilds
                (guild_id, name, description, leader_username, created_at, max_members, level, experience)
                VALUES (?, ?, ?, ?, ?, ?, 1, 0)
            """, (guild_id, name, description, leader_username, datetime.now(), max_members))

            # 將創建者加入公會
            cur.execute("""
                INSERT INTO guild_members
                (guild_id, username, role, joined_at, contribution)
                VALUES (?, ?, 'leader', ?, 100)
            """, (guild_id, leader_username, datetime.now()))

            # 更新社交統計
            self._update_social_stats(leader_username, guild_created=True)

            conn.commit()

        finally:
            conn.close()

        return guild_id

    def join_guild(self, username: str, guild_id: str) -> bool:
        """
        加入公會

        Args:
            username: 用戶名
            guild_id: 公會ID

        Returns:
            操作是否成功
        """
        # 檢查用戶是否已在公會中
        if self.get_user_guild(username):
            raise HTTPException(status_code=400, detail="用戶已經在公會中")

        # 檢查公會是否存在且未滿員
        guild = self.get_guild_info(guild_id)
        if not guild:
            raise HTTPException(status_code=404, detail="公會不存在")

        if guild['member_count'] >= guild['max_members']:
            raise HTTPException(status_code=400, detail="公會已滿員")

        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 加入公會
            cur.execute("""
                INSERT INTO guild_members
                (guild_id, username, role, joined_at, contribution)
                VALUES (?, ?, 'member', ?, 0)
            """, (guild_id, username, datetime.now()))

            # 更新社交統計
            self._update_social_stats(username, guild_joined=True)

            conn.commit()
            return True

        finally:
            conn.close()

    def leave_guild(self, username: str) -> bool:
        """
        離開公會

        Args:
            username: 用戶名

        Returns:
            操作是否成功
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 檢查是否為會長
            cur.execute("""
                SELECT g.leader_username, gm.guild_id
                FROM guild_members gm
                JOIN guilds g ON gm.guild_id = g.guild_id
                WHERE gm.username = ?
            """, (username,))

            result = cur.fetchone()
            if result and result['leader_username'] == username:
                raise HTTPException(status_code=400, detail="會長不能離開公會")

            # 移除會員
            cur.execute("""
                DELETE FROM guild_members
                WHERE username = ?
            """, (username,))

            # 更新社交統計
            self._update_social_stats(username, guild_left=True)

            conn.commit()
            return True

        finally:
            conn.close()

    def get_guild_info(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取公會資訊

        Args:
            guild_id: 公會ID

        Returns:
            公會資訊
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 獲取公會基本資訊
            cur.execute("""
                SELECT g.*, COUNT(gm.username) as member_count
                FROM guilds g
                LEFT JOIN guild_members gm ON g.guild_id = gm.guild_id
                WHERE g.guild_id = ?
                GROUP BY g.guild_id
            """, (guild_id,))

            row = cur.fetchone()
            if not row:
                return None

            return {
                'guild_id': row['guild_id'],
                'name': row['name'],
                'description': row['description'],
                'leader_username': row['leader_username'],
                'created_at': row['created_at'],
                'max_members': row['max_members'],
                'level': row['level'],
                'experience': row['experience'],
                'member_count': row['member_count']
            }

        finally:
            conn.close()

    def get_guild_members(self, guild_id: str) -> List[Dict[str, Any]]:
        """
        獲取公會成員列表

        Args:
            guild_id: 公會ID

        Returns:
            成員列表
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT gm.username, gm.role, gm.joined_at, gm.contribution, ss.social_points
                FROM guild_members gm
                LEFT JOIN social_stats ss ON gm.username = ss.username
                WHERE gm.guild_id = ?
                ORDER BY gm.role DESC, gm.contribution DESC
            """, (guild_id,))

            members = []
            for row in cur.fetchall():
                members.append({
                    'username': row['username'],
                    'role': row['role'],
                    'joined_at': row['joined_at'],
                    'contribution': row['contribution'],
                    'social_points': row['social_points'] or 0
                })

            return members

        finally:
            conn.close()

    def get_user_guild(self, username: str) -> Optional[Dict[str, Any]]:
        """
        獲取用戶的公會資訊

        Args:
            username: 用戶名

        Returns:
            公會資訊
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT g.*, gm.role, gm.contribution
                FROM guilds g
                JOIN guild_members gm ON g.guild_id = gm.guild_id
                WHERE gm.username = ?
            """, (username,))

            row = cur.fetchone()
            if not row:
                return None

            return {
                'guild_id': row['guild_id'],
                'name': row['name'],
                'role': row['role'],
                'contribution': row['contribution'],
                'level': row['level'],
                'experience': row['experience']
            }

        finally:
            conn.close()

    # ===== 訊息系統 =====

    def send_message(self, from_username: str, to_username: str, content: str, message_type: str = "friend") -> str:
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
        import uuid

        message_id = str(uuid.uuid4())

        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO messages
                (message_id, from_username, to_username, content, message_type, sent_at, is_read)
                VALUES (?, ?, ?, ?, ?, ?, FALSE)
            """, (message_id, from_username, to_username, content, message_type, datetime.now()))

            # 更新社交統計
            self._update_social_stats(from_username, message_sent=True)

            conn.commit()

        finally:
            conn.close()

        return message_id

    def get_messages(self, username: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        獲取用戶訊息

        Args:
            username: 用戶名
            unread_only: 是否只獲取未讀訊息

        Returns:
            訊息列表
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            query = """
                SELECT message_id, from_username, content, message_type, sent_at, is_read
                FROM messages
                WHERE to_username = ?
            """
            params = [username]

            if unread_only:
                query += " AND is_read = FALSE"

            query += " ORDER BY sent_at DESC"

            cur.execute(query, params)

            messages = []
            for row in cur.fetchall():
                messages.append({
                    'message_id': row['message_id'],
                    'from_username': row['from_username'],
                    'content': row['content'],
                    'message_type': row['message_type'],
                    'sent_at': row['sent_at'],
                    'is_read': bool(row['is_read'])
                })

            return messages

        finally:
            conn.close()

    def mark_message_as_read(self, username: str, message_id: str) -> bool:
        """
        標記訊息為已讀

        Args:
            username: 用戶名
            message_id: 訊息ID

        Returns:
            操作是否成功
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("""
                UPDATE messages
                SET is_read = TRUE
                WHERE message_id = ? AND to_username = ?
            """, (message_id, username))

            conn.commit()
            return cur.rowcount > 0

        finally:
            conn.close()

    def get_social_stats(self, username: str) -> Dict[str, Any]:
        """
        獲取用戶社交統計

        Args:
            username: 用戶名

        Returns:
            社交統計資料
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 獲取或建立統計記錄
            cur.execute("""
                SELECT * FROM social_stats WHERE username = ?
            """, (username,))

            row = cur.fetchone()
            if not row:
                # 建立新記錄
                cur.execute("""
                    INSERT INTO social_stats (username) VALUES (?)
                """, (username,))
                conn.commit()

                return {
                    'username': username,
                    'total_friends': 0,
                    'total_messages_sent': 0,
                    'total_messages_received': 0,
                    'guild_joined_at': None,
                    'social_points': 0,
                    'last_activity': datetime.now().isoformat()
                }

            return {
                'username': row['username'],
                'total_friends': row['total_friends'],
                'total_messages_sent': row['total_messages_sent'],
                'total_messages_received': row['total_messages_received'],
                'guild_joined_at': row['guild_joined_at'],
                'social_points': row['social_points'],
                'last_activity': row['last_activity']
            }

        finally:
            conn.close()

    def _update_social_stats(self, username: str, friend_added: bool = False, friend_removed: bool = False,
                           message_sent: bool = False, guild_created: bool = False,
                           guild_joined: bool = False, guild_left: bool = False):
        """
        更新社交統計

        Args:
            username: 用戶名
            friend_added: 是否新增好友
            friend_removed: 是否移除好友
            message_sent: 是否發送訊息
            guild_created: 是否創建公會
            guild_joined: 是否加入公會
            guild_left: 是否離開公會
        """
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # 獲取當前統計
            cur.execute("SELECT * FROM social_stats WHERE username = ?", (username,))
            row = cur.fetchone()

            if row:
                total_friends = row['total_friends']
                total_messages_sent = row['total_messages_sent']
                social_points = row['social_points']
                guild_joined_at = row['guild_joined_at']

                # 更新統計
                if friend_added:
                    total_friends += 1
                    social_points += 10
                elif friend_removed:
                    total_friends -= 1
                    social_points -= 5

                if message_sent:
                    total_messages_sent += 1
                    social_points += 1

                if guild_created:
                    social_points += 50

                if guild_joined and not guild_joined_at:
                    guild_joined_at = datetime.now()
                    social_points += 25

                if guild_left:
                    social_points -= 10

                cur.execute("""
                    UPDATE social_stats
                    SET total_friends = ?, total_messages_sent = ?, social_points = ?,
                        guild_joined_at = ?, last_activity = ?
                    WHERE username = ?
                """, (total_friends, total_messages_sent, social_points, guild_joined_at,
                      datetime.now(), username))

            else:
                # 建立新記錄
                total_friends = 1 if friend_added else 0
                total_messages_sent = 1 if message_sent else 0
                social_points = 10 if friend_added else 1 if message_sent else 0
                guild_joined_at = datetime.now() if guild_joined else None

                cur.execute("""
                    INSERT INTO social_stats
                    (username, total_friends, total_messages_sent, social_points, guild_joined_at, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, total_friends, total_messages_sent, social_points, guild_joined_at, datetime.now()))

            conn.commit()

        finally:
            conn.close()
