import { expect, test } from "@playwright/test";

import {
  backendReachable,
  completePlanningToApproval,
  completeRequirementCollection,
  sendChatMessage,
  setupAuthenticatedTrip,
  waitForApprovalReady,
  waitForAssistantReply,
} from "./helpers";

test.describe("修订路径 — E2E", () => {
  test.describe.configure({ timeout: 1_800_000 });

  test("修改行程后二次确认生成 ORDER（TC-E2E-003 / FLOW-021）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动 (需 :8200)");

    await setupAuthenticatedTrip(page);
    await completeRequirementCollection(page);
    await completePlanningToApproval(page);

    await page.getByRole("button", { name: "请求修改" }).click();
    await waitForAssistantReply(page, /(将根据|重新生成|修改|收到|调整|行程|Day|第.{0,2}天)/, 600_000);

    await waitForApprovalReady(page, 600_000);

    await page.getByRole("button", { name: "确认行程" }).click();
    await waitForAssistantReply(page, /ORDER-[A-F0-9]{8,}/, 600_000);
  });

  test("对话式修订关键词（TC-FLOW-018）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动 (需 :8200)");

    await setupAuthenticatedTrip(page);
    await completeRequirementCollection(page);
    await completePlanningToApproval(page);

    await sendChatMessage(page, "change hotel");
    await waitForAssistantReply(page, /(将根据|重新生成|修改|收到|调整)/, 600_000);
  });
});
