import json, requests
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# 模型配置
MODEL = "deepseek/deepseek-chat-v3-0324"

openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# 定义可用工具
def search_gutenberg_books(search_terms):
    search_query = " ".join(search_terms)
    url = "https://gutendex.com/books"
    print(f"搜索URL: {url}")
    print(f"搜索关键词: {search_query}")
    response = requests.get(url, params={"search": search_query})
    print("API响应:", response.json())
    simplified_results = []
    for book in response.json().get("results", []):
        simplified_results.append({
            "id": book.get("id"),
            "title": book.get("title"),
            "authors": book.get("authors")
        })
    return simplified_results

# 工具配置
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_gutenberg_books",
            "description": "Search for books in the Project Gutenberg library based on specified search terms",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_terms": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of search terms to find books in the Gutenberg library (e.g. ['dickens', 'great'] to search for books by Dickens with 'great' in the title)"
                    }
                },
                "required": ["search_terms"]
            }
        }
    }
]

TOOL_MAPPING = {
    "search_gutenberg_books": search_gutenberg_books
}

def process_tool_calls(response, messages):
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
        tool_args = json.loads(tool_call.function.arguments)
        tool_response = TOOL_MAPPING[tool_name](**tool_args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_name,
            "content": json.dumps(tool_response)
        })

def chat_loop():
    """主对话循环"""
    messages = [
        {
            "role": "system",
            "content": "你是一个有用的助手，可以帮助用户查找和了解书籍信息。"
        }
    ]
    
    print("欢迎使用AI助手！(按Ctrl+C退出)")
    print("可用工具：")
    print(tools)

    try:
        while True:
            # 获取用户输入
            user_input = input("用户: ")
            messages.append({"role": "user", "content": user_input})

            # 第一次调用
            response_1 = openai_client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools
            )

            # 如果需要调用工具
            if response_1.choices[0].message.tool_calls:
                print("\n正在处理工具调用...")
                process_tool_calls(response_1, messages)

                # 第二次调用获取最终结果
                response_2 = openai_client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=tools
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

if __name__ == "__main__":
    chat_loop()


