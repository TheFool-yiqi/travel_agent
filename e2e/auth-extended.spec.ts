import { expect, test } from "@playwright/test";

import {
  AUTH_STORAGE_KEY,
  backendReachable,
  injectInvalidToken,
  registerAndLogin,
} from "./helpers";

test.describe("鉴权扩展", () => {
  test("登录/注册 Tab 切换（TC-AUTH-018 / TC-UI-003）", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "注册" }).click();
    await expect(page.getByLabel("邮箱")).toBeVisible();
    await page.getByRole("tab", { name: "登录" }).click();
    await expect(page.getByLabel("邮箱")).not.toBeVisible();
    await expect(page.getByLabel("用户名")).toBeVisible();
  });

  test("localStorage 刷新后保持登录（TC-AUTH-019）", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    test.setTimeout(60_000);

    await registerAndLogin(page);
    const stored = await page.evaluate((key) => localStorage.getItem(key), AUTH_STORAGE_KEY);
    expect(stored).toContain("token");

    await page.reload();
    await expect(page.getByRole("button", { name: "规划新行程" })).toBeVisible({
      timeout: 30_000,
    });
  });

  test("无效 token 触发重新登录（TC-FLOW-060 / TC-AUTH-020 / TC-UI-026 / TC-SEC-014）", async ({
    page,
  }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    test.setTimeout(60_000);

    await registerAndLogin(page);
    await injectInvalidToken(page);
    await page.reload();

    await expect(page.getByRole("tab", { name: "登录" })).toBeVisible({ timeout: 30_000 });
  });
});
