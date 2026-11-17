import argparse
import csv
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "data", "colors.csv")
LABELS = ["red", "green", "blue"]
BLOCK = 20  # consecutive rows per held-out block


def load(path, use_clear):
    path = os.path.abspath(path)
    feats, labels, groups = [], [], []
    counters = {}
    with open(path, "r", newline="") as f:
        for row in csv.DictReader(f):
            if row["label"] not in LABELS:
                continue
            x = [float(row["r_share"]), float(row["g_share"]), float(row["b_share"])]
            if use_clear:
                x.append(np.log1p(float(row["clear"])))
            n = counters.get(row["label"], 0)
            counters[row["label"]] = n + 1
            feats.append(x)
            labels.append(LABELS.index(row["label"]))
            groups.append(f"{row['label']}-{n // BLOCK}")
    return np.array(feats), np.array(labels), np.array(groups)


def threshold_rule(X):
    """The hand-written baseline from the gateway plan (uses r_share and g_share only)."""
    out = np.full(len(X), LABELS.index("blue"))
    out[X[:, 1] > 0.35] = LABELS.index("green")
    out[X[:, 0] > 0.45] = LABELS.index("red")
    return out


def cross_validate(make_model, X, y, groups, folds):
    pred = np.empty_like(y)
    accs = []
    for train, test in GroupKFold(n_splits=folds).split(X, y, groups):
        if make_model is None:
            p = threshold_rule(X[test])
        else:
            model = make_model().fit(X[train], y[train])
            p = model.predict(X[test])
        pred[test] = p
        accs.append(accuracy_score(y[test], p))
    return pred, np.array(accs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--no-clear", action="store_true", help="do not use brightness as a feature")
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    X, y, groups = load(args.csv, use_clear=not args.no_clear)
    counts = {LABELS[i]: int((y == i).sum()) for i in range(len(LABELS))}
    print(f"{len(y)} samples {counts}, {len(set(groups))} blocks, features: {X.shape[1]}")

    models = {
        "threshold rule": None,
        "logistic regression": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "decision tree (depth 4)": lambda: DecisionTreeClassifier(max_depth=4, random_state=0),
        "small MLP (8 hidden)": lambda: make_pipeline(
            StandardScaler(), MLPClassifier((8,), max_iter=2000, random_state=0)),
    }

    for name, make in models.items():
        pred, accs = cross_validate(make, X, y, groups, args.folds)
        print(f"\n== {name}: accuracy {accs.mean():.3f} +/- {accs.std():.3f} over {len(accs)} folds")
        print("   rows = true, cols = predicted", LABELS)
        print(confusion_matrix(y, pred, labels=range(len(LABELS))))


if __name__ == "__main__":
    main()
