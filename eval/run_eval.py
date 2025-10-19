#!/usr/bin/env python3
"""
Evaluation harness for IFRS Q&A system.
Loads gold Q&A data and evaluates accuracy, groundedness, and abstention correctness.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import requests
import time

# Add the parent directory to the path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.agents.ifrs import answer_ifrs


class EvalRunner:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def load_gold_qa(self, fixtures_path: str) -> List[Dict[str, Any]]:
        """Load gold Q&A data from JSONL file."""
        gold_qa = []
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    gold_qa.append(json.loads(line.strip()))
        return gold_qa
    
    def score_answer(self, question_data: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single answer against gold standard."""
        scores = {
            'contains_gold': 0,
            'citations_match': 0,
            'abstain_correct': 0,
            'total_score': 0
        }
        
        # Check if answer contains any gold substrings
        if 'answer' in answer:
            answer_text = answer['answer'].lower()
            gold_contains = question_data.get('gold_answer_contains', [])
            for gold_substring in gold_contains:
                if gold_substring.lower() in answer_text:
                    scores['contains_gold'] = 1
                    break
        
        # Check if citations include any gold paragraphs
        if 'citations' in answer and answer['citations']:
            citations = answer['citations']
            gold_paragraphs = question_data.get('gold_paragraphs', [])
            for citation in citations:
                if 'paragraph' in citation:
                    if citation['paragraph'] in gold_paragraphs:
                        scores['citations_match'] = 1
                        break
        
        # Check abstention correctness (if expected to abstain)
        if question_data.get('expect_abstain', False):
            if answer.get('status') == 'ABSTAIN':
                scores['abstain_correct'] = 1
        
        # Calculate total score
        scores['total_score'] = scores['contains_gold'] + scores['citations_match'] + scores['abstain_correct']
        
        return scores
    
    def run_evaluation(self, fixtures_path: str) -> Dict[str, Any]:
        """Run evaluation on all gold Q&A data."""
        gold_qa = self.load_gold_qa(fixtures_path)
        
        print(f"Running evaluation on {len(gold_qa)} questions...")
        
        total_questions = len(gold_qa)
        total_contains_gold = 0
        total_citations_match = 0
        total_abstain_correct = 0
        total_score = 0
        
        for i, question_data in enumerate(gold_qa):
            print(f"Processing question {i+1}/{total_questions}: {question_data['question'][:50]}...")
            
            try:
                # Call the IFRS answer function
                answer = answer_ifrs(
                    question=question_data['question'],
                    topic=question_data.get('topic')
                )
                
                # Score the answer
                scores = self.score_answer(question_data, answer)
                
                # Update totals
                total_contains_gold += scores['contains_gold']
                total_citations_match += scores['citations_match']
                total_abstain_correct += scores['abstain_correct']
                total_score += scores['total_score']
                
                # Store result
                result = {
                    'question': question_data['question'],
                    'topic': question_data.get('topic'),
                    'answer': answer,
                    'scores': scores,
                    'gold_contains': question_data.get('gold_answer_contains', []),
                    'gold_paragraphs': question_data.get('gold_paragraphs', [])
                }
                self.results.append(result)
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing question {i+1}: {e}")
                continue
        
        # Calculate aggregate metrics
        metrics = {
            'total_questions': total_questions,
            'contains_gold_count': total_contains_gold,
            'citations_match_count': total_citations_match,
            'abstain_correct_count': total_abstain_correct,
            'total_score': total_score,
            'contains_gold_rate': total_contains_gold / total_questions if total_questions > 0 else 0,
            'citations_match_rate': total_citations_match / total_questions if total_questions > 0 else 0,
            'abstain_correct_rate': total_abstain_correct / total_questions if total_questions > 0 else 0,
            'overall_score': total_score / (total_questions * 3) if total_questions > 0 else 0
        }
        
        return metrics
    
    def print_results(self, metrics: Dict[str, Any]):
        """Print evaluation results in a formatted table."""
        print("\n" + "="*60)
        print("IFRS Q&A EVALUATION RESULTS")
        print("="*60)
        print(f"{'Metric':<30} {'Count':<10} {'Rate':<10}")
        print("-"*60)
        print(f"{'Total Questions':<30} {metrics['total_questions']:<10} {'100.0%':<10}")
        print(f"{'Contains Gold':<30} {metrics['contains_gold_count']:<10} {metrics['contains_gold_rate']*100:.1f}%")
        print(f"{'Citations Match':<30} {metrics['citations_match_count']:<10} {metrics['citations_match_rate']*100:.1f}%")
        print(f"{'Abstain Correct':<30} {metrics['abstain_correct_count']:<10} {metrics['abstain_correct_rate']*100:.1f}%")
        print("-"*60)
        print(f"{'Overall Score':<30} {metrics['total_score']:<10} {metrics['overall_score']*100:.1f}%")
        print("="*60)
    
    def save_report(self, metrics: Dict[str, Any], output_path: str = "eval_report.json"):
        """Save evaluation report to JSON file."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': metrics,
            'results': self.results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nEvaluation report saved to: {output_path}")


def main():
    """Main evaluation function."""
    # Get the path to the fixtures file
    fixtures_path = Path(__file__).parent / "fixtures" / "gold_qa.jsonl"
    
    if not fixtures_path.exists():
        print(f"Error: Fixtures file not found at {fixtures_path}")
        sys.exit(1)
    
    # Initialize evaluator
    evaluator = EvalRunner()
    
    # Run evaluation
    metrics = evaluator.run_evaluation(str(fixtures_path))
    
    # Print results
    evaluator.print_results(metrics)
    
    # Save report
    evaluator.save_report(metrics)
    
    # Exit with appropriate code
    if metrics['overall_score'] < 0.7:  # Less than 70% overall score
        print("\nWarning: Overall score below 70%")
        sys.exit(1)
    else:
        print("\nEvaluation completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
