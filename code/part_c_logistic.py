"""Part C - Logistic regression experiments (C1, C2, C3) on Breast Cancer Wisconsin."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, log_loss,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import C1, C2, C3, INK, INK2, RANDOM_SEED, TEST_SIZE, save_results, savefig, plt
from part_a_data import load_classification_df

FEATS_C1 = ["mean radius", "mean texture", "mean smoothness", "mean concave points", "mean symmetry"]
ONE_FEAT = ["mean radius"]
TWO_FEAT = ["mean radius", "mean texture"]


def clf_metrics(y, p, thr):
    yhat = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, yhat, labels=[0, 1]).ravel()
    return {"threshold": thr, "accuracy": float(accuracy_score(y, yhat)),
            "precision": float(precision_score(y, yhat, zero_division=0)),
            "recall": float(recall_score(y, yhat)), "f1": float(f1_score(y, yhat)),
            "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)}


def make_model():
    return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000))


def draw_cm(ax, m, title):
    cm = np.array([[m["TN"], m["FP"]], [m["FN"], m["TP"]]])
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.15)
    names = [["TN", "FP"], ["FN", "TP"]]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{names[i][j]}\n{cm[i, j]}", ha="center", va="center", fontsize=12,
                    color="white" if cm[i, j] > cm.max() * 0.6 else INK, fontweight="bold")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["benign (0)", "malignant (1)"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["benign (0)", "malignant (1)"])
    ax.set_xlabel("Predicted class"); ax.set_ylabel("Actual class")
    ax.set_title(title); ax.grid(False)


def main():
    df = load_classification_df()
    y = df["malignant"].values
    idx = np.arange(len(df))
    tr, te = train_test_split(idx, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y)
    ytr, yte = y[tr], y[te]
    res = {"split": {"train": len(tr), "test": len(te), "train_malignant": int(ytr.sum()),
                     "test_malignant": int(yte.sum())}, "features_C1": FEATS_C1}

    # ===================== C1 =====================
    Xtr, Xte = df.loc[tr, FEATS_C1].values, df.loc[te, FEATS_C1].values
    model = make_model().fit(Xtr, ytr)
    lr = model[-1]
    p_te = model.predict_proba(Xte)[:, 1]
    z_te = model.decision_function(Xte)
    m05 = clf_metrics(yte, p_te, 0.5)
    # coefficients mapped back to raw units (per 1 raw unit) for interpretation
    sc = model[0]
    raw_coef = lr.coef_[0] / sc.scale_
    res["C1"] = {"intercept_standardized": float(lr.intercept_[0]),
                 "coef_standardized": dict(zip(FEATS_C1, map(float, lr.coef_[0]))),
                 "odds_ratio_per_std": dict(zip(FEATS_C1, map(float, np.exp(lr.coef_[0])))),
                 "coef_raw_units": dict(zip(FEATS_C1, map(float, raw_coef))),
                 "intercept_raw_units": float(lr.intercept_[0] - np.sum(lr.coef_[0] * sc.mean_ / sc.scale_)),
                 "train_std": dict(zip(FEATS_C1, map(float, sc.scale_))),
                 "test@0.5": m05, "test_auc": float(roc_auc_score(yte, p_te)),
                 "test_logloss": float(log_loss(yte, p_te)),
                 "train_accuracy": float(accuracy_score(ytr, model.predict(Xtr)))}
    # example of raw output for 3 test patients
    ex = [0, 1, 2]
    res["C1"]["examples"] = [{"z": float(z_te[i]), "p": float(p_te[i]), "y": int(yte[i])} for i in ex]
    # misclassified test samples
    wrong = np.where((p_te >= 0.5).astype(int) != yte)[0]
    res["C1"]["misclassified"] = [{"p": float(p_te[i]), "y": int(yte[i]),
                                   **{f: float(df.loc[te[i], f]) for f in FEATS_C1}} for i in wrong]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"width_ratios": [1, 1.25]})
    draw_cm(axes[0], m05, "(a) Confusion matrix, test set, threshold 0.5")
    ax = axes[1]
    bins = np.linspace(0, 1, 26)
    ax.hist(p_te[yte == 0], bins=bins, color=C1, alpha=0.7, label="actual benign", edgecolor="white", linewidth=0.5)
    ax.hist(p_te[yte == 1], bins=bins, color=C2, alpha=0.7, label="actual malignant", edgecolor="white", linewidth=0.5)
    ax.axvline(0.5, color=INK, ls="--", lw=1, label="threshold 0.5")
    ax.set_xlabel("Predicted probability P(malignant | x)")
    ax.set_ylabel("Number of test samples")
    ax.set_title("(b) Model output before thresholding")
    ax.legend(fontsize=8)
    savefig(fig, "C1_confusion_matrix.png")

    # ===================== C2: thresholds =====================
    thr3 = [0.3, 0.5, 0.7]
    res["C2"] = {"test": {str(t): clf_metrics(yte, p_te, t) for t in thr3}}
    # threshold selection uses only the TRAINING data (5-fold out-of-fold probabilities)
    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_SEED)
    p_oof = cross_val_predict(make_model(), Xtr, ytr, cv=cv, method="predict_proba")[:, 1]
    res["C2"]["train_cv"] = {str(t): clf_metrics(ytr, p_oof, t) for t in thr3}

    grid = np.round(np.arange(0.05, 0.951, 0.01), 2)
    prec = [precision_score(yte, (p_te >= t).astype(int), zero_division=1) for t in grid]
    rec = [recall_score(yte, (p_te >= t).astype(int)) for t in grid]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    ax.plot(grid, prec, color=C1, label="precision")
    ax.plot(grid, rec, color=C2, label="recall")
    for t in thr3:
        m = res["C2"]["test"][str(t)]
        ax.axvline(t, color=INK2, lw=0.8, ls=":")
        ax.plot([t], [m["precision"]], "o", color=C1, ms=8, mec="white", mew=1.5)
        ax.plot([t], [m["recall"]], "o", color=C2, ms=8, mec="white", mew=1.5)
        ax.annotate(f"P={m['precision']:.2f}\nR={m['recall']:.2f}", (t, 0.72), ha="center", fontsize=8, color=INK2,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    ax.set_ylim(0.6, 1.02)
    ax.set_xlabel("Classification threshold")
    ax.set_ylabel("Score (test set)")
    ax.set_title("(a) Precision and recall vs. threshold")
    ax.legend(loc="lower left")
    ax = axes[1]
    x = np.arange(3)
    fps = [res["C2"]["test"][str(t)]["FP"] for t in thr3]
    fns = [res["C2"]["test"][str(t)]["FN"] for t in thr3]
    ax.bar(x - 0.18, fps, 0.34, color=C1, label="false positives (benign → malignant)")
    ax.bar(x + 0.18, fns, 0.34, color=C2, label="false negatives (malignant → benign)")
    for i in range(3):
        ax.text(x[i] - 0.18, fps[i] + 0.15, str(fps[i]), ha="center", fontsize=9)
        ax.text(x[i] + 0.18, fns[i] + 0.15, str(fns[i]), ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([f"t = {t}" for t in thr3])
    ax.set_ylabel("Count (test set, n = %d)" % len(te))
    ax.set_title("(b) Error types per threshold")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_ylim(0, max(fps + fns) + 3)
    savefig(fig, "C2_threshold.png")

    # ===================== C3: one vs two features =====================
    c3 = {}
    models = {}
    for name, fs in [("one_feature", ONE_FEAT), ("two_features", TWO_FEAT)]:
        m = make_model().fit(df.loc[tr, fs].values, ytr)
        p = m.predict_proba(df.loc[te, fs].values)[:, 1]
        models[name] = m
        c3[name] = {"features": fs, "coef_standardized": list(map(float, m[-1].coef_[0])),
                    "intercept": float(m[-1].intercept_[0]),
                    "test@0.5": clf_metrics(yte, p, 0.5), "test_auc": float(roc_auc_score(yte, p)),
                    "test_logloss": float(log_loss(yte, p))}
    # 1-feature decision point in raw units
    m1 = models["one_feature"]
    x_star_std = -m1[-1].intercept_[0] / m1[-1].coef_[0][0]
    c3["one_feature"]["decision_point_raw"] = float(x_star_std * m1[0].scale_[0] + m1[0].mean_[0])
    # boundary-margin analysis for the two-feature model
    m2 = models["two_features"]
    Xte2s = m2[0].transform(df.loc[te, TWO_FEAT].values)
    p2 = m2.predict_proba(df.loc[te, TWO_FEAT].values)[:, 1]
    w, b0 = m2[-1].coef_[0], m2[-1].intercept_[0]
    dist = np.abs(Xte2s @ w + b0) / np.linalg.norm(w)
    wrong2 = (p2 >= 0.5).astype(int) != yte
    c3["two_features"]["mean_dist_correct"] = float(dist[~wrong2].mean())
    c3["two_features"]["mean_dist_wrong"] = float(dist[wrong2].mean())
    c3["two_features"]["n_within_0.5std_of_boundary"] = int((dist < 0.5).sum())
    c3["two_features"]["error_rate_within_0.5std"] = float(wrong2[dist < 0.5].mean())
    c3["two_features"]["error_rate_beyond_0.5std"] = float(wrong2[dist >= 0.5].mean())
    res["C3"] = c3

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [1, 1.25]})
    # (a) one-feature model: sigmoid
    ax = axes[0]
    Xte1s = m1[0].transform(df.loc[te, ONE_FEAT].values)[:, 0]
    rng = np.random.default_rng(0)
    jit = rng.uniform(-0.03, 0.03, len(yte))
    ax.scatter(Xte1s[yte == 0], yte[yte == 0] + jit[yte == 0], s=16, color=C1, alpha=0.75, label="benign (test)")
    ax.scatter(Xte1s[yte == 1], yte[yte == 1] + jit[yte == 1], s=16, color=C2, alpha=0.75, label="malignant (test)")
    xs = np.linspace(-2.5, 4, 300)
    ax.plot(xs, 1 / (1 + np.exp(-(m1[-1].coef_[0][0] * xs + m1[-1].intercept_[0]))), color=INK, lw=1.8,
            label="P(malignant | radius)")
    ax.axvline(x_star_std, color=INK2, ls="--", lw=1, label=f"boundary: radius = {c3['one_feature']['decision_point_raw']:.1f} mm")
    ax.set_xlabel("mean radius (standardised, z-score)")
    ax.set_ylabel("P(malignant) / actual class")
    ax.set_title(f"(a) One feature  (test acc = {c3['one_feature']['test@0.5']['accuracy']:.3f})")
    ax.legend(fontsize=7.5, loc="center left")
    # (b) two-feature decision boundary
    ax = axes[1]
    gx, gy = np.meshgrid(np.linspace(-2.5, 4.2, 300), np.linspace(-2.6, 4.2, 300))
    zz = 1 / (1 + np.exp(-(w[0] * gx + w[1] * gy + b0)))
    cf = ax.contourf(gx, gy, zz, levels=np.linspace(0, 1, 11), cmap="RdBu_r", alpha=0.35)
    cs = ax.contour(gx, gy, zz, levels=[0.3, 0.5, 0.7], colors=[INK2, INK, INK2], linewidths=[1, 2, 1],
                    linestyles=[":", "-", ":"])
    ax.clabel(cs, fmt={0.3: "p=0.3", 0.5: "p=0.5", 0.7: "p=0.7"}, fontsize=8)
    Xtr2s = m2[0].transform(df.loc[tr, TWO_FEAT].values)
    ax.scatter(Xtr2s[ytr == 0, 0], Xtr2s[ytr == 0, 1], s=8, color=C1, alpha=0.25, edgecolor="none")
    ax.scatter(Xtr2s[ytr == 1, 0], Xtr2s[ytr == 1, 1], s=8, color=C2, alpha=0.25, edgecolor="none")
    ax.scatter(Xte2s[yte == 0, 0], Xte2s[yte == 0, 1], s=26, color=C1, edgecolor="white", linewidth=0.6, label="benign (test)")
    ax.scatter(Xte2s[yte == 1, 0], Xte2s[yte == 1, 1], s=26, color=C2, edgecolor="white", linewidth=0.6, label="malignant (test)")
    ax.scatter(Xte2s[wrong2, 0], Xte2s[wrong2, 1], s=80, facecolor="none", edgecolor=INK, linewidth=1.3,
               label="misclassified (test)")
    ax.set_xlim(-2.5, 4.2); ax.set_ylim(-2.6, 4.2)
    ax.set_xlabel("mean radius (standardised, z-score)")
    ax.set_ylabel("mean texture (standardised, z-score)")
    ax.set_title(f"(b) Two features  (test acc = {c3['two_features']['test@0.5']['accuracy']:.3f})")
    ax.legend(fontsize=7.5, loc="upper right")
    cb = fig.colorbar(cf, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("P(malignant)")
    ax.grid(False)
    savefig(fig, "C3_decision_boundary.png")

    save_results("C_logistic_results.json", res)


if __name__ == "__main__":
    main()
