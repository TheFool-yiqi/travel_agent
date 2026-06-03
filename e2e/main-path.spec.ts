import { expect, test } from "@playwright/test";

import {
  backendReachable,
  createNewTrip,
  registerAndLogin,
  sendChatMessage,
  waitForAssistantReply,
} from "./helpers";

test.describe("主路径 — UI 前几步", () => {
  test.describe.configure({ timeout: 180_000 });

  test.beforeEach(async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动 (需 :8200)");
    await registerAndLogin(page);
    await createNewTrip(page);
  });

  test("新建行程收到问候并推进到出发城市", async ({ page }) => {
    test.setTimeout(180_000);

    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|哪里|旅行顾问)/);

    await sendChatMessage(page, "北京");
    await waitForAssistantReply(page, /(从哪个城市出发|哪个城市出发)/);
  });

  test("进度条显示需求阶段", async ({ page }) => {
    test.setTimeout(180_000);

    await waitForAssistantReply(page, /(嗨|你好|想去|目的地|哪里|旅行顾问)/);
    await sendChatMessage(page, "北京");
    await waitForAssistantReply(page, /(从哪个城市出发|哪个城市出发)/);

    await expect(page.getByRole("navigation", { name: "规划进度" })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByText("需求", { exact: true })).toBeVisible();
  });
});
