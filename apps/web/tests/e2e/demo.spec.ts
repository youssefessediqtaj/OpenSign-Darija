import { expect, test } from '@playwright/test';

test('opens the simulated demo', async ({ page }) => {
  await page.goto('/demo');
  await expect(page.getByRole('heading', { name: /Demonstration simulee/i })).toBeVisible();
  await page.getByRole('button', { name: /Autoriser la camera/i }).click();
  await expect(page.getByText(/Zone camera simulee prete/i)).toBeVisible();
});
