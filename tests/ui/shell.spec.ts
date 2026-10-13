import { test, expect } from "@playwright/test";
import { projection } from "../../scripts/config.mjs";
import path from "node:path";

const client = projection(
  "desktop",
  process.env["APP_CONFIG_FILE"],
  process.env["APP_PROFILE"],
);
for (const colorScheme of ["light", "dark"] as const) {
  for (const [kind, origin, sizes] of [
    [
      "desktop",
      client.desktop_origin,
      [
        [1280, 800],
        [1024, 768],
      ],
    ],
    [
      "public",
      client.web_origin,
      [
        [390, 844],
        [360, 800],
      ],
    ],
  ] as const) {
    for (const [width, height] of sizes) {
      test(`${kind} ${String(width)}x${String(height)} ${colorScheme}: actual shell and connection`, async ({
        page,
      }, testInfo) => {
        await page.setViewportSize({ width, height });
        await page.emulateMedia({ colorScheme });
        const errors: string[] = [];
        page.on("pageerror", (error) => {
          errors.push(error.message);
        });
        const response = await page.goto(origin);
        if (kind === "public") {
          const headers = response?.headers();
          const csp = headers?.["content-security-policy"];
          expect(csp).toContain("script-src 'self' 'nonce-");
          expect(csp).toContain("frame-ancestors 'none'");
          expect(headers?.["cache-control"]).toContain("no-store");
          if (testInfo.project.name === "development")
            expect(csp).toContain("'unsafe-eval'");
          else expect(csp).not.toContain("'unsafe-eval'");
        }
        await expect(page.getByText("Bản khung giao diện")).toBeVisible();
        await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
        const button = page.getByRole("button", { name: "Kiểm tra kết nối" });
        await expect(button).toBeVisible();
        await button.focus();
        await expect(button).toBeFocused();
        await page.keyboard.press("Enter");
        await expect(page.getByRole("status")).toContainText(
          "Dịch vụ có phản hồi",
        );
        await expect(page.getByRole("status")).toContainText("chưa khả dụng");
        await expect(button).toBeEnabled();
        // Capture the settled enabled control, after Fluent's state transitions.
        await button.evaluate(async (node) => {
          await Promise.allSettled(
            node.getAnimations().map((animation) => animation.finished),
          );
        });
        const contrast = await page.evaluate(() => {
          // WCAG relative luminance and alpha compositing, not a product threshold.
          const rgba = (value: string) => {
            const parts = value.match(/[\d.]+/g)?.map(Number);
            if (!parts || parts.length < 3)
              throw new Error("COMPUTED_RGB_REQUIRED");
            return [parts[0] ?? 0, parts[1] ?? 0, parts[2] ?? 0, parts[3] ?? 1];
          };
          const composite = (front: number[], back: number[]) =>
            [0, 1, 2].map(
              (i) =>
                (front[i] ?? 0) * (front[3] ?? 1) +
                (back[i] ?? 0) * (1 - (front[3] ?? 1)),
            );
          const luminance = (color: number[]) =>
            color.reduce((sum, channel, i) => {
              const c = channel / 255;
              return (
                sum +
                (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4) *
                  ([0.2126, 0.7152, 0.0722][i] ?? 0)
              );
            }, 0);
          return [...document.querySelectorAll("button")].map((node) => {
            const chain: Element[] = [];
            for (
              let ancestor: Element | null = node;
              ancestor;
              ancestor = ancestor.parentElement
            )
              chain.push(ancestor);
            let background = [255, 255, 255];
            for (const ancestor of chain.reverse())
              background = composite(
                rgba(getComputedStyle(ancestor).backgroundColor),
                background,
              );
            const foreground = composite(
              rgba(getComputedStyle(node).color),
              background,
            );
            const f = luminance(foreground),
              b = luminance(background);
            return {
              label: node.textContent,
              ratio: (Math.max(f, b) + 0.05) / (Math.min(f, b) + 0.05),
            };
          });
        });
        for (const control of contrast)
          expect(control.ratio, control.label).toBeGreaterThanOrEqual(4.5);
        await testInfo.attach("computed-enabled-button-contrast", {
          body: JSON.stringify(contrast),
          contentType: "application/json",
        });
        const geometry = await page.evaluate(() => ({
          scroll: document.documentElement.scrollWidth,
          width: window.innerWidth,
          scale: window.devicePixelRatio,
          theme: document
            .querySelector(".cv-theme")
            ?.getAttribute("data-theme"),
        }));
        expect(geometry.scroll).toBeLessThanOrEqual(geometry.width);
        expect(geometry.scale).toBe(1);
        expect(geometry.theme).toBe(colorScheme);
        expect(errors).toEqual([]);
        await page.screenshot({
          path: path.join(
            ".local/screenshots",
            `${kind}-${String(width)}x${String(height)}-${colorScheme}.png`,
          ),
          fullPage: true,
        });
      });
    }
  }
}

test("desktop discard an old reply after changing selection", async ({
  page,
}) => {
  // Deliberately detach abort in this isolated fixture to exercise the stale-owner
  // guard even when a transport delivers a late successful reply.
  await page.addInitScript((origin) => {
    const original = window.fetch.bind(window);
    window.fetch = async (...args: Parameters<typeof fetch>) => {
      const url = args[0] instanceof Request ? args[0].url : String(args[0]);
      if (url === `${origin}/live`) {
        const response = await original(args[0], {
          ...args[1],
          signal: new AbortController().signal,
        });
        document.documentElement.dataset["oldReplySettled"] = "true";
        return response;
      }
      return original(...args);
    };
  }, client.api_origin);
  await page.goto(client.desktop_origin);
  let release: (() => void) | undefined;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let intercepted: (() => void) | undefined;
  const started = new Promise<void>((resolve) => {
    intercepted = resolve;
  });
  await page.route(`${client.api_origin}/live`, async (route) => {
    intercepted?.();
    await gate;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ component: "api", alive: true }),
    });
  });
  await page.getByRole("button", { name: "Kiểm tra kết nối" }).click();
  await started;
  await page.getByRole("button", { name: "Kết nối", exact: true }).click();
  release?.();
  await expect(page.locator("html")).toHaveAttribute(
    "data-old-reply-settled",
    "true",
  );
  await expect(page.getByRole("status")).toContainText("Chưa kiểm tra kết nối");
  await expect(page.getByRole("status")).not.toContainText(
    "Dịch vụ có phản hồi",
  );
});

test("public connection loss is actionable and exposes no data", async ({
  page,
}) => {
  await page.goto(client.web_origin);
  await page.route("**/api/status", (route) => route.abort());
  await page.getByRole("button", { name: "Kiểm tra kết nối" }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Không kết nối được dịch vụ" }),
  ).toContainText("Không kết nối được dịch vụ");
});
