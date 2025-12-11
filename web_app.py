import json
import os
import streamlit as st
from pathlib import Path
from streamlit_agraph import agraph, Node, Edge, Config

from src.summarizer import summarize_project

def main():
    st.set_page_config(
        page_title="Codebase Summarizer", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🚀 Codebase Workflow Summarizer")
    st.markdown("**AI-powered architecture understanding & workflow visualization**")

    # Sidebar
    st.sidebar.header("📁 Project Configuration")
    
    default_path = str(Path(".").resolve())
    project_path = st.sidebar.text_input(
        "Project path",
        value=default_path,
        help="Local folder containing your codebase",
    )
    
    max_files = st.sidebar.slider("Max files to analyze", 10, 100, 50)
    run_button = st.sidebar.button("🔍 Analyze Codebase", type="primary")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Project Overview", "📁 Folder Structure", "🔗 Workflow Graph"])

    if run_button and project_path:
        root = Path(project_path).resolve()
        if not root.exists():
            st.error(f"❌ Path does not exist: {root}")
            st.stop()

        with st.spinner(f"Analyzing {len(os.listdir(root))} files..."):
            result = summarize_project(str(root))

        # Auto-save
        out_path = root / "code_summary.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        st.sidebar.success(f"✅ Saved to: `{out_path}`")

        # TAB 1: Project Overview
        with tab1:
            st.subheader("🎯 Project Summary")
            st.markdown(result["project_summary"])
            
            st.subheader("🚪 Detected Entry Points")
            workflow = result["workflow"]
            if workflow["entrypoints"]:
                for ep in workflow["entrypoints"]:
                    st.success(f"• `{ep}`")
            else:
                st.warning("No obvious entry points detected")
            
            st.subheader("⭐ Top Modules (by importance)")
            for path, score in workflow["top_modules"]:
                st.info(f"**{os.path.basename(path)}** ({score:.1%}) - {path}")

        # TAB 2: Folder/File Structure (existing)
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📁 Folders")
                for folder, summary in sorted(result["folders"].items()):
                    label = folder or "Root"
                    with st.expander(f"📁 {label}"):
                        st.markdown(summary)
            
            with col2:
                st.subheader("📄 Files")
                for path, summary in sorted(result["files"].items()):
                    with st.expander(f"📄 {os.path.basename(path)}"):
                        st.markdown(summary)

        # TAB 3: Workflow Graph (NEW Day 3!)
        with tab3:
            st.subheader("🔗 Workflow Visualization")
            
            if workflow["graph"]["nodes"]:
                # Prepare graph data for agraph
                nodes = []
                edges = []
                
                for node_data in workflow["graph"]["nodes"]:
                    # Color-code important nodes
                    path = node_data["id"]
                    importance = workflow["important_modules"].get(path, 0)
                    
                    color = (
                        "#ff6b6b" if path in workflow["entrypoints"] else  # red for entrypoints
                        "#4ecdc4" if importance > 0.7 else             # teal for important
                        "#95e1d3" if importance > 0.4 else             # light teal
                        "#f7dc6f"                                     # yellow for others
                    )
                    
                    nodes.append(Node(
                        id=path,
                        label=os.path.basename(path),
                        size=importance * 20 + 10,
                        color=color
                    ))
                
                for edge_data in workflow["graph"]["edges"][:20]:  # limit edges
                    edges.append(Edge(source=edge_data["from"], target=edge_data["to"]))
                
                # Config for nice visualization
                config = Config(
                    width=800,
                    height=500,
                    directed=True,
                    physics=True,
                    hierarchical=False
                )
                
                # Render interactive graph
                return_value = agraph(nodes=nodes, edges=edges, config=config)
                
                st.caption("*Interactive graph: drag nodes, zoom, pan. Red=entrypoints, size=importance*")
            else:
                st.warning("No workflow graph data available")

if __name__ == "__main__":
    main()
