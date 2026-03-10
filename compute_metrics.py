import csv
import sys

def main():
    tp = tn = fp = fn = 0
    s1_rows = s2_rows = 0
    
    with open("labeled_scenarios.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ml = row["ml_result"].strip()
            actual = row["actual_label"].strip()
            scenario = row["scenario"].strip()
            
            if scenario == "Clear_Algae_Present":
                s1_rows += 1
            else:
                s2_rows += 1
            
            if ml == "Algae" and actual == "Algae":
                tp += 1
            elif ml == "No Algae" and actual == "No Algae":
                tn += 1
            elif ml == "Algae" and actual == "No Algae":
                fp += 1
            elif ml == "No Algae" and actual == "Algae":
                fn += 1
    
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total * 100 if total else 0
    precision = tp / (tp + fp) * 100 if (tp + fp) else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) else 0
    specificity = tn / (tn + fp) * 100 if (tn + fp) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    fpr = fp / (fp + tn) * 100 if (fp + tn) else 0
    
    print("=" * 60)
    print("AMLAC ALGAE DETECTION - CONFUSION MATRIX REPORT")
    print("=" * 60)
    print()
    print("SCENARIOS:")
    print(f"  S1: Clear + Algae Present   (P2sl.csv 20:50-21:16) = {s1_rows} rows")
    print(f"  S2: Clear + No Algae Present (Pev0.csv 22:17-23:26) = {s2_rows} rows")
    print(f"  Total labeled samples: {total}")
    print()
    print("CONFUSION MATRIX:")
    print(f"                    Predicted Algae    Predicted No Algae")
    print(f"  Actual Algae          TP = {tp:<14d} FN = {fn}")
    print(f"  Actual No Algae       FP = {fp:<14d} TN = {tn}")
    print()
    print("METRICS:")
    print(f"  Accuracy:           {accuracy:.2f}%  ({tp+tn}/{total})")
    print(f"  Precision:          {precision:.2f}%  ({tp}/{tp+fp})")
    print(f"  Recall/Sensitivity: {recall:.2f}%  ({tp}/{tp+fn})")
    print(f"  Specificity:        {specificity:.2f}%  ({tn}/{tn+fp})")
    print(f"  F1 Score:           {f1:.2f}")
    print(f"  False Positive Rate:{fpr:.2f}%  ({fp}/{fp+tn})")
    print()
    print("INTERPRETATION:")
    if recall >= 90:
        print(f"  + HIGH Recall ({recall:.1f}%): Model catches algae when present")
    else:
        print(f"  - LOW Recall ({recall:.1f}%): Model misses algae when present")
    
    if specificity < 50:
        print(f"  - VERY LOW Specificity ({specificity:.1f}%): Model falsely detects algae in clean water")
    
    if fp > tn:
        print(f"  - HIGH False Positive Rate: {fp} false alarms vs {tn} correct clean-water detections")
    
    print()
    print("PER-SCENARIO BREAKDOWN:")
    print(f"  S1 (Algae Present):    {tp}/{s1_rows} correctly detected = {tp/s1_rows*100:.1f}% detection rate")
    print(f"  S2 (No Algae Present): {tn}/{s2_rows} correctly identified = {tn/s2_rows*100:.1f}% rejection rate")

if __name__ == "__main__":
    main()
