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
