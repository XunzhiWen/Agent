# 📖 LangGraph Gemini Agent - 完整技术文档

> 这是一个详尽的、逐行代码讲解的技术指南,帮助你深入理解整个项目

## 📚 文档结构

本技术指南分为两部分,涵盖项目的所有方面:

### [📄 第一部分: 核心代码详解](TECHNICAL_GUIDE.md)

包含以下内容:

1. **项目概述**
   - 系统功能介绍
   - 核心技术栈
   - 项目结构

2. **依赖管理** (`requirements.txt`)
   - 逐行解析每个依赖包的作用

3. **环境配置** (`.env`)
   - API 密钥管理
   - 安全建议

4. **工具定义** (`src/tools.py`)
   - 计算器工具详解
   - 搜索工具详解
   - 双重定义模式解释

5. **核心图架构** (`src/graph.py`)
   - 状态定义
   - Gemini 客户端初始化
   - 消息格式转换 (最复杂的部分!)
   - call_model 节点详解
   - ToolNode 工作原理
   - 条件逻辑
   - 图构建过程

6. **主程序入口** (`main.py`)
   - 用户交互循环
   - 流式输出处理
   - 异常处理

---

### [📄 第二部分: 实战与进阶](TECHNICAL_GUIDE_PART2.md)

包含以下内容:

1. **调试脚本详解**
   - `debug_models.py` - 列出可用模型
   - `debug_gemini.py` - 测试工具调用

2. **工作流程详解**
   - 完整对话流程 (7个阶段)
   - 状态演变时间线
   - Mermaid 流程图
   - 数据流可视化

3. **最佳实践** (⭐ 重点!)
   - **安全性**: 替换危险的 `eval()`
   - **环境变量**: 密钥管理方案
   - **错误处理**: 重试机制和异常处理
   - **日志记录**: 结构化日志配置
   - **性能优化**: Token 监控、历史截断
   - **工具扩展**: 真实搜索、文件操作、天气查询
   - **持久化**: SQLite 和 PostgreSQL
   - **多会话**: 用户管理
   - **流式响应**: 逐字输出
   - **Web 界面**: Streamlit 集成

4. **进阶话题**
   - 多代理系统
   - 图结构可视化
   - 学习资源

5. **总结与展望**
   - 核心设计亮点
   - 下一步方向

---

## 🚀 快速开始

### 阅读建议

**如果你是新手**:
1. 先阅读 [第一部分](TECHNICAL_GUIDE.md) 的项目概述和结构
2. 依次阅读每个文件的详解
3. 重点关注 `src/graph.py` 的消息转换部分
4. 然后阅读 [第二部分](TECHNICAL_GUIDE_PART2.md) 的工作流程详解

**如果你想快速上手**:
1. 简单浏览 [第一部分](TECHNICAL_GUIDE.md) 理解代码结构
2. 直接跳到 [第二部分](TECHNICAL_GUIDE_PART2.md) 的完整工作流程详解
3. 查看最佳实践部分,了解生产环境建议

**如果你要扩展项目**:
1. 阅读 [第一部分](TECHNICAL_GUIDE.md) 的工具定义部分
2. 查看 [第二部分](TECHNICAL_GUIDE_PART2.md) 的工具扩展示例
3. 参考最佳实践中的安全性建议

---

## 📊 项目统计

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| `main.py` | 47 | 用户交互循环 |
| `src/graph.py` | 176 | 核心状态图逻辑 |
| `src/tools.py` | 28 | 工具定义 |
| `debug_gemini.py` | 37 | 工具调用测试 |
| `debug_models.py` | 21 | 模型列表查询 |
| **总计** | **309** | **完整 AI Agent** |

---

## 🎯 核心概念速查

### 关键类和函数

| 名称 | 位置 | 作用 |
|------|------|------|
| `AgentState` | graph.py:15 | 定义状态结构 |
| `convert_messages()` | graph.py:33 | LangChain ↔ Gemini 格式转换 |
| `call_model()` | graph.py:82 | 调用 Gemini API |
| `should_continue()` | graph.py:143 | 决定是否调用工具 |
| `calculator_func()` | tools.py:4 | 数学计算工具 |
| `search_func()` | tools.py:16 | 搜索工具 |

### 工作流程总结

```
用户输入
    ↓
[agent 节点] → Gemini 决定是否需要工具
    ↓
[should_continue] → 检查是否有工具调用
    ├─ 有 → [tools 节点] → 执行工具 → 返回 agent
    └─ 无 → END
```

### 消息流转

```
HumanMessage → AIMessage (tool_calls) → ToolMessage → AIMessage (最终答案)
     ↓              ↓                       ↓              ↓
   用户输入      决定调用工具            工具结果        自然语言答案
```

---

## ⚠️ 重要提示

### 安全警告

- ❌ **不要**直接使用 `eval()` (见第二部分的安全替代方案)
- ❌ **不要**将 `.env` 文件提交到 Git
- ✅ **务必**为生产环境添加输入验证
- ✅ **务必**实现适当的错误处理

### 成本优化

- 使用 `gemini-2.5-flash` (快速且便宜)
- 对于复杂任务考虑 `gemini-1.5-pro`
- 监控 token 使用量
- 截断过长的对话历史

---

## 🤝 贡献指南

### 添加新工具的完整流程

1. **在 `src/tools.py` 中**:
   ```python
   def your_tool_func(param: str) -> str:
       """详细的 docstring,Gemini 会读取!"""
       # 实现逻辑
       return result
   
   your_tool = tool("your_tool_func")(your_tool_func)
   ```

2. **在 `src/graph.py` 中**:
   ```python
   # 第29-30行
   gemini_tools = [calculator_func, search_func, your_tool_func]  # 添加
   langchain_tools = [calculator, search, your_tool]  # 添加
   ```

3. **测试**:
   ```python
   # 创建测试脚本
   python debug_your_tool.py
   ```

---

## 📞 获取帮助

遇到问题时的调试步骤:

1. **检查 API 密钥**: 运行 `python debug_models.py`
2. **测试工具调用**: 运行 `python debug_gemini.py`
3. **查看日志**: 检查错误信息
4. **阅读文档**: 本指南的相关章节

---

## 📖 开始阅读

### 👉 [第一部分: 核心代码详解](TECHNICAL_GUIDE.md)

**包含**: 项目概述、依赖管理、工具定义、图架构、主程序

### 👉 [第二部分: 实战与进阶](TECHNICAL_GUIDE_PART2.md)

**包含**: 调试脚本、工作流程、最佳实践、进阶话题

---

## 🌟 亮点预览

### 从第一部分你将学到:

- ✅ 如何定义 LangGraph 状态 (`Annotated` + `operator.add`)
- ✅ 为什么需要双重工具定义
- ✅ 消息格式转换的完整逻辑 (50+ 行详细注释!)
- ✅ Gemini API 的请求和响应结构
- ✅ 条件边和固定边的区别

### 从第二部分你将学到:

- 🚀 一个计算请求的 7 个执行阶段
- 🚀 如何用 AST 替换危险的 `eval()`
- 🚀 使用 DuckDuckGo API 实现真实搜索
- 🚀 SQLite/PostgreSQL 持久化方案
- 🚀 Streamlit Web 界面集成
- 🚀 多代理协作系统设计

---

## 💡 示例代码片段

### 快速测试工具

```python
from src.tools import calculator_func, search_func

# 测试计算器
print(calculator_func("15 * 8"))  # "120"

# 测试搜索
print(search_func("weather"))  # "Mock search results..."
```

### 运行完整系统

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API 密钥
echo "GEMINI_API_KEY=your-key-here" > .env

# 运行
python main.py
```

---

## 📈 预期收获

阅读完整指南后,你将能够:

- ✅ 理解 LangGraph 的状态管理机制
- ✅ 掌握 Gemini 工具调用的完整流程
- ✅ 独立添加新工具到系统
- ✅ 优化性能和成本
- ✅ 部署到生产环境
- ✅ 扩展为多代理系统

---

**祝学习愉快! Happy Coding! 🎉**

*最后更新: 2025-11-23*
