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
const evidence = [];
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const get = async (path) =>
    (await page.request.get(base + "/api" + path)).json();
  assert.equal((await get("/health")).mock_mode, true);
  const quests = await get("/quests");
  const preferences = await get("/preferences");
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    const response = await page.request.post(base + "/api/agent/runs", {
      data: {
        request_type: "explore",
        exploration_direction: "knowledge",
        text: "海洋",
        learning_source: {
          text: material.text,
          label: material.label,
          url: material.url,
        },
        available_minutes: 10,
        budget: 0,
        energy_level: "low",
      },
    });
    assert.equal(response.status(), 201);
    const parent = await response.json();
    await page.goto(base);
    await page
      .getByRole("navigation", { name: "主导航" })
      .getByRole("button", { name: /^Agent 足迹/ })
      .click();
    const runs = await get("/agent/runs");
    await page
      .locator(".run-list button")
      .nth(runs.findIndex((r) => r.run_id === parent.run_id))
      .click();
    const card = page.locator(".run-detail .learning-card");
    await card.waitFor();
    await card.screenshot({ path: `${artifact}/J-direct-${width}.png` });
    let writes = [];
    const watch = (request) => {
      if (request.url().includes("/api/") && request.method() !== "GET")
        writes.push(request);
    };
    page.on("request", watch);
    const begin = card.getByRole("button", { name: "接着探索", exact: true });
    await begin.focus();
    await page.keyboard.press("Enter");
    const dialog = page.getByRole("dialog", { name: "接着探索", exact: true });
    const question = dialog.getByLabel("接着想了解什么？");
    assert.equal(
      await question.inputValue(),
      parent.state.learning_card.follow_up_question,
    );
    await question.fill("我想改掉这个问题");
    await dialog.getByRole("button", { name: "放弃接续" }).click();
    assert.equal(await dialog.count(), 0);
    assert.equal(
      await begin.evaluate((el) => el === document.activeElement),
      true,
    );
    assert.equal(writes.length, 0);
    await begin.click();
    assert.equal(
      await question.inputValue(),
      parent.state.learning_card.follow_up_question,
    );
    await question.fill("荧光素酶起什么作用？");
    await dialog.screenshot({ path: `${artifact}/J-edit-${width}.png` });
    const wait = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/agent/runs") && r.request().method() === "POST",
    );
    await dialog.getByRole("button", { name: "提交接续问题" }).click();
    const submitted = await wait;
    assert.equal(submitted.status(), 201);
    const child = await submitted.json();
    assert.equal(child.state.request.parent_run_id, parent.run_id);
    assert.equal(child.state.request.text, "荧光素酶起什么作用？");
    assert.deepEqual(
      child.state.request.learning_source,
      parent.state.request.learning_source,
    );
    assert.equal(child.state.request.budget, 0);
    assert.deepEqual(child.state.proposals, []);
    const result = page.getByRole("region", { name: "本次探索结果" });
    await result
      .getByText(/催化剂/)
      .first()
      .waitFor();
    assert.equal(
      await result
        .getByRole("button", { name: "接着探索", exact: true })
        .count(),
      0,
    );
    await result.screenshot({ path: `${artifact}/J-answer-${width}.png` });
    assert.equal(writes.length, 1);
    page.off("request", watch);
    assert.deepEqual(await get(`/agent/runs/${parent.run_id}`), parent);
    // Return to the unchanged parent and submit the original extension: unsupported by this material.
    await page
      .getByRole("navigation", { name: "主导航" })
      .getByRole("button", { name: /^Agent 足迹/ })
      .click();
    const updated = await get("/agent/runs");
    await page
      .locator(".run-list button")
      .nth(updated.findIndex((r) => r.run_id === parent.run_id))
      .click();
    await page
      .locator(".run-detail")
      .getByRole("button", { name: "接着探索", exact: true })
      .click();
    const insufficientWait = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/agent/runs") && r.request().method() === "POST",
    );
    await dialog.getByRole("button", { name: "提交接续问题" }).click();
    const insufficient = await (await insufficientWait).json();
    assert.equal(insufficient.status, "succeeded");
    assert.equal(insufficient.state.learning_card, null);
    assert.deepEqual(insufficient.state.proposals, []);
    await result.getByText(/未解释它如何传递信息/).waitFor();
    await result.screenshot({
      path: `${artifact}/J-insufficient-${width}.png`,
    });
    await page.reload();
    await page
      .getByRole("navigation", { name: "主导航" })
      .getByRole("button", { name: /^Agent 足迹/ })
      .click();
    const historical = await get("/agent/runs");
    await page
      .locator(".run-list button")
      .nth(historical.findIndex((r) => r.run_id === child.run_id))
      .click();
    await page
      .locator(".run-detail")
      .getByText(`接续自运行 ${parent.run_id}`, { exact: true })
      .waitFor();
    await page
      .locator(".run-detail")
      .screenshot({ path: `${artifact}/J-history-${width}.png` });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
      false,
    );
    evidence.push({ width, parent, child, insufficient });
  }
  assert.deepEqual(await get("/quests"), quests);
  assert.deepEqual(await get("/preferences"), preferences);
  assert.deepEqual(errors, []);
  await writeFile(
    `${artifact}/continuation.json`,
    JSON.stringify({ kind: "fixed-mock-only", evidence }, null, 2),
  );
  console.log(
    "PASS J: direct/edit/cancel/no automatic requests/explicit submit/answer/insufficient/history; 1440/390; unchanged parent/Quest/preferences",
  );
} finally {
  await browser.close();
}
