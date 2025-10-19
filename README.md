# Perplexity cookie guide and LaTeX prompt template

This repository provides a clear, copy‑pasteable guide for:

- How to use your own Perplexity browser cookies safely (e.g., in scripts or API-like experiments that rely on your logged‑in session)
- A well‑tested, “default” LaTeX prompt template you can paste into your system/user prompt to get consistently formatted math output

Important: This repository contains documentation only. It does not ship code that talks to Perplexity for you. The examples below show how to pass cookies and prompts with common tooling (curl, Python, Node.js), which you can adapt to your own project.


## 1) Using your Perplexity cookies

Perplexity does not offer a public, stable, unrestricted API that you can use without authentication. Many users experiment by making requests with the same cookies their browser uses when they’re logged in. If you choose to do that, follow the steps and cautions below.

### Security and terms of service

- Your cookies are secrets. Anyone with them can act as you. Never share them, never commit them to Git, and store them like you would a password.
- Respect Perplexity’s Terms of Service. This guide is intended for educational purposes. Your use is your responsibility.
- Cookies expire. When a request suddenly starts failing with 401/403, refresh your cookie value from the browser.

### Get your cookie string (Chrome/Edge/Brave)

1. Log in to https://www.perplexity.ai/ in your browser.
2. Open Developer Tools → Network tab.
3. Perform an action that triggers a request (e.g., ask a question).
4. In the Network list, click any request made to `perplexity.ai`.
5. Go to the "Headers" panel. Under "Request Headers", locate the `cookie` header.
6. Right‑click the `cookie` value and copy it. It will look like a semicolon‑separated list:
   
   `cookie1=VALUE1; cookie2=VALUE2; cookie3=VALUE3; ...`

Alternative (Application tab):

- Developer Tools → Application → Storage → Cookies → https://www.perplexity.ai
- Select all relevant cookies and reconstruct the same `name=value; name2=value2; ...` string in the same order.

### Store the cookie securely

Recommended: put it into an environment variable so your scripts can reference it without hard‑coding.

macOS/Linux (bash/zsh):

```bash
# Temporarily set it for this shell session
export PPLX_COOKIE='cookie1=VALUE1; cookie2=VALUE2; ...'

# Or store it in a local .env file you DO NOT commit to git
# .env
# PPLX_COOKIE='cookie1=VALUE1; cookie2=VALUE2; ...'
```

Windows PowerShell:

```powershell
$Env:PPLX_COOKIE = "cookie1=VALUE1; cookie2=VALUE2; ..."
```

Add `.env` to your .gitignore (see the .gitignore in this repo) and never commit real cookie strings.

### Use the cookie in requests

Below are minimal examples that demonstrate how to forward your browser cookie. Replace the URL and payload with whatever endpoint or route your experiment requires.

Note: The exact Perplexity endpoints/paths may change. These snippets only show how to set the Cookie header correctly.

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
import requests

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
import fetch from "node-fetch"; // Node < 18; for Node >= 18, global fetch is available

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

Troubleshooting:

- 401/403 after it used to work → Your cookie expired. Re-copy it from the browser while logged in.
- 429/Rate limited → Slow down and respect fair use; automatic scraping may be blocked.
- Empty or HTML response when you expected JSON → You might be hitting a page endpoint. Inspect your browser’s Network tab to mirror the exact URL, method, and headers your browser uses.


## 2) Default LaTeX prompt template

Below is an “original default” LaTeX‑aware prompt you can paste into your system or user prompt to get consistently formatted math. It balances clarity, correctness, and copy‑paste‑ability.

Short version (use inline):

```
You are a math and LaTeX expert. For math:
- Use $...$ for inline math and $$...$$ for display equations.
- Do not place LaTeX inside Markdown code blocks.
- Keep LaTeX valid and minimal: standard amsmath/amsfonts commands only.
- When giving a final result, also output a minimal standalone LaTeX document between the markers BEGIN_LATEX and END_LATEX that renders only the final answer.
```

Full version (system prompt):

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

You can combine the short version in a user prompt with the full version as a system prompt for stronger control.

Tips:

- If your application renders Markdown, most renderers (including GitHub) support LaTeX via MathJax when enabled. Use `$` / `$$` as shown.
- If you need raw TeX output without Markdown surrounding text, ask for only the content between `BEGIN_LATEX` and `END_LATEX`.


## 3) Recommended project hygiene

- Never commit secrets: add `.env`, `cookies.txt`, and similar files to `.gitignore`.
- Rotate your cookie periodically by re‑copying it from the browser.
- Prefer environment variables over hard‑coded values.


## 4) FAQ

- Why do I get HTML instead of JSON?
  - You’re likely calling a page endpoint. Mirror your browser’s exact request (URL, method, headers). Use DevTools → Network to inspect.

- Can I extract only a subset of cookies?
  - Sometimes a single session cookie is enough; other times multiple cookies are required. The safest approach is to copy the complete `cookie` header as seen in a live, authenticated request.

- Is there an official API I should use instead?
  - If/when Perplexity offers a supported API plan for your needs, prefer that. This guide is for experiments and personal use.


## License

MIT — see LICENSE.
