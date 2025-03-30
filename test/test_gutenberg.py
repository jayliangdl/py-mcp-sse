import asyncio
import httpx

async def test_search_gutenberg_books(search_terms: list[str]) -> list:
    """测试版本的search_gutenberg_books函数"""
    # 构建搜索查询
    search_query = " ".join(search_terms)
    base_url = "https://gutendex.com/books/"  # 注意这里添加了末尾的斜杠
    
    print(f"测试搜索URL: {base_url}")
    print(f"测试搜索关键词: {search_query}")
    
    try:
        # 发起API请求
        async with httpx.AsyncClient() as client:
            # 添加调试信息
            print("\n1. 发起请求...")
            response = await client.get(
                base_url, 
                params={"search": search_query}, 
                timeout=30.0,
                follow_redirects=True  # 自动处理重定向
            )
            
            # 打印请求和响应信息
            print(f"2. 请求URL: {response.url}")
            print(f"3. 响应状态码: {response.status_code}")
            print(f"4. 响应头: {dict(response.headers)}")
            
            # 确保请求成功
            response.raise_for_status()
            data = response.json()
            print("\n5. API响应数据预览:")
            print(f"- 状态码: {response.status_code}")
            print(f"- 数据类型: {type(data)}")
            print(f"- 是否包含'results'键: {'results' in data}")
            if 'results' in data:
                print(f"- 结果数量: {len(data['results'])}")
        
        # 处理结果
        simplified_results = []
        for book in data.get("results", []):
            book_info = {
                "id": book.get("id"),
                "title": book.get("title"),
                "authors": book.get("authors")
            }
            simplified_results.append(book_info)
            print(f"\n找到书籍: {book_info['title']}")
            if book_info['authors']:
                print(f"作者: {', '.join(author['name'] for author in book_info['authors'])}")
        
        return simplified_results

    except httpx.RequestError as e:
        print(f"\n请求错误: {str(e)}")
        return []
    except httpx.HTTPStatusError as e:
        print(f"\nHTTP错误: {str(e)}")
        return []
    except Exception as e:
        print(f"\n未预期的错误: {str(e)}")
        return []

async def main():
    print("开始测试 Gutenberg 图书搜索功能...")
    
    # 测试用例1：搜索 James Joyce
    print("\n测试用例1: 搜索 James Joyce 的作品")
    results1 = await test_search_gutenberg_books(["James", "Joyce"])
    print(f"\n找到 {len(results1)} 本 James Joyce 的作品")

    # 测试用例2：搜索 Ulysses
    print("\n测试用例2: 搜索 Ulysses")
    results2 = await test_search_gutenberg_books(["Ulysses"])
    print(f"\n找到 {len(results2)} 本与 Ulysses 相关的作品")

if __name__ == "__main__":
    asyncio.run(main()) 