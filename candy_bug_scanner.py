import streamlit as st
import json
from groq import Groq

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="🍬 Candy Bug Scanner",
    page_icon="🍬",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;600;700;800;900&family=Fira+Code:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Baloo 2', sans-serif !important;
    background-color: #0a0212 !important;
    color: #f0e8ff !important;
}
.stApp {
    background: radial-gradient(ellipse at 15% 10%, #4a0a7033 0%, transparent 55%),
                radial-gradient(ellipse at 85% 90%, #0a3a5533 0%, transparent 55%),
                #0a0212;
}
.candy-header { text-align: center; padding: 10px 0 28px; }
.candy-pill {
    display: inline-block;
    background: linear-gradient(135deg, #ff6eb420, #c084fc20);
    border: 1px solid #ff6eb450; border-radius: 100px;
    padding: 4px 18px; font-size: 0.72rem; font-weight: 800;
    letter-spacing: 0.12em; text-transform: uppercase; color: #ff6eb4; margin-bottom: 10px;
}
.candy-title {
    font-size: 2.6rem; font-weight: 900;
    background: linear-gradient(135deg, #ff6eb4 0%, #c084fc 50%, #60d0ff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1.1; margin-bottom: 6px;
}
.candy-sub { color: #7a5f99; font-size: 0.92rem; font-weight: 600; }
.metric-row { display: flex; gap: 12px; margin: 16px 0; }
.metric-box {
    flex: 1; background: #120720; border: 1px solid #2a0f45;
    border-radius: 12px; padding: 14px 10px; text-align: center;
    font-family: 'Fira Code', monospace;
}
.metric-val { font-size: 1.8rem; font-weight: 700; line-height: 1; }
.metric-lbl { font-size: 0.65rem; color: #7a5f99; margin-top: 4px;
              letter-spacing: 0.1em; text-transform: uppercase; }
.summary-bar {
    background: #120720; border: 1px solid #2a0f45;
    border-radius: 14px; padding: 14px 18px; margin: 16px 0;
}
.summary-text { color: #3dffc0; font-weight: 700; font-size: 0.9rem; }
.lang-badge {
    display: inline-block; border-radius: 100px; border: 1px solid;
    padding: 5px 16px; font-size: 0.78rem; font-weight: 800;
    letter-spacing: 0.08em; margin-bottom: 12px;
}
.stTextArea textarea {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.8rem !important;
    background: #120720 !important;
    color: #d4b8ff !important;
    border: 1px solid #2a0f45 !important;
    border-radius: 12px !important;
}
.stButton > button {
    width: 100%; padding: 14px !important;
    background: linear-gradient(135deg, #ff6eb4, #c084fc) !important;
    color: white !important; font-family: 'Baloo 2', sans-serif !important;
    font-size: 1rem !important; font-weight: 800 !important;
    border: none !important; border-radius: 14px !important;
    box-shadow: 0 4px 24px #ff6eb440 !important;
    letter-spacing: 0.04em !important;
}
div[data-testid="stExpander"] {
    background: #120720 !important;
    border: 1px solid #2a0f45 !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ── System prompt ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert code reviewer and debugger supporting ALL programming languages.
The user will paste code in any language. Your job is to:
1. Detect the programming language automatically
2. Find ALL bugs, issues, bad practices, and potential improvements
3. Auto-fix every single issue and return the corrected code

Respond ONLY with a JSON object (no markdown, no backticks) in this exact shape:
{
  "language": "detected language name",
  "bugs": [
    {
      "id": 1,
      "severity": "critical|warning|suggestion",
      "line": <line number or null>,
      "title": "Short bug title",
      "description": "What is wrong and why it matters",
      "fix": "What was changed to fix it"
    }
  ],
  "fixedCode": "the full corrected code as a string",
  "summary": "One sentence summary of overall code health"
}"""

# ── Examples ───────────────────────────────────────────────────
EXAMPLES = {
    "Python — Division by zero": """\
def divide(a, b):
    return a / b

result = divide(10, 0)
print(result)
""",
    "JavaScript — Unhandled promise": """\
function fetchUser(id) {
  fetch('/api/user/' + id)
    .then(res => res.json())
    .then(data => {
      console.log(data.name)
    })
}
fetchUser(null)
""",
    "Java — Null pointer": """\
public class Main {
  public static void main(String[] args) {
    String s = null;
    System.out.println(s.length());
  }
}
""",
}

SEVERITY_COLORS = {
    "critical":   {"color": "#ff6eb4", "bg": "#2a0a1a", "icon": "💥"},
    "warning":    {"color": "#ffe94d", "bg": "#1f1a00", "icon": "⚠️"},
    "suggestion": {"color": "#3dffc0", "bg": "#001f15", "icon": "✨"},
}

LANG_COLORS = {
    "python": "#3dffc0", "javascript": "#ffe94d", "typescript": "#60d0ff",
    "java": "#ff7b6b", "c++": "#c084fc", "c": "#c084fc", "rust": "#ff6eb4",
    "go": "#60d0ff", "ruby": "#ff6eb4", "php": "#c084fc",
}

# ── Header ─────────────────────────────────────────────────────
st.markdown("""
<div class="candy-header">
  <div class="candy-pill">🍬 Multi-Language · AI Bug Detector</div>
  <div class="candy-title">Candy Bug Scanner</div>
  <div class="candy-sub">Paste any code in any language — AI finds & fixes every bug instantly</div>
</div>
""", unsafe_allow_html=True)

# ── API Key input ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Groq API Key")
    api_key = st.text_input(
        "Enter your Groq API key",
        type="password",
        placeholder="gsk_...",
        help="Get your free key at console.groq.com"
    )
    st.markdown("[Get free Groq API key →](https://console.groq.com)", unsafe_allow_html=False)
    st.divider()
    st.markdown("### 🤖 Model")
    model = st.selectbox(
        "Choose Groq model",
        ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"],
        index=0,
    )

# ── Example loader ─────────────────────────────────────────────
st.markdown("**🧪 Try an example:**")
col1, col2, col3 = st.columns(3)
load_example = None
with col1:
    if st.button("🐍 Python"):       load_example = "Python — Division by zero"
with col2:
    if st.button("🟨 JavaScript"):   load_example = "JavaScript — Unhandled promise"
with col3:
    if st.button("☕ Java"):          load_example = "Java — Null pointer"

if load_example:
    st.session_state["code_input"] = EXAMPLES[load_example]

# ── Code input ─────────────────────────────────────────────────
code = st.text_area(
    "Paste your code below:",
    value=st.session_state.get("code_input", ""),
    height=260,
    placeholder="# Paste any code here...\n# Python, JavaScript, Java, C++, Go, Rust, Ruby, PHP...\n# AI will auto-detect the language and find all bugs!",
    key="code_input",
)

# ── Scan button ────────────────────────────────────────────────
scan = st.button("🍬 Scan & Auto-Fix My Code", disabled=not code.strip())

# ── Run scan ───────────────────────────────────────────────────
if scan and code.strip():
    if not api_key:
        st.error("❌ Please enter your Groq API key in the sidebar first.")
        st.stop()

    with st.spinner("🔍 AI is scanning your code… detecting language · finding bugs · preparing fixes"):
        try:
            # ── GROQ API CALL ──────────────────────────────────
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": f"Analyze this code and return only the JSON:\n\n{code}"},
                ],
                temperature=0.2,
                max_tokens=4000,
            )
            raw   = response.choices[0].message.content.strip()
            clean = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean)
            # ──────────────────────────────────────────────────

            detected_lang = result.get("language", "Unknown")
            bugs          = result.get("bugs", [])
            fixed_code    = result.get("fixedCode", "")
            summary       = result.get("summary", "")

            # Language badge
            lang_color = LANG_COLORS.get(detected_lang.lower(), "#a07ab8")
            st.markdown(f"""
            <div class="lang-badge" style="color:{lang_color};border-color:{lang_color}55;background:{lang_color}12;">
              🔍 Detected: <strong>{detected_lang}</strong>
            </div>
            """, unsafe_allow_html=True)

            # Summary
            st.markdown(f"""
            <div class="summary-bar">
              <span class="summary-text">✅ {summary}</span>
            </div>
            """, unsafe_allow_html=True)

            # Metrics
            criticals   = sum(1 for b in bugs if b["severity"] == "critical")
            warnings    = sum(1 for b in bugs if b["severity"] == "warning")
            suggestions = sum(1 for b in bugs if b["severity"] == "suggestion")

            st.markdown(f"""
            <div class="metric-row">
              <div class="metric-box">
                <div class="metric-val" style="color:#f0e8ff">{len(bugs)}</div>
                <div class="metric-lbl">Total Issues</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="color:#ff6eb4">{criticals}</div>
                <div class="metric-lbl">💥 Critical</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="color:#ffe94d">{warnings}</div>
                <div class="metric-lbl">⚠️ Warnings</div>
              </div>
              <div class="metric-box">
                <div class="metric-val" style="color:#3dffc0">{suggestions}</div>
                <div class="metric-lbl">✨ Tips</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Bug cards
            if bugs:
                st.markdown(f"#### 🐛 {len(bugs)} Issue{'s' if len(bugs) != 1 else ''} Found")
                for bug in bugs:
                    s = SEVERITY_COLORS.get(bug["severity"], SEVERITY_COLORS["suggestion"])
                    line_txt = f"  —  line {bug['line']}" if bug.get("line") else ""
                    with st.expander(f"{s['icon']} #{bug['id']} — {bug['title']}{line_txt}"):
                        st.markdown(f"""
                        <div style="font-size:0.84rem;color:#c8aae8;line-height:1.6;margin-bottom:10px;">
                          {bug['description']}
                        </div>
                        <div style="font-size:0.68rem;font-weight:800;text-transform:uppercase;
                                    letter-spacing:0.1em;color:#3dffc0;margin-bottom:4px;">
                          🔧 Fix Applied
                        </div>
                        <div style="font-size:0.82rem;color:#a8f5dc;line-height:1.6;">
                          {bug['fix']}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.success("🎉 No bugs found — your code is clean!")

            # Fixed code
            if fixed_code:
                st.markdown("#### ✅ Auto-Fixed Code")
                st.code(fixed_code, language=detected_lang.lower())
                st.download_button(
                    label="⬇️ Download Fixed Code",
                    data=fixed_code.encode("utf-8"),
                    file_name=f"fixed_code.txt",
                    mime="text/plain",
                )

        except json.JSONDecodeError:
            st.error("❌ Couldn't parse AI response. Try again.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
