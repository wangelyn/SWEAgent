from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from pydantic import Field, model_validator

from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.logger import logger
from app.schema import Message, AgentState
from app.tool import (
    Bash,
    StrReplaceEditor,
    PythonExecute,
    AskHuman,
    Terminate,
    ToolCollection
)
from app.tool.conversation_swe_tools import (
    ConversationalCodeReview,
    ProjectProgressTracker,
    RequirementClarifier
)


class ConversationalSWEAgent(ToolCallAgent):
    """
    一个专注于多轮对话的软件开发智能体

    特色功能：
    1. 对话历史感知：理解开发过程中的上下文
    2. 渐进式开发：支持分步骤、多轮次的开发过程
    3. 智能提问：主动向用户询问需求细节
    4. 会话记忆：记住开发过程中的决策和偏好
    5. 代码审查对话：支持代码review的互动过程
    """

    name: str = "ConversationalSWE"
    description: str = "专注于多轮对话的软件开发智能体，支持渐进式开发和智能交互"

    # 系统提示词将在后面定义
    system_prompt: str = ""
    next_step_prompt: str = ""

        # 开发工具集
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Bash(),
            StrReplaceEditor(),
            PythonExecute(),
            AskHuman(),
            ConversationalCodeReview(),
            ProjectProgressTracker(),
            RequirementClarifier(),
            Terminate()
        )
    )
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])

    # 对话上下文管理
    conversation_context: Dict[str, Any] = Field(default_factory=dict)
    development_history: List[Dict[str, Any]] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)

    # 执行控制
    max_steps: int = 50  # 更长的对话轮数
    max_conversation_turns: int = 20
    current_conversation_turn: int = 0

    # 对话状态
    waiting_for_user_input: bool = False
    last_question_asked: Optional[str] = None
    pending_clarifications: List[str] = Field(default_factory=list)

    # 会话持久化
    session_id: Optional[str] = None
    session_file: Optional[str] = None
    auto_save: bool = True

    @model_validator(mode="after")
    def setup_prompts(self) -> "ConversationalSWEAgent":
        """初始化提示词和会话"""
        self.system_prompt = self._build_system_prompt()
        self.next_step_prompt = self._build_next_step_prompt()

        # 初始化会话
        if not self.session_id:
            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if not self.session_file:
            self.session_file = f"conversations/{self.session_id}.json"

        return self

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""你是ConversationalSWE，一个专注于多轮对话的软件开发智能体。

核心特点：
1. **对话驱动开发**：通过自然对话理解用户需求，渐进式完成开发任务
2. **智能提问**：当需求不明确时，主动询问用户获取更多信息
3. **上下文感知**：记住对话历史，理解开发过程中的上下文
4. **渐进式交付**：将复杂任务分解为多个步骤，每步都与用户确认

工作目录：{config.workspace_root}

工作方式：
- 仔细理解用户的开发需求
- 如果需求不明确，主动提问澄清
- 将大型任务分解为小步骤
- 每个关键步骤完成后，总结进展并询问用户意见
- 根据用户反馈调整开发方向
- 支持代码审查和迭代优化

对话原则：
- 使用简洁、友好的中文交流
- 主动解释技术决策的原因
- 在执行重要操作前征求用户同意
- 记住用户的编程偏好和项目要求
"""

    def _build_next_step_prompt(self) -> str:
        """构建下一步提示词"""
        context_info = self._get_conversation_context_summary()

        base_prompt = """
基于当前对话上下文和开发进展，选择最合适的下一步行动：

1. 如果用户需求不明确，使用 `ask_human` 工具提问澄清
2. 如果需要执行代码或命令，使用相应的工具
3. 如果需要编辑文件，使用 `str_replace_editor` 工具
4. 如果当前步骤完成，总结进展并询问用户下一步计划
5. 如果任务全部完成，使用 `terminate` 工具结束

记住：
- 保持对话的连贯性和上下文感知
- 每次重要操作前都要解释你的思路
- 优先确保用户理解和同意你的方案"""

        if context_info:
            return f"{base_prompt}\n\n当前上下文：\n{context_info}"

        return base_prompt

    def _get_conversation_context_summary(self) -> str:
        """获取对话上下文摘要"""
        context_parts = []

        if self.conversation_context:
            context_parts.append(f"项目背景：{self.conversation_context}")

        if self.development_history:
            recent_history = self.development_history[-3:]  # 最近3个操作
            history_summary = "\n".join([
                f"- {item.get('timestamp', '')}: {item.get('action', '')}"
                for item in recent_history
            ])
            context_parts.append(f"最近操作：\n{history_summary}")

        if self.pending_clarifications:
            context_parts.append(f"待澄清问题：{', '.join(self.pending_clarifications)}")

        return "\n\n".join(context_parts) if context_parts else ""

    def update_conversation_context(self, key: str, value: Any) -> None:
        """更新对话上下文"""
        self.conversation_context[key] = value
        logger.info(f"📝 更新对话上下文: {key} = {value}")

    def add_development_record(self, action: str, details: str = "", result: str = "") -> None:
        """添加开发历史记录"""
        record = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": action,
            "details": details,
            "result": result,
            "conversation_turn": self.current_conversation_turn
        }
        self.development_history.append(record)
        logger.info(f"📚 记录开发历史: {action}")

    def add_pending_clarification(self, question: str) -> None:
        """添加待澄清的问题"""
        self.pending_clarifications.append(question)
        logger.info(f"❓ 添加待澄清问题: {question}")

    def clear_pending_clarifications(self) -> None:
        """清除待澄清问题"""
        self.pending_clarifications.clear()
        logger.info("✅ 清除所有待澄清问题")

    async def think(self) -> bool:
        """增强的思考过程，加入对话上下文"""
        # 更新对话轮次
        self.current_conversation_turn += 1

        # 检查是否超过最大对话轮数
        if self.current_conversation_turn > self.max_conversation_turns:
            logger.warning("⚠️ 达到最大对话轮数，建议总结当前进展")
            self.update_memory(
                "system",
                "已达到最大对话轮数，请总结当前开发进展并询问用户是否继续"
            )

        # 动态更新next_step_prompt以包含最新上下文
        self.next_step_prompt = self._build_next_step_prompt()

        # 调用父类的think方法
        result = await super().think()

        return result

    async def act(self) -> str:
        """增强的行动过程，记录开发历史"""
        # 执行工具调用
        result = await super().act()

        # 记录本轮操作
        if self.tool_calls:
            for tool_call in self.tool_calls:
                self.add_development_record(
                    action=f"执行工具: {tool_call.function.name}",
                    details=tool_call.function.arguments,
                    result=result[:200] + "..." if len(result) > 200 else result
                )

        return result

    async def handle_user_response(self, user_input: str) -> None:
        """处理用户回复"""
        self.waiting_for_user_input = False
        self.last_question_asked = None

        # 将用户回复加入记忆
        self.update_memory("user", user_input)

        # 尝试从用户回复中提取偏好设置
        self._extract_user_preferences(user_input)

        logger.info(f"👤 收到用户回复: {user_input[:100]}...")

    def _extract_user_preferences(self, user_input: str) -> None:
        """从用户输入中提取偏好设置"""
        # 简单的偏好提取逻辑，可以扩展
        preferences_keywords = {
            "python版本": ["python3.8", "python3.9", "python3.10", "python3.11"],
            "代码风格": ["pep8", "black", "flake8"],
            "测试框架": ["pytest", "unittest", "nose"],
            "包管理": ["pip", "poetry", "conda"]
        }

        for pref_type, keywords in preferences_keywords.items():
            for keyword in keywords:
                if keyword.lower() in user_input.lower():
                    self.user_preferences[pref_type] = keyword
                    logger.info(f"🎯 检测到用户偏好: {pref_type} = {keyword}")

    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        summary_parts = [
            f"=== 对话摘要 ===",
            f"对话轮次: {self.current_conversation_turn}",
            f"执行步骤: {self.current_step}",
        ]

        if self.conversation_context:
            summary_parts.append(f"项目背景: {self.conversation_context}")

        if self.user_preferences:
            prefs = ", ".join([f"{k}:{v}" for k, v in self.user_preferences.items()])
            summary_parts.append(f"用户偏好: {prefs}")

        if self.development_history:
            summary_parts.append(f"完成操作: {len(self.development_history)}个")

        return "\n".join(summary_parts)

    async def cleanup(self):
        """清理资源并保存会话"""
        # 记录会话结束
        self.add_development_record(
            action="会话结束",
            details=f"总对话轮次: {self.current_conversation_turn}, 总执行步骤: {self.current_step}"
        )

        # 输出会话摘要
        logger.info("📊 " + self.get_conversation_summary())

        # 保存会话
        if self.auto_save:
            await self.save_session()

        # 调用父类清理
        await super().cleanup()

    async def save_session(self) -> None:
        """保存会话到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)

            session_data = {
                "session_id": self.session_id,
                "created_at": datetime.now().isoformat(),
                "conversation_context": self.conversation_context,
                "development_history": self.development_history,
                "user_preferences": self.user_preferences,
                "conversation_summary": self.get_conversation_summary(),
                "messages": [msg.to_dict() for msg in self.messages],
                "current_step": self.current_step,
                "current_conversation_turn": self.current_conversation_turn
            }

            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 会话已保存: {self.session_file}")

        except Exception as e:
            logger.error(f"❌ 保存会话失败: {e}")

    async def load_session(self, session_file: str) -> bool:
        """从文件加载会话"""
        try:
            if not os.path.exists(session_file):
                logger.warning(f"⚠️ 会话文件不存在: {session_file}")
                return False

            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # 恢复会话数据
            self.session_id = session_data.get("session_id")
            self.session_file = session_file
            self.conversation_context = session_data.get("conversation_context", {})
            self.development_history = session_data.get("development_history", [])
            self.user_preferences = session_data.get("user_preferences", {})
            self.current_step = session_data.get("current_step", 0)
            self.current_conversation_turn = session_data.get("current_conversation_turn", 0)

            # 恢复消息历史
            if "messages" in session_data:
                from app.schema import Message
                self.memory.messages = [
                    Message(**msg_data) for msg_data in session_data["messages"]
                ]

            logger.info(f"📂 会话已加载: {session_file}")
            logger.info(f"📊 恢复状态: 步骤{self.current_step}, 对话轮次{self.current_conversation_turn}")

            return True

        except Exception as e:
            logger.error(f"❌ 加载会话失败: {e}")
            return False

    def list_saved_sessions(self) -> List[Dict[str, Any]]:
        """列出保存的会话"""
        sessions = []
        conversations_dir = "conversations"

        if not os.path.exists(conversations_dir):
            return sessions

        try:
            for filename in os.listdir(conversations_dir):
                if filename.endswith('.json'):
                    session_path = os.path.join(conversations_dir, filename)
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)

                        sessions.append({
                            "session_id": session_data.get("session_id"),
                            "file_path": session_path,
                            "created_at": session_data.get("created_at"),
                            "conversation_turns": session_data.get("current_conversation_turn", 0),
                            "steps": session_data.get("current_step", 0),
                            "summary": session_data.get("conversation_summary", "")
                        })
                    except:
                        continue

            # 按创建时间排序
            sessions.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            logger.error(f"❌ 列出会话失败: {e}")

        return sessions

    async def start_new_conversation(self, user_input: str) -> str:
        """开始新的对话"""
        # 清理之前的状态
        self.conversation_context.clear()
        self.development_history.clear()
        self.pending_clarifications.clear()
        self.current_step = 0
        self.current_conversation_turn = 0
        self.memory.clear()

        # 生成新的会话ID
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_file = f"conversations/{self.session_id}.json"

        logger.info(f"🆕 开始新对话: {self.session_id}")

        # 处理初始用户输入
        return await self.run(user_input)
