from flask import Flask, render_template_string, request, jsonify, send_from_directory
from curl_cffi import requests
import json
import sys
import re
import os
import uuid
import time
import threading
from datetime import datetime, timedelta
import requests as std_requests

app = Flask(__name__)

# Windows stdout/stderr unicode handling
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

UPLOAD_FOLDER = 'generated_resumes'
CLEANUP_INTERVAL = 3600  # seconds

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple in-memory metadata for generated files
file_metadata = {}

# Dark minimal UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>ResumeStudio — Minimal Dark</title>
    <style>
        :root {
            --bg: #0b0f17;
            --panel: #121826;
            --muted: #a3b1c6;
            --text: #e6edf7;
            --primary: #7c9cff;
            --primary-2: #5d7ef4;
            --success: #22c55e;
            --error: #ef4444;
            --border: #202a3c;
            --code-bg: #0f1625;
        }
        * { box-sizing: border-box; }
        html, body { height: 100%; }
        body {
            margin: 0;
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell,
                Noto Sans, Helvetica Neue, Arial, \"Apple Color Emoji\", \"Segoe UI Emoji\";
            color: var(--text);
            background: radial-gradient(1200px 600px at 10% 10%, #10192b 0%, #0b0f17 60%) no-repeat fixed;
            display: grid;
            place-items: center;
            padding: 24px;
        }
        .app {
            width: min(1100px, 100%);
            display: grid;
            gap: 18px;
        }
        .header {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo {
            width: 36px; height: 36px; border-radius: 8px;
            display: grid; place-items: center;
            background: linear-gradient(135deg, var(--primary), #9e77ff);
            box-shadow: 0 8px 24px rgba(124, 156, 255, 0.25);
            font-size: 18px;
        }
        .title {
            font-weight: 700;
            letter-spacing: 0.3px;
        }
        .panel {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px;
        }
        label { display: block; color: var(--muted); font-size: 14px; margin-bottom: 8px; }
        textarea {
            width: 100%;
            min-height: 180px;
            resize: vertical;
            background: #0c1220;
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 14px;
            font-size: 14px;
            line-height: 1.4;
            outline: none;
            transition: border-color .2s, box-shadow .2s;
        }
        textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 4px rgba(124, 156, 255, .12); }
        .row { display: flex; gap: 12px; align-items: center; }
        .row.wrap { flex-wrap: wrap; }
        button {
            appearance: none; border: none; outline: none; cursor: pointer;
            background: linear-gradient(135deg, var(--primary), var(--primary-2));
            color: white; font-weight: 600; letter-spacing: .2px;
            padding: 12px 16px; border-radius: 12px; min-width: 160px;
            box-shadow: 0 10px 24px rgba(124, 156, 255, 0.25);
            transition: transform .12s ease, filter .2s ease, opacity .2s ease;
        }
        button:hover { transform: translateY(-1px); filter: brightness(1.05); }
        button:active { transform: translateY(0); filter: brightness(.98); }
        button.secondary {
            background: transparent; color: var(--muted); box-shadow: none; border: 1px solid var(--border);
        }
        button:disabled { opacity: .6; cursor: not-allowed; }
        .status { font-size: 14px; color: var(--muted); }
        .status.ok { color: var(--success); }
        .status.err { color: var(--error); }

        .grid { display: grid; gap: 18px; grid-template-columns: 1fr; }
        @media (min-width: 1000px) {
            .grid { grid-template-columns: 1.1fr .9fr; }
        }
        .section-title { font-size: 13px; color: var(--muted); margin-bottom: 10px; }
        .code {
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace;
            font-size: 12.5px;
            color: #d1e0ff;
            line-height: 1.45;
            max-height: 520px;
            overflow: auto;
            white-space: pre;
        }
        .muted { color: var(--muted); }
        .link { color: var(--primary); text-decoration: none; }
        .link:hover { text-decoration: underline; }
        .pdfbox { height: 560px; border-radius: 12px; overflow: hidden; border: 1px solid var(--border); background: #0c1220; }
        .pdfbox iframe { width: 100%; height: 100%; border: 0; background: #0c1220; }
        .hidden { display: none !important; }
        .footer { color: var(--muted); font-size: 12px; text-align: center; }
        .badge { font-size: 12px; padding: 6px 10px; border-radius: 999px; border: 1px solid var(--border); color: var(--muted); }
        .spacer { height: 4px; }
        .actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .small { font-size: 12px; }
        .chip { background: #0c1220; padding: 8px 10px; border-radius: 10px; border: 1px solid var(--border); }
        .right { margin-left: auto; }
    </style>
</head>
<body>
    <div class=\"app\">
        <div class=\"row\">
            <div class=\"logo\">📄</div>
            <div>
                <div class=\"title\">ResumeStudio</div>
                <div class=\"small muted\">Minimal dark tool to generate ATS-optimized LaTeX and preview the PDF</div>
            </div>
            <div class=\"right badge\">1-hour auto cleanup</div>
        </div>

        <div class=\"panel\">
            <label for=\"jobDescription\">Paste Job Description</label>
            <textarea id=\"jobDescription\" placeholder=\"Paste the complete job description here...\" spellcheck=\"false\"></textarea>
            <div class=\"spacer\"></div>
            <div class=\"row actions\">
                <button id=\"generateBtn\">Generate</button>
                <button id=\"clearBtn\" class=\"secondary\">Clear</button>
                <div id=\"status\" class=\"status\"></div>
            </div>
        </div>

        <div class=\"grid\">
            <div class=\"panel\">
                <div class=\"section-title\">LaTeX Code</div>
                <div class=\"row actions\">
                    <button id=\"copyLatex\" class=\"secondary\">Copy</button>
                    <a id=\"downloadPdf\" class=\"link hidden\" href=\"#\" download>Download PDF</a>
                </div>
                <div id=\"latexContainer\" class=\"code muted\">No output yet.</div>
            </div>

            <div class=\"panel\">
                <div class=\"section-title\">PDF Preview</div>
                <div id=\"pdfContainer\" class=\"pdfbox hidden\">
                    <iframe id=\"pdfFrame\" title=\"Resume PDF Preview\"></iframe>
                </div>
                <div id=\"pdfPlaceholder\" class=\"muted\">Your PDF preview will appear here after generation.</div>
            </div>
        </div>

        <div class=\"footer muted\">Built with the same AI + PDF generation pipeline. Files are auto-deleted after 1 hour.</div>
    </div>

    <script>
        const $ = (sel) => document.querySelector(sel);
        const jobDescription = $('#jobDescription');
        const generateBtn = $('#generateBtn');
        const clearBtn = $('#clearBtn');
        const status = $('#status');
        const latexContainer = $('#latexContainer');
        const copyLatexBtn = $('#copyLatex');
        const pdfContainer = $('#pdfContainer');
        const pdfFrame = $('#pdfFrame');
        const pdfPlaceholder = $('#pdfPlaceholder');
        const downloadPdf = $('#downloadPdf');

        function setStatus(msg, type = 'muted') {
            status.textContent = msg;
            status.className = 'status ' + (type === 'ok' ? 'ok' : type === 'err' ? 'err' : '');
        }

        function showPDF(url) {
            pdfContainer.classList.remove('hidden');
            pdfPlaceholder.classList.add('hidden');
            pdfFrame.src = url + '#view=FitH';
        }

        generateBtn.addEventListener('click', async () => {
            const text = jobDescription.value.trim();
            if (!text) {
                setStatus('Please paste a job description.', 'err');
                return;
            }

            generateBtn.disabled = true;
            setStatus('Generating optimized LaTeX and PDF… This can take up to ~2 minutes.');
            latexContainer.textContent = '';

            try {
                const res = await fetch('/optimize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ job_description: text })
                });
                const data = await res.json();

                if (!res.ok || data.error) {
                    throw new Error(data.error || 'Unexpected error');
                }

                if (data.latex_code) {
                    latexContainer.textContent = data.latex_code;
                    latexContainer.classList.remove('muted');
                }

                if (data.success && data.pdf_generated && data.preview_url && data.download_url) {
                    showPDF(data.preview_url);
                    downloadPdf.classList.remove('hidden');
                    downloadPdf.href = data.download_url;
                    setStatus('Success. PDF ready — view preview or download. Cleanup at: ' + new Date(data.cleanup_time).toLocaleString(), 'ok');
                } else if (data.success && !data.pdf_generated) {
                    setStatus('LaTeX generated, but PDF failed: ' + (data.pdf_error || 'unknown error'), 'err');
                } else {
                    setStatus('Failed: ' + (data.error || 'Unknown error'), 'err');
                }
            } catch (e) {
                setStatus('Network or server error: ' + e.message, 'err');
            } finally {
                generateBtn.disabled = false;
            }
        });

        clearBtn.addEventListener('click', () => {
            jobDescription.value = '';
            latexContainer.textContent = 'No output yet.';
            latexContainer.classList.add('muted');
            pdfContainer.classList.add('hidden');
            pdfPlaceholder.classList.remove('hidden');
            pdfFrame.src = '';
            downloadPdf.classList.add('hidden');
            setStatus('');
        });

        copyLatexBtn.addEventListener('click', async () => {
            const text = latexContainer.textContent || '';
            if (!text || text === 'No output yet.') return;
            try {
                await navigator.clipboard.writeText(text);
                setStatus('LaTeX copied to clipboard.', 'ok');
            } catch (e) {
                setStatus('Failed to copy.', 'err');
            }
        });
    </script>
</body>
</html>
"""


def cleanup_old_files():
    current_time = datetime.now()
    files_to_remove = []

    for file_id, metadata in list(file_metadata.items()):
        if current_time - metadata['created_at'] > timedelta(seconds=CLEANUP_INTERVAL):
            files_to_remove.append(file_id)

    for file_id in files_to_remove:
        try:
            file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pdf")
            if os.path.exists(file_path):
                os.remove(file_path)
            file_metadata.pop(file_id, None)
            print(f"Cleaned up file: {file_id}")
        except Exception as e:
            print(f"Error cleaning up file {file_id}: {e}")


def start_cleanup_scheduler():
    def cleanup_loop():
        while True:
            time.sleep(300)
            cleanup_old_files()

    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()


# ========= AI + PDF Generation ========= #

def ask_perplexity(query: str):
    url = "https://www.perplexity.ai/rest/sse/perplexity_ask"

    payload = {
        "params": {
            "attachments": [],
            "language": "en-US",
            "timezone": "Asia/Kolkata",
            "search_focus": "internet",
            "sources": ["web"],
            "frontend_uuid": "fae808a1-d386-4d43-85ff-cbdede546228",
            "mode": "copilot",
            "model_preference": "gemini2flash",
            "query_source": "home",
            "dsl_query": query,
            "version": "2.18"
        },
        "query_str": query
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Content-Type': 'application/json',
        'Referer': 'https://www.perplexity.ai/',
        'Origin': 'https://www.perplexity.ai',
        'Cookie': 'pplx.visitor-id=8839cf87-f6ac-4df0-a96a-d66d29b4e347'
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            impersonate="chrome110",
            timeout=120_000,
        )
        response.encoding = 'utf-8'
        final_answer = None

        for line in response.text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            try:
                data = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue

            if data.get("final") or data.get("status") == "COMPLETED":
                blocks = data.get("blocks", [])
                for block in blocks:
                    markdown = block.get("markdown_block")
                    if markdown and "answer" in markdown:
                        final_answer = markdown["answer"]
                        break

        return final_answer or "Warning: No answer found."

    except Exception as e:
        return f"Error occurred: {str(e)}"


def sanitize_latex(latex: str) -> str:
    if not latex:
        return latex
    s = latex.strip()
    # Remove fenced code markers like ``` or ```latex at start/end of lines
    s = re.sub(r'^\s*```[\w-]*\s*$', '', s, flags=re.MULTILINE)
    # Remove any remaining triple backticks just in case
    s = s.replace('```', '')
    # Truncate anything after \end{document}
    end_match = re.search(r'\\end{document}', s, flags=re.IGNORECASE)
    if end_match:
        s = s[:end_match.end()]
    return s.strip()


def extract_latex_code(text: str):
    if not text:
        return None
    # Prefer explicit latex/tex fenced block
    m = re.search(r'```(?:latex|tex)\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if m:
        return sanitize_latex(m.group(1))
    # Fallback: any fenced block that appears to contain LaTeX
    m2 = re.search(r'```[\w-]*\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if m2 and ('\\documentclass' in m2.group(1) or '\\begin{document}' in m2.group(1)):
        return sanitize_latex(m2.group(1))
    # Fallback: slice from first \\documentclass to end
    start = text.find('\\documentclass')
    if start != -1:
        end_match2 = re.search(r'\\end{document}', text[start:], re.IGNORECASE | re.DOTALL)
        if end_match2:
            end_index = start + end_match2.end()
            return sanitize_latex(text[start:end_index])
        return sanitize_latex(text[start:])
    return None


def convert_latex_to_pdf(latex_code: str):
    try:
        unique_id = str(uuid.uuid4())
        url = f"https://texviewer.herokuapp.com/upload.php?uid={unique_id}"

        payload = {
            'texts': latex_code,
            'nonstopmode': '1',
            'title': 'Optimized Resume'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Origin': 'https://texviewer.herokuapp.com',
            'Referer': 'https://texviewer.herokuapp.com/'
        }

        response = std_requests.post(url, headers=headers, data=payload, timeout=30)

        if response.status_code == 200:
            return check_pdf_status(unique_id)
        else:
            return f"Error submitting LaTeX: HTTP {response.status_code}"

    except Exception as e:
        return f"Error converting to PDF: {str(e)}"


def check_pdf_status(unique_id: str, max_attempts=30, delay=2):
    check_url = "https://texviewer.herokuapp.com/upload.php?action=checkcomplete"

    payload = {
        'uid': unique_id,
        'resultfile': f'temp/{unique_id}-result.txt'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Origin': 'https://texviewer.herokuapp.com',
        'Referer': 'https://texviewer.herokuapp.com/'
    }

    for attempt in range(max_attempts):
        try:
            response = std_requests.post(check_url, headers=headers, data=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()

                if 'error' in result and result['error']:
                    return f"PDF generation error: {result['error']}"

                if 'pdfname' in result:
                    return download_and_save_pdf(result['pdfname'], unique_id)
                elif 'progress' in result:
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                        continue
                    else:
                        return f"PDF generation timeout"

        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
                continue
            else:
                return f"Error checking PDF status: {str(e)}"

    return "PDF generation timeout"


def download_and_save_pdf(pdf_url: str, unique_id: str):
    try:
        pdf_response = std_requests.get(pdf_url, timeout=30)

        if pdf_response.status_code == 200:
            local_filename = f"{unique_id}.pdf"
            local_path = os.path.join(UPLOAD_FOLDER, local_filename)

            with open(local_path, 'wb') as f:
                f.write(pdf_response.content)

            file_metadata[unique_id] = {
                'created_at': datetime.now(),
                'filename': local_filename,
                'original_url': pdf_url,
            }

            return {
                'status': 'success',
                'file_id': unique_id,
                'local_filename': local_filename,
                'download_url': f'/download/{unique_id}',
                'preview_url': f'/preview/{unique_id}',
                'cleanup_time': datetime.now() + timedelta(seconds=CLEANUP_INTERVAL),
            }
        else:
            return f"Failed to download PDF: HTTP {pdf_response.status_code}"

    except Exception as e:
        return f"Error downloading PDF: {str(e)}"


# ========= Routes ========= #

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404

        filename = file_metadata[file_id]['filename']
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File no longer exists'}), 404

        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/preview/<file_id>')
def preview_file(file_id):
    try:
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404

        filename = file_metadata[file_id]['filename']
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File no longer exists'}), 404

        # Inline preview in browser
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/optimize', methods=['POST'])
def optimize_resume():
    try:
        data = request.get_json(force=True, silent=True) or {}
        job_description = data.get('job_description', '').strip()

        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400

        prompt = f"""MY RESUME LATEX CODE:

\\documentclass[10pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=0.5in]{{geometry}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}
\\usepackage{{fontawesome}}
\\usepackage{{lmodern}}

\\hypersetup{{
    colorlinks=true,
    linkcolor=black,
    urlcolor=black,
}}

\\pagestyle{{empty}}

\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{0pt}}
\\setlength{{\\itemsep}}{{0pt}}

\\begin{{document}}

% Name
\\begin{{center}}
{{\\huge \\textbf{{Koushik Navuluri}}}}
\\end{{center}}

% Contact Info
\\begin{{center}}
\\small
\\faEnvelope\\ \\href{{mailto:koushiknavuluri@gmail.com}}{{koushiknavuluri@gmail.com}} \\quad
\\faPhone\\ 8688660029 \\quad
\\faGlobe\\ \\href{{https://portfolio}}{{portfolio}} \\quad
\\faLinkedin\\ \\href{{https://linkedin.com/koushiknavuluri}}{{LinkedIn}} \\quad
\\faGithub\\ \\href{{https://github.com/koushiknavuluri}}{{Github}}
\\end{{center}}

\\vspace{{6pt}}

% Professional Summary
\\noindent\\textbf{{Professional Summary}}
\\vspace{{2pt}}
\\hrule
\\vspace{{6pt}}
\\noindent
Full-stack developer with expertise in Java, Javascript, Python, and database management. Experienced in Agile development, end-to-end systems design, and delivering scalable solutions. Proven ability to build strong business relationships and manage projects in dynamic environments. Skilled in problem-solving, technical design, and collaborating with global teams

\\vspace{{12pt}}

% Education
\\noindent\\textbf{{Education}}
\\vspace{{2pt}}
\\hrule
\\vspace{{6pt}}
\\noindent
\\textbf{{Bharath University}} \\hfill \\textit{{July 2019 - May 2023}}\\\\
\\textit{{B.Tech in Computer Science and Engineering}} \\hfill GPA: 9.0/10

\\vspace{{12pt}}

% Experience
\\noindent\\textbf{{Experience}}
\\vspace{{2pt}}
\\hrule
\\vspace{{6pt}}
\\noindent
\\textbf{{Accenture}} \\hfill \\textit{{Sep 2023 - Present}}\\\\
\\textit{{Software Engineer - Microservices, AI Integration, React}}
\\begin{{itemize}}[leftmargin=1em, itemsep=3pt, topsep=4pt, parsep=0pt]
    \\item Developed and maintained retail applications for enterprise clients, implementing scalable microservices architecture using React.
    \\item Integrated AI agent solutions to enhance customer experience and automate business processes, resulting in 25% improvement in operational efficiency
    \\item Collaborated with cross-functional teams to deliver end-to-end solutions for retail clients, ensuring high-quality deliverables and client satisfaction
    \\item Implemented robust data processing pipelines and API integrations to support real-time retail operations and inventory management
    \\item Utilized modern development practices including CI/CD pipelines, automated testing, and cloud deployment strategies
\\end{{itemize}}

\\vspace{{6pt}}

\\noindent
\\textbf{{TEACHNOOK}} \\hfill \\textit{{Feb 2023 - Apr 2023}}\\\\
\\textit{{Data Science Intern}}
\\begin{{itemize}}[leftmargin=1em, itemsep=3pt, topsep=4pt, parsep=0pt]
    \\item Explored and analyzed real-world datasets to extract meaningful insights and patterns using Python, Pandas, and NumPy
    \\item Performed comprehensive data preprocessing including cleaning, normalization, and feature engineering for machine learning models
    \\item Developed automated data processing workflows that reduced manual analysis time by 40%
\\end{{itemize}}

\\vspace{{12pt}}

% Projects
\\noindent\\textbf{{Projects}}
\\vspace{{2pt}}
\\hrule
\\vspace{{6pt}}
\\noindent
\\textbf{{URL Shortener - Python, Flask, SQLite}}
\\begin{{itemize}}[leftmargin=1em, itemsep=3pt, topsep=4pt, parsep=0pt]
    \\item Developed a web-based URL shortening service using Python and Flask framework, enabling users to create short, unique URLs that redirect to specific websites
    \\item Implemented secure URL generation with collision detection and database storage using SQLite for efficient data management
    \\item Added analytics tracking to monitor click counts and user engagement, providing valuable insights for URL performance
    \\item Designed responsive web interface with user-friendly features including custom alias options and expiration date settings
\\end{{itemize}}

\\vspace{{6pt}}

\\noindent
\\textbf{{Weather Forecasting Application - Python, APIs, Data Visualization}}
\\begin{{itemize}}[leftmargin=1em, itemsep=3pt, topsep=4pt, parsep=0pt]
    \\item Built a comprehensive weather forecasting application that fetches real-time weather information from cities worldwide using REST APIs
    \\item Integrated multiple weather data sources to ensure accuracy and reliability of forecasts across different geographical locations
\\end{{itemize}}

\\vspace{{12pt}}

% Technologies
\\noindent\\textbf{{Technologies}}
\\vspace{{2pt}}
\\hrule
\\vspace{{6pt}}
\\noindent
\\textbf{{Languages:}} JavaScript, Flutter, Python\\\\[4pt]
\\textbf{{Technologies:}} ReactJs, Redux, NextJS, Git, Jenkins, Docker, Kubernetes, Kafka, Chrome Dev Tools\\\\[4pt]
\\textbf{{Databases:}} MongoDB, PostgreSQL, Redis, MySQL.\\\\[4pt]
\\textbf{{Coursework:}} OOPs, OS, DBMS, Design Patterns, Microservices, SDLC.\\\\[4pt]
\\textbf{{Other Skills:}} Agile development, workflow design, stakeholder management, global collaboration

\\end{{document}}

JOB DETAILS: {job_description}

TASK: Revise the provided LaTeX resume code based on the posted job description. Incorporate all relevant ATS keywords to maximize the ATS score and improve shortlisting potential. Rephrase only the Professional Summary, Experience Descriptions, Project Descriptions, and Technologies sections based on the job description with same length as original text. Ensure the final version fits on one page, no text should exceed to next page please. Return only the complete updated LaTeX code — no explanations or additional text."""

        answer = ask_perplexity(prompt)
        latex_code = extract_latex_code(answer)

        if not latex_code:
            return jsonify({'error': 'Could not extract LaTeX code from response'}), 400

        # Final safety: ensure no stray fences
        latex_code = sanitize_latex(latex_code)

        pdf_response = convert_latex_to_pdf(latex_code)

        if isinstance(pdf_response, dict) and pdf_response.get('status') == 'success':
            return jsonify({
                'success': True,
                'latex_code': latex_code,
                'pdf_generated': True,
                'file_id': pdf_response['file_id'],
                'preview_url': pdf_response['preview_url'],
                'download_url': pdf_response['download_url'],
                'cleanup_time': pdf_response['cleanup_time'].isoformat(),
                'message': 'PDF generated successfully!'
            })
        else:
            return jsonify({
                'success': True,
                'latex_code': latex_code,
                'pdf_generated': False,
                'pdf_error': str(pdf_response),
                'message': 'LaTeX code generated, but PDF generation failed'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    start_cleanup_scheduler()
    print("🚀 ResumeStudio starting (dark minimal)…")
    print("📁 Generated files stored in:", UPLOAD_FOLDER)
    print("🗑️ Automatic cleanup enabled (files deleted after 1 hour)")
    app.run(debug=True, host='0.0.0.0', port=5000)
