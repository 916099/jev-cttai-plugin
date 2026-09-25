# Jev via CTTAI

一个可在 Codex 中使用的本地 MCP 插件，通过 Jev 对明确的问题进行结构化判断。

> **注册与 API Key：** 截至 2026-09-26，作者目前无法在 TypeSafe 官网完成新用户注册；官网开放状态可能变化，请以官网实际页面为准。个人使用时，作者推荐在 [CTTAI](https://llmapi.cttai.art/) 获取 Jev API Key。CTTAI 是第三方服务，使用前请自行了解其服务条款、价格和数据处理政策。

## 功能

- `jev_decide`：调用 Jev 对文本或数据进行 `choice` 选项分类、`score` 等级评分或 `noul` 是非判断，可一次提交多个问题。
- `jev_list_models`：查询当前 API Key 可用的模型。
- 通过本机标准输入/输出运行 MCP 服务，Python 仅依赖标准库。
- API Key 只从本机环境变量读取；错误信息不会回显上游响应正文。
- 作者本人实测，在保证任务完成的情况下，能给Codex处理复杂任务提速60%，且节省大量订阅额度。

## 安装

### 方式一：从 GitHub 安装到 Codex

需要已安装 Codex CLI，并在 Codex 桌面应用中使用插件目录。

1. 在 PowerShell 或终端运行（将 `916099/jev-cttai-plugin` 替换为实际仓库路径）：

   ```powershell
   codex plugin marketplace add 916099/jev-cttai-plugin
   ```

2. 重启 Codex 桌面应用，打开插件目录，选择 `Jev via CTTAI` 并安装。
3. 本仓库目前公开，正常情况下无需额外配置 GitHub 凭据。若你从其他私有镜像安装，请确保本机 Git 有权读取该仓库。

Codex 插件市场的 GitHub 来源和本地插件安装方式见 [OpenAI 插件打包与分发文档](https://developers.openai.com/plugins/build/plugins)。

### 方式二：本地安装

1. 从 GitHub 下载 ZIP 并解压，或克隆此仓库。
2. 在 Codex 支持的本地插件市场配置中，将插件来源指向解压后的项目目录；此仓库根目录包含 `plugin.json`、`mcp.json` 和 `skills/`。
3. 检查并按需修改 `mcp.json` 中的 Python 可执行文件路径。默认示例为 `D:/Anaconda/python.exe`；若 Python 已加入 PATH，可改成 `python`。
4. 按下文配置 API Key 和服务地址，然后完全退出并重启 Codex。

## 配置

### Windows 环境变量

打开“编辑账户的环境变量”，在“用户变量”中新增：

| 变量 | 必需 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `CTTAI_API_KEY` | 是 | 无 | 在 CTTAI 获取的 API Key。不要提交到 Git、粘贴到聊天或写入仓库文件。 |
| `CTTAI_BASE_URL` | 否 | `https://llmapi.cttai.art` | 服务根地址，可包含服务商要求的 API 前缀；不要在末尾附加接口路径。 |
| `CTTAI_MODEL` | 否 | `jev-latest` | 默认模型；也可在调用 `jev_decide` 时单独指定。 |
| `CTTAI_SYSTEMONE_PATH` | 否 | `/typesafe/v1/systemone` | Jev 判断接口路径。 |
| `CTTAI_MODELS_PATH` | 否 | `/v1/models` | 模型列表接口路径。 |

保存后完全退出并重启 Codex。可调用 `jev_list_models` 检查密钥、网络和模型列表接口是否可用。插件要求 `CTTAI_BASE_URL` 使用 HTTPS。

### 使用其他服务网站

只要其他服务提供兼容 Jev 的 System One 请求与响应格式，就可尝试通过配置接入：

1. 将 `CTTAI_API_KEY` 设置为该服务签发的密钥。
2. 将 `CTTAI_BASE_URL` 改为该服务文档给出的 HTTPS API 根地址。
3. 若判断接口路径不同，设置 `CTTAI_SYSTEMONE_PATH`；若模型列表路径不同，设置 `CTTAI_MODELS_PATH`。
4. 若该服务没有模型列表接口，可不调用 `jev_list_models`，并将 `CTTAI_MODEL` 设置为服务商支持的模型 ID。
5. 重启 Codex 后先查询模型（若支持），再执行一条低风险的判断请求。

例如（仅为格式示例，请替换成服务商文档提供的真实地址和路径）：

```text
CTTAI_BASE_URL=https://api.example.com
CTTAI_SYSTEMONE_PATH=/typesafe/v1/systemone
CTTAI_MODELS_PATH=/v1/models
CTTAI_MODEL=jev-latest
```

如果服务商的鉴权头、请求 JSON 或响应结构不兼容 Jev/TypeSafe System One，仅修改地址和路径不够，需要按其 API 文档修改 `server.py` 中的 `_api_request` 和 `jev_decide` 请求组装逻辑。不要关闭 HTTPS 校验，也不要把密钥写进源码或 `mcp.json`。

### Python 路径

`mcp.json` 控制本机 MCP 进程的启动命令。Windows 用户需把 `command` 改为自己的 Python 可执行文件绝对路径，或使用已加入 PATH 的 `python`；`args` 和 `cwd` 通常保持不变。

## 使用

在 Codex 中提出边界明确的判断任务，例如“把这条工单分为账单、技术、其他三类”，并提供工单文本、分类选项和判断标准。插件会调用 Jev 并返回结构化结果及其置信度/概率。

`jev_decide` 输入包含：

- `state`：需要判断的文本、对象或数组。
- `questions`：一个或多个问题；每项需指定 `type` 为 `choice`、`score` 或 `noul`。
- `model`：可选模型 ID；不填时使用 `CTTAI_MODEL` 或 `jev-latest`。

Jev 返回判断结果，不生成解释性长文。结果属于模型判断；重要决策应由人工复核。

## 安全与隐私

- API Key 仅通过 `CTTAI_API_KEY` 环境变量提供，不要提交密钥或包含密钥的日志。
- 请求中的判断文本会发送到 `CTTAI_BASE_URL` 指向的服务处理；请勿提交不应向该服务披露的敏感数据。
- 插件当前只允许 HTTPS API 地址。

## English

Jev via CTTAI is a local MCP plugin for Codex that uses Jev for structured judgments on clearly defined questions.

> **Registration and API key:** As of 2026-09-26, the maintainer is currently unable to complete new-user registration on the TypeSafe website. Availability may change; check the official site for its current status. For personal use, the maintainer recommends obtaining a Jev API key from [CTTAI](https://llmapi.cttai.art/). CTTAI is a third-party service. Review its terms of service, pricing, and data practices before using it.

### Features

- `jev_decide`: asks Jev to classify among `choice` options, assign a `score`, or make a `noul` yes/no judgment. Multiple questions can be sent in one request.
- `jev_list_models`: lists models available to the configured API key.
- Runs as a local stdio MCP server and uses only the Python standard library.
- Reads the API key from a local environment variable. Error messages do not echo the upstream response body.
- The author personally tested it and found that, while ensuring task completion, it can speed up Codex handling complex tasks by 60% and save a lot on subscription usage.

### Installation

#### Option 1: Install from GitHub in Codex

This method requires Codex CLI and the plugin directory in the Codex desktop app.

1. Run this command in PowerShell or a terminal (replace `916099/jev-cttai-plugin` with the repository path if you use a fork):

   ```powershell
   codex plugin marketplace add 916099/jev-cttai-plugin
   ```

2. Restart the Codex desktop app, open the plugin directory, and install `Jev via CTTAI` from the marketplace.
3. This repository is public, so GitHub credentials are normally not needed. If you install from a private mirror, make sure Git on your computer has permission to read it.

See the [OpenAI plugin packaging and distribution guide](https://developers.openai.com/plugins/build/plugins) for GitHub sources and local plugin marketplaces.

#### Option 2: Install locally

1. Clone this repository or download its ZIP from GitHub and extract it.
2. Add the extracted folder to a local Codex plugin marketplace. The repository root contains `plugin.json`, `mcp.json`, `skills/`, and the marketplace metadata under `.agents/plugins/`.
3. Check the Python executable in `mcp.json`. The current example uses `D:/Anaconda/python.exe`; replace it with the absolute path to Python on your computer, or use `python` if Python is on `PATH`.
4. Configure the API key and service address as described below, then fully quit and restart Codex.

### Configuration

#### Windows environment variables

Open **Edit environment variables for your account** in Windows. Under **User variables**, add the following variables:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `CTTAI_API_KEY` | Yes | None | The API key issued by CTTAI. Never commit it to Git, paste it into chat, or store it in repository files. |
| `CTTAI_BASE_URL` | No | `https://llmapi.cttai.art` | The service API base URL. It may include a provider-required API prefix, but do not append an endpoint path. |
| `CTTAI_MODEL` | No | `jev-latest` | Default model. You can also choose a model per `jev_decide` call. |
| `CTTAI_SYSTEMONE_PATH` | No | `/typesafe/v1/systemone` | Jev judgment endpoint path. |
| `CTTAI_MODELS_PATH` | No | `/v1/models` | Model-list endpoint path. |

Save the variables, fully quit Codex, and restart it so the plugin process can read them. Call `jev_list_models` to check the key, network connection, and model-list endpoint. `CTTAI_BASE_URL` must use HTTPS.

#### Using another API provider

You can try another service if it supports Jev-compatible System One requests and responses:

1. Set `CTTAI_API_KEY` to the key issued by that service.
2. Set `CTTAI_BASE_URL` to the HTTPS API base URL from the provider's documentation.
3. If its judgment endpoint path differs, set `CTTAI_SYSTEMONE_PATH`. If its model-list endpoint differs, set `CTTAI_MODELS_PATH`.
4. If the service has no model-list endpoint, skip `jev_list_models` and set `CTTAI_MODEL` to a model ID supported by that provider.
5. Restart Codex. If model listing is supported, check it first, then try a low-risk judgment request.

Example values only. Replace them with the actual URL and paths in the provider's documentation:

```text
CTTAI_BASE_URL=https://api.example.com
CTTAI_SYSTEMONE_PATH=/typesafe/v1/systemone
CTTAI_MODELS_PATH=/v1/models
CTTAI_MODEL=jev-latest
```

If the provider uses a different authentication header, request JSON schema, or response format, changing the URL and paths is not sufficient. Adapt `_api_request` and the request construction in `jev_decide` in `server.py` to that provider's API documentation. Do not disable HTTPS validation or put the API key in source code or `mcp.json`.

#### Python executable path

`mcp.json` controls how the local MCP process starts. On Windows, change `command` to the absolute path of Python on your computer, or use `python` if it is on `PATH`. The `args` and `cwd` values can normally stay unchanged.

### Usage

In Codex, provide a bounded task, such as “classify this ticket as billing, technical, or other,” together with the ticket text, allowed categories, and decision criteria. The plugin calls Jev and returns a structured judgment with confidence or probability values.

`jev_decide` accepts:

- `state`: the text, object, or array to evaluate.
- `questions`: one or more named questions. Each question must set `type` to `choice`, `score`, or `noul`.
- `model`: optional model ID. If omitted, the plugin uses `CTTAI_MODEL` or `jev-latest`.

Jev returns judgments rather than explanatory long-form text. Treat the output as a model judgment, not a guaranteed fact, and have a person review decisions with significant consequences.

### Security and privacy

- Provide the API key only through the `CTTAI_API_KEY` environment variable. Do not commit the key or logs containing it.
- Text sent for judgment is processed by the service configured in `CTTAI_BASE_URL`. Do not submit sensitive information that you are not permitted to share with that service.
- The plugin currently accepts HTTPS API URLs only.
