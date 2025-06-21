import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { serveHttp } from "@modelcontextprotocol/sdk/server/http.js";
import { z } from "zod";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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
    version: "1.0.0",
  });

  server.tool(
    "fetch_jobs",
    "Fetch Stepstone job listings based on search terms, zip code, and radius",
    z.object({
      search_terms: z.array(z.string()).default(["fraud", "crime"]),
      zip_code: z.string().default("40210"),
      radius: z.number().default(5),
    }),
    async ({ search_terms, zip_code, radius }) => {
      const input = JSON.stringify({ search_terms, zip_code, radius });
      const scriptPath = join(__dirname, "job_fetcher.py");

      return new Promise((resolve, reject) => {
        const py = spawn("python3", [scriptPath]);

        let output = "";
        let error = "";

        py.stdin.write(input);
        py.stdin.end();

        py.stdout.on("data", (data) => {
          output += data.toString();
        });

        py.stderr.on("data", (data) => {
          error += data.toString();
        });

        py.on("close", (code) => {
          if (code !== 0) {
            reject(new Error(`Python script failed: ${error}`));
          } else {
            try {
              const result = JSON.parse(output);
              resolve(result);
            } catch (err: any) {
              reject(new Error("Failed to parse output: " + output + "\nError: " + err.message));
            }
          }
        });
      });
    }
  );

  await serveHttp(server.server, { port: 8080 });
}
