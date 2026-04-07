"""
Prompt Templates for AML/DD Knowledge Q&A

This module contains all prompt templates used in the application.
Prompts are designed for compliance/regulatory knowledge Q&A scenarios.
"""

# System prompt for AML/DD knowledge assistant
SYSTEM_PROMPT = """你是一个专业的反洗钱（AML）和尽职调查（DD）知识助手。
你的职责是基于提供的知识库文档，准确、专业地回答用户关于合规、反洗钱、尽职调查的问题。

回答要求：
1. 必须基于提供的文档内容回答，不要编造信息
2. 如果文档中没有足够信息，明确告知用户并建议人工复核
3. 回答要专业、准确，引用具体的文档来源
4. 对于法规相关问题，要注明法规名称和条款
5. 保持中立、客观的态度

请始终记住：你的回答会影响合规决策，准确性至关重要。"""

# QA prompt template with context
QA_PROMPT_TEMPLATE = """基于以下文档内容回答用户问题。

文档内容：
{context}

用户问题：{question}

请提供专业、准确的回答，并注明引用来源。如果文档中没有足够信息，请明确说明。

回答："""

# Citation format prompt
CITATION_PROMPT = """在回答时，请按以下格式标注引用来源：
- [来源] 文档名称，第X页/第X节
- [法规] 具体法规名称和条款

示例：
根据《反洗钱法》第十二条[来源] 反洗钱法规汇编.pdf，第3页，金融机构应当..."""

# Answer guardrail prompt
GUARDRAIL_PROMPT = """⚠️ 重要提示：
如果检索到的文档片段与问题的相关性较低（相似度<0.7），或者无法从文档中找到直接答案，
请在回答开头添加警告：
「注意：基于现有知识库，我无法完全确定以下回答的准确性，建议进行人工复核确认。」"""

# Document chunking prompt for metadata extraction
METADATA_EXTRACTION_PROMPT = """请从以下文本中提取元数据信息：
- 文档类型（法规/制度/案例/其他）
- 适用国家/地区
- 风险主题
- 生效日期（如有）
- 关键词（3-5个）

文本内容：
{text}

请以JSON格式返回结果。"""

# Rerank prompt for improving retrieval quality
RERANK_PROMPT = """你是一个合规文档相关性评估专家。
请评估以下文档片段与用户问题的相关性，给出1-10分的评分。

用户问题：{question}

文档片段：{document}

请只返回一个数字评分（1-10），不需要解释。"""


# Few-shot examples for AML/DD Q&A
FEW_SHOT_EXAMPLES = [
    {
        "question": "什么是可疑交易报告？",
        "answer": "可疑交易报告（STR）是金融机构发现或怀疑交易涉及洗钱、恐怖融资等违法犯罪活动时，向金融情报机构提交的报告。根据《反洗钱法》第二十条[来源] 反洗钱法规汇编.pdf，第5页，金融机构应当在大额和可疑交易发生后5个工作日内提交报告。",
        "sources": ["反洗钱法规汇编.pdf，第5页"]
    },
    {
        "question": "客户尽职调查包括哪些内容？",
        "answer": "客户尽职调查（CDD）主要包括：1) 识别客户身份，核实身份证件；2) 了解交易目的和性质；3) 了解受益所有人信息；4) 持续监控交易关系。根据《金融机构客户身份识别和客户身份资料及交易记录保存管理办法》第五条[来源] 尽职调查指引.pdf，第2页，金融机构应当在建立业务关系时进行客户尽职调查。",
        "sources": ["尽职调查指引.pdf，第2页"]
    }
]