import sys
from typing import List, Tuple

def remove_commas_periods(text: str) -> str:
    return text.replace(',', '').replace('.', '')

def precision_recall_f1(prediction: str, ground_truth: str) -> Tuple[float, float, float]:
    pred_tokens = remove_commas_periods(prediction).lower().split()
    gt_tokens = remove_commas_periods(ground_truth).lower().split()
    
    common_tokens = set(pred_tokens) & set(gt_tokens)
    num_common_tokens = len(common_tokens)
    
    precision = num_common_tokens / len(pred_tokens) if pred_tokens else 0
    recall = num_common_tokens / len(gt_tokens) if gt_tokens else 0
    
    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
    
    return precision, recall, f1

def max_precision_recall_f1(prediction: str, ground_truths: List[str]) -> Tuple[float, float, float]:
    scores = [precision_recall_f1(prediction, gt) for gt in ground_truths]
    
    max_precision = max(score[0] for score in scores)
    max_recall = max(score[1] for score in scores)
    max_f1 = max(score[2] for score in scores)
    
    return max_precision, max_recall, max_f1

def evaluate(predictions_path: str, ground_truths_path: str) -> Tuple[float, float, float]:
    with open(predictions_path, 'r') as pred_file, open(ground_truths_path, 'r') as gt_file:
        predictions = pred_file.readlines()
        ground_truths = gt_file.readlines()
    
    assert len(predictions) == len(ground_truths), "Files must have the same number of lines"
    
    total_precision, total_recall, total_f1 = 0.0, 0.0, 0.0
    num_examples = len(predictions)
    
    for pred, gt_line in zip(predictions, ground_truths):
        prediction = pred.strip()
        gt_answers = [gt.strip() for gt in gt_line.split(';')] 
        max_precision, max_recall, max_f1 = max_precision_recall_f1(prediction, gt_answers)
        total_precision += max_precision
        total_recall += max_recall
        total_f1 += max_f1
    
    avg_precision = total_precision / num_examples
    avg_recall = total_recall / num_examples
    avg_f1 = total_f1 / num_examples
    
    return avg_precision, avg_recall, avg_f1

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <predictions_file> <ground_truths_file>")
        sys.exit(1)
    
    predictions_path = sys.argv[1]
    ground_truths_path = sys.argv[2]
    
    avg_precision, avg_recall, avg_f1 = evaluate(predictions_path, ground_truths_path)
    
    print(f"Precision: {avg_precision:.4f}")
    print(f"Recall: {avg_recall:.4f}")
    print(f"F1 Score: {avg_f1:.4f}")
