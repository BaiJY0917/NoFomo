 ---
  NoFomo 第一版实现方案

  1. 最终技术决策

  - 语言：Python
  - 摘要方式：纯规则摘要，不接 LLM
  - 执行方式：外部调度每天触发一次单次运行
  - 存储方式：本地 JSON / YAML 文件
  - 反馈方式：Telegram 命令式反馈，不做 inline keyboard
  - 反馈处理方式：手动触发同步，不常驻轮询

  ---
  2. 第一版运行形态

  第一版由两个入口组成：

  run-digest

  每天执行一次，完成：
  1. 读取来源配置
  2. 拉取 RSS
  3. 去重
  4. 标准化
  5. 规则摘要
  6. 关键词标记
  7. 生成日报
  8. 推送 Telegram
  9. 保存本地归档与日志

  sync-feedback

  用户读完日报后，按需手动执行一次，完成：
  1. 拉取 Telegram Bot 尚未处理的消息更新
  2. 识别命令式反馈，例如：
    - /like <item_id>
    - /dislike <item_id>
  3. 校验 item_id
  4. 记录反馈到本地文件
  5. 更新 Telegram offset，避免重复处理

  这样第一版没有任何必须常驻的进程。

  ---
  3. 目录结构

  NoFomo/
  ├─ config/
  │  ├─ sources.yaml
  │  ├─ keywords.yaml
  │  └─ telegram.yaml
  ├─ data/
  │  ├─ seen_items.json
  │  ├─ telegram_state.json
  │  ├─ feedback.jsonl
  │  ├─ reports/
  │  └─ logs/
  ├─ src/nofomo/
  │  ├─ main.py
  │  ├─ settings.py
  │  ├─ models.py
  │  ├─ source_loader.py
  │  ├─ rss_fetcher.py
  │  ├─ deduper.py
  │  ├─ normalizer.py
  │  ├─ summarizer.py
  │  ├─ keyword_matcher.py
  │  ├─ report_builder.py
  │  ├─ report_store.py
  │  ├─ telegram_sender.py
  │  ├─ telegram_feedback.py
  │  └─ logging_utils.py
  ├─ tests/
  │  ├─ test_deduper.py
  │  ├─ test_normalizer.py
  │  ├─ test_summarizer.py
  │  ├─ test_keyword_matcher.py
  │  ├─ test_report_builder.py
  │  └─ test_feedback_parser.py
  └─ pyproject.toml

  ---
  4. 模块边界

  配置层

  - settings.py
  - source_loader.py

  职责：
  - 读取 YAML 配置
  - 返回结构化配置对象

  内容处理层

  - rss_fetcher.py
  - deduper.py
  - normalizer.py
  - summarizer.py
  - keyword_matcher.py

  职责：
  - 从 RSS 拉到“可入日报内容”

  报告层

  - report_builder.py
  - report_store.py

  职责：
  - 构造日报结构
  - 保存 / 读取日报归档

  Telegram 集成层

  - telegram_sender.py
  - telegram_feedback.py

  职责：
  - 发送日报
  - 拉取并解析反馈命令

  入口层

  - main.py

  职责：
  - 暴露 run-digest / sync-feedback CLI

  ---
  5. 核心数据结构

  SourceConfig

  来源配置：
  - id
  - platform
  - name
  - rss_url
  - enabled

  NormalizedItem

  标准化后的内容对象：
  - item_id
  - source_id
  - platform
  - source_name
  - title
  - url
  - published_at
  - guid
  - raw_summary
  - normalized_text
  - summary_short
  - summary_long
  - matched_keywords
  - is_highlight

  DailyReport

  日报归档对象：
  - report_date
  - generated_at
  - total_new_items
  - total_sources
  - total_highlights
  - failed_sources
  - highlights
  - normal_items

  FeedbackRecord

  反馈记录对象：
  - item_id
  - report_date
  - feedback_type
  - source_id
  - source_name
  - matched_keywords
  - telegram_user_id
  - telegram_chat_id
  - telegram_message_id
  - created_at

  ---
  6. item_id 与去重策略

  item_id

  建议生成方式：

  - 优先基于 source_id + canonical_url + published_at
  - 否则退回 source_id + guid + title + published_at
  - 最终取短哈希作为稳定引用 ID

  用途：
  - 出现在日报中
  - 供 /like <item_id> / /dislike <item_id> 使用
  - 用于 feedback 归档关联

  去重键

  按 spec 优先级：
  1. 原始链接
  2. source_id + guid
  3. title + published_at

  seen 写入时机

  建议在日报成功发送后再写入 seen_items.json，避免中途失败导致内容丢失。

  ---
  7. Telegram 交互设计

  日报消息内容

  日报中每条内容都带稳定 item_id，例如：

  [重点关注]
  [V2EX] Indie Hackers Daily
  标题：...
  摘要：...
  命中关键词：AI, agent
  原文：https://...
  反馈命令：/like 4f8c2ad91b3e
           /dislike 4f8c2ad91b3e

  普通更新也同样带 item_id 和反馈命令提示，但摘要更短。

  反馈同步方式

  用户阅读后手动运行：

  python -m nofomo.main sync-feedback

  处理逻辑：
  1. 读取 telegram_state.json 中上次 offset
  2. 调 Telegram getUpdates
  3. 查找消息文本中的 /like <item_id> 或 /dislike <item_id>
  4. 校验 item 是否存在于历史日报
  5. 追加写入 feedback.jsonl
  6. 更新 offset

  第一版不做

  - inline keyboard
  - webhook
  - 常驻 polling
  - 自动回改 Telegram 历史消息

  ---
  8. 错误处理策略

  RSS 拉取失败

  - 记录日志
  - 不中断其他源
  - 在日报中列出失败来源

  单条内容异常

  - 跳过该条
  - 记录错误
  - 不影响本轮其他条目

  Telegram 发送失败

  - 日报先本地归档
  - 记录失败日志
  - 允许后续手动重发

  feedback 同步异常

  - 保留旧 offset，不前移
  - 防止消息被错误跳过

  这个点很关键：
  只有成功处理到某条 update 后，才推进 offset。

  ---
  9. 测试策略

  第一版重点测纯逻辑模块，不在一开始就重压端到端。

  单元测试重点

  - deduper.py
    - 三层去重优先级
    - 已见 / 未见判断
  - normalizer.py
    - RSS entry 缺字段时的兼容行为
    - HTML / 空白处理
  - summarizer.py
    - summary 优先
    - fallback 到正文裁剪
  - keyword_matcher.py
    - 多关键词命中
    - 标题/摘要/正文都可命中
  - report_builder.py
    - highlights / normal_items 分组
    - overview 统计正确
  - telegram_feedback.py
    - 正确解析 /like id
    - 忽略无效命令
    - 忽略不存在的 item_id

  集成测试可放轻

  第一版只要补少量：
  - mock RSS 输入
  - mock Telegram API 响应
  - 验证 run-digest 产出报告文件
  - 验证 sync-feedback 能写入 feedback 文件

  ---
  10. 第一版开发顺序

  我建议按下面顺序做，能最快跑通主链路：

  1. 配置与数据模型
  2. RSS 拉取 + 去重
  3. 标准化 + 规则摘要
  4. 关键词匹配
  5. 日报构建与本地归档
  6. Telegram 发送
  7. feedback 命令同步
  8. 日志与错误处理补齐
  9. 端到端联调

  这个顺序的好处是：
  - 先把“从 RSS 到本地日报”主干跑通
  - Telegram 发送是输出层，后挂上去
  - feedback 是独立链路，最后加不会阻塞主功能验证