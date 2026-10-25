"""Part B - Linear regression experiments (B1, B2, B3) on the Diabetes dataset."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from common import C1, C2, C3, C4, INK2, RANDOM_SEED, TEST_SIZE, save_results, savefig, plt
from part_a_data import load_regression_df


def metrics(y, p):
    return {"MAE": float(mean_absolute_error(y, p)), "MSE": float(mean_squared_error(y, p)),
            "RMSE": float(np.sqrt(mean_squared_error(y, p))), "R2": float(r2_score(y, p))}


def gradient_descent(X, y, lr, n_iter):
    """Batch gradient descent for linear regression.
    Loss J(w,b) = (1/2n) * sum (Xw + b - y)^2 ; returns weights, bias and loss history (MSE = 2J)."""
    n, d = X.shape
    w, b = np.zeros(d), 0.0
    hist = []
    for _ in range(n_iter):
        r = X @ w + b - y
        mse = float(np.mean(r ** 2))
        hist.append(mse)
        if not np.isfinite(mse) or mse > 1e12:
            hist[-1] = np.inf
            break
        w -= lr * (X.T @ r) / n
        b -= lr * r.mean()
    return w, b, np.array(hist)


def main():
    df = load_regression_df()
    feats = [c for c in df.columns if c != "target"]
    X, y = df[feats].values, df["target"].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED)
    res = {"split": {"train": len(ytr), "test": len(yte)}}

    # ===================== B1: baseline =====================
    lr_model = LinearRegression().fit(Xtr, ytr)
    p_tr, p_te = lr_model.predict(Xtr), lr_model.predict(Xte)
    res["B1"] = {"intercept": float(lr_model.intercept_),
                 "coef": dict(zip(feats, map(float, lr_model.coef_))),
                 "train": metrics(ytr, p_tr), "test": metrics(yte, p_te),
                 "baseline_mean_predictor_test": metrics(yte, np.full_like(yte, ytr.mean(), dtype=float))}

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    ax.scatter(ytr, p_tr, s=12, color=C1, alpha=0.35, edgecolor="none", label="train")
    ax.scatter(yte, p_te, s=22, color=C2, alpha=0.9, edgecolor="white", linewidth=0.5, label="test")
    lim = [0, 360]
    ax.plot(lim, lim, color=INK2, lw=1, ls="--", label="perfect prediction (y = ŷ)")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Actual disease progression")
    ax.set_ylabel("Predicted disease progression")
    t = res["B1"]["test"]
    ax.set_title(f"(a) Actual vs. predicted  (test R² = {t['R2']:.3f})")
    ax.legend(loc="upper left")
    ax = axes[1]
    resid = yte - p_te
    ax.scatter(p_te, resid, s=22, color=C2, edgecolor="white", linewidth=0.5)
    ax.axhline(0, color=INK2, lw=1, ls="--")
    ax.set_xlabel("Predicted value (test)")
    ax.set_ylabel("Residual  y − ŷ")
    ax.set_title("(b) Test residuals")
    savefig(fig, "B1_actual_vs_predicted.png")

    # ===================== B2: feature scaling =====================
    scaler = StandardScaler().fit(Xtr)               # fitted on training data only
    Xtr_s, Xte_s = scaler.transform(Xtr), scaler.transform(Xte)
    lr_s = LinearRegression().fit(Xtr_s, ytr)
    p_te_s = lr_s.predict(Xte_s)
    max_pred_diff = float(np.max(np.abs(p_te_s - p_te)))

    # Gradient-descent training behaviour: unscaled vs standardised.
    # Largest stable step for GD is 2 / lambda_max of the (augmented) Hessian (1/n) X^T X.
    def lam_max(Xm):
        A = np.hstack([Xm, np.ones((len(Xm), 1))])
        return float(np.linalg.eigvalsh(A.T @ A / len(A)).max()), float(np.linalg.cond(A.T @ A / len(A)))
    lmax_u, cond_u = lam_max(Xtr)
    lmax_s, cond_s = lam_max(Xtr_s)
    lr_u = 1.9 / lmax_u                               # ~ the largest stable learning rate, unscaled
    lr_sc = 0.1
    N2 = 5000
    w_u, b_u, h_u = gradient_descent(Xtr, ytr, lr_u, N2)
    w_s, b_s, h_s = gradient_descent(Xtr_s, ytr, lr_sc, N2)
    _, _, h_u_div = gradient_descent(Xtr, ytr, 1e-4, 200)  # a "normal looking" lr diverges unscaled
    gd_u_test = metrics(yte, Xte @ w_u + b_u)
    gd_s_test = metrics(yte, Xte_s @ w_s + b_s)

    res["B2"] = {
        "unscaled": {"intercept": float(lr_model.intercept_), "coef": dict(zip(feats, map(float, lr_model.coef_))),
                     "test": res["B1"]["test"]},
        "standardized": {"intercept": float(lr_s.intercept_), "coef": dict(zip(feats, map(float, lr_s.coef_))),
                         "test": metrics(yte, p_te_s)},
        "scaler_mean": dict(zip(feats, map(float, scaler.mean_))),
        "scaler_std": dict(zip(feats, map(float, scaler.scale_))),
        "max_abs_prediction_difference": max_pred_diff,
        "gd": {"lambda_max_unscaled": lmax_u, "cond_unscaled": cond_u,
               "lambda_max_scaled": lmax_s, "cond_scaled": cond_s,
               "lr_unscaled": lr_u, "lr_scaled": lr_sc, "iterations": N2,
               "final_train_mse_unscaled": float(h_u[-1]), "final_train_mse_scaled": float(h_s[-1]),
               "test_unscaled": gd_u_test, "test_scaled": gd_s_test,
               "unscaled_lr_1e-4_diverged_at_iter": int(len(h_u_div)),
               "closed_form_train_mse": float(mean_squared_error(ytr, p_tr))},
    }

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    cu = np.array([res["B2"]["unscaled"]["coef"][f] for f in feats])
    cs = np.array([res["B2"]["standardized"]["coef"][f] for f in feats])
    yy = np.arange(len(feats))
    ax.barh(yy + 0.2, cu, height=0.38, color=C1, label="raw units (per 1 unit of feature)")
    ax.barh(yy - 0.2, cs, height=0.38, color=C2, label="standardised (per 1 std. dev.)")
    ax.set_yticks(yy); ax.set_yticklabels(feats); ax.invert_yaxis()
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_xlabel("Coefficient value")
    ax.set_title("(a) OLS coefficients before / after standardisation")
    ax.legend(loc="lower right", fontsize=8)
    ax = axes[1]
    ax.plot(np.arange(1, len(h_u) + 1), h_u, color=C1, label=f"unscaled, lr = {lr_u:.1e} (max stable)")
    ax.plot(np.arange(1, len(h_s) + 1), h_s, color=C2, label=f"standardised, lr = {lr_sc}")
    ax.axhline(res["B2"]["gd"]["closed_form_train_mse"], color=INK2, ls="--", lw=1, label="closed-form OLS optimum")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Iteration (log)")
    ax.set_ylabel("Training MSE (log)")
    ax.set_title("(b) Gradient-descent training behaviour")
    ax.legend(fontsize=8)
    savefig(fig, "B2_scaling_comparison.png")

    # ===================== B3: learning rate & convergence =====================
    lrs = [0.001, 0.01, 0.1, 0.5, 1.0]
    N3 = 2000
    opt = res["B2"]["gd"]["closed_form_train_mse"]
    b3 = {"lr_stability_limit": float(2 / lmax_s), "iterations": N3, "runs": {}}
    curves = {}
    for lr in lrs:
        w, b, h = gradient_descent(Xtr_s, ytr, lr, N3)
        curves[lr] = h
        diverged = not np.isfinite(h[-1])
        near = np.where(h <= opt * 1.01)[0]
        b3["runs"][str(lr)] = {
            "diverged": bool(diverged),
            "final_train_mse": None if diverged else float(h[-1]),
            "iter_to_within_1pct_of_optimum": int(near[0] + 1) if len(near) else None,
            "test": None if diverged else metrics(yte, Xte_s @ w + b),
        }
    # effect of number of iterations at a fixed, good learning rate
    iter_grid = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2000, 5000]
    it_res = {}
    for lr in [0.01, 0.1]:
        it_res[str(lr)] = {}
        for n in iter_grid:
            w, b, h = gradient_descent(Xtr_s, ytr, lr, n)
            it_res[str(lr)][n] = {"train_MSE": float(mean_squared_error(ytr, Xtr_s @ w + b)),
                                  "test_R2": float(r2_score(yte, Xte_s @ w + b)),
                                  "coef_s5": float(w[feats.index("s5")]), "coef_s1": float(w[feats.index("s1")])}
    b3["iterations_effect"] = it_res
    b3["closed_form_test_R2"] = res["B2"]["standardized"]["test"]["R2"]
    b3["closed_form_coef_s5"] = res["B2"]["standardized"]["coef"]["s5"]
    b3["closed_form_coef_s1"] = res["B2"]["standardized"]["coef"]["s1"]
    res["B3"] = b3

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    cols = {0.001: C4, 0.01: C3, 0.1: C1, 0.5: C2, 1.0: "#e34948"}
    for lr in lrs:
        h = curves[lr]
        hh = h.copy(); hh[~np.isfinite(hh)] = np.nan
        lab = f"lr = {lr}" + ("  (diverged)" if not np.isfinite(h[-1]) else "")
        ax.plot(np.arange(1, len(hh) + 1), hh, color=cols[lr], label=lab)
    ax.axhline(opt, color=INK2, ls="--", lw=1, label="closed-form optimum")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_ylim(opt * 0.9, 1e6)
    ax.set_xlabel("Iteration (log)")
    ax.set_ylabel("Training MSE (log)")
    ax.set_title("(a) Training loss vs. iteration")
    ax.legend(fontsize=8, loc="upper right")
    ax = axes[1]
    for lr, col in [(0.01, C3), (0.1, C1)]:
        ax.plot(iter_grid, [it_res[str(lr)][n]["test_R2"] for n in iter_grid], marker="o", ms=5,
                color=col, label=f"lr = {lr}")
    ax.axhline(b3["closed_form_test_R2"], color=INK2, ls="--", lw=1, label="closed-form OLS")
    ax.set_xscale("log")
    ax.set_ylim(-0.6, 0.6)
    ax.set_xlabel("Number of training iterations (log)")
    ax.set_ylabel("Test R²")
    ax.set_title("(b) Final model quality vs. iteration budget")
    ax.legend(fontsize=8, loc="lower right")
    savefig(fig, "B3_learning_rate.png")

    save_results("B_linear_results.json", res)
    pd.DataFrame({"feature": feats, "coef_raw": cu, "coef_standardized": cs,
                  "train_std": scaler.scale_}).to_csv("../results/B_coefficients.csv", index=False)


if __name__ == "__main__":
    main()
