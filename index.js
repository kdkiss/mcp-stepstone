#!/usr/bin/env node

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const pythonScript = path.resolve(__dirname, "job_fetcher.py");

if (!fs.existsSync(pythonScript)) {
  console.error(`❌ job_fetcher.py not found at ${pythonScript}`);
  process.exit(1);
}

let input = "";

process.stdin.on("data", chunk => {
  input += chunk;
});

process.stdin.on("end", () => {
  const py = spawn("python3", [pythonScript]);

  py.stdin.write(input);
  py.stdin.end();

  py.stdout.on("data", data => process.stdout.write(data));
  py.stderr.on("data", data => process.stderr.write(data));

  py.on("close", code => process.exit(code));
});
