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
function backend(mock = true) {
  mockedApi.mockImplementation(async (path) => {
    if (path === "/stats")
      return { stars: 0, quests: 0, completed: 0, categories: [] };
    if (path === "/health") return { mock_mode: mock };
    if (path === "/preferences") return pref;
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
});
