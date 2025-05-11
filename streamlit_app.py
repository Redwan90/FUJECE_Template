import streamlit as st
import re
import os
from docx import Document
from PyPDF2 import PdfReader
import io

# --- Constants for FUJECE Template --- (Extracted from pasted_content.txt)
FUJECE_ABSTRACT_MIN_WORDS = 100
FUJECE_ABSTRACT_MAX_WORDS = 250
FUJECE_KEYWORDS_MIN_COUNT = 3
FUJECE_KEYWORDS_MAX_COUNT = 6
FUJECE_SECTIONS_ORDERED = [
    "Abstract",
    "Keywords",
    "Introduction",
    "Results", 
    "Acknowledgements", 
    "Author Contribution Statement",
    "Ethics Committee Approval and Conflict of Interest"
]

# --- Helper Functions for Parsing and Checking ---

def extract_text_from_docx(file_stream):
    """Extracts text from a .docx file stream."""
    try:
        document = Document(file_stream)
        full_text = []
        for para in document.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        st.error(f"Error reading DOCX file: {e}")
        return None

def extract_text_from_pdf(file_stream):
    """Extracts text from a .pdf file stream."""
    try:
        reader = PdfReader(file_stream)
        full_text = []
        for page in reader.pages:
            full_text.append(page.extract_text() or "") # Ensure None is handled
        return "\n".join(full_text)
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None

def extract_text_from_uploaded_file(uploaded_file):
    """Reads and returns text content from an uploaded file (txt, md, docx, pdf)."""
    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_stream = io.BytesIO(uploaded_file.getvalue())
        try:
            if file_name.lower().endswith(".txt") or file_name.lower().endswith(".md"):
                return file_stream.getvalue().decode("utf-8")
            elif file_name.lower().endswith(".docx"):
                return extract_text_from_docx(file_stream)
            elif file_name.lower().endswith(".pdf"):
                return extract_text_from_pdf(file_stream)
            else:
                st.error(f"Unsupported file type: {file_name}. Please upload .txt, .md, .docx, or .pdf")
                return None
        except Exception as e:
            st.error(f"Error reading file 	'{file_name}	': {e}")
            return None
    return None

def check_abstract_word_count(article_text, min_words, max_words):
    """Checks the word count of the abstract section."""
    if not article_text: return "FAIL: Article text is empty or could not be read."
    abstract_match = re.search(r"Abstract\s*(.*?)(Keywords|1\.\s*Introduction|\n\s*\n\s*\n)", article_text, re.IGNORECASE | re.DOTALL)
    if abstract_match:
        abstract_content = abstract_match.group(1).strip()
        word_count = len(abstract_content.split())
        if min_words <= word_count <= max_words:
            return f"PASS: Abstract word count ({word_count}) is within the range {min_words}-{max_words}."
        else:
            return f"FAIL: Abstract word count ({word_count}) is outside the range {min_words}-{max_words}. Abstract content found: 	'{abstract_content[:100]}...	'"
    return "FAIL: Abstract section not clearly identified or missing."

def check_keywords_count(article_text, min_count, max_count):
    """Checks the number of keywords."""
    if not article_text: return "FAIL: Article text is empty or could not be read."
    keywords_match = re.search(r"Keywords:\s*(.*?)(1\.\s*Introduction|\n\s*\n)", article_text, re.IGNORECASE | re.DOTALL)
    if keywords_match:
        keywords_content = keywords_match.group(1).strip()
        keywords_list = [k.strip() for k in re.split(r"[,;\n]+", keywords_content) if k.strip()]
        keyword_count = len(keywords_list)
        if min_count <= keyword_count <= max_count:
            return f"PASS: Number of keywords ({keyword_count}) is within the range {min_count}-{max_count}. Keywords: {keywords_list}"
        else:
            return f"FAIL: Number of keywords ({keyword_count}) is outside the range {min_count}-{max_count}. Keywords: {keywords_list}"
    return "FAIL: Keywords section not clearly identified or missing."

def check_section_presence(article_text, sections_to_check):
    """Checks for the presence of specified sections."""
    if not article_text: return "FAIL: Article text is empty or could not be read."
    results = []
    missing_sections = []
    for section_name in sections_to_check:
        if re.search(r"(?:\d+\.\s*)?" + re.escape(section_name), article_text, re.IGNORECASE):
            results.append(f"PASS: Section 	'{section_name}	' found.")
        else:
            results.append(f"FAIL: Section 	'{section_name}	' not found.")
            missing_sections.append(section_name)
    if missing_sections:
        return "\n".join(results) + f"\n\nSummary: Missing sections: {", ".join(missing_sections)}"
    return "\n".join(results) + "\n\nSummary: All essential sections appear to be present."

# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("Firat University Journal (FUJECE) Article Checker")

st.header("Upload Article")
# Updated file types
uploaded_article_file = st.file_uploader("Upload your article (.txt, .md, .docx, .pdf)", type=["txt", "md", "docx", "pdf"])

# Determine the base directory of the script for robust path handling
# This is important for Streamlit sharing or other deployment scenarios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to the bundled template guidelines
# Assuming 'app_data' is a subdirectory in the same directory as streamlit_app.py
# For local testing, this path needs to be relative to where streamlit_app.py is.
# For deployment, this structure (app_data/fujece_guidelines.txt alongside streamlit_app.py) needs to be maintained.
template_file_path = os.path.join(BASE_DIR, "app_data", "fujece_guidelines.txt")

# For local development, if BASE_DIR is /home/ubuntu, this will be /home/ubuntu/app_data/fujece_guidelines.txt
# If the script is in /home/ubuntu/fujece_checker_app, it will be /home/ubuntu/fujece_checker_app/app_data/fujece_guidelines.txt
# We created /home/ubuntu/fujece_checker_app/app_data/fujece_guidelines.txt earlier.
# So, the streamlit_app.py should be in /home/ubuntu/fujece_checker_app/

fujece_template_guidelines = None
try:
    with open(template_file_path, "r", encoding="utf-8") as f:
        fujece_template_guidelines = f.read()
    st.sidebar.success("FUJECE Template Guidelines loaded successfully.")
except FileNotFoundError:
    st.sidebar.error(f"Error: Template file not found at expected location: {template_file_path}. Please ensure 'fujece_guidelines.txt' is in an 'app_data' subdirectory next to the script.")
except Exception as e:
    st.sidebar.error(f"Error loading template guidelines: {e}")

if uploaded_article_file is not None and fujece_template_guidelines is not None:
    st.header("Comparison Results")
    article_text = extract_text_from_uploaded_file(uploaded_article_file)

    if article_text:
        results = []
        st.subheader("1. Abstract Check")
        abstract_check_result = check_abstract_word_count(article_text, FUJECE_ABSTRACT_MIN_WORDS, FUJECE_ABSTRACT_MAX_WORDS)
        st.markdown(abstract_check_result)
        results.append(f"Abstract Check: {abstract_check_result}")

        st.subheader("2. Keywords Check")
        keywords_check_result = check_keywords_count(article_text, FUJECE_KEYWORDS_MIN_COUNT, FUJECE_KEYWORDS_MAX_COUNT)
        st.markdown(keywords_check_result)
        results.append(f"Keywords Check: {keywords_check_result}")

        st.subheader("3. Section Presence Check")
        sections_to_check_from_template = FUJECE_SECTIONS_ORDERED
        section_presence_result = check_section_presence(article_text, sections_to_check_from_template)
        st.text(section_presence_result)
        results.append(f"Section Presence Check: {section_presence_result}")
        
        st.subheader("4. Other Formatting Checks (Conceptual - Not Implemented)")
        st.info("Detailed formatting checks (font, margins, heading styles, citation style, etc.) require more advanced parsing of rich text formats (DOCX/PDF) and are not fully implemented in this version. The template mentions specific fonts (Times New Roman), sizes (10pt, 11pt, 12pt), margins, and single-line spacing.")

        st.download_button(
            label="Download Full Report",
            data="\n".join(results),
            file_name="article_compliance_report.txt",
            mime="text/plain"
        )
    else:
        st.warning("Could not extract text from the uploaded article. Please ensure it is a valid .txt, .md, .docx, or .pdf file and not corrupted or password-protected (for PDFs).")
elif uploaded_article_file is not None and fujece_template_guidelines is None:
    st.error("Article uploaded, but the FUJECE template guidelines could not be loaded. Please check the application setup.")
else:
    st.info("Please upload an article file to begin the checks. The FUJECE template guidelines should be loaded automatically if correctly set up.")

st.sidebar.header("About")
st.sidebar.info(
    "This tool performs a basic comparison of an uploaded article "
    "against the Firat University Journal of Experimental and Computational Engineering (FUJECE) template guidelines. "
    "It checks for abstract word count, keyword count, and presence of key sections. "
    "It supports .txt, .md, .docx, and .pdf article uploads."
    "More advanced checks (e.g., detailed formatting) are conceptual in this version."
)

