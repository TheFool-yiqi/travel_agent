import { expect, test } from "@playwright/test";

import { backendReachable, registerAndLogin } from "./helpers";

test.describe("鉴权壳层", () => {
  test("未登录显示登录浮层", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /diao-travelagent/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: "登录" })).toBeVisible();
  });

  test("注册后进入主界面", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动");
    test.setTimeout(60_000);

    await registerAndLogin(page);
    await expect(page.getByText("我的行程")).toBeVisible();
  });
});
