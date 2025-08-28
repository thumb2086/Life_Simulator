"""
Life Simulator Server - 認證系統模組
處理用戶登入、權限驗證和會話管理
"""

import secrets
from typing import Dict, Optional
from fastapi import HTTPException, Header
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """登入請求模型"""
    username: str


class AuthManager:
    """
    認證管理器
    負責用戶認證、權杖管理和會話處理
    """

    def __init__(self, api_key: str = "dev-local-key"):
        self.api_key = api_key
        self.tokens: Dict[str, str] = {}

    def require_api_key(self, x_api_key: Optional[str] = Header(default=None)) -> None:
        """驗證API金鑰"""
        if x_api_key != self.api_key:
            raise HTTPException(status_code=401, detail="無效的API金鑰")

    def authenticate_user(self, username: str) -> str:
        """
        認證用戶並生成權杖

        Args:
            username: 用戶名

        Returns:
            訪問權杖
        """
        username = username.strip()
        if not username:
            raise HTTPException(status_code=400, detail="用戶名不能為空")

        # 生成權杖
        token = secrets.token_hex(16)
        self.tokens[token] = username

        return token

    def get_username_by_token(self, token: str) -> str:
        """通過權杖獲取用戶名"""
        username = self.tokens.get(token)
        if not username:
            raise HTTPException(status_code=401, detail="無效的權杖")
        return username

    def logout_user(self, token: str) -> bool:
        """用戶登出"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False

    def validate_token(self, token: str) -> bool:
        """驗證權杖是否有效"""
        return token in self.tokens

    def get_active_sessions_count(self) -> int:
        """獲取活躍會話數量"""
        return len(self.tokens)

    def get_all_active_users(self) -> list:
        """獲取所有活躍用戶"""
        return list(set(self.tokens.values()))
