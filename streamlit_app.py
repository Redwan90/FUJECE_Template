import streamlit as st
import re

# --- Constants for FUJECE Template --- (Extracted from pasted_content.txt)
FUJECE_ABSTRACT_MIN_WORDS = 100
FUJECE_ABSTRACT_MAX_WORDS = 250
FUJECE_KEYWORDS_MIN_COUNT = 3
FUJECE_KEYWORDS_MAX_COUNT = 6
FUJECE_SECTIONS_ORDERED = [
    "Abstract",
    "Keywords",
    "Introduction",
    # "Page Layout and Style", # This is a guideline section, not an article section
    "Results", # Or other main content sections like Methods, Discussion etc.
    "Acknowledgements", # Optional
    "Author Contribution Statement",
    "Ethics Committee Approval and Conflict of Interest"
]

# --- Helper Functions for Parsing and Checking ---

def parse_template_rules(template_content):
    """Placeholder for parsing rules from a more structured template if needed."""
    # For now, using predefined constants
    rules = {
        "abstract_word_count": (FUJECE_ABSTRACT_MIN_WORDS, FUJECE_ABSTRACT_MAX_WORDS),
        "keywords_count": (FUJECE_KEYWORDS_MIN_COUNT, FUJECE_KEYWORDS_MAX_COUNT),
        "sections": FUJECE_SECTIONS_ORDERED,
        # Add more rules as parsing logic develops
        "font_main_text": ("Times New Roman", 11),
        "page_margins": {"top": 30, "left": 15, "right": 15, "bottom": 25}, # in mm
        "line_spacing_main_text": "single",
        "title_font_size": 12,
        "headings_font_size": 12,
    }
    return rules

def extract_text_from_uploaded_file(uploaded_file):
    """Reads and returns text content from an uploaded file."""
    if uploaded_file is not None:
        try:
            # To read as text, decode bytes to string
            return uploaded_file.getvalue().decode("utf-8")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None
    return None

def check_abstract_word_count(article_text, min_words, max_words):
    """Checks the word count of the abstract section."""
    # A simple regex to find abstract, case-insensitive, until the next common section or many newlines
    abstract_match = re.search(r"Abstract\s*(.*?)(Keywords|1\.\s*Introduction|\n\s*\n\s*\n)", article_text, re.IGNORECASE | re.DOTALL)
    if abstract_match:
        abstract_content = abstract_match.group(1).strip()
        word_count = len(abstract_content.split())
        if min_words <= word_count <= max_words:
            return f"PASS: Abstract word count ({word_count}) is within the range {min_words}-{max_words}."
        else:
            return f"FAIL: Abstract word count ({word_count}) is outside the range {min_words}-{max_words}. Abstract content found: '{abstract_content[:100]}...'"
    return "FAIL: Abstract section not clearly identified or missing."

def check_keywords_count(article_text, min_count, max_count):
    """Checks the number of keywords."""
    keywords_match = re.search(r"Keywords:\s*(.*?)(1\.\s*Introduction|\n\s*\n)", article_text, re.IGNORECASE | re.DOTALL)
    if keywords_match:
        keywords_content = keywords_match.group(1).strip()
        # Keywords are often comma-separated or on new lines
        keywords_list = [k.strip() for k in re.split(r"[,;\n]+", keywords_content) if k.strip()]
        keyword_count = len(keywords_list)
        if min_count <= keyword_count <= max_count:
            return f"PASS: Number of keywords ({keyword_count}) is within the range {min_count}-{max_count}. Keywords: {keywords_list}"
        else:
            return f"FAIL: Number of keywords ({keyword_count}) is outside the range {min_count}-{max_count}. Keywords: {keywords_list}"
    return "FAIL: Keywords section not clearly identified or missing."

def check_section_presence(article_text, sections_to_check):
    """Checks for the presence of specified sections."""
    results = []
    missing_sections = []
    for section_name in sections_to_check:
        # Simple check for section name (case-insensitive, allows for numbering like "1. Introduction")
        # This regex looks for the section name, possibly preceded by a number and a dot, and followed by a newline or space.
        if re.search(r"(?:\d+\.\s*)?" + re.escape(section_name), article_text, re.IGNORECASE):
            results.append(f"PASS: Section 	'{section_name}	' found.")
        else:
            results.append(f"FAIL: Section 	'{section_name}	' not found.")
            missing_sections.append(section_name)
    if missing_sections:
        return "\n".join(results) + f"\n\nSummary: Missing sections: {', '.join(missing_sections)}"
    return "\n".join(results) + "\n\nSummary: All essential sections appear to be present."


# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("Firat University Journal (FUJECE) Article Checker")

st.header("Upload Article")
uploaded_article_file = st.file_uploader("Upload your article (e.g., .txt, .docx - .txt preferred for now)", type=["txt", "md"])

# Load template content (assuming it's available locally or fetched)
# For this example, we'll read the pasted_content.txt provided by the user
template_file_path = "/home/ubuntu/upload/pasted_content.txt"
try:
    with open(template_file_path, "r", encoding="utf-8") as f:
        fujece_template_guidelines = f.read()
    st.sidebar.success("FUJECE Template Guidelines loaded.")
    # st.sidebar.text_area("Template Guidelines (First 1000 chars):", fujece_template_guidelines[:1000], height=200)
except FileNotFoundError:
    st.sidebar.error(f"Error: Template file not found at {template_file_path}")
    fujece_template_guidelines = None
except Exception as e:
    st.sidebar.error(f"Error loading template guidelines: {e}")
    fujece_template_guidelines = None

if uploaded_article_file is not None and fujece_template_guidelines is not None:
    st.header("Comparison Results")
    article_text = extract_text_from_uploaded_file(uploaded_article_file)

    if article_text:
        # st.subheader("Uploaded Article Content (First 1000 chars):")
        # st.text_area("", article_text[:1000], height=150)

        # Perform checks
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
        # More robust section identification would be needed for a production tool
        # This is a simplified check based on the template's main sections.
        sections_to_check_from_template = [
            "Abstract", "Keywords", "Introduction", "Results", 
            # "Discussion", "Conclusion" # Add if these are explicitly required and distinct
            "Acknowledgements", "Author Contribution Statement", 
            "Ethics Committee Approval and Conflict of Interest"
        ]
        section_presence_result = check_section_presence(article_text, sections_to_check_from_template)
        st.text(section_presence_result)
        results.append(f"Section Presence Check: {section_presence_result}")
        
        st.subheader("4. Other Formatting Checks (Conceptual - Not Implemented)")
        st.info("Detailed formatting checks (font, margins, heading styles, citation style, etc.) require more advanced parsing and are not fully implemented in this basic version. The template mentions specific fonts (Times New Roman), sizes (10pt, 11pt, 12pt), margins, and single-line spacing.")

        # Provide a summary or download option
        st.download_button(
            label="Download Full Report",
            data="\n".join(results),
            file_name="article_compliance_report.txt",
            mime="text/plain"
        )

else:
    st.info("Please upload an article file to begin the checks. The FUJECE template guidelines should be loaded automatically.")


st.sidebar.header("About")
st.sidebar.info(
    "This tool performs a basic comparison of an uploaded article "
    "against the Firat University Journal of Experimental and Computational Engineering (FUJECE) template guidelines. "
    "It checks for abstract word count, keyword count, and presence of key sections. "
    "More advanced checks (e.g., detailed formatting) are conceptual in this version."
)

