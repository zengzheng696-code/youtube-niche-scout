# YouTube Pet Product Sniffer

面向英区宠物跨境电商独立站的 YouTube API 自动选品嗅探工具。它先用种子词搜索宠物内容，再从视频标题/描述里抽取产品短语并聚类，最后用 `videos.list` 和 `commentThreads.list` 给候选品打分，输出可交互仪表盘、Markdown 报告、CSV 和证据 JSON。

注意：YouTube 是内容需求代理，不等于真实销量。报告用于发现值得测试的产品假设，不直接代表成交。

## 快速使用

1. 生成演示报告：

   ```powershell
   python scripts/generate_weekly_report.py --fixture
   ```

2. 双击打开：

   ```text
   D:\codex\work2\index.html
   ```

3. 真实运行：

   ```powershell
   Copy-Item .env.example .env.local
   # 在 .env.local 填入 YOUTUBE_API_KEY
   python scripts/generate_weekly_report.py
   ```

## YouTube 信号

- 搜索覆盖：指定宠物用品主题在近 30 天视频结果中的覆盖量。
- 观看速度：按发布时间折算的平均 views/day。
- 互动强度：likes + comments / views 的代理指标。
- 评论痛点：少量 top comments 中出现 problem、mess、smell、stress、muddy 等痛点词的密度。
- 创作者扩散：不同频道数量，避免只由单一博主带动。

## 配置

`.env.local` 可调预算：

```text
YOUTUBE_API_KEY=
YOUTUBE_REGION_CODE=GB
YOUTUBE_RELEVANCE_LANGUAGE=en
YOUTUBE_LOOKBACK_DAYS=30
YOUTUBE_MAX_PROFILES=10
YOUTUBE_MAX_SEED_QUERIES=8
YOUTUBE_MAX_RESULTS_PER_QUERY=8
YOUTUBE_COMMENTS_PER_VIDEO=5
YOUTUBE_SEED_QUERIES=
```

YouTube Data API quota 里，`search.list` 单次成本是 100 units，`videos.list` 和 `commentThreads.list` 通常是 1 unit。默认预算约为：8 个种子词，搜索成本约 800 units，再加少量视频和评论请求。

## 自动嗅探策略

1. 用宽泛种子词搜索：`pet gadgets`、`dog gadgets`、`pet cleaning hacks`、`cat enrichment ideas` 等。
2. 从视频标题/描述抽取产品短语：例如 `paw washer`、`litter box`、`cat shelf`、`car hammock`。
3. 按产品短语聚类，把同类视频合并成一个候选品。
4. 对 Top 聚类抽样评论，用痛点词密度、观看速度、互动率和创作者扩散评分。
5. 输出 Top 10 候选品，并标注证据视频链接。

可以用 `YOUTUBE_SEED_QUERIES=dog gadgets|cat enrichment|pet cleaning hacks` 自定义种子词。

默认排除宠物食品、零食、保健品、药品和类似医疗声明的高合规风险品类。

## 测试

```powershell
python -m unittest discover -s tests
python scripts/generate_weekly_report.py --fixture
node --check app.js
```

## 大模型报告增强

本项目包含一个可复用 skill：

```text
D:\codex\work2\skills\youtube-product-report-enhancer
```

它的职责是把 Python 生成的 YouTube 嗅探数据增强成更像选品顾问报告的内容，包括语义合并、痛点总结、卖点、短视频角度、风险和 7 天测试计划。

当前已生成：

- `reports/latest_llm_context.md`：给大模型的压缩上下文
- `reports/latest_enhanced.md`：增强版选品报告

如果要安装到 Codex 全局 skills 目录，双击：

```text
D:\codex\work2\install_report_enhancer_skill.bat
```

## 每周自动化

Codex 定时任务会在每周五 17:00 Asia/Shanghai 运行真实周报脚本。若 `YOUTUBE_API_KEY` 未配置，报告仍生成，但会在数据源状态里标注未启用。
