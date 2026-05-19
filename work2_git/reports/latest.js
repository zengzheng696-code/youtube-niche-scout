window.__PET_SCOUT_REPORT__ = {
  "meta": {
    "generated_at": "2026-05-19T15:20:27+00:00",
    "week_id": "2026-W21",
    "market": "UK",
    "summary": "本周基于 YouTube 内容信号识别到 2 个可测宠物用品机会；最高分是 Dog post-walk paw washer (75/100, high)。数据源状态: fixture。",
    "category_policy": "Exclude pet food, treats, supplements, medicine and drug-like claims by default.",
    "source_policy": "Use YouTube Data API as a content-demand signal: search.list, videos.list, commentThreads.list."
  },
  "source_status": {
    "youtube": {
      "status": "fixture",
      "records": 3,
      "note": "local fixture data for tests and demos"
    }
  },
  "products": [
    {
      "product_key": "muddy-paw-washer",
      "name": "Dog post-walk paw washer",
      "pet": "Dog",
      "category": "Outdoor Care",
      "problem": "英国雨天和泥地遛狗后，狗爪清洁耗时且会弄脏车和地毯。",
      "risk": "Low",
      "suggested_price": "£18.99-24.99",
      "supply_price": "TBD",
      "moq": "TBD",
      "landing_page_angle": "30 秒清洁遛狗后的泥爪，减少地毯和车内清洁压力。",
      "creative_angles": [
        "雨天进门前后对比",
        "车后备箱泥爪场景",
        "小户型地毯保护"
      ],
      "test_plan": [
        "做雨天遛狗落地页",
        "拍 3 条 before/after UGC",
        "测试 £19.99 单品和毛巾套装"
      ],
      "risks": [
        "尺寸不适配会导致退货",
        "YouTube 是内容需求代理，不代表真实销量"
      ],
      "scores": {
        "youtube_search": 92,
        "youtube_velocity": 78,
        "youtube_engagement": 62,
        "youtube_comments": 58,
        "creator_diversity": 80
      },
      "score": 75,
      "confidence": "high",
      "signals": {
        "youtube_search": {
          "enabled": true,
          "score": 92,
          "summary": "18 videos across 8 channels",
          "metric": "search coverage"
        },
        "youtube_velocity": {
          "enabled": true,
          "score": 78,
          "summary": "avg 6400 views/day",
          "metric": "view velocity"
        },
        "youtube_engagement": {
          "enabled": true,
          "score": 62,
          "summary": "3.4% like/comment engagement proxy",
          "metric": "engagement proxy"
        },
        "youtube_comments": {
          "enabled": true,
          "score": 58,
          "summary": "6 pain comments from 20 sampled comments",
          "metric": "comment pain proxy"
        },
        "creator_diversity": {
          "enabled": true,
          "score": 80,
          "summary": "8 unique channels",
          "metric": "creator diversity"
        }
      },
      "evidence": [
        {
          "source": "youtube",
          "title": "How to clean muddy dog paws after a rainy walk",
          "url": "https://www.youtube.com/watch?v=demo001",
          "summary": "128000 views · 4100 likes · 320 comments · UK dog care creator",
          "metric": "dog paw washer muddy paws"
        },
        {
          "source": "youtube",
          "title": "Muddy paws car boot clean up routine",
          "url": "https://www.youtube.com/watch?v=demo002",
          "summary": "84000 views · 2500 likes · 190 comments · Pet travel channel",
          "metric": "rainy dog walk clean paws"
        }
      ],
      "excluded": false
    },
    {
      "product_key": "cat-calming-lick-mat",
      "name": "Cat calming lick mat",
      "pet": "Cat",
      "category": "Anxiety & Enrichment",
      "problem": "室内猫无聊、洗澡剪指甲或独处时容易紧张，主人想找低门槛安抚工具。",
      "risk": "Low",
      "suggested_price": "£12.99-16.99",
      "supply_price": "TBD",
      "moq": "TBD",
      "landing_page_angle": "给室内猫一个可清洗、低成本的 grooming calm-down routine。",
      "creative_angles": [
        "剪指甲前舔食垫 routine",
        "indoor cat boredom relief",
        "可冷冻慢食演示"
      ],
      "test_plan": [
        "测试 grooming calm 角度",
        "组合玩具做 AOV",
        "收集评论区猫年龄和使用场景"
      ],
      "risks": [
        "不能宣称治疗焦虑",
        "材质需明确 food-grade silicone"
      ],
      "scores": {
        "youtube_search": 74,
        "youtube_velocity": 69,
        "youtube_engagement": 71,
        "youtube_comments": 52,
        "creator_diversity": 60
      },
      "score": 66,
      "confidence": "medium",
      "signals": {
        "youtube_search": {
          "enabled": true,
          "score": 74,
          "summary": "11 videos across 6 channels",
          "metric": "search coverage"
        },
        "youtube_velocity": {
          "enabled": true,
          "score": 69,
          "summary": "avg 3100 views/day",
          "metric": "view velocity"
        },
        "youtube_engagement": {
          "enabled": true,
          "score": 71,
          "summary": "3.9% like/comment engagement proxy",
          "metric": "engagement proxy"
        },
        "youtube_comments": {
          "enabled": true,
          "score": 52,
          "summary": "4 pain comments from 15 sampled comments",
          "metric": "comment pain proxy"
        },
        "creator_diversity": {
          "enabled": true,
          "score": 60,
          "summary": "6 unique channels",
          "metric": "creator diversity"
        }
      },
      "evidence": [
        {
          "source": "youtube",
          "title": "Calm cat nail trim routine with a lick mat",
          "url": "https://www.youtube.com/watch?v=demo003",
          "summary": "76000 views · 3300 likes · 210 comments · Cat grooming creator",
          "metric": "cat lick mat grooming stress"
        }
      ],
      "excluded": false
    }
  ],
  "excluded_products": [
    {
      "product_key": "single-protein-treat",
      "name": "Freeze-dried single-protein treat",
      "pet": "Multi",
      "category": "Functional Treats",
      "problem": "敏感肠胃宠物主人寻找低敏、单一蛋白零食。",
      "risk": "Medium",
      "suggested_price": "TBD",
      "supply_price": "TBD",
      "moq": "TBD",
      "landing_page_angle": "TBD",
      "creative_angles": [],
      "test_plan": [],
      "risks": [
        "默认排除食品/药品/保健品或高合规声明"
      ],
      "scores": {
        "youtube_search": 90,
        "youtube_velocity": 76,
        "youtube_engagement": 75,
        "youtube_comments": 60,
        "creator_diversity": 70
      },
      "score": 74,
      "confidence": "high",
      "signals": {
        "youtube_search": {
          "enabled": true,
          "score": 90,
          "summary": "high content coverage",
          "metric": "search coverage"
        }
      },
      "evidence": [],
      "excluded": true
    }
  ],
  "next_week_actions": [
    "配置 YOUTUBE_API_KEY 并控制每周查询预算。",
    "对 Top 3 产品各做 1 个落地页和 3 条短视频素材。",
    "用独立站 CTR、ATC、询盘价和样品物流成本回填下周评分。"
  ]
};
