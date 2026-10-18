import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { api } from "./api";
import type { Run, Star, StarInput } from "./types";
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  api: vi.fn(),
}));
const mockedApi = vi.mocked(api);
const pref = {
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
const starInput: StarInput = {
  title: "海洋",
  original_text: "海洋",
  description: "深海发光",
  category: "自然",
  tags: ["海洋"],
  interest_reason: null,
  source_type: "paste",
  source_reference: null,
  estimated_minutes: null,
  estimated_budget: null,
  energy_level: null,
  status: "collected",
};
const savedStar: Star = {
  ...starInput,
  id: "star-1",
  created_at: "2026-10-18T00:00:00Z",
  updated_at: "2026-10-18T00:00:00Z",
};
function backend(
  mock = true,
  maxBudget: number | null = null,
  stars: Star[] = [],
) {
  mockedApi.mockImplementation(async (path) => {
    if (path === "/stars") return stars;
    if (path === "/stats")
      return { stars: stars.length, quests: 0, completed: 0, categories: [] };
    if (path === "/stars/star-1")
      return stars.find((star) => star.id === "star-1");
    if (path === "/health") return { mock_mode: mock };
    if (path === "/preferences")
      return { ...pref, explicit: { ...pref.explicit, max_budget: maxBudget } };
    return [];
  });
}
function collectionBackend(failSave = false) {
  let stars: Star[] = [];
  let generated = false;
  let failGenerate = false;
  let run: Run = {
    run_id: "run-1",
    request_type: "collect",
    status: "awaiting_decision",
    mode: "mock",
    model_name: "mock",
    started_at: "2026-10-18T00:00:00Z",
    elapsed_ms: 1,
    summary: "草稿待确认",
    error_type: null,
    events: [],
    decisions: {},
    state: {
      request: { request_type: "collect", text: "海洋" },
      draft: {
        draft: starInput,
        missing_fields: ["interest_reason"],
        questions: [],
      },
    },
  };
  mockedApi.mockImplementation(async (path, method = "GET", body) => {
    if (path === "/health") return { mock_mode: true };
    if (path === "/preferences") return pref;
    if (path === "/stars/star-1")
      return stars.find((star) => star.id === "star-1");
    if (path === "/stats")
      return { stars: stars.length, quests: 0, completed: 0, categories: [] };
    if (path === "/stars") {
      if (method === "POST") {
        if (failSave) throw new Error("模拟保存失败");
        stars = [{ ...savedStar, ...(body as StarInput) }];
        return stars[0];
      }
      return stars;
    }
    if (path === "/agent/runs") {
      if (method === "POST") {
        if (failGenerate) throw new Error("模拟生成失败");
        generated = true;
        return run;
      }
      return generated ? [run] : [];
    }
    if (path === "/agent/runs/run-1/decision") {
      if (failSave) throw new Error("模拟保存失败");
      const approved = (body as { approved: boolean }).approved;
      if (approved) stars = [savedStar];
      run = {
        ...run,
        status: "decided",
        decisions: {
          star: { approved, ...(approved ? { star_id: savedStar.id } : {}) },
        },
      };
      return run.decisions.star;
    }
    if (path === "/agent/runs/run-1") return run;
    return [];
  });
  return {
    failNextGeneration: () => {
      failGenerate = true;
    },
  };
}
async function collectDraft() {
  await screen.findByText("Mock 模式 · 规则生成");
  fireEvent.click(screen.getByRole("button", { name: /^收集星星/ }));
  fireEvent.change(screen.getByLabelText("你最近对什么感到好奇？"), {
    target: { value: "海洋" },
  });
  fireEvent.click(screen.getByRole("button", { name: "整理成草稿" }));
  await screen.findByText(/草稿已经生成，还没有加入正式档案/);
}
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
describe("后端数据与操作边界", () => {
  it("空档案展示真实空状态和 Mock 标记", async () => {
    backend();
    render(<App />);
    expect(await screen.findByText("Mock 模式 · 规则生成")).toBeInTheDocument();
    expect(screen.getByText("从收藏第一颗星星开始")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "收集第一颗星星" }),
    ).toBeVisible();
    expect(
      screen.getByText(
        "星星是你收藏的兴趣或好奇。从收藏第一颗星星开始，探索才有真实依据。",
      ),
    ).toBeVisible();
    expect(screen.queryByText("深海的微光")).not.toBeInTheDocument();
  });
  it("创建草稿不自动调用正式写入 API", async () => {
    backend();
    const defaultBackend = mockedApi.getMockImplementation()!;
    mockedApi.mockImplementation(async (path, ...args) =>
      (path === "/agent/runs" && args[0] === "POST") ||
      path === "/agent/runs/run-1"
        ? {
            run_id: "run-1",
            request_type: "collect",
            mode: "mock",
            status: "awaiting_decision",
            decisions: {},
            state: {
              draft: {
                draft: {
                  title: "海洋",
                  original_text: "海洋",
                  description: "海洋",
                  category: "自然",
                  tags: ["海洋"],
                  interest_reason: null,
                  source_type: "paste",
                  source_reference: null,
                  estimated_minutes: null,
                  estimated_budget: null,
                  energy_level: null,
                  status: "collected",
                },
                missing_fields: [
                  "interest_reason",
                  "estimated_minutes",
                  "estimated_budget",
                  "energy_level",
                  "future_optional_field",
                  "constructor",
                ],
                questions: [],
              },
            },
          }
        : defaultBackend(path, ...args),
    );
    render(<App />);
    await screen.findByText("Mock 模式 · 规则生成");
    fireEvent.click(screen.getByRole("button", { name: /^收集星星/ }));
    fireEvent.change(screen.getByLabelText("你最近对什么感到好奇？"), {
      target: { value: "海洋" },
    });
    fireEvent.click(screen.getByRole("button", { name: "整理成草稿" }));
    expect(
      await screen.findByRole("button", { name: "确认保存星星" }),
    ).toBeInTheDocument();
    const note = screen.getByText(/尚不清楚：/);
    expect(note).toBeVisible();
    expect(note).toHaveTextContent(
      "尚不清楚：兴趣原因、预计时间、预计预算、所需精力、其他待补充信息。这不表示整理出错，可选信息可补充或留空。",
    );
    expect(note.textContent).not.toMatch(
      /interest_reason|estimated_minutes|estimated_budget|energy_level|future_optional_field|constructor/,
    );
    expect(
      mockedApi.mock.calls.some(
        ([path, method]) => path === "/stars" && method === "POST",
      ),
    ).toBe(false);
    expect(
      mockedApi.mock.calls.some(([path]) => path.includes("/decision")),
    ).toBe(false);
  });
  it("无法连接后端时显示错误，不把数据标记为已连接", async () => {
    mockedApi.mockRejectedValue(new Error("服务连接失败"));
    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("服务连接失败"),
    );
    expect(screen.getByText("等待后端连接")).toBeInTheDocument();
    const actions = screen.getByRole("group", { name: "首页核心功能" });
    expect(within(actions).getAllByRole("button")).toHaveLength(1);
    expect(
      within(actions).getByRole("button", { name: "收集一颗星星" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "收集第一颗星星" }),
    ).not.toBeInTheDocument();
  });
  it("单兴趣示例、确认边界和链接用途可见，原始文字仍必填", async () => {
    backend();
    render(<App />);
    await screen.findByText("Mock 模式 · 规则生成");
    fireEvent.click(screen.getByRole("button", { name: /^收集星星/ }));
    const text = screen.getByLabelText("你最近对什么感到好奇？");
    expect(text).toBeRequired();
    expect(text).toHaveAttribute("maxlength", "12000");
    expect(text).toHaveAttribute(
      "placeholder",
      "例如：我想了解深海生物为什么会发光，想先记下几个好奇的问题。",
    );
    expect(text).toHaveAccessibleDescription(
      /一次整理生成一张可编辑草稿，确认后才会加入正式档案/,
    );
    expect(screen.getByText(/一次整理生成一张可编辑草稿/)).toBeVisible();
    const link = screen.getByLabelText("参考链接（可选）");
    expect(link).not.toBeRequired();
    expect(link).toHaveAccessibleDescription(
      /链接仅保存来源，不读取网页.*仍需填写上方的兴趣原始文字/,
    );
    expect(link).toHaveAttribute("placeholder", "https://example.com/notes");
    for (const value of [
      "http://example.com/notes",
      "https://example.com/notes",
      "HTTPS://example.com/notes",
    ]) {
      fireEvent.change(link, { target: { value } });
      expect(link).toBeValid();
    }
    fireEvent.change(link, { target: { value: "ftp://example.com/notes" } });
    expect(link).toBeInvalid();
    fireEvent.change(link, { target: { value: "https://example.com/notes" } });
    fireEvent.click(screen.getByRole("button", { name: "整理成草稿" }));
    expect(mockedApi.mock.calls.some(([, method]) => method === "POST")).toBe(
      false,
    );
  });
  it.each([
    ["", null],
    ["0", 0],
    ["8", 8],
  ] as const)(
    "偏好 5 元，本次预算输入 %s 时保留原始语义",
    async (input, expected) => {
      backend(true, 5);
      const defaultBackend = mockedApi.getMockImplementation()!;
      mockedApi.mockImplementation(async (path, ...args) =>
        path === "/agent/runs" && args[0] === "POST"
          ? {
              run_id: "budget-run",
              state: { proposals: [], questions: [] },
              decisions: {},
            }
          : defaultBackend(path, ...args),
      );
      render(<App />);
      await screen.findByText("Mock 模式 · 规则生成");
      fireEvent.click(screen.getByRole("button", { name: "我的偏好" }));
      expect(screen.getByLabelText("预算上限（元，可选）")).toHaveValue(5);
      fireEvent.click(screen.getByRole("button", { name: "微型探索" }));
      const budget = screen.getByLabelText("本次预算（元，可选）");
      expect(budget).toHaveAccessibleDescription(
        /留空仍遵守偏好上限；0 元为零预算；同时设置取更低上限/,
      );
      expect(budget).not.toBeRequired();
      expect(budget).toHaveAttribute("min", "0");
      expect(budget).toHaveAttribute("max", "100000");
      expect(screen.queryByText(/留空不限/)).not.toBeInTheDocument();
      const minutes = screen.getByLabelText("可用时间（分钟，可选）");
      expect(minutes).not.toBeRequired();
      expect(minutes).toHaveAttribute("min", "1");
      expect(minutes).toHaveAttribute("max", "1440");
      expect(minutes).toHaveAccessibleDescription(
        /留空用偏好最长时间；填写本次可用上限/,
      );
      fireEvent.change(minutes, { target: { value: "" } });
      fireEvent.change(budget, { target: { value: input } });
      fireEvent.change(screen.getByLabelText("今天想靠近哪份好奇？"), {
        target: { value: "深海" },
      });
      fireEvent.click(screen.getByRole("button", { name: "寻找小体验" }));
      await waitFor(() =>
        expect(mockedApi).toHaveBeenCalledWith(
          "/agent/runs",
          "POST",
          expect.objectContaining({
            budget: expected,
            available_minutes: null,
          }),
          expect.any(String),
        ),
      );
    },
  );
  it("偏好说明与范围关联，未设置精力和空预算仍保存 null", async () => {
    backend();
    render(<App />);
    await screen.findByText("Mock 模式 · 规则生成");
    fireEvent.click(screen.getByRole("button", { name: "我的偏好" }));
    const categories = screen.getByLabelText("兴趣类别（可选）");
    const constraints = screen.getByLabelText("明确约束（可选）");
    expect(categories).toHaveAccessibleDescription(/中英文逗号或换行分隔/);
    expect(constraints).toHaveAccessibleDescription(/其他约束需澄清/);
    const energy = screen.getByLabelText("精力偏好（可选）");
    expect(energy).toHaveValue("");
    expect(energy).toHaveAccessibleDescription(
      /未设置不额外限制，也不代表低精力/,
    );
    const min = screen.getByLabelText("最短时间（分钟，必填）");
    expect(min).toBeRequired();
    expect(min).toHaveAttribute("min", "1");
    expect(min).toHaveAttribute("max", "1440");
    expect(screen.getByLabelText("最长时间（分钟，必填）")).toBeRequired();
    expect(
      screen.getByLabelText("预算上限（元，可选）"),
    ).toHaveAccessibleDescription(/留空不额外限制；0 元仅限无需花费/);
    fireEvent.change(categories, { target: { value: "自然，文字,观察" } });
    fireEvent.change(constraints, {
      target: { value: "仅室内，不购买,不外出" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存明确偏好" }));
    await waitFor(() =>
      expect(mockedApi).toHaveBeenCalledWith(
        "/preferences",
        "PUT",
        expect.objectContaining({
          categories: ["自然", "文字", "观察"],
          constraints: ["仅室内", "不购买", "不外出"],
          max_budget: null,
          energy_level: null,
        }),
      ),
    );
  });
  it.each([
    ["微型探索", "查看时间、预算和精力规则", /本次和偏好均留空时不额外限制/],
    ["我的偏好", "查看偏好填写规则", /目前只支持免费的室内文字记录步骤/],
  ])("%s 默认只展示短提示，完整规则可按需展开", async (page, summary, rule) => {
    backend();
    render(<App />);
    await screen.findByText("Mock 模式 · 规则生成");
    fireEvent.click(screen.getByRole("button", { name: page }));
    const toggle = screen.getByText(summary);
    const help = toggle.closest("details")!;
    // 原生 summary 提供键盘激活语义；真实 Enter/Space 操作由浏览器测试验证。
    expect(toggle.tagName).toBe("SUMMARY");
    expect(help).not.toHaveAttribute("open");
    expect(within(help).getByText(rule)).not.toBeVisible();
    expect(
      screen.getByLabelText(
        page === "微型探索" ? "本次预算（元，可选）" : "预算上限（元，可选）",
      ),
    ).toBeVisible();
    fireEvent.click(toggle);
    expect(help).toHaveAttribute("open");
    expect(within(help).getByText(rule)).toBeVisible();
    fireEvent.click(toggle);
    expect(help).not.toHaveAttribute("open");
    expect(
      mockedApi.mock.calls.some(
        ([, method]) => method === "POST" || method === "PUT",
      ),
    ).toBe(false);
  });
  it.each(["collected", "exploring"] as const)(
    "已有 %s 星星时收集与探索都有明确按钮，导航不写入",
    async (status) => {
      backend(true, null, [{ ...savedStar, status }]);
      render(<App />);
      await screen.findByText("Mock 模式 · 规则生成");
      expect(
        screen.queryByRole("button", { name: "收集第一颗星星" }),
      ).not.toBeInTheDocument();
      const actions = screen.getByRole("group", { name: "首页核心功能" });
      for (const name of ["收集星星", "微型探索"]) {
        const button = within(actions).getByRole("button", { name });
        expect(button).toBeVisible();
        expect(button).toHaveClass("hero-core-action");
        expect(button).not.toHaveClass("text-button");
      }
      expect(within(actions).getAllByRole("button")).toHaveLength(2);
      expect(
        screen.getByText(/随时收集新的好奇.*体验又能带来新的好奇/),
      ).toBeVisible();
      fireEvent.click(
        within(actions).getByRole("button", { name: "微型探索" }),
      );
      expect(screen.getByLabelText("今天想靠近哪份好奇？")).toBeVisible();
      fireEvent.click(screen.getByRole("button", { name: "我的星屿" }));
      fireEvent.click(
        within(screen.getByRole("group", { name: "首页核心功能" })).getByRole(
          "button",
          { name: "收集星星" },
        ),
      );
      expect(screen.getByLabelText("你最近对什么感到好奇？")).toBeVisible();
      expect(
        mockedApi.mock.calls.every(([, method]) => !method || method === "GET"),
      ).toBe(true);
    },
  );
  it("只有归档星星时解释推荐边界，保留档案入口", async () => {
    backend(true, null, [{ ...savedStar, status: "archived" }]);
    render(<App />);
    await screen.findByText("Mock 模式 · 规则生成");
    expect(screen.getByText(/归档星星不参与推荐/)).toBeVisible();
    expect(screen.getByRole("button", { name: "查看星星档案" })).toBeVisible();
    const actions = screen.getByRole("group", { name: "首页核心功能" });
    expect(
      within(actions).getByRole("button", { name: "继续收集星星" }),
    ).toBeVisible();
    expect(
      within(actions).queryByRole("button", { name: "微型探索" }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "微型探索" }));
    expect(
      screen.getByRole("region", { name: "探索前的准备" }),
    ).toHaveTextContent("归档星星不会用于推荐");
  });
  it("草稿待确认与放下均不当作已收藏星星", async () => {
    collectionBackend();
    render(<App />);
    await collectDraft();
    expect(
      screen.queryByRole("region", { name: "保存后的下一步" }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "我的星屿" }));
    expect(
      screen.getByRole("button", { name: "收集第一颗星星" }),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /^收集星星/ }));
    fireEvent.click(screen.getByRole("button", { name: "暂不保存" }));
    await screen.findByText("这张草稿已放下，没有加入正式档案。");
    expect(screen.queryByText(/草稿已经生成/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "保存后的下一步" }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "我的星屿" }));
    expect(
      screen.getByRole("button", { name: "收集第一颗星星" }),
    ).toBeVisible();
    expect(
      mockedApi.mock.calls.filter(
        ([path, method]) => path.endsWith("/decision") && method === "POST",
      ),
    ).toHaveLength(1);
    expect(
      mockedApi.mock.calls.some(
        ([path, method]) => path === "/stars" && method === "POST",
      ),
    ).toBe(false);
  });
  it("实际批准后提供基础下一步，反复导航不重复正式写入", async () => {
    collectionBackend();
    render(<App />);
    await collectDraft();
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    const next = await screen.findByRole("region", { name: "保存后的下一步" });
    fireEvent.click(within(next).getByRole("button", { name: "查看这颗星星" }));
    await screen.findByRole("dialog");
    fireEvent.click(screen.getByRole("button", { name: "关闭弹窗" }));
    expect(
      screen.getByRole("button", { name: /海洋.*深海发光/ }),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /^收集星星/ }));
    fireEvent.click(
      within(screen.getByRole("region", { name: "保存后的下一步" })).getByRole(
        "button",
        { name: "开始微型探索" },
      ),
    );
    expect(screen.getByLabelText("今天想靠近哪份好奇？")).toBeVisible();
    expect(
      mockedApi.mock.calls.filter(
        ([path, method]) => path.endsWith("/decision") && method === "POST",
      ),
    ).toHaveLength(1);
  });
  it("保存失败不出现成功下一步", async () => {
    collectionBackend(true);
    render(<App />);
    await collectDraft();
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("模拟保存失败");
    expect(
      screen.queryByText("这张草稿已保存到档案。"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "保存后的下一步" }),
    ).not.toBeInTheDocument();
  });
  it("新整理失败时不沿用上次保存成功的引导", async () => {
    const control = collectionBackend();
    render(<App />);
    await collectDraft();
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    await screen.findByRole("region", { name: "保存后的下一步" });
    control.failNextGeneration();
    fireEvent.change(screen.getByLabelText("你最近对什么感到好奇？"), {
      target: { value: "新好奇" },
    });
    fireEvent.click(screen.getByRole("button", { name: "整理成草稿" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("模拟生成失败");
    expect(
      screen.queryByRole("region", { name: "保存后的下一步" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("这张草稿已保存到档案。"),
    ).not.toBeInTheDocument();
  });
  it.each([false, true])(
    "手动保存路径遵循真实响应（失败=%s）",
    async (failed) => {
      collectionBackend(failed);
      render(<App />);
      await screen.findByText("Mock 模式 · 规则生成");
      fireEvent.click(screen.getByRole("button", { name: /^收集星星/ }));
      fireEvent.click(screen.getByRole("button", { name: "手动填写" }));
      fireEvent.change(screen.getByLabelText("标题"), {
        target: { value: "海洋" },
      });
      fireEvent.change(screen.getByLabelText("原始文字"), {
        target: { value: "海洋" },
      });
      fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
      if (failed) {
        await screen.findByRole("alert");
        expect(
          screen.queryByRole("region", { name: "保存后的下一步" }),
        ).not.toBeInTheDocument();
      } else
        expect(
          await screen.findByRole("region", { name: "保存后的下一步" }),
        ).toBeVisible();
      expect(
        mockedApi.mock.calls.filter(
          ([path, method]) => path === "/stars" && method === "POST",
        ),
      ).toHaveLength(1);
    },
  );
  it.each([true, false, null])(
    "顶栏指南可重复打开关闭、管理焦点且反映真实模式（Mock=%s）",
    async (mock) => {
      if (mock === null) mockedApi.mockRejectedValue(new Error("连接失败"));
      else backend(mock);
      const { container } = render(<App />);
      if (mock === null) await screen.findByRole("alert");
      else
        await screen.findByText(
          mock ? "Mock 模式 · 规则生成" : "模型服务已连接",
        );
      const toggle = screen.getByRole("button", { name: "使用指南" });
      expect(toggle.closest(".topbar")).not.toBeNull();
      expect(container.querySelector(".main-content .usage-guide")).toBeNull();
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      for (const closeMethod of ["Escape", "button", "backdrop"]) {
        toggle.focus();
        fireEvent.click(toggle);
        const guide = screen.getByRole("dialog", { name: "星屿怎么使用" });
        const close = within(guide).getByRole("button", { name: "关闭弹窗" });
        expect(close).toHaveFocus();
        fireEvent.keyDown(close, { key: "Tab" });
        expect(close).toHaveFocus();
        fireEvent.keyDown(close, { key: "Tab", shiftKey: true });
        expect(close).toHaveFocus();
        expect(within(guide).getAllByRole("listitem")).toHaveLength(4);
        expect(within(guide).getByText(/接受体验后到“体验手记”/)).toBeVisible();
        expect(
          within(guide).getByText(
            mock === null
              ? /连接后可查看当前生成模式/
              : mock
                ? /不代表真实大模型理解/
                : /当前为模型模式.*仍需你检查、确认/,
          ),
        ).toBeVisible();
        fireEvent.click(within(guide).getByRole("heading"));
        expect(guide).toBeVisible();
        if (closeMethod === "Escape")
          fireEvent.keyDown(close, { key: "Escape" });
        else if (closeMethod === "button") fireEvent.click(close);
        else fireEvent.click(guide.parentElement!);
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
        expect(toggle).toHaveFocus();
      }
      expect(
        mockedApi.mock.calls.every(([, method]) => !method || method === "GET"),
      ).toBe(true);
    },
  );
  it.each([
    "我的星屿",
    "收集星星",
    "星星档案",
    "兴趣轨道",
    "微型探索",
    "体验手记",
    "Agent 足迹",
    "我的偏好",
  ])("%s 页面均可从顶栏打开指南，关闭后保留页面", async (name) => {
    backend();
    render(<App />);
    await screen.findByText("Mock 模式 · 规则生成");
    const nav = screen.getByRole("navigation", { name: "主导航" });
    fireEvent.click(
      within(nav).getByRole("button", { name: new RegExp("^" + name) }),
    );
    const toggle = screen.getByRole("button", { name: "使用指南" });
    fireEvent.click(toggle);
    expect(screen.getByRole("dialog", { name: "星屿怎么使用" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "关闭弹窗" }));
    expect(
      within(nav).getByRole("button", { name: new RegExp("^" + name) }),
    ).toHaveClass("active");
    expect(
      mockedApi.mock.calls.every(([, method]) => !method || method === "GET"),
    ).toBe(true);
  });
  it("打开指南不清除收集输入或待确认草稿，也不提交表单", async () => {
    collectionBackend();
    render(<App />);
    await collectDraft();
    fireEvent.change(screen.getByLabelText("标题"), {
      target: { value: "未保存的修改" },
    });
    const calls = mockedApi.mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "使用指南" }));
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(screen.getByLabelText("标题")).toHaveValue("未保存的修改");
    expect(screen.getByText(/草稿已经生成，还没有加入正式档案/)).toBeVisible();
    expect(mockedApi.mock.calls).toHaveLength(calls);
  });
});
