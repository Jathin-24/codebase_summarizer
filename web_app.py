import json
from pathlib import Path

import streamlit as st  # streamlit 1.52.0 [web:70][web:72]

from src.summarizer import summarize_project


def main():
    st.set_page_config(page_title="Codebase Summarizer", layout="wide")

    st.title("Codebase Summarizer (Gemini)")

    st.sidebar.header("Project configuration")

    default_path = str(Path(".").resolve())
    project_path = st.sidebar.text_input(
        "Project path",
        value=default_path,
        help="Absolute or relative path to the codebase you want to summarize.",
    )

    run_button = st.sidebar.button("Run summarization")

    if run_button:
        root = Path(project_path).resolve()
        if not root.exists():
            st.error(f"Path does not exist: {root}")
            return

        with st.spinner(f"Summarizing project at {root} ..."):
            result = summarize_project(str(root))

        st.success("Summarization complete.")

        # Save to file next to the project by default (optional)
        out_path = root / "code_summary.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        st.info(f"Summary JSON written to: {out_path}")

        # Display project summary
        st.subheader("Project summary")
        st.markdown(result["project_summary"])

        # Two columns: folders and files
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Folders")
            folders = result.get("folders", {})
            if not folders:
                st.write("No folder summaries available.")
            else:
                for folder, summary in sorted(folders.items(), key=lambda x: x[0] or ""):
                    label = folder or "<root>"
                    with st.expander(f"📁 {label}", expanded=False):
                        st.markdown(summary)

        with col2:
            st.subheader("Files")
            files = result.get("files", {})
            if not files:
                st.write("No file summaries available.")
            else:
                for path, summary in sorted(files.items(), key=lambda x: x[0]):
                    with st.expander(f"📄 {path}", expanded=False):
                        st.markdown(summary)


if __name__ == "__main__":
    main()
