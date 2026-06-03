import re
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st

load_dotenv()
api_key = st.secrets["GEMINI_API_KEY"]

MODEL_VERSION = "gemini-2.5-flash"
client = genai.Client(api_key=api_key)

st.set_page_config(page_title="Casio-chan", page_icon="⚡", layout="centered")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    color: #111 !important;
}

/* ── Force light background everywhere ── */
.stApp, .stApp > *, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stSidebar"], .main, .block-container {
    background-color: #ffffff !important;
    color: #111111 !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Title ── */
h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.9rem !important;
    color: #1a1a1a !important;
    margin-bottom: 10px !important;
}
h5, h4, h3 { color: #444 !important; font-family: 'Syne', sans-serif !important; }

/* ── Chat messages ── */
.stChatMessage {
    background: #f8f8fa !important;
    border: 1px solid #e4e4ec !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    color: #111 !important;
}
.stChatMessage p, .stChatMessage span, .stChatMessage div {
    color: #111 !important;
}

/* ── Bottom fixed panel ── */
.bottom-panel {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: #ffffff;
    border-top: 2px solid #e4e4ec;
    padding: 10px 20px 14px;
    z-index: 1000;
}

.main .block-container {
    padding-bottom: 400px;
    padding-top: 1rem;
    max-width: 820px;
}

/* ── All buttons: uniform size ── */
.stButton > button {
    width: 100px;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    padding: 0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: 1.5px solid #d0d0e0 !important;
    background: #f5f5fb !important;
    color: #333 !important;
    transition: all 0.15s !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    background: #ede9fe !important;
    border-color: #7c3aed !important;
    color: #5b21b6 !important;
}

/* ── Send button special style ── */
.send-btn > button {
    background: #5b21b6 !important;
    color: #fff !important;
    border-color: #5b21b6 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}
.send-btn > button:hover {
    background: #4c1d95 !important;
    border-color: #4c1d95 !important;
    color: #fff !important;
}

/* ── Tab buttons ── */
.tab-active > button {
    background: #5b21b6 !important;
    color: #fff !important;
    border-color: #5b21b6 !important;
    font-family: 'Syne', sans-serif !important;
}
.tab-inactive > button {
    background: #fff !important;
    color: #666 !important;
    border-color: #ccc !important;
    font-family: 'Syne', sans-serif !important;
}

/* ── Input textarea ── */
textarea {
    background: #f8f8fa !important;
    border: 1.5px solid #d0d0e0 !important;
    border-radius: 10px !important;
    color: #111 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
}
textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px #ede9fe !important;
}
[data-testid="stTextAreaLabel"] { display: none !important; }

/* ── LaTeX ── */
.stLatex { color: #111 !important; }

/* ── Alerts ── */
.stAlert { border-radius: 10px !important; }

/* ── Section label in keyboard .send-btn > button── */
.kb-section-label {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: #888;
    text-transform: uppercase;
    margin: 4px 0 2px 2px;
}

div[data-testid="stButton"] button[kind="primary"] {
    background: #5b21b6 !important;
    color: white !important;
}
</style>
""",
    unsafe_allow_html=True,
)

SYS_PROMPT = """
# Identity
Bạn là Casio-chan ⚡🧠 — AI chuyên toán THCS/THPT, đại số, hình học, giải tích, xác suất, thuật toán.
Phong cách: tự nhiên, rõ ràng, thân thiện, hơi vui tính. Xưng "tớ - cậu".
Công thức: luôn dùng $$ ... $$ (block). KHÔNG dùng inline $...$

# Lỗi đề bài
Nếu đề không hợp lệ, thiếu dữ kiện, hoặc sai cú pháp → thông báo:
"⚠️ Đề bài có vẻ bị lỗi: [mô tả]. Cậu kiểm tra lại nhé?"

# Core Behavior
1. Đọc kỹ đề, phân tích dữ kiện
2. Xác định dạng toán
3. Trình bày từng bước rõ ràng  
4. Kiểm tra kết quả cuối

# Format
- Dùng markdown, xuống dòng hợp lý
- Công thức: $$ ... $$
- Bài khó: chia nhỏ bước, giải thích logic
- Nếu nhiều cách: cơ bản trước, tối ưu sau
"""

# ── Math keyboard layout ──
# Each tab: list of (label, inserted_text)
KEYBOARD = {
    "Đại số": [
        ("x²", "x^2"),
        ("xⁿ", "x^n"),
        ("√x", "\\sqrt{}"),
        ("ⁿ√x", "\\sqrt[n]{}"),
        ("a/b", "\\frac{}{}"),
        ("|x|", "\\left|x\\right|"),
        ("log", "\\log_{}()"),
        ("ln", "\\ln()"),
        ("∞", "\\infty"),
        ("%", "%"),
        ("(", "("),
        (")", ")"),
        ("<", "<"),
        ("≤", "≤"),
        (">", ">"),
        ("≥", "≥"),
        ("≠", "≠"),
        ("=", "="),
        ("x", "x"),
        ("y", "y"),
        ("i", "i"),
    ],
    "Lượng giác": [
        ("sin", "\\sin()"),
        ("cos", "\\cos()"),
        ("tan", "\\tan()"),
        ("csc", "\\csc()"),
        ("sec", "\\sec()"),
        ("cot", "\\cot()"),
        ("arcsin", "\\arcsin()"),
        ("arccos", "\\arccos()"),
        ("arctan", "\\arctan()"),
        ("π", "π"),
        ("x²", "x^2"),
        ("x°", "x°"),
        ("(", "("),
        (")", ")"),
        ("=", "="),
        ("x", "x"),
        ("y", "y"),
        ("0", "0"),
    ],
    "Giải tích": [
        ("d/dx", "\\frac{d}{dx}"),
        ("∞", "∞"),
        ("ⁿ√", "\\sqrt[n]{}"),
        ("lim", "\\lim_{}"),
        ("lim→∞", "\\lim_{x\\to\\infty}"),
        ("lim→a", "\\lim_{x\\to a}"),
        ("log", "\\log_{}()"),
        ("C(n,k)", "C(n,k)"),
        ("P(n,k)", "P(n,k)"),
        ("∑", "∑"),
        ("∫", "∫"),
        ("∫ₐᵇ", "\\int_{a}^{b}"),
        ("e", "e"),
        ("(", "("),
        (")", ")"),
        ("x", "x"),
        ("y", "y"),
        ("=", "="),
        ("∈", "∈"),
        ("∉", "∉"),
        ("∪", "∪"),
        ("∩", "∩"),
        ("∀", "∀"),
        ("∃", "∃"),
        ("→", "→"),
        ("↔", "↔"),
        ("°", "°"),
    ],
}

COLS_PER_ROW = 6  # symbols per row — 18 symbols → 2 rows of 9
MAX_SYMBOLS = max(len(v) for v in KEYBOARD.values())  # cố định layout bàn phim


def render_message(message):
    parts = re.split(r"(\$\$.*?\$\$)", message, flags=re.DOTALL)
    for part in parts:
        if part.startswith("$$") and part.endswith("$$"):
            st.latex(part[2:-2].strip())
        else:
            if part.strip():
                st.markdown(part)


initial_bot_mess = (
    "Hí chào cậu, tớ là Casio-chan ⚡🧠\nCậu muốn giải bài gì? Tớ chuyên Toán nè!"
)


def submit_prompt():
    st.session_state.current_prompt = st.session_state.prompt_area
    st.session_state.prompt_area = ""


def chatbot_ui():
    st.title("⚡ Casio-chan")
    st.markdown("##### Toán gì cũng giải được — nhắm mắt cũng xong!")

    # ── Session state init ──
    if "conversation_log" not in st.session_state:
        st.session_state.conversation_log = [
            {"role": "assistant", "content": initial_bot_mess}
        ]
    if "kb_tab" not in st.session_state:
        st.session_state.kb_tab = "Đại số"

    # FIX 1: Xóa prompt TRƯỚC khi widget render (dùng flag)
    if st.session_state.get("_clear_prompt"):
        st.session_state.prompt_area = ""
        st.session_state._clear_prompt = False

    if "prompt_area" not in st.session_state:
        st.session_state.prompt_area = ""

    # ── Chat history ──
    for message in st.session_state.conversation_log:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                render_message(message["content"])

    # ════════════════════════════════
    # BOTTOM PANEL
    # ════════════════════════════════
    st.markdown('<div class="bottom-panel">', unsafe_allow_html=True)

    # ── Row 1: Tab selector ──
    tab_names = list(KEYBOARD.keys())
    tab_cols = st.columns([1, 1, 1, 4])
    for i, tab in enumerate(tab_names):
        active = st.session_state.kb_tab == tab
        label = f"{tab}" if active else tab
        with tab_cols[i]:
            if st.button(
                label,
                key=f"tab_{tab}",
                type="primary" if active else "secondary",
            ):
                st.session_state.kb_tab = tab
                st.rerun()

    # ── Row 2: Symbol buttons ──
    symbols = KEYBOARD[st.session_state.kb_tab].copy()
    while len(symbols) < MAX_SYMBOLS:
        symbols.append(("", ""))
    rows_needed = len(symbols) // COLS_PER_ROW
    for row_i in range(rows_needed):
        row_syms = symbols[row_i * COLS_PER_ROW : (row_i + 1) * COLS_PER_ROW]
        btn_cols = st.columns(COLS_PER_ROW)
        for j, (label, sym) in enumerate(row_syms):
            with btn_cols[j]:
                if label:
                    if st.button(
                        label, key=f"sym_{st.session_state.kb_tab}_{row_i}_{j}"
                    ):
                        st.session_state.prompt_area += sym
                        st.rerun()

    # ── Row 3: Textarea + Send ──
    with st.form("chat_form"):
        prompt = st.text_area(
            "",
            key="prompt_area",
            height=72,
        )
        send = st.form_submit_button("⚡ Gửi")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Send logic ──
    if send:
        current_prompt = prompt.strip()
        if not current_prompt:
            st.warning("Nhập đề bài trước nhé 😅")
            return

        # Thêm tin nhắn user vào lịch sử
        st.session_state.conversation_log.append(
            {"role": "user", "content": current_prompt}
        )

        # Gọi API
        with st.spinner("Casio-chan đang đăm chiêu... 🧠"):
            try:
                response = client.models.generate_content(
                    model=MODEL_VERSION,
                    contents=current_prompt,
                    config=types.GenerateContentConfig(system_instruction=SYS_PROMPT),
                )
                bot_reply = response.text
                if not bot_reply or not bot_reply.strip():
                    bot_reply = (
                        "⚠️ Tớ không tạo được phản hồi. Cậu thử đặt lại đề bài nhé?"
                    )
            except Exception as e:
                err = str(e)
                if any(k in err.lower() for k in ("invalid", "syntax", "parse")):
                    bot_reply = f"⚠️ Đề bài có vẻ bị lỗi cú pháp. Cậu kiểm tra lại công thức nhé?\n\n`{err}`"
                else:
                    bot_reply = f"😭 Đã xảy ra lỗi:\n\n`{err}`"

        # Thêm phản hồi bot vào lịch sử
        st.session_state.conversation_log.append(
            {"role": "assistant", "content": bot_reply}
        )

        # FIX 2: Set flag xóa prompt, sau đó mới rerun
        st.session_state._clear_prompt = True
        st.rerun()


if __name__ == "__main__":
    chatbot_ui()
