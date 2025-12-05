import re
import pdfplumber
import pandas as pd




def extract_text(pdf_path: str) -> str:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += "\n" + t
    return full_text




def parse_mcqs_with_year(text: str, topic: str) -> pd.DataFrame:
    # 1) Precompute year positions (2014–2023 in this PDF)
    year_positions = []
    for m in re.finditer(r"\b(20(?:1[4-9]|2[0-3]))\b", text):
        year_positions.append((m.start(), m.group(1)))

    # 2) Split by "Correct answer:" blocks
    blocks = re.split(r"Correct answer[:\-]?\s*[a-dA-D]", text)[:-1]
    answers = re.findall(r"Correct answer[:\-]?\s*([a-dA-D])", text)

    rows = []

    for block, ans in zip(blocks, answers):
        # Find start index of this block in whole text
        start_idx = text.find(block)

        # ---- Infer year: last year heading before this block ----
        year = ""
        for pos, y in year_positions:
            if pos <= start_idx:
                year = y
            else:
                break

        # ---- Work at line level ----
        lines = [l.strip() for l in block.splitlines() if l.strip()]

        if not lines:
            continue

        # Find line with "Q<number>." if present
        q_start = 0
        for i, l in enumerate(lines):
            if re.match(r"Q\d+\.", l):
                q_start = i
                break

        q_lines = lines[q_start:]
        joined = "\n".join(q_lines)

        # ---- Normalize option markers to a special token ----
        joined_norm = joined
        # Cover (a), a), ( a ), etc.
        for ch in ["a", "b", "c", "d"]:
            joined_norm = re.sub(
                rf"\(?\s*{ch}\s*\)",
                f"###OPT_{ch.lower()}###",
                joined_norm,
                flags=re.IGNORECASE,
            )

        # Split into [stem, a, b, c, d, ...]
        parts = re.split(r"###OPT_[a-d]###", joined_norm)
        if len(parts) < 5:
            # Not a proper 4-option block, skip
            continue

        # ----- Clean helper -----
        def clean_text(s: str) -> str:
            # Remove stray '(' at edges, extra spaces, and empty lines
            return "\n".join(
                line.strip().lstrip("(").rstrip("(").strip()
                for line in s.splitlines()
                if line.strip()
            ).strip()

        # Question stem: remove leading "Q<number>." if present
        stem_raw = parts[0]
        m_q = re.match(r"Q\d+\.\s*(.*)", stem_raw, flags=re.DOTALL)
        stem = clean_text(m_q.group(1) if m_q else stem_raw)

        a = clean_text(parts[1])
        b = clean_text(parts[2])
        c = clean_text(parts[3])
        d = clean_text(parts[4])

        rows.append(
            {
                "topic": topic,
                "question": stem,
                "option_a": a,
                "option_b": b,
                "option_c": c,
                "option_d": d,
                "correct_answer": ans.lower(),
            }
        )

    return pd.DataFrame(rows)





import os

if __name__ == "__main__":
    pdf_folder = "data/raw/pdf"
    output_folder = "data/raw/csv"

    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(pdf_folder):
        if not file.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(pdf_folder, file)
        csv_path = os.path.join(
            output_folder,
            file.replace(".pdf", ".csv")
        )

        print(f"Processing: {pdf_path}")

        text = extract_text(pdf_path)

        filename_no_ext = os.path.splitext(file)[0]
        topic = filename_no_ext.replace("_", " ").title()

        df = parse_mcqs_with_year(text, topic=topic)

        df = df[
            [
                "topic",
                "question",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_answer",
            ]
        ]

        # 5) Save CSV
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        print(f"Saved → {csv_path} | Rows: {len(df)}\n")
