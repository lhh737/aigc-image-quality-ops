window.DASHBOARD_DATA = {
  "meta": {
    "project": "AIGC 多模态数据质量评估与运营复现",
    "generated_at": "2026-10-19T18:10:39+08:00",
    "n_human": 36,
    "n_vlm": 112,
    "platforms": [
      "jimeng",
      "kling",
      "seedream"
    ],
    "stage": "pilot"
  },
  "leaderboard": [
    {
      "platform": "jimeng",
      "n": 12,
      "quality_mean": 4.508,
      "quality_ci": [
        4.379,
        4.646
      ],
      "constraint_pass": 0.972,
      "first_pass": 0.917,
      "latency_s": null,
      "cost_raw": null
    },
    {
      "platform": "seedream",
      "n": 12,
      "quality_mean": 4.288,
      "quality_ci": [
        4.029,
        4.538
      ],
      "constraint_pass": 0.957,
      "first_pass": 0.75,
      "latency_s": 7.2,
      "cost_raw": 0.0
    },
    {
      "platform": "kling",
      "n": 12,
      "quality_mean": 4.196,
      "quality_ci": [
        3.758,
        4.558
      ],
      "constraint_pass": 0.988,
      "first_pass": 0.667,
      "latency_s": null,
      "cost_raw": null
    }
  ],
  "category": {
    "categories": [
      "人像",
      "商品",
      "海报"
    ],
    "platforms": [
      "jimeng",
      "kling",
      "seedream"
    ],
    "matrix": {
      "jimeng": {
        "人像": 4.5,
        "商品": 4.75,
        "海报": 4.275
      },
      "kling": {
        "人像": 4.738,
        "商品": 3.5,
        "海报": 4.35
      },
      "seedream": {
        "人像": 3.925,
        "商品": 4.35,
        "海报": 4.588
      }
    }
  },
  "scene": {
    "categories": [
      "ecommerce",
      "portrait",
      "social"
    ],
    "platforms": [
      "jimeng",
      "kling",
      "seedream"
    ],
    "matrix": {
      "jimeng": {
        "ecommerce": 4.75,
        "portrait": 4.5,
        "social": 4.275
      },
      "kling": {
        "ecommerce": 3.5,
        "portrait": 4.738,
        "social": 4.35
      },
      "seedream": {
        "ecommerce": 4.35,
        "portrait": 3.925,
        "social": 4.588
      }
    }
  },
  "scene_weighted": {
    "weights": {
      "ecommerce": 0.4,
      "social": 0.35,
      "portrait": 0.25
    },
    "scores": {
      "jimeng": 4.521,
      "kling": 4.107,
      "seedream": 4.327
    }
  },
  "per_prompt": {
    "prompts": [
      "E01",
      "E02",
      "E03",
      "E04",
      "H01",
      "H02",
      "H03",
      "H04",
      "T01",
      "T02",
      "T03",
      "T04"
    ],
    "platforms": [
      "jimeng",
      "kling",
      "seedream"
    ],
    "matrix": {
      "jimeng": {
        "E01": 4.7,
        "E02": 5.0,
        "E03": 4.65,
        "E04": 4.65,
        "H01": 4.65,
        "H02": 4.35,
        "H03": 4.35,
        "H04": 4.65,
        "T01": 4.05,
        "T02": 4.35,
        "T03": 4.35,
        "T04": 4.35
      },
      "kling": {
        "E01": 3.0,
        "E02": 4.35,
        "E03": 2.65,
        "E04": 4.0,
        "H01": 4.65,
        "H02": 4.65,
        "H03": 5.0,
        "H04": 4.65,
        "T01": 4.35,
        "T02": 4.65,
        "T03": 4.7,
        "T04": 3.7
      },
      "seedream": {
        "E01": 4.35,
        "E02": 5.0,
        "E03": 4.35,
        "E04": 3.7,
        "H01": 4.35,
        "H02": 3.35,
        "H03": 4.35,
        "H04": 3.65,
        "T01": 4.35,
        "T02": 4.65,
        "T03": 4.65,
        "T04": 4.7
      }
    }
  },
  "win_rate": {
    "platforms": [
      "jimeng",
      "kling",
      "seedream"
    ],
    "matrix": {
      "jimeng": {
        "jimeng": null,
        "kling": 0.5,
        "seedream": 0.583
      },
      "kling": {
        "jimeng": 0.5,
        "kling": null,
        "seedream": 0.583
      },
      "seedream": {
        "jimeng": 0.417,
        "kling": 0.417,
        "seedream": null
      }
    },
    "n_prompts": 12
  },
  "friedman": {
    "available": true,
    "stat": 0.571,
    "p": 0.751477293075286,
    "n_prompts": 12,
    "platforms": [
      "jimeng",
      "kling",
      "seedream"
    ]
  },
  "wilcoxon": [
    {
      "a": "jimeng",
      "b": "seedream",
      "p_raw": 0.18199085778370594,
      "median_diff": 0.15,
      "p_holm": 0.546
    },
    {
      "a": "jimeng",
      "b": "kling",
      "p_raw": 0.2829343037511921,
      "median_diff": 0.0,
      "p_holm": 0.5659
    },
    {
      "a": "kling",
      "b": "seedream",
      "p_raw": 0.8383602338389031,
      "median_diff": 0.025,
      "p_holm": 0.8384
    }
  ],
  "stability": {
    "available": false
  },
  "human_vlm": {
    "available": true,
    "n": 36,
    "by_dim": {
      "g1": {
        "n": 36,
        "exact": 0.778,
        "adjacent": 0.972,
        "mae": 0.25,
        "alpha": 0.14
      },
      "g2": {
        "n": 36,
        "exact": 0.583,
        "adjacent": 0.944,
        "mae": 0.472,
        "alpha": 0.201
      },
      "g3": {
        "n": 36,
        "exact": 0.528,
        "adjacent": 0.972,
        "mae": 0.5,
        "alpha": 0.183
      }
    }
  },
  "human_retest": {
    "available": true,
    "n": 11,
    "main_file": "human_r1.csv",
    "retest_file": "human_r1_retest.csv",
    "interval_hours": 1.71,
    "by_dim": {
      "g1": {
        "exact": 0.818,
        "adjacent": 0.909,
        "mae": 0.273
      },
      "g2": {
        "exact": 0.455,
        "adjacent": 0.909,
        "mae": 0.636
      },
      "g3": {
        "exact": 0.545,
        "adjacent": 1.0,
        "mae": 0.455
      }
    },
    "note": "重测间隔不足 48 小时，属于短期一致性，不等同于 48h test–retest。"
  },
  "badcases": [
    {
      "platform": "jimeng",
      "tag": "文字乱码",
      "count": 1,
      "rate": 0.083
    }
  ],
  "constraint_failures": {
    "total": 7,
    "by_platform_check": [
      {
        "platform": "jimeng",
        "check": "两片柠檬",
        "count": 1
      },
      {
        "platform": "jimeng",
        "check": "小字“花好月圆”",
        "count": 1
      },
      {
        "platform": "kling",
        "check": "深色长裤",
        "count": 1
      },
      {
        "platform": "seedream",
        "check": "一杯拉花",
        "count": 1
      },
      {
        "platform": "seedream",
        "check": "两杯拿铁",
        "count": 1
      },
      {
        "platform": "seedream",
        "check": "两片柠檬",
        "count": 1
      },
      {
        "platform": "seedream",
        "check": "无品牌标志",
        "count": 1
      }
    ],
    "details": [
      {
        "platform": "jimeng",
        "prompt_id": "T02",
        "blind_id": "BFC2BB10208",
        "check": "小字“花好月圆”",
        "g1": 5,
        "g2": 4,
        "g3": 4,
        "quality": 4.35,
        "failure_tags": "文字乱码",
        "notes": "花好月圆文字错误"
      },
      {
        "platform": "kling",
        "prompt_id": "H03",
        "blind_id": "BE8EC8AA5A4",
        "check": "深色长裤",
        "g1": 5,
        "g2": 5,
        "g3": 5,
        "quality": 5.0,
        "failure_tags": "",
        "notes": ""
      },
      {
        "platform": "seedream",
        "prompt_id": "E03",
        "blind_id": "BD408F478D3",
        "check": "无品牌标志",
        "g1": 5,
        "g2": 4,
        "g3": 4,
        "quality": 4.35,
        "failure_tags": "",
        "notes": ""
      },
      {
        "platform": "jimeng",
        "prompt_id": "E01",
        "blind_id": "B53E47A1B47",
        "check": "两片柠檬",
        "g1": 5,
        "g2": 4,
        "g3": 5,
        "quality": 4.7,
        "failure_tags": "",
        "notes": ""
      },
      {
        "platform": "seedream",
        "prompt_id": "E01",
        "blind_id": "BA923E7CE44",
        "check": "两片柠檬",
        "g1": 5,
        "g2": 4,
        "g3": 4,
        "quality": 4.35,
        "failure_tags": "",
        "notes": ""
      },
      {
        "platform": "seedream",
        "prompt_id": "H04",
        "blind_id": "BCEC66CD323",
        "check": "两杯拿铁",
        "g1": 4,
        "g2": 4,
        "g3": 3,
        "quality": 3.65,
        "failure_tags": "",
        "notes": ""
      },
      {
        "platform": "seedream",
        "prompt_id": "H04",
        "blind_id": "BCEC66CD323",
        "check": "一杯拉花",
        "g1": 4,
        "g2": 4,
        "g3": 3,
        "quality": 3.65,
        "failure_tags": "",
        "notes": ""
      }
    ]
  },
  "low_scores": [
    {
      "platform": "kling",
      "prompt_id": "E03",
      "blind_id": "B7FC8BD543A",
      "g1": 3,
      "g2": 3,
      "g3": 2,
      "quality": 2.65,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "kling",
      "prompt_id": "E01",
      "blind_id": "B88088E8B9F",
      "g1": 3,
      "g2": 3,
      "g3": 3,
      "quality": 3.0,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "seedream",
      "prompt_id": "H02",
      "blind_id": "BB79CB32230",
      "g1": 4,
      "g2": 3,
      "g3": 3,
      "quality": 3.35,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "seedream",
      "prompt_id": "H04",
      "blind_id": "BCEC66CD323",
      "g1": 4,
      "g2": 4,
      "g3": 3,
      "quality": 3.65,
      "failed_checks": [
        "两杯拿铁",
        "一杯拉花"
      ],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "kling",
      "prompt_id": "T04",
      "blind_id": "BA2E4CED012",
      "g1": 5,
      "g2": 3,
      "g3": 3,
      "quality": 3.7,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "seedream",
      "prompt_id": "E04",
      "blind_id": "B36797C5BF1",
      "g1": 5,
      "g2": 3,
      "g3": 3,
      "quality": 3.7,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "kling",
      "prompt_id": "E04",
      "blind_id": "BB1CEB3224C",
      "g1": 5,
      "g2": 4,
      "g3": 3,
      "quality": 4.0,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "jimeng",
      "prompt_id": "T01",
      "blind_id": "BAB48E20A96",
      "g1": 5,
      "g2": 3,
      "g3": 4,
      "quality": 4.05,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "seedream",
      "prompt_id": "H01",
      "blind_id": "B12078842D9",
      "g1": 5,
      "g2": 4,
      "g3": 4,
      "quality": 4.35,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "seedream",
      "prompt_id": "E01",
      "blind_id": "BA923E7CE44",
      "g1": 5,
      "g2": 4,
      "g3": 4,
      "quality": 4.35,
      "failed_checks": [
        "两片柠檬"
      ],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "kling",
      "prompt_id": "E02",
      "blind_id": "BC02A0BD3EC",
      "g1": 5,
      "g2": 4,
      "g3": 4,
      "quality": 4.35,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    },
    {
      "platform": "jimeng",
      "prompt_id": "T04",
      "blind_id": "B63314E249A",
      "g1": 5,
      "g2": 4,
      "g3": 4,
      "quality": 4.35,
      "failed_checks": [],
      "failure_tags": "",
      "notes": ""
    }
  ],
  "limitations": [
    "pilot 规模小，结论是方向性的，不是公开 benchmark。",
    "闭源平台会改写提示词/做后处理，本项目测的是产品交付质量。",
    "平台版本会漂移，结论只代表测试日期。",
    "VLM 是第二评分通道，不是第二个人工标注者。",
    "可灵/即梦为手动采集，延迟与积分为空；Seedream 为 API 延迟。"
  ]
};
