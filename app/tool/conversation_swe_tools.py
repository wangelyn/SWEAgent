"""
对话式软件开发专用工具集
"""
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.tool.base import BaseTool
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.bash import Bash
from app.logger import logger


class ConversationalCodeReview(BaseTool):
    """
    对话式代码审查工具
    """

    def __init__(self):
        super().__init__(
            name="conversational_code_review",
            description="进行对话式代码审查，分析代码质量并提出改进建议",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要审查的文件路径"
                    },
                    "review_focus": {
                        "type": "string",
                        "description": "审查重点：'performance'(性能), 'security'(安全), 'readability'(可读性), 'architecture'(架构), 'all'(全面)",
                        "enum": ["performance", "security", "readability", "architecture", "all"],
                        "default": "all"
                    },
                    "ask_questions": {
                        "type": "boolean",
                        "description": "是否在审查中提出问题供开发者思考",
                        "default": True
                    }
                },
                "required": ["file_path"]
            }
        )

    async def execute(self, file_path: str, review_focus: str = "all", ask_questions: bool = True) -> str:
        """执行对话式代码审查"""
        try:
            if not os.path.exists(file_path):
                return f"❌ 文件不存在: {file_path}"

            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                return f"📄 文件为空: {file_path}"

            # 分析代码
            review_result = self._analyze_code(content, file_path, review_focus)

            # 生成对话式审查报告
            report = self._generate_conversation_report(review_result, ask_questions)

            return f"🔍 代码审查完成: {file_path}\n\n{report}"

        except Exception as e:
            logger.error(f"代码审查出错: {e}")
            return f"❌ 代码审查失败: {str(e)}"

    def _analyze_code(self, content: str, file_path: str, focus: str) -> Dict[str, Any]:
        """分析代码质量"""
        lines = content.split('\n')

        analysis = {
            "file_info": {
                "path": file_path,
                "lines": len(lines),
                "size": len(content),
                "extension": os.path.splitext(file_path)[1]
            },
            "issues": [],
            "suggestions": [],
            "questions": []
        }

        # 基础分析（简化版，实际应用中可集成静态分析工具）
        if focus in ["readability", "all"]:
            analysis = self._check_readability(content, lines, analysis)

        if focus in ["performance", "all"]:
            analysis = self._check_performance(content, lines, analysis)

        if focus in ["security", "all"]:
            analysis = self._check_security(content, lines, analysis)

        if focus in ["architecture", "all"]:
            analysis = self._check_architecture(content, lines, analysis)

        return analysis

    def _check_readability(self, content: str, lines: List[str], analysis: Dict) -> Dict:
        """检查代码可读性"""
        # 检查长行
        long_lines = [(i+1, line) for i, line in enumerate(lines) if len(line) > 100]
        if long_lines:
            analysis["issues"].append({
                "type": "readability",
                "severity": "medium",
                "message": f"发现 {len(long_lines)} 行超过100字符的长行",
                "lines": [line_num for line_num, _ in long_lines[:3]]
            })
            analysis["questions"].append("这些长行是否可以通过重构来提高可读性？")

        # 检查注释
        comment_lines = [line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')]
        comment_ratio = len(comment_lines) / len(lines) if lines else 0

        if comment_ratio < 0.1:
            analysis["suggestions"].append({
                "type": "readability",
                "message": "建议增加代码注释，当前注释比例较低",
                "action": "添加关键逻辑的注释说明"
            })
            analysis["questions"].append("哪些复杂的逻辑需要添加注释来帮助理解？")

        return analysis

    def _check_performance(self, content: str, lines: List[str], analysis: Dict) -> Dict:
        """检查性能相关问题"""
        # 检查循环嵌套
        nested_loops = 0
        loop_depth = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('for ') or stripped.startswith('while '):
                loop_depth += 1
                if loop_depth > 1:
                    nested_loops += 1
            if not line.startswith(' ') and not line.startswith('\t'):
                loop_depth = 0

        if nested_loops > 0:
            analysis["issues"].append({
                "type": "performance",
                "severity": "medium",
                "message": f"发现 {nested_loops} 处嵌套循环",
                "suggestion": "考虑优化算法复杂度"
            })
            analysis["questions"].append("这些嵌套循环是否可以通过更高效的算法来优化？")

        return analysis

    def _check_security(self, content: str, lines: List[str], analysis: Dict) -> Dict:
        """检查安全问题"""
        security_risks = []

        # 检查SQL注入风险
        if 'execute(' in content or 'query(' in content:
            if '%s' in content or '.format(' in content:
                security_risks.append("可能存在SQL注入风险")

        # 检查硬编码密码
        if any(keyword in content.lower() for keyword in ['password', 'secret', 'key']):
            if '=' in content:
                security_risks.append("可能存在硬编码敏感信息")

        if security_risks:
            analysis["issues"].extend([{
                "type": "security",
                "severity": "high",
                "message": risk
            } for risk in security_risks])
            analysis["questions"].append("如何确保敏感信息的安全存储和传输？")

        return analysis

    def _check_architecture(self, content: str, lines: List[str], analysis: Dict) -> Dict:
        """检查架构问题"""
        # 检查函数长度
        function_lines = []
        current_function_lines = 0
        in_function = False

        for line in lines:
            if line.strip().startswith('def ') or line.strip().startswith('class '):
                if in_function and current_function_lines > 0:
                    function_lines.append(current_function_lines)
                in_function = True
                current_function_lines = 0
            elif in_function:
                current_function_lines += 1

        long_functions = [length for length in function_lines if length > 50]
        if long_functions:
            analysis["suggestions"].append({
                "type": "architecture",
                "message": f"发现 {len(long_functions)} 个长函数(>50行)",
                "action": "考虑将长函数分解为更小的函数"
            })
            analysis["questions"].append("这些长函数是否承担了过多的职责？")

        return analysis

    def _generate_conversation_report(self, analysis: Dict, ask_questions: bool) -> str:
        """生成对话式审查报告"""
        report_parts = []

        # 文件基本信息
        file_info = analysis["file_info"]
        report_parts.append(f"📊 **文件概览**")
        report_parts.append(f"- 文件: {file_info['path']}")
        report_parts.append(f"- 行数: {file_info['lines']}")
        report_parts.append(f"- 大小: {file_info['size']} 字符")

        # 问题报告
        if analysis["issues"]:
            report_parts.append(f"\n⚠️  **发现的问题** ({len(analysis['issues'])}个)")
            for issue in analysis["issues"]:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue["severity"], "⚪")
                report_parts.append(f"{severity_emoji} {issue['message']}")
                if "lines" in issue:
                    report_parts.append(f"   位置: 第 {', '.join(map(str, issue['lines']))} 行")

        # 改进建议
        if analysis["suggestions"]:
            report_parts.append(f"\n💡 **改进建议** ({len(analysis['suggestions'])}个)")
            for suggestion in analysis["suggestions"]:
                report_parts.append(f"• {suggestion['message']}")
                if "action" in suggestion:
                    report_parts.append(f"  建议行动: {suggestion['action']}")

        # 思考问题
        if ask_questions and analysis["questions"]:
            report_parts.append(f"\n🤔 **思考问题**")
            for i, question in enumerate(analysis["questions"], 1):
                report_parts.append(f"{i}. {question}")
            report_parts.append("\n💬 请回答上述问题，我将根据您的回答提供更具体的建议。")

        # 总结
        if not analysis["issues"] and not analysis["suggestions"]:
            report_parts.append(f"\n✅ **总结**: 代码质量良好，未发现明显问题！")
        else:
            issue_count = len(analysis["issues"])
            suggestion_count = len(analysis["suggestions"])
            report_parts.append(f"\n📋 **总结**: 发现 {issue_count} 个问题，{suggestion_count} 个改进建议")
            report_parts.append("建议优先处理高优先级问题，然后考虑改进建议。")

        return "\n".join(report_parts)


class ProjectProgressTracker(BaseTool):
    """
    项目进度跟踪工具
    """
    progress_file: str = "project_progress.json"
    
    def __init__(self, **kwargs):
        print("Initializing ProjectProgressTracker...")
        super().__init__(
            name="project_progress_tracker",
            description="跟踪和管理软件开发项目的进度",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作类型",
                        "enum": ["create_milestone", "update_progress", "list_milestones", "add_task", "complete_task", "show_summary"]
                    },
                    "milestone_name": {
                        "type": "string",
                        "description": "里程碑名称"
                    },
                    "description": {
                        "type": "string",
                        "description": "描述信息"
                    },
                    "task_name": {
                        "type": "string",
                        "description": "任务名称"
                    },
                    "progress": {
                        "type": "integer",
                        "description": "进度百分比(0-100)",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["action"]
            },
            **kwargs
        )
        print("already")


    async def execute(self, action: str, **kwargs) -> str:
        """执行进度跟踪操作"""
        try:
            progress_data = self._load_progress_data()

            if action == "create_milestone":
                return await self._create_milestone(progress_data, kwargs)
            elif action == "update_progress":
                return await self._update_progress(progress_data, kwargs)
            elif action == "list_milestones":
                return await self._list_milestones(progress_data)
            elif action == "add_task":
                return await self._add_task(progress_data, kwargs)
            elif action == "complete_task":
                return await self._complete_task(progress_data, kwargs)
            elif action == "show_summary":
                return await self._show_summary(progress_data)
            else:
                return f"❌ 未知操作: {action}"

        except Exception as e:
            logger.error(f"进度跟踪出错: {e}")
            return f"❌ 操作失败: {str(e)}"

    def _load_progress_data(self) -> Dict:
        """加载进度数据"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # 默认数据结构
        return {
            "project_name": "软件开发项目",
            "created_at": datetime.now().isoformat(),
            "milestones": [],
            "tasks": [],
            "overall_progress": 0
        }

    def _save_progress_data(self, data: Dict) -> None:
        """保存进度数据"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def _create_milestone(self, data: Dict, kwargs: Dict) -> str:
        """创建里程碑"""
        milestone_name = kwargs.get("milestone_name")
        description = kwargs.get("description", "")

        if not milestone_name:
            return "❌ 请提供里程碑名称"

        milestone = {
            "id": len(data["milestones"]) + 1,
            "name": milestone_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "status": "planning",
            "tasks": []
        }

        data["milestones"].append(milestone)
        self._save_progress_data(data)

        return f"✅ 成功创建里程碑: {milestone_name}\n📝 描述: {description}"

    async def _add_task(self, data: Dict, kwargs: Dict) -> str:
        """添加任务"""
        task_name = kwargs.get("task_name")
        milestone_name = kwargs.get("milestone_name")
        description = kwargs.get("description", "")

        if not task_name:
            return "❌ 请提供任务名称"

        task = {
            "id": len(data["tasks"]) + 1,
            "name": task_name,
            "description": description,
            "milestone": milestone_name,
            "created_at": datetime.now().isoformat(),
            "status": "todo",
            "completed_at": None
        }

        data["tasks"].append(task)

        # 如果指定了里程碑，也添加到里程碑的任务列表
        if milestone_name:
            for milestone in data["milestones"]:
                if milestone["name"] == milestone_name:
                    milestone["tasks"].append(task["id"])
                    break

        self._save_progress_data(data)

        return f"✅ 成功添加任务: {task_name}\n📋 关联里程碑: {milestone_name or '无'}"

    async def _complete_task(self, data: Dict, kwargs: Dict) -> str:
        """完成任务"""
        task_name = kwargs.get("task_name")

        if not task_name:
            return "❌ 请提供任务名称"

        task_found = False
        for task in data["tasks"]:
            if task["name"] == task_name:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                task_found = True
                break

        if not task_found:
            return f"❌ 未找到任务: {task_name}"

        # 更新相关里程碑进度
        self._update_milestone_progress(data)
        self._save_progress_data(data)

        return f"🎉 任务完成: {task_name}"

    def _update_milestone_progress(self, data: Dict) -> None:
        """更新里程碑进度"""
        for milestone in data["milestones"]:
            if milestone["tasks"]:
                completed_tasks = sum(
                    1 for task in data["tasks"]
                    if task["id"] in milestone["tasks"] and task["status"] == "completed"
                )
                total_tasks = len(milestone["tasks"])
                milestone["progress"] = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

                if milestone["progress"] == 100:
                    milestone["status"] = "completed"
                elif milestone["progress"] > 0:
                    milestone["status"] = "in_progress"

        # 更新整体进度
        if data["milestones"]:
            total_progress = sum(milestone["progress"] for milestone in data["milestones"])
            data["overall_progress"] = int(total_progress / len(data["milestones"]))

    async def _show_summary(self, data: Dict) -> str:
        """显示项目总结"""
        summary_parts = []

        summary_parts.append(f"📊 **{data['project_name']} 进度总结**")
        summary_parts.append(f"🎯 整体进度: {data['overall_progress']}%")
        summary_parts.append(f"📅 创建时间: {data['created_at'][:10]}")

        # 里程碑统计
        milestones = data["milestones"]
        if milestones:
            completed_milestones = len([m for m in milestones if m["status"] == "completed"])
            in_progress_milestones = len([m for m in milestones if m["status"] == "in_progress"])

            summary_parts.append(f"\n🎯 **里程碑概览** (总共 {len(milestones)} 个)")
            summary_parts.append(f"✅ 已完成: {completed_milestones}")
            summary_parts.append(f"🚧 进行中: {in_progress_milestones}")
            summary_parts.append(f"📋 计划中: {len(milestones) - completed_milestones - in_progress_milestones}")

        # 任务统计
        tasks = data["tasks"]
        if tasks:
            completed_tasks = len([t for t in tasks if t["status"] == "completed"])
            summary_parts.append(f"\n📝 **任务概览** (总共 {len(tasks)} 个)")
            summary_parts.append(f"✅ 已完成: {completed_tasks}")
            summary_parts.append(f"📋 待完成: {len(tasks) - completed_tasks}")

        # 最近活动
        recent_tasks = sorted(
            [t for t in tasks if t.get("completed_at")],
            key=lambda x: x["completed_at"],
            reverse=True
        )[:3]

        if recent_tasks:
            summary_parts.append(f"\n🕒 **最近完成的任务**")
            for task in recent_tasks:
                completed_date = task["completed_at"][:10]
                summary_parts.append(f"• {task['name']} ({completed_date})")

        return "\n".join(summary_parts)

    async def _list_milestones(self, data: Dict) -> str:
        """列出所有里程碑"""
        milestones = data["milestones"]

        if not milestones:
            return "📋 当前没有创建任何里程碑\n💡 使用 create_milestone 操作来创建第一个里程碑"

        milestone_list = [f"🎯 **项目里程碑** (共 {len(milestones)} 个)"]

        for milestone in milestones:
            status_emoji = {
                "planning": "📋",
                "in_progress": "🚧",
                "completed": "✅"
            }.get(milestone["status"], "❓")

            milestone_list.append(f"\n{status_emoji} **{milestone['name']}** ({milestone['progress']}%)")
            if milestone["description"]:
                milestone_list.append(f"   📝 {milestone['description']}")

            # 显示关联任务
            milestone_tasks = [
                task for task in data["tasks"]
                if task["id"] in milestone.get("tasks", [])
            ]
            if milestone_tasks:
                completed_count = len([t for t in milestone_tasks if t["status"] == "completed"])
                milestone_list.append(f"   📊 任务进度: {completed_count}/{len(milestone_tasks)}")

        return "\n".join(milestone_list)


class RequirementClarifier(BaseTool):
    """
    需求澄清工具
    """

    def __init__(self):
        super().__init__(
            name="requirement_clarifier",
            description="智能分析和澄清软件开发需求",
            parameters={
                "type": "object",
                "properties": {
                    "user_requirement": {
                        "type": "string",
                        "description": "用户原始需求描述"
                    },
                    "analysis_depth": {
                        "type": "string",
                        "description": "分析深度",
                        "enum": ["basic", "detailed", "comprehensive"],
                        "default": "detailed"
                    }
                },
                "required": ["user_requirement"]
            }
        )

    async def execute(self, user_requirement: str, analysis_depth: str = "detailed") -> str:
        """执行需求澄清"""
        try:
            # 分析需求
            analysis = self._analyze_requirement(user_requirement, analysis_depth)

            # 生成澄清问题
            clarification_questions = self._generate_clarification_questions(analysis)

            # 生成报告
            report = self._generate_clarification_report(analysis, clarification_questions)

            return f"🔍 需求分析完成\n\n{report}"

        except Exception as e:
            logger.error(f"需求澄清出错: {e}")
            return f"❌ 需求澄清失败: {str(e)}"

    def _analyze_requirement(self, requirement: str, depth: str) -> Dict[str, Any]:
        """分析用户需求"""
        words = requirement.lower().split()

        analysis = {
            "original_requirement": requirement,
            "key_concepts": [],
            "technology_hints": [],
            "functional_areas": [],
            "ambiguous_parts": [],
            "missing_details": [],
            "complexity_level": "medium"
        }

        # 识别关键概念
        tech_keywords = {
            "web": ["网站", "web", "网页", "前端", "后端"],
            "mobile": ["手机", "移动", "app", "安卓", "ios"],
            "data": ["数据", "数据库", "分析", "统计", "报表"],
            "ai": ["人工智能", "ai", "机器学习", "深度学习", "智能"],
            "api": ["接口", "api", "服务", "调用"],
            "game": ["游戏", "游戏开发", "unity", "引擎"]
        }

        for category, keywords in tech_keywords.items():
            if any(keyword in requirement for keyword in keywords):
                analysis["technology_hints"].append(category)

        # 识别功能领域
        functional_keywords = {
            "user_management": ["用户", "登录", "注册", "账号"],
            "data_processing": ["处理", "计算", "算法", "逻辑"],
            "ui_ux": ["界面", "交互", "用户体验", "设计"],
            "integration": ["集成", "对接", "连接", "同步"],
            "automation": ["自动", "定时", "批处理", "任务"]
        }

        for area, keywords in functional_keywords.items():
            if any(keyword in requirement for keyword in keywords):
                analysis["functional_areas"].append(area)

        # 检测模糊部分
        ambiguous_indicators = ["类似", "差不多", "简单的", "复杂的", "好看的", "高性能"]
        for indicator in ambiguous_indicators:
            if indicator in requirement:
                analysis["ambiguous_parts"].append(f"'{indicator}' 需要更具体的定义")

        # 评估复杂度
        complexity_indicators = {
            "simple": ["简单", "基础", "小", "demo"],
            "complex": ["复杂", "高级", "大型", "企业级", "分布式", "微服务"]
        }

        if any(word in requirement for word in complexity_indicators["simple"]):
            analysis["complexity_level"] = "simple"
        elif any(word in requirement for word in complexity_indicators["complex"]):
            analysis["complexity_level"] = "complex"

        return analysis

    def _generate_clarification_questions(self, analysis: Dict) -> List[Dict[str, str]]:
        """生成澄清问题"""
        questions = []

        # 基于技术方向的问题
        if "web" in analysis["technology_hints"]:
            questions.append({
                "category": "技术选型",
                "question": "您希望开发什么类型的Web应用？(静态网站、动态Web应用、SPA单页应用)",
                "why": "不同类型的Web应用需要不同的技术栈和架构设计"
            })

        if "mobile" in analysis["technology_hints"]:
            questions.append({
                "category": "平台选择",
                "question": "您希望支持哪些移动平台？(iOS、Android、还是跨平台)",
                "why": "平台选择会影响开发工具和技术栈的选择"
            })

        # 基于功能领域的问题
        if "user_management" in analysis["functional_areas"]:
            questions.append({
                "category": "用户管理",
                "question": "用户管理需要哪些具体功能？(注册方式、权限等级、个人资料等)",
                "why": "用户管理的复杂程度会影响数据库设计和安全架构"
            })

        if "data_processing" in analysis["functional_areas"]:
            questions.append({
                "category": "数据处理",
                "question": "需要处理什么类型的数据？数据量大概有多少？",
                "why": "数据类型和规模会影响存储方案和处理架构的选择"
            })

        # 基于模糊部分的问题
        if analysis["ambiguous_parts"]:
            questions.append({
                "category": "需求澄清",
                "question": "能否具体说明以下表述？" + "、".join(analysis["ambiguous_parts"]),
                "why": "明确需求细节有助于准确估算工作量和选择合适方案"
            })

        # 通用问题
        questions.extend([
            {
                "category": "项目背景",
                "question": "这个项目的主要用户群体是谁？预期使用场景是什么？",
                "why": "了解用户群体有助于做出更好的设计决策"
            },
            {
                "category": "技术约束",
                "question": "有什么技术限制或偏好吗？(编程语言、框架、部署环境等)",
                "why": "技术约束会影响方案设计和实现方式"
            },
            {
                "category": "项目范围",
                "question": "项目的优先级如何？哪些功能是核心必须的，哪些是可选的？",
                "why": "明确优先级有助于合理规划开发顺序和资源分配"
            }
        ])

        return questions[:6]  # 限制问题数量，避免过多

    def _generate_clarification_report(self, analysis: Dict, questions: List[Dict]) -> str:
        """生成澄清报告"""
        report_parts = []

        # 需求理解
        report_parts.append("📋 **需求理解**")
        report_parts.append(f"原始需求: {analysis['original_requirement']}")

        if analysis["technology_hints"]:
            report_parts.append(f"技术方向: {', '.join(analysis['technology_hints'])}")

        if analysis["functional_areas"]:
            report_parts.append(f"功能领域: {', '.join(analysis['functional_areas'])}")

        report_parts.append(f"复杂度评估: {analysis['complexity_level']}")

        # 澄清问题
        report_parts.append(f"\n❓ **需要澄清的问题** (共{len(questions)}个)")

        for i, q in enumerate(questions, 1):
            report_parts.append(f"\n**问题 {i}: {q['category']}**")
            report_parts.append(f"🤔 {q['question']}")
            report_parts.append(f"💡 原因: {q['why']}")

        # 下一步建议
        report_parts.append(f"\n🎯 **建议的下一步**")
        report_parts.append("1. 请回答上述问题，我将根据您的回答制定具体的技术方案")
        report_parts.append("2. 如果需要，我可以帮您创建项目里程碑和任务分解")
        report_parts.append("3. 确定技术方案后，我们可以开始具体的开发工作")

        return "\n".join(report_parts)
