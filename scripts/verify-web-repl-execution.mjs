#!/usr/bin/env node
// Першопричина: жоден тест не доводив, що відвантажений портативний REPL
// справді ВИКОНУЄ Сенс. Усі перевірки міряли наявність файлу, тотожність
// байтів або підрядок у тексті. Цей вартовий вантажить сторінку в справжній
// headless-браузер і вимагає КОНКРЕТНЕ значення від КОНКРЕТНОЇ програми.
//
// Три перевірки (усі обов'язкові):
//   1) Готовність: #input стає enabled за обмежений час (інакше — червоний).
//      Саме це вбиває тихе «Loading…», яке лишалось назавжди без дедлайну.
//   2) Виконання: ввести (додати 1 2) -> рядок .line-value зі значенням "3".
//   3) Відмова не тиха: обірвати запит .wasm -> видимий .line-error, а #input
//      ЛИШАЄТЬСЯ disabled (жодного удаваного «живого» REPL).
//
// Використання: node scripts/verify-web-repl-execution.mjs [шлях-до-html]
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import process from "node:process";

const HTML = resolve(process.argv[2] ?? "public/my-lisp-cli-web.html");
const DIR = resolve(HTML, "..");
const READY_DEADLINE_MS = 20000;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".wasm": "application/wasm",
};

function fail(msg) {
  console.error(`WEB_REPL_EXECUTION_FAILED: ${msg}`);
  process.exitCode = 1;
}

function serve() {
  const server = createServer(async (req, res) => {
    const rel = decodeURIComponent((req.url ?? "/").split("?")[0]);
    const file = join(DIR, rel === "/" ? HTML.slice(DIR.length + 1) : rel);
    try {
      const body = await readFile(file);
      res.writeHead(200, { "content-type": MIME[extname(file)] ?? "application/octet-stream" });
      res.end(body);
    } catch {
      res.writeHead(404).end("not found");
    }
  });
  return new Promise((ok) => server.listen(0, "127.0.0.1", () => ok(server)));
}

async function main() {
  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch (e) {
    // Вартовий не має права «проходити» без браузера: це була б тиха порожнеча.
    fail(`playwright недоступний — вартовий не може підтвердити виконання (${e})`);
    return;
  }
  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}/`;
  const browser = await chromium.launch();
  try {
    // 1+2. Готовність і виконання.
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    await page.goto(base, { waitUntil: "load" });
    try {
      await page.waitForSelector("#input:not([disabled])", { timeout: READY_DEADLINE_MS });
    } catch {
      fail(`REPL не став готовий за ${READY_DEADLINE_MS}мс (тихе «Loading…»). Помилки сторінки: ${errors.join(" | ") || "немає"}`);
      return;
    }
    await page.fill("#input", "(додати 1 2)");
    await page.press("#input", "Enter");
    try {
      await page.waitForFunction(
        () => [...document.querySelectorAll(".line-value")].some((n) => n.textContent.trim() === "3"),
        { timeout: READY_DEADLINE_MS },
      );
    } catch {
      const seen = await page.$$eval("#log *", (ns) => ns.map((n) => n.textContent).join(" | "));
      fail(`REPL не виконав (додати 1 2) -> 3. Лог: ${seen}`);
      return;
    }
    await page.close();

    // 3. Відмова не тиха: обірвати .wasm.
    const page2 = await browser.newPage();
    await page2.route("**/*.wasm", (route) => route.abort());
    await page2.goto(base, { waitUntil: "load" });
    try {
      await page2.waitForFunction(
        () => [...document.querySelectorAll(".line-error")].some((n) => n.textContent.includes("could not load")),
        { timeout: READY_DEADLINE_MS },
      );
    } catch {
      fail("обірваний .wasm не дав видимої помилки — відмова ТИХА");
      return;
    }
    const stillDisabled = await page2.$eval("#input", (n) => n.disabled);
    if (!stillDisabled) {
      fail("#input став enabled попри провал ініціалізації — удаваний живий REPL");
      return;
    }
    await page2.close();
    console.log("WEB_REPL_EXECUTION_PASS: готовність + виконання + видима відмова");
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch((e) => fail(`непередбачений збій вартового: ${e}`));
