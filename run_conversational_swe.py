#!/usr/bin/env python3
"""
对话式软件开发智能体 - 示例运行脚本

这个脚本演示如何使用ConversationalSWEAgent进行多轮对话式软件开发。

主要功能：
1. 智能需求分析和澄清
2. 对话式代码开发
3. 进度跟踪和项目管理
4. 代码审查和优化建议
5. 会话持久化和恢复

使用方法：
    python run_conversational_swe.py                    # 开始新对话
    python run_conversational_swe.py --load SESSION_ID  # 加载已保存的会话
    python run_conversational_swe.py --list             # 列出所有保存的会话
"""

import argparse
import asyncio
import sys
from typing import Optional
from app.agent.conversational_swe import ConversationalSWEAgent
from app.logger import logger


async def interactive_mode(agent: ConversationalSWEAgent, initial_prompt: Optional[str] = None):
    """交互式对话模式"""
    print("🤖 欢迎使用对话式软件开发智能体！")
    print("💡 我可以帮助您:")
    print("   - 分析和澄清开发需求")
    print("   - 进行对话式代码开发")
    print("   - 跟踪项目进度")
    print("   - 审查代码质量")
    print("   - 回答技术问题")
    print("\n📝 您可以随时输入 'exit' 或 'quit' 来结束对话")
    print("🔄 输入 'new' 开始新的对话")
    print("💾 会话会自动保存，可以随时恢复\n")

    try:
        if initial_prompt:
            print(f"👤 用户: {initial_prompt}")
            result = await agent.run(initial_prompt)
            print(f"🤖 助手: {result}\n")

        while True:
            try:
                user_input = input("👤 您: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', '退出']:
                    print("👋 感谢使用！会话已保存。")
                    break

                if user_input.lower() in ['new', '新对话']:
                    print("🆕 开始新对话...")
                    new_input = input("👤 请描述您的开发需求: ").strip()
                    if new_input:
                        result = await agent.start_new_conversation(new_input)
                        print(f"🤖 助手: {result}\n")
                    continue

                # 处理用户输入
                await agent.handle_user_response(user_input)
                result = await agent.run()
                print(f"🤖 助手: {result}\n")

            except KeyboardInterrupt:
                print("\n⚠️ 检测到中断信号，正在保存会话...")
                break

    except Exception as e:
        logger.error(f"交互过程中出错: {e}")
        print(f"❌ 发生错误: {e}")


async def list_sessions():
    """列出所有保存的会话"""
    agent = ConversationalSWEAgent()
    sessions = agent.list_saved_sessions()

    if not sessions:
        print("📋 当前没有保存的会话")
        return

    print(f"📚 找到 {len(sessions)} 个保存的会话:\n")

    for i, session in enumerate(sessions, 1):
        print(f"{i}. 会话ID: {session['session_id']}")
        print(f"   📅 创建时间: {session['created_at']}")
        print(f"   💬 对话轮次: {session['conversation_turns']}")
        print(f"   📊 执行步骤: {session['steps']}")
        if session['summary']:
            print(f"   📝 摘要: {session['summary'][:100]}...")
        print(f"   📁 文件路径: {session['file_path']}")
        print()


async def load_session(session_id: str):
    """加载指定的会话"""
    agent = ConversationalSWEAgent()
    session_file = f"conversations/{session_id}.json"

    success = await agent.load_session(session_file)
    if not success:
        print(f"❌ 无法加载会话: {session_id}")
        print("💡 使用 --list 查看所有可用会话")
        return

    print(f"✅ 成功加载会话: {session_id}")
    print(f"📊 {agent.get_conversation_summary()}\n")

    # 进入交互模式
    await interactive_mode(agent)


async def start_new_session(prompt: Optional[str] = None):
    """开始新的会话"""
    agent = ConversationalSWEAgent()

    if not prompt:
        prompt = input("👤 请描述您的开发需求: ").strip()
        if not prompt:
            print("❌ 请提供有效的需求描述")
            return

    print(f"\n🚀 开始新的开发会话...")
    await interactive_mode(agent, prompt)


def create_demo_scenarios():
    """创建一些演示场景"""
    scenarios = {
        "1": {
            "title": "Web应用开发",
            "prompt": "我想开发一个简单的博客网站，用户可以发布文章和评论"
        },
        "2": {
            "title": "数据分析工具",
            "prompt": "需要一个Python脚本来分析CSV文件中的销售数据并生成报表"
        },
        "3": {
            "title": "API开发",
            "prompt": "开发一个RESTful API来管理用户信息，包括注册、登录和个人资料管理"
        },
        "4": {
            "title": "自动化脚本",
            "prompt": "写一个脚本自动备份指定目录的文件到云存储"
        },
        "5": {
            "title": "移动应用",
            "prompt": "开发一个简单的待办事项移动应用"
        }
    }

    print("🎯 选择一个演示场景开始:")
    for key, scenario in scenarios.items():
        print(f"   {key}. {scenario['title']}: {scenario['prompt']}")

    choice = input("\n请选择场景编号 (1-5) 或按回车自定义: ").strip()

    if choice in scenarios:
        return scenarios[choice]["prompt"]
    else:
        return None


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="对话式软件开发智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                                    # 开始新对话
  %(prog)s --prompt "开发一个Python爬虫"      # 直接开始指定需求的对话
  %(prog)s --load session_20250307_143022     # 加载指定会话
  %(prog)s --list                            # 列出所有保存的会话
  %(prog)s --demo                            # 选择演示场景
        """
    )

    parser.add_argument(
        "--prompt",
        type=str,
        help="直接指定开发需求开始对话"
    )

    parser.add_argument(
        "--load",
        type=str,
        metavar="SESSION_ID",
        help="加载指定的会话ID"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有保存的会话"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="选择演示场景"
    )

    args = parser.parse_args()

    try:
        if args.list:
            await list_sessions()
        elif args.load:
            await load_session(args.load)
        elif args.demo:
            prompt = create_demo_scenarios()
            await start_new_session(prompt)
        else:
            await start_new_session(args.prompt)

    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        print(f"❌ 程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🔧 对话式软件开发智能体 v1.0")
    print("=" * 50)
    asyncio.run(main())
