import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL(".", import.meta.url));
const publicDir = join(root, "public");
const port = Number(process.env.PORT || 3000);

function cleanLua(source) {
  if (typeof source !== "string" || source.length > 2_000_000) {
    throw new Error("Source harus berupa teks Lua maksimal 2 MB.");
  }

  const tokens = [];
  let i = 0;
  while (i < source.length) {
    const c = source[i];
    if (/\s/.test(c)) {
      i++;
      continue;
    }
    if (source.startsWith("--", i)) {
      const longStart = source.indexOf("[[", i + 2);
      const lineEnd = source.indexOf("\n", i + 2);
      if (longStart !== -1 && (lineEnd === -1 || longStart < lineEnd)) {
        const end = source.indexOf("]]", longStart + 2);
        i = end === -1 ? source.length : end + 2;
      } else {
        i = lineEnd === -1 ? source.length : lineEnd + 1;
      }
      continue;
    }
    if (c === "'" || c === '"' || source.startsWith("[[", i)) {
      const quote = c === "[" ? "]]" : c;
      let j = c === "[" ? i + 2 : i + 1;
      while (j < source.length) {
        if (source[j] === "\\" && c !== "[") {
          j += 2;
          continue;
        }
        if (c === "[" ? source.startsWith(quote, j) : source[j] === quote) {
          j += quote.length;
          break;
        }
        j++;
      }
      tokens.push(decodeLuaString(source.slice(i, j)));
      i = j;
      continue;
    }
    const match = source.slice(i).match(/^(?:[A-Za-z_][\w]*|\d+(?:\.\d+)?|==|~=|<=|>=|::|\.\.\.?|.)/s);
    tokens.push(match[0]);
    i += match[0].length;
  }

  function decodeLuaString(token) {
    return token.replace(/\\(\d{1,3})/g, (full, digits) => {
      const value = Number(digits);
      return value >= 32 && value <= 126 ? String.fromCharCode(value) : full;
    });
  }

  const lines = [];
  let line = "";
  let indent = 0;
  const blockEnd = new Set(["end", "until"]);
  const blockStart = new Set(["function", "if", "for", "while", "repeat", "do"]);
  const punctuation = new Set([",", ";", ")", "]", "}"]);
  const openPunctuation = new Set(["(", "[", "{"]);
  const operators = new Set(["=", "+", "-", "*", "/", "%", "^", "==", "~=", "<", ">", "<=", ">=", "..", "...", "and", "or"]);

  const flush = () => {
    if (line.trim()) lines.push(`${"  ".repeat(Math.max(0, indent))}${line.trim()}`);
    line = "";
  };
  let previous = "";
  for (const token of tokens) {
    if (blockEnd.has(token)) {
      flush();
      indent--;
    }
    if (token === ";") {
      flush();
      continue;
    }
    if (token === ",") {
      line = line.trimEnd() + ", ";
      continue;
    }
    if (punctuation.has(token)) {
      line = line.trimEnd() + token;
      continue;
    }
    if (openPunctuation.has(token)) {
      line = line.trimEnd() + token;
      previous = token;
      continue;
    }
    if (operators.has(token)) {
      line = `${line.trimEnd()} ${token} `;
      previous = token;
      continue;
    }
    const needsSpace = line && !line.endsWith("(") && !line.endsWith("[") &&
      !line.endsWith("{") && !line.endsWith(".") && !line.endsWith(":") &&
      !operators.has(previous);
    line += needsSpace ? " " : "";
    line += token;
    if (blockStart.has(token)) indent++;
    if (token === "then" || token === "else" || token === "do") {
      flush();
    }
    if (token === "end" || token === "until") flush();
    previous = token;
  }
  flush();
  return lines.join("\n").replace(/[ \t]+\n/g, "\n").trim() + "\n";
}

function json(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  res.end(data);
}

const server = createServer(async (req, res) => {
  try {
    if (req.method === "POST" && req.url === "/api/clean") {
      let body = "";
      for await (const chunk of req) body += chunk;
      const payload = JSON.parse(body);
      return json(res, 200, { code: cleanLua(payload.code) });
    }
    if (req.method === "GET" && (req.url === "/" || req.url === "/index.html")) {
      const html = await readFile(join(publicDir, "index.html"));
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      return res.end(html);
    }
    const requested = normalize(join(publicDir, req.url || "/"));
    if (requested.startsWith(publicDir) && extname(requested) === ".css") {
      const css = await readFile(requested);
      res.writeHead(200, { "Content-Type": "text/css; charset=utf-8" });
      return res.end(css);
    }
    res.writeHead(404);
    res.end("Not found");
  } catch (error) {
    json(res, 400, { error: error instanceof Error ? error.message : "Request tidak valid." });
  }
});

server.listen(port, "0.0.0.0", () => console.log(`Lua cleaner listening on ${port}`));
