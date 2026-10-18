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
