import { expect, test } from "@playwright/test";

import {
  backendReachable,
  createNewTrip,
  getConversationCount,
  registerAndLogin,
  waitForAssistantReply,
} from "./helpers";

test.describe("会话侧栏 UI", () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    test.setTimeout(120_000);
    await registerAndLogin(page);
  });

  test("侧栏多会话列表（TC-SESS-012 / TC-UI-007）", async ({ page }) => {
    await createNewTrip(page);
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/);

    await page.getByRole("button", { name: "规划新行程" }).click();
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/, 60_000);

    await expect(page.locator(".conversation-item")).toHaveCount(2, { timeout: 15_000 });
  });

  test("切换会话加载历史（TC-SESS-013 / TC-UI-008）", async ({ page }) => {
    await createNewTrip(page);
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/);

    await page.getByRole("button", { name: "规划新行程" }).click();
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/, 60_000);

    const items = page.locator(".conversation-item");
    await expect(items).toHaveCount(2);
    // 当前在第二个会话；切回第一个会话应加载历史问候
    await items.nth(1).click();
    await expect(items.nth(1)).toHaveClass(/conversation-item-active/);
    await expect(page.locator(".message-bubble-assistant").first()).toBeVisible({
      timeout: 30_000,
    });
  });

  test("删除会话确认对话框（TC-SESS-014）", async ({ page }) => {
    await createNewTrip(page);
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/);

    page.once("dialog", (dialog) => {
      expect(dialog.message()).toContain("确定删除");
      void dialog.dismiss();
    });

    await page.getByRole("button", { name: /删除/ }).first().click();
    expect(await getConversationCount(page)).toBeGreaterThanOrEqual(1);
  });

  test("移动端抽屉打开行程列表（TC-SESS-015 / TC-UI-009）", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.reload();
    await expect(page.getByRole("button", { name: "规划新行程" })).toBeVisible({
      timeout: 30_000,
    });
    await createNewTrip(page);
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/);

    await page.getByRole("button", { name: "打开行程列表" }).click();
    await expect(page.getByRole("dialog", { name: "我的行程" })).toBeVisible();
    await page.getByRole("button", { name: "关闭", exact: true }).click();
    await expect(page.getByRole("dialog", { name: "我的行程" })).not.toBeVisible();
  });
});
