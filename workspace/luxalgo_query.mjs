import { Client } from "../external/luxalgo-mcp-server/node_modules/@modelcontextprotocol/client/dist/index.mjs";
import { StdioClientTransport } from "../external/luxalgo-mcp-server/node_modules/@modelcontextprotocol/client/dist/stdio.mjs";
import { join } from "node:path";

const server = join(import.meta.dirname, "..", "external", "luxalgo-mcp-server", "dist", "index.js");
const client = new Client({ name: "heimdall-library-research", version: "1.0.0" });
const transport = new StdioClientTransport({ command: process.execPath, args: [server] });
await client.connect(transport);

for (const query of process.argv.slice(2)) {
  if (query.startsWith("@")) {
    const slug = query.slice(1);
    const detail = await client.callTool({
      name: "library_get_indicator",
      arguments: { slug },
    });
    const source = await client.callTool({
      name: "library_get_source_code",
      arguments: { slug },
    });
    console.log(JSON.stringify({
      slug,
      detail: JSON.parse(detail.content?.[0]?.text ?? "{}"),
      source: JSON.parse(source.content?.[0]?.text ?? "{}"),
    }, null, 2));
    continue;
  }
  const result = await client.callTool({
    name: "library_search",
    arguments: { query, type: "indicators", limit: 10 },
  });
  const payload = JSON.parse(result.content?.[0]?.text ?? "{}");
  console.log(JSON.stringify({ query, results: payload.results ?? [] }, null, 2));
}

await client.close();
