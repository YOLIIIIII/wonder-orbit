import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  Compass,
  Heart,
  Home,
  Network,
  Plus,
  RefreshCw,
  Settings2,
  Sparkles,
  Star as StarIcon,
  X,
  Activity,
} from "lucide-react";
import { api, ApiError } from "./api";
import {
  Empty,
  ListInput,
  OrbitArt,
  ProposalEditor,
  ProposalFacts,
  StarCard,
  StarEditor,
  energyNames,
  numeric,
  split,
  statusNames,
} from "./components";
import type {
  AgentRequest,
  Energy,
  PreferenceData,
  Proposal,
  Quest,
  Relation,
  Run,
  Star,
  StarInput,
  Stats,
} from "./types";

type Page =
  | "home"
  | "collect"
  | "archive"
  | "relations"
  | "explore"
  | "quests"
  | "runs"
  | "preferences";
const pages = [
  { id: "home", name: "我的星屿", icon: Home },
  { id: "collect", name: "收集星星", icon: Plus },
  { id: "archive", name: "星星档案", icon: BookOpen },
  { id: "relations", name: "兴趣轨道", icon: Network },
  { id: "explore", name: "微型探索", icon: Compass },
  { id: "quests", name: "体验手记", icon: Heart },
  { id: "runs", name: "Agent 足迹", icon: Activity },
  { id: "preferences", name: "我的偏好", icon: Settings2 },
] as const;
const blankStar: StarInput = {
  title: "",
  original_text: "",
  description: "",
  category: "未分类",
  tags: [],
  interest_reason: null,
  source_type: "manual",
  source_reference: null,
  estimated_minutes: null,
  estimated_budget: null,
  energy_level: null,
  status: "collected",
};
const draftFieldNames: Record<string, string> = {
  title: "标题",
  original_text: "原始文字",
  description: "整理后的描述",
  category: "兴趣类别",
  tags: "标签",
  interest_reason: "兴趣原因",
  source_type: "内容来源",
  source_reference: "参考链接",
  estimated_minutes: "预计时间",
  estimated_budget: "预计预算",
  energy_level: "所需精力",
  status: "收藏状态",
};
const initialPreferences: PreferenceData = {
  explicit: {
    categories: [],
    min_minutes: 1,
    max_minutes: 30,
    max_budget: null,
    energy_level: null,
    constraints: [],
  },
  candidates: [],
};

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [stars, setStars] = useState<Star[]>([]);
  const [quests, setQuests] = useState<Quest[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [relations, setRelations] = useState<Relation[]>([]);
  const [stats, setStats] = useState<Stats>({
    stars: 0,
    quests: 0,
    completed: 0,
    categories: [],
  });
  const [preferences, setPreferences] = useState(initialPreferences);
  const [mock, setMock] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [text, setText] = useState("");
  const [source, setSource] = useState<"manual" | "paste" | "link">("paste");
  const [reference, setReference] = useState("");
  const [manual, setManual] = useState(false);
  const [draftRun, setDraftRun] = useState<Run | null>(null);
  const [savedStarId, setSavedStarId] = useState<string | null>(null);
  const [exploreRun, setExploreRun] = useState<Run | null>(null);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [selectedStar, setSelectedStar] = useState<Star | null>(null);
  const [minutes, setMinutes] = useState("15");
  const [budget, setBudget] = useState("");
  const [energy, setEnergy] = useState<Energy>("low");
  const [query, setQuery] = useState("");
  const [searchIds, setSearchIds] = useState<string[] | null>(null);
  const [category, setCategory] = useState("");
  const [starStatus, setStarStatus] = useState("");
  const [editingProposal, setEditingProposal] = useState<{
    proposal: Proposal;
    run?: Run;
    index?: number;
    quest?: Quest;
  } | null>(null);
  const [feedbackQuest, setFeedbackQuest] = useState<Quest | null>(null);
  const [feedback, setFeedback] = useState("");
  const [liked, setLiked] = useState("");
  const [disliked, setDisliked] = useState("");
  const [outcome, setOutcome] = useState<"completed" | "skipped">("completed");

  const refresh = useCallback(async () => {
    const [s, q, r, links, counts, pref, health] = await Promise.all([
      api<Star[]>("/stars"),
      api<Quest[]>("/quests"),
      api<Run[]>("/agent/runs"),
      api<Relation[]>("/relations"),
      api<Stats>("/stats"),
      api<PreferenceData>("/preferences"),
      api<{ mock_mode: boolean }>("/health"),
    ]);
    setStars(s);
    setQuests(q);
    setRuns(r);
    setRelations(links);
    setStats(counts);
    setPreferences(pref);
    setMock(health.mock_mode);
  }, []);
  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, [refresh]);
  async function act(operation: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
      if (e instanceof ApiError && e.runId) {
        const failed = await api<Run>("/agent/runs/" + e.runId).catch(
          () => null,
        );
        if (failed) {
          setSelectedRun(failed);
          setPage("runs");
        }
      }
    } finally {
      setBusy(false);
    }
  }
  function openRun(run: Run) {
    setSelectedRun(run);
    setPage("runs");
  }
  async function generate(request: AgentRequest) {
    if (request.request_type === "collect") {
      setDraftRun(null);
      setSavedStarId(null);
    }
    const run = await api<Run>(
      "/agent/runs",
      "POST",
      request,
      crypto.randomUUID(),
    );
    if (request.request_type === "collect") setDraftRun(run);
    else setExploreRun(run);
  }
  async function decision(
    run: Run,
    index: number,
    approved: boolean,
    edited?: Proposal | StarInput,
  ) {
    const isStar = run.request_type === "collect";
    await api("/agent/runs/" + run.run_id + "/decision", "POST", {
      approved,
      index,
      ...(edited
        ? isStar
          ? { edited_star: edited }
          : { edited_proposal: edited }
        : {}),
    });
    const updated = await api<Run>("/agent/runs/" + run.run_id);
    if (isStar) {
      setDraftRun(updated);
      if (
        approved &&
        updated.decisions.star?.approved &&
        updated.decisions.star.star_id
      ) {
        setSavedStarId(updated.decisions.star.star_id);
        setText("");
        setNotice("这份好奇已加入星星档案。");
      }
    } else {
      setExploreRun(updated);
      setNotice(
        approved
          ? "已接受。可以在体验手记中记录结果。"
          : "已放下这个候选，随时可以重新探索。",
      );
    }
    setEditingProposal(null);
  }
  const filteredStars = stars.filter(
    (s) =>
      (!searchIds || searchIds.includes(s.id)) &&
      (!category || s.category === category) &&
      (!starStatus || s.status === starStatus),
  );
  const connected = mock !== null;
  const hasStars = stars.length > 0;
  const canExplore = stars.some((star) => star.status !== "archived");
  const draftDecision = draftRun?.decisions.star;
  const draftPending =
    draftRun?.request_type === "collect" &&
    draftRun.status === "awaiting_decision" &&
    !!draftRun.state.draft &&
    !draftDecision;
  const header = pages.find((p) => p.id === page)!;
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => setPage("home")}>
          <span className="brand-symbol">
            <Sparkles size={26} />
          </span>
          <span>
            WonderOrbit<small>星屿 · 好奇心档案馆</small>
          </span>
        </button>
        <span className="nav-caption">YOUR LITTLE UNIVERSE</span>
        <nav aria-label="主导航">
          {pages.map((item) => (
            <button
              key={item.id}
              className={page === item.id ? "active" : ""}
              onClick={() => {
                setPage(item.id);
                setError("");
                setNotice("");
              }}
            >
              <item.icon size={19} />
              {item.name}
              {item.id === "collect" && <span className="nav-plus">+</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <div className="companion" aria-hidden="true">
            <i />
            <i />
            <span>⌣</span>
            <b>✦</b>
          </div>
          <p>让好奇慢慢长大。</p>
          <small>不必赶路，也不用完成所有事。</small>
        </div>
        <div className="sidebar-bottom">
          <span
            className={
              mock === null ? "connection-dot offline" : "connection-dot"
            }
          />
          {mock === null
            ? "等待后端连接"
            : mock
              ? "Mock 模式 · 规则生成"
              : "模型服务已连接"}
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>
            {header.name}
            <small>A Personal Curiosity Agent</small>
          </span>
          <span className="mode-label">
            {mock === null ? "未连接" : mock ? "Mock" : "Live"}
          </span>
          <button
            className="quiet"
            disabled={busy}
            onClick={() =>
              act(async () => {
                await refresh();
                setNotice("档案已刷新。");
              })
            }
            aria-label="刷新后端数据"
          >
            <RefreshCw size={17} />
          </button>
        </header>
        <div className="main-content">
          {error && (
            <div className="alert" role="alert">
              {error}
              <button aria-label="关闭错误" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div className="notice" role="status">
              <Check size={17} />
              {notice}
            </div>
          )}
          {busy && (
            <div className="loading" role="status">
              正在处理，请稍候…
            </div>
          )}
          <UsageGuide mock={mock} />
          {page === "home" && (
            <>
              <section className="hero">
                <div className="hero-copy">
                  <span className="eyebrow">
                    <span /> A SPACE FOR YOUR CURIOSITY
                  </span>
                  <h1>
                    给好奇心，
                    <br />
                    一座小小的<span>星屿。</span>
                  </h1>
                  <p>
                    {!connected
                      ? "连接档案后，会根据已保存的兴趣给你下一步提示。"
                      : !hasStars
                        ? "星星是你收藏的兴趣或好奇。从收藏第一颗星星开始，探索才有真实依据。"
                        : canExplore
                          ? "从已有兴趣开始微型探索，参考实际收藏内容和你的明确偏好；也可以继续收集。"
                          : "你已收藏过兴趣，但归档星星不参与推荐。可先到档案恢复一颗星星，或继续收集。"}
                  </p>
                  <div className="hero-actions">
                    <button
                      className="primary"
                      onClick={() =>
                        setPage(
                          connected && hasStars
                            ? canExplore
                              ? "explore"
                              : "archive"
                            : "collect",
                        )
                      }
                    >
                      <Plus size={17} />
                      {connected && hasStars
                        ? canExplore
                          ? "开始微型探索"
                          : "查看星星档案"
                        : connected
                          ? "收集第一颗星星"
                          : "收集一颗星星"}
                    </button>
                    {connected && hasStars && (
                      <button
                        className="text-button"
                        onClick={() => setPage("collect")}
                      >
                        继续收集星星
                        <ArrowRight size={17} />
                      </button>
                    )}
                  </div>
                </div>
                <OrbitArt />
              </section>
              <section className="stat-row">
                <div>
                  <StarIcon />
                  <span>
                    <strong>{connected ? stats.stars : "—"}</strong>颗兴趣星星
                  </span>
                </div>
                <div>
                  <Network />
                  <span>
                    <strong>{connected ? stats.categories.length : "—"}</strong>
                    个兴趣类别
                  </span>
                </div>
                <div>
                  <Compass />
                  <span>
                    <strong>{connected ? stats.completed : "—"}</strong>
                    次完成的体验
                  </span>
                </div>
                <p>所有数字来自你的真实档案。</p>
              </section>
              <div className="section-title">
                <div>
                  <span className="eyebrow">RECENT SPARKS</span>
                  <h2>最近落在星屿的光</h2>
                </div>
                <button
                  className="text-button"
                  onClick={() => setPage("archive")}
                >
                  查看全部
                  <ArrowUpRight size={17} />
                </button>
              </div>
              {connected &&
                (hasStars ? (
                  <div className="star-grid">
                    {stars.slice(0, 3).map((s) => (
                      <StarCard
                        key={s.id}
                        star={s}
                        onOpen={() => setSelectedStar(s)}
                      />
                    ))}
                  </div>
                ) : (
                  <Empty
                    title="从收藏第一颗星星开始"
                    text="先在上方收集一份好奇，检查并确认草稿；保存后，再从已有兴趣里寻找小体验。"
                  />
                ))}
              <div className="home-footer">
                ✦ 好奇没有标准答案，探索也不需要打卡。
              </div>
            </>
          )}
          {page === "collect" && (
            <>
              <PageTitle
                eyebrow="CATCH A LITTLE SPARK"
                title="把一闪而过的好奇，留下来。"
                text="先留下原始文字，再由你确认整理后的内容。未知字段可以留空。"
              />
              <div className="two-column">
                <section className="panel">
                  <div className="panel-heading">
                    <h3>一份新的好奇</h3>
                    <button
                      className="text-button"
                      onClick={() => setManual(!manual)}
                    >
                      {manual ? "自然语言整理" : "手动填写"}
                    </button>
                  </div>
                  {manual ? (
                    <StarEditor
                      initial={blankStar}
                      disabled={busy}
                      onSave={(v) =>
                        act(async () => {
                          setSavedStarId(null);
                          setDraftRun(null);
                          const saved = await api<Star>("/stars", "POST", v);
                          setSavedStarId(saved.id);
                          setManual(false);
                          setNotice("星星已保存。");
                        })
                      }
                    />
                  ) : (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        act(() =>
                          generate({
                            request_type: "collect",
                            text,
                            source_type: source,
                            source_reference: reference || null,
                          }),
                        );
                      }}
                    >
                      <label>
                        你最近对什么感到好奇？（必填）
                        <textarea
                          className="idea-input"
                          required
                          maxLength={12000}
                          value={text}
                          onChange={(e) => setText(e.target.value)}
                          aria-label="你最近对什么感到好奇？"
                          aria-describedby="collect-draft-hint"
                          placeholder="例如：我想了解深海生物为什么会发光，想先记下几个好奇的问题。"
                        />
                      </label>
                      <p className="field-hint" id="collect-draft-hint">
                        一次整理生成一张可编辑草稿，确认后才会加入正式档案。建议每次围绕一个兴趣填写。
                      </p>
                      <div className="field-grid">
                        <label>
                          内容来源
                          <select
                            value={source}
                            onChange={(e) =>
                              setSource(e.target.value as typeof source)
                            }
                          >
                            <option value="paste">粘贴文字</option>
                            <option value="manual">手动输入</option>
                            <option value="link">链接引用</option>
                          </select>
                        </label>
                        <label>
                          参考链接（可选）
                          <input
                            type="url"
                            pattern="[Hh][Tt][Tt][Pp][Ss]?://.+"
                            aria-describedby="collect-reference-hint"
                            value={reference}
                            onChange={(e) => setReference(e.target.value)}
                            placeholder="https://example.com/notes"
                          />
                        </label>
                      </div>
                      <p className="field-hint" id="collect-reference-hint">
                        填写完整 http/https
                        地址。链接仅保存来源，不读取网页；选择链接引用后，仍需填写上方的兴趣原始文字。
                      </p>
                      <button className="primary" disabled={busy}>
                        <Sparkles size={16} />
                        整理成草稿
                      </button>
                    </form>
                  )}
                </section>
                <aside className="gentle-panel">
                  <StarIcon size={28} />
                  <h3>每种喜欢，都值得被记住。</h3>
                  <p>
                    一条兴趣不必完整，也不必特别。星屿会保留你的原话，让你随时修改整理结果。
                  </p>
                  <div className="note-line">01 留下原始想法</div>
                  <div className="note-line">02 预览与编辑草稿</div>
                  <div className="note-line">03 确认后加入档案</div>
                </aside>
              </div>
              {draftRun && (
                <section className="panel result-panel">
                  <ResultHeading
                    run={draftRun}
                    title={
                      draftDecision
                        ? draftDecision.approved
                          ? "保存结果"
                          : "已放下的草稿"
                        : draftPending
                          ? "草稿待确认"
                          : "整理状态"
                    }
                    onView={() => openRun(draftRun)}
                  />
                  {draftDecision ? (
                    <>
                      <p>
                        {draftDecision.approved && draftDecision.star_id
                          ? "这张草稿已保存到档案。"
                          : draftDecision.approved
                            ? "保存结果尚未确认，请刷新档案查看。"
                            : "这张草稿已放下，没有加入正式档案。"}
                      </p>
                      {savedStarId && draftDecision.approved && (
                        <SavedStarNextStep onNavigate={setPage} />
                      )}
                    </>
                  ) : draftPending ? (
                    <>
                      <p className="flow-note" role="status">
                        草稿已经生成，还没有加入正式档案。请检查、修改后确认保存，也可以暂不保存。
                      </p>
                      <div className="soft-note">
                        {draftRun.state.draft?.questions.join(" ")}
                        {!!draftRun.state.draft?.missing_fields.length && (
                          <p className="draft-fields">
                            尚不清楚：
                            {[
                              ...new Set(
                                draftRun.state.draft.missing_fields.map(
                                  (field) =>
                                    Object.hasOwn(draftFieldNames, field)
                                      ? draftFieldNames[field]
                                      : "其他待补充信息",
                                ),
                              ),
                            ].join("、")}
                            。这不表示整理出错，可选信息可补充或留空。
                          </p>
                        )}
                      </div>
                      {draftRun.state.draft && (
                        <StarEditor
                          key={draftRun.run_id}
                          initial={draftRun.state.draft.draft}
                          sourceLocked
                          disabled={busy}
                          onSave={(v) =>
                            act(() => decision(draftRun, 0, true, v))
                          }
                        />
                      )}
                      <button
                        className="text-button"
                        disabled={busy}
                        onClick={() => act(() => decision(draftRun, 0, false))}
                      >
                        暂不保存
                      </button>
                    </>
                  ) : (
                    <p>本次整理尚无可确认的草稿，请查看运行状态。</p>
                  )}
                </section>
              )}
              {savedStarId && !draftRun && (
                <section className="panel result-panel">
                  <p>星星已保存到档案。</p>
                  <SavedStarNextStep onNavigate={setPage} />
                </section>
              )}
            </>
          )}
          {page === "archive" && (
            <>
              <PageTitle
                eyebrow="YOUR CURIOSITY ARCHIVE"
                title="星星档案"
                text="所有喜欢都有来处。搜索、编辑，或让一颗星星暂时休息。"
              />
              <form
                className="filter-bar"
                onSubmit={(e) => {
                  e.preventDefault();
                  act(async () => {
                    const found = await api<Star[]>(
                      "/stars?q=" + encodeURIComponent(query),
                    );
                    setSearchIds(query ? found.map((s) => s.id) : null);
                  });
                }}
              >
                <input
                  aria-label="搜索星星"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="搜索标题、文字或标签…"
                />
                <select
                  aria-label="兴趣类别筛选"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  <option value="">所有类别</option>
                  {stats.categories.map((c) => (
                    <option key={c.name}>{c.name}</option>
                  ))}
                </select>
                <select
                  aria-label="星星状态筛选"
                  value={starStatus}
                  onChange={(e) => setStarStatus(e.target.value)}
                >
                  <option value="">所有状态</option>
                  <option value="collected">已收藏</option>
                  <option value="exploring">探索中</option>
                  <option value="archived">已归档</option>
                </select>
                <button className="secondary" disabled={busy}>
                  搜索
                </button>
              </form>
              <div className="star-grid">
                {filteredStars.map((s) => (
                  <StarCard
                    key={s.id}
                    star={s}
                    onOpen={() => setSelectedStar(s)}
                  />
                ))}
              </div>
              {!filteredStars.length && (
                <Empty
                  title="这里还没有匹配的星星"
                  text="试试其他关键词，或收藏一份新的好奇。"
                  action={
                    <button
                      className="primary"
                      onClick={() => setPage("collect")}
                    >
                      去收集
                    </button>
                  }
                />
              )}
            </>
          )}
          {page === "relations" && (
            <>
              <PageTitle
                eyebrow="FOLLOW THE THREADS"
                title="喜欢之间，自有轨道。"
                text="以真实的共同标签和兴趣类别连接星星。这里不会编造你的历史。"
              />
              {!relations.length && (
                <Empty
                  title="轨道会随着收藏慢慢出现"
                  text="至少两颗星星拥有相同标签或明确类别时，这里会展示它们的连接。"
                />
              )}
              <div className="relation-list">
                {relations.map((link) => (
                  <section
                    className="relation-card"
                    key={link.from_id + link.to_id}
                  >
                    <button
                      onClick={() =>
                        setSelectedStar(
                          stars.find((s) => s.id === link.from_id) || null,
                        )
                      }
                    >
                      <StarIcon size={20} />
                      {link.from_title}
                    </button>
                    <div className="relation-thread">
                      <span>✦</span>
                      {link.reasons.map((r) => (
                        <small key={r}>{r}</small>
                      ))}
                    </div>
                    <button
                      onClick={() =>
                        setSelectedStar(
                          stars.find((s) => s.id === link.to_id) || null,
                        )
                      }
                    >
                      <StarIcon size={20} />
                      {link.to_title}
                    </button>
                  </section>
                ))}
              </div>
            </>
          )}
          {page === "explore" && (
            <>
              <PageTitle
                eyebrow="MAKE ROOM FOR WONDER"
                title="一次刚刚好的微型探索"
                text="从真实兴趣出发，让时间、预算和精力决定这次探索的大小。"
              />
              {connected && !canExplore && (
                <section className="panel flow-note" aria-label="探索前的准备">
                  <p>
                    {hasStars
                      ? "归档星星不会用于推荐。请在档案中将一颗星星改为已收藏，或继续收集。"
                      : "探索需要已有的兴趣依据。请先收集并确认一颗星星，再用档案里的关键词探索。"}
                  </p>
                  <button
                    className="secondary"
                    onClick={() => setPage(hasStars ? "archive" : "collect")}
                  >
                    {hasStars ? "查看星星档案" : "去收集第一颗星星"}
                  </button>
                </section>
              )}
              <section className="panel">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    act(() =>
                      generate({
                        request_type: "explore",
                        text,
                        available_minutes: numeric(minutes),
                        budget: numeric(budget),
                        energy_level: energy,
                      }),
                    );
                  }}
                >
                  <label>
                    今天想靠近哪份好奇？（必填）
                    <input
                      required
                      value={text}
                      onChange={(e) => setText(e.target.value)}
                      aria-label="今天想靠近哪份好奇？"
                      maxLength={12000}
                      placeholder="使用档案里的关键词，如：海洋、星空…"
                    />
                  </label>
                  <div className="field-grid three">
                    <label>
                      可用时间（分钟，可选）
                      <input
                        aria-label="可用时间（分钟，可选）"
                        aria-describedby="explore-minutes-hint"
                        type="number"
                        min={1}
                        max={1440}
                        value={minutes}
                        onChange={(e) => setMinutes(e.target.value)}
                      />
                      <span className="field-hint" id="explore-minutes-hint">
                        留空用偏好最长时间；填写本次可用上限。
                      </span>
                    </label>
                    <label>
                      本次预算（元，可选）
                      <input
                        aria-label="本次预算（元，可选）"
                        aria-describedby="explore-budget-hint"
                        type="number"
                        min={0}
                        max={100000}
                        step="0.01"
                        value={budget}
                        onChange={(e) => setBudget(e.target.value)}
                      />
                      <span className="field-hint" id="explore-budget-hint">
                        留空仍遵守偏好上限；0 元为零预算；同时设置取更低上限。
                      </span>
                    </label>
                    <label>
                      当前精力（必选）
                      <select
                        aria-label="当前精力（必选）"
                        aria-describedby="explore-energy-hint"
                        value={energy}
                        onChange={(e) => setEnergy(e.target.value as Energy)}
                      >
                        {Object.entries(energyNames).map(([k, v]) => (
                          <option key={k} value={k}>
                            {v}
                          </option>
                        ))}
                      </select>
                      <span className="field-hint" id="explore-energy-hint">
                        按本次与偏好中的较低精力上限推荐。
                      </span>
                    </label>
                  </div>
                  <details className="form-help">
                    <summary>查看时间、预算和精力规则</summary>
                    <ul>
                      <li>
                        时间为 1–1440
                        分钟，同时设置时取较短上限，仍需达到偏好最短时间；时间冲突会要求澄清。
                      </li>
                      <li>
                        预算为 0–100000
                        元；本次和偏好均留空时不额外限制，有上限时未知成本无法通过检查。
                      </li>
                      <li>
                        精力按低、中、高比较；偏好未设置时只采用本次选择，不把未设置当作低精力。
                      </li>
                    </ul>
                  </details>
                  <button className="primary" disabled={busy}>
                    <Compass size={17} />
                    寻找小体验
                  </button>
                </form>
              </section>
              {exploreRun && (
                <section className="result-panel">
                  <ResultHeading
                    run={exploreRun}
                    onView={() => openRun(exploreRun)}
                  />
                  {exploreRun.state.questions?.map((q) => (
                    <p className="soft-note" key={q}>
                      {q}
                    </p>
                  ))}
                  <div className="proposal-grid">
                    {exploreRun.state.proposals?.map((proposal, i) => (
                      <section className="panel proposal" key={i}>
                        <span className="eyebrow">
                          EXPLORATION {String(i + 1).padStart(2, "0")}
                        </span>
                        <h3>{proposal.title}</h3>
                        <p>{proposal.description}</p>
                        <ProposalFacts proposal={proposal} />
                        <ol>
                          {proposal.steps.map((step, n) => (
                            <li key={n}>{step}</li>
                          ))}
                        </ol>
                        <div className="rationale">
                          <strong>为什么推荐</strong>
                          <p>{proposal.rationale}</p>
                          <div className="tags">
                            {proposal.based_on_star_ids.map((id) => (
                              <button
                                key={id}
                                className="chip"
                                onClick={() =>
                                  setSelectedStar(
                                    stars.find((s) => s.id === id) || null,
                                  )
                                }
                              >
                                {stars.find((s) => s.id === id)?.title || id}
                              </button>
                            ))}
                          </div>
                        </div>
                        <details>
                          <summary>仍然不确定的事</summary>
                          {proposal.uncertainties.map((u) => (
                            <p key={u}>{u}</p>
                          ))}
                        </details>
                        {exploreRun.decisions[String(i)] ? (
                          <div className="decision-label">
                            {exploreRun.decisions[String(i)].approved
                              ? "✓ 已接受，请到体验手记记录结果"
                              : "已放下这个候选"}
                          </div>
                        ) : (
                          <div className="button-row">
                            <button
                              className="primary"
                              disabled={busy}
                              onClick={() =>
                                act(() => decision(exploreRun, i, true))
                              }
                            >
                              接受这个体验
                            </button>
                            <button
                              className="quiet"
                              disabled={busy}
                              onClick={() =>
                                setEditingProposal({
                                  proposal,
                                  run: exploreRun,
                                  index: i,
                                })
                              }
                            >
                              修改
                            </button>
                            <button
                              className="quiet"
                              disabled={busy}
                              onClick={() =>
                                act(() => decision(exploreRun, i, false))
                              }
                            >
                              放下
                            </button>
                          </div>
                        )}
                      </section>
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
          {page === "quests" && (
            <>
              <PageTitle
                eyebrow="LITTLE FIELD NOTES"
                title="体验手记"
                text="留下一点真实的感受。完成或跳过，都只是这次体验的结果。"
              />
              {!quests.length && (
                <Empty
                  title="给自己一次小体验"
                  text="接受探索页中的候选后，体验会出现在这里。"
                  action={
                    <button
                      className="primary"
                      onClick={() => setPage("explore")}
                    >
                      寻找小体验
                    </button>
                  }
                />
              )}
              <div className="quest-list">
                {quests.map((quest) => (
                  <section className="panel" key={quest.id}>
                    <div className="panel-heading">
                      <h3>{quest.title}</h3>
                      <span className="chip">{statusNames[quest.status]}</span>
                    </div>
                    <p>{quest.description}</p>
                    <ProposalFacts proposal={quest} />
                    <ol>
                      {quest.steps.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                    <p className="soft-note">{quest.rationale}</p>
                    {quest.status === "accepted" ? (
                      <div className="button-row">
                        <button
                          className="primary"
                          disabled={busy}
                          onClick={() => {
                            setFeedbackQuest(quest);
                            setFeedback("");
                            setLiked("");
                            setDisliked("");
                            setOutcome("completed");
                          }}
                        >
                          记录体验感受
                        </button>
                        <button
                          className="quiet"
                          onClick={() =>
                            setEditingProposal({ proposal: quest, quest })
                          }
                        >
                          修改体验
                        </button>
                      </div>
                    ) : (
                      <div className="reflection">
                        <strong>你的真实反馈</strong>
                        <p>
                          {quest.reflection?.user_feedback ||
                            "没有填写文字反馈。"}
                        </p>
                        <p>
                          喜欢：
                          {quest.reflection?.liked_aspects.join("、") ||
                            "未填写"}{" "}
                          · 不喜欢：
                          {quest.reflection?.disliked_aspects.join("、") ||
                            "未填写"}
                        </p>
                      </div>
                    )}
                  </section>
                ))}
              </div>
            </>
          )}
          {page === "runs" && (
            <>
              <PageTitle
                eyebrow="VISIBLE AGENT STEPS"
                title="Agent 足迹"
                text="查看实际执行的节点、工具、耗时和错误。这里只记录可审计步骤，不保存隐藏推理。"
              />
              <div className="runs-layout">
                <div className="run-list">
                  {runs.map((run) => (
                    <button
                      className={
                        selectedRun?.run_id === run.run_id ? "selected" : ""
                      }
                      key={run.run_id}
                      onClick={() => setSelectedRun(run)}
                    >
                      <span className="chip">
                        {run.mode === "mock" ? "Mock" : "模型"}
                      </span>
                      <strong>{run.summary || run.request_type}</strong>
                      <small>
                        {statusNames[run.status]} ·{" "}
                        {new Date(run.started_at).toLocaleString("zh-CN")}
                      </small>
                    </button>
                  ))}
                </div>
                <section className="panel run-detail">
                  {selectedRun ? (
                    <>
                      <div className="panel-heading">
                        <h3>运行详情</h3>
                        <span className="chip">
                          {statusNames[selectedRun.status]}
                        </span>
                      </div>
                      <p className="mono">{selectedRun.run_id}</p>
                      <p>
                        {selectedRun.model_name} ·{" "}
                        {selectedRun.elapsed_ms ?? "—"} ms
                      </p>
                      {selectedRun.error_type && (
                        <p className="alert">{selectedRun.error_type}</p>
                      )}
                      <ol className="timeline">
                        {selectedRun.events.map((event, i) => (
                          <li key={i}>
                            <span
                              className={
                                event.status === "succeeded"
                                  ? "step-dot"
                                  : "step-dot failed"
                              }
                            />
                            <div>
                              <small>
                                {event.kind === "tool" ? "工具" : "节点"}
                              </small>
                              <strong>{event.name}</strong>
                            </div>
                            <span>
                              {statusNames[event.status]}
                              <small>{event.elapsed_ms} ms</small>
                            </span>
                          </li>
                        ))}
                      </ol>
                      {selectedRun.status === "failed" &&
                        selectedRun.request_type !== "reflection" && (
                          <button
                            className="secondary"
                            disabled={busy}
                            onClick={() =>
                              act(async () => {
                                const run = await api<Run>(
                                  "/agent/runs/" +
                                    selectedRun.run_id +
                                    "/retry",
                                  "POST",
                                );
                                setSelectedRun(run);
                                if (run.request_type === "collect")
                                  setDraftRun(run);
                                else setExploreRun(run);
                              })
                            }
                          >
                            重试生成
                          </button>
                        )}
                      {selectedRun.status === "awaiting_decision" && (
                        <button
                          className="primary"
                          onClick={() => {
                            if (selectedRun.request_type === "collect") {
                              setDraftRun(selectedRun);
                              setPage("collect");
                            } else {
                              setExploreRun(selectedRun);
                              setPage("explore");
                            }
                          }}
                        >
                          打开待确认结果
                        </button>
                      )}
                      <details>
                        <summary>结构化状态与验证结果</summary>
                        <pre>{JSON.stringify(selectedRun.state, null, 2)}</pre>
                      </details>
                    </>
                  ) : (
                    <Empty
                      title="每一步，都可以查看"
                      text="选择左侧运行记录查看详情。"
                    />
                  )}
                </section>
              </div>
            </>
          )}
          {page === "preferences" && (
            <>
              <PageTitle
                eyebrow="YOUR OWN PACE"
                title="按你的节奏探索"
                text="明确偏好由你设置。反馈带来的候选摘要，只有在你确认后才会成为明确偏好。"
              />
              <section className="panel">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    act(async () => {
                      await api("/preferences", "PUT", preferences.explicit);
                      setNotice("明确偏好已保存。");
                    });
                  }}
                >
                  <div className="field-grid">
                    <label className="wide">
                      兴趣类别（可选，用于候选排序）
                      <ListInput
                        label="兴趣类别（可选）"
                        value={preferences.explicit.categories}
                        onChange={(categories) =>
                          setPreferences({
                            ...preferences,
                            explicit: { ...preferences.explicit, categories },
                          })
                        }
                      />
                    </label>
                    <label>
                      最短时间（分钟，必填）
                      <input
                        required
                        type="number"
                        min={1}
                        max={1440}
                        aria-label="最短时间（分钟，必填）"
                        aria-describedby="preferences-time-hint"
                        value={preferences.explicit.min_minutes}
                        onChange={(e) =>
                          setPreferences({
                            ...preferences,
                            explicit: {
                              ...preferences.explicit,
                              min_minutes: Number(e.target.value),
                            },
                          })
                        }
                      />
                      <span className="field-hint" id="preferences-time-hint">
                        每次体验的时间范围，最长不能小于最短。
                      </span>
                    </label>
                    <label>
                      最长时间（分钟，必填）
                      <input
                        required
                        type="number"
                        min={1}
                        max={1440}
                        aria-describedby="preferences-time-hint"
                        value={preferences.explicit.max_minutes}
                        onChange={(e) =>
                          setPreferences({
                            ...preferences,
                            explicit: {
                              ...preferences.explicit,
                              max_minutes: Number(e.target.value),
                            },
                          })
                        }
                      />
                    </label>
                    <label>
                      预算上限（元，可选）
                      <input
                        type="number"
                        min={0}
                        max={100000}
                        step="0.01"
                        aria-label="预算上限（元，可选）"
                        aria-describedby="preferences-budget-hint"
                        value={preferences.explicit.max_budget ?? ""}
                        onChange={(e) =>
                          setPreferences({
                            ...preferences,
                            explicit: {
                              ...preferences.explicit,
                              max_budget: numeric(e.target.value),
                            },
                          })
                        }
                      />
                      <span className="field-hint" id="preferences-budget-hint">
                        留空不额外限制；0 元仅限无需花费的体验。
                      </span>
                    </label>
                    <label>
                      精力偏好（可选）
                      <select
                        aria-label="精力偏好（可选）"
                        aria-describedby="preferences-energy-hint"
                        value={preferences.explicit.energy_level || ""}
                        onChange={(e) =>
                          setPreferences({
                            ...preferences,
                            explicit: {
                              ...preferences.explicit,
                              energy_level: (e.target.value as Energy) || null,
                            },
                          })
                        }
                      >
                        <option value="">未设置（不额外限制）</option>
                        {Object.entries(energyNames).map(([k, v]) => (
                          <option key={k} value={k}>
                            {v}
                          </option>
                        ))}
                      </select>
                      <span className="field-hint" id="preferences-energy-hint">
                        所需精力上限；未设置不额外限制，也不代表低精力。
                      </span>
                    </label>
                    <label className="wide">
                      明确约束（可选）
                      <ListInput
                        label="明确约束（可选）"
                        describedBy="preferences-constraints-hint"
                        value={preferences.explicit.constraints}
                        onChange={(constraints) =>
                          setPreferences({
                            ...preferences,
                            explicit: { ...preferences.explicit, constraints },
                          })
                        }
                        placeholder="仅室内，不购买，不外出"
                      />
                      <span
                        className="field-hint"
                        id="preferences-constraints-hint"
                      >
                        支持“仅室内、不购买、不外出”；其他约束需澄清。
                      </span>
                    </label>
                  </div>
                  <details className="form-help">
                    <summary>查看偏好填写规则</summary>
                    <ul>
                      <li>
                        时间为 1–1440 分钟，预算为 0–100000
                        元；探索时仍需符合偏好时间范围，本次可用时间不足时会要求澄清。
                      </li>
                      <li>
                        本次探索与偏好同时设置时，时间、预算、精力均取更严格的上限；预算均留空时不额外限制。有预算上限时，未知成本无法通过检查。
                      </li>
                      <li>
                        约束请按“仅室内”“不购买”“不外出”原词填写，目前只支持免费的室内文字记录步骤；其他约束尚不能自动验证。
                      </li>
                      <li>
                        兴趣类别最多 30 项，每项不超过 80 字；明确约束最多 20
                        项。列表支持中英文逗号及换行解析，单行框建议用逗号。
                      </li>
                    </ul>
                  </details>
                  <div className="button-row">
                    <button className="primary" disabled={busy}>
                      保存明确偏好
                    </button>
                    <button
                      type="button"
                      className="danger quiet"
                      disabled={busy}
                      onClick={() =>
                        act(async () => {
                          await api("/preferences", "DELETE");
                          setNotice("偏好数据已清空。");
                        })
                      }
                    >
                      删除全部偏好数据
                    </button>
                  </div>
                </form>
              </section>
              <h2 className="spaced-title">来自反馈的候选偏好</h2>
              {!preferences.candidates.length && (
                <p className="muted">
                  暂无候选。体验反馈中明确填写的喜欢，会作为待确认摘要出现在这里。
                </p>
              )}
              {preferences.candidates.map((c) => (
                <section key={c.id} className="panel candidate">
                  <div>
                    <span className="chip">未确认</span>
                    <p>{c.summary}</p>
                    <small>反馈依据：{c.reflection_id}</small>
                  </div>
                  <div className="button-row">
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() =>
                        act(async () => {
                          await api(
                            "/preferences/candidates/" +
                              encodeURIComponent(c.id) +
                              "/confirm",
                            "POST",
                          );
                          setNotice("已加入明确兴趣类别，可继续编辑。");
                        })
                      }
                    >
                      确认加入类别
                    </button>
                    <button
                      className="quiet"
                      disabled={busy}
                      onClick={() =>
                        act(async () => {
                          await api(
                            "/preferences/candidates/" +
                              encodeURIComponent(c.id),
                            "DELETE",
                          );
                        })
                      }
                    >
                      删除
                    </button>
                  </div>
                </section>
              ))}
            </>
          )}
        </div>
      </main>
      {selectedStar && (
        <Modal
          error={error}
          title="编辑兴趣星星"
          onClose={() => setSelectedStar(null)}
        >
          <StarEditor
            key={selectedStar.id}
            initial={
              Object.fromEntries(
                Object.entries(selectedStar).filter(
                  ([key]) => !["id", "created_at", "updated_at"].includes(key),
                ),
              ) as unknown as StarInput
            }
            disabled={busy}
            onSave={(v) =>
              act(async () => {
                await api("/stars/" + selectedStar.id, "PUT", v);
                setSelectedStar(null);
                setNotice("星星已更新。");
              })
            }
          />
          <button
            className="danger text-button"
            disabled={busy}
            onClick={() => {
              if (
                window.confirm(
                  "确定删除这颗星星？已被探索引用的星星需保留，可改为归档。",
                )
              )
                act(async () => {
                  await api("/stars/" + selectedStar.id, "DELETE");
                  setSelectedStar(null);
                  setNotice("星星已删除。");
                });
            }}
          >
            删除这颗星星
          </button>
        </Modal>
      )}
      {editingProposal && (
        <Modal
          error={error}
          title="修改微型探索"
          onClose={() => setEditingProposal(null)}
        >
          <ProposalEditor
            initial={editingProposal.proposal}
            disabled={busy}
            onSave={(v) =>
              act(async () => {
                if (editingProposal.quest) {
                  await api("/quests/" + editingProposal.quest.id, "PUT", v);
                  setEditingProposal(null);
                  setNotice("体验已更新。");
                } else if (editingProposal.run)
                  await decision(
                    editingProposal.run,
                    editingProposal.index || 0,
                    true,
                    v,
                  );
              })
            }
          />
        </Modal>
      )}
      {feedbackQuest && (
        <Modal
          error={error}
          title="记录这次体验"
          onClose={() => setFeedbackQuest(null)}
        >
          <p>{feedbackQuest.title}</p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              act(async () => {
                await api(
                  "/quests/" + feedbackQuest.id + "/reflections",
                  "POST",
                  {
                    outcome,
                    user_feedback: feedback,
                    liked_aspects: split(liked),
                    disliked_aspects: split(disliked),
                  },
                  crypto.randomUUID(),
                );
                setFeedbackQuest(null);
                setNotice("真实感受已保存。跳过也没关系。");
              });
            }}
          >
            <label>
              这次的结果
              <select
                value={outcome}
                onChange={(e) => setOutcome(e.target.value as typeof outcome)}
              >
                <option value="completed">完成了</option>
                <option value="skipped">这次没有执行</option>
              </select>
            </label>
            <label>
              {outcome === "skipped"
                ? "没有执行的原因（可选）"
                : "感受（可选）"}
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
              />
            </label>
            <label>
              喜欢的方面（可选，最多 20 项，每项不超过 80 字）
              <input
                aria-describedby="feedback-list-hint"
                value={liked}
                onChange={(e) => setLiked(e.target.value)}
              />
            </label>
            <label>
              不喜欢的方面（可选，最多 20 项，每项不超过 80 字）
              <input
                aria-describedby="feedback-list-hint"
                value={disliked}
                onChange={(e) => setDisliked(e.target.value)}
              />
            </label>
            <p className="field-hint" id="feedback-list-hint">
              支持中英文逗号或换行分隔；单行输入建议用逗号。
            </p>
            <p className="muted">
              喜欢的方面会形成候选摘要，不会自动成为用户事实。
            </p>
            <button className="primary" disabled={busy}>
              保存真实反馈
            </button>
          </form>
        </Modal>
      )}
    </div>
  );
}
function UsageGuide({ mock }: { mock: boolean | null }) {
  return (
    <details className="usage-guide">
      <summary>星屿怎么使用</summary>
      <ol>
        <li>
          <strong>收集兴趣：</strong>
          星星是你收藏的兴趣或好奇，先写下一段原始想法。
        </li>
        <li>
          <strong>编辑并确认：</strong>
          整理先生成草稿，检查、修改后确认，才加入正式档案；也可以放下。
        </li>
        <li>
          <strong>微型探索：</strong>
          从未归档的星星和明确偏好出发，寻找小体验；候选需要你接受。
        </li>
        <li>
          <strong>记录真实感受：</strong>
          接受体验后到“体验手记”，记录完成或没有执行的感受。
        </li>
      </ol>
      <p>
        {mock === null
          ? "连接后可查看当前生成模式。"
          : mock
            ? "当前为 Mock 模式：内容由规则模拟生成，不代表真实大模型理解。"
            : "当前为模型模式：整理和候选仍需你检查、确认。"}
      </p>
    </details>
  );
}
function SavedStarNextStep({
  onNavigate,
}: {
  onNavigate: (page: "archive" | "explore") => void;
}) {
  return (
    <div className="next-step" role="region" aria-label="保存后的下一步">
      <p>接下来，可以查看星星档案，或从已收藏的兴趣开始微型探索。</p>
      <div className="button-row">
        <button className="secondary" onClick={() => onNavigate("archive")}>
          查看星星档案
        </button>
        <button className="text-button" onClick={() => onNavigate("explore")}>
          开始微型探索
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
function PageTitle({
  eyebrow,
  title,
  text,
}: {
  eyebrow: string;
  title: string;
  text: string;
}) {
  return (
    <div className="page-title">
      <span className="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p>{text}</p>
    </div>
  );
}
function ResultHeading({
  run,
  onView,
  title = "待确认结果",
}: {
  run: Run;
  onView: () => void;
  title?: string;
}) {
  return (
    <div className="panel-heading">
      <h3>
        <Sparkles size={18} />
        {title}
        <span className="chip">
          {run.mode === "mock" ? "Mock · 规则生成" : "模型生成"}
        </span>
      </h3>
      <button className="text-button" onClick={onView}>
        查看 Agent 足迹
        <ArrowUpRight size={16} />
      </button>
    </div>
  );
}
function Modal({
  title,
  onClose,
  children,
  error,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  error?: string;
}) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    ref.current
      ?.querySelector<HTMLElement>("input, textarea, select, button")
      ?.focus();
    return () => previous?.focus();
  }, []);
  return (
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        ref={ref}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
          if (e.key === "Tab") {
            const items = Array.from(
              ref.current?.querySelectorAll<HTMLElement>(
                "button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled)",
              ) || [],
            );
            if (e.shiftKey && document.activeElement === items[0]) {
              e.preventDefault();
              items.at(-1)?.focus();
            } else if (!e.shiftKey && document.activeElement === items.at(-1)) {
              e.preventDefault();
              items[0]?.focus();
            }
          }
        }}
      >
        <div className="panel-heading">
          <h2>{title}</h2>
          <button className="quiet" aria-label="关闭弹窗" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        {error && (
          <div className="alert" role="alert">
            {error}
          </div>
        )}
        {children}
      </section>
    </div>
  );
}
