# 基于 RAG + Eval 的游戏创意助手

这是一个适合面试展示的最小 AI 应用工程项目。它把 `RAG`、`结构化生成`、`Eval` 和一点点 `LLMOps` 思维放进了一个可运行的本地 Demo 里。现在它已经支持在页面里直接切换 `mock` 和 `openai-compatible` 模式，不再只是预留接口。

## 它现在能做什么

输入一句游戏创意后，系统会完成这条链路：

1. 从本地游戏案例知识库里检索最相关的 3 条案例。
2. 基于检索结果输出一份结构化游戏设计方案。
3. 自动做四类 Eval：
   - 是否完整
   - 是否格式正确
   - 是否引用了检索结果
   - 是否存在明显自相矛盾
4. 把每次结果落成日志，方便回看和对比。
5. 在页面里直接查看当前是否走了真实 API、是否发生回退、模型名、Base URL 和延迟。

## 这次升级了什么

- 从“只会 mock”升级成了“支持真实 API 的生成器路由”。
- 新增运行时设置存储：模式、Base URL、模型、Temperature、超时、最大输出 Token。
- 新增 API 设置面板，不必每次手动改代码或只靠环境变量。
- 新增 Key 状态显示和清除能力。
- 新增更稳的回退逻辑：真实 API 失败时会自动回退到 mock，并把原因记录到返回元数据和日志里。
- 新增更稳的 JSON 解析和字段归一化逻辑，减少模型偶发输出不规范时的崩溃概率。

## 为什么这个项目更像正式作品了

它现在不只是一个“能跑通一遍”的演示，而是已经有了更接近真实 AI 应用的三层结构：

- `生成层`：支持本地 mock 和 openai-compatible API 两种模式。
- `控制层`：运行时配置、回退、状态可见、日志记录。
- `展示层`：前端页面可以查看设置、结果、Eval、原始 JSON 和最近运行记录。

## 运行方式

在 ‘你自己选定的’ 目录下执行：

```powershell
python app.py
```

然后打开浏览器访问：

```text
http://127.0.0.1:8010
```

## 如何接入真实 API

### 方式一：直接在页面里配置

启动服务后，打开页面顶部的 `API 设置` 面板：

1. 把模式切成 `openai-compatible`
2. 填入 `Base URL`
3. 填入 `Model`
4. 填入 `API Key`
5. 点击 `保存设置`
6. 再生成一次方案

如果请求真的走到了目标接口，页面里的 `运行状态` 会显示：

- 生成模式
- 模型
- Provider
- Base URL
- 延迟
- 是否发生回退

### 方式二：用环境变量覆盖

如果你更习惯环境变量，也可以这样启动：

```powershell
$env:GAME_IDEA_ASSISTANT_LLM_MODE="openai"
$env:OPENAI_API_KEY="你的key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4.1-mini"
$env:GAME_IDEA_ASSISTANT_TEMPERATURE="0.4"
$env:GAME_IDEA_ASSISTANT_TIMEOUT_SECONDS="25"
$env:GAME_IDEA_ASSISTANT_MAX_OUTPUT_TOKENS="1400"
python app.py
```

环境变量优先级高于页面保存的本地配置。

## 配置会保存到哪里

页面保存的运行时配置会写到：

```text
G:\hanjia_work\game_idea_assistant\data\runtime_settings.json
```

说明：

- 这是一个本地项目，Key 会保存在这个文件里。
- 如果你不想长期保存 Key，可以在页面里点击 `清除已保存 Key`。
- 如果你使用环境变量，服务会优先采用环境变量值。

## 项目结构

```text
game_idea_assistant/
  app.py
  assistant/
    knowledge.py
    retriever.py
    generator.py
    evaluator.py
    service.py
    settings.py
  data/
    knowledge_base/game_cases.json
    run_logs/
    runtime_settings.json
  static/
    index.html
    styles.css
    app.js
  tests/
    test_pipeline.py
```

## 你可以怎么讲这个升级

### 30 秒版

我把这个项目从一个离线 mock Demo 升级成了一个支持真实 API 的最小 AI 应用系统。现在它不但能做 RAG、结构化输出和 Eval，还支持运行时切换模型模式、保存配置、展示当前是否真实走了 API，以及在接口失败时自动回退并记录原因。

### 1 分钟版

这个项目最开始只是一个本地的 RAG + Eval MVP。我后面把生成层做成了一个路由器，支持 `mock` 和 `openai-compatible` 两种模式。运行时设置被独立存储，前端页面可以直接配置 Base URL、模型、温度、超时和输出上限。生成时如果真实 API 成功，就返回真实模式的结构化方案；如果失败或者没 Key，就自动回退到本地 mock，并把回退原因、延迟和模型信息一起写进元数据和日志。这样这个项目就不只是能展示 AI 结果，还能展示工程控制能力。

## 你可能会被追问什么

### 1. 为什么还保留 mock

因为 mock 让这个项目在离线环境里也能稳定演示，同时它也是一个 fallback 路径。面试里这反而是加分项，因为说明你考虑了可用性和降级策略。

### 2. 为什么前端要做设置面板

因为真实 AI 应用里，模型、Base URL 和参数通常不是写死在代码里的。把它们做成运行时配置，能更贴近生产环境，也方便实验和演示。

### 3. 为什么要做 JSON 归一化

因为真实大模型即使要求输出 JSON，也可能偶尔多说一句话或漏某些字段。归一化逻辑能把系统从“碰一下就碎”变成“尽量稳定返回可评测结果”。

### 4. 如果要继续升级，还能做什么

- 把知识库从案例 JSON 升级到真正的文档分块 + embedding + rerank。
- 引入离线 benchmark 数据集，做版本回归。
- 增加 tracing 和请求级日志筛查。
- 增加多模型路由，比如小模型做草稿、强模型做终稿。
- 增加更严格的 schema 校验和二次修复器。

## 测试

```powershell
python -m unittest tests.test_pipeline
```
