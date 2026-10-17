import { afterEach, expect, it, vi } from "vitest";
import { api, ApiError } from "./api";
afterEach(() => vi.unstubAllGlobals());
it("审批携带明确请求体与幂等键", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValue(
      new Response(JSON.stringify({ quest_id: "actual" }), { status: 200 }),
    );
  vi.stubGlobal("fetch", fetchMock);
  expect(
    await api("/agent/runs/run-id/decision", "POST", { approved: true }, "key"),
  ).toEqual({ quest_id: "actual" });
  expect(fetchMock.mock.calls[0][1].headers["Idempotency-Key"]).toBe("key");
});
it("模型失败保留运行 ID 供界面查看与恢复", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: {
            message: "生成失败",
            run_id: "failed-run",
            error_type: "timeout",
          },
        }),
        { status: 502 },
      ),
    ),
  );
  try {
    await api("/agent/runs", "POST", {});
  } catch (e) {
    expect(e).toBeInstanceOf(ApiError);
    expect((e as ApiError).runId).toBe("failed-run");
    expect((e as Error).message).toBe("生成失败");
    return;
  }
  throw new Error("应当抛出 API 错误");
});
