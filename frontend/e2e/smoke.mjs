import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "playwright";
import { verifyLearning } from "./learning.mjs";
import { verifyDirections } from "./directions.mjs";
import { verifyResults } from "./results.mjs";

// 对专用临时数据库执行真实写入，避免把测试兴趣混入个人档案。
if (process.env.E2E_ALLOW_WRITE !== "true")
  throw new Error("请使用独立测试数据库，并设置 E2E_ALLOW_WRITE=true");
const base = process.env.E2E_BASE_URL || "http://127.0.0.1:5173";
const artifact = process.env.E2E_ARTIFACT_DIR || "../.cache/e2e";
await mkdir(artifact, { recursive: true });
const tempDir = resolve(artifact, "browser-tmp");
await mkdir(tempDir, { recursive: true });
process.env.TEMP = tempDir;
process.env.TMP = tempDir;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
const failures = [];
page.on("pageerror", (error) => failures.push(error.message));
const marker = "海洋-" + Date.now();
const starTitle = "深海的微光";
try {
  await page.goto(base);
  await page.getByText("Mock 模式 · 规则生成").waitFor();
  assert.deepEqual(
    await (await page.request.get(`${base}/api/stars`)).json(),
    [],
    "首次引导必须使用全新隔离空库",
  );
  await page
    .getByRole("button", { name: "我有一个新念头", exact: true })
    .waitFor();
  await page.screenshot({
    path: artifact + "/home-before.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "我有一个新念头", exact: true })
    .click();
  await page
    .getByText(/一次整理生成一张可编辑草稿，确认后才会加入正式档案/)
    .waitFor();
  await page.getByText(/链接仅保存来源，不读取网页/).waitFor();
  await page
    .getByLabel("你最近对什么感到好奇？")
    .fill(marker + " 我想了解深海生物为什么会发光，想先记下几个好奇的问题。");
  await page.getByLabel("参考链接（可选）").fill("https://example.com/notes");
  await page.getByRole("button", { name: "整理成草稿" }).click();
  await page.getByText("正在处理，请稍候…").waitFor({ state: "hidden" });
  await page.getByRole("button", { name: "确认保存星星" }).waitFor();
  await page.getByText(/草稿已经生成，还没有加入正式档案/).waitFor();
  assert.equal(
    (await (await page.request.get(`${base}/api/stars`)).json()).length,
    0,
  );
  // 只在浏览器拦截一次批准请求，模拟失败；真实后端仍没有正式写入。
  await page.route(
    "**/api/agent/runs/*/decision",
    (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "E2E 模拟保存失败" }),
      }),
    { times: 1 },
  );
  await page.getByRole("button", { name: "确认保存星星" }).click();
  await page
    .getByRole("alert")
    .filter({ hasText: "E2E 模拟保存失败" })
    .waitFor();
  assert.equal(
    await page.getByRole("region", { name: "保存后的下一步" }).count(),
    0,
  );
  assert.equal(
    (await (await page.request.get(`${base}/api/stars`)).json()).length,
    0,
  );
  await page.getByRole("button", { name: "暂不保存" }).click();
  await page.getByText("这张草稿已放下，没有加入正式档案。").waitFor();
  assert.equal(
    (await (await page.request.get(`${base}/api/stars`)).json()).length,
    0,
  );
  await page.getByRole("button", { name: "我的星屿", exact: true }).click();
  await page
    .getByRole("button", { name: "我有一个新念头", exact: true })
    .click();
  await page.getByRole("button", { name: "整理成草稿" }).click();
  await page.getByText(/草稿已经生成，还没有加入正式档案/).waitFor();
  const draftNote = await page.locator(".soft-note").textContent();
  assert.match(draftNote, /兴趣原因、预计时间、预计预算、所需精力/);
  assert.doesNotMatch(
    draftNote,
    /interest_reason|estimated_minutes|estimated_budget|energy_level/,
  );
  await page
    .locator(".soft-note")
    .screenshot({ path: `${artifact}/draft-fields.png` });
  await page.getByLabel("标题", { exact: true }).fill(starTitle);
  await page
    .getByLabel("整理后的描述")
    .fill("发光的生物、安静的深海，还有它们不为人知的故事。");
  await page.getByRole("button", { name: "确认保存星星" }).click();
  await page.getByText("这份好奇已加入星星档案。").waitFor();
  const next = page.getByRole("region", { name: "保存后的下一步" });
  await next.getByRole("button", { name: "查看这颗星星" }).click();
  const savedEditor = page.getByRole("dialog", { name: "星星详情" });
  await savedEditor
    .getByRole("heading", { name: starTitle, exact: true })
    .waitFor();
  assert.equal(
    await savedEditor.getByLabel("标题", { exact: true }).count(),
    0,
  );
  await savedEditor.getByRole("button", { name: "关闭弹窗" }).click();
  await page.getByRole("button", { name: new RegExp(starTitle) }).waitFor();
  await page.getByRole("button", { name: "我的星屿", exact: true }).click();
  const coreActions = page.getByRole("group", { name: "首页核心功能" });
  await coreActions
    .getByRole("button", { name: "今天想找点灵感", exact: true })
    .waitFor();
  await coreActions
    .getByRole("button", { name: "我有一个新念头", exact: true })
    .click();
  await page
    .getByRole("region", { name: "保存后的下一步" })
    .getByRole("button", { name: "开始微型探索" })
    .click();
  assert.equal(
    (await (await page.request.get(`${base}/api/stars`)).json()).length,
    1,
    "下一步导航不能重复创建星星",
  );
  await page.getByRole("button", { name: /^收集星星/ }).click();

  // 第二颗真实星星与第一颗共享海洋标签。
  await page.getByLabel("你最近对什么感到好奇？").fill(marker + " 星空和海洋");
  await page.getByRole("button", { name: "整理成草稿" }).click();
  await page.getByText("正在处理，请稍候…").waitFor({ state: "hidden" });
  await page.getByLabel("标题", { exact: true }).fill("海洋与星空的对话");
  await page
    .getByLabel("整理后的描述")
    .fill("遥远的星星和深海里的光，是否也藏着相似的秘密？");
  await page.getByRole("button", { name: "确认保存星星" }).click();
  await page.getByText("这份好奇已加入星星档案。").waitFor();
  await page.getByRole("button", { name: "兴趣轨道", exact: true }).click();
  await page.getByText("共同标签：海洋").first().waitFor();
  await page.getByRole("button", { name: "星星档案", exact: true }).click();
  await page.getByLabel("搜索星星").fill(marker);
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await page
    .getByRole("button", { name: new RegExp(starTitle) })
    .first()
    .waitFor();

  await page.getByRole("button", { name: "我的偏好", exact: true }).click();
  await page.getByLabel("预算上限（元，可选）").fill("5");
  await page.getByRole("button", { name: "保存明确偏好" }).click();
  await page.getByText("明确偏好已保存。").waitFor();
  await page.getByRole("button", { name: "微型探索", exact: true }).click();
  await page.getByLabel("今天想靠近哪份好奇？").fill(marker);
  await page.getByLabel("可用时间（分钟，可选）").fill("10");
  const budget = page.getByLabel("本次预算（元，可选）");
  assert.equal(await budget.inputValue(), "");
  await page.getByText(/留空仍遵守偏好上限/).waitFor();
  const blankBudgetRequest = page.waitForRequest(
    (req) => req.method() === "POST" && req.url().endsWith("/api/agent/runs"),
  );
  await page.getByRole("button", { name: "寻找小体验" }).click();
  assert.equal((await blankBudgetRequest).postDataJSON().budget, null);
  await page.getByRole("button", { name: "接受这个体验" }).first().waitFor();
  // 再验证显式 0 元；不接受上一批候选，不产生额外 Quest。
  await budget.fill("0");
  const zeroBudgetRequest = page.waitForRequest(
    (req) => req.method() === "POST" && req.url().endsWith("/api/agent/runs"),
  );
  await page.getByRole("button", { name: "寻找小体验" }).click();
  assert.equal((await zeroBudgetRequest).postDataJSON().budget, 0);
  await page.getByText("正在处理，请稍候…").waitFor({ state: "hidden" });
  await page.getByRole("button", { name: "接受这个体验" }).first().waitFor();
  await page.screenshot({ path: artifact + "/explore.png", fullPage: true });
  await page.getByRole("button", { name: "接受这个体验" }).first().click();
  await page.getByText("已接受。可以在体验手记中记录结果。").waitFor();
  await page.getByRole("button", { name: "体验手记", exact: true }).click();
  await page.getByRole("button", { name: "修改体验" }).first().click();
  const editor = page.getByRole("dialog");
  await editor.getByLabel("标题", { exact: true }).fill("深海微光 · 问题手记");
  await editor.getByRole("button", { name: "确认修改并保存" }).click();
  await page.getByText("体验已更新。").waitFor();
  await page.getByRole("button", { name: "记录体验感受" }).first().click();
  await page
    .getByLabel("感受（可选）")
    .fill("E2E 测试：写问题让我更想了解海洋。");
  await page
    .getByLabel("喜欢的方面（可选，最多 20 项，每项不超过 80 字）", {
      exact: true,
    })
    .fill("自然观察，文字记录");
  await page.getByRole("button", { name: "保存真实反馈" }).click();
  await page.getByText("真实感受已保存。跳过也没关系。").waitFor();
  await page.getByRole("button", { name: "我的偏好", exact: true }).click();
  await page.getByText("你在反馈中写下喜欢：自然观察").waitFor();
  await page.getByRole("button", { name: "确认加入类别" }).first().click();
  await page.getByText("已加入明确兴趣类别，可继续编辑。").waitFor();
  await page.getByRole("button", { name: "Agent 足迹", exact: true }).click();
  await page.locator(".run-list button").first().click();
  await page.getByText("record_reflection", { exact: true }).waitFor();
  await page.screenshot({ path: artifact + "/run.png", fullPage: true });
  await page.getByRole("button", { name: "我的星屿", exact: true }).click();
  await page.screenshot({ path: artifact + "/home-after.png", fullPage: true });
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const name of [
      "我的星屿",
      "收集星星",
      "星星档案",
      "兴趣轨道",
      "微型探索",
      "体验手记",
      "Agent 足迹",
      "我的偏好",
    ]) {
      await page
        .getByRole("navigation", { name: "主导航" })
        .getByRole("button", { name: new RegExp("^" + name) })
        .click();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > window.innerWidth,
      );
      assert.equal(overflow, false, `${name}在 ${width}px 不应横向溢出`);
      await page.screenshot({
        path: `${artifact}/${name}-${width}.png`,
        fullPage: true,
      });
      assert.equal(await page.locator(".main-content .usage-guide").count(), 0);
      const guideToggle = page.getByRole("button", {
        name: "使用指南",
        exact: true,
      });
      const toolbar = page.locator(".topbar-actions");
      const boxes = await Promise.all(
        [
          toolbar.locator(".mode-label"),
          guideToggle,
          toolbar.getByRole("button", { name: "刷新后端数据" }),
        ].map((el) => el.boundingBox()),
      );
      for (let i = 0; i < boxes.length; i++) {
        const box = boxes[i];
        assert.ok(
          box && box.x >= 0 && box.x + box.width <= width,
          "顶栏操作应在屏幕内",
        );
        if (i > 0)
          assert.ok(
            boxes[i - 1].x + boxes[i - 1].width <= box.x,
            "顶栏操作不得重叠",
          );
      }
      if (name === "我的星屿") {
        const entryWrites = [];
        const observeEntry = (request) => {
          if (request.method() !== "GET")
            entryWrites.push(
              request.method() + " " + new URL(request.url()).pathname,
            );
        };
        page.on("request", observeEntry);
        const actions = page.getByRole("group", { name: "首页核心功能" });
        const buttons = actions.locator(".hero-core-action");
        assert.equal(await buttons.count(), 3);
        const rects = await buttons.evaluateAll((els) =>
          els.map((el) => {
            const { x, y, width, height } = el.getBoundingClientRect();
            return {
              x,
              y,
              width,
              height,
              weight: getComputedStyle(el).fontWeight,
            };
          }),
        );
        for (const rect of rects)
          assert.ok(
            rect.width >= 130 &&
              rect.height >= 44 &&
              rect.x >= 0 &&
              rect.x + rect.width <= width,
          );
        for (let i = 0; i < rects.length; i++)
          for (let j = i + 1; j < rects.length; j++)
            assert.ok(
              rects[i].x + rects[i].width <= rects[j].x ||
                rects[i].y + rects[i].height <= rects[j].y,
              "首页按钮不得重叠",
            );
        const restingColors = await buttons.evaluateAll((els) =>
          els.map((el) => getComputedStyle(el).backgroundColor),
        );
        assert.equal(
          new Set(restingColors).size,
          3,
          "三个入口有克制的独立底色",
        );
        await buttons.nth(0).hover();
        await page.waitForTimeout(180);
        assert.notEqual(
          await buttons
            .nth(0)
            .evaluate((el) => getComputedStyle(el).backgroundColor),
          restingColors[0],
          "hover 应有可见反馈",
        );
        await page.screenshot({
          path: artifact + `/home-invitation-hover-${width}.png`,
          fullPage: true,
        });
        const inspire = actions.getByRole("button", {
          name: "今天想找点灵感",
          exact: true,
        });
        await inspire.hover();
        await page.waitForTimeout(180);
        const hoverColor = await inspire.evaluate(
          (el) => getComputedStyle(el).backgroundColor,
        );
        await page.mouse.down();
        await page.waitForTimeout(180);
        assert.notEqual(
          await inspire.evaluate((el) => getComputedStyle(el).backgroundColor),
          hoverColor,
          "按下态应有反馈",
        );
        await page.mouse.up();
        await page.getByRole("region", { name: "一点小建议" }).waitFor();
        await page.keyboard.press("Space");
        await page
          .getByRole("region", { name: "一点小建议" })
          .waitFor({ state: "hidden" });
        await actions
          .getByRole("button", { name: "我有一个新念头", exact: true })
          .focus();
        await page.keyboard.press("Tab");
        await page.keyboard.press("Tab");
        assert.equal(
          await inspire.evaluate(
            (el) =>
              el === document.activeElement && el.matches(":focus-visible"),
          ),
          true,
        );
        assert.ok(
          await inspire.evaluate(
            (el) => parseFloat(getComputedStyle(el).outlineWidth) >= 2,
          ),
          "键盘焦点边框清晰",
        );
        await page.keyboard.press("Enter");
        const suggestion = page.getByRole("region", { name: "一点小建议" });
        await suggestion.waitFor();
        await page.screenshot({
          path: artifact + `/home-invitation-help-${width}.png`,
          fullPage: true,
        });
        await suggestion.getByRole("button", { name: "看看这颗星星" }).click();
        await page
          .getByRole("dialog")
          .getByRole("button", { name: "编辑星星" })
          .waitFor();
        await page.keyboard.press("Escape");
        await suggestion.getByRole("button", { name: "先放一放" }).click();
        assert.equal(rects[0].weight, rects[1].weight);
        const before = await Promise.all(
          ["stars", "quests"].map(
            async (resource) =>
              (await (await page.request.get(`${base}/api/${resource}`)).json())
                .length,
          ),
        );
        for (const label of ["我有一个新念头", "我想看看以前的星星"]) {
          await actions
            .getByRole("button", { name: label, exact: true })
            .click();
          await page
            .getByRole("navigation", { name: "主导航" })
            .getByRole("button", { name: "我的星屿", exact: true })
            .click();
        }
        const after = await Promise.all(
          ["stars", "quests"].map(
            async (resource) =>
              (await (await page.request.get(`${base}/api/${resource}`)).json())
                .length,
          ),
        );
        assert.deepEqual(after, before, "首页导航不创建 Star 或 Quest");
        page.off("request", observeEntry);
        assert.deepEqual(entryWrites, [], "邀请入口不生成模型请求或写入");
      }
      await guideToggle.focus();
      await page.keyboard.press("Enter");
      const guide = page.getByRole("dialog", { name: "星屿怎么使用" });
      await guide.waitFor();
      const close = guide.getByRole("button", { name: "关闭弹窗" });
      assert.equal(
        await close.evaluate((el) => el === document.activeElement),
        true,
      );
      await page.keyboard.press("Tab");
      assert.equal(
        await close.evaluate((el) => el === document.activeElement),
        true,
      );
      await page.keyboard.press("Shift+Tab");
      assert.equal(
        await close.evaluate((el) => el === document.activeElement),
        true,
      );
      await guide.getByText(/不代表真实大模型理解/).waitFor();
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > window.innerWidth,
        ),
        false,
      );
      await page.screenshot({
        path: `${artifact}/${name}-guide-${width}.png`,
        fullPage: true,
      });
      const dialogBox = await guide.boundingBox();
      assert.ok(
        dialogBox && dialogBox.x >= 0 && dialogBox.x + dialogBox.width <= width,
      );
      assert.ok(dialogBox.y >= 0 && dialogBox.y + dialogBox.height <= 900);
      await page.keyboard.press("Escape");
      await guide.waitFor({ state: "hidden" });
      assert.equal(
        await guideToggle.evaluate((el) => el === document.activeElement),
        true,
      );
      await guideToggle.click();
      await close.click();
      await guideToggle.click();
      await page.locator(".modal-backdrop").click({ position: { x: 3, y: 3 } });
      await guide.waitFor({ state: "hidden" });
      assert.equal(
        await guideToggle.evaluate((el) => el === document.activeElement),
        true,
      );
      if (name === "微型探索") {
        const writes = [];
        const listener = (request) => {
          if (request.method() !== "GET" && request.url().includes("/api/"))
            writes.push(request.url());
        };
        page.on("request", listener);
        const radios = page.getByRole("radio");
        const knowledge = page.getByRole("radio", { name: /想了解一点知识/ });
        await knowledge.focus();
        await page.keyboard.press("Space");
        assert.equal(await knowledge.isChecked(), true);
        await page.getByText(/不能保证直接给出经过核验的科学答案/).waitFor();
        assert.equal(
          await knowledge.evaluate((el) => el.matches(":focus-visible")),
          true,
        );
        await page.screenshot({
          path: `${artifact}/direction-knowledge-${width}.png`,
          fullPage: true,
        });
        await page.keyboard.press("ArrowRight");
        assert.equal(
          await page.getByRole("radio", { name: /想动手试试看/ }).isChecked(),
          true,
        );
        await page.keyboard.press("ArrowRight");
        assert.equal(
          await page.getByRole("radio", { name: /想发挥一点创意/ }).isChecked(),
          true,
        );
        await page.keyboard.press("ArrowRight");
        assert.equal(
          await page.getByRole("radio", { name: /还没想好/ }).isChecked(),
          true,
        );
        for (const radio of await radios.all()) {
          const box = await radio.locator("..").boundingBox();
          assert.ok(box && box.x >= 0 && box.x + box.width <= width);
        }
        assert.deepEqual(writes, [], "切换方向不得产生 API 写请求");
        page.off("request", listener);
      }
      if (name === "微型探索" || name === "我的偏好") {
        const help = page.locator("details.form-help");
        const toggle = help.locator("summary");
        assert.equal(await help.evaluate((el) => el.open), false);
        await toggle.focus();
        await page.keyboard.press("Enter");
        assert.equal(
          await help.evaluate((el) => el.open),
          true,
          "Enter 应展开帮助",
        );
        assert.equal(
          await page.evaluate(
            () => document.documentElement.scrollWidth > window.innerWidth,
          ),
          false,
        );
        await page.screenshot({
          path: `${artifact}/${name}-help-${width}.png`,
          fullPage: true,
        });
        await page.keyboard.press("Space");
        assert.equal(
          await help.evaluate((el) => el.open),
          false,
          "Space 应收起帮助",
        );
        await toggle.click();
        assert.equal(
          await help.evaluate((el) => el.open),
          true,
          "点击应展开帮助",
        );
        await toggle.click();
      }
    }
  }
  await verifyResults(page, base, artifact);
  await verifyDirections(page, base, artifact);
  await verifyLearning(page, base, artifact);
  assert.deepEqual(failures, [], "不应出现浏览器脚本异常");
  console.log(
    "PASS: collection → draft approval → archive/search → relations → proposal approval → edit → reflection → preference confirmation → audit; desktop/mobile",
  );
} finally {
  await browser.close();
}
