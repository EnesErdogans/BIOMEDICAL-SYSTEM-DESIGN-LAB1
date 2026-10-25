"""Part A - dataset selection, export to CSV and exploration figures.

Dataset 1 (linear regression): Diabetes dataset (Efron et al., 2004), raw units.
Dataset 2 (logistic regression): Breast Cancer Wisconsin (Diagnostic), UCI.
Both ship with scikit-learn, so the experiment is fully reproducible offline.
"""
import os

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer, load_diabetes

from common import C1, C2, DATA_DIR, INK2, save_results, savefig, plt


def load_regression_df():
    d = load_diabetes(scaled=False)  # raw, un-normalised units
    df = pd.DataFrame(d.data, columns=["age", "sex", "bmi", "bp", "s1", "s2", "s3", "s4", "s5", "s6"])
    df["target"] = d.target
    return df


def load_classification_df():
    d = load_breast_cancer()
    df = pd.DataFrame(d.data, columns=d.feature_names)
    # sklearn encodes 0 = malignant, 1 = benign; we make malignant the positive class
    df["malignant"] = (d.target == 0).astype(int)
    return df


def main():
    reg = load_regression_df()
    clf = load_classification_df()
    reg.to_csv(os.path.join(DATA_DIR, "diabetes_regression.csv"), index=False)
    clf.to_csv(os.path.join(DATA_DIR, "breast_cancer_classification.csv"), index=False)

    # ---------- summary statistics ----------
    reg_desc = reg.describe().T[["mean", "std", "min", "max"]].round(2)
    reg_desc.to_csv(os.path.join(DATA_DIR, "..", "results", "A_regression_describe.csv"))
    corr = reg.corr()["target"].drop("target").sort_values(ascending=False)
    clf_counts = clf["malignant"].value_counts().to_dict()
    sel = ["mean radius", "mean texture", "mean smoothness", "mean concave points", "mean symmetry"]
    clf_desc = clf[sel].describe().T[["mean", "std", "min", "max"]].round(3)
    clf_desc.to_csv(os.path.join(DATA_DIR, "..", "results", "A_classification_describe.csv"))
    save_results("A_summary.json", {
        "regression": {"n": len(reg), "n_features": reg.shape[1] - 1,
                       "missing": int(reg.isna().sum().sum()),
                       "target_mean": float(reg.target.mean()), "target_std": float(reg.target.std()),
                       "target_min": float(reg.target.min()), "target_max": float(reg.target.max()),
                       "corr_with_target": corr.round(3).to_dict(),
                       "describe": reg_desc.to_dict(orient="index")},
        "classification": {"n": len(clf), "n_features_total": clf.shape[1] - 1,
                           "missing": int(clf.isna().sum().sum()),
                           "malignant": int(clf_counts[1]), "benign": int(clf_counts[0]),
                           "describe": clf_desc.to_dict(orient="index")},
    })

    # ---------- Figure A1: regression relationships ----------
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.2, 1]})
    ax = axes[0]
    ax.scatter(reg.bmi, reg.target, s=14, color=C1, alpha=0.65, edgecolor="white", linewidth=0.4)
    m, b = np.polyfit(reg.bmi, reg.target, 1)
    xs = np.linspace(reg.bmi.min(), reg.bmi.max(), 50)
    ax.plot(xs, m * xs + b, color=C2, label=f"least-squares fit (r = {corr['bmi']:.2f})")
    ax.set_xlabel("Body-mass index, bmi (kg/m$^2$)")
    ax.set_ylabel("Disease progression after 1 year")
    ax.set_title("(a) BMI vs. disease progression")
    ax.legend(loc="upper left")
    ax = axes[1]
    colors = [C1 if v > 0 else C2 for v in corr.values]
    ax.barh(corr.index[::-1], corr.values[::-1], color=colors[::-1], height=0.6)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_xlabel("Pearson correlation with target")
    ax.set_title("(b) Feature-target correlation")
    for i, v in enumerate(corr.values[::-1]):
        ax.text(v + (0.01 if v >= 0 else -0.01), i, f"{v:.2f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=8, color=INK2)
    ax.set_xlim(-0.55, 0.75)
    savefig(fig, "A1_regression_eda.png")

    # ---------- Figure A2: classification relationships ----------
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    for lab, col, name in [(0, C1, "benign (0)"), (1, C2, "malignant (1)")]:
        s = clf[clf.malignant == lab]
        ax.scatter(s["mean radius"], s["mean texture"], s=14, color=col, alpha=0.65,
                   edgecolor="white", linewidth=0.4, label=f"{name}, n={len(s)}")
    ax.set_xlabel("mean radius (mm)")
    ax.set_ylabel("mean texture (grey-level std)")
    ax.set_title("(a) Radius vs. texture by diagnosis")
    ax.legend(loc="upper right")
    ax = axes[1]
    bins = np.linspace(clf["mean concave points"].min(), clf["mean concave points"].max(), 30)
    for lab, col, name in [(0, C1, "benign"), (1, C2, "malignant")]:
        ax.hist(clf.loc[clf.malignant == lab, "mean concave points"], bins=bins, color=col,
                alpha=0.6, label=name, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("mean concave points")
    ax.set_ylabel("count")
    ax.set_title("(b) Concave points by diagnosis")
    ax.legend()
    savefig(fig, "A2_classification_eda.png")


if __name__ == "__main__":
    main()
