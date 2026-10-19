import { readFile } from "node:fs/promises";
import { parseAllDocuments } from "yaml";

const [path, version, expected] = process.argv.slice(2);
const documents = parseAllDocuments(await readFile(path, "utf8"));
if (documents.some((document) => document.errors.length)) throw new Error("Invalid consumer lockfile");
const key = `@releaseway/npm-actions-fixture@${version}`;
const entries = documents.map((document) => document.toJS()?.packages?.[key]).filter(Boolean);
if (entries.length !== 1 || entries[0].resolution?.integrity !== expected) {
  throw new Error("Installed integrity differs from the candidate plan");
}
