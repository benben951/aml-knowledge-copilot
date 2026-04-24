"""Ingest Demo Data Script

Load sample AML/DD documents into the knowledge base for testing.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.config import settings
from backend.app.services.document.document_service import DocumentService



SAMPLE_DOCUMENTS = {
    "反洗钱法规汇编.txt": """
反洗钱法规汇编

第十二条 金融机构尽职调查义务
金融机构应对客户进行尽职调查，了解客户身份和业务性质。在建立业务关系时，应当识别并核实客户身份，了解受益所有人信息。

第十三条 大额交易报告
金融机构应当在大额和可疑交易发生后5个工作日内提交报告。大额交易标准：
1. 单笔或当日累计现金收付人民币5万元以上
2. 非自然人客户银行账户之间单笔或累计转账人民币200万元以上
3. 自然人客户银行账户之间单笔或累计转账人民币50万元以上

第十四条 可疑交易报告（STR）
可疑交易报告是金融机构发现或怀疑交易涉及洗钱、恐怖融资等违法犯罪活动时，向金融情报机构提交的报告。提交STR后不得通知客户（tipping-off禁止）。
""",
    "尽职调查指引.txt": """
客户尽职调查指引

一、标准客户尽职调查（CDD）
1. 识别客户身份，核实身份证件
2. 了解交易目的和交易性质
3. 了解受益所有人信息
4. 持续监控交易关系

二、增强型尽职调查（EDD）
对高风险客户应执行EDD，包括：
1. 获取高级管理层批准
2. 核实资金来源和财富来源
3. 加强持续监控
4. 高风险情形：
   - 政治公众人物（PEP）及其关联人
   - 来自FATF高风险国家或地区
   - 现金密集型行业
   - 复杂所有权结构

三、受益所有人识别
受益所有人是指最终拥有或控制客户的自然人：
1. 直接或间接拥有超过25%股权或投票权的自然人
2. 通过其他方式对公司实施最终控制的自然人
3. 若无法识别上述人员，则识别担任高级管理职务的自然人
""",
    "客户风险分类管理办法.txt": """
客户风险分类管理办法

一、风险等级划分
高风险：PEP及关联人、来自FATF黑名单国家、现金密集型行业、复杂结构客户
中风险：一般企业客户、普通个人客户、来自FATF灰名单国家
低风险：政府机构、受监管金融机构、低风险国家上市公司

二、尽调措施
高风险客户：EDD、高级管理层审批、核实资金和财富来源、加强持续监控（至少每半年回顾）
中风险客户：标准CDD、身份识别和验证、了解交易目的和性质、年度回顾
低风险客户：简化CDD、减少定期回顾频率（可2-3年一次）

三、持续尽调要求
1. 交易监控：持续审查客户交易
2. 风险等级更新：定期或触发式更新
3. 文件更新：确保客户身份资料保持最新
4. 触发式回顾：重大交易、客户信息变更、负面新闻时立即重新尽调
""",
}


def main():
    print("=" * 50)
    print("AML/DD Knowledge Copilot - Demo Data Ingestion")
    print("=" * 50)

    # Initialize services (they create their own connections internally)
    doc_service = DocumentService()

    # Create sample files and ingest
    samples_dir = Path(__file__).parent.parent / "data" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    for filename, content in SAMPLE_DOCUMENTS.items():
        filepath = samples_dir / filename
        filepath.write_text(content.strip(), encoding="utf-8")
        print(f"\n📄 Processing: {filename}")

        try:
            result = doc_service.process_document(
                file_path=str(filepath),
                filename=filename,
                file_type="txt",
            )
            chunks_count = result.get("chunks_count", result.get("total_chunks", 0))
            print(f"  ✅ Chunks: {chunks_count}")
            total_chunks += chunks_count
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n{'=' * 50}")
    print(f"✅ Ingested {len(SAMPLE_DOCUMENTS)} documents, {total_chunks} total chunks")
    print(f"📁 Sample files saved to: {samples_dir}")


if __name__ == "__main__":
    main()