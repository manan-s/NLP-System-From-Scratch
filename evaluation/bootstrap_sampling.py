## Ref https://github.com/neubig/util-scripts/blob/master/paired-bootstrap.py

import sys
import argparse
from typing import List, Tuple
import string
import collections
import numpy as np

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

def compute_f1_scores(predictions: List[str], ground_truths: List[str]) -> List[float]:
    f1_scores = []
    for pred, gt_line in zip(predictions, ground_truths):
        prediction = pred.strip()
        gt_answers = [gt.strip() for gt in gt_line.split(';')]
        _, _, max_f1 = max_precision_recall_f1(prediction, gt_answers)
        f1_scores.append(max_f1)
    return f1_scores

def paired_bootstrap(sys1_scores: List[float], sys2_scores: List[float],
                    num_samples: int = 10000, sample_ratio: float = 0.5) -> None:
    """
    Perform paired bootstrap resampling to compare two systems' F1 scores.
    
    :param sys1_scores: List of F1 scores for system 1.
    :param sys2_scores: List of F1 scores for system 2.
    :param num_samples: Number of bootstrap samples to draw.
    :param sample_ratio: Ratio of samples to draw in each bootstrap iteration.
    """
    assert len(sys1_scores) == len(sys2_scores), "Systems must have the same number of F1 scores."
    n = len(sys1_scores)
    ids = np.arange(n)
    
    sys1_bootstrap = []
    sys2_bootstrap = []
    wins = [0, 0, 0]  # sys1 win, sys2 win, tie
    
    for _ in range(num_samples):
        sampled_ids = np.random.choice(ids, int(n * sample_ratio), replace=True)
        sampled_sys1 = [sys1_scores[i] for i in sampled_ids]
        sampled_sys2 = [sys2_scores[i] for i in sampled_ids]
        
        mean_sys1 = np.mean(sampled_sys1)
        mean_sys2 = np.mean(sampled_sys2)
        
        sys1_bootstrap.append(mean_sys1)
        sys2_bootstrap.append(mean_sys2)
        
        if mean_sys1 > mean_sys2:
            wins[0] += 1
        elif mean_sys1 < mean_sys2:
            wins[1] += 1
        else:
            wins[2] += 1
    
    # Calculate win ratios
    win_ratios = [win / num_samples for win in wins]
    print(f'Win ratio: sys1={win_ratios[0]:.3f}, sys2={win_ratios[1]:.3f}, tie={win_ratios[2]:.3f}')
    
    if win_ratios[0] > win_ratios[1]:
        print(f'(sys1 is superior with p-value p={1 - win_ratios[0]:.3f})\n')
    elif win_ratios[1] > win_ratios[0]:
        print(f'(sys2 is superior with p-value p={1 - win_ratios[1]:.3f})\n')
    else:
        print('(No significant difference between sys1 and sys2)\n')
    
    # Calculate confidence intervals
    sys1_bootstrap_sorted = sorted(sys1_bootstrap)
    sys2_bootstrap_sorted = sorted(sys2_bootstrap)
    lower_bound = int(num_samples * 0.025)
    upper_bound = int(num_samples * 0.975)
    
    sys1_mean = np.mean(sys1_bootstrap)
    sys1_median = np.median(sys1_bootstrap)
    sys1_ci = (sys1_bootstrap_sorted[lower_bound], sys1_bootstrap_sorted[upper_bound])
    
    sys2_mean = np.mean(sys2_bootstrap)
    sys2_median = np.median(sys2_bootstrap)
    sys2_ci = (sys2_bootstrap_sorted[lower_bound], sys2_bootstrap_sorted[upper_bound])
    
    print(f'sys1 mean={sys1_mean:.3f}, median={sys1_median:.3f}, 95% CI=[{sys1_ci[0]:.3f}, {sys1_ci[1]:.3f}]')
    print(f'sys2 mean={sys2_mean:.3f}, median={sys2_median:.3f}, 95% CI=[{sys2_ci[0]:.3f}, {sys2_ci[1]:.3f}]')

def main(predictions_path_sys1: str, predictions_path_sys2: str, ground_truths_path: str, 
         num_samples: int, sample_ratio: float) -> None:
    """
    Main function to evaluate two systems and perform paired bootstrap sampling.
    
    :param predictions_path_sys1: Path to system 1 predictions file.
    :param predictions_path_sys2: Path to system 2 predictions file.
    :param ground_truths_path: Path to ground truths file.
    :param num_samples: Number of bootstrap samples.
    :param sample_ratio: Ratio of samples to draw in each bootstrap iteration.
    """
    with open(ground_truths_path, 'r', encoding='utf-8') as f:
        ground_truths = f.readlines()
    
    with open(predictions_path_sys1, 'r', encoding='utf-8') as f:
        predictions_sys1 = f.readlines()
    
    with open(predictions_path_sys2, 'r', encoding='utf-8') as f:
        predictions_sys2 = f.readlines()
    
    if not (len(ground_truths) == len(predictions_sys1) == len(predictions_sys2)):
        print(f"Error: Number of ground truths ({len(ground_truths)}), "
              f"sys1 predictions ({len(predictions_sys1)}), and sys2 predictions ({len(predictions_sys2)}) do not match.")
        sys.exit(1)
    
    sys1_f1_scores = compute_f1_scores(predictions_sys1, ground_truths)
    sys2_f1_scores = compute_f1_scores(predictions_sys2, ground_truths)
    
    paired_bootstrap(sys1_f1_scores, sys2_f1_scores, num_samples=num_samples, sample_ratio=sample_ratio)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluate two systems and perform paired bootstrap sampling for statistical significance.')
    parser.add_argument('ground_truths', help='Path to the ground truths file.')
    parser.add_argument('sys1_predictions', help='Path to system 1 predictions file.')
    parser.add_argument('sys2_predictions', help='Path to system 2 predictions file.')
    parser.add_argument('--num_samples', type=int, default=10000, help='Number of bootstrap samples to draw (default: 10000).')
    parser.add_argument('--sample_ratio', type=float, default=0.5, help='Ratio of samples to draw in each bootstrap iteration (default: 0.5).')
    
    args = parser.parse_args()
    
    main(args.sys1_predictions, args.sys2_predictions, args.ground_truths, 
         num_samples=args.num_samples, sample_ratio=args.sample_ratio)
