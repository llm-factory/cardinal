import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from ..storage import AutoStorage  # 根据你的项目结构调整导入路径

class ChatMessage(BaseModel):
    """聊天消息数据模型"""
    user: str = Field(..., description="用户消息")
    bot: str = Field(..., description="机器人回复")
    timestamp: str = Field(..., description="消息时间戳")

class ChatSession(BaseModel):
    """聊天会话数据模型"""
    session_id: str = Field(..., description="会话唯一标识")
    title: str = Field(..., description="会话标题")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="最后更新时间")
    messages: List[ChatMessage] = Field(default_factory=list, description="消息列表")
    is_active: bool = Field(default=False, description="是否为活跃会话")

class ChatCollector:
    """聊天记录收集器"""
    
    def __init__(self, name: str = "default"):
        """
        初始化聊天收集器
        
        Args:
            name: 收集器名称，用于区分不同的用户或实例
        """
        self.name = name
        self.storage = AutoStorage[BaseModel]("chat_history")  # 固定使用chat_history索引
        self.current_session_id: Optional[str] = None
        # 用于存储会话列表的键
        self.sessions_list_key = f"{self.name}:sessions_list"
        self._initialize()
    
    def _initialize(self):
        """初始化收集器，加载上次活跃会话或创建新会话"""
        # 尝试加载上次的活跃会话
        last_active_session = self._get_last_active_session()
        
        if last_active_session:
            self.current_session_id = last_active_session.session_id
            print(f"已加载上次活跃会话: {last_active_session.title}")
        else:
            # 如果没有活跃会话，创建一个新的
            session_id = self.create_session("New Chat")  # 使用默认标题
            print(f"已创建首次聊天会话: {session_id}")
    
    def _get_sessions_list(self) -> List[str]:
        """获取会话ID列表"""
        try:
            data = self.storage.query(self.sessions_list_key)
            if data and isinstance(data, list):
                return data
        except Exception as e:
            print(f"获取会话列表失败: {e}")
        return []
    
    def _save_sessions_list(self, session_ids: List[str]):
        """保存会话ID列表"""
        try:
            self.storage.insert([self.sessions_list_key], [session_ids])
        except Exception as e:
            print(f"保存会话列表失败: {e}")
    
    def _add_session_to_list(self, session_id: str):
        """添加会话ID到列表"""
        session_ids = self._get_sessions_list()
        if session_id not in session_ids:
            session_ids.append(session_id)
            self._save_sessions_list(session_ids)
    
    def _remove_session_from_list(self, session_id: str):
        """从列表中移除会话ID"""
        session_ids = self._get_sessions_list()
        if session_id in session_ids:
            session_ids.remove(session_id)
            self._save_sessions_list(session_ids)
    
    def _get_last_active_session(self) -> Optional[ChatSession]:
        """获取上次活跃的会话"""
        try:
            session_ids = self._get_sessions_list()
            for session_id in session_ids:
                session = self.get_session(session_id)
                if session and session.is_active:
                    return session
        except Exception as e:
            print(f"获取活跃会话失败: {e}")
        return None
    
    def _set_session_active(self, session_id: str, active: bool = True):
        """设置会话的活跃状态"""
        try:
            session = self.get_session(session_id)
            if session:
                session.is_active = active
                session.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_session(session)
        except Exception as e:
            print(f"设置会话活跃状态失败: {e}")
    
    def _clear_all_active_sessions(self):
        """清除所有活跃会话状态"""
        try:
            session_ids = self._get_sessions_list()
            for session_id in session_ids:
                session = self.get_session(session_id)
                if session and session.is_active:
                    session.is_active = False
                    self._save_session(session)
        except Exception as e:
            print(f"清除活跃会话状态失败: {e}")
    
    def _save_session(self, session: ChatSession):
        """保存会话到存储"""
        key = f"{self.name}:{session.session_id}"
        self.storage.insert([key], [session.model_dump()])
    
    def _generate_session_key(self, session_id: str) -> str:
        """生成会话存储键"""
        return f"{self.name}:{session_id}"
    
    def generate_session_title(self, first_message: str, max_length: int = 20) -> str:
        """
        根据第一条消息生成会话标题
        
        Args:
            first_message: 第一条用户消息
            max_length: 标题最大长度
            
        Returns:
            生成的标题
        """
        if not first_message:
            return "New Chat"
        
        # 清理消息内容
        message = first_message.strip()
        
        # 如果消息太长，截取前面部分
        if len(message) > max_length:
            message = message[:max_length] + "..."
        
        # 移除换行符和多余空格
        message = " ".join(message.split())
        
        # 如果消息为空或只有标点符号，使用默认标题
        if not message or message.replace(" ", "").replace(".", "").replace("?", "").replace("!", "") == "":
            return "New Chat"
        
        return message
    
    def create_session(self, title: Optional[str] = None) -> str:
        """
        创建新的聊天会话
        
        Args:
            title: 会话标题，如果为None则自动生成
            
        Returns:
            新会话的ID
        """
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if title is None:
            title = f"聊天 - {timestamp}"
        
        # 清除其他会话的活跃状态
        self._clear_all_active_sessions()
        
        session = ChatSession(
            session_id=session_id,
            title=title,
            created_at=timestamp,
            updated_at=timestamp,
            messages=[],
            is_active=True
        )
        
        # 保存到存储
        self._save_session(session)
        # 添加到会话列表
        self._add_session_to_list(session_id)
        self.current_session_id = session_id
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        获取指定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象，如果不存在返回None
        """
        try:
            key = self._generate_session_key(session_id)
            data = self.storage.query(key)
            if data:
                return ChatSession(**data)
        except Exception as e:
            print(f"获取会话失败 {session_id}: {e}")
        return None
    
    def list_sessions(self) -> List[Dict[str, str]]:
        """
        获取当前用户的所有会话列表
        
        Returns:
            会话列表，每个元素包含session_id, title, created_at, is_active
        """
        sessions = []
        try:
            session_ids = self._get_sessions_list()
            
            for session_id in session_ids:
                session = self.get_session(session_id)
                if session:
                    sessions.append({
                        "session_id": session.session_id,
                        "title": session.title,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at,
                        "is_active": session.is_active,
                        "message_count": len(session.messages)
                    })
        except Exception as e:
            print(f"获取会话列表失败: {e}")
            
        # 按更新时间倒序排列，活跃会话优先
        sessions.sort(key=lambda x: (x["is_active"], x["updated_at"]), reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除指定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            key = self._generate_session_key(session_id)
            self.storage.delete(key)
            # 从会话列表中移除
            self._remove_session_from_list(session_id)
            
            # 如果删除的是当前会话，需要重新设置当前会话
            if self.current_session_id == session_id:
                self.current_session_id = None
                # 尝试设置另一个会话为活跃会话
                sessions = self.list_sessions()
                if sessions:
                    self.set_current_session(sessions[0]["session_id"])
                else:
                    # 如果没有其他会话，创建一个新的
                    self.create_session("New Chat")
            
            return True
        except Exception as e:
            print(f"删除会话失败 {session_id}: {e}")
            return False
    
    def add_message(self, session_id: str, user_message: str, bot_message: str) -> bool:
        """
        向指定会话添加消息
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            bot_message: 机器人回复
            
        Returns:
            是否添加成功
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # 添加新消息
        message = ChatMessage(
            user=user_message,
            bot=bot_message,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.messages.append(message)
        session.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存会话
        try:
            self._save_session(session)
            return True
        except Exception as e:
            print(f"添加消息失败 {session_id}: {e}")
            return False
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, str]]:
        """
        获取会话的所有消息，转换为Gradio格式
        
        Args:
            session_id: 会话ID
            
        Returns:
            Gradio消息格式的列表
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = []
        for msg in session.messages:
            messages.append({"role": "user", "content": msg.user})
            messages.append({"role": "assistant", "content": msg.bot})
        
        return messages
    
    def set_current_session(self, session_id: str) -> bool:
        """
        设置当前会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否设置成功
        """
        session = self.get_session(session_id)
        if session:
            # 清除其他会话的活跃状态
            self._clear_all_active_sessions()
            
            # 设置当前会话为活跃
            self._set_session_active(session_id, True)
            self.current_session_id = session_id
            return True
        return False
    
    def get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID"""
        return self.current_session_id
    
    def get_current_session(self) -> Optional[ChatSession]:
        """获取当前会话对象"""
        if self.current_session_id:
            return self.get_session(self.current_session_id)
        return None
    
    def save_current_conversation(self, messages: List[Dict[str, str]]) -> bool:
        """
        保存当前对话到当前会话
        
        Args:
            messages: Gradio格式的消息列表
            
        Returns:
            是否保存成功
        """
        if not self.current_session_id:
            # 如果没有当前会话，创建一个新的
            self.create_session()
        
        if not self.current_session_id:
            return False
        
        # 获取当前会话
        session = self.get_session(self.current_session_id)
        if not session:
            return False
        
        # 清空现有消息并重新添加
        session.messages = []
        
        # 转换Gradio格式的消息
        user_msg = None
        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
            elif msg["role"] == "assistant" and user_msg:
                message = ChatMessage(
                    user=user_msg,
                    bot=msg["content"],
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                session.messages.append(message)
                user_msg = None
        
        session.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存到存储
        try:
            self._save_session(session)
            return True
        except Exception as e:
            print(f"保存对话失败: {e}")
            return False
    
    def update_session_title(self, session_id: str, new_title: str) -> bool:
        """
        更新会话标题
        
        Args:
            session_id: 会话ID
            new_title: 新标题
            
        Returns:
            是否更新成功
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.title = new_title
        session.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self._save_session(session)
            return True
        except Exception as e:
            print(f"更新会话标题失败: {e}")
            return False
    
    def get_session_count(self) -> int:
        """获取当前用户的会话总数"""
        try:
            sessions = self.list_sessions()
            return len(sessions)
        except:
            return 0
    
    def clear_all_sessions(self) -> bool:
        """清空当前用户的所有会话"""
        try:
            session_ids = self._get_sessions_list()
            for session_id in session_ids:
                key = self._generate_session_key(session_id)
                self.storage.delete(key)
            
            # 清空会话列表
            self._save_sessions_list([])
            
            self.current_session_id = None
            # 创建一个新的默认会话
            self.create_session("New Chat")
            return True
        except Exception as e:
            print(f"清空所有会话失败: {e}")
            return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        sessions = self.list_sessions()
        total_messages = sum(session.get("message_count", 0) for session in sessions)
        
        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "current_session_id": self.current_session_id,
            "active_sessions": len([s for s in sessions if s.get("is_active", False)])
        }
