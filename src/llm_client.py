from typing import List, Optional
import google.generativeai as genai

from .config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)

_model = genai.GenerativeModel(GEMINI_MODEL)


def summarize_text_chunks(
    chunks: List[str],
    system_instruction: str,
    *,
    filename: Optional[str] = None,
    metadata_text: Optional[str] = None,
) -> str:
    """
    Join chunks and get one summary, with strong anti-hallucination rules.
    """

    joined = "\n\n".join(chunks)

    file_info = ""
    if filename:
        file_info += f"File name: {filename}\n"
    if metadata_text:
        file_info += f"{metadata_text}\n"

    prompt = (
        f"{system_instruction}\n\n"
        "Rules:\n"
        "- Only describe behavior that is clearly supported by the provided content.\n"
        "- If something is unclear or missing, explicitly say it is not clear from the code.\n"
        "- Do NOT invent APIs, functions, or use cases that are not visible.\n"
        "- Do NOT assume specific frameworks, libraries, or technologies if they are not present.\n\n"
        f"{file_info}"
        "Here is the content:\n\n"
        f"{joined}\n\n"
        "Now provide a concise, factual summary."
    )

    response = _model.generate_content(prompt)
    # In current SDK, response.text is the default text field. [web:30][web:31][web:41][web:44]
    return response.text
