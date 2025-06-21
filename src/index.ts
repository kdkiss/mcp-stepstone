import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js"; // fallback
import { StreamableHttpServerTransport } from "@modelcontextprotocol/sdk/server/http.js"; // correct import
import { z } from "zod";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

export const configSchema = z.object({
  debug: z.boolean().default(false).describe("Enable debug logging"),
});

export default async function createServer({
  config,
}: {
  config: z.infer<typeof configSchema>;
}) {
  const server = new McpServer({
    name: "mcp-stepstone",
    version: "1.1.0",
  });

  server.tool(
    "fetch_jobs",
    "Fetch Stepstone job listings",
    z.object({
      search_terms: z.array(z.string()).default(["fraud", "crime", "betrug"]),
      zip_code: z.string().default("40210"),
      radius: z.number().default(5),
    }),
    async ({ search_terms, zip_code, radius }) => {
      const input = JSON.stringify({ search_terms, zip_code, radius });
      const scriptPath = join(__dirname, "job_fetcher.py");

      return await new Promise((resolve, reject) => {
        const py = spawn("python3", [scriptPath]);
        let out = "", err = "";

        py.stdin.write(input);
        py.stdin.end();

        py.stdout.on("data", d => out += d.toString());
        py.stderr.on("data", d => err += d.toString());

        py.on("close", code => {
          if (code !== 0) return reject(new Error(`Error: ${err}`));
          try {
            resolve(JSON.parse(out));
          } catch (e: any) {
            reject(new Error(`Invalid JSON output: ${out}`));
          }
        });
      });
    }
  );

  // Choose the HTTP transport
  const transport = new StreamableHttpServerTransport({ port: 8080 });
  await server.connect(transport);
}
