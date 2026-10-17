# 从 Java 后端到 Agent 工程

## 建议阅读顺序

1. app/schemas.py：输入/输出 DTO、严格工具参数、Literal 状态和未知值。
2. app/workflow.py：状态、节点、条件边、编译调用和审计包装。
3. app/tools.py：工具注册、允许列表、权限、验证和事务内写入。
4. app/model_adapter.py：Mock/Live 切换、模型请求工具、结构化校验和错误分类。
5. app/models.py / db.py / migrations：ORM、Session、外键、JSON 更新、迁移。
6. app/main.py：HTTP 用例编排、幂等、批准 API、反馈与偏好确认。
7. tests/test_mvp.py：把业务边界写成失败可复现的断言。
8. frontend/src/App.tsx / components.tsx：预览、编辑、确认、可见运行步骤。

以上后端路径相对 backend/。不必一次记住所有依赖，先用 Mock 走完“海洋兴趣 → 确认 → 10 分钟/0 元/低精力探索 → 接受 → 反馈”。

## Python 类如何对应熟悉的 Java 概念

Pydantic BaseModel 类似 DTO + Bean Validation，但还负责运行时解析和 JSON schema。extra=forbid 拒绝未知参数，防止模型偷偷塞入任意工具参数；Field 给时间/预算设置边界；Literal 限定精力或状态。None 是未知，预算 0 是明确免费，二者不能混同。

SQLAlchemy ORM 类似 JPA 实体；Session 类似事务上下文，同时维护 identity map。flush 把 SQL 发送到数据库并取得 ID，但还没有 commit；批准操作先 flush 创建 Quest，再写关联表，最后与批准记录一起 commit。失败 rollback 避免“批准记录成功、实体没保存”的不一致。

Alembic 类似数据库版本迁移工具。models.py 是程序中的结构；版本文件是如何把现有数据库升级到这个结构。修改实体后不能依靠 create_all 更新正式表，要新增迁移再检查。

FastAPI Depends 类似依赖注入；get_session 的 yield 保证请求结束关闭 Session。端点用 Pydantic DTO 验证请求；业务中的 HTTPException 区分 404/409/422 等可预期情况。

## LangGraph 负责什么

看 AgentState：它是图在节点之间交换的公开结构状态，不是模型的思维过程。node handler 接收 state，返回局部更新；图根据边选择下个节点，compile 后才能 invoke。

understand_request 在第一版明确校验请求类型；不让模型随意决定要写数据库。检索节点查询真实历史，偏好节点读明确数据，生成节点仅让模型提出候选，验证节点用 Python 规则验证。await_user_decision 的含义是把待确认结果返回给 UI；不是一个一直占用进程的暂停线程。

node 包装器统一记录名称、成功/失败、耗时，并保存快照。这比每个节点写重复日志更容易检查。审批和反馈用独立短图，关闭节点内 commit，让调用方管理整体写事务。

## Tool Calling 不是“给模型执行代码”

工具是带结构化参数的受控函数。真实模型收到一个指定工具的 JSON schema，用 tool_calls 提交草稿/候选参数。ModelAdapter 校验工具名、数量和 Pydantic schema；后端才执行数据库查询或业务规则。

ToolRegistry 的 call 顺序：检查名字是否允许 → schema 校验 → 检查批准上下文 → 执行 handler → 保存结果状态。即使模型声称“用户已经同意”，也无法设置后端 approved 上下文。批准由用户明确提交 HTTP 决定 API 产生。模型无任意 Python、SQL 或系统命令能力。

MVP 的工具编排多数由图确定，模型只填允许的结构。这是一个容易学习和审计的起点；不要把动态自主工具选择、循环次数上限和错误重试一开始全部放进大函数。

## 个人偏好与真实性

explicit 只存用户填写或确认的数据。candidates 只是由实际反馈形成的可检查摘要，附真实 Reflection ID。用户喜欢“文字记录”，并不证明他永远喜欢文字记录；先展示候选，由用户确认或删除，确认后可编辑明确偏好。跳过仅保存 skipped 和原因，不写“懒惰”之类推测。

原始文字独立保存，让你能检查模型把哪句话整理成了什么。Mock 未知动机留空。真实模型输出也不是事实，要预览、修改和确认。推荐引用真实 ID 是最低条件，仍需对正文做人工复核。

## 失败与恢复怎么学习

在测试中找 test_model_failure_audited_and_retry：用 monkeypatch 让适配层模拟 timeout，确认 502、failed 运行和无正式 Star。恢复适配层后 retry 创建新运行，原失败记录不消失。

再看 test_edited_proposal_validates_again：用户把分钟或预算调超，批准仍返回 422。UI 修改和后端校验是两层不同责任，前端 required/min 不能代替后端规则。

Idempotency-Key 解决“响应丢失后重发”。同 key 同 payload 返回已成功或待确认的同一运行；仍在执行或此前失败的请求返回 409，失败响应附运行 ID，不冒充创建成功。同 key 不同 payload 也返回 409。生成失败可通过重试接口创建新运行；反馈失败需先检查原因，再用新请求提交。批准记录再用候选 index + fingerprint 防重，数据库唯一约束是最后一层。并发行为还依赖数据库锁，SQLite 不能证明 PostgreSQL 下的所有并发性质。

## 你可以亲自做的练习

- 运行 Mock 并在运行页逐个对照工具与节点，检查检索 match_basis 是否真实。
- 把星星归档，确认档案能找到、推荐不再使用它。
- 生成方案后将偏好最大分钟改为 1，再批准旧方案，观察重新验证。
- 留下喜欢的方面，确认候选出现但明确偏好未自动改变。
- 给规则新增一个可测试的约束（例如记录必须少于三步），先写失败场景，再实现验证。
- 拿真实模型时先运行 evals 的可选脚本，人工核对输出；不要用 Mock 测试通过率宣传模型效果。

当前推荐先处理用户已提出的输入文案与流程引导，再在 PostgreSQL 和所选真实模型上补证据，之后依据评测扩展多兴趣提取、澄清续问与模板；执行顺序以 [路线图](../ROADMAP.md) 和 [正式待办](PRODUCT_BACKLOG.md) 的最新评估为准。语义检索的接口在 semantic.py，尚没有实现，更没有虚构检索提升数据。
