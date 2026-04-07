"""
Ingest Demo Data Script

This script loads sample AML/DD documents into the knowledge base.
Useful for testing and demonstration purposes.
"""

import os
from pathlib import Path

# Sample AML/DD knowledge base (for demonstration)
SAMPLE_QA_DATA = [
    {
        "question": "什么是可疑交易报告？",
        "answer": "可疑交易报告（STR）是金融机构发现或怀疑交易涉及洗钱、恐怖融资等违法犯罪活动时，向金融情报机构提交的报告。",
        "source": "反洗钱法规汇编.pdf",
        "category": "基础概念"
    },
    {
        "question": "客户尽职调查包括哪些内容？",
        "answer": "客户尽职调查（CDD）主要包括：1) 识别客户身份；2) 了解交易目的和性质；3) 了解受益所有人信息；4) 持续监控交易关系。",
        "source": "尽职调查指引.pdf",
        "category": "尽职调查"
    },
    {
        "question": "高风险客户的识别标准是什么？",
        "answer": "高风险客户包括：1) 来自高风险国家/地区的客户；2) 政治公众人物（PEP）；3) 现金密集型行业客户；4) 复杂所有权结构的客户。",
        "source": "客户风险分类管理办法.pdf",
        "category": "风险评估"
    },
    {
        "question": "什么是受益所有人？",
        "answer": "受益所有人是指最终拥有或控制客户的自然人，包括：1) 直接或间接拥有25%以上权益的自然人；2) 对客户有实际控制权的自然人。",
        "source": "尽职调查指引.pdf",
        "category": "尽职调查"
    },
    {
        "question": "可疑交易报告的提交时限是多久？",
        "answer": "金融机构应当在大额和可疑交易发生后5个工作日内提交报告，最迟不超过10个工作日。",
        "source": "反洗钱法规汇编.pdf",
        "category": "报告要求"
    }
]


def create_sample_documents():
    """Create sample document files for testing."""
    samples_dir = Path(__file__).parent.parent / "data" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample text files
    for qa in SAMPLE_QA_DATA:
        filename = qa["source"].replace(".pdf", ".txt")
        filepath = samples_dir / filename
        
        content = f"""
文档名称：{qa['source']}
分类：{qa['category']}

问题：{qa['question']}

答案：{qa['answer']}

---
此文档用于演示目的，内容基于公开法规整理。
"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Created: {filepath}")
    
    print(f"\n✅ Created {len(SAMPLE_QA_DATA)} sample documents in {samples_dir}")


def ingest_to_qdrant():
    """Ingest sample documents into Qdrant."""
    # TODO: Implement actual ingestion
    print("🚧 Ingestion to Qdrant not yet implemented")
    print("This will:")
    print("1. Load documents from data/samples/")
    print("2. Parse and chunk text")
    print("3. Generate embeddings")
    print("4. Store in Qdrant vector database")


def main():
    """Main entry point."""
    print("=" * 50)
    print("AML/DD Knowledge Copilot - Demo Data Ingestion")
    print("=" * 50)
    
    print("\n📝 Creating sample documents...")
    create_sample_documents()
    
    print("\n📚 Ingesting to vector database...")
    ingest_to_qdrant()
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()