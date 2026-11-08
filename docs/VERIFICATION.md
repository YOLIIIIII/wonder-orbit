# 实际验证记录

日期：2026-10-11（Asia/Shanghai）。所有开发和应用数据输出位于 D:\Projects\wonder-orbit。没有 git commit/push，也没有连接 Codex Cloud。未启用真实模型。

## 开发阶段记录

以下保留开发阶段的实际结果；本轮验收重跑结果单独记录在文末，不能将旧记录视为本轮重新执行。

| 检查 | 实际结果 |
| --- | --- |
| Python / 模块导入 | 项目内 Python 3.12.15，FastAPI app 导入成功 |
| uv 依赖锁 | uv lock --check --offline 成功，解析 69 包 |
| Alembic SQLite 初始化 | 在新的 .cache/release-check.db 上 upgrade head 成功 |
| Alembic schema 差异 | alembic check：No new upgrade operations detected |
| 后端 pytest | 42 passed, 1 skipped；最后执行耗时 4.50s，不作为性能基准 |
| Ruff | backend 与 evals 检查通过，代码已格式化 |
| 前端 Vitest | 3 个测试文件、9 项通过 |
| TypeScript | npm run typecheck 通过；最新 npm run build 同时执行 tsc -b |
| ESLint | 通过，包含浏览器 E2E 脚本 |
| Prettier | format:check 通过 |
| Vite 生产构建 | 成功生成 frontend/dist |
| API / 页面服务 | /api/health 返回 ok 和 mock_mode=true；前端首页 HTTP 200 |
| 浏览器闭环 | Chromium 实际通过收集→编辑草稿→批准→搜索→关联→建议接受→修改体验→反馈→候选偏好确认→运行详情 |
| 浏览器尺寸 | 1440px 桌面、390px 移动端；无 pageerror，无移动端横向溢出；截图已检查 |
| 配置文件 | Compose 与 GitHub Actions YAML 可解析；未实际执行远程 CI |

后端测试重点：未知信息留空、拒绝空步骤和无效参数、实际引用/搜索依据、未批准写入被拒、约束和当前偏好二次验证、同一审批不重复创建、请求幂等冲突、超时失败审计与重试、真实反馈持久化、候选不自动进入明确偏好、归档不推荐、UTC 时间戳。

截图位于被忽略的 .cache/e2e/：home-before.png、home-after.png、explore.png、run.png、mobile.png。截图中的兴趣和反馈由浏览器测试实际提交，保存于独立 release-check.db，属于 Mock 测试数据，未放入个人 wonder.db。

## 修复的可复现问题

- 环境 Python 3.10 / Node 16 不满足所选依赖：项目内安装 Python 3.12 / Node 22，并保留锁文件。
- 安装初始失败：沙箱限制及失效代理；经工具批准联网下载到项目缓存。
- pytest 默认临时目录访问失败：使用项目 .cache/pytest，并在所需权限下执行。
- Testing Library 缺少 DOM 同级依赖：显式补充依赖并更新锁文件。
- 搜索结果被刷新覆盖：完整档案与搜索 ID 筛选分开。
- 标签输入时尾随逗号被清除：表单保留原始输入，同时更新结构化数组。
- 编辑正式 Quest 时传入多余数据库字段：编辑器只提交 Proposal 字段。
- 反馈失败审计被 rollback 清掉：回滚后恢复失败事件并保存运行状态。
- SQLite 时区丢失：序列化时统一补 UTC。
- 浏览器测试“喜欢”标签误匹配“不喜欢”：改为 exact 选择器并复验成功。
- E2E 浏览器上下文在 ESLint 中被当作纯 Node：显式声明对应执行环境。

## 未执行与限制

- PostgreSQL 集成测试因未提供 TEST_POSTGRES_URL 跳过。没有本机 Docker / PostgreSQL，未运行完整 Compose 或 PostgreSQL 的迁移/回滚。CI 已配置，未运行远程工作流。
- 未调用真实模型或运行 live eval，不报告模型准确率、效果或真实调用速度。
- 没有多用户并发压力测试；SQLite 的并发审批语义不等于 PostgreSQL 行锁。
- 没有 checkpointer 逐节点续跑；重试是新运行安全重跑生成。
- 本次浏览器测试以开发服务器验证 UI；生产静态资源构建通过，Nginx 容器尚未运行。
- 候选偏好目前支持查看、确认和删除；可在确认后编辑明确类别，尚无候选摘要单独编辑 API。

## MVP 验收复查（2026-10-11）

本轮阅读 README、本文、LEARNING_GUIDE 和 ROADMAP，检查 Git 可提交文件、配置及 Agent 审批/异常路径。只修复可复现问题，没有增加业务功能，没有暂存、提交或推送文件。

| 本轮检查 | 实际结果 |
| --- | --- |
| 后端 pytest | 47 passed, 1 skipped（2.85s，仅记录耗时，不作为性能基准） |
| PostgreSQL 集成测试 | 跳过：未设置 TEST_POSTGRES_URL；不计入通过数 |
| Ruff lint / format | backend、evals 通过；21 个 Python 文件符合格式 |
| uv 锁文件 | uv lock --check --offline 通过，解析 69 包 |
| SQLite 迁移 | 新建独立 .cache/acceptance-<随机 ID>.db，upgrade head / current 成功，版本 0001 (head) |
| SQLite schema 差异 | alembic check：No new upgrade operations detected |
| 前端 ESLint / TypeScript | lint、typecheck 通过；使用项目内 Node 22 |
| 前端 Vitest | 3 个测试文件、9 项通过 |
| 前端构建 / 格式 | build（含 tsc -b 和 Vite）、format:check 通过 |
| PowerShell 实际解析器 | Windows PowerShell 5.1.26100.9444 与 PowerShell 7.6.5 均检查两个启动脚本，语法错误数均为 0 |
| 脚本编码 | web.ps1 为 UTF-8 with BOM；dev.ps1 全 ASCII，可供两个版本读取；本轮未修改脚本 |
| Git 忽略规则 | 用 git check-ignore 逐项验证环境文件变体、SQLite 及附属文件、虚拟环境、缓存、依赖、构建与日志被忽略；.env.example、锁文件和固定评测案例可提交 |
| 配置凭据 | .env.example 的 MODEL_API_KEY 为空；数据库用户名/密码为明确标注的本地 wonder 占位值；当前不存在 .env |
| 可提交文件扫描 | 61 个 UTF-8 文本文件未命中常见 API Key、GitHub Token、AWS Key、私钥及 Bearer Token 格式；这是限定模式扫描，不能保证识别所有可能的秘密 |
| 个人数据库 | 只检查 wonder.db 存在且被 Git 忽略，未读取其内容、迁移或写入；测试和迁移使用独立数据库 |
| Git 状态 | main 尚无提交；git ls-files --stage 为空；61 个项目文件未跟踪，无运行数据库、缓存、日志或 node_modules 出现在可提交清单 |

初次 pytest 因沙箱无法访问既有项目内 pytest 临时目录而报错，Vitest 首次启动因子进程 spawn EPERM 失败；随后在工具获准的权限下实际重跑成功。初次失败没有计入通过，也没有用修改业务代码绕过环境限制。

### 发现并修复的问题

- 原 .gitignore 未排除 .env.local 等环境变体、SQLite 的 .sqlite/.sqlite3 扩展及 journal 附属文件。补齐这些规则和轮转日志规则，显式保留 .env.example；实际个人 wonder.db 原本已经被忽略。
- 同一失败请求的幂等键重放错误返回 201，可能让前端误以为生成或反馈保存成功。新增回归测试先复现两项失败，再在 begin_run 中将失败重放改为 409，附原运行 ID 和错误类型；不重复执行模型、不增加正式记录、不覆盖失败审计。
- 新增三项模拟服务异常测试，分别验证超时、限流、不可用分类，且不将原异常详情返回给用户；没有调用真实服务。
- ROADMAP、学习指南修正候选偏好可编辑的表述；README 明确 E2E_ALLOW_WRITE 不能自动证明数据库隔离，浏览器测试前仍须核对目标服务的 DATABASE_URL。

### 审批与运行记录核对

- 草稿和候选生成只持久化 AgentRun，不创建正式 Star/Quest；批准由用户决定 API 提供，模型不能设置后端的 approved 上下文。
- 工具允许列表及 Pydantic 校验拒绝未知工具、额外参数、未经审批的正式写入。批准时重新校验引用 ID、当前偏好、时间、预算和精力；相关拒绝路径已在 pytest 中执行。
- 请求键与摘要、审批指纹、Quest 候选唯一键及 Reflection 唯一约束共同防止重复写入；已测试顺序重复提交和冲突，未证明并发压力场景。
- 节点/工具状态与耗时、运行模式/模型、公开状态快照、错误类型和结果摘要保存于 AgentRun；模型异常保存失败记录，生成重试创建新运行。未保存隐藏推理或原始服务异常消息。

### 本轮未执行

- Docker 命令不可用，未运行 Compose、Nginx 容器和 PostgreSQL 迁移/回滚；PostgreSQL 行锁及并发提交仍未验收。
- 未调用真实模型或运行 live eval，模拟服务异常通过不代表真实服务兼容性通过。
- 未运行远程 GitHub Actions；本轮未重跑浏览器 E2E 或重新启动 Web 服务，开发阶段浏览器记录保留在上文。

可创建第一个本地 MVP 提交：当前 Mock + SQLite 的规则/API 与前端检查通过，已知验收问题已修复，运行数据被忽略。此结论不代表 PostgreSQL、容器部署、真实模型或生产并发已通过验收。不要使用 git add -f 加入运行数据；未来新增测试产物也应放入被忽略的目录。

## 需求管理文档建立（DOC-001）

日期：2026-10-11（Asia/Shanghai）。本轮仅整理管理文档，没有前后端业务、脚本、依赖、数据库变更，没有执行 git commit/push 或云连接。此节与上轮应用验收分开记录。

### 范围与证据来源

- 实际阅读 README、AGENTS、ROADMAP、本文、LEARNING_GUIDE 和历史 IMPLEMENTATION_PLAN，核对 evals/README 及项目目录。
- 检查 frontend/src/App.tsx、components.tsx、styles.css，核对 backend/app/schemas.py、tools.py 的输入/验证规则与 semantic.py 预留接口。确认已有步骤提示、单草稿、空预算仍受偏好上限约束等真实行为；没有修改这些实现。
- 实际查看既有 .cache/e2e/home-after.png 与 mobile.png（2026-10-11 16:43 的历史截图），作为视觉候选方案依据；没有重新启动浏览器，也没有据此声称新设计通过验收。
- 新建 [IDEA_LOG](IDEA_LOG.md)、[PRODUCT_BACKLOG](PRODUCT_BACKLOG.md)、[CHANGELOG](../CHANGELOG.md)；更新 AGENTS、README、ROADMAP、LEARNING_GUIDE、IMPLEMENTATION_PLAN 的相关规则/导航，以及本节。历史 MVP 与验收记录继续保留。

### 实际执行的文档检查

使用项目内 Python 3.12 执行内联检查（.venv/Scripts/python.exe -c），结合 git ls-files --others --exclude-standard 和变更前 SHA-256 快照；未新增检查脚本或依赖。

| 检查 | 实际结果 |
| --- | --- |
| 唯一记录 | 12 个 IDEA ID、25 个正式任务 ID，定义不重复 |
| 任务字段和索引 | 所有任务具备统一字段，索引与详情的优先级/状态一致，值属于定义集合 |
| 双向关联 | 每条想法引用的任务存在，每个任务能回指原想法 |
| 前置依赖 | 引用的任务全部存在，依赖图无循环 |
| 文档导航 | 本轮管理文档的本地 Markdown 文件链接及稳定 ID 锚点检查通过 |
| 基本格式 | 文档可按 UTF-8 读取、标题存在，无尾随空白 |
| 修改范围 | 仅 9 个管理文档新增/修改；55 个其他原文件 SHA-256 与本轮起始快照一致，包含业务代码、脚本、锁文件和配置；未删除原文件 |
| 状态 | 仅 DOC-001 done；10 planned、10 proposed、4 deferred，无业务任务 in_progress/done，未完成 P0 为 0、P1 为 8 |
| Git | 暂存区为空、未创建提交；64 个可提交项目文件未跟踪，新增 3 个管理文档；个人 wonder.db 仍被忽略 |

检查过程中补齐 RETR 检索任务前缀的校验与 AGENTS ID 约定，复检通过；没有将第一次检查失败当作通过。DOC-001 仅在文档及修改范围检查通过后标记 done，交付记录见 CHANGELOG。

### 本轮没有执行

- 没有重跑 pytest、前端 lint/typecheck/Vitest/build 或浏览器 E2E：本轮纯文档且代码/依赖哈希未变；旧 47 passed / 1 skipped 与前端 9 passed 是历史应用验收结果。
- 没有执行 PostgreSQL、Docker、真实模型/live eval、远程 CI 或并发验证，仍由相应 P1/P2 待办跟踪。
- 没有实现流程引导、输入文案或视觉优化，也没有新的可用性/对比度测量结果；其验收条件是后续目标，不是本轮结果。

当前状态：M1 本地 MVP 基线已交付；M2 体验修整准备阶段，推荐 UX-003 → UX-001 → UX-002；工程路径保留 INFRA-001/002/003、AGENT-001、EVAL-001。正式状态/优先级以 PRODUCT_BACKLOG 为准，本节为本轮历史快照。

## 2026-10-17：Git 身份与首次 CI 故障修复（INFRA-007 / INFRA-003）

本节是本轮实际执行记录；上文 2026-10-11 的“无提交/未运行远程”等说法是历史快照，不代表当前状态。范围仅 Git 元数据、CI 父目录准备与相关文档；未改业务、数据模型、测试、依赖或 UI，未直接查看个人数据/私有配置内容，未修改个人 wonder.db 或真实 .env。测试显式使用隔离数据库、Mock 和空模型 Key，未启用真实模型。

### Git 身份与历史修正证据

- 初始为实际 main，工作区/暂存区干净，origin 为 https://github.com/YOLIIIIII/wonder-orbit.git；HEAD 与 origin/main 均为唯一根提交 0fcb300ed9d06d7321b16354cb6f8ab5347bdbb3，无父提交。
- git config --local 没有 user.name/user.email；git var 和根提交实际 Author/Committer 为 YOLIII <12766407+yoliii@user.noreply.gitee.com>。仅在 local 设置 user.name=YOLIIIIII、user.email=143058454+YOLIIIIII@users.noreply.github.com；没有更改全局 Git 或换行配置。
- git ls-remote 在沙箱及获准权限下均失败：既有代理 127.0.0.1:7897 无法连接。未修改代理；改用 GitHub 连接器读取 main 提交，实际 SHA 与上述本地根提交相同，因此确认远程 main 当时也没有其他新增提交。
- 写 .git/config 首次因沙箱拒绝失败，获准权限下重试成功；确认实际身份后才继续。创建 backup/main-before-author-fix-20261017，指向旧根提交，然后在再次检查工作区/暂存区干净后执行 git commit --amend --no-edit --reset-author。
- 本地新根提交为 **5583c8bd2de9718b035ad16f5c5eeeadeb74599f**。git show -s --format=fuller HEAD 显示 Author 与 Committer 均为 YOLIIIIII <143058454+YOLIIIIII@users.noreply.github.com>；比较新旧 HEAD^{tree} 相同，文件内容没有因 amend 改动。
- 仅本地 main 历史已修正。origin/main 和 GitHub main 仍为旧 SHA；备份分支故意保留原始元数据。main 相对 origin/main ahead 1 / behind 1 是根提交 SHA 改写所致，不是完成了远程同步。
- 本轮没有创建 CI 修复提交，没有暂存、push、force push、合并或发布；后续提交使用已确认的 local GitHub 身份。INFRA-007 只验收本地范围；远程发布和 CI 仍由 INFRA-003 跟踪。

### 已读取的远程失败证据

原始运行：[GitHub Actions 38140512844](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/38140512844)，commit 为 0fcb300ed9d06d7321b16354cb6f8ab5347bdbb3；运行发生于 2026-10-11，本轮于 2026-10-17 通过 GitHub 连接器读取 jobs/steps 及 backend 完整日志。普通网页抓取失败，没有将失败抓取当作日志证据。

| 原始远程检查 | 实际结果 |
| --- | --- |
| frontend job | passed：npm ci、format:check、lint、typecheck、Vitest、build 步骤 success |
| backend 安装/迁移/schema/Ruff | passed：uv sync --frozen、alembic upgrade head/check、Ruff lint/format 步骤 success |
| backend 普通 pytest | failed：12 passed、1 skipped、35 errors，进程退出 1 |
| 独立 PostgreSQL 测试步骤 | skipped：前一个 pytest 失败，默认成功条件阻止后续步骤执行，不能计为集成通过 |
| 修复后的远程 run | not run：本轮未推送修复，也没有以重跑旧 SHA 冒充新配置验证 |

根因链：pyproject.toml 固定 addopts="--basetemp=.cache/pytest"；conftest.db 依赖 tmp_path，进而触发 pytest 临时目录创建。实际日志中 pathlib.mkdir 的 parents=False，尝试创建 /home/runner/work/wonder-orbit/wonder-orbit/.cache/pytest 时抛 FileNotFoundError。全新 checkout 不含被 .gitignore 排除的 .cache；setup-uv 的 UV_CACHE_DIR 是 runner 的外部路径，不会自动创建仓库内的 .cache。35 项依赖数据库 fixture 的测试因此在 setup 报错，未到业务断言；不依赖它的测试仍可通过。

唯一 CI 改动为在 Ruff 之后、普通 pytest 之前增加：

```yaml
- name: Prepare pytest cache parent
  run: mkdir -p .cache
```

保留 Python 3.12、Node 22、uv 0.13.0、PostgreSQL 16、锁文件、测试/断言及现有两个 pytest 命令。顺序仍为 PG 迁移/schema → Ruff → 创建测试父目录 → 普通 Mock/SQLite 测试 → 独立 PG 集成。TEST_POSTGRES_URL 仅在最后一步明确注入，conftest 不会覆盖它；普通测试跳过 PG 用例是有意分组，最后一步必须真正执行且 1 passed 才算集成验证。未用 continue-on-error、忽略异常或删除测试绕过失败。

### 本轮本地执行与结果

项目内 Python 3.12.15、uv 0.13.0、Node 22.23.3；npm CLI 通过该 Node 显式启动 D:/Soft/Node/node_modules/npm/bin/npm-cli.js，避免全局旧 Node/npm.cmd。缓存/日志/临时检出均放被忽略的 .cache。使用现有安装依赖与锁文件，未添加依赖。

| 本轮检查 | 状态 | 命令/实际证据 |
| --- | --- | --- |
| 冻结 Python 安装 | passed | 项目内 uv sync --frozen：Checked 66 packages；首次沙箱解释器查询拒绝访问，获准权限重试成功 |
| 干净源码检出复现 | failed（预期复现） | git archive HEAD 解压到 .cache/ci-clean-ead12d642f07，确认其中无 .cache；用共享已安装 .venv 和绝对 UV_CACHE_DIR 执行 uv run --offline pytest：12 passed / 1 skipped / 35 errors，退出 1，与远程一致 |
| 同一检出只补父目录 | passed / skipped | 在该检出创建 .cache，再执行相同 uv run --offline pytest：47 passed / 1 skipped，退出 0；没有修改任何测试或测试配置 |
| 根目录回归 | passed / skipped | uv run pytest：47 passed / 1 skipped；日志 .cache/ci-root-tests.log；PG 跳过不是通过 |
| 后端 lint | passed | uv run ruff check backend evals：All checks passed! |
| 后端格式 | passed | uv run ruff format --check backend evals：21 files already formatted |
| SQLite 迁移 | passed | DATABASE_URL 指向新 .cache/ci-fix-c28d8b40d49a42a685b39322464ce897.db，uv run alembic upgrade head / check / current：No new upgrade operations detected、0001 (head) |
| 本机 PostgreSQL 迁移/集成 | not run | 未发现可用 Docker/psql/postgres 或 PostgreSQL 安装；WSL 也不可用。未提供 TEST_POSTGRES_URL，普通 pytest 的该用例为 skipped |
| 前端锁安装 | passed | Node 22 启动 npm ci：added 267 packages；首次沙箱 mkdir EPERM 失败，获准权限重试成功，保留锁文件 |
| 前端格式 | passed | npm run format:check：All matched files use Prettier code style! |
| 前端 lint | passed | npm run lint：退出 0 |
| 前端类型 | passed | npm run typecheck：退出 0 |
| 前端测试 | passed | npm run test（脚本等同 npm test）：3 files、9 tests passed |
| 前端构建 | passed | npm run build：tsc -b 与 Vite 成功；1581 modules transformed |
| 浏览器闭环/容器/真实模型 | not run | 本轮未更改这些实现，不用历史结果冒充本轮执行 |

干净检出验证的是“源码没有预置 .cache”的场景，复用已安装 Python 环境及依赖缓存，**不等于**新 Linux runner 的完整安装/PG/CI 已验收。原失败/修复后日志分别保存在 .cache/ci-clean-before.log、ci-clean-after.log；这些运行产物不提交。npm 报了既有依赖 deprecated 提示，本轮不借机更新依赖。

交付前静态核对：工作流 YAML 可解析，创建父目录/两次 pytest 的顺序和独立 PG 环境变量符合预期；CI diff 仅新增上述两行，frontend、backend/app、测试、迁移、脚本、pyproject 和两个锁文件内容保持不变。8 个预期文件变更，暂存区为空；本地文档文件链接/任务锚点、26 个唯一任务与 13 个唯一想法、任务索引/状态一致，未完成 P1 为 8。README/PROJECT_GUIDE/本记录中共 22 段 PowerShell 示例经实际 5.1 与 7 解析器检查，均无语法错误，仅解析未执行发布命令。修正新增记录的一处末尾多余空行后重新检查通过，git diff --check 通过，没有以初次格式失败当作通过。

### 待用户确认的发布步骤（本轮未执行）

改写 Author/Committer 会改变根提交 SHA；普通 fast-forward push 无法将远程旧根提交替换为新根提交。备份引用保留在本地，不能自动一并推送。先审阅本轮八个文件，确认后可创建本地修复提交：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
git add -- .github/workflows/ci.yml README.md ROADMAP.md CHANGELOG.md docs/IDEA_LOG.md docs/PRODUCT_BACKLOG.md docs/PROJECT_GUIDE.md docs/VERIFICATION.md
git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Fix staged whitespace before committing' }
git diff --cached --stat
git commit -m "fix: prepare pytest cache for clean CI checkouts"
if ($LASTEXITCODE -ne 0) { throw 'Local fix commit failed' }
git show -s --format=fuller HEAD
```

**仅在用户明确批准覆盖远程 main 后**，在 Git 网络/认证正常的环境执行以下命令。若网络查询失败或远程 SHA 已变化则停止，不能把 fetch 的新值直接当作允许覆盖的值；不要用无条件 --force：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
$expectedRemote = '0fcb300ed9d06d7321b16354cb6f8ab5347bdbb3'
if ((git branch --show-current) -ne 'main') { throw 'Expected local main' }
if (git status --porcelain) { throw 'Review and commit local fixes first' }
if ((git config --local user.name) -ne 'YOLIIIIII') { throw 'Unexpected Git name' }
if ((git config --local user.email) -ne '143058454+YOLIIIIII@users.noreply.github.com') { throw 'Unexpected Git email' }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed; do not push' }
if ((git rev-parse origin/main) -ne $expectedRemote) { throw 'Remote main changed; stop and reassess history' }
git merge-base --is-ancestor 5583c8bd2de9718b035ad16f5c5eeeadeb74599f HEAD
if ($LASTEXITCODE -ne 0) { throw 'Corrected root not in current history' }
git push --force-with-lease="refs/heads/main:$expectedRemote" origin HEAD:refs/heads/main
if ($LASTEXITCODE -ne 0) { throw 'Lease push rejected; do not use force' }
```

这个 lease 同时防止核对后出现的远程竞态。若服务器保护规则拒绝，不绕过保护；保留备份并重新讨论发布方案。不要把旧备份分支 merge 回 main，否则错误邮箱根提交会重新进入主线历史。

发布后记录新的 run URL/commit SHA，确认 backend/frontend 均 success，且独立 PostgreSQL step 实际运行、输出 1 passed 而非 skipped，再更新 INFRA-003；PG 回滚/并发和完整容器仍按 INFRA-001/002/004 各自验收。当前 M1 基线保持，M2 未实施；未完成 P0 为 0、P1 为 8，本次只先收尾已确认的 CI 故障。


## 2026-10-17：M2 首轮输入文案校准（UX-003）

开发前核对：main / HEAD 与远程 main 均为 172103d3bc03c28c093db3cbe6ef863c936a887b；工作区干净；Author/Committer 配置为 YOLIIIIII <143058454+YOLIIIIII@users.noreply.github.com>。普通远程查询因本机 127.0.0.1:7897 代理不可用失败，获准联网重试后，命令级禁用代理成功核对，未更改全局配置。本轮只实施 UX-003，附带已授权的 INFRA-003 文档收尾。

<a id="ux-003-fields"></a>
### 开发前字段对照与验收映射

| 原有文案/问题 | 实际规则（源码） | 本轮新文案方案 | 对应验证 |
| --- | --- | --- | --- |
| 探索预算“元，留空不限” | tools.validate_quest_proposal / ModelAdapter.proposals 取非空预算最小值；0 有效 | 本次预算（元，可选）；0 为零预算；空值仍受偏好上限、都空不额外限制、同时设置取更低值 | App 预算提示及 null/0 请求；后端 5 元偏好回归 |
| 海洋、星空、深海生物多主题示例 | DraftResult 仅一份 StarInput，批准前不创建 Star | 单主题“深海生物为什么会发光”；一次一张可编辑草稿，确认后才入档 | App 收集可见提示、草稿审批边界；隔离示例流程 |
| 参考链接 https://… | valid_url 只接受带主机的 http/https；不抓取网页，text 必填 | 完整 https://example.com/notes；链接仅保存来源，仍需原始文字 | App/StarEditor 链接说明、格式及 required；后端 URL 校验 |
| 标签/类别/约束/反馈“逗号分隔” | split 支持英文逗号、中文逗号及换行；ListInput 为单行 input | 可选；支持中英文逗号或换行分隔（单行框建议逗号） | 组件 split、连续输入、中英文逗号；App 偏好/反馈说明 |
| 步骤/不确定性“每行一项” | 按换行切分；步骤 1–10 项且每项 1–1000 字；不确定性至多 20 项 | 一行一项；步骤必填并给范围，不确定性可选 | ProposalEditor 可见提示与换行 payload |
| 原因仅 placeholder 提示可空 | 原因、Star 时间/预算/精力允许 null，不能把未知预算变 0 | 明确选填和未知留空，不猜原因；0 表示无需花费 | StarEditor 清空/提交 null；ProposalEditor null 与 0 |
| 分钟/可用时间/偏好最短最长含义不清 | 预计分钟 1–1440；本次/偏好时间上限取较低值，仍需达到偏好下限 | 预计所需时长；本次可用上限；偏好每次体验范围，冲突会澄清 | 表单 required/min/max、App 辅助说明；后端已有约束测试 |
| 精力“轻轻一点/刚刚好/充满能量” | low/medium/high 有序上限；Star 未知、偏好未设置是 null | 低/中/高＋原温柔称呼；说明所需/可用/上限及未设置含义 | 编辑器/偏好/探索选项及 null 断言 |
| 偏好有限约束说明独立于字段 | SUPPORTED_CONSTRAINTS 精确三项；其他要求澄清，支持项限定免费室内文字步骤 | 字段附近说明仅室内、不购买、不外出；其他约束需澄清 | App 偏好可见说明；后端已有支持/不支持约束测试 |

### 上一轮 INFRA-003 远程成功证据补记

通过 GitHub 连接器核对 [运行 39030090153](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39030090153)：frontend job 117388639008 与 backend job 117388639211 均 completed / success。backend checkout 日志 SHA 为 172103d3bc03c28c093db3cbe6ef863c936a887b；Ubuntu 24.04 / Python 3.12 / PostgreSQL 16，锁安装、upgrade head、alembic check、Ruff 均成功。普通 pytest 为 47 passed / 1 skipped；独立 `uv run pytest backend/tests/test_postgres.py --override-ini addopts=` 实际为 **1 passed in 0.20s**。这是上一轮远程结果的补记，不是本轮测试重跑。保留前述首次失败与 skipped 记录；此证据不涵盖完整 Compose/Nginx、PG downgrade/upgrade 回滚或并发验证。

### 本轮修改与逐项验收证据

修改文件：frontend/src/App.tsx、components.tsx、styles.css、App.test.tsx、components.test.tsx；frontend/e2e/smoke.mjs；backend/tests/test_mvp.py；README.md、ROADMAP.md、CHANGELOG.md、docs/IDEA_LOG.md、PRODUCT_BACKLOG.md、PROJECT_GUIDE.md、VERIFICATION.md。未修改 backend/app、Schema、预算计算、依赖/锁文件、迁移或 CI 配置。

- 预算：App 参数化用例验证偏好上限 5 元、本次空/0/8 元分别提交 null/0/8，界面明确仍受偏好上限。后端新增四组 API 回归验证空/0/3/8 元请求实际限额为 5/0/3/5；未知成本或超额在确认 API 被拒，边界值可以确认。另验证都无预算上限时未知成本保持 null。
- 单草稿/链接：App 可见说明与 accessible description 断言，原始文字 required、maxlength=12000；只有链接不能发起整理。http/https（含大写 scheme）可用，ftp 被拒；示例为完整地址，编辑器说明来源用途。已有草稿不自动写正式 API 的测试继续通过。
- 分隔/未知字段：StarEditor 提交中英文逗号标签；原 split 的换行解析单独断言，明确 HTML 单行输入会移除换行，未声称新增多行控件。清空已知原因/分钟/预算/精力提交 null，0 元提交 0；偏好未设置保留 null。步骤/不确定性按换行提交，步骤中的逗号保持同项；required/min/max/maxlength 与 Schema 对照。
- 时间/精力/有限约束：组件检查各处关联说明，偏好低/中/高和空值含义清楚；探索可用时间从前端错误必填改为可选，与 AgentRequest 的可空语义一致，空值沿用偏好最长时间。只补既有边界，不新增解析或改变后端规则。

### 实际环境、命令和自动化结果

Windows / PowerShell，项目内 Python 3.12.15、Node 22.23.3，复用现有已安装依赖。下表以最终实际完成结果为准，失败/中止记录另列，不用旧测试冒充本轮。

| 检查 | 实际命令与环境 | 结果 |
| --- | --- | --- |
| 后端 pytest | `.venv/Scripts/python.exe -m pytest -q -rs --basetemp=.cache/ux003-pytest`；conftest 强制 Mock/空 Key，每例独立 SQLite | passed：52 passed；skipped：1 项 PG，未设置 TEST_POSTGRES_URL |
| Ruff lint | `.venv/Scripts/ruff.exe check backend evals` | passed：All checks passed |
| Ruff format | `.venv/Scripts/ruff.exe format --check backend evals` | passed：21 files already formatted |
| 前端格式 | `npm run format:check` | passed |
| 前端 lint | `npm run lint` | passed |
| 前端类型 | `npm run typecheck` | passed |
| 前端 Vitest | `npm run test` | passed：3 files / 17 tests（App 8、components 7、api 2） |
| 前端构建 | `npm run build` | passed：tsc -b 与 Vite 6.4.4，1581 modules |
| 隔离浏览器 | Node 22 执行 `e2e/smoke.mjs`；E2E_ALLOW_WRITE=true，E2E_BASE_URL=http://127.0.0.1:5178，PLAYWRIGHT_BROWSERS_PATH=项目/.cache/browsers，E2E_ARTIFACT_DIR=项目/.cache/ux003-e2e-final | passed：完整收集→审批→搜索/关联→探索→接受/修改→反馈→偏好确认→足迹；无 pageerror，三个表单页 1440/390px 无横向溢出 |
| 本轮本机 PostgreSQL / Docker / 真实模型 | 未配置本机 PG/Docker，未授权真实模型调用额度；代码没有改变相关能力 | not run；不以本地 PG skipped 或上一轮 CI 冒充本轮执行 |
| 用户人工体验验收 | 需要用户本人按下述步骤体验 | not run；UX-003 保留 in_progress |

前端命令实际由项目 `.tools/node/node_modules/node/bin/node.exe` 启动 `D:/Soft/Node/node_modules/npm/bin/npm-cli.js run <script>`，PATH 优先项目 Node 22、npm 缓存限定 .cache/npm。最后完整顺序 format:check → lint → typecheck → test → build 退出 0，无依赖变更。

失败与重试：首次 pytest 在沙箱内长时间无输出，主动中止（未计通过），改用获准权限与新的 basetemp 后完整通过。首次 Vitest 因 realpath EPERM 没有运行测试；获准权限后通过。首次 typecheck 发现新增测试误用了 Playwright 的 exact 参数，修正后完整前端检查通过。首次 build realpath EPERM，获准权限重跑通过。E2E 首次访问本机被 ERR_NETWORK_ACCESS_DENIED 拒绝，单独提升浏览器后因沙箱服务不可达超时；前后端均在获准权限下监听专用端口后业务闭环完成，但新增截图循环中“收集星星”精确名称与原导航可访问名称不一致而超时，修正定位并换另一份新库完整重跑通过。原失败产物 .cache/ux003-e2e 保留，不以其部分截图当成功结果。一次匿名 GitHub REST 查询遭 IP rate limit，改由现有 GitHub 连接器核对真实 run，不记录任何认证信息。

### 浏览器隔离与视觉核对

测试启动器（被忽略的 .cache/ux003_server.py）启动前断言新 DB 不存在、绝对路径位于项目 .cache 内，强制 DATABASE_URL、MOCK_MODE=true、空 MODEL_API_KEY，并从应用实际 engine.url.database 再次核对目标路径后才迁移/启动。最终目标为 **D:/Projects/wonder-orbit/.cache/ux003-browser-20261017c.db**；专用后端 127.0.0.1:8018，临时 Vite 127.0.0.1:5178 的 /api 明确转发 8018，不复用日常 8000/5173。早先隔离尝试的无后缀/b 库保留在 .cache，不删除个人数据。

运行前后仅对个人 wonder.db 做文件 SHA-256 对照，均为 FDBE6D81BB9ABF6684E06AD0D0A79F73F6795293748EB264CA0E869E1F243950；未查询其业务内容，也未向其写入测试数据。截图位于 .cache/ux003-e2e-final（忽略、不提交）。已查看“微型探索-390.png”“我的偏好-1440.png”“收集星星-1440.png”：字段附近说明可读，无覆盖/截断，维持原配色与布局。这是开发检查，不是用户本人验收。

### 待用户依次体验

1. 打开“我的偏好”，先记下原设置，将预算上限设为 5 元并保存；查看时间范围、精力未设置、列表格式和三种有限约束说明。
2. 打开“收集星星”，输入“我想了解深海生物为什么会发光，想先记下几个好奇的问题。”，参考链接可填 https://example.com/notes；确认只产生一张可编辑草稿。原因、预计时间/预算、精力未知时保留空值，确认后才加入档案；检查标签“深海，微光,观察”。可先试仅填链接、留空原文，确认不能整理。
3. 打开“微型探索”，输入档案中确有的关键词“深海”，可用时间 10 分钟、本次预算留空：说明应明确仍遵守 5 元上限；再填 0 元生成，说明应明确是零预算。当前 Mock 模板本来就免费，不能仅凭候选免费推断 5 元规则已验证；非零边界由后端 API 回归证明。
4. 点击候选“修改”，检查预计分钟、预算未知/0、精力必选、步骤必填与不确定性可选的“一行一项”说明。可以取消，不必保存测试体验；如接受并记录反馈，检查喜欢/不喜欢的格式说明。
5. 窄屏（约 390px）再次打开收集、探索、偏好，核对阅读和操作；体验后按需恢复原偏好，反馈是否有难懂或过长的说明。

风险/剩余：用户体验尚未执行；Mock 不能证明真实模型质量；PG 回滚/并发、完整容器仍待各自验收。本轮仅 UX-003 与 INFRA-003 文档收尾，下一项建议在用户体验通过后实施 UX-001，不继续开发。当前 M2，未修 P0 无已知实证，未完成 P1 七项见 Backlog。

本轮远程 CI 结果在提交推送后核对，并在最终交付中提供链接、SHA、两个 Job 与独立 PG 实际输出；按用户要求留待下轮补记，不为写入本次 CI 结果额外触发一次构建。

提交前静态复核：运行被忽略的 .cache/ux003_doccheck.py，265 个本地 Markdown 文件链接/锚点存在，26 个任务 ID 与索引/详情状态一致，13 个 IDEA ID 未重复，UX-001/002/UI-001 保持 planned，未完成 P1 七项；变更限定上述 14 个文件，backend/app、依赖锁文件与个人 DB 未纳入。已审阅 git diff、git diff --check 通过；重新 fetch origin main 后确认远程与本地基线仍为 172103d，无未知远程变更。测试临时前后端已停止，隔离库/截图保留在忽略目录供复核。


<a id="ux-003-feedback-20261018"></a>

## 2026-10-18：UX-003 人工反馈修正

### 来源、基线与范围

用户于 2026-10-18 实际使用后反馈五项问题，并描述截图中的 snake_case 字段名；本轮未收到可读取图片文件，来源按用户文字描述记录，未冒称查看原截图。已读 AGENTS/ROADMAP/IDEA_LOG/Backlog/VERIFICATION/CHANGELOG/导航，核对本地 main 为 a04b35efaebe9c90474a2f8af96b4455515d0838、工作区干净、仓库本地身份正确。GitHub 连接器读取 branches/main 确认远程同 SHA；Git 命令沙箱 DNS 失败，获准权限后直连仍超时，现有本机 7897 代理未运行；已请用户恢复现有代理，用户回复“我会启动现有代理”，继续推进本地工作，不改全局网络配置。

只实施 UX-003 默认短提示/完整规则按需展开、草稿未知字段中文展示。未改后端计算、Schema、原始/结构化数据、API、依赖、迁移、审批/提交调用链；未增加自动滚动/焦点定位、新手引导、统计面板、足迹重设计或真实模型接入。ROADMAP 核对后不变：仍为 M2，开发顺序未调整。

### 五项反馈归档与范围边界

| 用户真实反馈（2026-10-18） | 想法 / 任务 | 本轮处置 |
| --- | --- | --- |
| 1. 草稿生成后要下滑找结果，希望自动定位 | IDEA-001 / UX-002 | 记录后续候选定位验收，本轮未实现自动滚动 |
| 2. 探索/偏好说明长且重复，希望短提示、按需帮助并与引导分工 | IDEA-002 / UX-003；IDEA-001 / UX-001 | 本轮精简与折叠；后续引导未开发 |
| 3. 担心记录增多难找，希望概览、状态与关键词 | IDEA-009 / DATA-001、UX-004 | 首页统计/档案搜索筛选已有；分页仍待评估，体验记录查找新列 P2 候选，未实施 |
| 4. 整体闭环不流畅、不清楚，感受不到真正 AI 的作用 | IDEA-001 / UX-001/002；IDEA-005 / AGENT-001、EVAL-001 | 保留真实体验感受，不当作模型评测结论；本轮不接入模型或宣称增强 |
| 5. 不理解足迹价值，希望通俗解释并保留技术详情 | 新 IDEA-014 / UX-005 | 与已实现事件审计和 IDEA-010 保留策略区分，P2 候选，未重设计 |

草稿未知字段的附加反馈合并 IDEA-002 / UX-003。新增任务为 UX-004/005，新增想法仅 IDEA-014；旧 ID/依赖保留，全部未完成项含 deferred 已复评，优先级和当前顺序未变，无新 P0 证据，未完成 P1 仍为 7 项。

### 前后文案与验收映射

| 原表现 | 本轮表现 | 自动化证据 |
| --- | --- | --- |
| 探索字段下多行完整规则 | 时间/预算/精力各一句短提示；预算关键语义始终可见，范围与冲突规则在默认收起的帮助中 | App 参数化空/0/8 元请求不变，说明关联输入；帮助默认关闭、可展开/收起 |
| 偏好通用规则重复展开、类别标签较长 | 简短常用提示与类别标签；完整范围/严格上限/约束/列表数量在“查看偏好填写规则”中 | 偏好 null、列表和 required/min/max 原提交断言继续通过 |
| 未知字段直接 join 内部 key | 中文显示并说明不是整理出错、可选项可补充或留空；未知 key 通用中文，重复兜底合并 | App 草稿模拟含四个真实 key、未来 key、constructor，中文可见且无原始 key；未自动审批的断言保留 |
| 详情无按需访问层次 | 原生 details/summary，键盘/点击可访问，无浮层；14px 帮助文字和草稿字段说明 | 浏览器 Enter 展开、Space 收起、点击切换；1440/390px 收起/展开均无横向溢出 |

### 本轮实际执行

Windows / PowerShell，复用项目 Python 3.12.15、Node 22.23.3 和已安装锁定依赖。下表是本轮实际检查；2026-10-17 结果仅在独立补记中引用。

| 检查 | 实际命令 / 环境 | 结果 |
| --- | --- | --- |
| 后端 pytest | `.venv/Scripts/python.exe -m pytest -q -rs --basetemp=.cache/ux003-feedback-pytest-final`；conftest 强制 Mock/空 Key/每例独立 SQLite | passed：52 passed；skipped：本机无 TEST_POSTGRES_URL，PG 1 项跳过 |
| Ruff lint | `.venv/Scripts/ruff.exe check backend evals` | passed |
| Ruff format | `.venv/Scripts/ruff.exe format --check backend evals` | passed：21 files already formatted |
| 前端格式 | `npm run format:check` | passed |
| 前端 lint | `npm run lint` | passed |
| 前端类型 | `npm run typecheck` | passed |
| 前端 Vitest | `npm run test` | passed：3 files / 19 tests（App 10、components 7、api 2） |
| 前端构建 | `npm run build` | passed：tsc -b / Vite，1581 modules |
| 独立库浏览器 | `node e2e/smoke.mjs`，E2E_ALLOW_WRITE=true、E2E_BASE_URL=http://127.0.0.1:5178、PLAYWRIGHT_BROWSERS_PATH=项目/.cache/browsers、E2E_ARTIFACT_DIR=项目/.cache/ux003-feedback-e2e | passed：原闭环与空预算/0 元、草稿中文、帮助键盘/点击，三页 1440/390px；无 pageerror，展开后也无横向溢出 |
| 本机 PG / Docker / 真实模型 | 环境/服务与调用额度未具备，本轮范围不包含 | not run；本机 PG skipped 不计通过 |
| 本轮修正后用户人工体验 | 必须由用户实际使用确认 | not run；UX-003 保持 in_progress |

前端 npm 命令实际由项目 `.tools/node/node_modules/node/bin/node.exe` 执行 `D:/Soft/Node/node_modules/npm/bin/npm-cli.js run <script>`，PATH 优先项目 Node 22、npm 缓存位于 .cache/npm。初次 pytest 沙箱无输出被主动中止，首次 Vitest 无测试执行（realpath EPERM），首次 build 因 realpath EPERM 失败；按权限流程重跑完整前端检查与独立 basetemp 后通过。失败/中止不计通过；未删除测试或降低要求。没有安装或更改依赖。

### 隔离与视觉检查

被忽略的 .cache/ux003_server.py 启动前断言 DB 文件为新文件、解析路径位于项目 .cache，强制 DATABASE_URL / MOCK_MODE=true / 空 Key，从应用实际 engine.url.database 再核对目标。使用 **D:/Projects/wonder-orbit/.cache/ux003-feedback-browser-20261018.db**，专用后端 8018，临时 Vite 5178 明确代理至 8018，不复用个人应用服务。个人 wonder.db 仅做运行前后 SHA-256 对照，均为 DB295A97ED21302CDA24B9C8809BCEFC8A8B56A4935ADA294C4221AC13A27A20；未查询业务内容或写入测试数据。

截图保留在忽略目录 .cache/ux003-feedback-e2e。已查看微型探索-390.png、我的偏好-help-390.png、draft-fields.png：短提示与完整帮助分层、原有焦点样式可见、中文字段可读，无浮层覆盖。浏览器脚本还保存 1440px 与 390px 的收起/展开截图并检查页面宽度；开发截图复核不替代用户人工验收。

### 上一轮成功 CI 独立补记

本轮通过 GitHub 连接器重新核对 [运行 39033400335](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39033400335)：提交 a04b35efaebe9c90474a2f8af96b4455515d0838，backend（117398324488）/frontend（117398324780）均 completed / success。backend 日志确认普通 pytest 52 passed / 1 skipped；单独 `uv run pytest backend/tests/test_postgres.py --override-ini addopts=` 为 **1 passed in 0.18s**。这是上一轮远程证据，不是本轮重跑，不代表完整 Docker、PG 回滚或并发验收。

### 新一轮待用户体验

1. “微型探索”：常态下查看三项短提示，尤其预算空值仍受偏好上限、0 元明确零预算、同时设置取更低上限；键盘 Tab 到“查看时间、预算和精力规则”，Enter 展开、Space 收起。
2. “我的偏好”：检查时间、预算、精力、约束说明是否够短；打开完整规则确认范围/有限约束可查。保留原偏好，必要时用 5 元上限试空预算和 0 元，体验后恢复。
3. “收集星星”：输入单兴趣示例并整理，手动下滑到结果，检查“兴趣原因、预计时间、预计预算、所需精力”中文及可补充/留空说明；确认原审批/保存行为。此轮没有自动定位。
4. 约 390px 窄屏复核上述页面的收起和展开状态，反馈是否仍过长、重复或难懂；无须测试新手引导/统计/足迹重设计/真实模型，这些尚未实施。

本轮 CI 在普通推送后核对并于最终汇报给出链接与真实 Job/PG 结果，后续反馈轮再补记，避免为写入同一次 CI 结果额外触发构建。当前 M2；剩余 P1 为 UX-001/002/003、INFRA-001/002、AGENT-001、EVAL-001，待本轮用户体验后按原顺序推进，修正后人工验收不能先记完成。

提交前复核：.cache/ux003_feedback_doccheck.py 通过 283 个本地 Markdown 链接/锚点、28 个任务索引/详情状态及 14 个 IDEA ID 检查；变更限定 10 个预期文件，后端/Schema/依赖/迁移/ROADMAP 未修改。已审阅代码 diff，git diff --check 通过；最后浏览器截图补充后重跑 format:check/lint 均通过。临时测试前后端已停止，个人数据库哈希保持不变。GitHub 连接器再次确认远程 main 仍为 a04b35e；普通 Git 网络仍待现有代理恢复，不用连接器文件写入替代普通推送。


<a id="ux-001-20261018"></a>

## 2026-10-18：UX-001 首次使用与状态引导

### 开发前基线、反馈与范围

本地 main、HEAD 与实际 fetch 后的 origin/main 均为 1614dc47cef684fffa5c126e747ecd78e8ca64d1，工作区干净，Git 身份为 YOLIIIIII <143058454+YOLIIIIII@users.noreply.github.com>。沙箱访问用户提供的 12450 代理失败，获准权限后命令级代理 fetch 成功；不改全局配置。

UX-003 用户最新原话：“感觉这次改动之后可读性还可以，等我之后多用用再感受一下，我们先继续接下来的开发吧。”记录为可读性达到愿意继续推进的阶段性反馈，未推断用户做过键盘/预算/完整示例测试。代码/规则映射、组件、浏览器、远程 CI 已有证据，但验收标准中“人工按示例提交并记录结果”尚无具体记录，因此 Backlog 保留 in_progress；本轮明确授权不阻塞独立 UX-001。旧测试不是本轮重跑。

唯一业务范围 UX-001：真实状态的基础引导、可反复打开的使用指南、实际保存成功后的普通页面入口。UX-002 的自动定位/精确跳转/失败恢复/跨页面待审批恢复，以及 UX-004/005、模型/数据结构扩展均不实施。AGENTS 同步新增三问复盘约定。

### 实施前状态—页面行为对照

| 真实状态与来源 | 本轮目标行为 | 验收边界 |
| --- | --- | --- |
| refresh 七类数据尚未成功连接 | 不将初始空数组当作确定的空档案，不显示假成功/首次引导 | 连接错误仍可见，不宣称已有数据 |
| /stars 返回 0 个正式 Star（不含草稿） | 首页主入口“收集第一颗星星”，解释星星与探索依据；复用原空状态，不重复堆入口 | 不生成演示记录，不增加统计 |
| 有 status 非 archived 的实际 Star | 首页主入口微型探索，说明依据真实收藏和明确偏好；仍可继续收集 | 不强制顺序，不预言关键词一定有匹配 |
| 只有 archived Star | 说明归档不参与推荐，先查看档案恢复兴趣或继续收集 | 依据 retrieval.search/include_archived=False，不误称无星星 |
| collect / awaiting_decision，含 draft，且没有 star 决定 | 结果附近明确草稿已生成未入档，可检查/修改/确认/放下 | 正式计数不变；不实现自动滚动 |
| collect 决定 approved=False | 显示已放下、未加入档案，不给保存后的下一步 | 不创建 Star |
| 明确审批成功且返回实际 star_id，或手动 POST /stars 成功返回 id | 提供查看档案/开始探索的基础页面入口 | 导航不调用写 API，不做精确 ID 深链 |
| 生成或保存请求失败 | 不显示本次已保存或虚假下一步 | 保留现有错误/API/审批边界，失败恢复仍归 UX-002 |
| 任意页面，Mock/模型/未连接 | 原生可收起指南“星屿怎么使用”，简述四步及接受后去手记 | 不强制观看，不写永久状态；Mock 仅为规则模拟，不重复 UX-003 范围/预算帮助 |


### 实际实现与测试证据

修改：frontend/src/App.tsx、styles.css、App.test.tsx、frontend/e2e/smoke.mjs；AGENTS.md、README.md、ROADMAP.md、CHANGELOG.md、docs/IDEA_LOG.md、PRODUCT_BACKLOG.md、PROJECT_GUIDE.md、VERIFICATION.md。仅前端引导与文档/测试，不更改后端/API/Schema/依赖/迁移；无新重要源码文件。UsageGuide/SavedStarNextStep 留在 App 内，普通切页不调用正式写 API。

| 本轮检查 | 实际命令/环境 | 结果 |
| --- | --- | --- |
| 后端 pytest | `.venv/Scripts/python.exe -m pytest -q -rs --basetemp=.cache/ux001-pytest`；conftest 强制 Mock/空 Key，每例独立 SQLite | passed：52 passed；skipped：本机 TEST_POSTGRES_URL 未配置，PG 1 项跳过 |
| Ruff lint | `.venv/Scripts/ruff.exe check backend evals` | passed |
| Ruff format | `.venv/Scripts/ruff.exe format --check backend evals` | passed：21 files already formatted |
| 前端格式/lint/类型 | `npm run format:check` / `npm run lint` / `npm run typecheck` | passed |
| 前端 Vitest | `npm run test` | passed：3 files，30 tests（App 21、components 7、api 2） |
| 前端构建 | `npm run build` | passed：tsc -b + Vite，1581 modules |
| 浏览器闭环 | Node 22 执行 `e2e/smoke.mjs`，E2E_ALLOW_WRITE=true，base=http://127.0.0.1:5178，artifact=项目/.cache/ux001-e2e，PLAYWRIGHT_BROWSERS_PATH=项目/.cache/browsers | passed：新库为空→待确认→浏览器拦截一次批准模拟 503（后端未写）→真实放下→正式计数仍 0→重新生成并批准→下一步普通导航计数仍 1→搜索/关联/探索接受/修改/反馈/偏好/足迹；无 pageerror |
| 桌面/窄屏 | 同一闭环 1440/390px，首页/收集/探索/偏好；原生指南 Enter 展开、Space 收起及已有关联帮助 | passed：收起/展开均无横向溢出，截图保存于上述忽略目录 |
| 本机 PG / Docker / 真实模型 | 服务环境与调用额度未具备，亦不在本轮范围 | not run；本机 PG skipped 不计通过 |
| 用户 UX-001 首次使用体验 | 必须由用户本人体验 | not run，Backlog 保留 in_progress |

Windows / PowerShell，复用项目 Python 3.12.15、Node 22.23.3 和锁定依赖；npm 由项目 Node 启动 D:/Soft/Node/node_modules/npm/bin/npm-cli.js，PATH 优先 Node 22、缓存 .cache/npm。首轮前端 28 passed / 2 failed：新增查询同时命中隐藏指南/首页文案，模型模式标签也与实际既有文本不一致；修正查询定位后完整 format/lint/typecheck/test/build 通过 30 项，未删除断言或降低要求。首轮失败后 build 因前置测试退出未运行，最终轮 build 已实际执行；不把失败轮部分结果计为通过。

组件覆盖：空档案、已收藏/探索中的 Star、仅归档、未连接；草稿不算正式 Star、放下不算已保存、审批成功有下一步、保存失败/新生成失败无旧成功误报；手动保存成功/失败；反复导航不增加正式写入；指南在 Mock/模型模式可重复开关。仅归档与手动路径由组件验证，不冒称全部在浏览器单独跑过。

### 数据隔离与开发视觉检查

启动器为被忽略的 .cache/ux003_server.py（复用本机测试辅助，未提交）：启动前断言新库不存在、解析路径在项目 .cache 内，强制 Mock/空 Key，从应用实际 engine.url.database 再核对 **D:/Projects/wonder-orbit/.cache/ux001-browser-20261018.db** 后才迁移。后端仅本机 8018，临时 Vite 5178 的 /api 明确代理到 8018，不复用日常个人服务。

浏览器启动后还断言实际 /api/stars 返回空列表，避免将已有数据当作首次使用。失败通过浏览器仅一次拦截批准请求模拟（非后端故障注入），随后真实拒绝/批准均访问隔离后端；使用实际接口计数验证没有额外 Star。个人 wonder.db 未读取业务内容或写测试数据，运行前后文件 SHA-256 均为 F9AC010495FF365B8BA422EAC251DEB38B0CCA7FA50CC6890D40E119F1058C9B。

已查看 home-before.png、我的星屿-guide-390.png、收集星星-1440.png：首页单一主引导、指南焦点与四步可读、保存后的两个普通入口可见，原配色/品牌保留，无浮层。截图为开发核对，不能代替用户体验通过。

### 待用户体验与剩余边界

1. 打开首页与“星屿怎么使用”，确认能理解星星是什么、为什么要先收集，以及 Mock 只是规则模拟；指南可收起、重复打开。
2. 若当前档案为空，使用主入口收集第一颗星星；生成后手动下滑到结果，确认提示未入档，可修改或暂不保存。放下后应仍无新星星。不要为验收删除个人档案；非空场景可直接检查已有兴趣的探索引导，空状态自动化使用隔离库已有证据。
3. 重新整理并确认，检查“查看星星档案 / 开始微型探索”两个入口；已有星星首页不再强调第一颗。只有归档时，应提示恢复或继续收集。
4. 接受小体验后，按指南到体验手记记录感受；窄屏约 390px 再查看引导、指南开关和基础入口。反馈流畅度与是否仍有不清楚的下一步。

不包含自动滚动/精确 ID 跳转/跨页审批恢复/新失败恢复，也不扩展 UX-004/005。UX-003 当前可读性已获阶段性正面反馈，但“人工按示例提交并记录结果”的具体证据仍缺，不替用户填已执行记录。当前 M2，未修 P0 无已知实证，未完成 P1 仍 7 项；UX-001 用户体验后建议 UX-002，不自动续做。

### 本轮三问复盘

- 为什么用户需要这次改动？IDEA-001 的真实反馈是闭环下一步不清楚；页面现在直接解释星星/审批/探索，并在实际保存后给可点击入口。是否足够清楚仍等用户首次体验，不能用自动化代替。
- 它在 AI Agent 系统中解决了什么问题？这是 UI/UX 工程对生成结果、用户审批、正式持久化边界的准确表达；Mock/模型、草稿/正式 Star、归档/推荐状态不再混同。未改模型、工具、推理或检索能力，没有模型效果提升结论。
- 我们通过这次开发学到了什么？引导必须同时看真实 Star、归档状态和运行决定，不能用“无错误”推断已保存；导航入口应只切页，浏览器实际计数才能验证不重复写。测试也需区分隐藏指南与可见文案，使用准确查询；原生可收起指南已能满足本轮键盘与窄屏需求，无须新增引导依赖或持久化表。

本轮提交推送后将核对真实 CI 并在最终汇报给出 Job/PG 证据；按连续迭代方式留待下一轮补记，不为记录同一次 CI 额外触发构建。

上一轮 CI 独立补记：本轮通过 GitHub 连接器重新读取 [运行 39116179321](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39116179321) 的 Job 与 backend 日志，提交为 1614dc47cef684fffa5c126e747ecd78e8ca64d1；backend 117642320130 / frontend 117642320320 均 success。普通 pytest 为 52 passed / 1 skipped，独立 PG 命令实际 1 passed in 0.18s。此为 UX-003 交付的远程证据，不是本轮 UX-001 重跑，也不证明完整 Docker/PG 回滚或真实模型已验收。

本轮静态复核：.cache/ux001_doccheck.py 检查 284 个本地 Markdown 链接/锚点、28 个任务索引/详情状态、14 个 IDEA ID，均通过；12 个预期变更文件，未改 backend/app、Schema、依赖或迁移。UX-001/003 保持 in_progress，UX-002 尚未实施，UX-004/005 为候选；P1 仍为 7 项。git diff --check 通过，已检查业务 diff；临时测试前后端已停止，测试库与截图保留在忽略目录，个人数据库哈希保持不变。

<a id="ux-001-feedback2-20261018"></a>

## 2026-10-18：UX-001 人工体验反馈修正（二）

### 基线、真实反馈与本轮边界

开发前本地 main/HEAD 为用户预期 2988d376890566a83a32bb166201f99231f662c8，工作区干净；通过用户给定的命令级 HTTP 代理 127.0.0.1:12450 实际 fetch origin main，origin/main 与 HEAD 相同。沙箱首次代理连接失败，按权限流程重试成功，未修改全局 Git 配置。作者沿用 YOLIIIIII <143058454+YOLIIIIII@users.noreply.github.com>。

两条 2026-10-18 用户实际反馈并入 IDEA-001 / UX-001：正文顶部指南占空间、影响连续性；已有星星时探索过强、收集过弱。用户评价整体不错，仍有具体修改与新一轮体验待验收，不将其当作全项验收。实施定位决策单独标注为设计：持续收集与微型行动互相促进。复评全部未完成项含 deferred 后，优先级/阶段/顺序无变化，不改 ROADMAP；未修 P0 无新实证，未完成 P1 仍 7 项。

本轮只改顶栏指南入口、首页双入口与相关样式/测试/文档；后端、Schema、迁移、依赖、模型、API 审批逻辑未变。UX-001/003 的状态只在 Backlog 维护；UX-001 继续等待人工体验，UX-003 原具体人工记录缺口保留。UX-002 自动滚动/精确跳转/恢复、UX-004 统计检索、UX-005 足迹重设计、真实模型均未实施。

### 状态与实现对照

| 真实状态 | 本轮首页/指南行为 | 验证方式 |
| --- | --- | --- |
| 后端尚未连接或初始 refresh 失败 | 连接提示和未知计数；不显示“第一颗”或虚构真实档案；指南提示连接后可查看模式 | 组件连接失败与 null 模式 |
| 已连接、无正式 Star | “收集第一颗星星”，解释探索需要真实兴趣依据 | 组件与新空库浏览器 |
| 至少一颗 collected / exploring 等未归档 Star | 浅紫“收集星星”/深紫“微型探索”，共同 .hero-core-action 尺寸/权重；桌面并排，窄屏可换行；文案说明持续收集和行动 | 组件两种状态；浏览器实际尺寸/权重、桌面同排与导航计数 |
| 只有 archived Star | 保留归档不参与推荐的提示，查看档案恢复或继续收集；不呈现可探索双按钮 | 组件 |
| 待确认草稿 / 拒绝 / 保存失败 | 仍不当作正式 Star 或成功保存；现有审批/保存后引导不变 | 组件与隔离浏览器失败/放下/批准 |
| 所有八页、Mock/模型/未连接 | 顶栏状态、帮助、刷新分组；指南内容仅在复用 Modal 打开时出现，原正文 details 与空白占位移除；四步与模式原语义保留 | 八页组件/浏览器；三种模式组件 |

guideOpen 仅为本次 React 临时状态，初值 false；按钮有帮助图标、文字和 accessible name“使用指南”、aria-haspopup=dialog。Modal 沿用对话框语义、初始聚焦关闭按钮、Tab/Shift+Tab 循环、Escape/显式关闭/点击遮罩关闭并恢复帮助入口焦点；点击内容不关闭，不自动打开，不写持久化状态。收集页打开帮助后未保存的修改和待确认草稿保留，没有新请求。首页按钮只 setPage，不调用写 API。

### 本轮实际命令与结果

环境：Windows / PowerShell、项目 Python 3.12.15 / Node 22.23.3 与已有锁定依赖。npm 由项目 Node 启动 D:/Soft/Node/node_modules/npm/bin/npm-cli.js，当前进程 PATH 优先项目 Node，缓存 .cache/npm。

| 检查 | 实际命令/环境 | 最终结果 |
| --- | --- | --- |
| 后端 pytest | `.venv/Scripts/python.exe -m pytest -q -rs --basetemp=.cache/ux001-feedback2-pytest`；conftest 强制 Mock、空 Key、隔离 SQLite | passed：52 passed；skipped：本机缺 TEST_POSTGRES_URL，PG 1 项跳过，11.61s |
| Ruff | `.venv/Scripts/ruff.exe check backend evals`；`.venv/Scripts/ruff.exe format --check backend evals` | passed；21 files already formatted |
| 前端格式/lint/类型 | frontend 中 `npm run format:check`、`npm run lint`、`npm run typecheck` | passed |
| Vitest | `npm run test` | passed：3 files、40 tests（App 31、components 7、api 2）；样式/E2E 定稿轮 19.87s，补强未连接/仅归档断言后再核对格式/lint/类型与 40 项测试，13.59s |
| build | `npm run build` | passed：tsc -b + Vite，1581 modules，4.15s |
| 隔离浏览器完整闭环 | `node e2e/smoke.mjs`；E2E_ALLOW_WRITE=true；E2E_BASE_URL=http://127.0.0.1:5178；项目 .cache/browsers | passed：收集→拦截模拟批准失败→真实放下→重新生成/批准→档案/搜索/关联→探索空预算/0 元→接受/编辑/反馈→偏好确认→足迹；无 pageerror |
| 1440px / 390px | 同一浏览器脚本，八页各检查布局、顶栏三个操作无重叠且在屏幕内；指南 Enter 打开、Tab/Shift+Tab、三种关闭与恢复焦点；首页双按钮尺寸/文字权重与实际 Star/Quest 计数 | passed；展开/关闭不新增横向溢出，指南边界完全位于视口；原 UX-003 字段帮助 Enter/Space/点击继续通过 |
| 本机 PG / Docker / 真实模型 | 本机服务/额度未配置，且不在本轮实现范围 | PG skipped；其余 not run，不记通过 |
| 用户新一轮人工体验 | 必须由用户本人操作、评价 | not run，等待体验，不关闭 UX-001 |

失败、修复与重试：首轮沙箱 Vitest 报 realpath spy.js EPERM，0 tests、3 unhandled errors；提升运行权限后完整检查 40 项通过。首轮浏览器已通过业务闭环与桌面八页，但在 390px 首页指南边界断言失败，截图显示原 Modal 的 650px 固定宽度撑开隐式网格，文字与关闭按钮裁切；不算浏览器通过。修复 .modal-backdrop 的 minmax(0,1fr) 网格列及 Modal min-width/居中，保留全部断言；另建全新隔离库重跑完整闭环与 16 个页面/尺寸组合通过。样式/E2E 最终变更后再次完整执行前端格式/lint/typecheck/40 tests/build，均通过；未删测试或降低要求。

### 数据隔离、视觉核对与文档范围

被忽略的启动器 .cache/ux001_feedback2_server.py 在迁移前断言目标新库不存在、路径位于项目 .cache，并将应用实际 engine.url.database 与目标解析路径比对，强制 Mock/空 Key。首轮库为 D:/Projects/wonder-orbit/.cache/ux001-feedback2-browser-20261018.db；修复后新库为 **D:/Projects/wonder-orbit/.cache/ux001-feedback2-browser-retry-20261018.db**。后端仅本机 8018，临时 Vite 5178 的 /api 显式代理到 8018。浏览器启动后还检查 /api/stars 实际为空，不把旧数据当首次体验。

失败截图留 .cache/ux001-feedback2-e2e；最终截图留 .cache/ux001-feedback2-e2e-retry。已实际查看最终“我的星屿-1440.png”“我的星屿-390.png”“我的星屿-guide-390.png”：原星球与配色保留、正文自然开始、双按钮可见、窄屏指南关闭按钮与四步完整显示。截图为开发核对，不能代替用户验收。个人 wonder.db 仅核对文件哈希、不读业务内容；前后 SHA-256 一致，均为 55CA7EDCDC1563E045445B5B3BD5BAB182CF0C19E1F1BE4099C416967C02B626；首次沙箱 Get-FileHash 报占用，正常权限复核成功。测试写入仅发生于上述两份隔离库。

改动文件：frontend/src/App.tsx、styles.css、App.test.tsx、frontend/e2e/smoke.mjs；README.md、CHANGELOG.md、docs/IDEA_LOG.md、PRODUCT_BACKLOG.md、PROJECT_GUIDE.md、VERIFICATION.md。共 10 个预期文件，无新增重要源码文件；ROADMAP 的阶段/顺序不变，AGENTS 无需修改。临时库/截图/辅助启动器保持忽略，不提交。.cache/ux001_feedback2_doccheck.py 已检查 287 个本地 Markdown 链接/锚点、28 个任务索引/详情状态、14 个 IDEA ID、7 项未完成 P1 及预期文件集合，均通过；git diff --check 与业务/文档 diff 复核通过，无后端/Schema/锁文件/数据库/临时文件混入。临时前后端已停止；提交前再次 ls-remote 核对 origin/main 仍为基线，Git 本地作者身份正确。

### 上一轮 UX-001 远程 CI 成功补记（不是本轮重跑）

本轮通过 GitHub 连接器重新读取 [运行 39118235192](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39118235192) 的 Job 和日志，属于基线提交 2988d376890566a83a32bb166201f99231f662c8。backend Job 117648310266 与 frontend Job 117648310079 均 completed / success；backend 普通 pytest 52 passed / 1 skipped，独立 `uv run pytest backend/tests/test_postgres.py --override-ini addopts=` 实际 **1 passed in 0.19s**；frontend 30 tests passed、build success。此补记只证明上一轮远程运行，不证明本轮或完整 Compose/PG 回滚/并发、真实模型通过。本轮推送后的 CI 将在最终报告给出真实链接与日志结果，下一轮再补记，不为记录同次构建再提交。

### 待用户体验

1. 桌面首页确认正文不再有顶部折叠指南占位，视觉是否连续；顶栏能否自然找到“使用指南”。在收集、探索、偏好等页面重复打开，查看四步与真实模式说明是否清楚。
2. 用关闭按钮、Escape、点击弹窗外部关闭；Tab/Shift+Tab 应留在弹窗，关闭后回到帮助入口。编辑收集内容时打开/关闭，确认输入不丢失。
3. 有未归档 Star 时，首页两个按钮是否同样容易发现，是否理解可以继续收集也可以行动；分别进入收集/探索，确认只是正常切页。无需为测试删除个人数据；空档案/仅归档/未连接的状态已有自动化覆盖。
4. 在约 390px 窄屏检查模式/帮助/刷新不拥挤，指南关闭按钮、四步和首页双入口完整可用；原草稿确认、保存和 UX-003 帮助是否仍自然。报告仍不清楚或不顺畅之处。

### 本轮三问复盘

- 为什么用户需要这次改动？IDEA-001 两条真实反馈说明：找到帮助不该牺牲首页连续性，已有兴趣也仍需持续收集。本轮收起正文占位、顶栏随时打开，两个按钮接近的可发现性仍需用户体验确认。
- 它在 AI Agent 系统中解决了什么问题？改进的是 UI/UX 与工作流状态展示：帮助解释真实四步、Mock/模型与审批边界，首页按正式未归档 Star 提供路径；不改变推理、检索、工具或模型能力，没有智能效果提升结论。
- 我们通过这次开发学到了什么？App 的页面入口视觉可调整而不改变审批/持久化；复用 Modal 仍需在真实窄屏检查 CSS 网格的最小宽度。App.test 验证三种模式和状态，smoke.mjs 用真实焦点、几何边界及 Star/Quest 计数补足 JSDOM 的局限，首轮失败直接定位并修复了裁切问题。

<a id="ux-002-20261018"></a>

## 2026-10-18：UX-002 操作结果与流程衔接

开发前本地 main 与实际 fetch 的 origin/main 均为 943e8052e2b3524cbf641f9f27ea5ac8233d3b23，工作区干净，Git 作者正确；命令级代理 12450 在沙箱失败、正常权限 fetch 成功，不改全局配置。已阅读规定文档与前后端相关源码。以下先记录实施前状态/验收边界，后续追加实际实现和测试，不把目标当通过。

UX-001 阶段性验收：本次用户原话“并且我也体验了一下，两处改动都还不错，我们继续接下来的开发吧”，明确对应顶栏指南弹窗与首页双核心入口。结合先前“整体不错”、既有空档案/归档/审批状态测试、隔离首次闭环与双尺寸指南检查，当前范围验收条件已具备，Backlog 关闭 UX-001。未推断用户亲测所有键盘/空档案/390px。UX-003 仍缺具体人工按示例提交记录，单独保留。

### 实施前状态—操作—目标结果—写入边界

| 状态 | 用户操作 | 目标结果 | API 写入边界 |
| --- | --- | --- | --- |
| collect / explore 新生成成功 | 整理 / 寻找 | DOM 提交后一次性定位本轮 run_id 的草稿/候选/澄清顶部并程序性聚焦；减少动画偏好无平滑动画 | 仅原生成 POST，定位无请求 |
| 生成失败 / 请求后用户切页 | 等待 / 导航 | 不定位旧结果、不拉回页面；错误关联真实 run_id | 无额外写入 |
| 审批成功且有真实 star_id / 手动保存返回 id | 查看这颗星星 | GET 目标、清除档案搜索/筛选、复用编辑 Modal；读取失败可原入口重试 | 只读，不重放保存 |
| 每个候选已批准且有 quest_id | 查看这次体验 | GET /quests 按 ID 核对后定位自己的卡片；不自动打开反馈表单 | 只读，不重放审批/反馈 |
| 拒绝 / 保存失败 / 无可核验 ID | 查看结果 | 不出现虚假精确成功入口 | 不新增正式记录 |
| failed 的 collect/explore，且无决定、有效原请求 | 重试生成 | 先 GET 核对，POST retry 返回新 run_id，保留原失败，定位新结果 | 只新建生成运行，不自动批准 |
| running / 已决定 / reflection | 查看运行 | 不提供生成重试；running 不猜后端保护期 | 不绕过后端重试限制 |
| 刷新后真实 awaiting_decision，存在未决定草稿/候选 | 打开待确认结果 | GET 对应 run_id 再核对，进入正确页面并定位；无有效结果不展示假入口 | 只读，审批仍由用户触发 |
| 仅有澄清、无可审批候选 | 查看澄清提示 | 定位真实问题，避免假称待审批 | 只读 |
| 普通 refresh / 无关状态变化 / 弹窗打开 | 刷新 / 帮助 | 不重复抢滚动/焦点，不破坏 Modal 焦点管理 | 仅现有读取 |

### 实际实现与 ID / 焦点依据

App 的 setPage 同步递增导航序号，生成/只读导航/恢复/重试分别记录操作起点；异步返回前如用户切过页（包括切走又回来），不跳页、不定位。生成开始清除旧结果，只有新运行的有效草稿/候选/澄清才能提交 focusTarget；useEffect 等结果 DOM 提交并且 busy 结束后执行一次，随后清空。结果区 tabIndex=-1、区域名称明确，以 preventScroll 聚焦再 scrollIntoView(block=start)，scroll-margin-top=24px；prefers-reduced-motion:reduce 使用 auto，其余 smooth，不依赖固定延时。没有足够底部空间时遵从浏览器最大滚动边界，仍让提示可见；不添加大块空白。Modal 存在时丢弃自动定位，不破坏关闭后焦点恢复。

正式 Star 的精确入口来自成功审批后 GET /agent/runs/{id} 的 decisions.star.star_id，手动路径使用 POST /stars 返回 id；不根据 notice 文本猜测。查看时 GET /stars/{id}，核对 ID、清空关键词/搜索结果/类别/状态过滤，复用档案页及编辑 Modal；关闭后原按钮如已卸载，回到对应 StarCard 的稳定 DOM ID。每个候选只取自己 decisions[index] 的 quest_id；当前无单个 Quest GET 路由，因此读取现有 /quests 列表核对目标后定位卡片，不默认打开反馈表单。目标缺失给可恢复提示并保留原入口，不改为打开其他记录，不重新审批。

错误显示真实 ApiError.runId 及详情入口，用户主动查看才进入足迹。运行详情、打开待确认、retry 都先 GET 核对状态；只有 collect/explore、failed、无决定且有原请求时提供重试。running 不猜测可变的后端超时配置，不暴露绕过保护的操作；后端仍是最终裁决，重试失败的新 run_id 也能进入详情。重试成功核对返回的新 run_id，保留旧失败运行，定位新结果而不批准。awaiting_decision 需有未决定草稿/候选才显示“打开待确认结果”；只有问题时显示“查看澄清提示”，无内容或已决定不假称待审批。

refresh 同步当前草稿/候选/足迹详情的服务器决定；对仍在查看但不在最近 50 项列表中的 run_id 额外 GET，避免沿用过期本地成功/待确认。没有新增分页或跨重启 checkpointer。operationActive ref 补足 busy 的同步点击保护，后端原幂等/指纹/事务/约束仍原样保留；定位与导航不写正式记录。

### 实际命令、自动化与失败重跑

Windows / PowerShell，项目 Python 3.12.15、Node 22.23.3 和已有锁定依赖；npm 由项目 Node 执行 D:/Soft/Node/node_modules/npm/bin/npm-cli.js，进程 PATH 优先项目 Node，缓存 .cache/npm。本轮正常权限执行，未把旧轮成绩当本轮重跑。

| 本轮检查 | 实际命令/环境 | 结果 |
| --- | --- | --- |
| pytest | `.venv/Scripts/python.exe -m pytest -q -rs --basetemp=.cache/ux002-pytest`；conftest 强制 Mock/空 Key，每例独立 SQLite | passed：55 passed；skipped：本机 TEST_POSTGRES_URL 未配置，PG 1 项跳过；11.51s |
| Ruff | `.venv/Scripts/ruff.exe check backend evals`；`.venv/Scripts/ruff.exe format --check backend evals` | passed；21 files already formatted |
| 前端格式/lint/类型 | frontend 中 `npm run format:check`、`npm run lint`、`npm run typecheck` | passed |
| Vitest | `npm run test` | passed：4 files、69 tests（App 31、App.results 29、components 7、api 2），最终 18.39s |
| build | `npm run build` | passed：tsc -b + Vite，1581 modules，5.31s |
| 完整浏览器 | Node 22 `e2e/smoke.mjs` → `verifyResults`，E2E_ALLOW_WRITE=true，E2E_INJECTED_FAILURE=true，base 127.0.0.1:5178，PLAYWRIGHT_BROWSERS_PATH=项目/.cache/browsers | 重跑 passed：原搜索/关联/预算/审批/反馈/偏好/足迹闭环，八页指南双尺寸；新生成/澄清、减少动画、refresh 不重复定位、刷新丢失内存后恢复、异步切页取消、真实失败/新运行重试、精确 Star/多 Quest ID 与正式记录/反馈计数不变 |
| 本机 PostgreSQL / Docker / 真实模型 | 本机服务与调用额度未配置，本轮未扩展环境或模型 | PG skipped；其余 not run，不算通过 |
| 本轮用户 UX-002 人工体验 | 用户本人实际操作后补记 | not run，Backlog 保留 in_progress |

新增后端 3 个测试检查 running 保护期 409、已批准/拒绝不可重试，运行数与正式 Star 数不变。既有失败重试测试仍检查新 run_id。组件新增 29 例，覆盖两种动画偏好、草稿/候选/澄清、重复生成/失败清除旧结果、切走又返回、Modal、两种保存、过滤清除、多个 Quest、拒绝/缺 ID/目标暂缺恢复、真实 run_id、failed/running/decided/reflection/已有决定的重试边界、过期待审批与最近列表之外的运行。JSDOM 仅模拟 scrollIntoView 调用，实际位置和 Tab 由浏览器核对。

真实失败与重跑记录：首轮组件 65 项通过；补充最近列表之外/过期待审批/缺 star_id 后完整检查 68 项通过。首轮浏览器旧闭环和八页指南通过，但 UX-002 脚本的导航 exact 查询未包含桌面收集按钮里的“＋”，30s timeout，整轮不算通过；改为主导航内前缀查询，保留断言、换全新隔离库重跑完整闭环通过。代码复核将 effect 延后至 busy=false，避免处理提示卸载造成定位位移；没有固定 sleep 或删减检查。随后新增普通 Tab 流程和定位时截图，使用另一份新库核对最终脚本，此次复核在 smoke 保存后读取目标弹窗处超时，日志确认没有发出目标 GET：保存 notice 与下一步已出现、act 的 refresh 仍未完成，快速点击被操作锁忽略。修复 SavedStarNextStep 在 busy 时禁用两条入口，新增延迟 /stats 刷新的回归测试；最终完整前端 69 项和 build 通过。换第四份新库（delivery）完整重跑，包含普通 Tab 的最终脚本通过，无跳过故障段、无 pageerror，未降低要求。

### 隔离数据与变更范围

被忽略的 .cache/ux002_server.py 启动前断言新库不存在、解析路径在项目 .cache，从应用实际 engine.url.database 再核对目标后才 Alembic upgrade head，强制 Mock/空 Key；后端只监听 127.0.0.1:8018，临时 Vite 5178 的 /api 明确代理到 8018。首轮 .cache/ux002-browser-20261018.db，修复重跑 .cache/ux002-browser-retry-20261018.db，追加复核 .cache/ux002-browser-final-20261018.db（保存后快速点击暴露时序缺陷），修复后最终交付库 .cache/ux002-browser-delivery-20261018.db。浏览器开头实际 /api/stars 断言空库，避免把个人数据当测试。

故障仅在此隔离启动器中，对无敏感文本 UX002-E2E-FAIL- 注入一次 ModelFailure(timeout)，请求仍经过真实 FastAPI/LangGraph/审计和 retry API；重试该文本正常 Mock 生成，原失败可 GET。故障不提交、不改变正式适配器/工作流，不使用真实 Key。E2E 脚本没有此 fixture 时明确 SKIP 故障段，其余流程继续；本轮环境明确启用并实际验证，不以配置存在代替执行。

产物分别保留于 .cache/ux002-e2e、ux002-e2e-retry、ux002-e2e-final、ux002-e2e-delivery；库、截图、辅助脚本均不提交。个人 wonder.db 仅核对文件哈希，不读业务内容；测试前 SHA-256 为 55CA7EDCDC1563E045445B5B3BD5BAB182CF0C19E1F1BE4099C416967C02B626，最终运行后哈希与测试前完全一致；临时前后端已停止。

本轮范围为前端 App、components/样式、既有测试/setup/smoke，新 App.results.test.tsx / e2e/results.mjs，以及 backend/tests/test_acceptance.py 的保护测试；后端业务、API、Schema、迁移、依赖/锁文件未修改。同步 IDEA_LOG、Backlog、VERIFICATION、README、CHANGELOG、PROJECT_GUIDE；ROADMAP 仅因 UX-001 当前范围验收、M2 当前任务转 UX-002 更新相关说明，不改变优先级或后续里程碑。

### 上一轮 UX-001 远程证据补记

本轮重新读取 [39123903729](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39123903729) 的实际 Job/日志，提交 943e8052e2b3524cbf641f9f27ea5ac8233d3b23；frontend 117664928473、backend 117664928613 均 completed/success。backend 普通 pytest 52 passed / 1 skipped，独立 `uv run pytest backend/tests/test_postgres.py --override-ini addopts=` **1 passed in 0.17s**。这是上一轮补记，不代表本轮 CI 或完整容器/PG 回滚/并发、真实模型已验收。本轮 push 后将核对两个 Job 与独立 PG，并在最终报告给出真实链接；按连续迭代方式下一轮补记，不为同一构建额外提交。

### 待用户按顺序体验

1. 收集一段兴趣，整理后观察是否自然看到当次“草稿待确认”顶部；从结果继续 Tab 到操作。失败不定位旧结果；可尝试生成后主动切页，返回不应突然拉回。
2. 确认保存后点“查看这颗星星”，确认正是刚保存的内容，关闭后焦点回到该卡片；原搜索/筛选应解除。手动填写保存也有相同入口，导航不会二次保存。
3. 进行微型探索，检查候选或真实澄清是否可发现；接受一项后“查看这次体验”定位自己的卡片，再由你选择何时记录感受，不自动声称完成。多项入口各指向自己的体验。
4. 生成后先不审批，刷新页面，从 Agent 足迹选择对应运行并打开待确认结果；内容/定位应正确。若遇实际生成失败，用真实运行详情查看和适用重试；不要求主动破坏个人数据或配置来制造故障。
5. 在约 390px 窄屏及系统减少动画设置下体验定位/Tab/弹窗，确认首页双入口、顶栏指南和 UX-003 字段说明未回退。无匹配和各种失败保护已有隔离自动化，不冒称用户亲测。

### 本轮三问复盘

- 为什么用户需要这次改动？用户真实反馈是生成后仍停留在输入区，并希望保存/接受后找回对应记录；本轮把结果、真实记录和下一步连接起来，减少手动寻找，是否自然仍待本人体验。
- 它在 AI Agent 系统中解决了什么问题？这是 UI/UX 与工作流可靠性的表达：真实 run_id/审批决定/正式 ID 控制入口，恢复不等于重放批准，重试保留审计。没有改变模型理解、推荐质量、工具或检索能力，不宣称智能增强。
- 我们通过这次开发学到了什么？一次性定位要同时等待 DOM 和处理状态稳定，异步返回还需页面导航版本保护；精确导航不仅要 ID，还要目标存在、过滤和跨页弹窗焦点恢复。JSDOM 调用断言不足以证明滚动，真实浏览器/隔离数据库计数与后端保护测试共同验证边界。

最终复核：已查看 .cache/ux002-e2e-delivery/result-focus-390.png、clarification-1440.png、quest-target-1.png，草稿顶部与真实澄清可见、体验定位正确、原品牌与 UX-003 中文提示保留。完整浏览器最终通过包括 1440/390px 几何边界、正常 Tab、八页指南和减少动画；故障段真实执行。文档检查脚本 .cache/ux002_doccheck.py 已核对 294 个本地链接/锚点、28 个任务索引/详情、14 个 IDEA、6 项未完成 P1、16 个预期文件；git diff --check 与源码/测试 diff 复核通过。个人 wonder.db 前后 SHA-256 相同，未改业务后端/Schema/迁移/依赖；提交前 ls-remote 核对 main 仍为预期基线。

<a id="ux-002-star-reading-20261018"></a>

## 2026-10-18：UX-002 人工反馈修正——星星查看与编辑分离

### 基线、反馈和范围

本地 main / HEAD 与实际 fetch 后的 origin/main 均为 edfb3892082a6ebe375163d1b3fb49b90dffa8c8，工作区干净，作者为 YOLIIIIII <143058454+YOLIIIIII@users.noreply.github.com>。命令级代理 12450 在沙箱连接失败，正常权限 fetch 成功；不改全局配置，不覆盖未知修改。

2026-10-18 用户实际体验原话：“我都体验过了，你想了解的两个地方，第一点我觉得挺好的，切换很丝滑；但是第二点，我确实有点意料之外，我只是想看看而已。其余都不错。”记录为自动定位良好、整体衔接正面反馈，以及默认打开编辑表单的明确预期偏差；没有扩写为所有边界/键盘/390px 已由用户亲测。追加 IDEA-001，不新增重复想法。UX-002 继续修正并等待再体验，UX-001 保持 done，UX-003 的具体人工记录缺口独立保留。全部未完成项含 deferred 复评无排序或优先级变化，M2 与 6 项未完成 P1 保持，ROADMAP 无需改动，不开始 AGENT-001。

### 实际实现与操作边界

| 操作/数据 | 当前行为 | 写入边界 |
| --- | --- | --- |
| 保存后的查看、首页/档案 StarCard、轨道两端、探索来源 | 共用 selectedStar，默认只读 StarDetails + 现有 Modal；来源入口按 ID 读取，精确档案跳转仍清除过滤 | 查看仅 GET 或当前真实列表，不 POST/PUT/DELETE |
| 阅读详情 | 标题、类别/标签/状态，原文与描述独立展示，真实原因才显示；预计时间/预算/精力、来源及存在的时间 | null 显示尚未记录，不转为零；明确预算 0 显示 0 元，不猜原因 |
| 原文、长描述、链接 | 普通 React 文本，换行/任意长词可折行；Modal 可滚动；只有解析为 http/https 的 URL 可点击，其他来源仍安全文本 | 不注入 HTML，不抓网页，不新增 Schema |
| 编辑星星 | 明确点击才挂载原 StarEditor，保留现有允许字段与校验、状态归档 | 挂载和切换无请求 |
| 取消编辑 / 关闭 | 卸载未保存草稿；取消回阅读标题，关闭回原触发元素或跨页对应卡片 | 无保存/删除请求 |
| 保存成功 | PUT 返回的正式 Star 核对同一 id，展示服务端确认内容并更新卡片缓存，回阅读 | 单次既有 PUT；不以输入值或 notice 当作服务器结果 |
| 保存失败 | 保留编辑器、输入、错误与重试方式，不显示成功；取消仍可回原详情 | 不假称已保存；重试由用户触发 |
| 删除 / 归档 | 删除只在编辑中，沿用确认及后端引用保护；引用星星不可删但可改状态归档 | 保留原 DELETE/PUT，不由查看触发 |
| 异步详情读取 / 读写中关闭 | 点击时捕获 starOpener；保存响应用查看版本避免关闭后重新弹出；Modal Tab 循环包括新链接 | 不增加持久化状态或依赖 |

焦点：默认阅读聚焦 Modal 关闭按钮；进入编辑聚焦标题输入；取消/保存后聚焦详情标题（tabIndex=-1），普通 Tab 可进入链接和编辑按钮；关闭还原原入口，精确跨页沿用 StarCard DOM ID。Quest 的查看/编辑、UX-002 一次性结果定位/减少动画/失败重试/刷新待确认恢复、顶栏指南和首页双入口继续沿用，没有新工作流、真实模型或新数据库字段。

### 本轮实际检查

环境：Windows / PowerShell，已有 Python 3.12.15 / Node 22.23.3 与锁定依赖。npm 仍由项目 Node 执行 D:/Soft/Node/node_modules/npm/bin/npm-cli.js，PATH 优先项目 Node，缓存 .cache/npm。

| 检查 | 实际命令/环境 | 结果 |
| --- | --- | --- |
| 后端 pytest | `.venv/Scripts/python.exe -m pytest -q -rs --basetemp=.cache/ux002-star-reading-pytest`，conftest 强制 Mock/空 Key、逐例隔离 SQLite | passed：55 passed；skipped：本机缺 TEST_POSTGRES_URL，PG 1 项跳过；15.68s |
| Ruff | `.venv/Scripts/ruff.exe check backend evals`；`.venv/Scripts/ruff.exe format --check backend evals` | passed；21 files already formatted |
| 前端格式/lint/类型 | frontend 中 `npm run format:check`、`npm run lint`、`npm run typecheck` | passed；E2E 选择器最终修正后又核对格式/lint |
| Vitest | `npm run test` | passed：4 files、82 tests（App 31、App.results 39、components 10、api 2）；19.43s |
| build | `npm run build` | passed：tsc -b + Vite，1581 modules，3.59s |
| 本机 PG / Docker / 真实模型 | 服务/额度未具备且不在本轮新增范围 | PG skipped，其余 not run，不记通过 |
| 用户修正后的再次体验 | 本人尚未反馈修正版本 | not run，保留 UX-002 in_progress |

组件保留原 69 项并扩展为 82 项：默认阅读/无输入框/无删除、四类卡片和引用入口、精确 ID 查看、取消/关闭丢弃、服务端确认内容、0 元与归档、失败重试、删除保护、原文/描述独立、未知不当零、安全文本/非 http 链接，以及异步入口失焦后的焦点恢复。旧 69 项与旧 CI 不能当本轮重跑，以上为实际执行。

### 浏览器隔离、失败修复与重跑

Node 22 执行 frontend/e2e/smoke.mjs → verifyResults → verifyStarReading，base=http://127.0.0.1:5178，E2E_ALLOW_WRITE=true，E2E_INJECTED_FAILURE=true，PLAYWRIGHT_BROWSERS_PATH=项目/.cache/browsers。沿用隔离启动器的一次性 Mock timeout，仅对无敏感 UX002-E2E-FAIL- 文本故障注入，真实 failed/retry API 及新 run_id 回归继续执行，不调用真实模型。新的编辑失败由浏览器仅一次拦截 PUT 503 模拟，核对真实 GET 仍是旧值，重试才真实写入。

实际三份新库：首轮 D:/Projects/wonder-orbit/.cache/ux002-star-reading-20261018.db，修复重跑 .cache/ux002-star-reading-retry-20261018.db，最终 .cache/ux002-star-reading-final-20261018.db。被忽略的 .cache/ux002_star_reading_server.py 每次启动先断言新库不存在、解析路径在项目 .cache，核对应用实际 engine.url.database，再迁移；强制 Mock/空 Key，后端仅本机 8018。临时 Vite 5178 的 /api 显式代理 8018，浏览器开头实际 /api/stars 返回空列表。个人 wonder.db 只核对文件哈希，不读取业务内容；测试前 SHA-256 为 B449C756D6B762E52D0C76CC11C6788D7FEDCCE8BA7E938A929AD5B3DEE43AA9，结束后另行核对，不沿用上轮个人库哈希。

首轮组件 81 项、完整前端及后端通过；首轮浏览器原闭环通过，但新阅读入口关闭后的焦点断言失败。原因是异步读取时触发按钮被 busy 禁用，Modal 打开时原活动元素已丢失；修复为点击时捕获 starOpener、Modal 明确 returnFocusTo，跨页仍用卡片 fallback，保存时不覆盖原入口。补 1 个异步失焦组件回归后 82 项与 build 通过。第二轮新库已通过五类查看、双尺寸长文、链接 Tab、取消、保存失败/重试，但归档脚本 exact 标签查询未匹配含选项的状态控件，30s timeout，整轮不记通过；改用 role=combobox 和状态名称前缀定位，保留实际后端 archived 结果断言，再换新库完整重跑。第三轮全量 passed：原 UX-001/002/003 闭环、真实故障/重试/恢复、五类只读入口、1440/390px、长文与链接 Tab、取消/保存失败/重试/服务器最新内容、引用删除保护后归档，以及新手动星星明确编辑后成功删除；无 pageerror，未删除测试或降低断言。

实际查看最终 star-reading-1440.png 与 star-reading-390.png，原文和描述分区清楚、长文本可滚动、无横向溢出。视觉复核将新详情标题的键盘焦点纳入既有暖黄色规则；仅此 CSS 追加后 format/lint/build 再通过（4.20s），被忽略的只读预览脚本在同一隔离库两种宽度验证焦点色、无表单且零写请求，截图更新于 .cache/ux002-star-reading-e2e-final。没有据此声称用户已体验。

最终安全/范围复核：个人 wonder.db 前后 SHA-256 均为 B449C756D6B762E52D0C76CC11C6788D7FEDCCE8BA7E938A929AD5B3DEE43AA9，未向个人库写测试数据；临时前后端已停止。首轮/第二轮/最终产物分别位于 .cache/ux002-star-reading-e2e、ux002-star-reading-e2e-retry、ux002-star-reading-e2e-final，均保持忽略。.cache/ux002_star_reading_doccheck.py 实际检查 296 个本地 Markdown 链接/锚点、28 个任务索引/详情状态、14 个 IDEA ID、6 项未完成 P1 与 13 个预期变更文件，通过；git diff --check 与实现/测试/文档 diff 复核通过。仅改 App、components/样式、App.results/components 测试、smoke/results 浏览器，以及 README/CHANGELOG/IDEA_LOG/Backlog/VERIFICATION/PROJECT_GUIDE；无新增文件、后端/Schema/迁移/依赖、个人配置或临时产物混入。ROADMAP 阶段/顺序未变，未修改；提交前再次核对远程 main 仍为预期基线。

### 上一轮远程 CI 补记

本轮重新读取 [39126328074](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39126328074) 的实际 Job/日志，提交 edfb3892082a6ebe375163d1b3fb49b90dffa8c8。backend 117672117198、frontend 117672117360 均 completed/success；普通后端 55 passed / 1 skipped，独立 `uv run pytest backend/tests/test_postgres.py --override-ini addopts=` **1 passed in 0.13s**，前端为上一轮 69 passed。这是上一轮补记，不算本轮重跑，也不代表完整容器、PG 回滚/并发或真实模型已通过。本轮推送后的实际 CI 在最终汇报给出，后续迭代再补记，不为记录同次构建额外提交。

### 待本人再次体验与三问复盘

1. 保存后点“查看这颗星星”，应先读到详情，原文和描述是否清楚；其他卡片、轨道和探索引用应有同样预期。
2. 明确点“编辑星星”，修改后取消应不保存；保存后回阅读并显示新内容。删除仅在编辑中，已有引用的星星可归档。
3. 桌面与约 390px 看长文、来源链接和未知值是否自然；用关闭/Escape、编辑/取消及普通 Tab 体验焦点，原结果定位和 Quest 流程应继续顺畅。用户尚未报告的边界不代填人工通过。

- 为什么用户需要它？真实反馈是“只是想看看”，默认编辑造成意外；本轮把阅读作为查看入口的默认动作，修改由明确选择触发。
- 它在 AI Agent 系统中解决了什么问题？对齐阅读、修改和持久化意图，并清楚区分原文与结构化内容、未知与零；保留审批/API 安全边界，属于 UI/UX 与工作流展示改进，没有模型能力提升。
- 我们通过这次开发学到了什么？入口写“查看”就需要提供阅读界面；服务端返回记录才是保存后的展示依据。异步 busy 会影响真实浏览器焦点，JSDOM 不会自动重现全部行为，需要显式触发元素、组件回归与浏览器几何/键盘/写入检查共同验证。

<a id="agent-001-phase1-20261025"></a>

## 2026-10-25：UX-002 实际验收与 AGENT-001 第一阶段（仅离线）

### 范围、基线与阶段

来源：本轮用户完整任务书及转述的实际体验。开始时工作区/暂存区干净，分支 main，本地 HEAD 与预期 a455b17dcca8d6ed13055af83e4f51e3046b6150 一致。默认 Git 连接失败，原因是已有代理 127.0.0.1:7897 不可用；检测用户此前提供的 127.0.0.1:12450 可连接后，只在相关 Git 命令加 `-c http.proxy=http://127.0.0.1:12450`，实际 `ls-remote origin refs/heads/main` 返回同一 SHA。未修改全局代理或覆盖未知修改。

已读取 AGENTS、ROADMAP、Backlog、IDEA_LOG、VERIFICATION、PROJECT_GUIDE、README、CHANGELOG、evals 文档、config/model_adapter/workflow/tools/schemas、相关模型/审批测试、CI/.env.example/.gitignore/uv.lock。模型/运行器改动不涉及前端/Prompt/Schema/迁移/工作流权限/工具清单；未新增依赖，uv.lock 未改。

M2 UX-001 保留既有验收，UX-002 见下节收尾；UX-003 人工按示例提交记录仍缺，未关闭。M3 开始 AGENT-001 第一阶段接入准备，正式任务继续 in_progress；未进入真实 API/完整评测阶段。全部未完成项含 deferred 已复评，顺序/理由及剩余 P1 以 Backlog 为准；无新 P0 证据。

### UX-002 实际用户认可与上一轮 CI（非本轮重跑）

用户实际原话：“我体验了一下，感觉可以了，这个版本就比较清晰。我们来进行下一步吧。”核对 App 的只读 StarDetails 与显式 StarEditor 切换、components、App.results 测试及之前隔离浏览器证据，结合此次认可，满足 UX-002 当前范围验收。用户未报告亲测的全部异常、390px 与键盘边界不代填；自动化/历史浏览器和本人体验分开标记。IDEA-001 保留原话，Backlog 完成当前任务状态变更。

实际通过 GitHub 连接器复查 [上一轮 CI 39129060995](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39129060995)，关联提交 a455b17dcca8d6ed13055af83e4f51e3046b6150：backend Job 117680271393、frontend Job 117680271528 均 completed/success。读取日志确认普通后端 **55 passed / 1 skipped**、独立 PostgreSQL **1 passed in 0.17s**、前端 **82 passed**，以及迁移/schema、Ruff、前端格式/lint/typecheck/build 成功。这是 2026-10-18 上轮证据，本轮只是复查，不算本轮重跑；不证明 PG 回滚/并发、完整容器或真实模型通过。

### 实现与官方/锁版本核对

- 唯一新增设置 MODEL_PROVIDER，Literal 限定 openai-compatible / bailian，默认通用；原 Mock 默认及无 Key 日常回退保留。仅百炼 + qwen3.8-flash 传 extra_body.enable_thinking=false；不引入百炼 SDK、任意参数字典或额外 Host 设置。
- 适配器固定 `use_responses_api=False`，保持指定 tool_choice；拒绝普通文本、无调用、错误名称、多个调用，以及正常调用夹带 invalid_tool_calls。DTO 仍经 Pydantic，原文/来源覆盖与推测动机清除保留；数据库权限、审批二次约束、幂等和 Star 来源追溯仍沿原链路。
- last_usage 只白名单保留实际 SDK 的 input_tokens/output_tokens/total_tokens 非负整数，每次请求清空；无 usage 为 null，无估算。没有保存模型原始响应、headers 或隐藏推理。
- Live runner 不再强制 Settings(mock_mode=False)，需要显式 --allow-live，默认 --max-cases 1；本地预检 Key 非空/常见占位、非 Mock、模型名称、HTTPS /v1 URL（无凭据/查询串/fragment）、百炼北京专属域名/路径/示例替换、SDK retries=0。预检只判格式，不验证密钥有效性或实际地域权限。失败停止并非零退出，不补案例/升级模型；只处理公开 extraction，不导入 db/workflow 或审批。
- runner 报告记录实际案例数/模型/配置上限/失败类型/耗时/公开 DTO/SDK usage 或 null；未知异常只记 runner_error，不回显异常文本。报告 .cache/live-eval.json 被忽略且每轮覆盖，当前没有真实报告。正常 pytest、CI、lint、build、E2E 不运行 Live runner；入口测试使用 Fake Settings/Adapter，不是执行真实 --allow-live 命令。

实际安装及 uv.lock 相符：Python 3.12.15、langchain-openai **1.7.0**、langchain-core **1.6.9**、OpenAI **3.28.0**、httpx **0.28.1**；OpenAI 此版本用已有 httpx2 **2.13.1** 传输。读取本地 ChatOpenAI.bind_tools / _get_request_payload 实现：工具名转指定函数对象；max_tokens 转 max_completion_tokens。离线传输进一步验证最终 JSON 的 URL、model、工具列表、tool_choice、enable_thinking=false 顶层字段、max_completion_tokens=2048，没有 extra_body 外层或 max_tokens 残留；不只断言本地变量。

2026-10-25 实际浏览阿里云官方：[Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)（指定函数与非思考配置示例）、[OpenAI 兼容](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)（北京专属域名/地域 Key）、[Chat 参数](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)（enable_thinking、max_completion_tokens 支持 Flash 3.5 及之后）、[Qwen3.8-Flash](https://help.aliyun.com/zh/model-studio/qwen3-8-flash)（型号/北京 Function Calling）。官方参数依据与本地序列化不代表服务已连通。

### 实际离线检查与失败修复

环境：Windows PowerShell，仓库 D:/Projects/wonder-orbit，已有 .venv，不安装/升级依赖。后端命令使用 `./.venv/Scripts/python.exe`。前端在 frontend，通过当前进程 PATH 前置 `.tools/node/node_modules/node/bin` 使用 **Node 22.23.3**；系统 Node 16 不用于测试，未修改系统配置。npm 旧版 CLI 的 global/local 配置弃用提示存在，但检查成功。

| 检查 | 本轮实际命令 | 结果与限制 |
| --- | --- | --- |
| 专项离线模型/runner | `./.venv/Scripts/python.exe -m pytest backend/tests/test_qwen_adapter.py backend/tests/test_live_runner.py -q -rs` | 修复后 **48 passed**；真实 SDK + 内存传输及 Fake，非 Live |
| 后端最终完整回归 | `./.venv/Scripts/python.exe -m pytest -q -rs` | **103 passed / 1 skipped in 3.96s**；新增 48 项，包含全部既有审批/约束/幂等回归 |
| Ruff | `./.venv/Scripts/python.exe -m ruff check backend evals`；`./.venv/Scripts/python.exe -m ruff format --check backend evals` | 最终 passed；23 files already formatted |
| 前端格式/lint/类型 | frontend 下 `npm run format:check`、`npm run lint`、`npm run typecheck` | passed，无前端源码改动 |
| 前端测试 | `npm test` | **4 files / 82 passed**，34.35s；含 UX-002 查看/编辑/恢复既有回归 |
| 前端构建 | `npm run build` | passed；tsc -b + Vite，1581 modules，构建 14.34s；不当作性能比较 |
| 本机 PostgreSQL | pytest 中 test_postgres.py | skipped，未配置独立服务；不操作现有数据库 |
| 新浏览器 E2E / 完整 Docker / PG 回滚与并发 | 本轮未启动这些命令 | not run；无 UI/数据库结构变更，本轮风险由 SDK 内存/API 隔离回归覆盖；保留历史浏览器证据，不冒充重跑 |
| 真实 Qwen / Key 验证 / 免费额度 / Token / 真实 collect/explore / 审批目标环境 | 无 | **全部 not run，用户明确禁止**；不执行 evals/run_live.py --allow-live |

首轮专项为 **44 passed / 1 error**：统一禁止 socket.connect 拦截了 Windows TestClient/asyncio 的 loopback socketpair 自唤醒，引发未完整创建事件循环的清理警告。修复只允许 127.0.0.1/::1 的事件循环本机连接，仍禁止 DNS/create_connection/外网 connect/connect_ex；模型 HTTP 全走内存 MockTransport。补 SDK timeout、explore 指定工具、来源/动机回归后 48 passed；后续完整回归无该错误/警告。

首轮 Ruff 因 conftest 在禁用 .env 后才导入应用，触发 5 处 E402；使用明确的文件级 noqa 并说明安全初始化必须先于 app.db/app.main。随后修改测试断言触发 1 个格式差异，实际 ruff format 修正再重跑 check/format/full pytest 全通过；没有删除测试或降低业务断言。

专项覆盖：Qwen 型号/北京测试 Base URL、非思考参数、实际指定工具结构与输出上限、正常 DTO、未知原因/时间/预算/精力 null、非 Qwen/通用服务不传专用参数；缺/错/多工具、坏 JSON、合法夹坏调用、非法/多余参数失败；模拟 SDK 429/503/timeout 分类且只有一次传输；usage 缺失不估算/不沿用；原文/来源/动机防推测。隔离 API 确认非法输出不创建 Star/Quest、正常生成也不入档、显式批准才写且重复批准仍只有一条。runner 测试覆盖缺授权、非法数量、缺 Key/Mock/模型/URL/地域/示例 Host/重试不足预检拒绝、默认单案例/显式上限/失败停跑/报告脱敏及异常分类；全部 Fake、公开测试文本与 tmp_path。

### 安全与未触碰范围

未读取、打印、复制或覆盖当前 .env，未使用真实 Key/Host，未访问百炼推理 endpoint 或验证凭据。测试 conftest 在 app 导入前将 Settings.model_config.env_file=None，空 Key/Mock/隔离 URL，关闭 LangSmith tracing。SDK 测试只使用占位凭据，不记录 Authorization；没有上传测试产物、个人兴趣或运行隐藏推理。

个人 wonder.db 仅做文件 SHA-256 前后对照（未以 SQLite/ORM 打开）：均为 **168DBA7DA4099D3818191ED62A748EDC71189355F2EBFDEF8A64AE52CAAA8D62**。测试仅 tmp_path 下 test.db 与 .cache/test-import.db 配置；没有在个人库插入 Star/Quest，没有迁移个人库。未连接 Codex Cloud、部署/发布、启动日常后端/浏览器、实施 EVAL-001/Embedding/检索重构/MCP/多 Agent。

实际 `git check-ignore` 验证 .env、.env.local、.env.secret、.cache/qwen-offline-test.json、wonder.db、wonder.db-wal 被忽略；`git ls-files '.env*' '*.db' '*.sqlite*' '*.log*'` 仅返回 .env.example，示例只含公开值/空 Key。.gitignore 已足够，本轮未制造忽略规则变更。文档链接/锚点、任务状态一致性、源码 diff/敏感内容/修改范围与 git diff --check 的最终结果在本节交付核对追加；真实 CI 以该提交实际运行记录为准，不先写成功。

### 本轮三问复盘

- 为什么用户需要它？现有 Mock 只能演示固定规则，下一步需要可控地试真实模型；提前处理协议差异与单案例/零重试边界，避免第一次尝试就误跑全量或暴露凭据。
- 它在 AI Agent 系统中解决了什么问题？本轮是模型适配协议、结构结果的信任边界与评测入口成本控制；模型提交参数，受控后端校验，用户批准正式写入。UX-002 属 UI/UX 意图与工作流展示，本轮兼容准备也不等于模型理解/推荐质量提升。
- 我们通过这次开发学到了什么？OpenAI 兼容不保证参数完全通用，必须看锁定框架的最终 JSON；指定 tool_choice 要与思考模式协调，且一个有效调用可能夹着坏调用。SDK 能返回的 usage 才是可追溯用量，缺失不能当零；离线成功不能替代真实鉴权、额度、语义效果或审批目标环境证据。Windows 事件循环的本机 socket 自唤醒应和真实 HTTP 网络区分。

下一项建议仅为：用户在本地自行确认被忽略的 Key/北京 Host/模型配置并另行授权首次一个 collect 的真实请求；本轮完成后停止，不自动继续。

交付前最终核对：`.cache/agent001_phase1_doccheck.py`（被忽略的本轮检查器，不导入应用）实际检查 **306 处本地 Markdown 链接/锚点、28 个任务索引/详情状态、14 个唯一 IDEA ID**，均通过；未完成 P1 实际为 UX-003、INFRA-001、INFRA-002、AGENT-001、EVAL-001。15 个变更文件均在预期清单；仅扫描可提交文件的疑似 Key 与北京 Host，未发现真实凭据或非示例 Host。`git diff --check` 通过；`.env.example` / 文档 / 适配器 / runner / 两个新测试 / conftest 为本轮实际改动，无 .env、个人数据、产物、依赖或迁移混入。提交/推送前再次核对远程 main 与开始基线一致；后续普通推送和本提交实际 CI 结果在最终交付消息提供，不把尚未运行的 CI 预写为成功。


### 首次普通推送与实际 CI 失败（保留证据）

主实现提交 **a3958d12106a378747d5b0af2cd301b4c64b1e80**，Author/Committer 均为指定 YOLIIIIII GitHub noreply。实际普通 `git -c http.proxy=http://127.0.0.1:12450 push origin main` 成功，远程 main 同 SHA，未 force/改写历史，工作区当时干净。

[本轮首次 CI 40177809670](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/40177809670) 对应该提交，已实际读取 Job/日志：backend **121122202367 success**，迁移/schema/Ruff 成功，普通 **103 passed / 1 skipped in 2.93s**，独立 PostgreSQL **1 passed in 0.19s**；frontend **121122202476 failure**，格式/lint/类型通过、测试 **81 passed / 1 failed**，因此本次 frontend build 未执行，不能宣称整个 CI 成功。

失败为原有 App.results.test.tsx“多个候选各自使用 quest_id，导航不打开反馈也不重放审批”，第 402 行立即 toHaveFocus 观察到 body，而目标区域已渲染。源码中实际焦点由 busy 结束后的 useEffect 设置，idle 只等待处理中提示消失；这里存在观察时序窗口（源码/日志推断，不能凭一次本地通过断言所有环境稳定）。因此追加最小测试修正：仅将该断言改为 `await waitFor(() => expect(target).toHaveFocus())`，等待实际焦点到位，保留正确 ID、无弹窗、记录反馈按钮、两次审批及无反馈写入的所有断言；不改业务逻辑、不加固定 sleep、不删除断言或开启测试自动重试。UX-002 本人的验收保留，不把测试观察时序问题冒充新的功能交付。

修复后的实际本地重跑（Node 22.23.3，frontend）：再次执行 `npm run format:check`、`npm run lint`、`npm run typecheck`、`npm test`、`npm run build`，全部 passed；**82 passed / 4 files**，6.86s，Vite 1581 modules / 1.87s。不是只重跑失败案例。后端业务/测试/依赖自先前 103 passed 的版本后未改变，本次仅前端测试单行与文档，不冒称再次重跑后端。

追加修复后的范围核对：本轮相对原基线共 **16 个预期文件**（首实现 15 个，新增既有 frontend/src/App.results.test.tsx 单行等待修正），检查器按原基线至工作区核对，原始 Key/Host 扫描与 306 链接/28 任务/14 IDEA 一致性检查再次通过，git diff --check 通过。修复另作普通后续提交，不 amend/force，不把第一次失败改写成成功。后续提交/普通推送/CI 终态在最终报告给出，等待成功后才作交付结论。

<a id="agent-001-workflow-20261025"></a>

## 2026-10-25：AGENT-001 第二阶段工作流验证

### 用户已报告的 collect-only 证据（非本轮重跑）

来源为本轮用户附件：本人执行 `evals/run_live.py --allow-live --max-cases 1`，qwen3.8-flash，1 case，schema_valid，无错误，input_tokens=1037、output_tokens=223、total_tokens=1260、elapsed_ms=4860；用户观察免费额度 1M→998.74K。这是用户报告的实际结果，本轮不重跑该脚本，不冒称亲自联网复核。它只证明直接适配器 collect，不证明 FastAPI/LangGraph、explore/约束或审批链路。

上一轮最终提交 0e5846e78622748305263d96bc9d10b0819104a4 的 [CI 40178061446](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/40178061446) 已于上一轮实际核对成功：backend 103 passed / 1 skipped，独立 PG 1 passed，frontend 82 passed/build；这是上一轮远程证据，不属于本轮重跑。前一失败运行及焦点断言修正保留在上节。

### 本轮范围与开发前检查

用户授权本轮最多两次真实调用（collect/explore 各一次），失败/超时同样占次数；禁止重试/探针/批量/换模型/完整 EVAL/Embedding/MCP/多 Agent/部署。真实凭据只允许既有 Settings 运行时读取，不浏览或输出 .env，不调整模型请求代理。补充要求：提交前核对 .env 忽略、跟踪和暂存区敏感信息；疑似泄露停止推送。文档只追加本项目工程/实证，保留历史，不再扩写通用密钥知识。

开始工作区干净，分支 main；本地 HEAD 和通过临时 Git 代理 ls-remote 得到的远程 main 均为预期 0e5846e78622748305263d96bc9d10b0819104a4。仓库 local 姓名/邮箱符合指定身份。已按约定核对要求的文档、config/model_adapter/workflow/tools/main/schemas/db/retrieval、迁移、模型/审批测试、run_live/cases、示例/忽略规则。未浏览私有 .env 内容或历史私人业务数据。

### 安全入口与离线实现证据

新增 evals/run_workflow_live.py：缺 --allow-live 在 Settings 前拒绝；显式授权后固定百炼 qwen3.8-flash、非 Mock、零 SDK 重试并复用 validate_live_config。通过进程内 TestClient 调用原 API/图/工具，未启动网络服务。适配器 request 和实际 bind_tools.invoke 双重限制 collect→explore 各一次，invoke 前原子更新尝试报告，失败不补跑。没有生产 Schema/表/Prompt/权限或依赖变更。

临时库仅新建于仓库 .cache，拒绝复用文件/越界/符号链接，核验 app.db.engine 及 SessionLocal 实际绑定同一 SQLite 文件；调用既有 Alembic upgrade head，确认迁移版本与 Star/Quest/Reflection 初始零记录，任何异常均在模型前停止。临时环境、函数/工厂绑定在退出时恢复；个人 wonder.db 只做前后文件哈希。报告只保留公开测试文本/经校验 DTO、节点/工具事件、审批计数/ID、实际 usage/耗时，剔除真实 Key/Host，不保存原始服务错误或隐藏推理；日志/tracing 在专用运行期间禁用。测试批准明确标注 isolated_test_simulation，不冒充用户本人操作。

新增 test_workflow_live_runner.py 使用 Fake Chat + 实际 API/图/迁移，禁止 DNS/HTTP 连接，仅允许 Windows 事件循环 loopback 自唤醒；不读 .env，个人库 hash 函数在单元测试中替换为空值。覆盖完整双场景、零次拒绝/错误参数、实际 engine 错绑、旧库/非零初始库、调用顺序/第三次阻止、失败占额度/不补跑、错误/多个/缺工具、非法结构/未知字段编造、无候选/预算未知/错误引用/时间/精力/步骤约束拒绝、报告脱敏及环境恢复；既有 pytest 继续覆盖未批准工具/拒绝决策/异常分类/审计和幂等。

首轮新增专项 25 passed，出现 14 条已有 Alembic prepend_sys_path 路径分隔方式弃用提示；专用入口在其 Config 对象明确 path_separator=os 后复验消除提示，不改生产 alembic.ini。初始 Ruff 因 ROOT 赋值位于路径设置与应用导入之前触发 E402，移动 ROOT 定义到导入之后修正；未绕过规则。随后补 explore 超时停跑案例及实际节点/工具检查，最终命令与结果在下文追加。


### 本轮真实执行：一次 collect，严格语义检查失败后停止

所有必要离线测试通过后，实际只执行 **一次** `./.venv/Scripts/python.exe evals/run_workflow_live.py --allow-live`。没有执行旧 collect-only runner，没有模型探针、重试、余额 API 或第二次请求。进程退出码 1，脱敏报告 `.cache/qwen-workflow-hwngib7z/report.json`，实际库 `.cache/qwen-workflow-hwngib7z/workflow.db`；均被忽略且保留在本机。

实际配置：provider=bailian、model=qwen3.8-flash、北京专属地址（不记录完整 Host）、OpenAI 兼容 Chat Completions、指定 create_star_draft、enable_thinking=false、SDK max_retries=0、max_completion_tokens=2048、timeout=30s。凭据只由该进程 Settings 读取，未人工浏览、打印、复制 .env 或 Key；模型网络配置未改道。库在请求前已实际核验 app.db.engine/SessionLocal、Alembic 0001 和三项零计数，没有连接个人库。

| 项目 | 本轮真实结果 |
| --- | --- |
| 实际模型请求数 | **1 / 上限 2**，collect 一次，explore 未请求 |
| Tool Calling | 返回唯一 create_star_draft，无 invalid_tool_calls，DraftResult/Pydantic 通过 |
| Token（SDK 实际） | input=**1038**、output=**207**、total=**1245**；非估算，免费余额未查询 |
| 耗时 | 模型 invoke **10119ms**；API **10483ms**；AgentRun **10456ms**，测量边界不同 |
| API/Run | POST 201；run_id=**9129741a-5198-4726-8ad4-9617f13655b8**；mode=live、model_name=qwen3.8-flash、status=awaiting_decision、error_type=null |
| 节点 | understand_request → extract_star_draft → await_user_decision 均 succeeded |
| 工具 | create_star_draft succeeded；没有写工具或审批节点 |
| 公开原文 | 我一直想了解深海生物为什么会发光，想找时间记录三个感兴趣的问题。 |
| 原文与未知数值 | original_text 正确保留，source_type=paste、reference=null；estimated_minutes/budget/energy 均 null |
| 严格语义失败 | interest_reason 返回“**一直想了解深海生物为什么会发光**”，不是 null；runner 报 **collect_unknown_fields**，在测试批准前停止 |
| 正式记录 | 初始和停止后只读核对均 **Star=0、Quest=0、Reflection=0**；只存在 1 条待确认 AgentRun，无正式 star_id/quest_id |
| 场景 A 审批/幂等 | **not run**，严格语义检查未通过，不自动批准不合格草稿 |
| 场景 B 检索/图/候选/约束/审批/关联 | **not run**，A 未通过，因此不消耗第二次请求，不制造 Star 或候选 |

精确区分：服务/工具协议、结构和图的生成部分成功，**本轮整个 collect 验收及真实工作流闭环失败**。该 reason 是原文主题的逐字片段，并非新编造的外部个人经历；但本场景未明确给出“为什么感兴趣”，不能将“想了解什么”当作动机事实。现有 adapter 只清除不在原文中的 reason，子串条件不足以判定字段语义。本轮未弱化 null 检查、改 Prompt、替换该输出、批准它或用剩余次数重跑。后续需要独立决策如何区分主题与明确兴趣动机，离线回归优先；本轮没有宣称模型兼容故障或审批链已实际通过。

另观察到 category=未分类、tags=[]、description 为空，missing_fields 包含 available_minutes/budget 等请求字段名称，提问要求分类/标签/时间/精力。这些是当前公开响应的质量观察，不是额外业务验收通过或本轮已修复能力，不据单样本给质量统计。完整公开 DTO 保存在忽略报告中；文档只节选与失败有关的字段，不写隐藏推理/服务 headers。

进程返回后，只用 `sqlite3` 的 **mode=ro** 打开明确的隔离库，`PRAGMA database_list` 对照实际路径，查询三类正式记录和 AgentRun，核对上述零计数/运行状态；在忽略报告追加 post_stop_read_only_audit（additional_model_calls=0）。没有重启 Live runner、审批、改动测试数据或触及个人库。个人 wonder.db 只文件哈希：执行前后与只读审计后均 **168DBA7DA4099D3818191ED62A748EDC71189355F2EBFDEF8A64AE52CAAA8D62**；环境恢复检查 true。

基于本次失败，仅完善专用 runner 的异常退出计数落盘，并增加“原文主题复述为 reason”的离线回归；不修改生产适配层/Prompt/Schema。修改后的入口未再真实执行，因此不能把该新计数分支说成在本次 Live 已验证；本次正式计数证据来自上述只读审计。AGENT-001 保持 in_progress，EVAL-001、INFRA-001/002 不关闭。

### 本轮最终工程检查与复盘

环境为 Windows PowerShell / Python 3.12.15，已有 .venv；前端在 frontend 中临时 PATH 前置仓库 Node **22.23.3**，不改系统配置、不升级/新增依赖。后端命令均以 `./.venv/Scripts/python.exe` 执行；测试层禁用 .env/真实 Key/tracing，新增 runner 测试均为 Fake，不是再次真实运行。

| 检查 | 实际命令 | 本轮结果 |
| --- | --- | --- |
| 后端完整回归（含新增 28 项保护） | `./.venv/Scripts/python.exe -m pytest -q -rs` | 最终 **131 passed / 1 skipped in 16.53s**；本机无独立 PG，test_postgres skipped；包含本次主题/动机原文片段回归和失败退出计数 |
| Ruff | `./.venv/Scripts/python.exe -m ruff check backend evals`；`./.venv/Scripts/python.exe -m ruff format --check backend evals` | passed，25 files already formatted |
| 前端格式/lint/类型 | `npm run format:check`、`npm run lint`、`npm run typecheck` | passed，前端文件未改 |
| Vitest | `npm test` | **4 files / 82 passed**，55.83s；不作性能比较 |
| build | `npm run build` | passed，tsc -b + Vite，1581 modules / 15.99s |
| 真实工作流 runner | `./.venv/Scripts/python.exe evals/run_workflow_live.py --allow-live`（只执行一次） | **failed / 1 invoke**：工具/结构/图生成通过、collect_unknown_fields；不是真实闭环成功 |
| 停止后隔离库审计 | `.cache/qwen-workflow-hwngib7z/workflow.db`，sqlite mode=ro + PRAGMA 路径核对 | passed，正式三类记录零，1 awaiting_decision AgentRun，新增模型调用 0 |
| 真实 explore/审批/幂等/引用约束 | 未执行 | **not run**；collect 未满足严格语义，按授权边界停止，不补跑 |
| 真实 429/timeout/服务不可用 | 未人为制造 | **not run**；异常由 Fake/内存传输和失败审计离线回归，不额外耗 Token |
| 完整浏览器 E2E / Docker / PG 回滚并发 / EVAL 基线 | 未执行 | **not run**，不在本轮范围；CI 独立 PG 与本机缺服务分开记录 |

未启动公网或日常后端服务、未读取私人兴趣数据、未执行旧 collect-only runner、余额探针、自动重试、模型切换或额外 Live 请求，未连接 Codex Cloud/部署。个人库只哈希，.env 只由真实运行 Settings 使用，未浏览/打印/复制/修改；所有真实业务测试原本只允许进入新隔离库，本轮在批准前停止所以没有正式业务写入。

- 为什么用户需要这次改动／真实 Agent 工作流？直接适配器的 schema_valid 不能证明应用的图/审批安全与字段含义；专用入口把真实返回放进原工作流，能在正式写入前发现语义问题并留下可复核结果。
- 它在 AI Agent 系统中解决了什么问题／哪些边界取得实证？本轮实际取得 API→understand_request→extract_star_draft/create_star_draft→await_user_decision、指定唯一工具/Pydantic、未知数值空值、来源保留和批准前正式零记录证据；真实审批/explore 没有实证，Fake 的完整路径与真模型证据明确分开。
- 我们通过这次开发学到了什么？结构合法与字段语义正确是两层验证。兴趣主题的原文子串仍可能被填成“原因”；仅防止新增原文之外的内容并不保证字段语义。严格验收在批准前停下，比把剩余调用额度用来凑成功更能保护可信证据。没有据此宣称通用模型效果提升或兼容服务不可用。

当前 M3 仍为 AGENT-001 真实工作流验收中，无完整闭环结论；剩余 P1 五项/无新增已证实 P0 见 Backlog。下一项建议是针对“兴趣主题／明确动机”的离线对照与最小防护决策，另获授权后再采真实审批/explore 证据；本轮交付结束即停止，不启动 EVAL-001。

### 提交前文档、范围与暂存区安全核对

实际 `.cache/agent001_workflow_doccheck.py` 检查 **313 个本地 Markdown 链接/锚点、28 个任务索引/详情状态**，全部通过；相对基线仅 10 个预期文件改变（两个新 runner/测试文件及八个文档），无生产逻辑、依赖、Schema、迁移、前端或私人配置变化。`git diff --check` 与暂存区检查通过，远程 main 在提交前仍是预期 0e5846e78622748305263d96bc9d10b0819104a4。

按用户补充要求，在 commit/push 前实际执行 `git check-ignore --quiet .env`（成功）与 Git 跟踪文件名检查：.env 被忽略且未跟踪，未发现被跟踪的私人 .env 变体。只读取 Git 暂存区十个文件的版本进行 Key 签名、Authorization 凭据、私人北京 Host、非空示例 Key、私人/产物文件名检查；没有读取私人 .env。初次自检把 evals/README.md 的空 MODEL_API_KEY= 误判，已停止提交/推送并调查；逐行检查仅输出 value_empty=true，确认是正则 \s 跨行匹配下一项配置而非泄露，改为仅匹配行内空白后重新全量扫描，疑似敏感命中 **0**。未隐藏真实发现、未输出匹配值，也未以忽略规则绕过检查。安全扫描汇总在被忽略的 .cache/agent001_workflow_staged_safety.json；其结果不包含真实 Key/Host/headers。再次暂存文档后重扫通过才执行普通提交/推送；任何新疑似泄露仍须停止。提交、推送和实际 CI 结果在最终交付报告提供，不预先把 CI 记为通过。

<a id="agent-001-reason-20261025"></a>

## 2026-10-25：AGENT-001 兴趣主题与明确动机的离线语义修正

### 范围、基线与既有证据

来源：用户本轮明确字段契约和最小修正任务书。本轮 **实际 Live 请求数 0**；未运行 run_workflow_live.py --allow-live、collect-only runner、任何模型/密钥探针，不使用此前未消耗次数。所有模型响应是 Fake 或真实 SDK 的内存传输，未读取或修改私人 .env；个人 wonder.db 只做文件哈希，测试只用隔离临时库。

开始时工作区/暂存区干净，main、本地 HEAD 和远程 ls-remote 均为预期 **a9bfe7885b4b9c24e016700345fd7099ad25654e**。Git 仅对相关命令临时使用既有 127.0.0.1:12450 代理，没有修改全局配置。已按 AGENTS 核对 ROADMAP/Backlog/IDEA/历史 VERIFICATION/CHANGELOG、model_adapter/schemas/workflow/tools、API 决策落库位置、两个适配/runner 测试、run_workflow_live 与案例。重审未完成任务及 deferred，仍在 M3 AGENT-001 范围内，无新阶段/优先级调整，ROADMAP 保留历史而不机械改写。

上一轮真实 collect 的 **1245 Token / collect_unknown_fields** 是历史结果，不算本轮消耗或重跑。已通过 GitHub 连接器复查 [CI 40185466889](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/40185466889)，head_sha 为上述基线，completed/success；其 131 后端/82 前端/独立 PG 成功是上一轮证据，不冒充本轮测试。

### 根因、实现与字段边界

真正根因有两层：旧 Prompt 仅说“兴趣原因仅在原文明确提供时提取”，没有明确区分兴趣对象与个人动机；Pydantic 检查结构/类型，旧 adapter 只要求 reason 是原文子串，不能证明该子串回答了“为什么产生兴趣”。因此“想了解深海生物为什么发光”这个主题复述会被保留，虽非原文外编造，也不满足动机字段契约。

最小实现仅改 model_adapter.py：

1. 给 create_star_draft 的 SystemMessage 追加字段提示，说明个人动机的正例、主题/问题/活动/时间/科学因果/否定的反例与 null 规则。generate_quest_proposal 不收到此追加；既有室内文字探索限制、工具定义/指定名称、唯一调用/Pydantic 与错误分类不变。
2. 在 Pydantic 后、原文/来源覆盖之后调用 explicit_interest_reason。先保留原文子串要求，再要求模型原因完整对应同一句明确个人因果句的原因片段。有限支持 `我喜欢/好奇/对…感兴趣，因为/由于…`、`因为/由于…，所以/因此我…`、`…让我/使我对…产生兴趣`，可带列明的少量程度词。排除主题/目标式原因、否定/不确定/引述、原文外或改写证据；不自动编写新原因。保留的字符串仍来自原文。
3. 只规范 interest_reason 的 missing_fields：未知时出现一次，已知时移除；其他缺失字段名称/顺序、questions、category/tags/description、时间/预算/精力均保持原结果，不借此清理全部提取质量。

这是保守的小型句式规则，不是通用中文理解。复杂/跨句/隐含动机、改写文本、包含引号或否定的真实原因可能被漏掉；片段不完整也优先 null。用户仍可在原有草稿编辑中明确填写原因。没有增加第二个 LLM、联网校验器、模型成本、依赖、数据库字段或迁移。

字段链为：指定工具返回→Pydantic→adapter.draft 原文来源覆盖/原因标准化/该字段缺失信息→ToolRegistry 再验 DTO→AgentRun.state 待确认；正式 Star 仍只由原 decision API 在明确批准后写入。手动输入和用户编辑值仍走原 Schema/审批，不用该模型提取规则重新推断用户直接填写的动机。**正式 API/Schema/审批协议未变**，来源/真实 Star 引用/约束/幂等、Qwen 非思考和 Live runner 的调用上限/隔离检查均未改。

### 公开对照、类型与模拟工作流

新增 evals/interest_reason_cases.json（explicit-personal-motivation-v1），**30 个公开回归对照**，不是 EVAL-001 完整评测集或模型效果统计。包含用户十类要求及少量句式/证据边界；历史真实输入和错误 reason 不变，期望仍 null，未硬编码某个主题的生产答案。

| 输入/模型原因类别 | 期望与实际离线结果 |
| --- | --- |
| 深海为什么发光、宇宙起源、历史原文主题复述 | null，并补 interest_reason 缺失状态 |
| 我喜欢天文，因为小时候看过星空纪录片 | 保留“小时候看过星空纪录片”（或原文中的因果前缀版本） |
| 因为纪录片所以我对天文感兴趣；纪录片让我对天文产生兴趣 | 保留明确的纪录片经历原因 |
| 我之所以喜欢园艺，是因为外婆教过我照料花草；音乐让我心情平静的明确因果表达 | 保留原文明说的经历/感受 |
| 光合作用使植物生长、否定赚钱原因、不要猜测、计划完成活动/投入时间 | null，不把科学原因/否定/目标当个人动机 |
| 原文外经历、只取主题碎片、别人引述、不确定、跨句隐含或改写原因 | 保守 null，不补造事实 |
| 空/空白字符串、null、字段缺失 | null；不会因默认值变为已知原因 |
| 数字或对象类型 | invalid_model_output；保留 Pydantic 严格失败，不转成字符串 |

对照通过实际 ChatOpenAI/LangChain/OpenAI SDK + 内存 MockTransport，检查适配器最终 DTO/missing_fields，而不是只测正则或修改本地变量。每个合法对照还断言其他结构化字段、原文/来源和提问不变；专测 collect 提示范围、Mock 原行为、缺失状态增补/去重/移除。

两处隔离 API/实际 LangGraph 回归（分别为 SDK 内存和 Fake Chat）重放相同历史错误 reason，最终 draft.interest_reason=None，数值/精力未知仍 null，Run 仍 live 配置标签/awaiting_decision，批准前 Star/Quest 为空、decisions={}，只发生一次 Fake/内存 invoke，没有发送审批或 explore。live 标签是测试配置，不能据此称联网成功。

旧 runner 测试的 topic_as_reason 曾断言其触发失败；本轮将这一单项迁为明确的“清空原因且批准前零记录”回归，保留公开原文/错误输出/null 期望和 runner 原 unknown_fields 条件，没有删除语义要求或放宽 runner。其他工具/非法结构/预算等未知信息编造仍要求失败，完整既有 Fake 双场景/上限/隔离/审批回归继续运行，不是实际模型操作。

### 本轮实际检查

环境：Windows PowerShell，已有 Python 3.12.15/.venv 与 Node **22.23.3**；前端当前进程 PATH 前置项目 Node，无安装/升级。测试 conftest 在应用导入前禁用 .env、空 Key/Mock 与 tracing；SDK 专项禁止 DNS/HTTP，仅允许 Windows 事件循环本机自唤醒，响应全在内存。

| 检查 | 实际命令 | 本轮结果 |
| --- | --- | --- |
| 首轮专项 | `./.venv/Scripts/python.exe -m pytest backend/tests/test_qwen_adapter.py backend/tests/test_workflow_live_runner.py -q -rs` | **78 passed in 7.46s**；后续再增 2 个对照/2 个 Mock 检查，最终包含于下行完整回归 |
| 后端完整 | `./.venv/Scripts/python.exe -m pytest -q -rs` | **165 passed / 1 skipped in 14.90s**；PG 因本机无 TEST_POSTGRES_URL 跳过，不是 PG 通过 |
| Ruff | `./.venv/Scripts/python.exe -m ruff check backend evals`；`./.venv/Scripts/python.exe -m ruff format --check backend evals` | passed；25 files already formatted |
| 前端格式/lint/类型 | frontend 下 `npm run format:check`、`npm run lint`、`npm run typecheck` | passed；前端源码未修改 |
| 前端单测 | `npm test` | **4 files / 82 passed**，16.80s |
| 前端构建 | `npm run build` | passed，tsc -b + Vite，1581 modules / 2.03s；不作性能比较 |
| 真实模型/真实审批/真实 explore | 无命令 | **全部 not run，本轮实际请求 0**，不使用前轮剩余次数 |
| 新浏览器 E2E / Docker / PG 回滚并发 / 完整 EVAL | 未执行 | **not run**；本轮字段协议风险由 SDK 内存、隔离 API/图与全量回归覆盖，无 UI/DB/部署变更 |

本轮无失败测试，代码仅做实际 Ruff format 后检查通过，没有更改案例期望凑成功。没有新增依赖或评测框架，原 run_workflow_live.py 与 cases.json 的 guard/输入没有改变。个人 wonder.db 本轮仅文件 SHA-256 对照，未以 SQL/ORM 打开；安全/范围/暂存区检查在交付前追加，不读取 .env 内容。

### 其他质量观察与三问复盘

前次 category=未分类、tags=[]、description 为空是 Schema 合法默认，不等于整理质量充分；可能影响分类/标签查找或摘要展示，但原文仍保留，不能断言检索失效。其他 missing_fields 名称可能降低补充信息引导准确性。本轮不改这些内容，仅在既有 EVAL-001 记录候选观察，分别评价结构合法、字段语义可信、内容整理质量、产品可用性；EVAL-001 仍未正式开展，不建立虚构效果基线。

- 为什么用户需要这次改动？避免把“对什么好奇”显示或经批准保存成“为什么好奇”，同时让草稿明确暴露仍未知的原因，减少用户被看似有依据的字段误导。
- 它在 AI Agent 系统中解决了什么问题？在模型结构输出与待确认草稿之间增加字段级文本证据和语义边界；Prompt 引导生成、确定性规则保守守门、审批控制正式副作用，三者各有职责。不是 UI 文案优化或已证明的模型效果提升。
- 我们通过这次开发学到了什么？原文一致只能证明文本来源，不能证明字段角色；Pydantic 合法也不等于语义可信。对不确定个人事实选择 null 会漏掉一些隐含动机，但比自动补全事实更符合本项目契约，缺失字段也必须与规范化后的 DTO 同步。

AGENT-001 继续 in_progress，M3 真实工作流验收未完成；UX-001/002 与 UX-003 人工记录边界保留，剩余 P1 仍 UX-003、INFRA-001、INFRA-002、AGENT-001、EVAL-001，无新增已证实 P0。下一项仅建议在另获明确授权后验证修正后的真实 collect/审批/explore；本轮结束即停止，不执行该建议。

交付前最终核对：`.cache/agent001_reason_doccheck.py` 实际检查 **319 处本地 Markdown 链接/锚点、28 项任务索引/详情、30 个唯一对照 ID 与历史输入/错误 reason/null 期望**，全部通过；相对基线仅 **11 个预期文件**。git diff --check 和已暂存 diff 检查通过；schemas/workflow/tools/main/config、两个 Live runner、原 cases.json、前端、依赖/锁、忽略规则、迁移和 ROADMAP 均未改，未覆盖未知工作区修改。

个人 wonder.db 开始及结束 SHA-256 均为 **168DBA7DA4099D3818191ED62A748EDC71189355F2EBFDEF8A64AE52CAAA8D62**，未读取业务内容。提交前再次实际核验 .env 被 Git 忽略、未被跟踪且无私人 .env 变体被跟踪；仅扫描暂存区 11 个源码/测试/公开夹具/文档文件，Key 签名、Authorization 值、私人北京 Host、非空配置/私人文件检查均未发现疑似命中。没有读取/打印 .env；扫描汇总在被忽略的 .cache/agent001_reason_staged_safety.json。远程 main 提交前仍为预期 a9bfe7885b4b9c24e016700345fd7099ad25654e；文档补记再次暂存/扫描通过后，才按授权执行普通提交/推送。提交与实际 CI 终态在最终报告提供，不预写 CI 成功。


<a id="agent-001-live-recheck-20261101"></a>

## 2026-11-01：AGENT-001 最新语义代码真实 Collect → Explore 复验

### 基线、授权与执行前保护

用户本轮明确授权最多两次 Qwen3.8-Flash 请求（collect/explore 各一次），失败/超时也计数，禁止重试、探针、旧 runner、批量、换模型或其他云服务。本轮只执行一次现有 `./.venv/Scripts/python.exe evals/run_workflow_live.py --allow-live`，不修改源码、Prompt、固定输入、验收条件或保护规则。

开始工作区/暂存区干净，main、本地和通过 Git 临时代理 `-c http.proxy=http://127.0.0.1:12450 ls-remote origin refs/heads/main` 得到的远程均为预期 **8f940efe9158c1e406c558e519b4eb293491fc54**。读取 AGENTS、ROADMAP、Backlog、IDEA-005、最新 VERIFICATION 与相关源码；确认 draft 使用 explicit_interest_reason，unknown_fields 仍要求动机/时间/预算/精力全 null，collect 原文未改，双层 request/invoke 上限、零重试、失败停跑、路径/engine/SessionLocal/Alembic/零记录检查仍有效。.env 实际 check-ignore 成功且 ls-files 无跟踪，未浏览或输出明文。Key 仅该 runner 的 Settings 在运行时使用。

实际离线预检：`./.venv/Scripts/python.exe -m ruff check backend evals`、`./.venv/Scripts/python.exe -m ruff format --check backend evals` **passed / 25 files already formatted**；`./.venv/Scripts/python.exe -m pytest -q -rs` **165 passed / 1 skipped in 15.45s**，包含 30 项动机公开对照、历史错误清空、明确原因保留、missing_fields、真实 SDK 内存/Fake API/图、调用上限/失败占次数/停跑/无重试及库隔离回归。PG 因本机无 TEST_POSTGRES_URL skipped，不冒称通过。

本轮无源码/依赖变更，按用户范围不机械重跑前端 format/lint/typecheck/Vitest/build、浏览器 E2E 或完整应用全套环境；这些本机检查本轮 **not run**。上一轮 82 前端等记录仍是历史，推送触发的新 CI 另在最终报告核对，不用配置存在证明通过。

### 唯一一次 Live 执行与数据库核验

实际退出码 **0**、status=passed、adapter_requests=2、invoke=2。provider=bailian、model=qwen3.8-flash、北京地域（完整私人 Host 不记录）、Chat Completions、enable_thinking=false、max_retries=0、max_completion_tokens=2048、timeout=30s。没有额外请求、重试、余额查询、请求代理改道或其他云服务，免费额度扣减未查询/估算。

新库 `.cache/qwen-workflow-ck3r1ink/workflow.db`：请求前实际核验不存在/路径在项目 .cache、app.db.engine 与 SessionLocal 绑定同一文件，既有 Alembic upgrade head 版本 **0001**，Star/Quest/Reflection 初始全零。报告 `.cache/qwen-workflow-ck3r1ink/report.json` 保留公开 DTO/节点/工具/计数和 SDK usage，无 Key/Authorization/私人 Host/隐藏推理，均被忽略不提交。报告 SHA-256：**107b1e8ce5732b406831d43b1d875890438adf60ef201c8b00a6584f19e3d4c8**。

| 场景 | input/output/total Token（SDK 实际） | invoke / API / AgentRun 耗时 ms | 结果 |
| --- | --- | --- | --- |
| collect | 1178 / 160 / 1338 | 4136 / 4429 / 4408 | passed |
| explore | 1219 / 312 / 1531 | 4569 / 4688 / 4670 | passed |
| 合计 | **2397 / 472 / 2869** | 各测量边界不同，不作为性能基准 | 两次上限内，无失败 |

collect run_id=**41e24644-27ec-4097-b83d-bc7981ce869d**。真实模型原始工具参数中 interest_reason 就是 null，adapter 后仍 null；missing_fields=[interest_reason] 一致。历史公开原文与 paste/null 来源保留，estimated_minutes/estimated_budget/energy_level 均 null；唯一 create_star_draft、无 invalid_tool_calls、DraftResult/Pydantic 通过，API 201、mode=live、awaiting_decision。节点 understand_request→extract_star_draft→await_user_decision 与 create_star_draft 工具全部 succeeded，批准后 persist_approved_result succeeded。

explore run_id=**83200791-e774-47a3-8dc7-8d15f17dc7f4**。先只读检索确认命中刚创建的真实测试 Star，再实际图内检索/详情/偏好、唯一 generate_quest_proposal、ProposalResult/Pydantic、validate_quest_proposal 全部通过。节点 understand_request→retrieve_related_stars→load_preferences→generate_suggestions→validate_suggestions→await_user_decision；工具 search_stars、get_star_details、get_user_preferences、generate_quest_proposal、validate_quest_proposal 全部 succeeded。批准时再次读取偏好/校验约束，persist_approved_quest 与 persist_approved_result succeeded。

| 实际计数检查点 | Star | Quest | Reflection |
| --- | --- | --- | --- |
| 初始 / collect 批准前 | 0 | 0 | 0 |
| collect 批准 / 重复同一批准 | 1 | 0 | 0 |
| explore 批准前 | 1 | 0 | 0 |
| explore 批准 / 重复同一批准 / 退出 | 1 | 1 | 0 |

模拟测试决定 actor=isolated_test_simulation，均通过原 decision API，**不是用户本人审批**。Star ID=**d5c5fdad-e16d-4f3b-8e00-0019e5208c6c**；Quest ID=**afe9fdfe-756b-47f1-9c0b-f38cb962b68c**。两个场景重复相同决定返回相同结果/ID且计数不变，Quest 只关联该 Star，未写 Reflection、未声称用户已完成体验。

运行后仅以 sqlite mode=ro 打开这个明确隔离库，PRAGMA database_list 再核对实际路径，确认三类计数 1/1/0、QuestStar 一对正确 ID、两个 AgentRun 最终 decided 且各只有一个决定。独立只读审计保存在 `.cache/qwen-workflow-ck3r1ink/read-only-audit.json`，没有新增模型调用或修改业务数据。

### 实际公开结构化输出（仅测试数据）

以下为报告中模型通过 Pydantic 的公开输出，不含隐藏推理或 headers。collect 最终状态另由 adapter 再校验，此次原因本来就是 null：

```json
{
  "collect": {
    "draft": {
      "title": "深海生物发光",
      "original_text": "我一直想了解深海生物为什么会发光，想找时间记录三个感兴趣的问题。",
      "description": "用户希望了解深海生物发光的原因，并计划记录三个感兴趣的问题。",
      "category": "未分类",
      "tags": [
        "深海生物",
        "发光",
        "海洋"
      ],
      "interest_reason": null,
      "source_type": "paste",
      "source_reference": null,
      "estimated_minutes": null,
      "estimated_budget": null,
      "energy_level": null,
      "status": "collected"
    },
    "missing_fields": [
      "interest_reason"
    ],
    "questions": [
      "你为什么会想了解深海生物发光？是某个经历或内容触发了你的兴趣吗？",
      "你有大概可用的时间和预算来探索这个主题吗？"
    ]
  },
  "explore": {
    "proposals": [
      {
        "title": "深海生物发光：三问记录小体验",
        "description": "利用10分钟，围绕已有星星“深海生物发光”做一次室内文字思考：先读原始内容，再写下三个想进一步了解的问题，最后选出最想追问的一个并记录这次感受。全程免费、不外出、不购买。",
        "estimated_minutes": 10,
        "estimated_budget": 0.0,
        "energy_level": "low",
        "steps": [
          "读一遍这条星星的原始内容。",
          "写下三个你想进一步了解的问题。",
          "选出最想追问的一个，记录这次感受。"
        ],
        "based_on_star_ids": [
          "d5c5fdad-e16d-4f3b-8e00-0019e5208c6c"
        ],
        "rationale": "用户请求与星星均指向“深海生物发光的原因”，且星星原文写明计划记录三个感兴趣的问题；在低能量、10分钟、预算为0且仅室内的约束下，逐字采用给定模板步骤进行纯文字记录最合适。",
        "uncertainties": [
          "星星文本未提供具体的发光机制信息，只能基于问题记录展开，无法回答科学原因本身。",
          "用户希望记录的三个具体问题尚未写出，需由用户自行填写。",
          "10分钟是否足够完成三步取决于用户的书写速度。"
        ]
      }
    ],
    "questions": []
  }
}
```

### 质量、验收边界与复盘

本样本区分五层：两个指定唯一 Tool Calling 正确；Pydantic 结构正确；历史动机误填在本次真实返回中没有复现且原文/未知值符合契约；真实引用/时间≤10分钟/0预算/low/三个逐字模板步骤及批准时二次校验正确；**用户体验质量仍未由本次测试评定**。只有 1 collect + 1 explore，不构成高准确率、广泛兴趣覆盖或体验成功率。

仍有质量观察：category 仍未分类；本次 tags 有深海生物/发光/海洋，description 不再为空，但不能据两轮单样本宣称稳定提升。missing_fields 只列原因，未穷举其他未知数值；本轮只要求原因一致，不扩展契约。collect 追问时间/预算但仍成功留草稿；Explore 使用既有免费文字模板，能记录问题，未回答科学机制也未验证真实体验效果；不确定性已说明信息不足、问题待写与书写时长差异。上述关联既有 EVAL-001 候选，不改 Prompt、不硬造质量结论、不开展完整评测。

正式验收对照：真实 collect/explore 的指定工具/结构、真实 ID 引用、未知空值、生成前后批准边界、批准后二次约束和重复决定幂等均有本次实证；超时/限流/不可用/非法工具的分类与失败审计仍由本轮离线 Fake/内存测试证明，**真实故障未人为制造（not run）**。完成此单一服务的既定兼容/审批验收可收尾 AGENT-001，质量基线/更多样本归 EVAL-001，PG 回滚/容器仍归各自任务，不联动关闭。未改变源码/依赖/Schema/正式 API/Prompt/工具权限/runner 保护。

个人 wonder.db 仅前后文件哈希，均 **168DBA7DA4099D3818191ED62A748EDC71189355F2EBFDEF8A64AE52CAAA8D62**；没有读取、导入或写入其业务数据。environment_restored=true。未修改 .env、输出密钥/私人 Host、启动公网服务、连接 Codex Cloud 或部署；临时测试数据和报告仅留在 .cache，不发布。两次额度已用完，本轮不再发请求。

- 为什么用户需要它？验证刚修正的动机边界能进入真实应用闭环，且模型候选只有明确测试批准后才成为正式记录。
- 它在 AI Agent 系统中解决了什么问题？首次取得真实 FastAPI→LangGraph→指定工具/Pydantic→来源/约束→模拟 decision→Star/Quest 持久化与幂等的完整证据；不是仅适配器结构通过。
- 我们学到了什么？模型返回合法结果与后端可信执行是不同层；保守字段规则、确定性验证和审批事务需要一起验证。此次真实原始原因已为空，但单样本不足以区分 Prompt 与规则的总体贡献或宣称模型准确率。

本轮停止，下一项只建议另行规划 EVAL-001 的人工复核基线，不自动实施或追加真实调用。文档/暂存安全/提交/CI 的实际结果交付前核对，CI 终态在最终报告提供。

交付前检查：`.cache/agent001_recheck_doccheck.py` 检查 323 个本地 Markdown 链接/锚点、28 项任务索引/详情及历史 30 个对照/原文/null 期望，全部通过；仅 7 个预期文档变化，git diff --check/暂存 diff 通过。当前所有源码、Prompt、依赖和 runner 与执行基线一致。个人库结束哈希再次相同；.env check-ignore 成功且未跟踪，暂存区 Key 签名/Authorization 值/私人 Host/数据库/私人配置扫描疑似命中 0，无 .cache 产物混入，不读取 .env 内容。普通提交/推送前再次核对远程，作者/提交者使用指定 GitHub 身份；CI 实际终态在最终报告给出，不提前写通过。


<a id="eval-001-phase1-20261101"></a>

## 2026-11-01：EVAL-001 第一阶段质量规范与离线框架

基线：main/HEAD/远程均为 aa1c56e28cdac02b15c66da37561cf21de78f7d9，初始工作区/暂存区干净；按顺序读取 AGENTS、ROADMAP、Backlog、IDEA-005、最新实证、evals 与模型/Schema/工具/图及相关测试。AGENT-001 历史真实闭环通过保持不变。本轮仅评测方法和工具；EVAL-001 第一阶段交付，完整质量基线仍待验收，正式状态只在 Backlog。

交付：wonderorbit-quality-v1 的 Collect 7 项 / Explore 5 项人工 0/1/2 标准（逐分值依据、not_rated），与结构/保真/已知空值/来源/资源/审批确定性检查分开；wonderorbit-cases-v1 新增 10 个公开综合案例，原 3+7 个场景和 30 个动机对照未改。合计 50 个文件内案例条目（有主题/规则复用，不等于独立语义样本）。check_results.py 只依赖现有 DTO、规则常量与已安装 Pydantic，不新建框架/表/迁移/依赖。显式公开 JSON → 校验版本/类型/规则 → stdout JSON；不自动读取或转换私人历史报告，不保存输入到数据库。Fake/Mock/Live 证据标签分别报告，Live 标签仅表示调用者声明，不验证供应商来源。

实际环境：Windows PowerShell，项目 Python 3.12.15/.venv；最终前端使用项目已有 Node 22.23.3，PATH 仅当前进程前置 .tools/node/node_modules/node/bin，npm 缓存 .cache/npm；无安装/升级。

| 实际命令/检查 | 本轮结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q`（最终轮） | 209 passed / 1 skipped，25.83s；本机未配置 TEST_POSTGRES_URL，PG 跳过不是通过 |
| `.venv/Scripts/python.exe -m ruff check backend evals` | passed |
| `.venv/Scripts/python.exe -m ruff format --check backend evals` | passed，28 files |
| 前端 `npm run format:check` / `lint` / `typecheck` / `test` / `build`（Node 22 完整重跑） | 全部 passed；82 tests / 4 files；Vite 1581 modules，build 14.52s |
| `python evals/check_results.py --results evals/sample_fake_results.json` | exit 0；7 passed / 0 failed / 9 not_run / 1 not_rated；人工 0 rated / 60 not_rated；仅工具样例，非模型成绩 |

新增 44 项专项覆盖：正确结果、错误 Star ID、时间/预算/精力、未知事实/原文/来源编造、缺人工评分、非法 JSON/封装/输出字段、not_run 矛盾、重复/未知 ID、评分类型和备注、版本区分、Fake/Mock/Live 分类、无历史/不支持约束、合法但空泛输出、批准/拒绝/重复的外部观察。另以无数据库 lookup 替身对照已有 ToolRegistry 约束验证结果，防止离线时间/预算/引用规则漂移。

独立子进程 audit hook 实际阻断 socket/SQLite 事件、.env/.cache/数据库打开及 config/db/model_adapter/tools/workflow 导入，运行真实 CLI 样例通过；检查器没有网络调用/数据库/配置依赖。路径拒绝在打开前验证；错误报告不回显输入或原始 ValidationError。完整后端测试仍只使用隔离测试库、Fake/内存 SDK，未启动任何 Live runner。

失败与修正保留：首次专项 35 passed / 1 failed，原因是 pytest 临时目录在 .cache 内，CLI 路径保护正确拒绝；将 JSON 解析/退出码单元测试与路径策略测试分开，未放宽保护，最终专项全部通过。首次前端误用系统 Node 16：format/typecheck 通过，lint 因 structuredClone 缺失失败，Vitest/build 因 fs/promises.constants 缺失失败；随后使用仓库已有 Node 22 完整重跑，不更改业务或依赖。首轮完整后端 201 passed / 1 skipped，之后补评分严格类型及规则对照测试，最终完整重跑如表；不拿旧轮冒充本轮。

未执行：真实模型请求 **0**、Qwen Token **0**；未采集完整真实输出/人工质量基线、未优化 Prompt、未运行浏览器 E2E（无前端或生产流程变动）、未验证本机 PG 回滚/并发或完整容器。全部质量维度仍缺这一固定集的真实评分基线，历史 AGENT-001 单样本只证明既定兼容/闭环。工具的手写样例不是 Qwen 基线；人工未评分不等于 0 分，规则通过不等于体验优秀。

三问复盘：

- 为什么用户需要这次改动？已有真实闭环能运行，但用户还需要知道整理字段与探索建议是否准确、有用，才能有依据比较未来 Prompt/模型。
- 它在 AI Agent 系统中解决了什么问题？将 DTO 合法、来源/资源/审批安全与语义质量分开，用版本化公开案例和可复查结果减少“只看结构成功”的误判；这是 Agent 评价能力建设，不是 UI 改动或模型能力增强。
- 我们通过这次开发学到了什么？未分类/空摘要或泛化步骤可能合法而低价值；未知、未执行与人工观察不足必须分开。离线工具可证明检查方法工作，不能证明供应商输出质量，更不能从单次真实闭环推断总体效果。

当前 M3；无新增已证实 P0，未完成 P1：UX-003、INFRA-001、INFRA-002、EVAL-001。下一项仅建议另行授权后采集同版本公开输出并人工复核；本轮交付后停止，不执行真实质量测试。提交前链接/状态/范围/暂存安全检查与最终前端结果在交付前追加；提交/本次 CI 实际终态在最终报告给出，不提前记成功。

交付前实际检查追加：全仓 Markdown 本地链接/锚点 330 处、28 个任务索引/详情状态、14 个唯一 IDEA ID 均通过；案例条目 50（原 40 + 新 10）。暂存 12 个预期文件，无生产源码/依赖/前端/迁移或旧案例变更；git diff --check 通过。.env 被忽略且未跟踪；暂存文件 Key/Bearer 签名 0、非示例北京 Host 0，无 .env/.cache/数据库产物。没有读取私人配置或历史缓存，未覆盖初始未知改动（初始干净）。Node 22 最终前端全项通过见表；本提交 CI 将在普通推送后核对，最终报告给出，历史 CI 成功不替代本次。


<a id="ux-006-20261101"></a>

## 2026-11-01：UX-006 轻问候、自主入口与按需引导首页 MVP

基线：main/HEAD 69cf73bc3b8c3717b6628e40d75f8fef63b4bd4c，初始工作区/暂存区干净；GitHub 连接读取远程 main 一致。按顺序读取 AGENTS/ROADMAP/Backlog、IDEA-001/009/014 与最新 UX/AGENT/EVAL 实证，新增 IDEA-015/UX-006 并完整复评未完成任务（含 deferred）。本轮只修改前端首页、其组件/浏览器测试及相关文档，不改后端/审批/Prompt/依赖/表/迁移。

实现：三个入口始终可见，轻问候不问时间/预算/精力。homeHelpOpen 由用户点击展开/收起，切页收起；断连提示读不到档案；无正式 Star 建议收集；存在未归档项按 created_at 降序（同时间按 ID）选一颗，引用真实标题且按钮打开既有只读详情；仅归档提示收集或档案，由用户明确编辑状态。忽略会收起并恢复按钮焦点；不自动调用生成/批准、写入或恢复。原草稿/审批与探索流程保持，用户仍可从导航进入微型探索。

实际环境：Windows PowerShell / 项目 Python 3.12.15、Node 22.23.3（进程 PATH 前置 .tools/node/node_modules/node/bin），已有依赖未安装升级。所有后端测试为隔离库/Fake/内存 SDK，真实模型请求 0；未读 .env 或个人业务库内容。

| 本轮实际命令 | 结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q` | 209 passed / 1 skipped，8.02s；无 TEST_POSTGRES_URL，本机 PG 跳过不算通过 |
| `.venv/Scripts/python.exe -m ruff check backend evals` | passed（后端未改，额外回归） |
| `.venv/Scripts/python.exe -m ruff format --check backend evals` | passed，28 files |
| 前端 `npx prettier --write`（仅本轮四个前端文件）、`npm run format:check` / `lint` / `typecheck` / `test` / `build` | passed；84 tests / 4 files；1581 modules，build 1.96s |

状态测试覆盖：三入口/只读建议、collected/exploring、仅归档、零正式 Star、断连不误判、按保存时间而非修改时间/数组顺序、排除归档、忽略/重开/切页重置、所有建议操作无非 GET 请求；原 UX-001/002/003 组件及 AGENT-001 后端基础回归保留。

浏览器使用回环 Vite 5173→8000，新建 `.cache/ux006-e2e-final.db`，启动器先断言文件不存在、禁用 .env、强制 Mock/空 Key/关闭 tracing，运行 Alembic 并核对实际 engine.url.database；不使用个人库。一次性 Mock timeout fixture 仅隔离进程内用于既有失败恢复回归。产物留在忽略的 .cache/ux006-e2e-final。浏览器终态及交付安全检查在本节后追加。

失败/调整：第一次 Playwright 未设置已有浏览器目录，启动失败；设置 PLAYWRIGHT_BROWSERS_PATH=.cache/browsers 后无需安装。首轮浏览器因既有脚本仍查找首页旧“微型探索”按钮超时；同步剩余选择器后在全新隔离库重跑，不放宽审批/写入断言。不是应用生成失败。Git 默认代理 127.0.0.1:7897 不可达，命令级去代理的直连重试也连接失败；未改全局/仓库代理或启动外部服务，普通 push/CI 实际结果交付前记录。

未执行：真实模型/质量基线、人工主观满意度验收、本机 PG 回滚/并发与完整容器；本轮浏览器自动检查不冒称用户亲测。多轮引导式 Agent、通知、mascot 均未实现。

三问复盘：为什么用户需要？好奇允许搁置，有方向直接进入，无方向再要帮助，减少被要求完成任务的压力。它在 AI Agent 系统中解决什么？将建议触发权与执行/写入批准分开，展示真实来源、简单排序和只读入口；这是 UI/UX 与安全交互表达，未提升模型推理能力。我们学到什么？“主动一点”可以先由透明规则和可忽略建议实现，不需要强制对话；连接未知、无正式记录与归档必须分别处理，合法候选也不等于用户接受。

当前 M3、穿插 M2 首页体验；无已证实新增 P0，剩余 P1 为 UX-003（人工缺口）、INFRA-001/002（目标环境）、EVAL-001（真实基线）。下一项建议用户体验首页后反馈；本轮结束即停止，不继续开发多轮或通知。


浏览器最终实证：设置 PLAYWRIGHT_BROWSERS_PATH 为项目已有 .cache/browsers、E2E_ALLOW_WRITE=true、E2E_INJECTED_FAILURE=true、E2E_ARTIFACT_DIR=../.cache/ux006-e2e-final，执行 `npm run test:e2e` exit 0。三条 PASS：全部 Star 入口只读/编辑取消/服务器确认/失败恢复/归档保护；UX-002 结果定位/减少动画/恢复/精确 ID/无重复写入与真实 failed run 重试；收集→草稿批准→档案搜索→关联→候选批准→编辑→反馈→偏好确认→审计。两种尺寸 1440/390 的首页三按钮边界/不重叠及建议阅读检查通过，并实际查看“我的星屿-1440.png”和“我的星屿-390.png”，无裁切重叠。启动器/数据库/截图均留在忽略缓存，不加入 Git。


交付前检查：339 个本地 Markdown 链接/锚点、29 项任务索引/详情优先级及状态、15 个唯一 IDEA ID 一致；11 个预期文件，无后端/依赖/迁移或缓存变更。最终 `npm run format:check` 和 `git diff --check` 通过。.env 被忽略且未跟踪，变更文件 Key/Bearer/私钥签名扫描无命中；暂存仅上述源码/测试/文档，不含私人配置或数据库。指定身份创建本地提交；普通推送/CI 以最终报告实际结果为准，不提前写通过。UX-006 本地验收通过，远程交付仍待网络恢复，正式状态暂保留 in_progress。


远程交付实际结果：功能提交 `947315b8a3d663aadbfed666c4981a92a5a8bca7`，信息 `feat(ux): add guided home entry points`；Author/Committer 均为 YOLIIIIII <143058454+YOLIIIIII@users.noreply.github.com>。`git push origin main` exit 1（本地代理 127.0.0.1:7897 未监听）；命令级 `git -c http.proxy= -c https.proxy= -c http.version=HTTP/1.1 push origin main` exit 1（GitHub 443 连接 21s 超时），未变更代理配置、未强推。GitHub 连接查询此 SHA 的 Actions runs 返回 total_count=0，故本提交 CI 未触发/未执行，不是通过。远程仍为预期旧基线，UX-006 保留 in_progress，依赖网络恢复后普通推送并核对 CI。测试回环服务已停止，个人配置/数据库未改。补充此记录为独立文档提交；仅检查 Markdown/范围与 diff，不将此前应用测试冒称再次重跑。


<a id="eval-001-phase2-prep-20261101"></a>

## 2026-11-01：EVAL-001 第二阶段离线准备、UX-006 邀请入口与长期需求记录

### 基线、历史证据与范围

本地 main/HEAD 为 `ff8ae6c5bfcd012168080f81bb0e488872abf1f4`，初始工作区和暂存区干净。按 AGENTS 顺序读取 ROADMAP/Backlog、相关 IDEA 和最新实证，核对质量规范/固定集/检查器/两个 Live runner 与首页/测试/实际生成检索链路。GitHub 连接实际 GET 远程 main 一致；[历史运行 41296127363](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/41296127363) 对应相同 SHA，completed/success，backend/frontend 均 success。上一轮网络依赖已解除，这不是本轮测试或本轮 CI。

本轮明确只本地实现/离线测试，不 commit/push；真实模型请求 **0**。不读/输出 .env、Key、私人 Host 或私人历史模型报告，不访问个人业务库；不修改生产后端、Prompt、Agent 规则、Live runner、依赖、Schema/迁移。IDEA-016 只记候选，模糊故事游戏念头、邀请式入口反馈、小绿藻素材缺口已记录并去重；所有未完成任务含 deferred 完整复评见 Backlog。

### 实现与已知限制

UX-006：原三个 button 变为浅色紧凑邀请卡，标题/说明/图标/箭头、hover/active/focus-visible 与展开态，保留奶油白/紫/暖黄与星球、最近星星。可访问名称/说明由 aria-labelledby/describedby 关联；第三项仍由 aria-expanded 控制原规则区，明确只按保存时间，不声称个性或实时状态理解。原 collect/archive/只读详情/忽略/审批保持不变。

EVAL-001：没有新建评分器或重写人工规则。在 check_results 增加 `--prepare-captures`，互斥于原 --results，显式公开 JSON→严格封装/案例/版本/输入/偏好/检索快照/一一 ID 映射→stdout 既有结果封装（保留 capture 原始 DTO/ID/版本/观察层）→原检查器。只变合法 ProposalResult.based_on_star_ids 的精确元素，不改描述、依据、步骤等文本；重检核对归一化输出，拒绝证据漂移。错误 DTO 不修复，仍报告 failed；缺人工分为 not_rated，缺执行为 not_run。公开两条 Fake 自测样例复用旧手写测试内容、合成 UUID，绝非新 Qwen 输出或质量成绩。模式/版本为提交者声明，工具无法证明供应商来源或源码真实性。

源码确定的边界：run_live 是旧 extraction collect、run_workflow_live 是单深海闭环；都没有新固定案例完整元数据。本轮 workflow.generate 的 stars 包含 text/score/match_basis，固定质量快照则为 original_text 等，不能仅替换 UUID 或删字段说一致；严格准备入口拒绝不等价内容。仅未来明确 adapter_dto 层实际提供同一固定快照的结果可按本格式接入；workflow 固定集接入还需先另行定义/版本化实际检索上下文并离线核对，再授权采集，未在本轮实现。历史“未分类/机械描述/三问重复”只是探索性观察，未填入新集/人工分数。

### 本轮真实验证

Windows PowerShell / 项目 Python 3.12.15 与 Node 22.23.3，PATH 进程内前置 .tools/node/node_modules/node/bin；已有依赖未安装/升级。

| 实际命令/环境 | 本轮结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m ruff check backend evals` | passed |
| `.venv/Scripts/python.exe -m ruff format --check backend evals` | passed，28 files |
| `.venv/Scripts/python.exe -m pytest -q`（最终源码轮） | **239 passed / 1 skipped**，23.85s；无 TEST_POSTGRES_URL，本机 PG 跳过不算通过 |
| 前端仅变更文件 prettier --write；`npm run format:check` / `lint` / `typecheck` / `test` / `build` | 全部 passed；**85 tests / 4 files**，1581 modules，build 17.40s |
| `python -X utf8 evals/check_results.py --prepare-captures evals/sample_public_captures.json` → subprocess 捕获并 UTF-8 写入新建临时公开 JSON → 原 `--results` | 两阶段 exit 0；14 passed / 0 failed / 8 not_run / 2 not_rated；人工 0 rated / 60 not_rated；仅工具自测。临时公开 JSON 已移除，不进入交付 |
| 独立子进程 audit hook 禁 socket/SQLite、.env/.cache/数据库打开和运行时配置/模型/图导入，执行真实准备 CLI | passed；证明默认离线、无私人路径读取，非仅 mock 函数断言 |
| `npm run test:e2e`，E2E_BASE_URL=http://127.0.0.1:5176 | exit 0；隔离库 Mock 完整双尺寸回归，下述证据 |

最终新增 30 项后端专项回归（既有 44 → 74）：输入/来源/偏好/检索快照差异、UUID 映射缺失/重复/错误来源、重复案例、版本不匹配、非法/缺失 DTO、未知人工维度或分值、not_run、转换后原始证据保留/漂移、CLI 路径保护与独立进程离线边界。没有重建原人工评分规则。前端新增邀请卡可访问标题/说明与规则透明断言，原状态/导航/审批回归保留。

浏览器：新建 `.cache/eval002-ux006-polish.db`，启动器先断言文件不存在、禁用 .env、强制 Mock/空 Key、关 tracing，运行 Alembic 并核对实际 engine.url.database。回环 Vite 5176→8026，不复用已有 5173/8000 服务；一次性 timeout fixture 仅隔离测试进程。PLAYWRIGHT_BROWSERS_PATH=.cache/browsers，E2E_ALLOW_WRITE=true，E2E_INJECTED_FAILURE=true，产物 .cache/eval002-ux006-polish。1440/390px 邀请入口边界/不重叠、Tab→焦点可见→Enter 展开、建议只读详情/忽略及整个入口段请求监听（无非 GET，包括无生成 POST）通过；原收集/批准/搜索/关联/探索/反馈/偏好/审计、结果定位/恢复/精确 ID/失败重试/只读编辑回归三条 PASS。实际查看桌面首页与移动展开建议截图，标题/说明可读、焦点框清楚、未裁切，最近星星仍可找到；不称人工主观满意度或用户本人验收。

失败/重跑保留：首轮后端专项 70 passed/1 failed，独立子进程中文 stdout 使用 Windows 默认编码，父进程按 UTF-8 解码失败；为该子进程显式 -X utf8，不改业务/保护。随后专项 71 passed；补预算 bool/来源/空白版本边界后完整最终如表。首轮全后端 236 passed/1 skipped，最终 239 passed/1 skipped，不以首轮冒称最终。本轮前端完整链与 E2E 无失败。纯文档收尾不冒称再跑应用测试。

未执行：真实 Qwen、真实固定集基线/人工评分、AGENT-004 模板改进、workflow 固定集自动采集/导出、本机 PG 回滚/并发/完整容器、本轮远程 CI、commit/push。未授权远程交付不是网络阻塞；历史 CI success 不作为本轮源码成绩。EVAL-001 仍 in_progress；UX-006 原首页基础认可/历史 CI 已有证据，新邀请视觉仍待用户体验，保留 in_progress。

### 三问复盘与下一步

- 为什么用户需要？用户知道自己想靠近什么时能自主进入，没方向时可轻点求助或搁置；邀请式说明减少工具面板感。将来质量改进也需要公开、可核对的输入输出，避免只凭“能生成”判断有用。
- 在 AI Agent 系统解决什么？首页是 UX 表达，没有增强模型能力；离线准备则补足评测证据的案例/版本/上下文/ID 对应与保真，保留人工未知，防止将不同兴趣上下文或不同 DTO 层混成基线。
- 学到了什么？UUID 对照不足以证明同一来源，生成实际看到的检索内容也必须相同；安全可执行与探索价值仍是两回事。渐进陪伴需要未来有历史和继续意图的证据，本轮只记录，不用邀请文案包装成长期 Agent。

当前 M3，穿插 M2 体验；无新增已证实 P0。剩余 P1：UX-003、INFRA-001/002、EVAL-001、UX-006。下一步先体验邀请入口并 review 本地差异；若要推进真实质量基线，先确定 adapter/workflow 观察层及检索快照版本，再独立明确采集范围/额度。未授权不调用、不提交、不推送。


交付前实际收尾：349 个本地 Markdown 链接/锚点、29 项任务索引/详情和 16 个唯一 IDEA ID 一致；15 个预期文件（含新增公开 Fake capture 样例），git diff --check 通过。变更文件密钥/Bearer/私钥签名扫描无命中，.env 被忽略且未跟踪；暂存区为空，HEAD 仍 ff8ae6c，无 commit/push。生产后端、依赖、Live runner、迁移未改；仅本轮 5176/8026 且命令行匹配本轮启动器的测试服务已停止，未操作已有其他服务。纯文档收尾只复核链接/任务/范围，不重复宣称运行应用测试。


<a id="ux-006-tint-docs-20261101"></a>

## 2026-11-01：UX-006 淡底色微调与产品/工程文档一致性（合并未提交批次）

开始先执行 `git status --short`、`git diff --stat`：14 个已修改文件 + 未跟踪公开 Fake capture 样例，共 15 个现存未提交文件，与上一轮一致；HEAD 为 ff8ae6c。将这 15 个文件的开始 SHA256 写到忽略缓存作保留核对，不 reset/clean/stash，不覆盖或重建上一轮源码。顺序读取 AGENTS/ROADMAP/Backlog、近期 IDEA/验证与相关样式/浏览器检查，复评记录追加到 Backlog；沿用 UX-006/IDEA-015/016，无新任务或提级。

本轮增量：styles.css 仅将三张邀请卡设为淡薰衣草紫 #f4eefb、暖奶油黄 #fbf5e5、浅紫粉 #f8eff5，分别配低饱和边框/hover/active 底色，hover/focus 增加轻阴影，第二张图标用暖金；保留 3px 可见焦点框。尺寸、布局、标题说明、插画/最近星星与原导航/规则建议/审批不变，App.tsx 本轮未改。smoke.mjs 在原回归上补双尺寸底色区分、hover/按下反馈、Space/Tab/Enter 及焦点框断言，保留入口段无非 GET 请求与原主流程检查。

文档仅更新 README、ROADMAP、Backlog、IDEA_LOG、CHANGELOG 和本验证记录：统一“星屿不是 To-do List，念头可搁置/重新拾起，有方向自主选、无方向按需引导，AI 建议由用户决定”；README 保留全部技术/安装/能力说明，新增已实现与长期候选边界；ROADMAP 顶部改为 M3 穿插 M2，AGENT-001 既定真实闭环已验收，EVAL-001 无固定真实质量基线，INFRA-001/002 完整环境待验收；旧失败/阶段/排序保留且标历史语境。Backlog 旧基线与旧推荐顺序加日期语境，任务状态不变；IDEA-015 追加最新浅底色反馈、IDEA-016 补历史经历找方向，未新增 IDEA。小绿藻正式形象和渐进/个性化接续继续候选，未写成已实现。

### 本轮实际检查

| 检查 | 实际结果 |
| --- | --- |
| 前端 `npx prettier --write src/styles.css e2e/smoke.mjs`、`npm run format:check` / `lint` / `typecheck` / `test` / `build` | 全部 passed；85 tests / 4 files，1581 modules，build 4.74s；Node 22.23.3，进程 PATH 使用项目已有工具，未升级依赖 |
| `npm run test:e2e` | exit 0；1440/390px 的三卡底色、hover、按下/展开、Space 收起、Tab/Enter、焦点框、无额外写请求检查通过；原收集/草稿审批/搜索/探索/反馈/偏好/审计、只读详情/编辑/失败恢复等三条 PASS |
| 视觉核对 | 实际查看 .cache/ux006-tint-docs/我的星屿-1440.png 与 我的星屿-390.png；浅底色可分辨，无裁切/重叠，尺寸和留白仍稳定，不称用户本人验收 |

浏览器仅使用新建隔离 `.cache/ux006-tint-docs.db`，启动前断言不存在、Alembic 初始化、核对实际 engine.url.database，关闭 .env 读取、强制 Mock/空 Key/关闭 tracing，一次性 timeout fixture 只在本轮隔离进程。E2E_BASE_URL=http://127.0.0.1:5176，代理到回环 8026；PLAYWRIGHT_BROWSERS_PATH=.cache/browsers，E2E_ALLOW_WRITE/E2E_INJECTED_FAILURE=true，产物在忽略缓存 .cache/ux006-tint-docs。未访问个人业务库。

未执行后端 pytest/Ruff：本轮只改 CSS、浏览器检查和文档，未变更上一轮 EVAL 源码/测试/样例或生产后端，依用户本轮最小充分验证要求保留上一轮 239 passed/1 skipped 与 Ruff 结论，**不是本轮重跑**。本轮真实模型请求 0，未读取 .env/Key/私人 Host 或私人模型历史缓存，未新增迁移/依赖/大需求。远程 CI 不重跑；历史 41296127363 success 只属于 ff8ae6c 旧首页基线。当前邀请卡、EVAL 离线准备和本轮整理仍未 commit/push，暂存区未操作。

三问复盘：用户需要更易察觉的温柔入口，并能从文档看清项目为何存在及哪些能力可用；本轮解决的是 UI 可发现性、Agent 建议/用户决定边界和工程事实的一致表达，不是模型能力增强。学到的是可以用低饱和底色加强可点击性，同时用有日期的历史上下文保留失败证据；产品愿景和真实验证必须分开。

当前仍 M3 穿插 M2；AGENT-001 保持 done，EVAL-001/UX-006 保持 in_progress（新视觉待用户检查），UX-003 人工缺口、INFRA-001/002 环境验收保留，无新增 P0。下一步建议用户检查合并工作区后另行确认统一提交/推送；本轮停止，不自动执行。


收尾实证：353 个本地 Markdown 链接/锚点、29 项任务索引/详情、16 个唯一 IDEA ID 一致，git diff --check 通过。相对开始 SHA256 清单，本轮只追加修改 8 个授权文件（六份文档 + styles.css/smoke.mjs）；此前 15 个未提交文件均保留，EVAL 源码/测试/公开样例、App.tsx/App.test.tsx、evals README/项目导航与开始内容逐字节相同。四份产品文档定位/候选边界、指定任务状态检查通过。密钥/Bearer/私钥签名扫描无命中，.env 仍被忽略且未跟踪，暂存区为空、HEAD 保持 ff8ae6c；本轮 5176/8026 测试服务按端口及本轮启动命令核对后已停止，不影响其他服务。

<a id="eval-001-phase3-a-20261101"></a>

## 2026-11-01：EVAL-001 第三阶段 A（离线准备，真实请求 0）与 UX-006 收尾

开始实测 HEAD=bee5596d7bb0ea0a199af7ba9722ddded25e81a8，工作区干净；按 AGENTS→ROADMAP/Backlog→IDEA-005/015/近期 VERIFICATION 核对历史证据。用户本次任务书的新范围/反馈追加至 IDEA_LOG，全部未完成项含 deferred 的复评见 Backlog；本轮不启动 AGENT-004、生产 Prompt/规则/Schema、首页或依赖改动，不 commit/push，不连接云或发布。

新增 evals/collect_quality.py 与 backend/tests/test_quality_collector.py；原 check_results 仅增加可选 failure_type（封闭脱敏类别）与 sampling 旁证，失败不得伪装成合法输出，不放宽案例/版本/快照/映射检查。默认只输出公开计划，无 Settings/适配器/数据库运行时导入；真实开关之后才读现有 Settings 并执行既有预检。固定三个案例、直接 adapter_dto；完整公开快照、展开默认值的实际适配器参数、模型实际 payload、合成 ID 一一映射、源码哈希/Git SHA 与 dirty 标记保留。现有适配器会做 Pydantic 和动机规则处理，本观察层不能区分所有未经防护的原始模型错误；后续人工分析必须承认此边界。

真实批次目录独占创建，不复用/恢复；request 前 fsync 尝试计数和 attempted_unknown、usage=unknown，最多三次且每例一次，零 SDK retries，失败即停。实际合法 DTO 原值保留，非法结构无 DTO 时不重建输出。中断记录 elapsed_ms=null/usage=unknown，后续可人工审核后导出 interrupted_unknown；不猜测零消耗。隔离日志默认 public_data=false；只有显式人工已审核声明的导出才写 public_data=true，且导出拒绝 fake/mock、上下文/映射/版本/实际 payload 漂移和覆盖目标。公开导出→既有 --prepare-captures→--results，人工缺分保持 not_rated，审批未观察、不推断或伪造计数。没有自动上传。

### 本轮实际检查（Windows / 项目现有 Python 3.12 .venv）

| 命令/检查 | 最终结果与边界 |
| --- | --- |
| `.venv/Scripts/ruff.exe check backend evals` | passed；All checks passed |
| `.venv/Scripts/ruff.exe format --check backend evals` | passed；30 files already formatted |
| `.venv/Scripts/python.exe -m pytest -q -rs` | 268 passed / 1 skipped，15.24s；跳过 test_postgres 因未配置独立 TEST_POSTGRES_URL，不声称 PG 通过 |
| 默认 `.venv/Scripts/python.exe -X utf8 evals/collect_quality.py` | exit 0；mode=offline、requests=0、三例顺序准确；没有真实批次目录或公开输出文件 |
| 原 checker `--prepare-captures evals/sample_public_captures.json`、`--results evals/sample_fake_results.json` | 均 exit 0；仅 Fake 工具自测，非 Qwen 质量报告。完整准备→检查与失败类别/旁证保真在新增 pytest 中覆盖 |
| GitHub 连接器 fetch_workflow_run_jobs：YOLIIIIII/wonder-orbit，41301902392 | backend job 124834414738、frontend job 124834414893 均 completed/success；后端迁移/schema/Ruff/pytest/独立 PG、前端格式/lint/type/test/build 步骤均 success。这是已推送 bee5596 的历史 CI，本轮未触发新 CI |

新增 29 项采集保护用例。SDK Fake 客户端走实际适配器/解析，测试模型调用参数固定、三例次数/顺序/每例第二次请求拒绝、每个位置超时/非法结构即停、unknown usage、请求前日志、固定集哈希漂移、错误模型/Mock/空 Key/非零重试拒绝、输入/偏好/快照/映射/版本/model_payload 差异拒绝、Fake 标记拒绝作为真实导出、原始 DTO 保留及缺评分 not_rated。两种独立子进程 audit hook：默认 CLI 禁配置/模型/图导入与私人 .env/.cache/DB/网络访问；模拟真实分支使用显式测试 Settings/Fake Timeout，禁个人配置/数据库/SQLAlchemy/图导入、DB 打开和网络，报告不含测试 Key/Host/原错误。所有 Fake 结果只在 pytest 隔离临时目录，无真实提供商证据产物。

开发中首轮测试文件有一个括号语法错误，修复后两项断言误按案例数组位置查找 Explore（suite 顺序并非本批顺序），改为 case_id 精确查找；没有放宽生产检查。最终全量结果如上，260/266 项为中途迭代结果，非最终结果。

未执行：真实模型请求/Token 采集/真实 DTO 内容评分/阶段 B/公开真实导出；实际真实请求数 **0**，无本批真实 usage 可以汇报。前端未修改，按用户本轮范围不重跑 lint/typecheck/test/build、视觉/E2E，使用上述真实历史证据评估 UX-006，明确不是本轮应用测试。未运行新 PG/完整容器检查，无个人数据库访问、无 .env 原文/Key/私人 Host 读取或保存；Settings 私有读取分支本轮未执行。

### UX-006 验收依据与复盘

用户本次明确报告已查看新版邀请卡并接受阶段成果，且 bee5596 已推送；本轮核对指定 CI 双 Job success。既有全项前后端回归、1440/390px 隔离浏览器/键盘/状态/无额外写请求记录见本文件 eval-001-phase2-prep-20261101、ux-006-tint-docs-20261101；未当作本轮重跑。由这些已有工程证据和新增实际用户接受反馈，现有 MVP 验收缺口已补齐，正式状态在 Backlog 收尾；整体视觉提升仍归 UI-001/002，不强行扩展当前范围。

为什么用户需要这次改动：建立可复核的小样本真实质量证据入口，未来讨论整理和探索价值时有同一输入可对照，而非凭历史印象或漂亮文字下结论。它在 Agent 系统中解决什么：隔离适配器内容质量与工作流/审批证据，固定上下文与预算，防止中断漏计、Fake/缺评分冒充质量结论；属于评测工程能力，不是本轮模型能力增强。学到了什么：工作流检索项与质量快照不是同一格式；直接传完整公开快照才可保持一致；结构合法、动机防护后的 DTO 和真正值得尝试的内容是不同证据，后续人工判断不能由确定性通过代替。首页收尾仅为 UI/UX 阶段接受，不提供模型效果证据。

当前 M3 穿插 M2，M1 已交付，M2/M3 整体未完成。无新增已证实 P0；剩余 P1 为 UX-003、INFRA-001/002、EVAL-001，EVAL-001 尚无完整正式质量基线。下一项推荐为审阅本轮差异后单独确认 B 的固定脚本/额度；本轮按用户明确两阶段要求停止，不自动真实请求或提交推送。

交付前文档/范围实测：360 个本地 Markdown 链接/锚点通过，29 项任务索引/详情状态一致；本轮仅 10 个预期文件（evals/collect_quality.py、backend/tests/test_quality_collector.py、evals/check_results.py、evals/README.md、docs/IDEA_LOG.md、docs/PRODUCT_BACKLOG.md、docs/PROJECT_GUIDE.md、docs/VERIFICATION.md、ROADMAP.md、CHANGELOG.md）。git diff --check 通过，变更文件密钥/Bearer/私钥签名扫描无命中；真实批次目录和公开导出不存在，暂存区为空、HEAD 仍为 bee5596。最后只追加文档记录，不宣称又重跑了应用测试。

<a id="eval-001-hash-fix-20261101"></a>

## 2026-11-01：EVAL-001 固定案例 CRLF/LF 跨平台 CI 修复

开始 HEAD=87e86fc3f17667c4fbad0265bf61e4fbc0ceca12，工作区干净；既有 local Git 身份核对为 YOLIIIIII <143058454+YOLIIIIII@users.noreply.github.com>。读取约定、路线图、Backlog 和相关 IDEA/实证后，沿用 IDEA-005/EVAL-001，仅修复采集器版本校验，不改变产品/模型/审批/数据库/前端。当前 M3、M2 体验阶段边界不变，未完成项复评见 Backlog；无新 P0，P1 仍为 UX-003、INFRA-001/002、EVAL-001。

失败历史：[Actions 41303909059](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/41303909059) 属于上述提交。经 GitHub 连接器实际核对 backend job 124840302418 failure、frontend job 124840302560 success；后端 Ruff/迁移/schema 步骤成功、pytest 失败、后续独立 PG 步骤 skipped。读取 backend job 日志并提取最终 23 个失败测试 ID：均来自 test_quality_collector.py，23 failed / 245 passed / 1 skipped，根因 fixed_suite_changed。没有将此前 Windows 本地 268 passed 当作该次远程通过。

根因实测：本地公开 quality_cases.json 有 286 个 CRLF，原始字节 SHA256=e08d9c85346d4678a8ed60eeb2f5718033691c52ea86996eade7a637732df79f；仅 CRLF→LF 后 SHA256=f4e90c1783d0cf4168f5f833ac2e87d5e2b29aebb990e95fb74392337488dea4。旧常量绑定 Windows 换行字节，Linux LF 因而误报案例变化。没有修改真实案例文件或语义。

修复：仅新增 suite_hash(path)，read_bytes().replace(CRLF, LF) 后 SHA256；SUITE_HASH 更新为上述 LF 值。plan、采样 source_hashes 的固定案例项及 export_reviewed 的当前文件校验共用它；retrieval_version 对应该规范化值，记录 suite_hash_normalization=crlf-to-lf。file_hash 不变，其他源码保留实际字节哈希；不做 JSON 重排、空白折叠、孤立 CR 转换或全项目静默规范化，不关闭版本保护。调整旧漂移测试至 suite_hash，原失败断言保留；新增四项换行等价、LF/CRLF 采样到导出一致性、实质内容修改拒绝测试。内部实现变化，不改变模块职责/调用链/启动方式，无需重写 PROJECT_GUIDE。

### 本轮实际验证（Windows / 现有 Python 3.12 .venv）

| 实际命令/检查 | 结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest backend/tests/test_quality_collector.py -q --junitxml=.cache/hash-fix-targeted.xml` | 33 passed，8.04s |
| `.venv/Scripts/python.exe -m pytest -q -rs` | 272 passed / 1 skipped，30.74s；唯一 skipped 因未配置独立 TEST_POSTGRES_URL，不宣称本轮 PG 通过 |
| `.venv/Scripts/ruff.exe check backend evals` | passed，All checks passed |
| `.venv/Scripts/ruff.exe format --check backend evals` | passed，30 files already formatted |
| `.venv/Scripts/python.exe -X utf8 evals/collect_quality.py`，subprocess 解析 stdout | exit 0，mode=offline、requests=0，固定三例；没有执行真实开关 |
| 隔离公开源码副本：仅将副本 quality_cases.json 明确写为 LF，使用原 .venv 运行同一专项命令，JUnit `.cache/hash-fix-lf.xml` | 33 passed，14.97s；这是 Windows 上的 LF 文件验证，不能称 Linux CI 重跑成功 |
| 远程原失败 ID 与上述两份 JUnit 逐项比对 | 主工作区与 LF 副本均为原 23/23 标识 passed，无删除/跳过断言 |

辅助 LF 副本最初从归档获取时仍带 CRLF，因此只在副本显式转换案例文件；放在 .cache 下时，默认 CLI 的原审计 hook 正确拒读缓存路径（32 passed / 1 failed），随后把验证副本放到项目内独立临时位置完成 33 passed，没有放宽审计保护。完成后将该公开副本移至忽略目录 .cache/hash-fix-lf-verified 保留证据。真实项目案例、既有 .cache/quality-baseline-v1 均未删除、重置或改写。

未执行：真实 Qwen/API、真实采样或公开导出；实际真实请求 **0**，没有本批真实 Token 数据。所有采样分支测试使用 Fake/显式测试配置与隔离临时目录，未读取私人 .env/Key/Host 或个人库。前端未改，本轮不重跑前端/视觉/E2E；未跑完整容器或新远程 CI。既有旧 CRLF 哈希记录不自动迁移、不改写成新版本；如果存在，保留原件，本次不为它们删除批次目录或重采样。

为什么用户需要：相同公开案例应能在 Windows 开发与 Linux CI 使用同一版本标识，恢复离线验收可信度。Agent 系统解决的问题：修复评测来源校验的跨平台稳定性，保证采样与导出一致且实质修改仍被阻止；属于评测基础设施可靠性，不是模型探索能力提升。学到什么：内容版本与文件换行字节需明确区分，固定案例可以使用限定的规范化，其他源码证据仍应保留真实字节；跨平台假设要用 LF/CRLF 输入和完整链路验证。

本轮只授权一次本地修复提交（fix(evals): normalize fixed suite hash across platforms），不推送、不改历史。下一项由用户在 PowerShell 推送后查看新 CI；在新运行实际成功前不能宣称远程修复已验收，EVAL-001 保持 in_progress，阶段 B 仍需独立确认。

交付前实测：363 个本地 Markdown 链接/锚点通过，修改范围仅七个预期文件；无新增未跟踪交付文件，git diff --check 通过，变更文件密钥/Bearer/私钥签名扫描无命中。上述最后检查为文档/范围检查，不冒称又重跑应用测试。

<a id="eval-001-first-baseline-20261106"></a>

## 2026-11-06：EVAL-001 第一批真实质量基线整理与反馈归档（本地、部分证据）

本轮开始 git status --short 为空，HEAD=e0afb6277ac0160683e17915408bf6176218c2f0，与用户给出的基线一致；按约定核对 ROADMAP/Backlog、IDEA-005/006/近期验证。全程离线，无 GitHub/模型/其他网络查询。用户此前已亲自执行阶段 B，本轮只读取指定 .cache/quality-baseline-v1/raw.json，不读取其他历史缓存、.env、私人配置或个人库；未删除/覆盖/重建采样目录。本轮不 commit/push，不改生产代码/Prompt/规则/审批/数据库/前端/固定案例。

### 原始审核与可公开条件

原始文件 SHA256（开始与结束核对）：89eeb9c71de5458a00fab39b39a788a6b8913482bcfd68827b2a4c6755815bdb。format_version=private-quality-sampling-v1，public_data=false；采集 SHA=e0afb6277ac0160683e17915408bf6176218c2f0，working_tree_dirty=false；started_at=2026-11-01T12:09:43.462147+00:00（北京时间2026-11-01 20:09:43.462147）。审核/归档日期为2026-11-06，不把它当作采样日期。用户报告采集程序 exit 0；raw 本身没有进程退出码字段，未补造该元数据。

- 模型/模式：bailian / qwen3.8-flash / live；三条 observation_layer=adapter_dto。workflow_version=not_executed:adapter_dto，workflow_executed=false，approval_observation=not_observed:adapter_only；不能称完整 Workflow 或审批基线。
- 案例 wonderorbit-cases-v1；rubric wonderorbit-quality-v1。Prompt/adapter SHA256=78b3474336ab7c9a46b8106c97ff213c5d2a2ac1a457dfad0be5397959efe7e9；固定公开快照 SHA256=f4e90c1783d0cf4168f5f833ac2e87d5e2b29aebb990e95fb74392337488dea4，suite_hash_normalization=crlf-to-lf。raw.source_hashes 的适配器/DTO/规则/采集器/预检/案例/规范/检查器 **8/8** 与当前文件按规定算法一致，所有实际哈希保留在公开 capture 文件顶层 sampling.source_hashes 旁证中，不倒推或编造生成版本。
- attempted_requests=3、max_requests=3、sdk_retries=0、max_output_tokens=2048、timeout_seconds=30、enable_thinking=false；顺序与三例固定计划一致，均 schema_valid，无失败或中断条目。
- 逐字段核对 capture.input/preferences/retrieved_stars/id_map 与固定计划一致；adapter_inputs 为实际展开默认值后的参数，model_payload 与其完全对应。Explore 的 request.text=“深海发光”，Star 原文“我对深海生物发光很好奇”，保留 title/original_text/category/tags 全字段；偏好输入{}，展开默认约束为空，effective_limits={minutes:10,budget:0,energy:low}，constraint_template=null。未将 workflow 的另一种检索格式改名混用。
- 合成UUID 00000000-0000-4000-8000-000000000001 → public-star-ocean，一一对应且内容完整；属于测试公开快照映射，绝非实际数据库记录。

| 案例 | 原始状态 | input_tokens | output_tokens | total_tokens | elapsed_ms |
| --- | --- | ---: | ---: | ---: | ---: |
| explicit-motivation | schema_valid | 1173 | 159 | 1332 | 3601 |
| unknown-motivation | schema_valid | 1171 | 196 | 1367 | 2926 |
| grounded-explore | schema_valid | 1082 | 423 | 1505 | 8904 |

累计输入3426、输出778、总4204 Token，均来自 raw 的 SDK usage，逐项与用户任务书一致；本批已有三次真实请求，**本轮整理新增0次**。不据此推算服务账单或总体性能。

公开审核先检查字段集合和潜在密钥/Authorization/Bearer/私人Host/数据库连接/隐藏推理/URL/邮箱/手机号签名，再人工阅读三个DTO、全部实际输入/模型payload及元数据。仅发现固定公开兴趣文字、合成ID及其生成建议，无个人档案/配置/原始服务错误或不应公开的文本。三条DTO与用户任务书所列字段、标题、步骤、动机/预算/缺失字段和问题描述一致。任务书未附此前完整DTO的逐字副本，因此不声称独立证明与未附历史消息逐字节相同；本次以只读原报告的完整合法DTO为证据，未发现无法解释的不一致，符合本次公开导出条件。扫描本身不等于隐私保证，本次已补充实际内容审核；数据仅本地导出，未上传。

### 实际离线流程和结果

使用 Python subprocess 捕获 stdout/检查退出码，以 UTF-8 新文件方式保存；不会覆盖既有文件。三个 CLI 均安装独立子进程 audit hook，禁止 socket/sqlite 访问及导入 app.config/model_adapter/db/main/workflow，未执行真实开关。

| 命令/检查 | 本轮实际结果 |
| --- | --- |
| `.venv/Scripts/python.exe -X utf8 evals/collect_quality.py --export-reviewed-public` | exit 0，已审核公开 capture 新建成功 |
| `.venv/Scripts/python.exe -X utf8 evals/check_results.py --prepare-captures evals/reviewed_quality_captures.json` | exit 0；输出保存 reviewed_quality_results.json；仅 formal manual 填入已确认用户分，其余显式 not_rated |
| `.venv/Scripts/python.exe -X utf8 evals/check_results.py --results evals/reviewed_quality_results.json` | **exit 1（预期真实发现）**，stdout 保存 reviewed_quality_report.json |
| `.venv/Scripts/python.exe -m pytest backend/tests/test_offline_evals.py backend/tests/test_quality_collector.py -q -rs` | **107 passed，8.91s**；全部离线/Fake，非模型重采样 |

三个新文件：[公开capture](../evals/reviewed_quality_captures.json)、[正式结果](../evals/reviewed_quality_results.json)、[确定性报告](../evals/reviewed_quality_report.json)。raw_output 原值完整保留，只有规范化 output 的 based_on_star_ids 元素转为公开ID；原文/rationale/步骤不改。原报告public_data=false未变，导出文件public_data=true为本次人工审核声明。离线报告证据类型仍为 supplied_live_output_unverified，工具无法独立认证供应商来源，不把离线核对夸大为重新调用服务。

确定性计数：20 passed / 1 failed / 7 not_run / 3 not_rated（单位为检查项，非成功率）。explicit-motivation 的唯一失败是 estimated_budget：原始0.0，固定期望null；不得改为null以过评测。其余Schema/原文来源/明确动机/时间未知/精力未知/原因缺失一致性通过。unknown-motivation 的既有确定性项全部通过，未知动机保持null；这不能证明整理充分。grounded-explore 的Schema、非空建议、检索ID、时间/预算/精力和现有约束项通过；“标题三分钟而步骤合计/estimated_minutes八分钟”不在现有检查器覆盖范围，记录为人工可核对的文本一致性问题，未虚构程序失败。

其余七例 multiple-topics、source-organization、unknown-resources、empty-history、unsupported-constraint、vague-but-legal、approval-lifecycle 为not_run，未补造输出。三条已执行案例的approval_boundary均not_rated；模型说法不能代替审批观察。

### 用户评分、助手候选与真实反馈

机器可读正式manual中仅 grounded-explore.exploration_value=1：来源为用户亲自选择的评价选项，由本次任务书明确映射既有rubric。note保存来源和依据。用户原话：“有一点趣味，但没有真正帮我理解深海发光。”补充：“就针对当前这个问题来说，我感觉还是有点不太符合我的预期，特别是第三点‘选择一个猜想，给它取一个比喻性的名字’，让我觉得很没有必要。”不改写成满意或全无价值，不伪称用户评价其他维度或已实际完成活动。原反馈时点未给出，2026-11-06是本次归档来源日期。

以下是**助手候选评分，未获用户最终确认，不写入正式manual数值**；仅用来解释草案。三例共19个维度，除上述1项外其余18项正式保留not_rated；全10例报告为1 rated / 59 not_rated。没有整体总分/合格率，not_rated不是0。

| Collect维度 | explicit-motivation 候选分/理由 | unknown-motivation 候选分/理由 |
| --- | --- | --- |
| topic | 2：保留天文兴趣与明确来源动机 | 2：保留深海生物发光主题和问题 |
| title | 1：“天文”可识别但较宽，未突出好奇点 | 2：“深海生物发光原因”概括具体科学问题 |
| category | 1：未分类，对归档帮助有限 | 1：未分类，对归档帮助有限 |
| tags | 1：仅“天文”，部分有用但粒度宽 | 2：深海生物/发光/海洋生物学与主题有依据 |
| description | 0：空字符串未组织或表达兴趣 | 0：空字符串未组织或表达兴趣 |
| motivation | 2：保留明确原文个人动机 | 2：未知动机保持null，与主题问题区分 |
| clarification | 1：问题具体但询问时间/精力，预算无依据填0且未提示缺口 | 1：missing_fields仅动机，问题却扩展至时间/精力；收藏场景可能产生任务压力 |

| Explore维度 | 候选分 | 理由与确认情况 |
| --- | ---: | --- |
| relevance | 1 | 主题相关，但用户期待知识理解，建议走想象/比喻；助手候选，用户未逐项确认 |
| feasibility | 1 | 数值满足上限，但标题三分钟与步骤合计/estimated_minutes八分钟不一致；助手候选 |
| steps | 2 | 动作、对象、记录产出具体；第三步必要性不足计入探索价值，助手候选 |
| uncertainty | 2 | 指出来源不足、目标未明和活动限制；助手候选 |
| exploration_value | 1 | 有一定趣味而知识收获不足，比喻命名被认为不必要；已确认用户反馈映射，正式唯一评分 |

### 问题归因与未来方向（本轮不实施）

结构/确定性：Collect未知预算误写0.0是可复核空值问题；Explore三分钟/八分钟的矛盾是真实内容一致性问题，后者现有checker未覆盖。兴趣整理：两条description为空、category均未分类；Schema允许这些值，不能把合法等同充分整理。时间/精力追问可能把“先收藏”变成安排任务的压力，尚无本批强制阻断行为证据，不说已证明阻止保存。

探索体验：具体动作不等于有意义的收获，比喻命名对当前用户理解深海发光的帮助不足。Explore固定请求仅“深海发光”，Star仅说好奇，**未明确指令学习科学机制**；不能把独立Collect科学问题当成这次Explore已经传入的学习目标，也不能断言模型违反明确学习指令。建议在uncertainties承认目标不明，却仍选创意方向且未提澄清问题；反映系统未充分区分期望收获，不能简单归因模型“拒绝科普”。

源码中的安全Prompt限定仅依据已有文字、室内思考/记录、不联网/购买/假定设备；本批Star无科学知识材料，模型理由也明确援引这一限制。这是对当前科学知识型探索的明显能力边界；可以解释选择范围，但单批同Prompt结果不能分离模型本身与Prompt的因果贡献，未做对照，不保证换模型/改Prompt即可改善。adapter_dto又包含既有Pydantic/动机防护，不能从最终未知动机null反推未经防护的原始模型从未猜测。

AGENT-004候选优先方向：先定义“学到知识/动手体验/创意表达”等期望收获，意图不明提供少量清楚标识的方向或可跳过的轻量澄清，避免强制对话；每步应与收获有可解释联系，比喻命名不作默认必选项；在来源和安全边界明确后再设计有依据的知识小探索。先比较手动选方向/查看记录的简单替代，不提前改生产Prompt/规则或引入检索依赖。若需明确科学学习目标的新例，记为未来案例版本候选，不修改 wonderorbit-cases-v1 或本批输入，尚无新调用额度。AGENT-004状态仅在Backlog保持proposed。

为什么用户需要：把实际不符合预期的建议变成可追溯质量证据，避免修掉失败数字后失去改进依据。Agent系统解决的问题：将结构/约束检查、适配器防护、内容价值和用户期望分开观察；这是评测和产品学习，不是本轮模型能力提升。学到了什么：原文和动机保真可以与整理空泛并存，安全可执行也可能学不到知识；后续改进要先区分收获方向并承认上下文歧义，不能由少量结构合法输出推断总体优秀。

必要验证范围为既有离线检查器/相关107项测试和公开JSON/文档一致性；未修改应用源码或依赖，不重跑完整后端/前端/视觉/E2E，不把历史测试说成本轮重跑。未执行新的模型/网络/工作流/审批、完整容器/PG验证或CI查询。原始证据字段完整，已展示的任务书摘要均可核对；历史完整DTO消息与采集进程退出码的独立记录未附，只按上述来源界定，不补造。

当前M3穿插M2，M1已交付、M2/M3仍未全部完成；无新增已证实P0，剩余P1为UX-003、INFRA-001/002、EVAL-001。本轮交付首批部分adapter证据；EVAL-001完整正式基线、其余七例/审批/其余人工评分仍未完成。下一项建议用户复核助手候选评分并讨论AGENT-004收获方向，未授权不新增调用/实施/提交推送。此前失败CI/测试记录均保留，未声称远程已验证。


交付前实际检查：原始SHA256仍为89eeb9c71de5458a00fab39b39a788a6b8913482bcfd68827b2a4c6755815bdb；三份公开JSON逐条核对capture与原报告完全相同、正式manual仅一项用户分、report与evaluate(results)完全一致。374个本地Markdown链接/锚点、29项任务索引/详情一致，公开JSON敏感签名/URL扫描无命中，git diff --check通过。范围为新建三个公开JSON，更新VERIFICATION/PRODUCT_BACKLOG/IDEA_LOG/evals README/CHANGELOG/ROADMAP六份文档，共九个文件；应用/检查器/案例源码未改，暂存区为空、HEAD保持e0afb62，无commit/push或上传。

公开产物SHA256：reviewed_quality_captures.json=4bc5f0576eaa5c8400bfba1428de416e7ce788258bc69fdc1bb8ab768267d4be；reviewed_quality_results.json=dc4a1aab7a56c111942d2f18c0eaa6c95e47b76af0ad5ceeeb84844753d5436f；reviewed_quality_report.json=47eaa93337af56266d3553ec184c07123eb818fce8d1040f9095861b495b84db。最后仅追加本段文档记录，未冒称重跑应用测试。


<a id="agent-004-a-20261106"></a>
## 2026-11-06 · AGENT-004-A 显式期望收获（离线）

授权与起点：工作区初始干净，HEAD=733747719009e3176c4cf0e5f5ef24fc0752c662，与用户给定 SHA 一致；本轮没有远程 CI 查询/新 CI 运行，不将用户提供的 CI 链接当成本轮结果。不 commit/push/云连接/发布。沿用 IDEA-006 / AGENT-004，正式状态仅 Backlog 维护；EVAL-001 整体仍待验收。

实现：可选四状态原生 radio，默认还没想好，切换仅本地 state，方向不会变成偏好。枚举字段 exploration_direction；Collect 非空方向 422。wrap serializer 仅省略新增空方向，旧默认字段和嵌套 payload 保持，旧 Run 无字段显示还没想好。main/workflow 原链直接保存与恢复 request，无新工作流/迁移/Quest 或 Reflection 结构改动。方向专属策略仅用于明确 Explore；生成/确定性校验分离，支持约束按所选有限步骤逐字验证，不支持约束继续澄清，不用关键词评判探索价值。

Mock（AGENT-004-A offline-v1）：knowledge 整理用户已提供信息、一个待核实问题、检索词及来源核实方向；不输出科学机制。hands_on 只用已有 Star 文字选两个词、排序比较并记录观察，是实际文字小尝试，明确不是设备/实物实验。creative 自愿构思短文或设计点子，并标明不代表科学结论。未选沿用原三个好奇问题步骤。所有候选有 Mock 标识、真实检索 Star 引用和估计不确定性；这些证明契约，不证明语义质量。

环境与安全：Windows / 项目现有 Python 3.12 .venv、Node 22.23.3，未安装或升级依赖。pytest fixture 禁用 .env/Key、隔离 SQLite；内存 SDK fixture 禁止网络，只用 fake-test/test-placeholder。所有新增真实 Qwen 请求数 **0**，未执行真实开关、探针或真实模型。独立浏览器启动器 `.cache/agent004a_server.py` 启动前断言新库不存在、禁用 .env、Mock=true/空 Key/tracing=false，Alembic 初始化并核对实际 engine URL 指向 `.cache/agent004a-e2e.db`，回环 5173→8000；只对该隔离库做模拟审批。专用进程中一次 timeout 注入仅为原恢复回归。

实际命令与结果（最终补充见下段）：

- `.venv/Scripts/ruff.exe check backend evals` 与 `format --check backend evals` 通过；初次完整 pytest 为 285 passed / 1 skipped，后因增加离线 SDK 策略检查重跑，最终结果下补。
- 前端以进程 PATH 前置 `.tools/node/node_modules/node/bin` 执行 `npm run format:check`、`lint`、`typecheck`、`test`、`build` 全部通过；89 tests / 4 files，build 1581 modules。初次误用系统 Node 16：lint 因 structuredClone 缺失、Vite/test 因 fs/promises.constants 缺失失败；此失败为环境问题，切到已有 Node 22 后重跑通过。后续仅新增 E2E 脚本和收紧选项排版，格式/lint/build 最终检查下补，不重复声称组件测试重跑。
- `npm run test:e2e`（E2E_ALLOW_WRITE=true / E2E_INJECTED_FAILURE=true / PLAYWRIGHT_BROWSERS_PATH=.cache/browsers）exit 0：原收集→草稿批准→搜索/关联→候选批准→编辑→反馈→偏好→审计、Star 只读/编辑失败恢复/归档保护、结果定位/刷新恢复和真实模拟失败重试三条 PASS。1440/390 原生 Space/方向键四状态、焦点、标签边界和切换无 API 写请求通过。截图已实际查看，知识说明无弹窗，页面无横向溢出；新增方向结果/刷新专项与最终视觉下补。
- `.venv/Scripts/python.exe -X utf8 evals/check_results.py --results evals/reviewed_quality_results.json`：原检查器复现历史报告，stdout 另存 `.cache/agent004a-historical-report.json`，**预期 exit 1** 是既有未知预算误填的真实失败，不是本轮 CI 结果；测试 evaluate(results)==归档 report 通过。历史确定性 20 passed / 1 failed / 7 not_run / 3 not_rated；人工 1 rated / 59 not_rated，未补评分。
- 三份归档 JSON SHA256 与上轮记录完全一致：captures=4bc5f0576eaa5c8400bfba1428de416e7ce788258bc69fdc1bb8ab768267d4be；results=dc4a1aab7a56c111942d2f18c0eaa6c95e47b76af0ad5ceeeb84844753d5436f；report=47eaa93337af56266d3553ec184c07123eb818fce8d1040f9095861b495b84db。cases-v1 / quality-v1 及其检查器未修改。

限制与复盘：用户需要先表达希望得到什么，避免把好奇变成 Agent 布置的无关练习。Agent 改进是显式意图进入生成契约且可追溯；radio 与布局是 UX 工程价值，不能说模型已更懂科学。我们从真实反馈学到原请求歧义与能力边界需要分别解决，安全、可执行、结构合法不等于有学习价值。此次没有知识资料或外部核验，不能保证直接给出科学答案；hands_on 仍局限文字，不假设设备。AGENT-004 的可信材料学习、更丰富实际尝试、逐模板用户评价及真实质量效果尚未验收；Collect 整理独立保留，未同时修。未执行真实模型/PG/完整容器/远程 CI，不把历史成绩说成本轮重跑。当前 M3 穿插 M2，无新增已证实 P0；剩余 P1 为 UX-003、INFRA-001/002、EVAL-001。下一切片建议用户提供可信材料的有出处学习路径，等待独立授权。


最终补充（2026-11-06，同轮）：

- 增加内存 SDK SystemMessage 四状态检查后，最终 `.venv/Scripts/python.exe -m pytest -q -rs`：**289 passed / 1 skipped，19.64s**；唯一跳过 test_postgres，未配置 TEST_POSTGRES_URL。Ruff check / format check 均通过，31 files。新增专项 13 项及 SDK 4 项全部离线。
- 前端最终 CSS 调整为选项横向图文排列后，format:check / lint / build 再次通过，build 1581 modules；TS/组件逻辑未再变，typecheck 与 89 项测试结果来自前述本轮执行，不虚构再次重跑。新增方向 E2E 最终格式/lint 也通过。
- 专项通过 `.cache/agent004a_directions.mjs` 调用正式 `frontend/e2e/directions.mjs`：**exit 0**，四方向 × 1440/390 的真实表单 payload、Mock 候选标题、Run API/state、刷新后点击最新运行并核对具体 run_id 和方向、无 Quest/偏好新增均通过。原 smoke 全链与此专项分开执行；最终 smoke 已接入专项，未再对同库冒称从空库全跑。专项前两类失败是脚本遗漏刷新后选择运行，以及手机上等待隐藏的桌面模式标记 visible；已分别改为点击运行并核对 ID、等待模式标记 attached（API run.mode 另核验为 mock）。这些失败不计通过，应用持久化未因此修改。
- 最终实际查看 `direction-result-knowledge-390.png` 与 `direction-result-hands_on-1440.png`，两尺寸图文无裁切/重叠，知识说明与待核实问题清楚，动手结果明确限定文字尝试。图像/临时启动器/隔离库留在忽略的 `.cache/agent004a-e2e` 等缓存中。旧记录不是本轮重跑。
- 再用 subprocess 捕获原检查器，确认返回码确为 1 且 stdout JSON 与归档 report 完全一致；三份 JSON 实际字节 SHA256 不变，固定案例和 rubric 与 HEAD 规范换行后内容一致，检查器源码未改。
- 文档检查：377 个本地链接/锚点、29 项任务索引/详情状态一致、16 个 IDEA ID 唯一；git diff --check 通过。最终范围和安全检查见下。

本轮文件清单（18 个；仅项目内）：backend/app/{schemas.py,model_adapter.py,rules.py,tools.py}；backend/tests/{test_exploration_direction.py（新增）,test_qwen_adapter.py}；frontend/src/{App.tsx,types.ts,styles.css,App.test.tsx}；frontend/e2e/{smoke.mjs,directions.mjs（新增）}；docs/{IDEA_LOG.md,PRODUCT_BACKLOG.md,PROJECT_GUIDE.md,VERIFICATION.md}；ROADMAP.md；CHANGELOG.md。没有依赖、迁移、正式数据库、首页邀请卡、评测归档或 Collect 整理策略改动。

最终范围安全实测：18 个预期文件，暂存区为空，HEAD 仍为 733747719009e3176c4cf0e5f5ef24fc0752c662；变更文件密钥/Bearer/私钥签名扫描无命中，.env 未跟踪。最后仅追加此记录，未冒称再次运行应用检查。隔离 Mock 预览暂留回环 5173→8000 供用户检查，与个人库无关。


<a id="agent-004-a-finish-20261106"></a>
## 2026-11-06 · AGENT-004-A 截图收尾：知识候选针对性与呈现

起点与范围：承接上一轮全部18个未提交改动，未 reset/checkout/丢弃；HEAD 仍为733747719009e3176c4cf0e5f5ef24fc0752c662。用户本轮以两张隔离 Mock 截图说明问题，消息没有附图文件；本轮根据其准确文字描述建立两颗公开测试 Star 并实际浏览器截图，不冒称读到了未附的原图。沿用 IDEA-006/AGENT-004，两个任务状态仍仅 Backlog 维护。

截图暴露的问题：知识方向把长 Star 标题取前30字再拼接，可能半句话截断；不同 Star 复用相同三步，宽泛“深海”关键词命中没有解释与“深海发光”的距离。不是 Qwen 新输出或真实模型退步/提升证据。修正前是“给『长篇文字前30字』整理一个待核实的问题”加读原文/写问题/记方向；修正后第一张标题“挑选适合这份兴趣的入门资料”，使用原文片段“找入门书”，给出初学者定位、问题覆盖、作者/机构/参考出处、更新时间等比较标准，不给书名/购买渠道；第二张“拆解星星中已有的学习问题”，引用实际可见问题片段，分别提出黑暗、高压条件下如何适应的待核实问题与检索词，不预填答案。两张来源均说明“相邻兴趣：仅有部分关键词关联，未找到本次主题的直接知识依据。匹配词：深海。”提供换方向或补更贴近问题的 Star 选择。

实际调用链核对：search 的 text=description 或 original_text，含 title/tags/category/score/match_basis；Workflow 另读的 star_details 没有传入 generate，adapter 收到 ranked related_stars。没有假设完整原文一定可见，没有改变 retrieval.py/workflow.py 或固定 EVAL 快照。知识 Mock 只读取可见 text（空才用 title），不偷用未传递原文。完整主题包含只称“词面匹配，不是科学证据”，部分匹配称相邻兴趣；不是通用相关性判定。RETR-001 的匹配精度独立候选已关联 IDEA-006/Backlog，未实施 Embedding/检索重构。

实现边界：同文件两种显式文本结构（资料意图、如何/为什么/怎么问题），并列适应条件只按原文拆分，绝无科学知识表。一个结构只保留首个候选；未知结构只保守展示一个。超过120字的片段不截取伪装成完整问题。支持约束时不扩大确定性规则，退回一个原 knowledge 固定步骤示例并说明原因。unsupported constraints、低精力/时间预算、真实 Star ID、审批幂等、Run 方向、Collect、其他方向、旧请求序列化和 Live Prompt/payload 维持。Mock offline-v2 不代表语义理解或事实核验能力；词形规则可能漏识别/误识别，无法识别时减量，仍待用户体验。

本轮实测环境/命令：Windows、已有 Python3.12 .venv / Node22.23.3（进程 PATH 前置项目 .tools/node），未安装依赖，真实 Qwen/其他模型请求0，未执行真实开关、探针、联网检索或迁移新增。

| 实际检查 | 结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q -rs` | 最终 **293 passed / 1 skipped，27.94s**；PG 未配置 TEST_POSTGRES_URL，未验收PG |
| `.venv/Scripts/ruff.exe check backend evals`、`format --check backend evals` | 全通过，31 files |
| 前端 `npx prettier --write e2e/directions.mjs`、`npm run format:check` / `lint` / `typecheck` / `test` / `build` | 全通过，89 tests / 4 files，build 1581 modules |
| 原 `npm run test:e2e`，E2E_BASE_URL=127.0.0.1:5178、E2E_ALLOW_WRITE=true、E2E_INJECTED_FAILURE=true | exit0；四条PASS：只读/编辑/归档保护；结果/失败重试/刷新恢复；四方向请求/结果/方向追溯与无Quest/偏好写入；收集→草稿批准→搜索/关联→候选批准→编辑→反馈→偏好→审计，1440/390 |
| `.tools/node/node_modules/node/bin/node.exe .cache/agent004a_finish_screenshot.mjs` | exit0；按用户文字说明的两颗Star，深海发光查询，两条不同路径、准确来源、有效ID、两尺寸无横向溢出、Quest数不变 |
| 原 `evals/check_results.py --results evals/reviewed_quality_results.json`，subprocess捕获 | **预期exit1**；JSON与归档report完全一致；20 passed / 1 failed / 7 not_run / 3 not_rated，人工1 rated / 59 not_rated |

首次静态检查发现新增 path 变量漏定义，pytest对应截图用例随之失败（1 failed / 292 passed / 1 skipped）；修正后完整重跑上述293/1，不删除断言或修改证据。新增4项离线用例覆盖截图两类差异、长文本保守标题、同类/未知结构减量、摘要边界及完整词面匹配不等于科学证据；旧契约测试仍保留。

隔离浏览器：新启动器 `.cache/agent004a_finish_server.py` 禁用.env、空Key、强制Mock、关闭tracing，启动前断言 `.cache/agent004a-finish.db` 不存在，运行既有 Alembic 初始化并核对 engine URL；回环5178→8034。没有碰个人库，也没有重启/覆盖上一轮5173服务。先在空库完成原完整smoke，再在同一已核验隔离库将原测试Star归档、增加两颗目标Star复现；仅测试准备写入Star，探索生成无Quest写入。已实际查看 `.cache/agent004a-finish/knowledge-screenshot-1440.png` 与 `knowledge-screenshot-390.png`，标题完整、步骤有实质区别、说明可读且无重叠。预览5178仍留给用户验收；原5173进程可能仍运行旧版本，检查本轮请用5178。

本轮增量文件：backend/app/model_adapter.py、backend/tests/test_exploration_direction.py、frontend/e2e/directions.mjs、docs/IDEA_LOG.md、PRODUCT_BACKLOG.md、PROJECT_GUIDE.md、VERIFICATION.md、CHANGELOG.md。没有改其他既有实现/依赖/迁移；未 commit/push/云连接/发布。

复盘：为什么用户需要——避免阅读半截标题和多张同义活动卡，能看清建议究竟帮助选择资料还是拆问题。Agent系统解决什么——收紧Mock生成与可见上下文、来源说明、候选数量之间的关系；呈现修正属于UX/规则工程，不证明Live模型能力提升。学到什么——显式方向仍不足以保证针对性，生成内容必须受实际传入证据和可解释结构约束；少给一张比换词制造差异更诚实。知识解答真实性仍需可信材料、资料依据校验与独立真实质量验收；完整相关性判断属于RETR-001后续评估。当前M3穿插M2，无新增已证实P0，剩余P1为UX-003、INFRA-001/002、EVAL-001；AGENT-004/EVAL-001未收尾。下一项仍建议可信资料支持的学习路径，但本轮结束等待界面验收。

最终检查：380个本地链接/锚点、任务索引/详情状态及IDEA唯一性通过；git diff --check通过。三份归档JSON SHA256与上一节完全一致。原18个工作区文件保留，HEAD/暂存区未变；变更文件敏感签名扫描无命中。最后仅追加本记录，不冒称应用测试再次重跑。


<a id="agent-004-a-ci-import-20261106"></a>
## 2026-11-06 · AGENT-004-A 测试导入兼容修复

来源：用户确认 Actions 42143836403 的 backend 为292 passed / 1 failed / 1 skipped，唯一失败是 test_archived_public_baseline_unchanged 直接导入 evals 引起 ModuleNotFoundError。本轮未独立查询远程日志或运行新CI，以上为用户提供证据。起点工作区干净，HEAD=6136e4bb01e8a5bedb88e35eddc1d69caa7355cf。

仅改 backend/tests/test_exploration_direction.py：参照 test_offline_evals.py，以文件自身推导的仓库路径定位 evals/check_results.py，通过 importlib.util.spec_from_file_location/module_from_spec/exec_module 加载，再调用 checker.evaluate；保留原报告完全相等断言。没有改全局pytest配置、evals包结构、依赖、生产代码/Prompt/审批、历史JSON或评分，也没有删除/跳过失败测试。本文仅补充真实检查记录；不新增需求、改变阶段/任务状态/优先级或重写导航。

本轮Windows环境：Python3.12.15、pytest9.1.1，已有项目.venv。进程PATH前置项目 .tools/bootstrap/bin，设置PYTHONPATH=backend（与CI一致）；UV_NO_SYNC=true、UV_OFFLINE=true、UV_CACHE_DIR=.cache/uv，避免同步/安装依赖和访问网络，使用已有环境。按用户要求使用uv run调用pytest控制台入口，未以python -m pytest替代。

| 实际命令 | 结果 |
| --- | --- |
| `uv run pytest backend/tests/test_exploration_direction.py` | **17 passed，2.92s** |
| `uv run pytest` | **293 passed / 1 skipped，28.21s**；test_postgres因未配置独立TEST_POSTGRES_URL跳过，不代表PG通过 |
| `uv run ruff check backend evals` | passed |
| `uv run ruff format --check backend evals` | 最初1个文件需换行；仅对修改的测试运行ruff format后重跑，**31 files already formatted** |
| 既有check_results.py对reviewed_quality_results.json的离线CLI复核（subprocess捕获） | **预期exit1**，JSON与归档report完全一致；确定性20 passed / 1 failed / 7 not_run / 3 not_rated；人工1 rated / 59 not_rated |

最后的formatter只折行新增spec调用，未改变测试逻辑；pytest成绩来自本轮格式化前的实际执行，不冒称再次重跑。三份JSON SHA256保持：captures=4bc5f0576eaa5c8400bfba1428de416e7ce788258bc69fdc1bb8ab768267d4be；results=dc4a1aab7a56c111942d2f18c0eaa6c95e47b76af0ad5ceeeb84844753d5436f；report=47eaa93337af56266d3553ec184c07123eb818fce8d1040f9095861b495b84db。

真实模型请求0，未运行真实开关/探针/工作流。未重跑前端或浏览器：本轮只有测试导入与本文记录，无业务/依赖/界面改动，不以历史成绩冒充本轮。当前M3穿插M2，AGENT-004/EVAL-001保持既有未完成状态；无新增已证实P0，剩余P1仍为UX-003、INFRA-001/002、EVAL-001。下一步是用户提交推送后核对远程CI，本轮未commit/push，不能称Linux CI已通过。

复盘：用户需要可靠的CI保护现有交付；Agent系统解决的是离线基线保护测试在不同pytest入口下的导入稳定性，不改变Agent能力。我们学到python -m pytest与pytest控制台入口的sys.path行为可能不同，仓库外于backend的脚本应复用明确文件路径加载方式，不能依赖本地偶然可导入的仓库根目录。历史评测中的真实1 failed仍然是证据，不因导入修复消失。


<a id="agent-004-b-20261106"></a>
## 2026-11-06 · AGENT-004-B 用户材料知识微探索（离线开发）

起点HEAD=ff45e291a2a9df6abd2d9438bdf245c9e41bd839；git status仅有M docs/VERIFICATION.md。先完整读取并保留既有24行“A测试导入兼容修复”修改，本节仅追加，不将它当作B交付。A验收及Actions 42145983644成功为本次用户提供证据，本轮未独立查询远程CI。沿用IDEA-006/AGENT-004，AGENT-004/EVAL-001保持in_progress；M3穿插M2。无新增已证实P0；剩余P1 UX-003、INFRA-001/002、EVAL-001。完整复评见Backlog同日B记录。

真实实现：LearningSource(text≤5000,label≤200,url≤2000且http/https)仅knowledge Explore接受，原文与空白保留，纯空白拒绝；无材料序列化不增加learning_source键。材料作为结构化Human JSON数据，System只含固定边界指令，仍原有一次工具生成，无第二LLM核查。受控工具对LearningCard的Python Unicode零基半开位置、非空连续子串、source_kind字面值、用户来源名/URL完全一致性校验；不合格清空卡片与候选并说明依据不足，结构错误导致Run失败。无新增工具或SQL/执行权限。卡片在Run.state保存、结果与足迹均可重读，不给Proposal添加数据库字段；正式Quest仍按真实Star ID、时间/预算/精力/约束及用户审批验证。main.py/rules.py已核对，无需修改。

来源真实性边界：user_supplied_unverified仅指用户提供且未独立核实；精确引用存在不证明原文真实、来源身份或解释语义正确。界面明确分开原文/Agent简要解释/未知；不称已验证科学事实。Prompt数据隔离降低指令混淆，不能证明已解决Prompt Injection或语义幻觉。URL从未访问；本轮无科学知识联网查询。

数据保留：提交材料与卡片随本次Agent Run记录保存直到记录清理；不自动存Star、偏好、知识库，也不随批准写入Quest。当前无材料清理入口，UI已说明，长期保留/导出依赖DATA-004/002，未实现自动清理。未将用户真实材料写入公开夹具；Mock材料全部为显式虚构测试文本A–E，位于learning.py。仅A/C/D且海洋主题的固定示例能保守复述引用；B不相关/E恶意或任意未知材料均拒绝知识结论，不伪装任意文章理解能力。

本轮环境：Windows、已有Python3.12.15 .venv、Node22.23.3；没有依赖安装/更新。真实Qwen/OpenAI/其他模型请求0，SDK测试为内存MockTransport。未执行采样入口、云连接、commit/push或发布。

| 实际命令/检查 | 结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q -rs` | 最终319 passed / 1 skipped，29.55s；唯一test_postgres因未配置独立TEST_POSTGRES_URL跳过；不代表PG通过。此前新增SDK用例前318/1为同轮早期结果。 |
| `.venv/Scripts/ruff.exe check backend evals` / `format --check backend evals` | 通过，33 files。首次新增测试E701排版错误经formatter修正后重跑通过。 |
| Node22下前端 `npm run format:check` / `lint` / `typecheck` / `test` / `build` | 全通过；89 tests / 4 files，build 1581 modules。新增E2E格式化后format:check/lint再次通过；业务代码未再改，不冒称后面重复其他前端检查。首次误用系统旧Node导致lint structuredClone错误，纠正PATH后上述全项重跑；未改依赖。 |
| Node22执行 `frontend/e2e/smoke.mjs` | exit0，原Star阅读编辑/UX-002恢复/四方向/收集审批反馈全链加B专项五条PASS，1440/390。首次缺默认浏览器缓存启动失败，改用项目已有PLAYWRIGHT_BROWSERS_PATH后通过，无下载。 |
| 原 `evals/check_results.py --results evals/reviewed_quality_results.json`（subprocess捕获） | 预期exit1，JSON与原归档report完全相等；确定性20 passed / 1 failed / 7 not_run / 3 not_rated，人工1 rated / 59 not_rated。首次捕获因Windows编码错误失败，设置子进程PYTHONIOENCODING=utf-8后复核成功，不改检查器。 |

三份JSON实际SHA256与本轮开始前已有记录完全一致：captures=4bc5f0576eaa5c8400bfba1428de416e7ce788258bc69fdc1bb8ab768267d4be；results=dc4a1aab7a56c111942d2f18c0eaa6c95e47b76af0ad5ceeeb84844753d5436f；report=47eaa93337af56266d3553ec184c07123eb818fce8d1040f9095861b495b84db。工作树CRLF与Git blob LF原本不同，不能声称原始字节与HEAD相等；已核对换行规范化内容一致且工作树上述字节哈希未变。原EVAL版本、历史评分和检查器未改。

浏览器专用启动器.cache/agent004b_server.py先断言新库.cache/agent004b.db不存在，禁用.env、空Key、强制Mock/关tracing、Alembic head并核对实际engine.url.database；回环5179→8035，与个人库及旧预览分离。E2E_ALLOW_WRITE=true、E2E_INJECTED_FAILURE=true，PLAYWRIGHT_BROWSERS_PATH=.cache/browsers，产物.cache/agent004b-e2e。新增B专项覆盖完整输入、折叠预览、来源/URL、切创意隐藏材料、Tab标签焦点、准确payload、限定词、原文引用、刷新后按run_id重读卡片、无横向溢出且Quest/偏好无新增；原四方向验证保证无材料路径。实际查看learning-result-1440.png、learning-result-390.png，引用和解释区分、正文可读无重叠；不把自动浏览器当用户主观验收或屏幕阅读器人工实测。

新文件（当前未跟踪，交付时务必纳入后续用户提交）：backend/app/learning.py、backend/tests/test_learning_source.py、frontend/e2e/learning.mjs。修改：backend/app/{schemas.py,model_adapter.py,tools.py,workflow.py}、backend/tests/test_qwen_adapter.py、frontend/src/{App.tsx,types.ts,styles.css}、frontend/e2e/smoke.mjs、docs/{IDEA_LOG.md,PRODUCT_BACKLOG.md,PROJECT_GUIDE.md,VERIFICATION.md}、ROADMAP.md、CHANGELOG.md。VERIFICATION包含明确保留的先前修改。忽略缓存中的隔离启动器/数据库/截图不应提交。

未执行/待验收：真实Qwen材料解释、任意材料相关性/语义忠实性、真实科学质量与用户亲测；自动知识检索、PDF/网页解析、Embedding/RAG不在范围。无本轮远程CI或PG结果。AGENT-004-B离线切片之后停止，等待用户与助手验收，不执行真实采样。下一项推荐先在Mock预览验收卡片，再单独约定公开非敏感材料与真实调用额度，不能据本轮推断已授权。

复盘：用户需要——从“写问题/去搜索”前进到看到有原文根据的一条信息，并可追问。Agent系统解决——把外部不可信文本接入同一生成边界，用独立DTO与确定性来源门控约束可展示结果，同时保留正式写入审批；表单与视觉属于UX工程，非模型能力提升。学到什么——精确出处、来源真实性和语义正确性是三个不同问题；Mock能证明协议/留存/安全路径，不能证明真实解释质量，自动来源门控也不能替代人工语义评价。

最终文档/范围检查：349个本地Markdown链接路径存在（本次未逐一检查锚点，不冒称锚点全通过）；git diff --check通过。确认先前A导入兼容记录仍完整位于新增B节之前。工作区15个修改文件+3个新且未跟踪文件，暂存区为空，HEAD未变；无个人库/历史评测文件改动。隔离Mock预览留在回环5179供用户验收。最后仅追加此检查，不冒称应用测试再次重跑。


<a id="agent-004-c-20261108"></a>
## 2026-11-08 · AGENT-004-C / EVAL-001 知识解释质量离线准备

起点HEAD=0dd5dc48b936b34aeb8859b1d9e62fecf8564057，git status --short为空；未覆盖已有用户修改。读取AGENTS、ROADMAP、Backlog、IDEA、PROJECT_GUIDE、最新VERIFICATION、evals README/QUALITY_RUBRIC与指定生产/评测/测试源码。用户提供成功CI链接为来源信息，本轮没有访问远程CI或连接云服务。当前仍M3穿插M2，两任务整体仍in_progress，优先级/未完成任务完整复评见Backlog本轮记录。

案例：独立learning-cases-v1/learning-quality-v1，五例公开固定虚构数据：等长窗口3/7次可比较记录、部分/可能与范围、相互冲突记录、主题无关、恶意材料与Unicode。每例固定AgentRequest材料元数据、公开模拟related_stars七字段、Preferences默认展开与合成UUID映射、支持信息/禁止结论/可接受行为及人工维度。没有star_details/original_text补料、真实Star或个人库访问。CASE-01/02/04固定为未来三例，不能按输出事后挑选。

双层证据：ModelAdapter.proposals原始Pydantic DTO先保存，再对深拷贝调用现有validate_learning_result；validated_output和gate保存位置/元数据、保留/拒绝/移除数及系统问题。原始卡片、uncertainties、后续问题、proposals/questions随raw保留。非法工具/Pydantic失败/超时保留分类和null原始DTO，不伪装主动拒绝；取得DTO后本地失败可保留raw。来源失败与成功拦截分别呈现，不再次请求。人工六维+拒绝适当性独立，默认not_rated，无总分；有评分必须附日期/评审者/依据/来源声明，程序不能认证身份。

安全边界：默认检查与计划入口在独立子进程审计下拒绝socket/sqlite/.env/.cache读取及模型/配置/数据库/图导入。未来真实入口只有--allow-live后才读取配置，复用北京百炼预检，固定qwen3.8-flash、SDK retries=0；预写fsync尝试/实际payload、每例一次/全批三次、失败或来源门控拒绝即停。批次目录原子创建，已有目录拒绝重跑；中断不恢复，不提供覆盖。测试只用内存Fake，含真实Adapter解析分支但SDK构造器被替换，所有模型网络请求0。未创建.cache/learning-quality-v1，未删除/覆盖任何已有真实采样记录。无数据库/API审批/生产材料操作。

追溯：源码/Prompt所在Adapter/Schema/learning/rules/retrieval/采样器/检查器/预检/规范按真实字节SHA256；案例仅CRLF→LF规范化，固定SHA256=8d390e8d4425b9849351a11ddd82916899efeea52a5368887627b2297ea96a4f。LF/CRLF等价且实质变化拒绝；保存完整上下文、模型配置摘要、Git SHA/dirty、usage或unknown和耗时。历史源码差异显式显示source_matches_current，不宣称当前门控重放等于旧代码执行。Live来源离线无法独立认证，不混合Fake/Mock/Live，不保存隐藏推理或密钥。

环境：Windows PowerShell、Python3.12.15、已有.venv，未安装/修改依赖。uv未在PATH发现；采用与CI `uv run pytest`相同的pytest控制台入口 `.venv/Scripts/pytest.exe`，使用仓库pyproject与隔离SQLite测试配置，不依赖python -m pytest偶然sys.path。未在Linux执行，不能宣称新远程CI通过。

| 实际执行 | 结果 |
| --- | --- |
| 新专项首次 `.venv/Scripts/pytest.exe backend/tests/test_learning_quality_evals.py -q -rs` | 初版42 passed；随后添加额度/中断/真实Adapter解析/非法封装保护，最终48项均在最终完整回归中执行通过，不冒称首次已含后续用例。 |
| 最终 `.venv/Scripts/pytest.exe -q -rs` | **367 passed / 1 skipped，36.59s**；唯一PostgreSQL测试因未配置独立TEST_POSTGRES_URL跳过，不代表PG通过。中间版364/366 passed仅是同轮历史结果。 |
| `.venv/Scripts/ruff.exe check backend evals` | passed |
| `.venv/Scripts/ruff.exe format --check backend evals` | 最终passed，37 files；初次新增文件格式化、末轮新增参数保护后一个条件需折行，执行ruff format后重跑check/format通过。最终完整pytest在最后一次仅格式化折行前执行，没有冒称格式化后再跑全部应用测试。 |
| 新check_learning_quality.py / collect_learning_quality.py默认CLI（Python -X utf8，subprocess解析stdout） | exit0；默认报告5 not_run、0人工rated/35 not_rated，计划固定01/02/04、最多3次。无模型输出、无质量结论。 |
| 原check_results.py --results evals/reviewed_quality_results.json（最终完整pytest内子进程执行） | **预期exit1**，输出JSON与旧report完全相等：20 passed / 1 failed / 7 not_run / 3 not_rated；人工1 rated / 59 not_rated。未知预算被写成0.0的真实失败继续保留。 |
| 文档本地链接路径检查（正则提取本轮七份Markdown中的非远程链接） | 308条路径存在，无缺失；未逐一验证所有历史锚点，不宣称全锚点通过。新知识入口与本节使用显式锚点。 |
| git diff --check | passed；交付前再次检查范围、未跟踪文件与HEAD/暂存区。 |

旧三份JSON从开始到结束逐字节SHA256不变：captures=4bc5f0576eaa5c8400bfba1428de416e7ce788258bc69fdc1bb8ab768267d4be；results=dc4a1aab7a56c111942d2f18c0eaa6c95e47b76af0ad5ceeeb84844753d5436f；report=47eaa93337af56266d3553ec184c07123eb818fce8d1040f9095861b495b84db。旧案例/规范/采样器/检查器均未修改。新案例不冒充旧版本对照，没有质量提升结论。

新增且未跟踪（全部5个）：evals/learning_quality_cases.json、evals/LEARNING_QUALITY_RUBRIC.md、evals/check_learning_quality.py、evals/collect_learning_quality.py、backend/tests/test_learning_quality_evals.py。修改7份文档：evals/README.md、docs/IDEA_LOG.md、docs/PRODUCT_BACKLOG.md、docs/PROJECT_GUIDE.md、docs/VERIFICATION.md、ROADMAP.md、CHANGELOG.md。生产后端/Prompt/Workflow/审批/数据库Schema、依赖和前端均未改。没有commit/push、发布、私人报告上传或真实请求。

未执行：真实Qwen/任何探针、人工知识内容评分、完整LangGraph/审批评价、Linux新CI、独立PG集成；前端lint/typecheck/test/build和浏览器视觉测试未重跑，因为本轮仅独立评测设施/后端离线测试及文档，未改业务/依赖/前端，不以历史成绩代替新结果。未来配置预检只验证本地格式，无法证明Key/余额/真实兼容性或质量；这些需另行授权。离线准备具备本地验收条件，停止于此，等待用户验收，不进入Live。

为什么用户需要：来源能定位仍可能解释错误，用户需要可复核的学习价值评价，而非只看到合法卡片。Agent系统解决什么：建立模型生成与系统门控之间的可观察边界，以及严格请求预算和分层证据；这是评测/安全工程改进，不是模型能力或普通UI改进。学到了什么：准确引用、保留限定、语义忠实与有学习收获须分别判断；正确拒绝也可能有价值，Schema失败则没有可评分解释。48项离线保护能证明协议与执行边界，不能证明真实科学正确性、全面Prompt Injection防护或真实用户学习效果。

剩余P0/P1：无新增已证实P0；P1仍为UX-003、INFRA-001/002、EVAL-001。下一项推荐先验收本轮离线成果，再单独确认未来固定三例采样及人工评价来源，AGENT-004/EVAL-001整体不done。

最终收尾复查：新增本节后8份相关Markdown共315条本地链接路径存在；两个默认CLI再次exit0，旧三份JSON字节哈希仍相等，未来固定Live批次目录不存在。git diff --check通过，7份修改文档+5个未跟踪新文件，暂存区为空，HEAD仍为0dd5dc48b936b34aeb8859b1d9e62fecf8564057。没有再次执行应用测试。
