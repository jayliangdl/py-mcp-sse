# 本项目建于2025-03-30，是一个MCP Client 与 MCP Server的样例实现（Python版本）
## 它是以https://github.com/sidharthrajaram/mcp-sse为基础优化实现的【原项目上是基于(https://github.com/modelcontextprotocol/python-sdk/issues/145)的原始讨论，可下载原项目有更多说明】。
## 原版本是使用ANTHROPIC LLM实现，本版本调整使用OpenRouter.ai的LLM中转调用平台实现。

# 基于SSE的 [MCP](https://modelcontextprotocol.io/introduction) 服务器和客户端

## `mcp_server.py` 是一个基于SSE的MCP服务器，提供了基于古腾堡计划API的图书搜索工具。改编自MCP文
档中的[示例STDIO服务器实现](https://modelcontextprotocol.io/quickstart/server)。

## `client.py` 是一个MCP客户端，可以连接并使用基于SSE的MCP服务器提供的工具。改编自MCP文档中的[示例STDIO客户端实现](https://modelcontextprotocol.io/quickstart/client)。


## 系统要求

- Python 3.13 或更高版本
- uv包管理器（推荐）或pip

## 安装步骤

1. **克隆项目**
```bash
git clone [your-repository-url]
cd jay-py-mcp-sse
```

2. **环境配置**

使用uv（推荐）：
```bash
# 安装uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
uv pip install .
```

或使用传统pip：
```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install .
```

3. **配置环境变量**

复制环境变量示例文件并填写必要信息：
```bash
cp .env.sample .env
```

编辑 `.env` 文件，填入你的 OpenRouter API 密钥：
```plaintext
OPENROUTER_API_KEY=your_api_key_here
```

## 运行服务

1. **启动服务器**
```bash
uv run mcp_server.py
# 或指定主机和端口
uv run mcp_server.py --host 127.0.0.1 --port 8080
```

2. **启动客户端**
```bash
uv run client.py http://localhost:8080/sse
```

## 示例输出
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

## 项目结构
```
.
├── mcp_server.py    # SSE服务器实现
├── client.py        # MCP客户端实现
├── .env.sample      # 环境变量示例
├── pyproject.toml   # 项目依赖和配置管理
└── README.md        # 项目文档
```

## 为什么选择这种方式？

这种实现方式意味着MCP服务器现在可以作为一个运行中的进程，代理（客户端）可以随时随地连接、使用并断开连接。换句话说，基于SSE的服务器和客户端可以是解耦的进程（甚至可以在解耦的节点上运行）。这与基于STDIO的模式不同，在STDIO模式中客户端本身会将服务器作为子进程启动。这种方式更适合"云原生"用例。

## 故障排除

如果遇到问题，请检查：

1. Python版本是否满足要求（>=3.13）
2. 环境变量是否正确配置
3. 所有依赖是否正确安装
4. 端口8080是否被占用（如被占用，可使用--port参数指定其他端口）

## 获取帮助

如果遇到问题，请：
1. 检查项目的GitHub Issues页面
2. 提供完整的错误信息和运行环境信息
3. 描述问题重现步骤
