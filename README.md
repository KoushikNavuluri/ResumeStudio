# Perplexity Cookie Toolkit + LaTeX Prompt Template

A concise, copy‑pasteable toolkit for:

- Replacing and using your Perplexity browser cookies safely in scripts
- A clean, “default” LaTeX prompt template for consistently formatted math
- Ready‑to‑use examples with curl, Python, and Node.js

This repo is documentation‑first. It doesn’t ship an integration to Perplexity; it shows you how to pass your cookie and prompts with common tools, so you can adapt the approach in your own project.


## Features

- Step‑by‑step guide to extract your Perplexity cookie from the browser
- Secure handling patterns (environment variables, .env)
- Drop‑in examples for curl, Python (requests), and Node.js (fetch)
- "Original default" LaTeX prompt template (short + full versions)
- requirements.txt for Python users and a preconfigured .gitignore to keep secrets out of git


## Requirements

- A Perplexity account and desktop browser (Chrome/Edge/Brave/Firefox)
- Optional tooling depending on what you want to use:
  - Python 3.9+ (examples use requests and python‑dotenv)
  - Node.js 18+ (has native fetch; for Node < 18, use node‑fetch)
  - curl (for simple shell examples)

If you plan to run the Python examples, install the dependencies provided:

```bash
pip install -r requirements.txt
```


## Quick start

1) Clone or download this repository.

2) Put your Perplexity cookie into an environment variable (see “Get your cookie” below):

- macOS/Linux:

```bash
export PPLX_COOKIE='cookie1=VALUE1; cookie2=VALUE2; ...'
```

- Windows PowerShell:

```powershell
$Env:PPLX_COOKIE = "cookie1=VALUE1; cookie2=VALUE2; ..."
```

Optional: create a local .env file (not committed) to load automatically in Python via python‑dotenv:

```
# .env (do not commit)
PPLX_COOKIE='cookie1=VALUE1; cookie2=VALUE2; ...'
```

3) Try a request:

- curl:

```bash
curl "https://www.perplexity.ai/" \
  -H "Cookie: $PPLX_COOKIE" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Accept: */*"
```

- Python (requests):

```python
import os
from dotenv import load_dotenv
import requests

load_dotenv()  # loads .env if present
cookie = os.environ.get("PPLX_COOKIE", "")
headers = {
    "Cookie": cookie,
    "User-Agent": "Mozilla/5.0",
}

resp = requests.get("https://www.perplexity.ai/", headers=headers, timeout=30)
print(resp.status_code)
print(resp.text[:500])
```

- Node.js (fetch):

```js
// Node >= 18 has global fetch
const cookie = process.env.PPLX_COOKIE || "";
const res = await fetch("https://www.perplexity.ai/", {
  headers: {
    Cookie: cookie,
    "User-Agent": "Mozilla/5.0",
  },
});
console.log(res.status);
console.log((await res.text()).slice(0, 500));
```


## How to get your Perplexity cookie

Important: Your cookies are secrets. Do not share them, do not commit them to git, and store them like a password. Respect Perplexity’s Terms of Service. Cookies expire; re‑copy them when you get 401/403 errors.

Steps (Chrome/Edge/Brave):

1. Log in to https://www.perplexity.ai/.
2. Open DevTools → Network.
3. Trigger a request (e.g., ask a question).
4. Click any request to `perplexity.ai` in the Network list.
5. In Headers → Request Headers, copy the entire value of the `cookie` header.
6. Save it to `PPLX_COOKIE` (see Quick start above).

Alternative (DevTools → Application → Storage → Cookies → https://www.perplexity.ai):
- Select relevant cookies and reconstruct `name=value; name2=value2; ...` in the same order.

Replace/rotate your cookie:
- When a request starts failing with 401/403, or after you log out/in, repeat the steps and update `PPLX_COOKIE`.


## Default LaTeX prompt template

Short version (paste into a user prompt):

```
You are a math and LaTeX expert. For math:
- Use $...$ for inline math and $$...$$ for display equations.
- Do not place LaTeX inside Markdown code blocks.
- Keep LaTeX valid and minimal: standard amsmath/amsfonts commands only.
- When giving a final result, also output a minimal standalone LaTeX document between the markers BEGIN_LATEX and END_LATEX that renders only the final answer.
```

Full version (useful as a system prompt):

```
You are a rigorous math & LaTeX assistant.

Formatting rules:
- Use $...$ for inline math and $$...$$ for display equations; do not mix with backticks.
- Use standard LaTeX (amsmath, amssymb). Avoid unusual packages unless asked.
- Prefer clear, stepwise reasoning with math typeset where appropriate.
- Do not escape backslashes or dollar signs.
- When presenting code or pseudocode, use Markdown code blocks; when presenting math, never use code blocks.

Final answer requirements:
1) Provide a concise boxed final result in display math where appropriate.
2) Then output a minimal, standalone LaTeX document (final answer only) between markers:

BEGIN_LATEX
\documentclass{article}
\usepackage{amsmath, amssymb}
\usepackage[margin=1in]{geometry}
\begin{document}
% Final result only below (no explanation):
% e.g. \[
%   E = mc^2
% \]
\[
  % Your final expression here
\]
\end{document}
END_LATEX
```

Tips:
- If your app renders Markdown with MathJax or KaTeX, use `$` / `$$` as shown.
- If you need only raw TeX for the final answer, ask for the content strictly between `BEGIN_LATEX` and `END_LATEX`.


## Project structure

- README.md — this guide
- requirements.txt — optional Python dependencies for the examples
- .gitignore — keeps secrets and common noise files out of git
- LICENSE — MIT


## Troubleshooting

- 401/403 after it used to work → Your cookie expired. Re‑copy it while logged in.
- 429 / rate limited → Slow down; automated scraping may be blocked.
- HTML instead of JSON → You may be hitting a page endpoint. Mirror the exact URL, method, and headers your browser uses (inspect Network tab).


## Security and terms

- Treat cookies as secrets; never share or commit them.
- Use responsibly and comply with Perplexity’s Terms of Service.
- Prefer an official API if/when one fits your use case.


## License

MIT — see LICENSE.
