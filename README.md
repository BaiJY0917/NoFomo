# **NoFomo**

> 用更少时间，获取更有价值的信息。

用 AI 消解 “AI slop”（低质量、批量生成的信息噪音）。

---

## **✨ Features**

- 📰 **多源聚合**：基于 RSSHub 汇总来自多个平台的内容
- 🤖 **AI 自动摘要**：快速判断内容是否值得阅读
- 🎯 **偏好学习**：通过 like / unlike 持续优化推荐
- ⚡ **低摩擦使用**：基于 Telegram Bot，无需额外客户端
- 🧘 **抗 FOMO 设计**：减少信息焦虑，同时不错过重要内容

---

## **🚀 Quick Start**

### **1. 准备环境**

- Python 3.12+
- RSSHub 实例
- Telegram Bot Token

---

### **2. 配置 NoFomo**

```
# Clone the repository
git clone <repository-url>
cd NoFomo
​
# Install dependencies
pip install -e .
​
# Configure RSS Sources
Edit `config/sources.yaml`
​
# Configure Keywords
Edit `config/keywords.yaml`
​
# Configure Telegram
Edit `config/telegram.yaml`
To get your bot token, talk to [@BotFather](https://t.me/botfather) on Telegram.
```


---



### **3. 使用**

```
# 生成每日摘要
nofomo run-digest

# 同步阅读反馈
nofomo sync-feedback
```
---

### **4. 使用流程**

1. 添加订阅源（RSS）
2. 系统抓取内容
3. AI 生成摘要
4. 在 Telegram 中查看内容
5. 通过 👍 / 👎 训练你的偏好

---

## **🧠 Why NoFomo?**

现代互联网内容分发高度碎片化，典型用户的信息来源通常包括：

YouTube / Weibo / X / V2EX / Reddit / Bilibili / Telegram / 公众号 / 博客 / 知识星球 / 新闻资讯

这些信息源通常只能在各自平台内阅读，且更新与排序方式并不总是按时间线呈现。通过自建 RSSHub 并配合 RSS 阅读器，确实可以解决约 80% 的聚合问题；但对“个人化阅读效率”来说仍有明显缺口。

### **主要问题**

1. **内容膨胀与质量失控**：自媒体依赖高频更新获取流量与收益，低营养内容本就普遍；在 AI 普及后，内容生产速度更快，但质量更难保证，甚至出现“日更七八条碎碎念”的情况。
2. **收藏/待读永远看不完**：当你同时关注多个方向的创作者（娱乐、科技、生活、健身等），即使他们都在持续输出高价值内容，阅读任务也会被指数式堆高。例如关注 10 位创作者、每人每天发布 2 条内容，就意味着每天需要处理约 20 条信息。
3. **过滤成本过高**：大部分内容并无阅读价值（生活碎片、梗图、圈内互转等）。人工浏览筛选浪费时间；关键词过滤又需要不断维护与扩展，且容易误伤。
4. **取关与 FOMO 的矛盾**：理性上取关多数账号并不会影响生活，但完全忽略网络信息又容易触发 FOMO（错失恐惧）情绪。

---

## **🎯 Design Goals**

- **摘要优先**：先用 AI 总结，再决定是否阅读原文
- **偏好驱动**：系统持续学习你的兴趣，而不是依赖规则过滤
- **降低决策成本**：让“看不看”变得几乎无成本

---

## **🏗️ Architecture**

### **Data Layer**

- RSSHub：聚合多平台内容
- cookieCloud：维持登录态（部分平台）

### **Backend**

- 订阅源管理
- 定时抓取
- 已读 / 未读状态管理
- AI 摘要生成
- 用户偏好建模

### **Frontend**

- Telegram Bot（轻量交互）

---

## **📌 Todo**

- [ ]  Telegram Bot支持反馈按钮
- [ ] 摘要按照更新内容分类汇总
- [ ]  增加推荐算法优化（embedding / ranking）
- [ ]  支持后台运行


---

## **⭐ Philosophy**

> NoFomo 的目标不是“阅读更多”，而是“用更少时间获取更有价值的信息”。

---

## **📄 License**

MIT License