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
  await page.screenshot({
    path: artifact + "/home-before.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /^收集星星/ }).click();
  await page
    .getByLabel("你最近对什么感到好奇？")
    .fill(marker + " 我想了解深海生物和海洋的微光。");
  await page.getByRole("button", { name: "整理成草稿" }).click();
  await page.getByText("正在处理，请稍候…").waitFor({ state: "hidden" });
  await page.getByRole("button", { name: "确认保存星星" }).waitFor();
  await page.getByLabel("标题", { exact: true }).fill(starTitle);
  await page
    .getByLabel("整理后的描述")
    .fill("发光的生物、安静的深海，还有它们不为人知的故事。");
  await page.getByRole("button", { name: "确认保存星星" }).click();
  await page.getByText("这份好奇已加入星星档案。").waitFor();

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

  await page.getByRole("button", { name: "微型探索", exact: true }).click();
  await page.getByLabel("今天想靠近哪份好奇？").fill(marker);
  await page.getByLabel("可用时间（分钟）").fill("10");
  await page.getByLabel("预算（元，留空不限）").fill("0");
  await page.getByRole("button", { name: "寻找小体验" }).click();
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
    .getByLabel("喜欢的方面（逗号分隔）", { exact: true })
    .fill("自然观察, 文字记录");
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
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: artifact + "/mobile.png", fullPage: true });
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  assert.equal(overflow, false, "移动端不应横向溢出");
  assert.deepEqual(failures, [], "不应出现浏览器脚本异常");
  console.log(
    "PASS: collection → draft approval → archive/search → relations → proposal approval → edit → reflection → preference confirmation → audit; desktop/mobile",
  );
} finally {
  await browser.close();
}
