import assert from "node:assert/strict";

// Only use with a launcher-verified isolated Mock database. Synthetic test text.
export async function verifyLearning(page, base, artifact) {
  const text = "测试材料C（限定条件）：部分海洋观察记录可能受到光照条件影响。";
  const read = async (path) =>
    (await page.request.get(base + "/api" + path)).json();
  assert.equal((await read("/health")).mock_mode, true);
  const quests = await read("/quests");
  const preferences = await read("/preferences");
  const nav = (name) =>
    page
      .getByRole("navigation", { name: "主导航" })
      .getByRole("button", { name: new RegExp("^" + name) })
      .click();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await nav("微型探索");
    await page.getByRole("radio", { name: /想了解一点知识/ }).check();
    const input = page.getByLabel("有想一起看的材料吗？（选填）");
    await input.fill(text);
    assert.equal(await input.getAttribute("maxlength"), "5000");
    await page
      .getByLabel("这段材料来自哪里？（选填）")
      .fill("公开虚构测试材料C");
    await page
      .getByLabel("参考 URL（选填，仅记录，不访问）")
      .fill("https://example.org/test");
    await page.getByText(/预览本次材料/).click();
    await page.locator(".material-preview").filter({ hasText: text }).waitFor();
    await page.screenshot({
      path: `${artifact}/learning-input-${width}.png`,
      fullPage: true,
    });
    await page.getByRole("radio", { name: /想发挥一点创意/ }).check();
    assert.equal(await input.count(), 0);
    await page.getByRole("radio", { name: /想了解一点知识/ }).check();
    await page.getByLabel("今天想靠近哪份好奇？").fill("海洋");
    await input.focus();
    await page.keyboard.press("Tab");
    assert.equal(
      await page
        .getByLabel("这段材料来自哪里？（选填）")
        .evaluate((e) => e === document.activeElement),
      true,
    );
    const response = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/agent/runs") && r.request().method() === "POST",
    );
    await page.getByRole("button", { name: "寻找小体验", exact: true }).click();
    const wire = await response;
    const run = await wire.json();
    assert.equal(wire.status(), 201);
    assert.equal(wire.request().postDataJSON().learning_source.text, text);
    const card = page
      .getByRole("region", { name: "本次探索结果" })
      .getByRole("region", { name: "基于材料的知识微探索" });
    // section has an accessible region role through its label.
    await card.getByText("原文依据", { exact: true }).waitFor();
    assert.match(await card.innerText(), /部分.*可能/);
    assert.equal(
      await card.locator("blockquote").innerText(),
      run.state.learning_card.evidence_quote,
    );
    await page.screenshot({
      path: `${artifact}/learning-result-${width}.png`,
      fullPage: true,
    });
    await page.reload();
    await page.getByRole("button", { name: "使用指南", exact: true }).waitFor();
    await nav("Agent 足迹");
    await page.locator(".run-list button").first().click();
    await page
      .locator(".run-detail .mono")
      .filter({ hasText: run.run_id })
      .waitFor();
    await page
      .locator(".run-detail .learning-card blockquote")
      .filter({ hasText: run.state.learning_card.evidence_quote })
      .waitFor();
    assert.deepEqual(
      (await read(`/agent/runs/${run.run_id}`)).state.learning_card,
      run.state.learning_card,
    );
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
      false,
    );
    await page.screenshot({
      path: `${artifact}/learning-reloaded-${width}.png`,
      fullPage: true,
    });
  }
  assert.deepEqual(await read("/quests"), quests);
  assert.deepEqual(await read("/preferences"), preferences);
  console.log(
    "PASS: AGENT-004-B input/preview/keyboard/card/refresh; 1440/390; no Quest/preferences writes",
  );
}
