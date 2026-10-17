# 固定评测集

cases.json 保存固定输入、Mock 的精确期望标签和业务失败场景。backend/tests/test_mvp.py 将场景转为断言，使用隔离数据库，不调用真实模型。Mock 不用于衡量模型准确率。

真实模型与确定性测试分开：

```powershell
$env:PYTHONPATH='backend'
uv run python evals/run_live.py --allow-live
```

先在 .env 配置 MODEL_API_KEY、MODEL_API_BASE_URL 和 MODEL_NAME。脚本明确强制 Live 模式，缺少 Key 则拒绝执行；输出每个案例的结构校验状态、耗时和验证后草稿到 .cache/live-eval.json，不输出密钥或隐藏推理。真实模型可能产生费用，脚本不会被默认 pytest 或 CI 调用。

当前没有执行过真实模型评测，没有模型准确率或性能结论。下一阶段扩充人工标注检索集和用户体验规则，记录 Prompt / workflow / retrieval 版本后比较；不能把 Mock 精确匹配率当作模型效果。
