"""
AML/DD Knowledge Copilot - Streamlit Frontend

A simple web interface for the AML/DD Knowledge Q&A system.
"""

import streamlit as st
import httpx
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Page configuration
st.set_page_config(
    page_title="AML Knowledge Copilot",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .confidence-high {
        color: green;
    }
    .confidence-low {
        color: orange;
    }
    .needs-review {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application."""
    # Header
    st.markdown('<h1 class="main-header">🏦 AML/DD Knowledge Copilot</h1>', unsafe_allow_html=True)
    st.markdown("**反洗钱/尽职调查知识问答系统**")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 文档管理")
        uploaded_file = st.file_uploader(
            "上传文档",
            type=["pdf", "docx", "txt"],
            help="支持 PDF、DOCX、TXT 格式"
        )
        
        if uploaded_file:
            if st.button("处理文档"):
                with st.spinner("处理中..."):
                    # TODO: Call API to upload document
                    st.success(f"文档 '{uploaded_file.name}' 已上传")
        
        st.divider()
        
        st.header("🔍 检索设置")
        top_k = st.slider("返回结果数", 1, 10, 5)
        min_score = st.slider("最小相似度", 0.0, 1.0, 0.7, 0.1)
        
        st.divider()
        
        st.header("📊 系统状态")
        if st.button("检查状态"):
            try:
                response = httpx.get(f"{API_BASE_URL}/health")
                if response.status_code == 200:
                    st.success("✅ 系统正常")
                else:
                    st.error("❌ 系统异常")
            except:
                st.error("❌ 无法连接后端服务")
    
    # Main content area
    tab1, tab2 = st.tabs(["💬 问答", "📚 文档库"])
    
    with tab1:
        st.header("提问")
        
        # Question input
        question = st.text_area(
            "输入您的问题",
            placeholder="例如：什么是可疑交易报告？客户尽职调查包括哪些内容？",
            height=100
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            ask_button = st.button("🔍 提问", type="primary")
        
        if ask_button and question:
            with st.spinner("正在检索并生成回答..."):
                # TODO: Call API to get answer
                # Placeholder response
                st.markdown("### 回答")
                st.markdown("""
                这是一个示例回答。实际的 RAG 功能正在开发中。
                
                根据相关法规，答案将包含具体的引用来源和文档参考。
                """)
                
                st.markdown("#### 📚 引用来源")
                st.info("暂无引用来源")
        
        # Example questions
        st.divider()
        st.markdown("#### 💡 示例问题")
        example_questions = [
            "什么是可疑交易报告？",
            "客户尽职调查包括哪些内容？",
            "高风险客户的识别标准是什么？",
            "如何进行受益所有人识别？"
        ]
        
        cols = st.columns(2)
        for i, eq in enumerate(example_questions):
            with cols[i % 2]:
                if st.button(eq, key=f"example_{i}"):
                    st.session_state.question = eq
    
    with tab2:
        st.header("已上传文档")
        
        # TODO: Fetch and display documents from API
        st.info("暂无已上传的文档")
        
        # Document list placeholder
        documents_data = [
            {"name": "反洗钱法规汇编.pdf", "chunks": 45, "status": "已处理"},
            {"name": "尽职调查指引.docx", "chunks": 23, "status": "已处理"},
        ]
        
        if documents_data:
            import pandas as pd
            df = pd.DataFrame(documents_data)
            st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
