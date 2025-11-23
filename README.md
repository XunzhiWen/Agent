# 🤖 LangGraph Gemini Agent

> 基于 LangGraph 和 Google Gemini API 构建的智能代理系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![Gemini](https://img.shields.io/badge/Gemini-2.5--flash-orange.svg)](https://ai.google.dev/)

## ✨ 特性

- 🤖 使用 **Gemini 2.5 Flash** 模型进行自然语言理解
- 🔧 **工具调用**能力 (计算器、搜索等)
- 💾 **对话记忆**功能 (支持多轮对话)
- 🔄 **自动决策**何时使用工具
- 📊 基于 **LangGraph** 的状态图管理

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/XunzhiWen/Agent.git
cd Agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

依赖包括:
- `langgraph` - 状态图编排框架
- `langchain-community` - LangChain 工具
- `python-dotenv` - 环境变量管理
- `google-genai` - Gemini API 客户端

### 3. 配置 API 密钥

创建 `.env` 文件:

```bash
echo "GEMINI_API_KEY=your-api-key-here" > .env
```

获取 API 密钥: https://aistudio.google.com/app/apikey

### 4. 运行

```bash
python main.py
```

## 💬 使用示例

```
You: What is 100 * 25?
Agent is thinking...
Node 'agent':
Calling Tool: calculator_func
---
Node 'tools':
---
Node 'agent':
The result of 100 * 25 is 2500.
---
```

## 📁 项目结构

```
Agent/
├── main.py                    # 主程序入口
├── requirements.txt           # Python 依赖
├── .env                      # API 密钥配置 (需自行创建)
├── src/
│   ├── __init__.py          # Python 包初始化
│   ├── tools.py             # 工具函数定义
│   └── graph.py             # LangGraph 状态图逻辑
├── debug_gemini.py          # Gemini API 调试脚本
├── debug_models.py          # 模型列表查询脚本
└── README_GUIDE.md          # 📖 完整技术文档入口
```

## 📖 详细文档

本项目提供了**超详细的逐行代码讲解文档**:

### 👉 [开始阅读完整技术指南](README_GUIDE.md)

文档包含:
- ✅ 每个文件的逐行代码解析
- ✅ 工作流程可视化 (Mermaid 图表)
- ✅ 生产环境最佳实践
- ✅ 安全性增强方案
- ✅ 工具扩展示例
- ✅ 持久化存储方案
- ✅ Web 界面集成
- ✅ 多代理系统设计

## 🛠️ 核心组件

### 1️⃣ 工具系统 (`src/tools.py`)

定义了两个示例工具:

```python
# 计算器工具
calculator_func("2 + 3")  # "5"

# 搜索工具 (当前为模拟实现)
search_func("weather")  # 返回模拟搜索结果
```

### 2️⃣ 状态图 (`src/graph.py`)

使用 LangGraph 构建的工作流:

```
用户输入 → [agent节点] → 决定是否需要工具
              ↓
         [should_continue]
              ↓
    有工具调用? ─Yes→ [tools节点] → 执行工具 → 回到agent
              ↓
             No → END (输出结果)
```

### 3️⃣ 对话记忆

使用 `MemorySaver` 实现多轮对话:

```python
# 第一轮
You: My name is Alice
Agent: Nice to meet you, Alice!

# 第二轮 (能记住上下文)
You: What's my name?
Agent: Your name is Alice.
```

## ⚙️ 配置选项

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `GEMINI_API_KEY` | Gemini API 密钥 | ✅ |
| `GOOGLE_API_KEY` | 备用密钥名称 | ⭕ |

### 模型选择

在 `src/graph.py` 中修改:

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",  # 可选: gemini-1.5-pro, gemini-2.0-flash
    # ...
)
```

## 🔧 添加自定义工具

只需 3 步:

### 1. 在 `src/tools.py` 中定义工具函数

```python
def weather_func(city: str) -> str:
    """Get weather information for a city."""
    # 实现你的逻辑
    return f"Weather in {city}: Sunny"

weather = tool("weather_func")(weather_func)
```

### 2. 在 `src/graph.py` 中注册

```python
gemini_tools = [calculator_func, search_func, weather_func]
langchain_tools = [calculator, search, weather]
```

### 3. 测试

```python
You: What's the weather in Tokyo?
Agent: The weather in Tokyo is Sunny.
```

## 🐛 调试

### 检查 API 连接

```bash
python debug_models.py
```

### 测试工具调用

```bash
python debug_gemini.py
```

## 🔒 安全注意事项

⚠️ **重要警告**:

1. **永远不要**将 `.env` 文件提交到 Git
2. **不要**在生产环境使用 `eval()` (参考文档中的安全替代方案)
3. **务必**为 API 密钥设置使用限制和监控

## 🚧 已知限制

- 计算器工具使用 `eval()` (仅供演示，生产环境需替换)
- 搜索工具为模拟实现 (需集成真实 API)
- 对话历史仅保存在内存中 (程序重启后丢失)

## 🎯 未来改进方向

- [ ] 数据库持久化 (SQLite/PostgreSQL)
- [ ] 真实搜索 API 集成 (DuckDuckGo/Google)
- [ ] Web 界面 (Streamlit/Gradio)
- [ ] 更多工具 (天气、文件操作、邮件等)
- [ ] 多代理协作系统
- [ ] 流式响应
- [ ] Docker 容器化

## 📚 学习资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [Gemini API 文档](https://ai.google.dev/docs)
- [LangChain 工具指南](https://python.langchain.com/docs/modules/agents/tools/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License

## 👤 作者

Xunzhi Wen ([@XunzhiWen](https://github.com/XunzhiWen))

---

**开始探索**: 阅读 [完整技术指南](README_GUIDE.md) 了解所有细节! 📖
