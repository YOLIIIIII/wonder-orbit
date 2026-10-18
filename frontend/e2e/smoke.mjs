import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "playwright";

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
    .getByRole("button", { name: "收集第一颗星星", exact: true })
    .waitFor();
  await page.screenshot({
    path: artifact + "/home-before.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "收集第一颗星星", exact: true })
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
    .getByRole("button", { name: "收集第一颗星星", exact: true })
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
  await next.getByRole("button", { name: "查看星星档案" }).click();
  await page.getByRole("button", { name: new RegExp(starTitle) }).waitFor();
  await page.getByRole("button", { name: "我的星屿", exact: true }).click();
  await page
    .getByRole("button", { name: "开始微型探索", exact: true })
    .waitFor();
  await page.getByRole("button", { name: "继续收集星星", exact: true }).click();
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
    for (const name of ["我的星屿", "收集星星", "微型探索", "我的偏好"]) {
      await page.getByRole("button", { name: new RegExp("^" + name) }).click();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > window.innerWidth,
      );
      assert.equal(overflow, false, `${name}在 ${width}px 不应横向溢出`);
      await page.screenshot({
        path: `${artifact}/${name}-${width}.png`,
        fullPage: true,
      });
      const guide = page.locator("details.usage-guide");
      const guideToggle = guide.locator("summary");
      await guideToggle.focus();
      await page.keyboard.press("Enter");
      assert.equal(await guide.evaluate((el) => el.open), true);
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
      await page.keyboard.press("Space");
      assert.equal(await guide.evaluate((el) => el.open), false);
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
  assert.deepEqual(failures, [], "不应出现浏览器脚本异常");
  console.log(
    "PASS: collection → draft approval → archive/search → relations → proposal approval → edit → reflection → preference confirmation → audit; desktop/mobile",
  );
} finally {
  await browser.close();
}
