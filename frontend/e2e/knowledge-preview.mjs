import assert from "node:assert/strict";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { chromium } from "playwright";
if (process.env.E2E_ALLOW_WRITE !== "true")
  throw new Error("Requires launcher-verified isolated Mock DB");
const base = process.env.E2E_BASE_URL || "http://127.0.0.1:5173";
const artifact = process.env.E2E_ARTIFACT_DIR || "../.cache/agent004f";
const material = JSON.parse(
  await readFile(
    new URL("../../evals/knowledge_preview_material.json", import.meta.url),
    "utf8",
  ),
);
await mkdir(artifact, { recursive: true });
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const api = async (path) =>
    (await page.request.get(base + "/api" + path)).json();
  assert.equal((await api("/health")).mock_mode, true);
  const seed = await page.request.post(base + "/api/stars", {
    data: {
      title: "海洋发光预览",
      original_text: "我想了解海洋生物为什么会发光",
      tags: ["海洋"],
    },
  });
  assert.equal(seed.status(), 201);
  const quests = await api("/quests");
  const preferences = await api("/preferences");
  const cases = [
    ["A", material.text],
    ["B", "测试材料A（虚构观察记录）：海洋观察小组在周一记录了三次发光现象。"],
    ["C", "测试材料B（不相关）：这份记录只列出了面包的包装颜色。"],
    [
      "D-limited",
      "测试材料C（限定条件）：部分海洋观察记录可能受到光照条件影响。",
    ],
    [
      "D-conflict",
      "测试材料D（冲突）：海洋记录甲称观察到发光；记录乙称没有观察到发光。",
    ],
    ["E", ""],
  ];
  const outputs = [];
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const [id, text] of cases) {
      await page.goto(base);
      await page
        .getByRole("navigation", { name: "主导航" })
        .getByRole("button", { name: /^微型探索/ })
        .click();
      await page.getByRole("radio", { name: /想了解一点知识/ }).check();
      await page.getByLabel("今天想靠近哪份好奇？").fill("海洋");
      await page.getByLabel("有想一起看的材料吗？（选填）").fill(text);
      if (text)
        await page
          .getByLabel("这段材料来自哪里？（选填）")
          .fill(id === "A" ? material.label : "公开虚构预览 " + id);
      const response = page.waitForResponse(
        (r) =>
          r.url().endsWith("/api/agent/runs") &&
          r.request().method() === "POST",
      );
      await page
        .getByRole("button", { name: "寻找小体验", exact: true })
        .click();
      const wire = await response;
      assert.equal(wire.status(), 201);
      const run = await wire.json();
      outputs.push({ id, width, state: run.state });
      const result = page.getByRole("region", { name: "本次探索结果" });
      await result.waitFor();
      const card = result.locator(".learning-card");
      assert.equal(await card.count(), ["C", "E"].includes(id) ? 0 : 1);
      assert.ok(run.state.proposals.length <= 1);
      assert.ok(run.state.validation.every((v) => v.valid));
      if (await card.count()) {
        assert.ok(
          await card
            .locator(".learning-takeaway")
            .evaluate((e) => parseFloat(getComputedStyle(e).fontSize) >= 17),
        );
        assert.deepEqual(run.state.questions, []);

        assert.equal(await card.locator("details").getAttribute("open"), null);
        assert.equal(await card.locator("blockquote").isVisible(), false);
        await card.screenshot({ path: `${artifact}/${id}-${width}-card.png` });
        await card.locator("summary").focus();
        await page.keyboard.press("Enter");
        assert.equal(await card.locator("blockquote").isVisible(), true);
        await card.screenshot({
          path: `${artifact}/${id}-${width}-expanded.png`,
        });
        await page.keyboard.press("Space");
        assert.equal(await card.locator("blockquote").isVisible(), false);
      }
      await result.screenshot({
        path: `${artifact}/${id}-${width}-result.png`,
      });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
    }
  }
  assert.deepEqual(await api("/quests"), quests);
  assert.deepEqual(await api("/preferences"), preferences);
  assert.deepEqual(errors, []);
  await writeFile(
    `${artifact}/preview.json`,
    JSON.stringify({ kind: "fixed-mock-not-model-quality", outputs }, null, 2),
  );
  console.log(
    "PASS knowledge preview A/B/C/D-limited/D-conflict/E; desktop/mobile; keyboard; no Quest/preferences writes",
  );
} finally {
  await browser.close();
}
