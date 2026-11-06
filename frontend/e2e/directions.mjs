import assert from "node:assert/strict";

// AGENT-004-A offline-v1; called only on the smoke runner's verified Mock database.
export async function verifyDirections(page, base, artifact) {
  const nav = (name) =>
    page
      .getByRole("navigation", { name: "主导航" })
      .getByRole("button", { name: new RegExp("^" + name) })
      .click();
  const read = async (path) =>
    (await page.request.get(base + "/api" + path)).json();
  const questsBefore = (await read("/quests")).length;
  const preferenceBefore = await read("/preferences");
  const options = [
    [
      "想了解一点知识",
      "knowledge",
      "整理一个待核实的问题|挑选适合这份兴趣的入门资料|拆解星星中已有的学习问题",
    ],
    ["想动手试试看", "hands_on", "做一次文字排序小尝试"],
    ["想发挥一点创意", "creative", "构思一份小创作"],
    ["还没想好", undefined, "写三个好奇问题"],
  ];
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const [label, direction, resultTitle] of options) {
      await nav("微型探索");
      await page.getByLabel("今天想靠近哪份好奇？").fill("海洋");
      await page.getByRole("radio", { name: new RegExp(label) }).check();
      const response = page.waitForResponse(
        (r) =>
          r.url().endsWith("/api/agent/runs") &&
          r.request().method() === "POST",
      );
      await page
        .getByRole("button", { name: "寻找小体验", exact: true })
        .click();
      const wire = await response;
      const sent = wire.request().postDataJSON();
      if (direction) assert.equal(sent.exploration_direction, direction);
      else assert.equal(Object.hasOwn(sent, "exploration_direction"), false);
      const run = await wire.json();
      assert.equal(run.mode, "mock");
      assert.equal(run.state.request.exploration_direction, direction);
      assert.ok(run.state.proposals.length);
      assert.ok(
        run.state.proposals.every((p) => new RegExp(resultTitle).test(p.title)),
      );
      await page.getByText("正在处理，请稍候…").waitFor({ state: "hidden" });
      await page
        .getByRole("heading", { name: new RegExp(resultTitle) })
        .first()
        .waitFor();
      await page.screenshot({
        path: `${artifact}/direction-result-${direction || "unset"}-${width}.png`,
        fullPage: true,
      });
      await page
        .getByRole("button", { name: "查看 Agent 足迹", exact: true })
        .click();
      await page.getByText("本次探索方向：" + label, { exact: true }).waitFor();
      await page.reload();
      await page
        .getByText("Mock 模式 · 规则生成")
        .waitFor({ state: "attached" });
      await nav("Agent 足迹");
      await page.locator(".run-list button").first().click();
      await page
        .locator(".run-detail .mono")
        .filter({ hasText: run.run_id })
        .waitFor();
      await page.getByText("本次探索方向：" + label, { exact: true }).waitFor();
      const persisted = await read(`/agent/runs/${run.run_id}`);
      assert.equal(persisted.state.request.exploration_direction, direction);
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
    }
  }
  assert.equal((await read("/quests")).length, questsBefore);
  assert.deepEqual(await read("/preferences"), preferenceBefore);
  console.log(
    "PASS: AGENT-004-A four directions, request → Mock result → persisted run after reload; no Quest/preferences writes; 1440/390",
  );
}
