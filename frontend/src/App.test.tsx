import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { api } from "./api";
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
function backend(mock = true, maxBudget: number | null = null) {
  mockedApi.mockImplementation(async (path) => {
    if (path === "/stats")
      return { stars: 0, quests: 0, completed: 0, categories: [] };
    if (path === "/health") return { mock_mode: mock };
    if (path === "/preferences")
      return { ...pref, explicit: { ...pref.explicit, max_budget: maxBudget } };
    return [];
  });
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
    expect(screen.getByText("你的第一颗星星，正在路上")).toBeInTheDocument();
    expect(screen.queryByText("深海的微光")).not.toBeInTheDocument();
  });
  it("创建草稿不自动调用正式写入 API", async () => {
    backend();
    const defaultBackend = mockedApi.getMockImplementation()!;
    mockedApi.mockImplementation(async (path, ...args) =>
      path === "/agent/runs"
        ? {
            run_id: "run-1",
            request_type: "collect",
            mode: "mock",
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
                missing_fields: ["interest_reason"],
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
        /0 元表示本次预算为 0.*仍遵守“我的偏好”的预算上限.*偏好也未设置时不额外限制.*同时设置时取更低上限/,
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
        /留空沿用偏好最长时间.*仍需达到偏好最短时间/,
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
    expect(constraints).toHaveAccessibleDescription(
      /其他约束尚不能自动验证，会要求澄清/,
    );
    const energy = screen.getByLabelText("精力偏好（可选）");
    expect(energy).toHaveValue("");
    expect(energy).toHaveAccessibleDescription(
      /未设置表示不额外限制，不代表低精力/,
    );
    const min = screen.getByLabelText("最短时间（分钟，必填）");
    expect(min).toBeRequired();
    expect(min).toHaveAttribute("min", "1");
    expect(min).toHaveAttribute("max", "1440");
    expect(screen.getByLabelText("最长时间（分钟，必填）")).toBeRequired();
    expect(
      screen.getByLabelText("预算上限（元，可选）"),
    ).toHaveAccessibleDescription(/留空不额外限制，0 表示仅限无需花费/);
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
});
