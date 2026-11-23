import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { chromium } from "playwright";
if (process.env.E2E_ALLOW_WRITE !== "true")
  throw new Error("Isolated launcher required");
const base = process.env.E2E_BASE_URL;
const artifact = process.env.E2E_ARTIFACT_DIR;
const material = JSON.parse(
  await readFile(
    new URL("../../evals/knowledge_preview_material.json", import.meta.url),
    "utf8",
  ),
);
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const get = async (path) =>
    (await page.request.get(base + "/api" + path)).json();
  assert.equal((await get("/health")).mock_mode, true);
  const quests = await get("/quests");
  const preferences = await get("/preferences");
  const evidence = [];
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const hasMaterial of [true, false]) {
      const response = await page.request.post(base + "/api/agent/runs", {
        data: {
          request_type: "explore",
          exploration_direction: "knowledge",
          text: "海洋",
          ...(hasMaterial
            ? {
                learning_source: {
                  text: "测试材料B（不相关）：这份记录只列出了面包的包装颜色。",
                  label: "原用户材料",
                  url: "https://example.org/original",
                },
              }
            : {}),
          available_minutes: 12,
          budget: hasMaterial ? 0 : null,
          energy_level: hasMaterial ? "medium" : null,
        },
      });
      assert.equal(response.status(), 201);
      const original = await response.json();
      assert.equal(original.state.learning_card, null);
      const openOriginal = async () => {
        await page.goto(base);
        await page
          .getByRole("navigation", { name: "主导航" })
          .getByRole("button", { name: /^Agent 足迹/ })
          .click();
        const runs = await get("/agent/runs");
        await page
          .locator(".run-list button")
          .nth(runs.findIndex((r) => r.run_id === original.run_id))
          .click();
      };
      await openOriginal();
      let writes = [];
      const watch = (request) => {
        if (request.url().includes("/api/") && request.method() !== "GET")
          writes.push(request);
      };
      page.on("request", watch);
      const start = page.getByRole("button", {
        name: "补充材料再探索",
        exact: true,
      });
      await start.focus();
      await page.keyboard.press("Enter");
      const question = page.getByLabel("今天想靠近哪份好奇？", { exact: true });
      const source = page.getByRole("textbox", {
        name: "本次一起看的材料（必填）",
        exact: true,
      });
      const submit = page.getByRole("button", { name: "提交材料，重新探索" });
      assert.equal(await question.inputValue(), "海洋");
      assert.equal(
        await question.evaluate((el) => el === document.activeElement),
        true,
      );
      assert.equal(
        await source.inputValue(),
        original.state.request.learning_source?.text || "",
      );
      assert.equal(
        await page
          .getByLabel("本次预算（元，可选）", { exact: true })
          .inputValue(),
        hasMaterial ? "0" : "",
      );
      assert.equal(
        await page.getByLabel("当前精力（必选）", { exact: true }).inputValue(),
        hasMaterial ? "medium" : "",
      );
      await question.fill("只是编辑");
      await page.getByRole("button", { name: "取消补充，返回原运行" }).click();
      await page.locator(".run-detail").waitFor();
      assert.equal(writes.length, 0);
      await start.click();
      assert.equal(await question.inputValue(), "海洋");
      await source.fill("");
      await submit.click();
      assert.equal(
        await source.evaluate((el) => el.validity.valueMissing),
        true,
      );
      assert.equal(writes.length, 0);
      await source.fill("   ");
      await submit.click();
      await page.getByRole("alert").filter({ hasText: "非空白" }).waitFor();
      assert.equal(writes.length, 0);
      await question.fill("海洋发光的用途");
      await source.fill(material.text);
      await page
        .getByLabel("这段材料来自哪里？（选填）", { exact: true })
        .fill("新提交的公开材料");
      const url = page.getByLabel("参考 URL（选填，仅记录，不访问）", {
        exact: true,
      });
      await url.fill("ftp://example.org/a");
      await submit.click();
      assert.equal(
        await url.evaluate((el) => el.validity.patternMismatch),
        true,
      );
      assert.equal(writes.length, 0);
      await url.fill("https://example.org/new-source");
      await page
        .getByLabel("可用时间（分钟，可选）", { exact: true })
        .fill("18");
      await page
        .getByLabel("当前精力（必选）", { exact: true })
        .selectOption("low");
      // Dismiss the earlier validation message after correcting inputs.
      await page.getByRole("button", { name: "关闭错误" }).click();
      // Full form spans multiple screens on mobile; capture all submitted fields.
      await page.screenshot({
        path: `${artifact}/K-edit-${width}-${hasMaterial}.png`,
        fullPage: true,
      });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      const wait = page.waitForResponse(
        (r) =>
          r.url().endsWith("/api/agent/runs") &&
          r.request().method() === "POST",
      );
      await submit.click();
      const submitted = await wait;
      assert.equal(submitted.status(), 201);
      const next = await submitted.json();
      assert.equal(writes.length, 1);
      const sent = writes[0].postDataJSON();
      assert.equal("parent_run_id" in sent, false);
      assert.equal("parent_run_id" in next.state.request, false);
      assert.equal(next.state.request.learning_source.text, material.text);
      assert.equal(
        next.state.request.learning_source.label,
        "新提交的公开材料",
      );
      assert.equal(
        next.state.request.learning_source.url,
        "https://example.org/new-source",
      );
      assert.equal(next.state.request.available_minutes, 18);
      assert.equal(next.state.request.budget, hasMaterial ? 0 : null);
      assert.equal(next.state.request.energy_level, "low");
      assert.equal(next.state.request.text, "海洋发光的用途");
      assert.notEqual(next.run_id, original.run_id);
      const result = page.getByRole("region", { name: "本次探索结果" });
      await result
        .getByText(/未经独立核实/)
        .first()
        .waitFor();
      await result.screenshot({
        path: `${artifact}/K-result-${width}-${hasMaterial}.png`,
      });
      assert.deepEqual(await get(`/agent/runs/${original.run_id}`), original);
      page.off("request", watch);
      await openOriginal();
      await start.waitFor();
      assert.deepEqual(await get(`/agent/runs/${original.run_id}`), original);
      evidence.push({ width, hasMaterial, original, next });
    }
  }
  assert.deepEqual(await get("/quests"), quests);
  assert.deepEqual(await get("/preferences"), preferences);
  assert.deepEqual(errors, []);
  await writeFile(
    `${artifact}/replenishment.json`,
    JSON.stringify({ kind: "fixed-mock-only", evidence }, null, 2),
  );
  console.log(
    "PASS K 1440/390: material/no-material, keyboard entry, edit/cancel/invalid no writes, explicit new root, new source, constraints, unchanged history/Quest/preferences",
  );
} finally {
  await browser.close();
}
