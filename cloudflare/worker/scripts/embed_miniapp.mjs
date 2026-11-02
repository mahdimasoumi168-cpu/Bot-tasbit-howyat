import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const html = await readFile(resolve(root, "public/index.html"), "utf8");
const js = await readFile(resolve(root, "public/app.js"), "utf8");
const target = resolve(root, "src/generated/miniapp.ts");
await mkdir(dirname(target), { recursive: true });
await writeFile(target, "export const MINIAPP_HTML = " + JSON.stringify(html) + ";\nexport const MINIAPP_JS = " + JSON.stringify(js) + ";\n", "utf8");
