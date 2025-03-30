import asyncio
import json
import os
from openai import OpenAI
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv

load_dotenv()  # 从.env文件加载环境变量

class MCPClient:
    def __init__(self):
        # 初始化会话和客户端对象
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_sse_server(self, server_url: str):
        """连接到运行SSE传输的MCP服务器"""
        # 保存上下文管理器以保持其活跃状态
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        # 初始化
        await self.session.initialize()

        # 列出可用工具以验证连接
        print("已初始化SSE客户端...")
        print("正在列出工具...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nMCP server提供的工具：")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        # 转换工具格式并打印
        formatted_tools = [] 
        # tools_for_call = {}
        for tool in tools:
            # 构建参数属性
            properties = {}
            for param_name, param_info in tool.inputSchema["properties"].items():
                param_data = {
                    "type": param_info["type"],
                    "description": param_info.get("description", param_info["title"])
                }
                
                # 如果是数组类型，添加items
                if param_info["type"] == "array" and "items" in param_info:
                    param_data["items"] = {
                        "type": param_info["items"]["type"]
                    }
                
                properties[param_name] = param_data

            # 使用工具名作为key
            tool_dict = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": tool.inputSchema.get("required", [])
                    }
                }
            }
            
            # 存储工具配置到 formatted_tools
            formatted_tools.append(tool_dict)
            # 存储工具对象到 tools_for_call
            # tools_for_call[tool.name] = tool  # 存储整个工具对象
        
        print("\n转换后的工具格式：")
        print(json.dumps(formatted_tools, indent=2, ensure_ascii=False))
        return formatted_tools, self.session

    async def cleanup(self):
        """正确清理会话和流"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    async def chat_loop(self, available_tools, model, session):
        openai_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        """主对话循环"""
        messages = [
            {
                "role": "system",
                "content": "你是一个有用的助手，可以帮助用户查找和了解书籍信息。"
            }
        ]
        
        print("欢迎使用AI助手！(按Ctrl+C退出)")
        print("可用工具：")
        print(available_tools)

        try:
            while True:
                # 获取用户输入
                user_input = input("用户: ")
                messages.append({"role": "user", "content": user_input})

                # 第一次调用
                response_1 = openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=available_tools
                )

                # 如果需要调用工具
                if response_1.choices[0].message.tool_calls:
                    await process_tool_calls(response_1, messages, session)

                    # 第二次调用获取最终结果
                    response_2 = openai_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=available_tools
                    )
                    final_response = response_2.choices[0].message.content
                else:
                    # 如果不需要工具调用，直接使用第一次响应
                    final_response = response_1.choices[0].message.content

                # 添加AI的最终响应到消息历史
                messages.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                print("\nAI: " + final_response + "\n")

        except KeyboardInterrupt:
            print("\n\n再见！")
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

async def process_tool_calls(response, messages, session):
    """处理工具调用并更新消息历史"""
    # 追加AI的响应消息
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            } for tool_call in response.choices[0].message.tool_calls
        ]
    })

    # 处理工具调用
    for tool_call in response.choices[0].message.tool_calls:
        tool_name = tool_call.function.name
        print(f'\n调用工具: {tool_name}')
        tool_args = json.loads(tool_call.function.arguments)
        print(f'参数: {json.dumps(tool_args, indent=2, ensure_ascii=False)}')
        
        try:
            # 使用session的call_tool方法来调用工具
            tool_response = await session.call_tool(tool_name, tool_args)
            
            # 处理工具响应
            if tool_response.isError:
                # 如果是错误响应，获取错误信息
                error_message = tool_response.content[0].text if tool_response.content else "未知错误"
                print(f'工具执行错误: {error_message}')
                # 将错误信息格式化为更友好的形式
                formatted_error = {
                    "status": "error",
                    "message": "工具执行出错",
                    "details": error_message,
                    "suggestion": "这可能是临时性问题，您可以：\n1. 尝试重新查询\n2. 换个不同的查询方式\n3. 使用其他可用的工具"
                }
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(formatted_error, ensure_ascii=False)
                })
            else:
                # 如果是正常响应，获取响应内容
                result = tool_response.content[0].text if tool_response.content else ""
                print(f'工具执行成功: {result}')
                formatted_result = {
                    "status": "success",
                    "result": result
                }
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(formatted_result, ensure_ascii=False)
                })
        except Exception as e:
            print(f"工具调用异常: {str(e)}")
            formatted_error = {
                "status": "error",
                "message": "工具调用异常",
                "details": str(e),
                "suggestion": "这是一个意外错误，请稍后重试或联系管理员"
            }
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(formatted_error, ensure_ascii=False)
            })

async def main():
    if len(sys.argv) < 2:
        print("使用方法: uv run client.py <SSE MCP服务器的URL (例如: http://localhost:8080/sse)>")
        sys.exit(1)

    client = MCPClient()
    try:
        model = os.getenv("MODEL")
        available_tools, session = await client.connect_to_sse_server(server_url=sys.argv[1])
        await client.chat_loop(available_tools, model, session)
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys
    asyncio.run(main())
