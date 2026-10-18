import assert from "node:assert/strict";

// 由 smoke.mjs 在已核验的专用后端上执行；不连接日常个人服务。
export async function verifyResults(page, base, artifact) {
  const nav = async (name) =>
    page
      .getByRole("navigation", { name: "主导航" })
      .getByRole("button", { name: new RegExp("^" + name) })
      .click();
  const read = async (path) =>
    (await page.request.get(base + "/api" + path)).json();
  const counts = async () => {
    const [stars, quests] = await Promise.all([
      read("/stars"),
      read("/quests"),
    ]);
    return [
      stars.length,
      quests.length,
      quests.filter((q) => q.reflection).length,
    ];
  };
  const idle = async () =>
    page.getByText("正在处理，请稍候…").waitFor({ state: "hidden" });
  const create = async (type, text) => {
    await nav(type === "collect" ? "收集星星" : "微型探索");
    await page
      .getByLabel(
        type === "collect" ? "你最近对什么感到好奇？" : "今天想靠近哪份好奇？",
      )
      .fill(text);
    const response = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/agent/runs") && r.request().method() === "POST",
    );
    await page
      .getByRole("button", {
        name: type === "collect" ? "整理成草稿" : "寻找小体验",
        exact: true,
      })
      .click();
    const result = await (await response).json();
    await idle();
    return result;
  };
  const located = async (id) => {
    await page.waitForFunction((target) => {
      const el = document.getElementById(target);
      const rect = el?.getBoundingClientRect();
      if (!el || !rect || el !== document.activeElement) return false;
      // 页面底部不足一屏时，block:start 会受最大滚动位置限制。
      const top = rect.top + scrollY;
      const margin = parseFloat(getComputedStyle(el).scrollMarginTop) || 0;
      const maxScroll = Math.max(
        0,
        document.documentElement.scrollHeight - innerHeight,
      );
      const expected = top - Math.min(maxScroll, Math.max(0, top - margin));
      return (
        rect.top >= 0 &&
        rect.top < innerHeight - 60 &&
        Math.abs(rect.top - expected) < 2
      );
    }, id);
    assert.equal(await page.locator("#" + id).getAttribute("tabindex"), "-1");
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
      false,
    );
  };
  await page.addInitScript(() => {
    window.resultScrolls = [];
    const scroll = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function (options) {
      window.resultScrolls.push({ id: this.id, behavior: options?.behavior });
      return scroll.call(this, options);
    };
  });
  await page.reload();
  await page.getByRole("button", { name: "使用指南", exact: true }).waitFor();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({
      reducedMotion: width === 390 ? "reduce" : "no-preference",
    });
    const draft = await create("collect", "海洋 UX-002 定位 " + width);
    await located("collect-result-" + draft.run_id);
    await page.screenshot({ path: `${artifact}/result-focus-${width}.png` });
    await page.keyboard.press("Tab");
    assert.equal(
      await page
        .getByRole("region", { name: "本次收集结果" })
        .getByRole("button", { name: "查看 Agent 足迹" })
        .evaluate((el) => el === document.activeElement),
      true,
      "结果容器不进入 Tab 顺序，后续操作可正常访问",
    );
    assert.equal(
      await page.evaluate(() => window.resultScrolls.at(-1).behavior),
      width === 390 ? "auto" : "smooth",
    );
    const scrollCount = await page.evaluate(() => window.resultScrolls.length);
    await page.getByRole("button", { name: "刷新后端数据" }).click();
    await idle();
    assert.equal(
      await page.evaluate(() => window.resultScrolls.length),
      scrollCount,
      "普通刷新不重复定位",
    );
    // 从真实持久化运行恢复，而非内存里的旧结果。
    await page.reload();
    await idle();
    await nav("Agent 足迹");
    await page.locator(".run-list button").first().click();
    await idle();
    assert.equal(
      await page.locator(".run-detail .mono").textContent(),
      draft.run_id,
    );
    const before = await counts();
    await page.getByRole("button", { name: "打开待确认结果" }).click();
    await idle();
    await located("collect-result-" + draft.run_id);
    assert.deepEqual(await counts(), before);
    // 不匹配关键词得到真实澄清，仍定位到问题顶部。
    const clarification = await create("explore", "完全不在档案中的关键词xyz");
    assert.equal(clarification.state.proposals.length, 0);
    assert.ok(clarification.state.questions.length > 0);
    await located("explore-result-" + clarification.run_id);
    await page.screenshot({ path: `${artifact}/clarification-${width}.png` });
  }
  // 请求进行时切页：真实后端已生成，但响应延后送到页面。
  let release;
  let received;
  const gate = new Promise((resolve) => {
    release = resolve;
  });
  const responseReady = new Promise((resolve) => {
    received = resolve;
  });
  await page.route(
    "**/api/agent/runs",
    async (route) => {
      if (route.request().method() !== "POST") return route.continue();
      const response = await route.fetch();
      received();
      await gate;
      await route.fulfill({ response });
    },
    { times: 1 },
  );
  await nav("收集星星");
  await page.getByLabel("你最近对什么感到好奇？").fill("海洋 UX-002 切页");
  const scrollCount = await page.evaluate(() => window.resultScrolls.length);
  await page.getByRole("button", { name: "整理成草稿" }).click();
  await responseReady;
  await nav("我的偏好");
  release();
  await idle();
  assert.equal(await page.getByLabel("预算上限（元，可选）").count(), 1);
  assert.equal(
    await page.evaluate(() => window.resultScrolls.length),
    scrollCount,
  );

  // 临时后端启动器对这个无敏感文本仅一次注入 Mock timeout，重试走真实 API。
  let retried;
  if (process.env.E2E_INJECTED_FAILURE === "true") {
    const failed = await create("collect", "UX002-E2E-FAIL-海洋");
    const failedId = failed.detail.run_id;
    assert.ok(failedId, "必须是真实后端失败运行，不以通知猜测 ID");
    await page
      .getByRole("alert")
      .getByRole("button", { name: new RegExp(failedId) })
      .click();
    await idle();
    assert.equal(
      await page.locator(".run-detail .mono").textContent(),
      failedId,
    );
    const beforeRetry = await counts();
    const retryResponse = page.waitForResponse((r) =>
      r.url().endsWith("/" + failedId + "/retry"),
    );
    await page.getByRole("button", { name: "重试生成" }).click();
    retried = await (await retryResponse).json();
    await idle();
    assert.notEqual(retried.run_id, failedId);
    await located("collect-result-" + retried.run_id);
    assert.equal((await read("/agent/runs/" + failedId)).status, "failed");
    assert.deepEqual(await counts(), beforeRetry, "重试不自动批准正式记录");
  } else {
    console.log(
      "SKIP: real failure/retry browser fixture not enabled; no backend fault injected",
    );
    retried = await create("collect", "海洋 UX-002 精确导航");
  }

  // 精确 Star 导航：已有搜索/状态过滤也能找到新保存的目标。
  await nav("星星档案");
  await page.getByLabel("搜索星星").fill("不存在的兴趣");
  await page.getByLabel("星星状态筛选").selectOption("archived");
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await idle();
  await nav("收集星星");
  const decisionResponse = page.waitForResponse((r) =>
    r.url().endsWith("/" + retried.run_id + "/decision"),
  );
  await page.getByRole("button", { name: "确认保存星星" }).click();
  const decision = await (await decisionResponse).json();
  await idle();
  assert.ok(decision.star_id);
  const afterSave = await counts();
  for (let i = 0; i < 2; i++) {
    await page.getByRole("button", { name: "查看这颗星星" }).click();
    await idle();
    const dialog = page.getByRole("dialog");
    assert.equal(
      await dialog.getByLabel("标题", { exact: true }).inputValue(),
      (await read("/stars/" + decision.star_id)).title,
    );
    assert.equal(await page.getByLabel("搜索星星").inputValue(), "");
    assert.equal(await page.getByLabel("星星状态筛选").inputValue(), "");
    await dialog.getByRole("button", { name: "关闭弹窗" }).click();
    assert.equal(
      await page
        .locator("#star-card-" + decision.star_id)
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await nav("收集星星");
  }
  assert.deepEqual(await counts(), afterSave);

  // 多候选各自使用实际返回 quest_id；不自动打开反馈，不重复写入。
  const exploration = await create("explore", "海洋");
  assert.ok(exploration.state.proposals.length >= 2);
  await located("explore-result-" + exploration.run_id);
  const questIds = [];
  for (let i = 0; i < 2; i++) {
    const accepted = page.waitForResponse((r) =>
      r.url().endsWith("/" + exploration.run_id + "/decision"),
    );
    await page
      .locator(".proposal")
      .nth(i)
      .getByRole("button", { name: "接受这个体验" })
      .click();
    questIds.push((await (await accepted).json()).quest_id);
    await idle();
  }
  assert.ok(questIds.every(Boolean));
  assert.notEqual(questIds[0], questIds[1]);
  const afterAccept = await counts();
  for (const index of [1, 0, 1]) {
    await page
      .locator(".proposal")
      .nth(index)
      .getByRole("button", { name: "查看这次体验" })
      .click();
    await idle();
    await located("quest-" + questIds[index]);
    assert.equal(await page.getByRole("dialog").count(), 0);
    await page
      .locator("#quest-" + questIds[index])
      .getByRole("button", { name: "记录体验感受" })
      .waitFor();
    await page.screenshot({ path: `${artifact}/quest-target-${index}.png` });
    await nav("微型探索");
  }
  assert.deepEqual(await counts(), afterAccept);
  console.log(
    "PASS: UX-002 current result focus/reduced motion, persisted recovery, navigation cancellation, exact Star/Quest IDs, no duplicate writes; " +
      (process.env.E2E_INJECTED_FAILURE === "true"
        ? "real failed run retry verified"
        : "failure/retry fixture skipped"),
  );
}
