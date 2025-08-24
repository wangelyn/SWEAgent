# 对话式软件开发智能体 (ConversationalSWE)

基于OpenManus框架开发的专注于**多轮对话**的软件开发智能体，通过自然语言交互完成复杂的软件开发任务。

## 🎯 核心特性

### 1. 对话驱动开发
- **智能需求分析**: 自动分析用户需求，识别关键技术点和功能模块
- **主动提问澄清**: 当需求不明确时，智能生成澄清问题
- **渐进式开发**: 将复杂任务分解为多个步骤，逐步完成

### 2. 上下文感知
- **对话历史记忆**: 记住整个开发过程中的决策和上下文
- **用户偏好学习**: 自动识别并记住用户的技术偏好
- **开发历史追踪**: 完整记录每个开发步骤和结果

### 3. 专业开发工具
- **对话式代码审查**: 分析代码质量并提出改进建议
- **项目进度跟踪**: 管理开发里程碑和任务进度
- **需求澄清工具**: 智能分析需求并生成澄清问题

### 4. 会话持久化
- **自动保存**: 对话过程自动保存到本地文件
- **会话恢复**: 支持加载之前的开发会话继续工作
- **多会话管理**: 可以管理多个并行的开发项目

## 🚀 快速开始

### 安装和配置

1. 确保已安装OpenManus项目的基础环境
2. 将ConversationalSWE相关文件添加到项目中：
   ```
   app/agent/conversational_swe.py
   app/tool/conversation_swe_tools.py
   run_conversational_swe.py
   ```

### 基本使用

#### 1. 开始新的开发对话
```bash
python run_conversational_swe.py
```

#### 2. 直接指定开发需求
```bash
python run_conversational_swe.py --prompt "开发一个Python爬虫程序"
```

#### 3. 选择演示场景
```bash
python run_conversational_swe.py --demo
```

#### 4. 加载已保存的会话
```bash
python run_conversational_swe.py --load session_20250307_143022
```

#### 5. 查看所有保存的会话
```bash
python run_conversational_swe.py --list
```

## 💬 对话示例

### 需求澄清对话

```
👤 用户: 我想开发一个博客网站

🤖 助手: 我来帮您分析一下这个博客网站的需求。

📋 **需求理解**
原始需求: 我想开发一个博客网站
技术方向: web
功能领域: user_management, ui_ux
复杂度评估: medium

❓ **需要澄清的问题** (共6个)

**问题 1: 技术选型**
🤔 您希望开发什么类型的Web应用？(静态网站、动态Web应用、SPA单页应用)
💡 原因: 不同类型的Web应用需要不同的技术栈和架构设计

**问题 2: 用户管理**
🤔 用户管理需要哪些具体功能？(注册方式、权限等级、个人资料等)
💡 原因: 用户管理的复杂程度会影响数据库设计和安全架构

...

👤 用户: 我希望开发一个动态Web应用，支持用户注册登录，可以发布和编辑文章

🤖 助手: 非常好！基于您的回答，我建议采用以下技术方案：
- 后端: Python Flask/Django
- 前端: HTML + CSS + JavaScript
- 数据库: SQLite (开发) / PostgreSQL (生产)

现在让我们开始创建项目结构...
```

### 代码审查对话

```
👤 用户: 请审查我的user.py文件

🤖 助手: 🔍 代码审查完成: user.py

📊 **文件概览**
- 文件: user.py
- 行数: 85
- 大小: 2341 字符

⚠️  **发现的问题** (2个)
🟡 发现 3 行超过100字符的长行
   位置: 第 15, 23, 67 行
🔴 可能存在SQL注入风险

💡 **改进建议** (1个)
• 建议增加代码注释，当前注释比例较低
  建议行动: 添加关键逻辑的注释说明

🤔 **思考问题**
1. 这些长行是否可以通过重构来提高可读性？
2. 哪些复杂的逻辑需要添加注释来帮助理解？
3. 如何确保敏感信息的安全存储和传输？

💬 请回答上述问题，我将根据您的回答提供更具体的建议。

👤 用户: 第15行是数据库查询语句比较长，第23行是函数参数很多，关于SQL注入我使用的是参数化查询

🤖 助手: 很好的回答！针对您的情况我提供以下具体建议：

1. **长查询语句优化**：
   ```python
   # 可以这样分行提高可读性
   query = """
   SELECT u.id, u.username, u.email, p.avatar, p.bio
   FROM users u
   LEFT JOIN profiles p ON u.id = p.user_id
   WHERE u.active = ? AND u.created_at > ?
   """
   ```

2. **多参数函数重构**：
   建议使用数据类或字典来组织参数...
```

## 🛠️ 核心工具详解

### 1. 需求澄清工具 (RequirementClarifier)

自动分析用户输入的需求，识别技术方向、功能领域，生成针对性的澄清问题。

**使用示例**:
```python
# 在对话中使用
"请分析一下我想开发一个电商网站的需求"

# 工具会自动:
# 1. 识别技术关键词 (web, 数据库, 支付等)
# 2. 分析功能领域 (用户管理, 商品管理, 订单处理等)
# 3. 生成澄清问题 (支付方式、用户类型、商品类别等)
```

### 2. 对话式代码审查 (ConversationalCodeReview)

提供智能代码审查，支持多种审查重点，生成对话式的审查报告。

**支持的审查重点**:
- `performance`: 性能分析
- `security`: 安全检查
- `readability`: 可读性评估
- `architecture`: 架构分析
- `all`: 全面审查

**使用示例**:
```python
# 审查特定文件
"请审查我的 app.py 文件的性能"

# 全面审查
"对 user_service.py 进行全面的代码审查"
```

### 3. 项目进度跟踪 (ProjectProgressTracker)

管理软件开发项目的里程碑和任务，跟踪开发进度。

**支持的操作**:
- `create_milestone`: 创建里程碑
- `add_task`: 添加任务
- `complete_task`: 完成任务
- `list_milestones`: 列出里程碑
- `show_summary`: 显示项目总结

**使用示例**:
```python
# 创建里程碑
"创建一个名为'用户系统开发'的里程碑"

# 添加任务
"添加'实现用户注册功能'任务到用户系统开发里程碑"

# 完成任务
"标记'实现用户注册功能'任务为已完成"
```

## 📊 会话管理

### 会话自动保存

每个对话会话都会自动保存到 `conversations/` 目录下，包含：
- 对话历史记录
- 开发上下文信息
- 用户偏好设置
- 项目进度数据

### 会话文件结构

```json
{
  "session_id": "session_20250307_143022",
  "created_at": "2025-03-07T14:30:22",
  "conversation_context": {
    "project_type": "web_application",
    "tech_stack": "python_flask"
  },
  "development_history": [
    {
      "timestamp": "14:35:15",
      "action": "执行工具: requirement_clarifier",
      "details": "{\"user_requirement\": \"开发博客网站\"}",
      "result": "需求分析完成...",
      "conversation_turn": 2
    }
  ],
  "user_preferences": {
    "python版本": "python3.10",
    "代码风格": "black"
  },
  "messages": [...],
  "current_step": 5,
  "current_conversation_turn": 8
}
```

## 🎯 最佳实践

### 1. 需求描述

**好的需求描述**:
- "开发一个基于Flask的RESTful API，支持用户注册、登录、个人资料管理，使用JWT认证"
- "创建一个Python数据分析脚本，读取CSV文件，生成销售趋势图表，支持按月/季度统计"

**需要改进的需求描述**:
- "做个网站" (太模糊)
- "写个爬虫程序" (缺少具体目标)

### 2. 有效的对话策略

1. **分步骤进行**: 不要一次性提出过于复杂的需求
2. **及时反馈**: 对agent的建议和问题及时回应
3. **明确偏好**: 主动说明技术偏好和约束条件
4. **利用工具**: 善用代码审查、进度跟踪等专业工具

### 3. 会话管理建议

1. **定期保存**: 重要节点手动触发保存
2. **合理命名**: 为重要会话使用有意义的标识
3. **及时整理**: 定期清理不需要的会话文件

## 🔧 自定义扩展

### 添加新的对话工具

1. 创建新工具类继承 `BaseTool`
2. 实现 `execute` 方法
3. 在 `ConversationalSWEAgent` 中注册新工具

```python
class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="我的自定义工具",
            parameters={...}
        )

    async def execute(self, **kwargs) -> str:
        # 实现工具逻辑
        return "工具执行结果"
```

### 自定义提示词

修改 `ConversationalSWEAgent` 中的提示词构建方法：

```python
def _build_system_prompt(self) -> str:
    return """
    您的自定义系统提示词...
    """
```

## 📚 常见问题

### Q: 如何恢复中断的开发会话？
A: 使用 `--list` 查看所有会话，然后用 `--load SESSION_ID` 恢复指定会话。

### Q: 会话文件过多怎么办？
A: 可以手动删除 `conversations/` 目录下不需要的会话文件。

### Q: 如何备份重要的开发会话？
A: 直接复制 `conversations/` 目录下的对应JSON文件。

### Q: agent没有理解我的需求怎么办？
A: 尝试更详细地描述需求，或者使用需求澄清工具来帮助分析。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个对话式软件开发智能体！

## 📄 许可证

基于OpenManus项目的MIT许可证。
