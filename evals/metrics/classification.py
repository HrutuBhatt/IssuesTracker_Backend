"""Binary classification metrics — precision, recall, F1 for guardrail evals."""


def compute_metrics(predictions: list[bool], labels: list[bool]) -> dict:
    """
    predictions: what the system returned (True = safe)
    labels:      ground truth (True = safe)

    For guardrail evals we care about catching unsafe inputs (positive class = unsafe).
    So we flip: unsafe = True for metric computation.
    """
    tp = fp = tn = fn = 0

    for pred, label in zip(predictions, labels):
        unsafe_pred = not pred
        unsafe_label = not label

        if unsafe_pred and unsafe_label:
            tp += 1
        elif unsafe_pred and not unsafe_label:
            fp += 1
        elif not unsafe_pred and not unsafe_label:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = (tp + tn) / len(predictions) if predictions else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "accuracy": round(accuracy, 3),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
    }
