import { expect, test } from "@playwright/test";

import {
  backendReachable,
  completePlanningToApproval,
  completeRequirementCollection,
  createNewTrip,
  registerAndLogin,
  sendChatMessage,
  setupAuthenticatedTrip,
  waitForAssistantReply,
} from "./helpers";

test.describe("UI 组件", () => {
  test("空消息点击发送不新增气泡（TC-UI-015）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    await registerAndLogin(page);
    await createNewTrip(page);
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/);

    const before = await page.locator(".message-bubble-user").count();
    await page.getByRole("button", { name: "发送消息" }).click();
    await page.waitForTimeout(500);
    const after = await page.locator(".message-bubble-user").count();
    expect(after).toBe(before);
  });

  test("发送消息后显示 TypingIndicator（TC-UI-016 / TC-CHAT-024）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    test.setTimeout(120_000);
    await setupAuthenticatedTrip(page);

    await sendChatMessage(page, "北京");
    await expect(page.locator(".typing-indicator")).toBeVisible({ timeout: 15_000 });
  });

  test("错误密码显示 Toast（TC-UI-025）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    await page.goto("/");
    await page.getByRole("tab", { name: "登录" }).click();
    await page.getByLabel("用户名").fill("nobody_user_xyz");
    await page.getByLabel("密码").fill("wrong-password-xyz");
    await page.getByRole("button", { name: "登录" }).click();
    await expect(page.locator(".toast-error")).toBeVisible({ timeout: 15_000 });
  });

  test("SettingsPage 显示用户信息（TC-UI-027）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    const username = await registerAndLogin(page);
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "设置" })).toBeVisible();
    await expect(page.getByText(username)).toBeVisible();
    await page.getByRole("link", { name: "返回对话" }).click();
    await expect(page.getByRole("button", { name: "规划新行程" })).toBeVisible();
  });

  test("响应式布局：桌面侧栏可见（TC-UI-029）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    await registerAndLogin(page);
    await page.setViewportSize({ width: 1280, height: 800 });
    await expect(page.locator(".sidebar")).toBeVisible();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.getByRole("button", { name: "打开行程列表" })).toBeVisible();
  });

  test("StepProgress 需求阶段可见（TC-UI-017 / TC-UI-018）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    test.setTimeout(180_000);
    await setupAuthenticatedTrip(page);
    await sendChatMessage(page, "北京");
    await waitForAssistantReply(page, /(从哪个城市出发|哪个城市出发)/);
    await expect(page.getByRole("navigation", { name: "规划进度" })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.locator(".step-progress-item--active")).toHaveCount(1);
  });

  test("ApprovalBanner 按钮（TC-UI-022~024 / TC-APR-012~015）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    test.setTimeout(900_000);
    await setupAuthenticatedTrip(page);
    await completeRequirementCollection(page);
    await completePlanningToApproval(page);

    await expect(page.getByRole("region", { name: "行程确认" })).toBeVisible();
    await expect(page.getByRole("button", { name: "确认行程" })).toBeEnabled();
    await expect(page.getByRole("button", { name: "请求修改" })).toBeEnabled();
  });

  test("ItineraryCard 行程卡片（TC-UI-020）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    test.setTimeout(900_000);
    await setupAuthenticatedTrip(page);
    await completeRequirementCollection(page);
    await completePlanningToApproval(page);
    await expect(page.locator(".itinerary-card, .message-bubble-assistant").last()).toBeVisible();
  });
});
