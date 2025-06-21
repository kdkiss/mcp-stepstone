#!/usr/bin/env node
import { spawn } from "child_process";
const py = spawn("python3", ["mcp_server.py"], { stdio: "inherit" });