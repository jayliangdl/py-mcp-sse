# 本项目建于2025-03-30，是一个MCP Client 与 MCP Server的样例实现（Python版本）
## 它是以https://github.com/sidharthrajaram/mcp-sse为基础优化实现的【原项目上是基于(https://github.com/modelcontextprotocol/python-sdk/issues/145)的原始讨论，可下载原项目有更多说明】。
## 原版本是使用ANTHROPIC LLM实现，本版本调整使用OpenRouter.ai的LLM中转调用平台实现。

# 基于SSE的 [MCP](https://modelcontextprotocol.io/introduction) 服务器和客户端

## 使用方法

**注意**：确保在 `.env` 文件或环境变量中提供 `OPENROUTER_API_KEY`。（`.env`文件的内容可参考`.env.sample`）

```bash
# 启动服务器
uv run mcp_server.py

# 启动客户端
uv run client.py http://localhost:8080/sse
```

示例输出：
```
已初始化SSE客户端...
正在列出工具...

已连接到服务器，可用工具：['search_gutenberg_books']

AI助手已启动！
输入您的问题或输入'quit'退出。

用户: 请推荐一些詹姆斯·乔伊斯的作品

AI: 让我帮您搜索詹姆斯·乔伊斯的作品...
[调用工具 search_gutenberg_books，参数：{"search_terms": ["James Joyce"]}]

找到以下作品：
- 《尤利西斯》(Ulysses)
- 《都柏林人》(Dubliners)
- 《青年艺术家的画像》(A Portrait of the Artist as a Young Man)
...
```

## 为什么选择这种方式？

这种实现方式意味着MCP服务器现在可以作为一个运行中的进程，代理（客户端）可以随时随地连接、使用并断开连接。换句话说，基于SSE的服务器和客户端可以是解耦的进程（甚至可以在解耦的节点上运行）。这与基于STDIO的模式不同，在STDIO模式中客户端本身会将服务器作为子进程启动。这种方式更适合"云原生"用例。

### 服务器

`mcp_server.py` 是一个基于SSE的MCP服务器，提供了基于古腾堡计划API的图书搜索工具。改编自MCP文档中的[示例STDIO服务器实现](https://modelcontextprotocol.io/quickstart/server)。

默认情况下，服务器运行在 0.0.0.0:8080，但可以通过命令行参数配置：

```bash
uv run mcp_server.py --host <主机地址> --port <端口号>
```

### 客户端

`client.py` 是一个MCP客户端，可以连接并使用基于SSE的MCP服务器提供的工具。改编自MCP文档中的[示例STDIO客户端实现](https://modelcontextprotocol.io/quickstart/client)。

默认情况下，客户端通过命令行参数提供的SSE端点进行连接：

```bash
uv run client.py http://localhost:8080/sse
```
