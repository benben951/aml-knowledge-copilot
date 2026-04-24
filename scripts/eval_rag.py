"""RAG Evaluation Script

Evaluate the RAG system's performance using the AML eval dataset.
Measures retrieval accuracy, answer quality, and citation correctness.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.config import settings
from backend.app.infra.vector.qdrant_client import get_qdrant_client
from backend.app.services.retrieval.retrieval_service import RetrievalService
from backend.app.services.answer.answer_service import AnswerService
from backend.app.infra.llm.llm_client import get_llm_client


def load_eval_dataset(dataset_path: str = None) -> List[Dict]:
    """Load evaluation dataset from JSONL file."""
    if dataset_path is None:
        dataset_path = Path(__file__).parent.parent / "data" / "eval" / "aml_eval.jsonl"
    else:
        dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        print(f"❌ Eval dataset not found: {dataset_path}")
        print("Run `python scripts/ingest_demo_data.py` first to set up the knowledge base.")
        return []

    questions = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


def compute_keyword_recall(expected_answer: str, actual_answer: str) -> float:
    """Simple keyword-based recall metric."""
    expected_words = set(expected_answer.replace("，", " ").replace("、", " ").replace("。", " ").split())
    actual_words = set(actual_answer.replace("，", " ").replace("、", " ").replace("。", " ").split())
    expected_words = {w for w in expected_words if len(w) > 1}
    actual_words = {w for w in actual_words if len(w) > 1}

    if not expected_words:
        return 0.0

    overlap = expected_words & actual_words
    return len(overlap) / len(expected_words)


async def evaluate_single(
    question_data: Dict,
    retrieval_service: RetrievalService,
    answer_service: AnswerService,
) -> Dict:
    """Evaluate a single question."""
    question = question_data["question"]
    expected = question_data.get("expected_answer", "")

    # Step 1: Retrieve
    try:
        search_results = retrieval_service.search(
            query=question,
            top_k=settings.TOP_K_RESULTS,
        )
        retrieval_score = max((r.score for r in search_results), default=0.0)
        sources_found = len(search_results)
    except Exception as e:
        search_results = []
        retrieval_score = 0.0
        sources_found = 0

    # Step 2: Generate answer
    try:
        answer_result = await answer_service.answer(
            question=question,
            search_results=search_results,
        )
        actual_answer = answer_result.answer
        confidence = answer_result.confidence
        needs_review = answer_result.needs_review
    except Exception as e:
        actual_answer = f"Error: {str(e)}"
        confidence = 0.0
        needs_review = True

    # Step 3: Compute metrics
    keyword_recall = compute_keyword_recall(expected, actual_answer)

    return {
        "question": question,
        "category": question_data.get("category", "unknown"),
        "difficulty": question_data.get("difficulty", "unknown"),
        "retrieval_score": round(retrieval_score, 3),
        "sources_found": sources_found,
        "keyword_recall": round(keyword_recall, 3),
        "confidence": round(confidence, 3),
        "needs_review": needs_review,
        "answer_preview": actual_answer[:200] + "..." if len(actual_answer) > 200 else actual_answer,
    }


async def run_evaluation(dataset_path: str = None):
    """Run full evaluation."""
    print("=" * 60)
    print("🏦 AML/DD Knowledge Copilot - RAG Evaluation")
    print("=" * 60)

    # Load dataset
    questions = load_eval_dataset(dataset_path)
    if not questions:
        return

    print(f"\n📝 Loaded {len(questions)} evaluation questions")

    # Initialize services
    qdrant = get_qdrant_client()
    llm = get_llm_client()
    retrieval_service = RetrievalService(qdrant_client=qdrant)
    answer_service = AnswerService(llm_client=llm)

    # Evaluate each question
    results = []
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {q['question'][:50]}...")
        result = await evaluate_single(q, retrieval_service, answer_service)
        results.append(result)
        print(f"  📊 Retrieval: {result['retrieval_score']:.3f} | "
              f"Recall: {result['keyword_recall']:.3f} | "
              f"Confidence: {result['confidence']:.3f}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 Evaluation Summary")
    print("=" * 60)

    avg_retrieval = sum(r["retrieval_score"] for r in results) / len(results)
    avg_recall = sum(r["keyword_recall"] for r in results) / len(results)
    avg_confidence = sum(r["confidence"] for r in results) / len(results)
    review_count = sum(1 for r in results if r["needs_review"])

    print(f"\n📈 Overall Metrics:")
    print(f"  Avg Retrieval Score:  {avg_retrieval:.3f}")
    print(f"  Avg Keyword Recall:   {avg_recall:.3f}")
    print(f"  Avg Confidence:       {avg_confidence:.3f}")
    print(f"  Needs Review:         {review_count}/{len(results)}")

    # By category
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    print(f"\n📋 By Category:")
    for cat, cat_results in sorted(categories.items()):
        cat_recall = sum(r["keyword_recall"] for r in cat_results) / len(cat_results)
        cat_retrieval = sum(r["retrieval_score"] for r in cat_results) / len(cat_results)
        print(f"  {cat}: Recall={cat_recall:.3f}, Retrieval={cat_retrieval:.3f} ({len(cat_results)} questions)")

    # By difficulty
    difficulties = {}
    for r in results:
        diff = r["difficulty"]
        if diff not in difficulties:
            difficulties[diff] = []
        difficulties[diff].append(r)

    print(f"\n🎯 By Difficulty:")
    for diff, diff_results in sorted(difficulties.items()):
        diff_recall = sum(r["keyword_recall"] for r in diff_results) / len(diff_results)
        print(f"  {diff}: Recall={diff_recall:.3f} ({len(diff_results)} questions)")

    return results


def main():
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(run_evaluation(dataset_path))


if __name__ == "__main__":
    main()