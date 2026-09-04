import { expect, test, type Page } from '@playwright/test';

/**
 * Regression coverage for the ChartFrame visually-hidden fallback table.
 *
 * Bug this guards against: the fallback `<table>` used `sr-only` directly
 * (making the table itself the `position: absolute` box, with no positioned
 * containing block). On mobile viewports this could leave extra, empty
 * scrollable space below the real content — the document's scrollable
 * height grew past where the footer visually ends, even though nothing is
 * visibly there. The fix wraps the table in a dedicated sr-only clipping
 * element and makes `.chart-frame` its containing block with
 * `overflow: clip`.
 *
 * This suite must FAIL against the pre-fix markup (table directly sr-only,
 * `.chart-frame` with no `position`/`overflow` containment) and PASS against
 * the fix.
 */

const ROUTES = ['/deep-thinker/overview', '/deep-thinker/uncertainty'];

// Tolerance for rounding/subpixel differences between the footer's visual
// bottom edge and the document's scrollable height. This is intentionally
// small — it must not mask genuine empty trailing scroll space, only
// sub-pixel layout rounding.
const SCROLL_TOLERANCE_PX = 2;

async function fallbackTables(page: Page) {
	return page.locator('table.chart-frame__fallback');
}

for (const route of ROUTES) {
	test.describe(`${route}`, () => {
		test('fallback tables and their content are present and semantically visible', async ({
			page
		}) => {
			await page.goto(route);
			await page.waitForLoadState('networkidle');

			const tables = await fallbackTables(page);
			const count = await tables.count();
			expect(count).toBeGreaterThan(0);

			for (let i = 0; i < count; i += 1) {
				const table = tables.nth(i);

				// Present in the DOM (attached), not removed/display:none via
				// Playwright's actionability-style "attached" check, and not
				// aria-hidden — i.e. reachable by assistive tech.
				await expect(table).toBeAttached();
				expect(await table.getAttribute('aria-hidden')).not.toBe('true');

				const displayValue = await table.evaluate(
					(el) => getComputedStyle(el).display
				);
				expect(displayValue).not.toBe('none');

				const visibilityValue = await table.evaluate(
					(el) => getComputedStyle(el).visibility
				);
				expect(visibilityValue).not.toBe('hidden');

				// The caption and at least one data row must be real,
				// semantically-present content — not just an empty shell.
				const caption = table.locator('caption');
				await expect(caption).toBeAttached();
				const captionText = (await caption.textContent())?.trim() ?? '';
				expect(captionText.length).toBeGreaterThan(0);

				const rowCells = table.locator('tbody tr td');
				await expect(rowCells.first()).toBeAttached();
				const cellCount = await rowCells.count();
				expect(cellCount).toBeGreaterThan(0);
			}
		});

		test('no vertical scroll extends past the visual end of the footer', async ({ page }) => {
			await page.goto(route);
			await page.waitForLoadState('networkidle');

			const footer = page.locator('footer.app-footer');
			await expect(footer).toBeAttached();

			// Scroll all the way down first: some layouts only reveal true
			// scrollable height once scrolled, and this also surfaces any
			// scroll-anchoring artifacts.
			await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
			await page.waitForTimeout(50);

			const footerBottom = await footer.evaluate((el) => {
				const rect = el.getBoundingClientRect();
				return rect.bottom + window.scrollY;
			});
			const scrollHeight = await page.evaluate(() => document.documentElement.scrollHeight);

			// The footer's visual bottom edge (in document coordinates) should
			// coincide with the document's total scrollable height — i.e.
			// scrolling to the bottom shows the footer and nothing else. A
			// scrollHeight meaningfully larger than the footer's bottom edge
			// means there is empty, non-visible scrollable space below the
			// real content (the bug this test guards against). A scrollHeight
			// smaller than the footer bottom would mean clipping legitimate
			// content, which is equally wrong.
			expect(Math.abs(scrollHeight - footerBottom)).toBeLessThanOrEqual(SCROLL_TOLERANCE_PX);
		});
	});
}
