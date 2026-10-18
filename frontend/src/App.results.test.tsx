import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { api, ApiError } from "./api";
import type { Proposal, Quest, Relation, Run, Star, StarInput } from "./types";
vi.mock("./api", async (original) => ({
  ...(await original<typeof import("./api")>()),
  api: vi.fn(),
}));
const mockedApi = vi.mocked(api);
const star: Star = {
  id: "saved-star",
  title: "海洋",
  original_text: "海洋",
  description: "深海",
  category: "自然",
  tags: [],
  interest_reason: null,
  source_type: "paste",
  source_reference: null,
  estimated_minutes: null,
  estimated_budget: null,
  energy_level: null,
  status: "collected",
  created_at: "2026-10-18",
  updated_at: "2026-10-18",
};
const proposal: Proposal = {
  title: "小体验一",
  description: "写下问题",
  estimated_minutes: 5,
  estimated_budget: 0,
  energy_level: "low",
  steps: ["记录"],
  based_on_star_ids: [star.id],
  rationale: "依据海洋",
  uncertainties: [],
};
function run(type: "collect" | "explore" = "collect", id = "new-run"): Run {
  return {
    run_id: id,
    request_type: type,
    status: "awaiting_decision",
    mode: "mock",
    model_name: "mock",
    started_at: "2026-10-18T00:00:00Z",
    elapsed_ms: 1,
    summary: id,
    error_type: null,
    events: [],
    decisions: {},
    state: {
      request: { request_type: type, text: "海洋" },
      ...(type === "collect"
        ? { draft: { draft: star, missing_fields: [], questions: [] } }
        : { proposals: [proposal, { ...proposal, title: "小体验二" }] }),
    },
  };
}
function server(initial: Run[] = [], initialStars: Star[] = []) {
  const state = {
    runs: initial,
    stars: initialStars,
    quests: [] as Quest[],
    generation: run(),
    missingId: false,
    missingTarget: false,
    editFailure: false,
    deleteFailure: false,
    relations: [] as Relation[],
  };
  mockedApi.mockImplementation(async (path, method = "GET", body) => {
    if (path === "/health") return { mock_mode: true };
    if (path === "/stats")
      return {
        stars: state.stars.length,
        quests: state.quests.length,
        completed: 0,
        categories: [],
      };
    if (path === "/preferences")
      return {
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
    if (path === "/stars" && method === "POST") {
      state.stars = [star];
      return state.missingId ? { ...star, id: undefined } : star;
    }
    if (path.startsWith("/stars/")) {
      const target = state.stars.find((s) => path.endsWith("/" + s.id));
      if (!target || state.missingTarget)
        throw new Error("星星暂未找到，请刷新后重试");
      if (method === "PUT") {
        if (state.editFailure) throw new Error("修改暂未保存，请重试");
        const input = body as StarInput;
        const updated = {
          ...target,
          ...input,
          title: input.title.trim(),
          updated_at: "2026-10-18T12:00:00Z",
        };
        state.stars = state.stars.map((item) =>
          item.id === target.id ? updated : item,
        );
        return updated;
      }
      if (method === "DELETE") {
        if (state.deleteFailure) throw new Error("已被体验引用，请改为归档");
        state.stars = state.stars.filter((item) => item.id !== target.id);
        return undefined;
      }
      return target;
    }
    if (path.startsWith("/stars")) return state.stars;
    if (path === "/relations") return state.relations;
    if (path === "/quests") return state.missingTarget ? [] : state.quests;
    if (path === "/agent/runs") {
      if (method === "POST") {
        state.runs = [state.generation, ...state.runs];
        return state.generation;
      }
      return state.runs;
    }
    const current = state.runs.find((r) => path.includes("/" + r.run_id));
    if (path.endsWith("/retry")) {
      state.runs = [state.generation, ...state.runs];
      return state.generation;
    }
    if (path.endsWith("/decision") && current) {
      const { approved, index } = body as { approved: boolean; index: number };
      const id = current.request_type === "collect" ? "star" : String(index);
      const decision = {
        approved,
        ...(approved && !state.missingId
          ? current.request_type === "collect"
            ? { star_id: star.id }
            : { quest_id: "quest-" + index }
          : {}),
      };
      current.decisions = { ...current.decisions, [id]: decision };
      if (approved && !state.missingId) {
        if (current.request_type === "collect") state.stars = [star];
        else
          state.quests.push({
            ...current.state.proposals![index],
            id: "quest-" + index,
            status: "accepted",
            reflection: null,
          });
      }
      if (
        current.request_type === "collect" ||
        Object.keys(current.decisions).length ===
          current.state.proposals?.length
      )
        current.status = "decided";
      return decision;
    }
    if (current) return current;
    return [];
  });
  return state;
}
async function nav(name: string) {
  fireEvent.click(
    within(screen.getByRole("navigation", { name: "主导航" })).getByRole(
      "button",
      { name: new RegExp("^" + name) },
    ),
  );
}
async function ready() {
  await screen.findByText("Mock 模式 · 规则生成");
}
async function generate(type: "collect" | "explore" = "collect") {
  await nav(type === "collect" ? "收集星星" : "微型探索");
  fireEvent.change(
    screen.getByLabelText(
      type === "collect" ? "你最近对什么感到好奇？" : "今天想靠近哪份好奇？",
    ),
    { target: { value: "海洋" } },
  );
  fireEvent.click(
    screen.getByRole("button", {
      name: type === "collect" ? "整理成草稿" : "寻找小体验",
    }),
  );
}
async function idle() {
  await waitFor(() =>
    expect(screen.queryByText("正在处理，请稍候…")).not.toBeInTheDocument(),
  );
}
async function selectRun(id: string) {
  await nav("Agent 足迹");
  fireEvent.click(screen.getByRole("button", { name: new RegExp(id) }));
  await idle();
}
beforeEach(() => {
  vi.mocked(Element.prototype.scrollIntoView).mockClear();
});
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
  vi.unstubAllGlobals();
});
describe("UX-002 真实结果衔接", () => {
  it.each([false, true])("新草稿仅定位一次，减少动画=%s", async (reduced) => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn(() => ({ matches: reduced })),
    );
    server();
    render(<App />);
    await ready();
    await generate();
    const result = await screen.findByRole("region", { name: "本次收集结果" });
    await waitFor(() => expect(result).toHaveFocus());
    expect(result).toHaveAttribute("id", "collect-result-new-run");
    expect(result).toHaveAttribute("tabindex", "-1");
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledExactlyOnceWith({
      behavior: reduced ? "auto" : "smooth",
      block: "start",
    });
    await idle();
    fireEvent.click(screen.getByRole("button", { name: "刷新后端数据" }));
    await idle();
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledTimes(1);
  });
  it.each([false, true])(
    "候选与仅澄清都定位真实结果，澄清=%s",
    async (clarification) => {
      const s = server();
      s.generation = run("explore");
      if (clarification)
        s.generation.state = {
          request: s.generation.state.request,
          questions: ["请补充兴趣"],
        };
      render(<App />);
      await ready();
      await generate("explore");
      const result = await screen.findByRole("region", {
        name: "本次探索结果",
      });
      await waitFor(() => expect(result).toHaveFocus());
      expect(
        within(result).getByText(clarification ? "请补充兴趣" : "小体验一"),
      ).toBeVisible();
    },
  );
  it("重复生成只定位最新运行，失败不会定位旧结果", async () => {
    const s = server();
    render(<App />);
    await ready();
    await generate();
    await idle();
    s.generation = run("collect", "latest-run");
    await generate();
    await idle();
    expect(
      screen.getByRole("region", { name: "本次收集结果" }),
    ).toHaveAttribute("id", "collect-result-latest-run");
    const original = mockedApi.getMockImplementation()!;
    mockedApi.mockImplementation(async (path, method, ...rest) => {
      if (path === "/agent/runs" && method === "POST")
        throw new Error("生成失败");
      return original(path, method, ...rest);
    });
    await generate();
    await screen.findByRole("alert");
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledTimes(2);
    expect(
      screen.queryByRole("region", { name: "本次收集结果" }),
    ).not.toBeInTheDocument();
  });
  it.each(["切页", "打开指南"])(
    "异步完成后%s不抢视口和焦点",
    async (action) => {
      const s = server();
      const original = mockedApi.getMockImplementation()!;
      let finish!: (r: Run) => void;
      mockedApi.mockImplementation(async (path, method, ...rest) =>
        path === "/agent/runs" && method === "POST"
          ? new Promise<Run>((resolve) => {
              finish = resolve;
            })
          : original(path, method, ...rest),
      );
      render(<App />);
      await ready();
      await generate();
      if (action === "切页") {
        await nav("我的偏好");
        await nav("收集星星");
      } else fireEvent.click(screen.getByRole("button", { name: "使用指南" }));
      await act(async () => finish(s.generation));
      await idle();
      expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
      if (action === "打开指南")
        expect(screen.getByRole("button", { name: "关闭弹窗" })).toHaveFocus();
    },
  );
  it("保存后的 Star ID 只读导航，清除过滤并打开正确弹窗", async () => {
    server();
    render(<App />);
    await ready();
    await nav("星星档案");
    fireEvent.change(screen.getByLabelText("搜索星星"), {
      target: { value: "不存在" },
    });
    fireEvent.change(screen.getByLabelText("星星状态筛选"), {
      target: { value: "archived" },
    });
    fireEvent.click(screen.getByRole("button", { name: "搜索" }));
    await idle();
    await generate();
    await idle();
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    await idle();
    fireEvent.click(screen.getByRole("button", { name: "查看这颗星星" }));
    const dialog = await screen.findByRole("dialog");
    await idle();
    expect(within(dialog).getByRole("heading", { name: "海洋" })).toBeVisible();
    expect(within(dialog).queryByLabelText("标题")).not.toBeInTheDocument();
    expect(screen.getByLabelText("搜索星星")).toHaveValue("");
    expect(screen.getByLabelText("星星状态筛选")).toHaveValue("");
    expect(mockedApi).toHaveBeenCalledWith("/stars/saved-star");
    fireEvent.click(within(dialog).getByRole("button", { name: "关闭弹窗" }));
    expect(document.getElementById("star-card-saved-star")).toHaveFocus();
    expect(
      mockedApi.mock.calls.filter(([, method]) => method === "POST"),
    ).toHaveLength(2);
  });
  it.each([true, false])(
    "手动保存只在有实际 id 时给精确入口，缺少=%s",
    async (missing) => {
      const s = server();
      s.missingId = missing;
      render(<App />);
      await ready();
      await nav("收集星星");
      fireEvent.click(screen.getByRole("button", { name: "手动填写" }));
      fireEvent.change(screen.getByLabelText("标题"), {
        target: { value: "海洋" },
      });
      fireEvent.change(screen.getByLabelText("原始文字"), {
        target: { value: "海洋" },
      });
      fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
      await idle();
      expect(!!screen.queryByRole("button", { name: "查看这颗星星" })).toBe(
        !missing,
      );
      if (!missing) {
        fireEvent.click(screen.getByRole("button", { name: "查看这颗星星" }));
        await screen.findByRole("dialog");
      }
    },
  );
  it("多个候选各自使用 quest_id，导航不打开反馈也不重放审批", async () => {
    const s = server();
    s.generation = run("explore");
    render(<App />);
    await ready();
    await generate("explore");
    await idle();
    const result = screen.getByRole("region", { name: "本次探索结果" });
    for (let index = 0; index < 2; index++) {
      fireEvent.click(
        within(result).getAllByRole("button", { name: "接受这个体验" })[0],
      );
      await idle();
    }
    for (const index of [1, 0, 1]) {
      fireEvent.click(
        within(
          screen.getByRole("region", { name: "本次探索结果" }),
        ).getAllByRole("button", { name: "查看这次体验" })[index],
      );
      await idle();
      const target = screen.getByRole("region", {
        name: index ? "小体验二" : "小体验一",
      });
      expect(target).toHaveAttribute("id", "quest-quest-" + index);
      expect(target).toHaveFocus();
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      expect(
        within(target).getByRole("button", { name: "记录体验感受" }),
      ).toBeVisible();
      await nav("微型探索");
    }
    expect(
      mockedApi.mock.calls.filter(
        ([path, method]) => path.endsWith("/decision") && method === "POST",
      ),
    ).toHaveLength(2);
    expect(
      mockedApi.mock.calls.some(([path]) => path.endsWith("/reflections")),
    ).toBe(false);
  });
  it.each(["拒绝", "缺少ID", "目标不存在"])(
    "候选%s不显示假入口或打开其他体验",
    async (scenario) => {
      const s = server();
      s.generation = run("explore");
      s.missingId = scenario === "缺少ID";
      render(<App />);
      await ready();
      await generate("explore");
      await idle();
      fireEvent.click(
        screen.getAllByRole("button", {
          name: scenario === "拒绝" ? "放下" : "接受这个体验",
        })[0],
      );
      await idle();
      if (scenario === "目标不存在") {
        s.missingTarget = true;
        fireEvent.click(screen.getByRole("button", { name: "查看这次体验" }));
        expect(await screen.findByRole("alert")).toHaveTextContent(
          "暂未找到这次体验",
        );
        expect(
          screen.queryByRole("region", { name: "小体验一" }),
        ).not.toBeInTheDocument();
        s.missingTarget = false;
        fireEvent.click(screen.getByRole("button", { name: "查看这次体验" }));
        expect(
          await screen.findByRole("region", { name: "小体验一" }),
        ).toBeVisible();
      } else
        expect(
          screen.queryByRole("button", { name: "查看这次体验" }),
        ).not.toBeInTheDocument();
    },
  );
  it("Star 缺失时保留可重试入口，不打开错误星星", async () => {
    const s = server();
    render(<App />);
    await ready();
    await generate();
    await idle();
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    await idle();
    s.missingTarget = true;
    fireEvent.click(screen.getByRole("button", { name: "查看这颗星星" }));
    await screen.findByRole("alert");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    s.missingTarget = false;
    fireEvent.click(screen.getByRole("button", { name: "查看这颗星星" }));
    await screen.findByRole("dialog");
  });
  it("生成失败显示真实 run_id；重试新运行并保留旧失败", async () => {
    const failed = {
      ...run("collect", "failed-run"),
      status: "failed",
      error_type: "timeout",
    };
    const s = server([failed]);
    const original = mockedApi.getMockImplementation()!;
    mockedApi.mockImplementation(async (path, method, ...rest) => {
      if (path === "/agent/runs" && method === "POST")
        throw new ApiError("生成失败", failed.run_id);
      return original(path, method, ...rest);
    });
    render(<App />);
    await ready();
    await generate();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("failed-run");
    expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
    fireEvent.click(
      within(alert).getByRole("button", { name: /查看运行详情/ }),
    );
    await idle();
    fireEvent.click(screen.getByRole("button", { name: "重试生成" }));
    await idle();
    expect(
      screen.getByRole("region", { name: "本次收集结果" }),
    ).toHaveAttribute("id", "collect-result-new-run");
    expect(s.runs.find((r) => r.run_id === "failed-run")?.status).toBe(
      "failed",
    );
    expect(mockedApi.mock.calls.some(([p]) => p.endsWith("/decision"))).toBe(
      false,
    );
  });
  it.each(["running", "decided", "reflection", "failed-with-decision"])(
    "%s 不提供生成重试",
    async (status) => {
      const current = run("collect", "protected-run");
      current.status =
        status === "reflection" || status === "failed-with-decision"
          ? "failed"
          : status;
      if (status === "reflection") current.request_type = "reflection";
      if (status === "failed-with-decision")
        current.decisions = { star: { approved: true, star_id: star.id } };
      server([current]);
      render(<App />);
      await ready();
      await selectRun("protected-run");
      expect(
        screen.queryByRole("button", { name: "重试生成" }),
      ).not.toBeInTheDocument();
    },
  );
  it("点击重试前再次读服务器，running 保护期不发 POST", async () => {
    const current = { ...run("collect", "changing-run"), status: "failed" };
    server([current]);
    render(<App />);
    await ready();
    await selectRun("changing-run");
    current.status = "running";
    fireEvent.click(screen.getByRole("button", { name: "重试生成" }));
    await screen.findByRole("alert");
    expect(mockedApi.mock.calls.some(([p]) => p.endsWith("/retry"))).toBe(
      false,
    );
  });
  it.each(["collect", "explore"] as const)(
    "刷新后恢复 %s 的真实待确认运行并定位",
    async (type) => {
      const pending = run(type, "pending-run");
      server([pending]);
      render(<App />);
      await ready();
      await selectRun("pending-run");
      fireEvent.click(screen.getByRole("button", { name: "打开待确认结果" }));
      await idle();
      const result = screen.getByRole("region", {
        name: type === "collect" ? "本次收集结果" : "本次探索结果",
      });
      expect(result).toHaveAttribute("id", type + "-result-pending-run");
      expect(result).toHaveFocus();
      expect(
        mockedApi.mock.calls.filter(([, method]) => method === "POST"),
      ).toHaveLength(0);
    },
  );
  it("无有效内容或已决定的运行没有待确认入口", async () => {
    const empty = run("collect", "empty-run");
    empty.state = { request: empty.state.request };
    const decided = { ...run("collect", "decided-run"), status: "decided" };
    server([empty, decided]);
    render(<App />);
    await ready();
    for (const id of ["empty-run", "decided-run"]) {
      await selectRun(id);
      expect(
        screen.queryByRole("button", { name: "打开待确认结果" }),
      ).not.toBeInTheDocument();
    }
  });
  it("普通刷新按服务器撤销已过期的待审批入口", async () => {
    const current = run("collect", "pending-run");
    const s = server([current]);
    render(<App />);
    await ready();
    await selectRun("pending-run");
    s.runs = [
      {
        ...current,
        status: "decided",
        decisions: { star: { approved: false } },
      },
    ];
    fireEvent.click(screen.getByRole("button", { name: "刷新后端数据" }));
    await idle();
    expect(
      screen.queryByRole("button", { name: "打开待确认结果" }),
    ).not.toBeInTheDocument();
  });
  it("当前运行离开最近列表后，刷新仍按 ID 读取真实状态", async () => {
    const current = run("collect", "older-run");
    const s = server([current]);
    render(<App />);
    await ready();
    await selectRun("older-run");
    const original = mockedApi.getMockImplementation()!;
    mockedApi.mockImplementation(async (path, method, ...rest) =>
      path === "/agent/runs" && (!method || method === "GET")
        ? []
        : original(path, method, ...rest),
    );
    s.runs = [
      {
        ...current,
        status: "decided",
        decisions: { star: { approved: false } },
      },
    ];
    fireEvent.click(screen.getByRole("button", { name: "刷新后端数据" }));
    await idle();
    expect(
      screen.queryByRole("button", { name: "打开待确认结果" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("older-run")).toBeVisible();
  });
  it("待确认入口在点击时再次核验，已决定就不恢复旧草稿", async () => {
    const current = run("collect", "changing-pending");
    const s = server([current]);
    render(<App />);
    await ready();
    await selectRun("changing-pending");
    s.runs = [
      {
        ...current,
        status: "decided",
        decisions: { star: { approved: false } },
      },
    ];
    fireEvent.click(screen.getByRole("button", { name: "打开待确认结果" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "已无待确认结果",
    );
    expect(
      screen.queryByRole("region", { name: "本次收集结果" }),
    ).not.toBeInTheDocument();
  });
  it("草稿审批缺少 star_id 不报保存成功或给精确入口", async () => {
    const s = server();
    s.missingId = true;
    render(<App />);
    await ready();
    await generate();
    await idle();
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    await idle();
    expect(
      screen.queryByRole("button", { name: "查看这颗星星" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("保存结果尚未确认，请刷新档案查看。"),
    ).toBeVisible();
    expect(
      screen.queryByText("这份好奇已加入星星档案。"),
    ).not.toBeInTheDocument();
  });
  it("保存已返回但刷新未完成时禁用下一步，刷新结束后点击有效", async () => {
    server();
    const original = mockedApi.getMockImplementation()!;
    let pause = false;
    let finish!: () => void;
    const gate = new Promise<void>((resolve) => {
      finish = resolve;
    });
    mockedApi.mockImplementation(async (path, method, ...rest) => {
      if (path === "/stats" && pause) await gate;
      return original(path, method, ...rest);
    });
    render(<App />);
    await ready();
    await generate();
    await idle();
    pause = true;
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    const next = await screen.findByRole("button", { name: "查看这颗星星" });
    expect(next).toBeDisabled();
    fireEvent.click(next);
    expect(mockedApi.mock.calls.some(([p]) => p === "/stars/saved-star")).toBe(
      false,
    );
    await act(async () => finish());
    await idle();
    expect(next).toBeEnabled();
    fireEvent.click(next);
    expect(await screen.findByRole("dialog")).toBeVisible();
  });
});

describe("UX-002 星星阅读与明确编辑", () => {
  async function openCard() {
    const card = document.getElementById("star-card-" + star.id)!;
    card.focus();
    fireEvent.click(card);
    return screen.findByRole("dialog", { name: "星星详情" });
  }
  it.each(["首页", "档案", "轨道", "探索引用"])(
    "%s 查看入口统一只读，关闭恢复焦点且不写正式记录",
    async (entry) => {
      const s = server(
        [],
        [star, { ...star, id: "other-star", title: "星空" }],
      );
      s.relations = [
        {
          from_id: star.id,
          to_id: "other-star",
          from_title: "海洋",
          to_title: "星空",
          reasons: ["共同兴趣"],
        },
      ];
      s.generation = run("explore");
      render(<App />);
      await ready();
      let trigger: HTMLElement;
      if (entry === "首页" || entry === "档案") {
        if (entry === "档案") await nav("星星档案");
        trigger = document.getElementById("star-card-" + star.id)!;
      } else if (entry === "轨道") {
        await nav("兴趣轨道");
        trigger = screen.getByRole("button", { name: "海洋" });
      } else {
        await generate("explore");
        await idle();
        trigger = screen.getAllByRole("button", { name: "海洋" })[0];
      }
      trigger.focus();
      fireEvent.click(trigger);
      const dialog = await screen.findByRole("dialog", { name: "星星详情" });
      await idle();
      expect(
        within(dialog).getByRole("heading", { name: "海洋" }),
      ).toBeVisible();
      expect(within(dialog).queryByRole("textbox")).not.toBeInTheDocument();
      expect(
        within(dialog).queryByRole("button", { name: "删除这颗星星" }),
      ).not.toBeInTheDocument();
      fireEvent.click(within(dialog).getByRole("button", { name: "关闭弹窗" }));
      expect(trigger).toHaveFocus();
      expect(
        mockedApi.mock.calls.some(
          ([path, method]) =>
            method === "PUT" ||
            method === "DELETE" ||
            (path === "/stars" && method === "POST") ||
            path.endsWith("/decision"),
        ),
      ).toBe(false);
    },
  );
  it("编辑才出现表单；取消和关闭丢弃草稿，不发生写入", async () => {
    server([], [star]);
    render(<App />);
    await ready();
    await openCard();
    fireEvent.click(screen.getByRole("button", { name: "编辑星星" }));
    expect(screen.getByLabelText("标题")).toHaveFocus();
    fireEvent.change(screen.getByLabelText("标题"), {
      target: { value: "未保存的修改" },
    });
    fireEvent.click(screen.getByRole("button", { name: "取消编辑" }));
    const dialog = screen.getByRole("dialog", { name: "星星详情" });
    expect(within(dialog).getByRole("heading", { name: "海洋" })).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "编辑星星" }));
    expect(screen.getByLabelText("标题")).toHaveValue("海洋");
    fireEvent.change(screen.getByLabelText("标题"), {
      target: { value: "关闭后丢弃" },
    });
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    await openCard();
    fireEvent.click(screen.getByRole("button", { name: "编辑星星" }));
    expect(screen.getByLabelText("标题")).toHaveValue("海洋");
    expect(
      mockedApi.mock.calls.every(([, method]) => !method || method === "GET"),
    ).toBe(true);
  });
  it("异步来源读取使入口失焦后，关闭仍恢复原触发元素", async () => {
    const s = server([], [star]);
    s.relations = [
      {
        from_id: star.id,
        to_id: star.id,
        from_title: "查看来源",
        to_title: "另一端",
        reasons: [],
      },
    ];
    const original = mockedApi.getMockImplementation()!;
    let finish!: () => void;
    const gate = new Promise<void>((resolve) => {
      finish = resolve;
    });
    mockedApi.mockImplementation(async (path, ...rest) => {
      if (path === "/stars/saved-star") await gate;
      return original(path, ...rest);
    });
    render(<App />);
    await ready();
    await nav("兴趣轨道");
    const trigger = screen.getByRole("button", { name: "查看来源" });
    trigger.focus();
    fireEvent.click(trigger);
    trigger.blur();
    await act(async () => finish());
    await idle();
    fireEvent.click(
      within(screen.getByRole("dialog", { name: "星星详情" })).getByRole(
        "button",
        { name: "关闭弹窗" },
      ),
    );
    expect(trigger).toHaveFocus();
  });
  it("保存使用服务端确认内容返回阅读，并保留归档和明确零预算", async () => {
    server([], [star]);
    render(<App />);
    await ready();
    await openCard();
    fireEvent.click(screen.getByRole("button", { name: "编辑星星" }));
    fireEvent.change(screen.getByLabelText("标题"), {
      target: { value: " 更新后的星星 " },
    });
    fireEvent.change(screen.getByLabelText("状态"), {
      target: { value: "archived" },
    });
    fireEvent.change(screen.getByLabelText("预计预算（元，可选）"), {
      target: { value: "0" },
    });
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    const dialog = await screen.findByRole("dialog", { name: "星星详情" });
    await idle();
    expect(
      within(dialog).getByRole("heading", { name: "更新后的星星" }),
    ).toHaveFocus();
    expect(within(dialog).getByText("已归档")).toBeVisible();
    expect(within(dialog).getByText("0 元")).toBeVisible();
    expect(within(dialog).queryByRole("textbox")).not.toBeInTheDocument();
    expect(mockedApi).toHaveBeenCalledWith(
      "/stars/saved-star",
      "PUT",
      expect.objectContaining({
        title: " 更新后的星星 ",
        status: "archived",
        estimated_budget: 0,
      }),
    );
    expect(await screen.findByText("星星已更新。")).toBeVisible();
  });
  it("保存失败保留编辑内容和错误，可重试，不误报成功", async () => {
    const s = server([], [star]);
    s.editFailure = true;
    render(<App />);
    await ready();
    await openCard();
    fireEvent.click(screen.getByRole("button", { name: "编辑星星" }));
    fireEvent.change(screen.getByLabelText("标题"), {
      target: { value: "继续编辑" },
    });
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    const dialog = screen.getByRole("dialog", { name: "编辑兴趣星星" });
    expect(await within(dialog).findByRole("alert")).toHaveTextContent(
      "修改暂未保存",
    );
    await idle();
    expect(within(dialog).getByLabelText("标题")).toHaveValue("继续编辑");
    expect(screen.queryByText("星星已更新。")).not.toBeInTheDocument();
    s.editFailure = false;
    fireEvent.click(
      within(dialog).getByRole("button", { name: "确认保存星星" }),
    );
    expect(
      await within(
        await screen.findByRole("dialog", { name: "星星详情" }),
      ).findByRole("heading", { name: "继续编辑" }),
    ).toBeVisible();
  });
  it.each([false, true])(
    "删除仅在明确编辑中，引用保护失败=%s",
    async (protectedStar) => {
      const s = server([], [star]);
      s.deleteFailure = protectedStar;
      vi.stubGlobal(
        "confirm",
        vi.fn(() => true),
      );
      render(<App />);
      await ready();
      await openCard();
      expect(
        screen.queryByRole("button", { name: "删除这颗星星" }),
      ).not.toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "编辑星星" }));
      fireEvent.click(screen.getByRole("button", { name: "删除这颗星星" }));
      await idle();
      if (protectedStar) {
        expect(
          within(screen.getByRole("dialog")).getByRole("alert"),
        ).toHaveTextContent("请改为归档");
        expect(screen.getByLabelText("状态")).toBeVisible();
      } else expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      expect(
        mockedApi.mock.calls.filter(([, method]) => method === "DELETE"),
      ).toHaveLength(1);
    },
  );
});
