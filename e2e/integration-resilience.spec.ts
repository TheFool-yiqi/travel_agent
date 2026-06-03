import { expect, test } from "@playwright/test";

import {
  backendReachable,
  createNewTrip,
  registerAndLogin,
  sendChatMessage,
  waitForAssistantReply,
} from "./helpers";

test.describe("集成 — 中断恢复与韧性", () => {
  test.describe.configure({ timeout: 900_000 });

  test("F5 刷新后继续对话（TC-FLOW-030 / TC-DATA-002）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");

    await registerAndLogin(page);
    await createNewTrip(page);
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/);

    await sendChatMessage(page, "北京");
    await waitForAssistantReply(page, /(从哪个城市出发|哪个城市出发)/);

    await page.reload();
    await expect(page.locator("#chat-message-input")).toBeVisible({ timeout: 120_000 });
    await expect(page.locator(".chat-body")).toHaveAttribute("aria-busy", "false", {
      timeout: 120_000,
    });
    await expect(page.locator("#chat-message-input")).toBeEnabled({ timeout: 120_000 });
    await expect(page.locator(".message-bubble-assistant").first()).toContainText(
      /(嗨|你好|北京|出发)/,
    );

    await sendChatMessage(page, "上海");
    await waitForAssistantReply(page, /(您大概想什么时候|几号|端午|本周末|小长假|从.+出发，交通)/);
  });

  test("旧会话再次打开不重复问候（TC-FLOW-071）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");

    await registerAndLogin(page);
    await createNewTrip(page);
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/);

    const greetingCount = await page.locator(".message-bubble-assistant").count();

    await page.getByRole("button", { name: "规划新行程" }).click();
    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|旅行顾问)/, 120_000);

    const items = page.locator(".conversation-item");
    await items.nth(1).click();
    await expect(page.locator(".message-bubble-assistant")).toHaveCount(greetingCount, {
      timeout: 30_000,
    });
  });
});
