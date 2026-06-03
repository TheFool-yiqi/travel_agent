import { expect, type Page } from "@playwright/test";

const API_BASE =
  process.env.PLAYWRIGHT_API_BASE_URL ?? "http://localhost:8200/api/v1";

export function uniqueUsername(prefix = "smoke"): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export async function registerAndLogin(page: Page, username?: string): Promise<string> {
  const name = username ?? uniqueUsername();
  const password = "smoke-test-pass";

  await page.goto("/");
  await page.getByRole("tab", { name: "注册" }).click();
  await page.getByLabel("用户名").fill(name);
  await page.getByLabel("邮箱").fill(`${name}@example.com`);
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: "注册" }).click();

  const mainButton = page.getByRole("button", { name: "规划新行程" });
  const errorHint = page.getByText(/注册失败|用户名已存在|请求失败|网络/i);
  const outcome = await Promise.race([
    mainButton.waitFor({ state: "visible", timeout: 60_000 }).then(() => "ok" as const),
    errorHint.waitFor({ state: "visible", timeout: 60_000 }).then(() => "error" as const),
  ]).catch(() => "timeout" as const);

  if (outcome !== "ok") {
    const hint = outcome === "error" ? await errorHint.textContent() : "backend 无响应（检查 :8200）";
    throw new Error(`注册未完成: ${hint}`);
  }

  await expect(mainButton).toBeVisible();

  return name;
}

export async function createNewTrip(page: Page): Promise<void> {
  await page.getByRole("button", { name: "规划新行程" }).click();
  const input = page.locator("#chat-message-input");
  await expect(input).toBeVisible({ timeout: 15_000 });
  await expect(input).toBeEnabled({ timeout: 30_000 });
}

export async function sendChatMessage(page: Page, content: string): Promise<void> {
  const input = page.locator("#chat-message-input");
  await expect(input).toBeEnabled({ timeout: 300_000 });
  await input.fill(content);
  await page.getByRole("button", { name: "发送消息" }).click();
}

/** 等待助手回复完成且输入框可再次编辑 */
export async function waitForChatReady(page: Page, timeout = 300_000): Promise<void> {
  await expect(page.locator(".chat-body")).toHaveAttribute("aria-busy", "false", { timeout });
  await expect(page.locator("#chat-message-input")).toBeEnabled({ timeout: 120_000 });
}

export async function waitForAssistantReply(
  page: Page,
  pattern: RegExp,
  timeout = 300_000,
): Promise<void> {
  await expect(page.locator(".message-bubble-assistant").last()).toContainText(pattern, {
    timeout,
  });
  await waitForChatReady(page, timeout);
}

/** zustand persist key for auth */
export const AUTH_STORAGE_KEY = "diao-travelagent-auth";

export async function injectInvalidToken(page: Page): Promise<void> {
  await page.evaluate((key) => {
    const raw = localStorage.getItem(key);
    if (!raw) return;
    const parsed = JSON.parse(raw) as { state?: { token?: string } };
    if (parsed.state) {
      parsed.state.token = "invalid.jwt.token";
      localStorage.setItem(key, JSON.stringify(parsed));
    }
  }, AUTH_STORAGE_KEY);
}

export async function getConversationCount(page: Page): Promise<number> {
  return page.locator(".conversation-item").count();
}

export async function backendReachable(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE.replace(/\/api\/v1\/?$/, "")}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

/** 注册 + 新建行程 + 等待 bootstrap 问候 */
export async function setupAuthenticatedTrip(page: Page): Promise<void> {
  await registerAndLogin(page);
  await createNewTrip(page);
  await waitForAssistantReply(page, /(嗨|你好|想去|目的地|哪里|旅行顾问)/);
}

/** 若目的地被自动填为出发地，则纠正为指定出发城市 */
export async function ensureDepartureCity(page: Page, city: string): Promise<void> {
  const last =
    (await page.locator(".message-bubble-assistant").last().textContent()) ?? "";
  if (/从哪个城市出发|哪个城市出发/.test(last)) {
    await sendChatMessage(page, city);
  } else if (!new RegExp(`出发城市：${city}`).test(last)) {
    await sendChatMessage(page, `出发地改成${city}`);
  }
  await waitForAssistantReply(
    page,
    /(您大概想什么时候|几号|端午|本周末|小长假|从.+出发，交通|天数|几天)/,
  );
}

/** 主路径需求收集 7 步（北京/上海/2026-06-19/3天/1人/穷游党/对的） */
export async function completeRequirementCollection(page: Page): Promise<void> {
  await sendChatMessage(page, "北京");
  await waitForAssistantReply(
    page,
    /(从哪个城市出发|哪个城市出发|您大概想什么时候|几号|端午|本周末|小长假|从.+出发，交通)/,
    300_000,
  );
  await ensureDepartureCity(page, "上海");
  await sendChatMessage(page, "2026-06-19");
  await waitForAssistantReply(page, /(几天|天数|玩几天|多少天)/);
  await sendChatMessage(page, "3天");
  await waitForAssistantReply(page, /(几个人|人数|成人|同行|独自)/);
  await sendChatMessage(page, "就我一个人");
  await waitForAssistantReply(page, /(预算|穷游|一般|花费|多少钱)/);
  await sendChatMessage(page, "穷游党");
  await waitForAssistantReply(page, /(整理|对吗|确认|需求|理解)/, 300_000);
  await sendChatMessage(page, "对的");
  await waitForAssistantReply(page, /(目的地|交通|已确认|规划|北京)/, 300_000);
}

/** 等待审批横幅出现且流式输出结束（避免匹配活动节点的「开始生成完整行程」过早返回） */
export async function waitForApprovalReady(page: Page, timeout = 600_000): Promise<void> {
  await expect(page.getByRole("region", { name: "行程确认" })).toBeVisible({ timeout });
  await waitForChatReady(page, timeout);
  await expect(page.getByRole("button", { name: "确认行程" })).toBeEnabled({ timeout: 60_000 });
}

/** build_itinerary 完成信号（不含 plan_activities 的「开始生成完整行程」） */
const BUILD_COMPLETE = /(Day\s*\d|第\s*\d+\s*天|已生成\s*\d+\s*天|行程与预算已生成|交通.*住宿|估算模式)/;

/** 规划阶段：交通 → 食宿 → 活动 → 等待行程卡片（每步确认后需主动发下一条） */
export async function completePlanningToApproval(page: Page): Promise<void> {
  await sendChatMessage(page, "高铁");
  await waitForAssistantReply(page, /(交通方式已确认|高铁)/, 300_000);

  await sendChatMessage(page, "经济酒店，本地小吃");
  await waitForAssistantReply(page, /(住宿|餐饮|活动偏好|接下来)/, 300_000);

  await sendChatMessage(page, "文化体验");
  try {
    await waitForAssistantReply(page, BUILD_COMPLETE, 300_000);
  } catch {
    // 偶发 stream 无响应：重发活动偏好后再等 build
    await sendChatMessage(page, "文化体验");
    await waitForAssistantReply(page, BUILD_COMPLETE, 600_000);
  }
  await waitForApprovalReady(page, 120_000);
}
