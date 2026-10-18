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
    const dialog = page.getByRole("dialog", { name: "星星详情" });
    await dialog
      .getByRole("heading", {
        name: (await read("/stars/" + decision.star_id)).title,
        exact: true,
      })
      .waitFor();
    assert.equal(await dialog.getByLabel("标题", { exact: true }).count(), 0);
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
  await verifyStarReading(page, base, artifact);
  console.log(
    "PASS: UX-002 current result focus/reduced motion, persisted recovery, navigation cancellation, exact Star/Quest IDs, no duplicate writes; " +
      (process.env.E2E_INJECTED_FAILURE === "true"
        ? "real failed run retry verified"
        : "failure/retry fixture skipped"),
  );
}

async function verifyStarReading(page, base, artifact) {
  const read = async (path) =>
    (await page.request.get(base + "/api" + path)).json();
  const nav = async (name) =>
    page
      .getByRole("navigation", { name: "主导航" })
      .getByRole("button", { name: new RegExp("^" + name) })
      .click();
  const idle = async () =>
    page.getByText("正在处理，请稍候…").waitFor({ state: "hidden" });
  let target = (await read("/stars"))[0];
  const writes = [];
  const record = (request) => {
    if (["POST", "PUT", "DELETE"].includes(request.method()))
      writes.push(request.method() + " " + request.url());
  };
  page.on("request", record);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const entry of ["我的星屿", "星星档案", "兴趣轨道", "微型探索"]) {
      await nav(entry);
      const trigger =
        entry === "我的星屿" || entry === "星星档案"
          ? page.locator("#star-card-" + target.id)
          : entry === "兴趣轨道"
            ? page
                .locator(".relation-card")
                .getByRole("button", { name: target.title, exact: true })
                .first()
            : page
                .locator(".rationale")
                .getByRole("button", { name: target.title, exact: true })
                .first();
      const count = writes.length;
      await trigger.click();
      await idle();
      const detail = page.getByRole("dialog", { name: "星星详情" });
      await detail
        .getByRole("heading", { name: target.title, exact: true })
        .waitFor();
      assert.equal(await detail.locator("input,textarea,select").count(), 0);
      assert.equal(
        await detail.getByRole("button", { name: "删除这颗星星" }).count(),
        0,
      );
      const rect = await detail.boundingBox();
      assert.ok(
        rect &&
          rect.x >= 0 &&
          rect.x + rect.width <= width &&
          rect.y >= 0 &&
          rect.y + rect.height <= 900,
      );
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      await detail.getByRole("button", { name: "关闭弹窗" }).click();
      assert.equal(
        await trigger.evaluate((el) => el === document.activeElement),
        true,
        `${entry} ${width}px 关闭后应恢复原查看入口焦点`,
      );
      assert.equal(writes.length, count, "查看与关闭不写 API");
    }
    await nav("星星档案");
    await page.locator("#star-card-" + target.id).click();
    const detail = page.getByRole("dialog", { name: "星星详情" });
    const count = writes.length;
    await detail.getByRole("button", { name: "编辑星星" }).click();
    const editor = page.getByRole("dialog", { name: "编辑兴趣星星" });
    assert.equal(
      await editor
        .getByLabel("标题", { exact: true })
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await editor.getByLabel("标题", { exact: true }).fill("取消这次修改");
    await editor.getByRole("button", { name: "取消编辑" }).click();
    await detail
      .getByRole("heading", { name: target.title, exact: true })
      .waitFor();
    assert.equal(writes.length, count, "取消编辑不写 API");
    await detail.getByRole("button", { name: "编辑星星" }).click();
    assert.equal(
      await editor.getByLabel("标题", { exact: true }).inputValue(),
      target.title,
    );
    const title = "海洋阅读测试 " + width;
    const description =
      "记录好奇，保留真实来源。\n".repeat(50) + "海".repeat(500);
    await editor.getByLabel("标题", { exact: true }).fill(title);
    await editor.getByLabel("整理后的描述").fill(description);
    await editor
      .getByLabel("参考链接（可选）", { exact: true })
      .fill("https://example.com/notes?topic=" + "curiosity".repeat(30));
    await page.route(
      "**/api/stars/" + target.id,
      (route) =>
        route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({ detail: "E2E 模拟编辑保存失败" }),
        }),
      { times: 1 },
    );
    await editor.getByRole("button", { name: "确认保存星星" }).click();
    await editor
      .getByRole("alert")
      .filter({ hasText: "E2E 模拟编辑保存失败" })
      .waitFor();
    await idle();
    assert.equal(
      await editor.getByLabel("标题", { exact: true }).inputValue(),
      title,
    );
    assert.equal((await read("/stars/" + target.id)).title, target.title);
    await editor.getByRole("button", { name: "确认保存星星" }).click();
    await idle();
    target = await read("/stars/" + target.id);
    assert.equal(target.title, title);
    assert.equal(target.description, description);
    const heading = detail.getByRole("heading", { name: title, exact: true });
    await heading.waitFor();
    assert.equal(
      await heading.evaluate((el) => el === document.activeElement),
      true,
    );
    assert.equal(await detail.locator("input,textarea,select").count(), 0);
    assert.equal(
      await detail.evaluate((el) => el.scrollWidth > el.clientWidth),
      false,
    );
    assert.ok(
      await detail.evaluate((el) => el.scrollHeight > el.clientHeight),
      "长详情应可滚动",
    );
    const close = detail.getByRole("button", { name: "关闭弹窗" });
    await close.focus();
    await page.keyboard.press("Tab");
    assert.equal(
      await detail
        .getByRole("link")
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await page.keyboard.press("Tab");
    assert.equal(
      await detail
        .getByRole("button", { name: "编辑星星" })
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await page.keyboard.press("Tab");
    assert.equal(
      await close.evaluate((el) => el === document.activeElement),
      true,
    );
    await heading.focus();
    await page.screenshot({ path: `${artifact}/star-reading-${width}.png` });
    await page.keyboard.press("Escape");
    assert.equal(
      await page
        .locator("#star-card-" + target.id)
        .evaluate((el) => el === document.activeElement),
      true,
    );
  }
  // 引用保护仍来自真实后端；明确编辑后可归档。
  const referencedId = (await read("/quests"))[0].based_on_star_ids[0];
  await nav("星星档案");
  await page.locator("#star-card-" + referencedId).click();
  await page.getByRole("button", { name: "编辑星星", exact: true }).click();
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "删除这颗星星" }).click();
  await idle();
  const editor = page.getByRole("dialog", { name: "编辑兴趣星星" });
  await editor.getByRole("alert").waitFor();
  await editor
    .getByRole("combobox", { name: /^状态/ })
    .selectOption("archived");
  await editor.getByRole("button", { name: "确认保存星星" }).click();
  await idle();
  assert.equal((await read("/stars/" + referencedId)).status, "archived");
  await page
    .getByRole("dialog", { name: "星星详情" })
    .getByRole("button", { name: "关闭弹窗" })
    .click();
  // 新手动记录无引用，删除仍可正常完成。
  await nav("收集星星");
  await page.getByRole("button", { name: "手动填写" }).click();
  await page.getByLabel("标题", { exact: true }).fill("用于删除验证的临时兴趣");
  await page.getByLabel("原始文字", { exact: true }).fill("E2E 独立库临时数据");
  await page.getByRole("button", { name: "确认保存星星" }).click();
  await idle();
  await page.getByRole("button", { name: "查看这颗星星" }).click();
  await idle();
  await page.getByRole("button", { name: "编辑星星", exact: true }).click();
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "删除这颗星星" }).click();
  await idle();
  assert.equal(await page.getByRole("dialog").count(), 0);
  assert.equal(
    (await read("/stars")).some(
      (star) => star.title === "用于删除验证的临时兴趣",
    ),
    false,
  );
  page.off("request", record);
  console.log(
    "PASS: all Star viewing entries read-only; edit/cancel/server-confirmed save/failure recovery; long text/link focus at 1440/390; deletion and archive protection",
  );
}
