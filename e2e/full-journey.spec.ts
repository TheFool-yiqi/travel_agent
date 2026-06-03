import { expect, test } from "@playwright/test";

import {
  backendReachable,
  completePlanningToApproval,
  completeRequirementCollection,
  setupAuthenticatedTrip,
  waitForAssistantReply,
} from "./helpers";

test.describe("端到端 — 主路径至订单", () => {
  test.describe.configure({ timeout: 900_000 });

  test("新用户注册→首行程→问候（TC-E2E-001）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动 (需 :8200)");
    await setupAuthenticatedTrip(page);
    await expect(page.getByRole("button", { name: "规划新行程" })).toBeVisible();
  });

  test("主路径需求收集至规划（TC-E2E-002 前半）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动 (需 :8200)");
    await setupAuthenticatedTrip(page);
    await completeRequirementCollection(page);
    await expect(page.getByRole("navigation", { name: "规划进度" })).toBeVisible({
      timeout: 30_000,
    });
  });

  test("主路径全流程至 ORDER（TC-E2E-002 / FLOW-020）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动 (需 :8200)");
    await setupAuthenticatedTrip(page);
    await completeRequirementCollection(page);
    await completePlanningToApproval(page);

    await page.getByRole("button", { name: "确认行程" }).click();
    await waitForAssistantReply(page, /ORDER-[A-F0-9]{8,}/, 180_000);
  });
});
