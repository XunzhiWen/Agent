# LangGraph Gemini Agent - 详细技术指南 (续)

> 这是技术指南的第二部分,包含调试脚本、工作流程详解、最佳实践等内容

## 调试脚本

### 📄 `debug_models.py` (21行)

用于测试 API 连接并列出可用的 Gemini 模型。

#### 完整代码逐行解析

```python
# 第1-3行: 导入
import os
import google.generativeai as genai
from dotenv import load_dotenv
```

**第1行**: `import os`
- 用于访问环境变量

**第2行**: `import google.generativeai as genai`
- 这是 **旧版** Google AI SDK (`google-generativeai` 包)
- 与项目主代码使用的 `google-genai` **不同**!
- **重要区别**:
  - 旧版: `import google.generativeai as genai`
  - 新版: `from google import genai`
- **注意**: 本项目主代码使用新版 SDK

**第3行**: `from dotenv import load_dotenv`
- 从 `.env` 文件加载环境变量

---

```python
# 第5-6行: 加载环境变量
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
```

**第5行**: `load_dotenv()`
- 读取项目根目录的 `.env` 文件
- 将键值对加载到 `os.environ`

**第7行**: `api_key = os.getenv("GOOGLE_API_KEY")`
- 读取 `GOOGLE_API_KEY` (注意不是 `GEMINI_API_KEY`)
- 这个脚本使用旧的命名约定

---

```python
# 第8-10行: 验证密钥
if not api_key:
    print("Error: GOOGLE_API_KEY not found.")
    exit(1)
```

**第8行**: `if not api_key:`
- 检查密钥是否存在

**第9-10行**: 错误处理
- 打印错误信息
- `exit(1)` - 以错误代码1退出程序 (非零表示错误)

---

```python
# 第12行: 配置 SDK
genai.configure(api_key=api_key)
```

**配置方式对比**:

| 旧版 SDK (本脚本) | 新版 SDK (主代码) |
|------------------|------------------|
| `genai.configure(api_key=...)` | `client = genai.Client(api_key=...)` |
| 全局配置 | 实例化客户端 |

---

```python
# 第14-21行: 列出模型
print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
```

**第16行**: `genai.list_models()`
- 获取所有可用模型
- 返回模型对象的迭代器

**第17行**: 过滤条件
```python
if 'generateContent' in m.supported_generation_methods:
```
- **作用**: 只显示支持文本生成的模型
- **过滤掉**: 
  - 嵌入模型 (如 `embedding-001`)
  - 图像生成模型
  - 其他专用模型

**第18行**: `print(m.name)`
- 打印符合条件的模型名称

**示例输出**:
```
Listing available models...
models/gemini-1.0-pro
models/gemini-1.0-pro-001
models/gemini-1.0-pro-latest
models/gemini-1.5-pro
models/gemini-1.5-pro-001
models/gemini-1.5-pro-latest
models/gemini-1.5-flash
models/gemini-1.5-flash-001
models/gemini-1.5-flash-latest
models/gemini-2.0-flash-exp
models/gemini-2.5-flash
```

**第19-20行**: 异常处理
- 捕获网络错误、认证错误等
- 打印友好的错误信息

---

### 📄 `debug_gemini.py` (37行)

测试 Gemini 工具调用功能,验证工具配置是否正确。

#### 完整代码逐行解析

```python
# 第1-5行: 导入
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.tools import calculator_func, search_func
```

**第2-3行**: 使用新版 SDK
```python
from google import genai
from google.genai import types
```
- ✅ **正确**: 与主项目代码一致
- 这是 `google-genai` 包的导入方式

**第5行**: `from src.tools import calculator_func, search_func`
- 导入原始工具函数
- 这些函数将传给 Gemini API

---

```python
# 第7-12行: API密钥加载
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: API Key not found")
    exit(1)
```

**第9行**: 优雅的备用逻辑
```python
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
```

**工作原理**:
- Python 的 **短路求值**
- 如果第一个值为真 → 返回第一个值
- 如果第一个值为假 (None) → 返回第二个值
- 同时支持两种环境变量命名

**等价代码**:
```python
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")
```

---

```python
# 第14-16行: 初始化客户端和工具
client = genai.Client(api_key=api_key)

gemini_tools = [calculator_func, search_func]
```

**第14行**: `client = genai.Client(api_key=api_key)`
- 创建客户端实例 (新版 SDK)

**第16行**: `gemini_tools = [calculator_func, search_func]`
- 将原始函数传给 Gemini
- Gemini 会自动解析函数签名和 docstring

---

```python
# 第18-37行: 测试工具调用
print("Calling Gemini with tool...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Search for the weather in Timbuktu",
        config=types.GenerateContentConfig(
            tools=gemini_tools
        )
    )
    print("\n--- Response ---")
    print(response)
    print("\n--- Parts ---")
    if response.candidates:
        for part in response.candidates[0].content.parts:
            print(f"Part: {part}")
            if part.function_call:
                print(f"Function Call: {part.function_call}")
except Exception as e:
    print(f"Error: {e}")
```

#### 测试用例分析

**第22行**: 测试输入
```python
contents="Search for the weather in Timbuktu"
```

**为什么选择这个输入?**
- 包含关键词 "Search for"
- 应该触发 `search_func` 工具
- Timbuktu (廷巴克图) 是一个真实地点,测试搜索功能

**预期 Gemini 行为**:
1. 读取 `search_func` 的 docstring: "Useful for searching for information on the internet."
2. 识别用户意图: 需要搜索信息
3. 决定调用 `search_func(query="weather in Timbuktu")`

---

#### 输出分析

**第27-28行**: 打印完整响应
```python
print("\n--- Response ---")
print(response)
```

**示例输出**:
```
--- Response ---
GenerateContentResponse(
    candidates=[
        Candidate(
            content=Content(
                role='model',
                parts=[
                    Part(function_call=FunctionCall(
                        name='search_func',
                        args={'query': 'weather in Timbuktu'}
                    ))
                ]
            ),
            finish_reason=FinishReason.STOP
        )
    ]
)
```

---

**第29-33行**: 详细解析 Parts
```python
print("\n--- Parts ---")
if response.candidates:
    for part in response.candidates[0].content.parts:
        print(f"Part: {part}")
        if part.function_call:
            print(f"Function Call: {part.function_call}")
```

**示例输出**:
```
--- Parts ---
Part: function_call {
  name: "search_func"
  args {
    fields {
      key: "query"
      value {
        string_value: "weather in Timbuktu"
      }
    }
  }
}
Function Call: name: "search_func"
args {
  fields {
    key: "query"
    value {
      string_value: "weather in Timbuktu"
    }
  }
}
```

---

#### 调试价值

| 调试目的 | 验证点 |
|---------|-------|
| **工具识别** | Gemini 是否正确识别 `search_func`? |
| **参数提取** | `args` 中的 `query` 参数是否正确? |
| **隔离测试** | 不涉及 LangGraph,纯 API 调用 |
| **错误诊断** | 如果主程序出错,这里可以定位是否是 API 问题 |

---

## 工作流程详解

### 🔄 完整对话流程

让我们通过一个具体例子**深入理解**整个系统的运作:

**用户输入**: "What is 15 * 8?"

---

### 阶段1: 用户输入处理

**执行位置**: `main.py` 第24行

```python
inputs = {"messages": [HumanMessage(content="What is 15 * 8?")]}
```

**初始状态构建**:
```python
state = {
    "messages": [
        HumanMessage(content="What is 15 * 8?")
    ]
}
```

**状态类型**: `AgentState` (TypedDict)

---

### 阶段2: Agent 节点 - 第一次调用

**执行**: `call_model(state)`

#### 步骤 2.1: 消息转换

```python
gemini_contents = convert_messages(state['messages'])
```

**转换结果**:
```python
[
    types.Content(
        role="user",
        parts=[types.Part.from_text(text="What is 15 * 8?")]
    )
]
```

**可视化**:
```
LangChain格式          →          Gemini格式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HumanMessage           →          Content
├─ content: "..."      →          ├─ role: "user"
                                  └─ parts: [Part(text="...")]
```

---

#### 步骤 2.2: 调用 Gemini API

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=gemini_contents,
    config=types.GenerateContentConfig(tools=[calculator_func, search_func])
)
```

**API 请求结构**:
```json
{
  "model": "gemini-2.5-flash",
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "What is 15 * 8?"}]
    }
  ],
  "tools": [
    {
      "function_declarations": [
        {
          "name": "calculator_func",
          "description": "Useful for performing mathematical calculations...",
          "parameters": {
            "type": "object",
            "properties": {
              "expression": {"type": "string"}
            }
          }
        },
        {
          "name": "search_func",
          "description": "Useful for searching for information...",
          "parameters": {
            "type": "object", 
            "properties": {
              "query": {"type": "string"}
            }
          }
        }
      ]
    }
  ]
}
```

---

#### 步骤 2.3: Gemini 内部推理

**Gemini 的思考过程** (内部,不可见):

1. **意图识别**:
   - 分析: "What is 15 * 8?"
   - 识别: 这是一个数学计算请求

2. **工具匹配**:
   - 检查 `calculator_func` docstring: "Useful for performing mathematical calculations"
   - ✅ 匹配度高!
   - 检查 `search_func` docstring: "Useful for searching for information"
   - ❌ 不匹配

3. **决策**:
   - 不直接回答 (虽然 Gemini 知道答案是 120)
   - 选择调用工具以展示工具使用能力
   - 构造函数调用: `calculator_func(expression="15 * 8")`

---

#### 步骤 2.4: Gemini 响应

```python
response.candidates[0].content.parts = [
    Part(function_call=FunctionCall(
        name="calculator_func",
        args={"expression": "15 * 8"}
    ))
]
```

**响应结构**:
```
response
└── candidates: [...]
    └── [0]
        ├── content
        │   ├── role: "model"
        │   └── parts: [Part(function_call=...)]
        └── finish_reason: STOP
```

---

#### 步骤 2.5: call_model 处理响应

```python
tool_calls = []
content = ""

for part in response.candidates[0].content.parts:
    if part.function_call:
        fn_name = part.function_call.name  # "calculator_func"
        tool_calls.append({
            "name": fn_name,
            "args": part.function_call.args,  # {"expression": "15 * 8"}
            "id": "call_calculator_func"
        })

return {"messages": [AIMessage(content="", tool_calls=tool_calls)]}
```

**返回值**:
```python
{
    "messages": [
        AIMessage(
            content="",
            tool_calls=[{
                "name": "calculator_func",
                "args": {"expression": "15 * 8"},
                "id": "call_calculator_func"
            }]
        )
    ]
}
```

---

#### 步骤 2.6: 状态自动合并

**LangGraph 自动执行**:
```python
# 由于 Annotated[..., operator.add]
state["messages"] = state["messages"] + returned_messages

# 结果
state = {
    "messages": [
        HumanMessage(content="What is 15 * 8?"),           # 原有
        AIMessage(content="", tool_calls=[...])             # 新增!
    ]
}
```

---

### 阶段3: 条件判断 - 第一次

**执行**: `should_continue(state)`

```python
def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]  # AIMessage(tool_calls=[...])
    
    if last_message.tool_calls:  # True! (列表非空)
        return "tools"
    return END
```

**决策**: 返回 `"tools"` → 跳转到 `tools` 节点

---

### 阶段4: Tools 节点 - 执行工具

**执行**: `tool_node(state)`

#### ToolNode 内部工作流程

**步骤 4.1**: 提取工具调用
```python
ai_msg = state["messages"][-1]  # AIMessage
tool_call = ai_msg.tool_calls[0]  # {"name": "calculator_func", ...}
```

**步骤 4.2**: 查找工具
```python
tool_name = tool_call["name"]  # "calculator_func"
# 在 langchain_tools 中查找名为 "calculator_func" 的工具
tool = find_tool_by_name(langchain_tools, tool_name)
# 找到: calculator 工具
```

**步骤 4.3**: 执行工具
```python
# ToolNode 调用
result = tool.invoke(tool_call["args"])

# 内部流程
calculator.invoke({"expression": "15 * 8"})
└─> calculator_func("15 * 8")
    └─> str(eval("15 * 8"))
        └─> str(120)
            └─> "120"
```

**执行链**:
```
ToolNode
  → calculator (LangChain 工具)
    → calculator_func (原始 Python 函数)
      → eval("15 * 8")
        → 120
          → "120" (字符串)
```

---

#### 步骤 4.4: 构造 ToolMessage

```python
tool_message = ToolMessage(
    name="calculator_func",
    content="120",
    tool_call_id="call_calculator_func"
)
```

**字段说明**:
- `name`: 必须匹配函数名,Gemini 需要知道这是哪个工具的结果
- `content`: 工具执行结果
- `tool_call_id`: 关联到之前的工具调用

---

#### 步骤 4.5: 返回结果

```python
return {"messages": [tool_message]}
```

**状态更新** (自动合并):
```python
state = {
    "messages": [
        HumanMessage(content="What is 15 * 8?"),
        AIMessage(content="", tool_calls=[...]),
        ToolMessage(name="calculator_func", content="120")  # 新增!
    ]
}
```

---

### 阶段5: 返回 Agent 节点 - 第二次调用

**图流转**: `tools` 节点通过固定边返回 `agent` 节点

**执行**: `call_model(state)` (再次调用)

---

#### 步骤 5.1: 消息转换 (完整历史)

```python
gemini_contents = convert_messages(state['messages'])
```

**转换结果**:
```python
[
    types.Content(
        role="user",
        parts=[Part.from_text(text="What is 15 * 8?")]
    ),
    types.Content(
        role="model",
        parts=[Part.from_function_call(
            name="calculator_func",
            args={"expression": "15 * 8"}
        )]
    ),
    types.Content(
        role="user",  # 注意: 工具结果的 role 是 "user"!
        parts=[Part.from_function_response(
            name="calculator_func",
            response={"result": "120"}
        )]
    )
]
```

**关键点**: 完整的三轮对话历史!

---

#### 步骤 5.2: 调用 Gemini (带历史)

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=gemini_contents,  # 完整历史!
    config=types.GenerateContentConfig(tools=gemini_tools)
)
```

**Gemini 看到的上下文**:
1. 用户问: "What is 15 * 8?"
2. 我 (Gemini) 调用了: `calculator_func("15 * 8")`
3. 工具返回了: "120"
4. 现在我需要: 给用户一个自然语言回复

---

#### 步骤 5.3: Gemini 响应 (最终答案)

```python
response.candidates[0].content.parts = [
    Part(text="15 multiplied by 8 equals 120.")
]
```

**注意**: 这次没有 `function_call`! 只有文本。

---

#### 步骤 5.4: call_model 处理

```python
tool_calls = []  # 空列表!
content = "15 multiplied by 8 equals 120."

return {"messages": [AIMessage(content=content, tool_calls=[])]}
```

**状态更新**:
```python
state = {
    "messages": [
        HumanMessage(content="What is 15 * 8?"),
        AIMessage(content="", tool_calls=[...]),
        ToolMessage(name="calculator_func", content="120"),
        AIMessage(content="15 multiplied by 8 equals 120.", tool_calls=[])  # 新增!
    ]
}
```

---

### 阶段6: 条件判断 - 第二次

**执行**: `should_continue(state)`

```python
last_message = state["messages"][-1]
# AIMessage(content="...", tool_calls=[])

if last_message.tool_calls:  # False! (空列表)
    return "tools"
return END  # 执行这里!
```

**决策**: 返回 `END` → 对话结束

---

### 阶段7: 用户界面输出

**main.py 的流式输出**:

```
You: What is 15 * 8?
Agent is thinking...
Node 'agent':
Calling Tool: calculator_func
---
Node 'tools':
---
Node 'agent':
15 multiplied by 8 equals 120.
---
--------------------------------------------------
```

**输出解析**:
1. **Node 'agent'**: 第一次调用,决定使用工具
2. **Node 'tools'**: 执行工具 (无可见输出)
3. **Node 'agent'**: 第二次调用,提供最终答案

---

### 📊 完整流程可视化

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant M as main.py
    participant A as Agent节点<br/>(call_model)
    participant G as Gemini API
    participant SC as should_continue
    participant T as Tools节点<br/>(ToolNode)
    participant C as calculator_func

    U->>M: "What is 15 * 8?"
    M->>A: state: [HumanMessage]
    
    Note over A: 第一次调用
    A->>A: convert_messages()
    A->>G: generate_content(history, tools)
    
    Note over G: 分析: 需要计算<br/>决定: 调用 calculator_func
    G-->>A: FunctionCall(calculator_func)
    
    A-->>M: AIMessage(tool_calls=[...])
    M->>SC: 检查最后消息
    
    Note over SC: 有tool_calls → "tools"
    SC-->>M: 返回 "tools"
    
    M->>T: state: [..., AIMessage]
    T->>T: 提取 tool_call
    T->>C: calculator_func("15 * 8")
    C-->>T: "120"
    T-->>M: ToolMessage(content="120")
    
    Note over M: 固定边 → 返回 agent
    
    M->>A: state: [..., ToolMessage]
    
    Note over A: 第二次调用
    A->>A: convert_messages()<br/>(完整历史)
    A->>G: generate_content(完整历史)
    
    Note over G: 读取工具结果<br/>生成自然语言答案
    G-->>A: Part(text="15 multiplied...")
    
    A-->>M: AIMessage(content="...", tool_calls=[])
    M->>SC: 检查最后消息
    
    Note over SC: 无tool_calls → END
    SC-->>M: 返回 END
    
    M->>U: "15 multiplied by 8 equals 120."
```

---

### 🧠 状态演变时间线

| 时间 | 节点 | 操作 | messages 列表内容 |
|-----|------|------|------------------|
| T0 | - | 初始化 | `[]` |
| T1 | main | 用户输入 | `[HumanMessage("What is 15 * 8?")]` |
| T2 | agent | 第一次返回 | `+ [AIMessage(tool_calls=[...])]` |
| T3 | tools | 执行工具 | `+ [ToolMessage(content="120")]` |
| T4 | agent | 第二次返回 | `+ [AIMessage(content="15 multiplied...")]` |
| T5 | - | 结束 | (不变,共4条消息) |

---

### 📈 数据流图

```mermaid
graph TD
    Start[用户输入] -->|HumanMessage| State1[State: 1条消息]
    State1 -->|agent节点| Convert1[convert_messages]
    Convert1 --> GeminiCall1[Gemini API 调用 #1]
    GeminiCall1 -->|FunctionCall| State2[State: 2条消息]
    
    State2 -->|should_continue<br/>→ tools| ToolNode[ToolNode]
    ToolNode -->|执行calculator_func| Result[结果: 120]
    Result --> State3[State: 3条消息]
    
    State3 -->|固定边<br/>→ agent| Convert2[convert_messages<br/>完整历史]
    Convert2 --> GeminiCall2[Gemini API 调用 #2]
    GeminiCall2 -->|Text响应| State4[State: 4条消息]
    
    State4 -->|should_continue<br/>→ END| Output[输出结果]
    
    style State1 fill:#e1f5ff
    style State2 fill:#e1f5ff
    style State3 fill:#e1f5ff
    style State4 fill:#e1f5ff
    style GeminiCall1 fill:#fff4e1
    style GeminiCall2 fill:#fff4e1
    style ToolNode fill:#e8f5e9
```

---

## 最佳实践

### ✅ 生产环境建议

#### 1. 安全性增强

##### 问题: eval() 的危险性

**❌ 当前代码 (tools.py 第12行)**:
```python
return str(eval(expression))  # 危险!
```

**为什么危险?**
```python
# 恶意输入示例
calculator_func("__import__('os').system('rm -rf /')")
# 这会删除系统文件!

calculator_func("open('/etc/passwd').read()")
# 这会读取敏感文件!
```

---

##### 解决方案1: 使用 AST (推荐)

```python
import ast
import operator as op

# 支持的操作符
operators = {
    ast.Add: op.add,       # +
    ast.Sub: op.sub,       # -
    ast.Mult: op.mul,      # *
    ast.Div: op.truediv,   # /
    ast.Pow: op.pow,       # **
    ast.Mod: op.mod,       # %
    ast.FloorDiv: op.floordiv,  # //
    ast.USub: op.neg,      # -x (一元负号)
}

def safe_eval(node):
    """递归求值 AST 节点"""
    if isinstance(node, ast.Num):  # 数字
        return node.n
    elif isinstance(node, ast.BinOp):  # 二元操作
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):  # 一元操作
        operand = safe_eval(node.operand)
        return operators[type(node.op)](operand)
    else:
        raise ValueError(f"Unsupported operation: {type(node)}")

def calculator_func(expression: str) -> str:
    """
    安全的数学计算器,只支持基本算术运算。
    支持: +, -, *, /, **, %, //
    示例: "5 + 5", "10 * 2", "2 ** 3"
    """
    try:
        # 解析表达式
        tree = ast.parse(expression, mode='eval')
        # 求值
        result = safe_eval(tree.body)
        return str(result)
    except (ValueError, KeyError, SyntaxError) as e:
        return f"Error: Invalid expression - {e}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error calculating: {e}"
```

**测试**:
```python
print(calculator_func("2 + 3"))        # "5"
print(calculator_func("10 * 5"))       # "50"
print(calculator_func("2 ** 3"))       # "8"
print(calculator_func("10 / 2"))       # "5.0"
print(calculator_func("os.system('')")) # "Error: Unsupported operation"
```

---

##### 解决方案2: 使用 simpleeval 库

```bash
pip install simpleeval
```

```python
from simpleeval import simple_eval

def calculator_func(expression: str) -> str:
    """
    使用 simpleeval 进行安全计算。
    支持基本数学运算和常见函数 (sin, cos, sqrt 等)。
    """
    try:
        result = simple_eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"
```

**优点**:
- 自动支持数学函数
- 可自定义允许的函数和变量
- 性能优秀

---

##### 解决方案3: 使用 sympy (高级数学)

```bash
pip install sympy
```

```python
from sympy import sympify, SympifyError
from sympy.parsing.sympy_parser import parse_expr

def calculator_func(expression: str) -> str:
    """
    使用 SymPy 进行符号计算。
    支持复杂数学表达式和符号运算。
    """
    try:
        result = sympify(expression)
        # 如果是数值表达式,求值
        if result.is_number:
            return str(float(result))
        # 否则返回符号表达式
        return str(result)
    except (SympifyError, ValueError) as e:
        return f"Error: Invalid expression - {e}"
```

---

#### 2. 环境变量管理

**❌ 不安全做法**:
```python
# .env 文件提交到 Git
GEMINI_API_KEY=AIzaSyCH257-Hn30gQOKDfHVwGgPICZ5IjO8DCU
```

**✅ 安全做法**:

##### 步骤1: .gitignore
```bash
# .gitignore
.env
.env.local
.env.*.local
*.key
```

##### 步骤2: 环境变量模板
```bash
# .env.example (提交到 Git)
GEMINI_API_KEY=your-api-key-here
GOOGLE_API_KEY=your-api-key-here

# 说明
# 从 https://makersuite.google.com/app/apikey 获取 API 密钥
```

##### 步骤3: 文档说明
```markdown
# 设置步骤

1. 复制环境变量模板:
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件,填入你的 API 密钥

3. 运行程序:
   ```bash
   python main.py
   ```
```

---

##### 生产环境: 使用密钥管理服务

**Google Secret Manager**:
```python
from google.cloud import secretmanager

def get_api_key(project_id: str, secret_id: str) -> str:
    """从 Google Secret Manager 获取密钥"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# 使用
api_key = get_api_key("my-project", "gemini-api-key")
client = genai.Client(api_key=api_key)
```

**AWS Secrets Manager**:
```python
import boto3
import json

def get_api_key(secret_name: str, region_name: str = "us-east-1") -> str:
    """从 AWS Secrets Manager 获取密钥"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    return secret['GEMINI_API_KEY']
```

---

#### 3. 错误处理和重试机制

##### 添加重试逻辑

```bash
pip install tenacity
```

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from google.api_core import exceptions as google_exceptions

@retry(
    # 最多重试3次
    stop=stop_after_attempt(3),
    # 指数退避: 4秒, 8秒, 16秒
    wait=wait_exponential(multiplier=1, min=4, max=60),
    # 只重试特定异常
    retry=retry_if_exception_type((
        google_exceptions.ServiceUnavailable,
        google_exceptions.DeadlineExceeded,
        google_exceptions.ResourceExhausted
    ))
)
def call_model(state: AgentState):
    """调用 Gemini 模型,自动重试"""
    logger.info(f"Calling Gemini with {len(state['messages'])} messages")
    
    try:
        messages = state['messages']
        gemini_contents = convert_messages(messages)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=gemini_contents,
            config=types.GenerateContentConfig(tools=gemini_tools)
        )
        
        logger.info("Gemini responded successfully")
        # ... 处理响应
        
    except google_exceptions.InvalidArgument as e:
        # 不重试的错误
        logger.error(f"Invalid argument: {e}")
        raise
    except Exception as e:
        logger.warning(f"API call failed (will retry): {e}")
        raise
```

---

##### 详细的异常处理

```python
def call_model(state: AgentState):
    try:
        # ... API 调用
        pass
    except google_exceptions.PermissionDenied:
        # API 密钥无效
        return {"messages": [AIMessage(
            content="Error: API 密钥无效,请检查配置"
        )]}
    except google_exceptions.ResourceExhausted:
        # 配额用尽
        return {"messages": [AIMessage(
            content="Error: API 配额已用尽,请稍后再试"
        )]}
    except google_exceptions.InvalidArgument as e:
        # 请求参数错误
        logger.error(f"Invalid request: {e}")
        return {"messages": [AIMessage(
            content=f"Error: 请求参数错误 - {e}"
        )]}
    except Exception as e:
        # 其他未知错误
        logger.exception("Unexpected error in call_model")
        return {"messages": [AIMessage(
            content=f"Error: 发生未知错误 - {e}"
        )]}
```

---

#### 4. 日志记录

##### 配置结构化日志

```python
import logging
import sys
from pathlib import Path

# 创建日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # 文件处理器
        logging.FileHandler(log_dir / 'agent.log', encoding='utf-8'),
        # 控制台处理器
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getlogger(__name__)
```

##### 在代码中使用日志

```python
def call_model(state: AgentState):
    logger.info("=" * 50)
    logger.info(f"Calling Gemini model")
    logger.debug(f"Current state has {len(state['messages'])} messages")
    
    # 记录最后一条用户消息
    user_msgs = [m for m in state['messages'] if isinstance(m, HumanMessage)]
    if user_msgs:
        logger.info(f"User query: {user_msgs[-1].content[:100]}")
    
    start_time = time.time()
    
    try:
        response = client.models.generate_content(...)
        
        elapsed = time.time() - start_time
        logger.info(f"API call succeeded in {elapsed:.2f}s")
        
        # 记录响应类型
        if response.candidates:
            parts = response.candidates[0].content.parts
            has_text = any(p.text for p in parts)
            has_tool_call = any(p.function_call for p in parts)
            
            if has_tool_call:
                tool_names = [p.function_call.name for p in parts if p.function_call]
                logger.info(f"Model requested tools: {tool_names}")
            elif has_text:
                logger.info("Model provided text response")
        
        return {"messages": [AIMessage(...)]}
        
    except Exception as e:
        logger.error(f"Error in call_model: {e}", exc_info=True)
        raise
```

---

#### 5. 性能优化

##### Token 使用监控

```python
def call_model(state: AgentState):
    response = client.models.generate_content(...)
    
    # 记录token使用情况
    if hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
        logger.info(
            f"Token usage - "
            f"Prompt: {usage.prompt_token_count}, "
            f"Response: {usage.candidates_token_count}, "
            f"Total: {usage.total_token_count}"
        )
        
        # 警告: token 使用过多
        if usage.total_token_count > 30000:
            logger.warning("Token usage is high! Consider truncating history")
    
    return {"messages": [AIMessage(...)]}
```

---

##### 历史消息截断

```python
def truncate_messages(messages: list[BaseMessage], max_messages: int = 20) -> list[BaseMessage]:
    """保留最近的 N 条消息,避免上下文过长"""
    if len(messages) <= max_messages:
        return messages
    
    # 保留第一条 (通常是系统提示) 和最近的消息
    return [messages[0]] + messages[-(max_messages-1):]

def call_model(state: AgentState):
    messages = state['messages']
    
    # 截断历史
    messages = truncate_messages(messages, max_messages=20)
    
    gemini_contents = convert_messages(messages)
    # ...
```

---

##### 缓存重复转换

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def convert_single_message_cached(msg_type: str, content: str, role: str) -> types.Content:
    """缓存单个消息的转换结果"""
    if msg_type == "human":
        return types.Content(
            role="user",
            parts=[types.Part.from_text(text=content)]
        )
    # ... 其他类型
```

---

#### 6. 工具扩展示例

##### 真实搜索工具 (DuckDuckGo)

```bash
pip install duckduckgo-search
```

```python
from duckduckgo_search import DDGS

def search_func(query: str) -> str:
    """
    Search for information on the internet using DuckDuckGo.
    Returns a summary of the top 3 search results.
    
    Args:
        query: The search query string
        
    Returns:
        A formatted string with search results
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        if not results:
            return f"No search results found for: {query}"
        
        summary = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            summary += f"{i}. {result['title']}\n"
            summary += f"   {result['body'][:200]}...\n"
            summary += f"   Source: {result['href']}\n\n"
        
        return summary
        
    except Exception as e:
        return f"Search error: {e}"

# 更新 LangChain 工具
search = tool("search_func")(search_func)
```

---

##### 文件操作工具

```python
from pathlib import Path

def read_file_func(filepath: str) -> str:
    """
    Read and return the contents of a text file.
    
    Args:
        filepath: Absolute or relative path to the file
        
    Returns:
        File contents as a string (max 5000 chars)
    """
    try:
        file_path = Path(filepath)
        
        # 安全检查
        if not file_path.exists():
            return f"Error: File not found: {filepath}"
        
        if not file_path.is_file():
            return f"Error: Not a file: {filepath}"
        
        # 限制文件大小
        if file_path.stat().st_size > 1_000_000:  # 1MB
            return "Error: File too large (max 1MB)"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(5000)  # 限制字符数
        
        return content
        
    except UnicodeDecodeError:
        return f"Error: Cannot decode file (not a text file?)"
    except PermissionError:
        return f"Error: Permission denied: {filepath}"
    except Exception as e:
        return f"Error reading file: {e}"

# 创建工具
read_file = tool("read_file_func")(read_file_func)

# 注册
gemini_tools = [calculator_func, search_func, read_file_func]
langchain_tools = [calculator, search, read_file]
```

---

##### 天气查询工具

```bash
pip install requests
```

```python
import requests

def get_weather_func(city: str) -> str:
    """
    Get current weather information for a city.
    Uses OpenWeatherMap API (free tier).
    
    Args:
        city: City name (e.g., "London", "Tokyo")
        
    Returns:
        Weather description and temperature
    """
    try:
        # 注意: 需要在 .env 中添加 OPENWEATHERMAP_API_KEY
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            return "Error: OpenWeatherMap API key not configured"
        
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric"  # 摄氏度
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        
        return (
            f"Weather in {city}:\n"
            f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
            f"Conditions: {description}\n"
            f"Humidity: {humidity}%"
        )
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Error: City not found: {city}"
        return f"API error: {e}"
    except requests.exceptions.Timeout:
        return "Error: Request timed out"
    except Exception as e:
        return f"Error: {e}"

get_weather = tool("get_weather_func")(get_weather_func)
```

---

#### 7. 持久化存储

**当前问题**: `MemorySaver` 只保存在内存中,程序重启后对话历史丢失。

##### 解决方案1: SQLite (本地)

```bash
pip install aiosqlite
```

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 创建 SQLite 检查点器
checkpointer = SqliteSaver.from_conn_string("agent_checkpoints.db")

# 编译图
app = workflow.compile(checkpointer=checkpointer)
```

**优点**:
- 本地文件数据库
- 无需额外服务
- 自动保存所有状态

**数据库结构**:
```sql
-- checkpoints 表
CREATE TABLE checkpoints (
    thread_id TEXT,
    checkpoint_id TEXT,
    parent_id TEXT,
    data BLOB,
    PRIMARY KEY (thread_id, checkpoint_id)
);
```

---

##### 解决方案2: PostgreSQL (生产)

```bash
pip install psycopg2-binary
```

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 连接 PostgreSQL
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/agentdb"
)

app = workflow.compile(checkpointer=checkpointer)
```

**优点**:
- 生产级数据库
- 支持并发
- 可扩展

---

##### 查询历史对话

```python
# 获取某个线程的所有检查点
checkpoints = checkpointer.list({"configurable": {"thread_id": "1"}})

for cp in checkpoints:
    print(f"Checkpoint: {cp.id}")
    print(f"Messages: {len(cp.data['messages'])}")
```

---

#### 8. 多会话管理

```python
import uuid

def main():
    print("Multi-session Agent")
    
    # 为每个用户生成唯一 thread_id
    user_id = input("Enter your user ID (or press Enter for new): ")
    
    if not user_id:
        user_id = str(uuid.uuid4())
        print(f"New session created: {user_id}")
    
    config = {"configurable": {"thread_id": user_id}}
    
    # ... 对话循环
```

---

#### 9. 流式响应

**当前**: 等待完整响应后才显示

**改进**: 逐字输出 (更好的用户体验)

```python
# 注意: 需要 Gemini API 支持流式响应
def call_model_streaming(state: AgentState):
    """流式调用 Gemini"""
    messages = state['messages']
    gemini_contents = convert_messages(messages)
    
    # 流式请求
    stream = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=gemini_contents,
        config=types.GenerateContentConfig(tools=gemini_tools)
    )
    
    full_content = ""
    tool_calls = []
    
    for chunk in stream:
        if chunk.candidates:
            for part in chunk.candidates[0].content.parts:
                if part.text:
                    # 逐字打印
                    print(part.text, end="", flush=True)
                    full_content += part.text
                if part.function_call:
                    tool_calls.append({
                        "name": part.function_call.name,
                        "args": part.function_call.args,
                        "id": f"call_{part.function_call.name}"
                    })
    
    print()  # 换行
    return {"messages": [AIMessage(content=full_content, tool_calls=tool_calls)]}
```

---

#### 10. Web 界面

##### 使用 Streamlit

```bash
pip install streamlit
```

```python
# webapp.py
import streamlit as st
from langchain_core.messages import HumanMessage
from src.graph import app

st.title("🤖 LangGraph Gemini Agent")

# 会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
if prompt := st.chat_input("Your message"):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 调用代理
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    inputs = {"messages": [HumanMessage(content=prompt)]}
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        for output in app.stream(inputs, config=config):
            for key, value in output.items():
                if "messages" in value and value["messages"]:
                    last_msg = value["messages"][-1]
                    if hasattr(last_msg, "content") and last_msg.content:
                        full_response = last_msg.content
                        message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
```

**运行**:
```bash
streamlit run webapp.py
```

---

## 进阶话题

### 🤖 多代理系统

创建专门的代理处理不同任务:

```python
from langgraph.graph import StateGraph

# 定义专门的代理
def create_math_agent():
    """数学专家代理"""
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode([calculator]))
    # ... 配置
    return workflow.compile()

def create_search_agent():
    """搜索专家代理"""
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode([search]))
    # ... 配置
    return workflow.compile()

# 监督者代理
def supervisor_node(state: AgentState):
    """决定调用哪个专家代理"""
    last_message = state["messages"][-1].content.lower()
    
    if any(word in last_message for word in ["calculate", "math", "compute"]):
        return "math_agent"
   elif any(word in last_message for word in ["search", "find", "look up"]):
        return "search_agent"
    else:
        return "general_agent"

# 主图
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("math_agent", create_math_agent())
workflow.add_node("search_agent", create_search_agent())
# ... 链接节点
```

---

### 📊 可视化工具

##### 绘制图结构

```python
from IPython.display import Image, display

# 生成图的可视化
display(Image(app.get_graph().draw_mermaid_png()))
```

##### 生成 Mermaid 代码

```python
mermaid_code = app.get_graph().draw_mermaid()
print(mermaid_code)
```

**输出**:
```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
	__start__([<p>__start__</p>]):::first
	agent(agent)
	tools(tools)
	__end__([<p>__end__</p>]):::last
	__start__ --> agent;
	tools --> agent;
	agent -.->|tools| tools;
	agent -.->|__end__| __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

---

### 🎓 学习资源

1. **LangGraph 官方文档**: [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/)
2. **Gemini API 文档**: [https://ai.google.dev/docs](https://ai.google.dev/docs)
3. **LangChain 工具指南**: [https://python.langchain.com/docs/modules/agents/tools/](https://python.langchain.com/docs/modules/agents/tools/)
4. **Google GenAI SDK**: [https://github.com/google/generative-ai-python](https://github.com/google/generative-ai-python)

---

## 总结

### 🎯 项目核心设计

本项目展示了一个完整的、生产级的 AI Agent 架构:

#### 1. 模块化设计
- **工具层** (`tools.py`): 定义可复用的功能
- **图逻辑** (`graph.py`): 编排状态流转
- **主程序** (`main.py`): 用户交互界面

#### 2. 有状态对话
- 使用 `Annotated[..., operator.add]` 自动累积历史
- LangGraph 的检查点机制支持持久化

#### 3. 工具集成
- 双重定义: Gemini 函数 + LangChain 工具
- 无缝的函数调用和结果处理

#### 4. 可扩展性
- 易于添加新工具 (只需 3 步)
- 支持多节点、多代理架构

---

### ⭐ 关键设计亮点

| 设计 | 作用 |
|-----|------|
| **双工具列表** | 兼容 Gemini 和 LangChain |
| **消息转换层** | 优雅处理格式差异 |
| **条件路由** | 自动决策工具调用 |
| **状态累加** | 自动管理对话历史 |

---

### 🚀 下一步方向

#### 功能增强
- [ ] 添加 Web 界面 (Streamlit/Gradio)
- [ ] 实现流式响应
- [ ] 支持多模态 (图片、语音)
- [ ] 集成更多工具 (数据库、API)

#### 架构优化
- [ ] 多代理协作系统
- [ ] 任务规划和执行分离
- [ ] 长期记忆和向量数据库

#### 生产部署
- [ ] Docker 容器化
- [ ] 云平台部署 (Google Cloud Run, AWS Lambda)
- [ ] 监控和告警系统
- [ ] 负载均衡和扩展

---

**Happy Building! 🎉**

---

*本指南由 AI 生成,欢迎提出改进建议!*
