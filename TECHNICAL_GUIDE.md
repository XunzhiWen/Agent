# LangGraph Gemini Agent - 详细技术指南

> 本指南将逐文件、逐行详细讲解整个项目的架构和实现细节

## 目录

1. [项目概述](#项目概述)
2. [项目结构](#项目结构)
3. [依赖管理 - requirements.txt](#依赖管理)
4. [环境配置 - .env](#环境配置)
5. [工具定义 - src/tools.py](#工具定义)
6. [核心图架构 - src/graph.py](#核心图架构)
7. [主程序入口 - main.py](#主程序入口)
8. [调试脚本](#调试脚本)
9. [工作流程详解](#工作流程详解)
10. [最佳实践](#最佳实践)

---

## 项目概述

这是一个基于 **LangGraph** 和 **Google Gemini** API 构建的智能代理(AI Agent)系统。该系统能够:

- 🤖 使用 Gemini 2.5 Flash 模型进行自然语言理解
- 🔧 调用自定义工具(计算器、搜索)
- 💾 维护对话历史记忆
- 🔄 自动决策何时使用工具
- 📊 使用状态图管理复杂的对话流程

### 核心技术栈

| 技术 | 作用 | 版本要求 |
|------|------|---------|
| LangGraph | 状态图编排框架 | 最新版 |
| LangChain Core | 消息抽象层 | 最新版 |
| Google GenAI SDK | Gemini API 客户端 | 最新版 |
| Python dotenv | 环境变量管理 | 最新版 |

---

## 项目结构

```
Agent/
├── .env                    # 环境变量配置文件(API密钥)
├── .gitattributes         # Git属性配置
├── README.md              # 项目简介
├── requirements.txt       # Python依赖列表
├── main.py               # 主程序入口
├── debug_gemini.py       # Gemini API调试脚本
├── debug_models.py       # 模型列表调试脚本
├── src/
│   ├── __init__.py      # Python包初始化文件
│   ├── tools.py         # 工具函数定义
│   └── graph.py         # LangGraph状态图定义
└── tests/               # 测试目录
```

---

## 依赖管理

### 📄 `requirements.txt` (5行)

```txt
langgraph
langchain-community
python-dotenv
google-genai
```

#### 逐行解析

**第1行: `langgraph`**
- **作用**: LangGraph 是 LangChain 生态的核心组件,用于构建有状态的多步骤应用
- **功能**: 提供 `StateGraph`、`ToolNode`、`MemorySaver` 等核心类
- **为何需要**: 管理代理的状态流转和工具调用逻辑

**第2行: `langchain-community`**
- **作用**: LangChain 社区维护的扩展包
- **功能**: 提供额外的工具、向量存储、文档加载器等
- **为何需要**: 虽然本项目主要依赖 `langchain-core`,但社区包可能被其他依赖隐式需要

**第3行: `python-dotenv`**
- **作用**: 从 `.env` 文件加载环境变量
- **功能**: 使用 `load_dotenv()` 函数读取配置
- **为何需要**: 安全地管理 API 密钥,避免硬编码

**第4行: `google-genai`**
- **作用**: Google 官方的 Generative AI Python SDK
- **功能**: 提供 `genai.Client`、`types.Content` 等与 Gemini API 交互的类
- **为何需要**: 这是调用 Gemini 2.5 Flash 模型的核心库

**第5行: (空行)**
- 标准的文件结束符,符合 POSIX 标准

---

## 环境配置

### 📄 `.env` (该API_KEY已弃用)

```env
GEMINI_API_KEY=AIzaSyCH257-Hn30gQOKDfHVwGgPICZ5IjO8DCU
```

#### 逐行解析

**第1行: `GEMINI_API_KEY=...`**
- **格式**: 键值对,`KEY=VALUE`
- **密钥来源**: 从 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取
- **安全性**: 
  - ⚠️ **警告**: 这是真实的API密钥,应该加入 `.gitignore`
  - 建议使用环境变量或密钥管理服务(如 Google Secret Manager)
- **作用域**: 该密钥用于所有 Gemini API 请求的身份验证

**第2行: (空行)**

### 🔐 安全建议

```bash
# 将 .env 加入 .gitignore
echo ".env" >> .gitignore

# 或使用环境变量(推荐)
export GEMINI_API_KEY="your-api-key-here"
```

---

## 工具定义

### 📄 `src/tools.py` (28行)

此文件定义了代理可以调用的工具函数。关键点:
1. 定义原始 Python 函数(供 Gemini SDK 使用)
2. 包装为 LangChain 工具(供 ToolNode 执行)

#### 完整代码逐行解析

```python
# 第1行: 导入LangChain工具装饰器
from langchain_core.tools import tool
```
- `tool` 是一个装饰器,将普通函数转换为 LangChain 可识别的工具
- 来自 `langchain-core` 包(会自动安装)

---

```python
# 第3行: 注释 - 区分两种定义方式
# 1. Define raw functions (for google-genai SDK)
```
- **设计模式**: 双重定义
  - 原始函数 → Gemini 理解工具签名
  - LangChain 工具 → ToolNode 执行

---

```python
# 第4-14行: 计算器工具函数
def calculator_func(expression: str) -> str:
    """
    Useful for performing mathematical calculations.
    The input should be a valid mathematical expression as a string.
    Example: "5 + 5" or "10 * 2"
    """
    try:
        # WARNING: eval is dangerous in production. Use with caution or replace with a safer parser.
        return str(eval(expression))
    except Exception as e:
        return f"Error calculating: {e}"
```

**第4行: 函数签名**
```python
def calculator_func(expression: str) -> str:
```
- **函数名**: `calculator_func` (必须与 Gemini 调用的名称一致)
- **参数**: `expression: str` - 数学表达式字符串
  - 类型提示 `str` 帮助 Gemini 理解参数类型
- **返回值**: `str` - 计算结果或错误信息

**第5-9行: 文档字符串(Docstring)**
```python
"""
Useful for performing mathematical calculations.
The input should be a valid mathematical expression as a string.
Example: "5 + 5" or "10 * 2"
"""
```
- **重要性**: Gemini 会读取这个描述来决定何时调用此工具!
- **内容结构**:
  1. 功能描述 - "Useful for..."
  2. 参数说明 - "The input should be..."
  3. 示例 - "Example: ..."
- **最佳实践**: 清晰描述工具的用途和使用方法

**第10-14行: 实现逻辑**
```python
try:
    # WARNING: eval is dangerous in production
    return str(eval(expression))
except Exception as e:
    return f"Error calculating: {e}"
```
- **第12行**: `eval(expression)` - 执行字符串中的Python表达式
  - ⚠️ **安全警告**: `eval()` 可以执行任意代码,生产环境应使用 `ast.literal_eval()` 或 `sympy`
  - 示例: `eval("2+3")` → `5`
- **第13行**: `str()` - 将结果转换为字符串
- **第14行**: 异常处理 - 捕获语法错误等异常

---

```python
# 第16-21行: 搜索工具函数
def search_func(query: str) -> str:
    """
    Useful for searching for information on the internet.
    """
    # Mock implementation for demonstration
    return f"Mock search results for: {query}. The weather is sunny."
```

**第16行: 函数签名**
```python
def search_func(query: str) -> str:
```
- **参数**: `query` - 搜索查询字符串

**第17-19行: Docstring**
- 简洁描述工具用途
- Gemini 根据 "searching for information" 判断何时使用

**第20-21行: 模拟实现**
```python
# Mock implementation for demonstration
return f"Mock search results for: {query}. The weather is sunny."
```
- **当前状态**: 仅返回模拟数据
- **生产环境建议**: 集成真实搜索 API
  - Google Custom Search API
  - Bing Search API
  - DuckDuckGo API (免费)

---

```python
# 第23-27行: 创建 LangChain 工具
# 2. Create LangChain tools (for ToolNode)
# IMPORTANT: Name them exactly as the function name so Gemini mapping is 1:1
calculator = tool("calculator_func")(calculator_func)
search = tool("search_func")(search_func)
```

**第26行: 包装计算器工具**
```python
calculator = tool("calculator_func")(calculator_func)
```
- **分解理解**:
  1. `tool("calculator_func")` - 创建一个装饰器,指定工具名称
  2. `(calculator_func)` - 将装饰器应用到原始函数
  3. 结果: `calculator` 对象可被 ToolNode 识别

- **关键设计决策**: 名称必须一致!
  - Gemini 调用 `calculator_func`
  - ToolNode 查找名为 `calculator_func` 的工具
  - 如果不匹配会导致 "Tool not found" 错误

**第27行: 包装搜索工具**
```python
search = tool("search_func")(search_func)
```
- 同样的模式应用于搜索工具

---

### 🎯 工具设计模式总结

```mermaid
graph LR
    A[原始函数<br/>calculator_func] -->|Gemini读取签名| B[Gemini理解工具]
    A -->|tool装饰器| C[LangChain工具<br/>calculator]
    C -->|ToolNode执行| D[返回结果]
    B -->|决策调用| D
```

---

## 核心图架构

### 📄 `src/graph.py` (176行)

这是项目的核心文件,定义了整个代理的状态管理和执行流程。

#### 第1-12行: 导入和初始化

```python
import os
from typing import TypedDict, Annotated, Sequence, Any
import operator
from google import genai
from google.genai import types
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from .tools import calculator, search, calculator_func, search_func

load_dotenv()
```

**逐行解析**:

**第1行**: `import os`
- 用于访问环境变量 `os.getenv()`

**第2行**: `from typing import TypedDict, Annotated, Sequence, Any`
- `TypedDict` - 创建带类型提示的字典类(Python 3.8+)
- `Annotated` - 添加元数据到类型(用于状态合并逻辑)
- `Sequence` - 通用序列类型(列表、元组等)
- `Any` - 任意类型

**第3行**: `import operator`
- 提供 `operator.add` 函数,用于状态累加

**第4-5行**: Gemini SDK 导入
```python
from google import genai
from google.genai import types
```
- `genai.Client` - API 客户端
- `types.Content`, `types.Part` - 消息格式类

**第6行**: LangChain 消息类型
```python
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
```
- `HumanMessage` - 用户消息
- `AIMessage` - AI响应(可包含工具调用)
- `ToolMessage` - 工具执行结果
- `BaseMessage` - 基类

**第7行**: LangGraph 核心组件
```python
from langgraph.graph import StateGraph, END
```
- `StateGraph` - 状态图构建器
- `END` - 特殊节点,表示流程结束

**第8行**: `from langgraph.prebuilt import ToolNode`
- `ToolNode` - 预构建的工具执行节点

**第10行**: 导入工具
```python
from .tools import calculator, search, calculator_func, search_func
```
- `calculator`, `search` - LangChain工具(给ToolNode)
- `calculator_func`, `search_func` - 原始函数(给Gemini)

**第12行**: `load_dotenv()`
- 从 `.env` 文件加载环境变量到 `os.environ`

---

#### 第14-16行: 状态定义

```python
# 1. Define State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
```

**深度解析**:

**为什么需要状态?**
- LangGraph 是有状态的图,每个节点都接收和返回状态
- 状态在节点间传递和累积

**AgentState 结构**:
```python
{
    "messages": [HumanMessage(...), AIMessage(...), ToolMessage(...), ...]
}
```

**`Annotated[Sequence[BaseMessage], operator.add]` 详解**:
- `Sequence[BaseMessage]` - 消息列表的类型
- `operator.add` - 合并策略
  - 当节点返回 `{"messages": [new_msg]}` 时
  - LangGraph 会执行 `state["messages"] = state["messages"] + [new_msg]`
  - 这样消息历史会自动累积!

**示例流程**:
```python
# 初始状态
state = {"messages": [HumanMessage(content="Hello")]}

# 节点1返回
node1_output = {"messages": [AIMessage(content="Hi!")]}

# 合并后 (自动执行)
state = {"messages": [HumanMessage("Hello"), AIMessage("Hi!")]}
```

---

#### 第18-26行: 初始化 Gemini 客户端

```python
# 2. Initialize Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found.")

client = genai.Client(api_key=api_key)
```

**逐行解析**:

**第19行**: `api_key = os.getenv("GEMINI_API_KEY")`
- 尝试读取 `GEMINI_API_KEY`
- 如果不存在返回 `None`

**第20-21行**: 备用密钥
```python
if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")
```
- 兼容性设计: 同时支持两种命名方式

**第23-24行**: 验证
```python
if not api_key:
    raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found.")
```
- **快速失败**: 如果缺少密钥,立即抛出异常
- 避免后续神秘错误

**第26行**: `client = genai.Client(api_key=api_key)`
- 创建 Gemini API 客户端实例
- 所有 API 调用都通过此客户端

---

#### 第28-30行: 工具列表

```python
# 3. Define Tools
gemini_tools = [calculator_func, search_func]
langchain_tools = [calculator, search]
```

**双列表设计**:

1. **`gemini_tools`** (原始函数)
   - 传给 `client.models.generate_content(tools=...)`
   - Gemini 通过函数签名和 docstring 理解工具

2. **`langchain_tools`** (LangChain 工具)
   - 传给 `ToolNode(langchain_tools)`
   - 用于实际执行工具调用

---

#### 第32-79行: 消息格式转换函数

这是整个项目最复杂的部分!

```python
def convert_messages(messages: Sequence[BaseMessage]) -> list[types.Content]:
```

**为什么需要转换?**
- LangChain 使用自己的消息格式 (`HumanMessage`, `AIMessage`)
- Gemini SDK 需要 `types.Content` 格式
- 必须在两者之间转换

**函数签名**:
- **输入**: `Sequence[BaseMessage]` - LangChain 消息列表
- **输出**: `list[types.Content]` - Gemini 消息列表

**代码逐段解析**:

```python
contents = []
for msg in messages:
```
- 初始化空列表,遍历每条消息

---

**处理用户消息 (第36-40行)**:
```python
if isinstance(msg, HumanMessage):
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=msg.content)]
    ))
```

**转换流程**:
```python
# LangChain 格式
HumanMessage(content="Hello")

# ↓ 转换为 ↓

# Gemini 格式
types.Content(
    role="user",
    parts=[types.Part.from_text(text="Hello")]
)
```

**关键点**:
- `role="user"` - 用户角色
- `parts` - 消息可以包含多个部分(文本、图片等)
- `types.Part.from_text()` - 创建文本部分

---

**处理 AI 消息 (第41-56行)**:
```python
elif isinstance(msg, AIMessage):
    parts = []
    if msg.content:
        parts.append(types.Part.from_text(text=msg.content))
    if msg.tool_calls:
        for tc in msg.tool_calls:
            parts.append(types.Part.from_function_call(
                name=tc['name'],
                args=tc['args']
            ))
    contents.append(types.Content(
        role="model",
        parts=parts
    ))
```

**复杂场景处理**:

1. **纯文本响应**:
```python
AIMessage(content="The answer is 42")
→
types.Content(role="model", parts=[Part(text="The answer is 42")])
```

2. **带工具调用**:
```python
AIMessage(
    content="",
    tool_calls=[{
        "name": "calculator_func",
        "args": {"expression": "2+2"}
    }]
)
→
types.Content(
    role="model",
    parts=[Part(function_call=FunctionCall(name="calculator_func", args={"expression": "2+2"}))]
)
```

**第45-52行: 工具调用转换**
```python
if msg.tool_calls:
    for tc in msg.tool_calls:
        parts.append(types.Part.from_function_call(
            name=tc['name'],
            args=tc['args']
        ))
```
- `tc['name']` - 工具名称 (如 "calculator_func")
- `tc['args']` - 工具参数字典
- `types.Part.from_function_call()` - 创建函数调用部分

---

**处理工具结果 (第57-77行)**:
```python
elif isinstance(msg, ToolMessage):
    parts = [types.Part.from_function_response(
        name=msg.name,
        response={"result": msg.content}
    )]
    contents.append(types.Content(
        role="user",
        parts=parts
    ))
```

**转换示例**:
```python
# LangChain 格式
ToolMessage(
    name="calculator_func",
    content="4"
)

# ↓ 转换为 ↓

# Gemini 格式
types.Content(
    role="user",  # 注意: 工具响应的 role 是 "user"!
    parts=[Part(function_response=FunctionResponse(
        name="calculator_func",
        response={"result": "4"}
    ))]
)
```

**关键设计点**:
- **第75行**: `role="user"` - 工具结果以"用户"角色发送
  - 这是 Gemini API 的要求
  - 代表"环境"返回的信息
- **第72行**: `response={"result": msg.content}`
  - 包装为字典格式
  - Gemini 期望结构化响应

---

#### 第81-138行: 核心节点 - call_model

```python
def call_model(state: AgentState):
```

**作用**: 调用 Gemini 模型生成响应

**完整流程解析**:

```python
messages = state['messages']
```
- 从状态中提取消息历史

```python
gemini_contents = convert_messages(messages)
```
- 转换为 Gemini 格式

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=gemini_contents,
    config=types.GenerateContentConfig(
        tools=gemini_tools
    )
)
```

**API 调用详解**:

**第91行**: `model="gemini-2.5-flash"`
- **模型选择**: Gemini 2.5 Flash
- **特点**: 快速、低成本、支持函数调用
- **替代选项**: `gemini-2.0-flash`, `gemini-1.5-pro`

**第92行**: `contents=gemini_contents`
- 完整的对话历史
- Gemini 会考虑所有历史上下文

**第93-95行**: 工具配置
```python
config=types.GenerateContentConfig(
    tools=gemini_tools
)
```
- 告诉 Gemini 可用的工具
- Gemini 会根据用户请求决定是否调用

---

**响应解析 (第98-136行)**:

```python
tool_calls = []
content = ""

if response.candidates and response.candidates[0].content.parts:
    for part in response.candidates[0].content.parts:
        if part.text:
            content += part.text
        if part.function_call:
            fn_name = part.function_call.name
            tool_calls.append({
                "name": fn_name,
                "args": part.function_call.args,
                "id": "call_" + fn_name
            })
```

**响应结构**:
```
response
└── candidates (列表)
    └── [0] (第一个候选)
        └── content
            └── parts (列表)
                ├── Part(text="...") ← 文本响应
                └── Part(function_call=...) ← 工具调用
```

**第104-105行: 提取文本**
```python
if part.text:
    content += part.text
```
- 累积所有文本部分
- 多个文本部分会拼接

**第106-136行: 提取工具调用**
```python
if part.function_call:
    fn_name = part.function_call.name
    tool_calls.append({
        "name": fn_name,
        "args": part.function_call.args,
        "id": "call_" + fn_name
    })
```

**工具调用格式**:
```python
{
    "name": "calculator_func",
    "args": {"expression": "10 * 2"},
    "id": "call_calculator_func"
}
```

**第138行: 返回状态更新**
```python
return {"messages": [AIMessage(content=content, tool_calls=tool_calls)]}
```
- 创建 `AIMessage` 包含响应和工具调用
- 返回的字典会合并到状态中(自动累加到 `messages` 列表)

---

#### 第140行: 创建工具节点

```python
tool_node = ToolNode(langchain_tools)
```

**ToolNode 工作原理**:
1. 接收包含 `AIMessage` (带 `tool_calls`) 的状态
2. 查找匹配的工具(通过 `name`)
3. 执行工具函数
4. 返回 `ToolMessage` 结果

**自动化流程**:
```python
# 输入状态
state = {
    "messages": [
        HumanMessage(content="What is 2+2?"),
        AIMessage(content="", tool_calls=[{"name": "calculator_func", "args": {"expression": "2+2"}}])
    ]
}

# ToolNode 自动执行
calculator("2+2") → "4"

# 输出状态
{
    "messages": [
        ...,
        ToolMessage(name="calculator_func", content="4")
    ]
}
```

---

#### 第142-148行: 条件逻辑

```python
def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END
```

**决策逻辑**:
- **如果最后一条消息有工具调用** → 返回 `"tools"` (执行工具)
- **否则** → 返回 `END` (结束对话)

**图流程示例**:
```
[agent节点] → 生成带tool_calls的AIMessage
     ↓
should_continue() → 检测到tool_calls → 返回"tools"
     ↓
[tools节点] → 执行工具 → 返回ToolMessage
     ↓
回到 [agent节点] → 读取工具结果 → 生成最终答案(无tool_calls)
     ↓
should_continue() → 无tool_calls → 返回END
     ↓
[结束]
```

---

#### 第150-175行: 构建图

```python
workflow = StateGraph(AgentState)
```
- 创建状态图,指定状态类型

```python
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
```
- 添加两个节点:
  1. `agent` - AI 决策节点
  2. `tools` - 工具执行节点

```python
workflow.set_entry_point("agent")
```
- 设置入口点: 总是从 `agent` 开始

```python
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)
```

**条件边详解**:
- **源节点**: `"agent"`
- **条件函数**: `should_continue`
- **映射**:
  - 如果返回 `"tools"` → 跳转到 `tools` 节点
  - 如果返回 `END` → 结束

```python
workflow.add_edge("tools", "agent")
```
- 固定边: `tools` 节点执行完后总是返回 `agent`

**完整图结构**:
```mermaid
graph TD
    Start([开始]) --> Agent[agent节点<br/>调用Gemini]
    Agent -->|有工具调用| Tools[tools节点<br/>执行工具]
    Tools --> Agent
    Agent -->|无工具调用| End([结束])
```

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)
```

**第174行**: `checkpointer = MemorySaver()`
- 内存检查点器: 在会话期间保存状态
- **作用**: 支持多轮对话,记住历史

**第175行**: `app = workflow.compile(checkpointer=checkpointer)`
- 编译图为可执行应用
- 传入检查点器启用记忆功能

---

## 主程序入口

### 📄 `main.py` (47行)

用户交互层,提供命令行接口。

#### 完整代码逐行解析

```python
# 第1-3行: 导入
import sys
from langchain_core.messages import HumanMessage
from src.graph import app
```

**第1行**: `import sys`
- 虽然导入了但未使用(可能用于未来扩展)

**第2行**: `from langchain_core.messages import HumanMessage`
- 创建用户消息对象

**第3行**: `from src.graph import app`
- 导入编译好的 LangGraph 应用

---

```python
# 第5-8行: main函数开始
def main():
    print("Initializing LangGraph Agent with Gemini...")
    print("Type 'exit' to quit.")
    print("-" * 50)
```
- 打印欢迎信息和分隔线

---

```python
# 第10-11行: 配置线程ID
config = {"configurable": {"thread_id": "1"}}
```

**关键配置**:
- `thread_id` - 会话标识符
- **作用**: MemorySaver 使用此 ID 保存/加载状态
- **多会话支持**: 不同 `thread_id` 可以并行维护多个独立对话

---

```python
# 第13-21行: 主循环
while True:
    try:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        if not user_input.strip():
            continue
```

**第15行**: `user_input = input("You: ")`
- 阻塞等待用户输入

**第16-18行**: 退出检查
- 输入 "exit" 或 "quit" 则跳出循环

**第20-21行**: 空输入过滤
- `strip()` 移除首尾空格
- 如果输入为空则继续下一轮

---

```python
# 第23-24行: 构建输入
inputs = {"messages": [HumanMessage(content=user_input)]}
```

**输入格式**:
```python
{
    "messages": [
        HumanMessage(content="用户输入的文本")
    ]
}
```
- 这会被累加到现有状态的 `messages` 列表

---

```python
# 第26-37行: 流式执行
print("Agent is thinking...")
for output in app.stream(inputs, config=config):
    for key, value in output.items():
        print(f"Node '{key}':")
        if "messages" in value and value["messages"]:
            last_msg = value["messages"][-1]
            if hasattr(last_msg, "content") and last_msg.content:
                print(last_msg.content)
            elif hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                print(f"Calling Tool: {last_msg.tool_calls[0]['name']}")
        print("---")
```

**第27行**: `app.stream(inputs, config=config)`
- **流式执行**: 每个节点完成后立即返回
- **参数**:
  - `inputs` - 新消息
  - `config` - 包含 `thread_id` 的配置

**返回格式**:
```python
# 每次迭代返回一个字典
{
    "agent": {
        "messages": [AIMessage(...)]
    }
}
# 或
{
    "tools": {
        "messages": [ToolMessage(...)]
    }
}
```

**第28-37行: 输出处理**
```python
for key, value in output.items():
    print(f"Node '{key}':")  # 打印节点名称
```

**第31-36行: 提取消息内容**
```python
if "messages" in value and value["messages"]:
    last_msg = value["messages"][-1]
    if hasattr(last_msg, "content") and last_msg.content:
        print(last_msg.content)
    elif hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        print(f"Calling Tool: {last_msg.tool_calls[0]['name']}")
```

**逻辑**:
1. 获取节点返回的最后一条消息
2. 如果有文本内容 → 打印内容
3. 如果有工具调用 → 打印工具名称

**示例输出**:
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
--------------------------------------------------
```

---

```python
# 第39行: 分隔线
print("-" * 50)
```

---

```python
# 第41-43行: 异常处理
except Exception as e:
    print(f"An error occurred: {e}")
    print("Did you set your GEMINI_API_KEY in .env?")
```
- 捕获所有异常
- 提示检查 API 密钥

---

```python
# 第45-46行: 程序入口
if __name__ == "__main__":
    main()
```
- 标准 Python 入口点检查
- 只有直接运行此文件时才执行 `main()`

---

