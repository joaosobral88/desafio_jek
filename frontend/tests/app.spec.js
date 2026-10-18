import { test, expect } from "@playwright/test";

test("criar, abrir, votar, impedir voto repetido e publicar resultados", async ({
  page,
}) => {
  await page.goto("/#anfitriao");
  await page
    .getByLabel("Pergunta", { exact: true })
    .fill("Que linguagem preferes?");
  await page.getByLabel("Opção 1", { exact: true }).fill("Python");
  await page.getByLabel("Opção 2", { exact: true }).fill("C");
  await page.getByRole("button", { name: "+ Adicionar opção" }).click();
  await page.getByLabel("Opção 3", { exact: true }).fill("Java");
  await page.getByRole("button", { name: "Guardar rascunho" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Votação criada em rascunho",
  );
  let card = page
    .locator("article")
    .filter({ hasText: "Que linguagem preferes?" });
  await expect(card.getByText("Rascunho", { exact: true })).toBeVisible();
  await card.getByRole("button", { name: "Abrir votação" }).click();
  await expect(card.getByText("Aberta", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Público", exact: true }).click();
  card = page.locator("article").filter({ hasText: "Que linguagem preferes?" });
  await expect(
    card.getByRole("heading", { name: "Resultados", exact: true }),
  ).toHaveCount(0);
  await card.getByLabel("Python", { exact: true }).check();
  await card.getByRole("button", { name: "Registar voto" }).click();
  await expect(card.getByRole("status")).toContainText(
    "O seu voto foi registado",
  );
  const token = await page.evaluate(() =>
    localStorage.getItem("live-pulse-token"),
  );
  expect(token).toMatch(/^[0-9a-f-]{36}$/);

  await page.reload();
  await card.getByLabel("C", { exact: true }).check();
  await card.getByRole("button", { name: "Registar voto" }).click();
  await expect(card.getByRole("alert")).toContainText("Já votou");
  expect(
    await page.evaluate(() => localStorage.getItem("live-pulse-token")),
  ).toBe(token);

  await page.getByRole("link", { name: "Anfitrião", exact: true }).click();
  await card.getByRole("button", { name: "Atualizar resultados" }).click();
  await expect(
    card.getByText("1 voto registado", { exact: true }),
  ).toBeVisible();
  await expect(
    card.getByRole("img", { name: "Python: 1 votos, 100%" }),
  ).toBeVisible();
  await card.getByRole("button", { name: "Fechar votação" }).click();
  await expect(card.getByText("Fechada", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Público", exact: true }).click();
  await expect(
    card.getByRole("heading", { name: "Resultados", exact: true }),
  ).toBeVisible();
  await expect(card.getByRole("radio")).toHaveCount(0);
  await expect(
    card.getByText("1 voto registado", { exact: true }),
  ).toBeVisible();
});

test("formulário valida opções e adapta-se a um ecrã pequeno", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/#anfitriao");
  await page
    .getByLabel("Pergunta", { exact: true })
    .fill("Uma pergunta de teste");
  await page.getByLabel("Opção 1", { exact: true }).fill("Sim");
  await page.getByLabel("Opção 2", { exact: true }).fill(" sim ");
  await page.getByRole("button", { name: "Guardar rascunho" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "As opções não podem estar repetidas",
  );
  for (let i = 0; i < 3; i++)
    await page.getByRole("button", { name: "+ Adicionar opção" }).click();
  await expect(
    page.getByRole("button", { name: "+ Adicionar opção" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Remover opção 5", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "+ Adicionar opção" }),
  ).toBeEnabled();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
