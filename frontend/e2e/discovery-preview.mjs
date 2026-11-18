import assert from "node:assert/strict";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { chromium } from "playwright";
if (process.env.E2E_ALLOW_WRITE !== "true")
  throw new Error("Requires launcher-verified isolated Mock DB");
const base = process.env.E2E_BASE_URL || "http://127.0.0.1:5173";
const artifact = process.env.E2E_ARTIFACT_DIR || "../.cache/agent004h";
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
    ["B", material.text],
    [
      "weak",
      "测试材料A（虚构观察记录）：海洋观察小组在周一记录了三次发光现象。",
    ],
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
      await page
        .getByLabel("今天想靠近哪份好奇？")
        .fill(id === "B" ? "海洋发光：预测光也能帮助脱身吗？" : "海洋");
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
      outputs.push({ id, width, run_id: run.run_id, state: run.state });
      const result = page.getByRole("region", { name: "本次探索结果" });
      await result.waitFor();
      const card = result.locator(".learning-card");
      assert.equal(await card.count(), ["C", "E"].includes(id) ? 0 : 1);
      assert.ok(run.state.proposals.length <= 1);
      assert.ok(run.state.validation.every((v) => v.valid));
      if (id !== "E") {
        assert.equal(run.status, "succeeded");
        assert.deepEqual(run.state.proposals, []);
        assert.equal(
          await result.getByRole("button", { name: /接受|编辑候选/ }).count(),
          0,
        );
        assert.doesNotMatch(
          await result.innerText(),
          /本次没有可查看|还需要一点信息/,
        );
      }
      if (await card.count()) {
        if (id === "B") {
          let requests = [];
          const watch = (request) => {
            if (request.url().includes("/api/"))
              requests.push(request.method());
          };
          page.on("request", watch);
          assert.equal(
            await card.locator(".learning-extension").isVisible(),
            true,
          );
          assert.equal(
            await card.locator(".learning-details").isVisible(),
            true,
          );
          assert.equal(
            await card.locator(".learning-takeaway").last().isVisible(),
            true,
          );
          await card.screenshot({ path: `${artifact}/B-${width}-before.png` });
          const reveal = card.getByRole("button", {
            name: /揭晓答案|收起答案/,
          });
          await reveal.focus();
          await page.keyboard.press("Enter");
          assert.equal(await reveal.getAttribute("aria-expanded"), "true");
          assert.equal(
            await reveal.evaluate((e) => e === document.activeElement),
            true,
          );
          assert.equal(
            await card.locator(".learning-reveal").isVisible(),
            true,
          );
          await card.screenshot({
            path: `${artifact}/B-${width}-revealed.png`,
          });
          await page.keyboard.press("Space");
          assert.equal(await reveal.getAttribute("aria-expanded"), "false");
          await page.keyboard.press("Space");
          assert.deepEqual(requests, []);
          page.off("request", watch);
        }
        assert.ok(
          await card
            .locator(".learning-takeaway")
            .first()
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
  await page.reload();
  await page.getByRole("button", { name: "使用指南", exact: true }).waitFor();
  await page
    .getByRole("navigation", { name: "主导航" })
    .getByRole("button", { name: /^Agent 足迹/ })
    .click();
  await page.locator(".run-list button").first().click();
  const saved = await api("/agent/runs");
  const scienceId = outputs.find((o) => o.id === "B" && o.width === 390).run_id;
  const index = saved.findIndex((r) => r.run_id === scienceId);
  assert.ok(index >= 0);
  await page.locator(".run-list button").nth(index).click();
  const historical = page.locator(".run-detail .learning-card");
  await historical.waitFor();
  assert.equal(
    await historical
      .getByRole("button", { name: "揭晓答案" })
      .getAttribute("aria-expanded"),
    "false",
  );
  assert.equal(
    await historical.locator(".learning-extension").isVisible(),
    true,
  );
  assert.equal(
    await page.getByRole("button", { name: "打开待确认结果" }).count(),
    0,
  );
  await historical.getByRole("button", { name: "揭晓答案" }).click();
  assert.equal(await historical.locator(".learning-reveal").isVisible(), true);
  assert.deepEqual(
    (await api(`/agent/runs/${scienceId}`)).state,
    outputs.find((o) => o.run_id === scienceId).state,
  );
  await historical.screenshot({ path: `${artifact}/history-390.png` });
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
