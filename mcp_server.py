from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
import requests

# 初始化用于图书搜索工具的FastMCP服务器（SSE）
mcp = FastMCP("book_search")

@mcp.tool()
async def search_gutenberg_books(search_terms: list[str]) -> list:
    """Search for books in the Project Gutenberg library.

    Args:
        search_terms: List of search terms to find books (e.g. ["dickens", "great"] to search for books by Dickens with 'great' in the title)
    """    
    # return simplified_results
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

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """创建一个Starlette应用程序，可以通过SSE为提供的mcp服务器提供服务。"""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    mcp_server = mcp._mcp_server  # noqa: WPS437

    import argparse
    
    parser = argparse.ArgumentParser(description='运行基于SSE的MCP服务器')
    parser.add_argument('--host', default='0.0.0.0', help='绑定的主机地址')
    parser.add_argument('--port', type=int, default=8080, help='监听的端口号')
    args = parser.parse_args()

    # 将SSE请求处理绑定到MCP服务器
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port)
