---
name: jev-cttai
description: 通过用户的 CTTAI API 调用 Jev，对给定文本或数据做有明确边界的分类、评分或是非判断；不要用于开放式写作或长链路推理。
---

# 通过 CTTAI 调用 Jev

当任务需要对给定内容作出边界明确的判断时，使用 `jev_decide` MCP 工具。Jev 可返回 `choice`、`score` 或 `noul`（是非概率）类型的答案。

- 只向 Jev 提供完成判断所需的状态和标准。
- 将问题写得具体、独立；一次请求可以提交多个问题。
- 将结果视为模型判断，而不是解释或必然正确的事实。
- 说明 API 返回的概率和置信度。涉及重要后果时，应设置明确阈值并保留人工复核。
- 使用 `jev_list_models` 确认当前 CTTAI Key 可访问的模型。
- 不要要求用户在聊天中粘贴 API Key。本机 MCP 进程从继承的环境变量 `CTTAI_API_KEY` 读取密钥。
