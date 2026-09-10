/**
 * Page-specific background artwork for the Command Operations shell.
 *
 * Each entry maps a route pathname (as it appears in src/routes/index.tsx)
 * to a static background image under /public/images/background/. Any route
 * not listed here — and any future route added to the app — falls back to
 * DEFAULT_PAGE_BACKGROUND ("common theme"), so new pages never render with
 * no background and never need an entry added here to stay covered.
 *
 * Consumed by AppLayout (see getPageBackground below), which paints the
 * image behind <main> only — the Sidebar and Header keep their own opaque
 * backgrounds, so this never affects navigation chrome.
 */
const BASE = '/images/background';

export const DEFAULT_PAGE_BACKGROUND = `${BASE}/common-theme.png`;

export const PAGE_BACKGROUNDS: Record<string, string> = {
  '/': `${BASE}/overview-page.png`,
  '/analytics': `${BASE}/analytics-page.png`,
  '/incidents': `${BASE}/incident-board.png`,
  '/evidence': `${BASE}/evidence-vault.png`,
};

export function getPageBackground(pathname: string): string {
  return PAGE_BACKGROUNDS[pathname] ?? DEFAULT_PAGE_BACKGROUND;
}
