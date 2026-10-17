# 想法与决策记录

更新日期：2026-10-17（Asia/Shanghai）。

本文件保留原始问题、来源和评估结论；正式任务的优先级、状态、验收标准以 [PRODUCT_BACKLOG](PRODUCT_BACKLOG.md) 为准。里程碑见 [ROADMAP](../ROADMAP.md)，交付见 [CHANGELOG](../CHANGELOG.md)，证据见 [VERIFICATION](VERIFICATION.md)。

## 维护方式

- IDEA ID 稳定、全局唯一，不复用或删除；每次新增取已有最大序号加一，日期和来源必须真实。
- 先记录用户原话与场景，再区分源码观察、用户反馈和未经验证的假设。迁入旧路线图的事项不冒充本轮新用户意见。
- 同一问题合并到既有条目并追加日期、来源和变更原因；若已分配 ID，保留该条目并写“合并至 IDEA-xxx”，不抹去历史。
- 一项想法可关联多个任务。想法“纳入计划”不等于改动已经实现；某个关联任务暂缓或完成不会自动改变其他任务。
- 暂缓/拒绝保留原因、简单替代方案和重新评估触发条件；任务排序由 Backlog 的统一规则决定。
- 本轮界面检查为源码阅读和历史截图观察，未运行新浏览器验收；所有体验候选方案均尚未实现。
- 以下“处置”使用 proposed / planned / deferred 等决策标签；任务是否 done 仍须看任务及证据，不由想法标签推断。

## 记录

### IDEA-001

**流程引导优化**

- 记录日期：2026-10-11。
- 来源：用户本轮实际体验反馈。
- 原始想法/迁入内容：新用户在使用网站时，流程引导不够清晰，需要让用户更容易理解下一步要做什么。
- 当前观察与候选方案：已有首页收集/探索按钮、空状态入口、收集页三步说明；保存草稿后只显示已保存，接受候选后提示去体验手记。候选改进：无星星时优先引导收集；已有星星时解释如何探索；保存/接受后给直接入口；失败时指向运行详情与恢复。
- 处置：planned。
- 评估与决策：拆成首次使用与结果衔接两个任务；先改上下文提示和入口，暂不做强制导览、账号或任务打卡。
- 正式任务：[UX-001](PRODUCT_BACKLOG.md#ux-001)、[UX-002](PRODUCT_BACKLOG.md#ux-002)。
- 相关位置：frontend/src/App.tsx；frontend/src/components.tsx。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-002

**输入框示例与提示准确性**

- 记录日期：2026-10-11。
- 来源：用户本轮实际体验反馈。
- 原始想法/迁入内容：部分用户填写框内的示例和提示词不够准确，需要结合实际功能、字段含义和真实支持的输入格式重新设计。
- 当前观察与候选方案：探索页“预算（元，留空不限）”与后端沿用偏好上限的行为不一致；收集示例含多个主题但每次只生成一张草稿；列表提示只写逗号分隔，而 split 同时识别中英文逗号。候选改进：说明空预算/0元差别、单草稿限制、链接仅作引用、必填/选填和允许范围；以可直接使用的完整示例替换 https://…。
- 处置：planned。
- 评估与决策：纳入近期迭代；核对字段与 schema 后改文案，不借此新增抓取、多草稿或通用约束理解。
- 正式任务：[UX-003](PRODUCT_BACKLOG.md#ux-003)。
- 相关位置：frontend/src/App.tsx；frontend/src/components.tsx；backend/app/schemas.py；backend/app/tools.py。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-003

**视觉设计打磨与原创陪伴形象**

- 记录日期：2026-10-11。
- 来源：用户本轮实际体验反馈；合并旧 ROADMAP 的正式陪伴 SVG 项。
- 原始想法/迁入内容：整体美工仍需要打磨，希望保留 WonderOrbit 的产品定位，并更好地使用紫色、暖黄色星星、奶油白、温柔的童话感和可替换的原创陪伴形象。
- 当前观察与候选方案：已有紫/奶油白配色、暖黄星星、OrbitArt SVG、CSS companion 和响应式样式；历史截图显示装饰英文、小字号标签以及移动端横向导航。候选改进：统一色彩/排版层级、弱化装饰文字、突出操作与状态、检查移动端导航可发现性；正式形象以后替换现有占位。未测量当前对比度，不宣称无障碍通过或失败。
- 处置：planned。
- 评估与决策：拆成界面层级打磨与正式陪伴素材替换；前者纳入计划，后者等用户原创素材并暂缓。不能把陪伴形象变成业务核心。
- 正式任务：[UI-001](PRODUCT_BACKLOG.md#ui-001)、[UI-002](PRODUCT_BACKLOG.md#ui-002)。
- 相关位置：frontend/src/styles.css；frontend/src/components.tsx；frontend/src/App.tsx；.cache/e2e/ 历史截图（忽略目录）。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-004

**验证数据库、容器和 CI，并补并发证据**

- 记录日期：2026-10-11。
- 来源：迁入旧 ROADMAP v0.1 验证待办及 v0.3 可靠性项；VERIFICATION 未执行项。
- 原始想法/迁入内容：保留 PostgreSQL 迁移/回滚与集成、完整 Compose/Nginx、远程 CI、并发审批/反馈及事务故障验证。
- 当前观察与候选方案：相关 ORM、迁移、配置和独立 PostgreSQL 测试已存在，缺实际 PostgreSQL/容器/远程运行证据。
- 处置：planned。
- 评估与决策：验证现有实现，不把配置存在当验收通过；独立分为四项，环境等待写依赖。
- 正式任务：[INFRA-001](PRODUCT_BACKLOG.md#infra-001)、[INFRA-002](PRODUCT_BACKLOG.md#infra-002)、[INFRA-003](PRODUCT_BACKLOG.md#infra-003)、[INFRA-004](PRODUCT_BACKLOG.md#infra-004)。
- 相关位置：docker-compose.yml；.github/workflows/ci.yml；backend/tests/test_postgres.py；docs/VERIFICATION.md。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。
- 决策历史：2026-10-17，用户提供首次失败运行，合并到现有 INFRA-003，不另建 CI 重复任务。实际日志确认缺少 .cache 父目录，按最小方案在 pytest 前创建；本地验证完成，独立 PG 集成和修复后的远程 CI 仍待验收，不纳入业务或 UI 重构。

### IDEA-005

**真实模型兼容性和可复核 Agent 评测**

- 记录日期：2026-10-11。
- 来源：迁入旧 ROADMAP v0.1/v0.2；evals/README.md。
- 原始想法/迁入内容：验证所选兼容模型的工具调用、限流与结构输出；建立 Prompt/工作流版本和人工复核基线。
- 当前观察与候选方案：模型适配层与可选 live 评测脚本已实现，固定 Mock 案例已存在；尚无真实调用及人工标注效果基线。
- 处置：planned。
- 评估与决策：拆兼容性与评测；先选一个服务小批量验证，不新增多个模型供应商，不用 Mock 通过率宣传效果。
- 正式任务：[AGENT-001](PRODUCT_BACKLOG.md#agent-001)、[EVAL-001](PRODUCT_BACKLOG.md#eval-001)。
- 相关位置：backend/app/model_adapter.py；evals/run_live.py；evals/cases.json；evals/README.md。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-006

**多兴趣整理、澄清延续和更多轻体验规则**

- 记录日期：2026-10-11。
- 来源：迁入旧 ROADMAP v0.2。
- 原始想法/迁入内容：多兴趣草稿、澄清后的延续请求；扩充轻体验模板和可验证约束。
- 当前观察与候选方案：当前单草稿、返回问题但无延续请求协议、固定免费文字体验及少量确定性约束。
- 处置：proposed。
- 评估与决策：拆三项，先收集实际失败/不足案例；不要把自由文本约束判断直接交给模型批准。
- 正式任务：[AGENT-002](PRODUCT_BACKLOG.md#agent-002)、[AGENT-003](PRODUCT_BACKLOG.md#agent-003)、[AGENT-004](PRODUCT_BACKLOG.md#agent-004)。
- 相关位置：backend/app/schemas.py；backend/app/workflow.py；backend/app/rules.py；frontend/src/App.tsx。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-007

**有来源的反馈归纳候选偏好**

- 记录日期：2026-10-11。
- 来源：迁入旧 ROADMAP v0.2。
- 原始想法/迁入内容：反馈总结形成有来源的候选偏好，由用户确认。
- 当前观察与候选方案：已实现从明确 liked_aspects 生成候选并确认/删除；待评估的是模型归纳，而不是重做现有候选偏好功能。
- 处置：proposed。
- 评估与决策：只考虑可追溯、可拒绝的候选；简单替代方案为继续使用当前明确反馈规则。
- 正式任务：[AGENT-005](PRODUCT_BACKLOG.md#agent-005)。
- 相关位置：backend/app/tools.py；backend/app/models.py；backend/app/main.py。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-008

**关键词与语义检索对比**

- 记录日期：2026-10-11。
- 来源：迁入旧 ROADMAP v0.2；README 限制；semantic.py。
- 原始想法/迁入内容：通过独立 Embedding 模块比较关键词和语义检索，不预设语义检索更好。
- 当前观察与候选方案：关键词/标签检索已实现；semantic.py 只有 Protocol 接口，尚无 Embedding 实现或比较结果。
- 处置：proposed。
- 评估与决策：先建立真实 ID 与人工标注相关性测试集，再评估最小语义实现；不引入大型向量基础设施。
- 正式任务：[RETR-001](PRODUCT_BACKLOG.md#retr-001)。
- 相关位置：backend/app/retrieval.py；backend/app/semantic.py；evals/。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-009

**档案增长后的数据与前端维护能力**

- 记录日期：2026-10-11。
- 来源：迁入旧 ROADMAP v0.2。
- 原始想法/迁入内容：列表分页、模块化前端路由、数据导出、编辑反馈。
- 当前观察与候选方案：现有 CRUD 和单次最终反馈已实现；尚未分页/导出/反馈编辑，App.tsx 集中页面切换。没有用户规模数据证明当前必须重构路由。
- 处置：proposed。
- 评估与决策：拆四项；先看数据量和真实编辑需求，路由重构暂缓，避免为模块化而打断可用流程。
- 正式任务：[DATA-001](PRODUCT_BACKLOG.md#data-001)、[UI-003](PRODUCT_BACKLOG.md#ui-003)、[DATA-002](PRODUCT_BACKLOG.md#data-002)、[DATA-003](PRODUCT_BACKLOG.md#data-003)。
- 相关位置：backend/app/main.py；frontend/src/App.tsx；README.md。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-010

**恢复能力与数据保留策略**

- 记录日期：2026-10-11。
- 来源：迁入旧 ROADMAP v0.2/v0.3。
- 原始想法/迁入内容：真正的 checkpointer 恢复、运行清理、审计保留策略和幂等请求生命周期。
- 当前观察与候选方案：已持久化节点快照、待审批结果、失败历史，安全重试创建新运行；本轮前的失败幂等重放问题已修复。待评估的是逐步续跑与数据生命周期，不重列既有修复为未完成。
- 处置：proposed。
- 评估与决策：拆三项；清理须保留审批/依据且默认不删除个人数据；checkpointer 暂缓到实际恢复痛点明确。
- 正式任务：[AGENT-006](PRODUCT_BACKLOG.md#agent-006)、[DATA-004](PRODUCT_BACKLOG.md#data-004)、[INFRA-005](PRODUCT_BACKLOG.md#infra-005)。
- 相关位置：backend/app/workflow.py；backend/app/main.py；backend/app/models.py；docs/VERIFICATION.md。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-011

**对外部署前的身份与防护**

- 记录日期：2026-10-11。
- 来源：迁入旧 ROADMAP v0.3 条件项。
- 原始想法/迁入内容：如需对外使用，再增加身份、对象权限、请求限流与部署配置。
- 当前观察与候选方案：当前明确是单用户、本地回环监听；用户尚未要求公网部署。
- 处置：deferred。
- 评估与决策：保留条件项；在对外部署前必须重新评估并提升优先级，当前不构建复杂账号系统。
- 正式任务：[INFRA-006](PRODUCT_BACKLOG.md#infra-006)。
- 相关位置：README.md；docs/ARCHITECTURE.md；docker-compose.yml。
- 决策历史：2026-10-11，建立长期记录；本轮未实现关联业务改进。

### IDEA-012

**长期维护的项目管理记录**

- 记录日期：2026-10-11。
- 来源：用户本轮任务。
- 原始想法/迁入内容：让仓库文档持续管理原始想法、评估、正式待办、里程碑、交付和真实验证。
- 当前观察与候选方案：此前有路线图和一次性实施记录，缺稳定任务 ID、想法决策历史与统一状态。
- 处置：done（仅需求管理文档机制）。
- 评估与决策：本轮只交付文档机制；通过文档一致性和修改范围检查后记 DOC-001 done，体验与工程任务仍待处理。
- 正式任务：[DOC-001](PRODUCT_BACKLOG.md#doc-001)。
- 相关位置：AGENTS.md；ROADMAP.md；docs/IMPLEMENTATION_PLAN.md。
- 决策历史：2026-10-11，纳入本轮文档计划；文档一致性与修改范围检查通过后 DOC-001 完成。该完成状态不影响其他想法及其业务任务。

### IDEA-013

**修正 Git 提交身份并安全保留历史**

- 记录日期：2026-10-17。
- 来源：用户本轮 Git 身份与 CI 修复任务。
- 原始想法/迁入内容：当前仓库未来提交及需要修正的历史提交，使用 YOLIIIIII 与 143058454+YOLIIIIII@users.noreply.github.com；不修改全局配置、不用 mailmap 替代，不经确认覆盖远程 main。
- 当前观察与候选方案：本地 main 与 GitHub main 均是唯一根提交 0fcb300ed9d06d7321b16354cb6f8ab5347bdbb3，Author/Committer 使用 Gitee 邮箱；初始工作区和暂存区干净。选仓库 local 配置、备份旧引用、amend --reset-author，保留文件树；发布时单独确认并核对远程期望 SHA。
- 处置：done（仅本地身份及根提交元数据）。
- 评估与决策：拆为 INFRA-007 本地修复；远程历史改写推送和修复后 CI 的验收交由现有 INFRA-003 跟踪，不自动执行。SHA 会改变，本地成功不等于 GitHub 历史已修正。
- 正式任务：[INFRA-007](PRODUCT_BACKLOG.md#infra-007)、[INFRA-003](PRODUCT_BACKLOG.md#infra-003)。
- 相关位置：仓库 .git/config、备份引用；docs/VERIFICATION.md 的修复证据与发布步骤。
- 决策历史：2026-10-17，按用户授权仅本地修正，备份与 Author/Committer/tree 校验通过；远程保留旧提交，等待用户确认发布。
