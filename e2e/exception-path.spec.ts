import { expect, test } from "@playwright/test";

import {
  backendReachable,
  ensureDepartureCity,
  sendChatMessage,
  setupAuthenticatedTrip,
  waitForAssistantReply,
} from "./helpers";

test.describe("异常路径 — E1 错别字澄清", () => {
  test.describe.configure({ timeout: 300_000 });

  test.beforeEach(async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动 (需 :8200)");
    await setupAuthenticatedTrip(page);
  });

  test("程度→成都澄清链（E1 / FLOW-040）", async ({ page }) => {
    await sendChatMessage(page, "程度");
    await waitForAssistantReply(page, /(成都|是不是|确认|澄清)/);

    await sendChatMessage(page, "对");
    await waitForAssistantReply(
      page,
      /(从哪个城市出发|哪个城市出发|您大概想什么时候|几号|端午|从.+出发，交通)/,
    );
    await ensureDepartureCity(page, "上海");
  });

  test("天堂模糊澄清不自动绑定（FLOW-041）", async ({ page }) => {
    await sendChatMessage(page, "天堂");
    await waitForAssistantReply(page, /(天津|天水|哪个|澄清|确认|是不是)/);
    const bubbles = page.locator(".message-bubble-assistant");
    const last = await bubbles.last().textContent();
    expect(last).not.toMatch(/^天津$/);
  });
});

test.describe("异常路径 — 多轮跨槽（FLOW-042）", () => {
  test.describe.configure({ timeout: 300_000 });

  test("成都→上海→日期", async ({ page }) => {
    test.skip(!(await backendReachable()), "backend 未启动 (需 :8200)");
    await setupAuthenticatedTrip(page);

    await sendChatMessage(page, "成都");
    await waitForAssistantReply(
      page,
      /(从哪个城市出发|哪个城市出发|您大概想什么时候|几号|端午|从.+出发，交通)/,
    );
    await ensureDepartureCity(page, "上海");

    await sendChatMessage(page, "2026-07-01");
    await waitForAssistantReply(page, /(几天|天数|玩几天|多少天)/);
  });
});
