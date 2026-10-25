"""Builds the PDF lab report (English + Turkish) from results/*.json and figures/*.png."""
import json
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from common import FIG_DIR, RES_DIR, ROOT

FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DV-B", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DV-I", FD + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("DV-BI", FD + "DejaVuSans-BoldOblique.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

BLUE = colors.HexColor("#1f4e8c")
ST = {
    "title": ParagraphStyle("t", fontName="DV-B", fontSize=20, leading=25, alignment=TA_CENTER, textColor=BLUE),
    "sub": ParagraphStyle("s", fontName="DV", fontSize=11.5, leading=16, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=14, leading=18, spaceBefore=10, spaceAfter=6, textColor=BLUE),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=4, textColor=BLUE),
    "p": ParagraphStyle("p", fontName="DV", fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=5),
    "q": ParagraphStyle("q", fontName="DV", fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=5,
                        leftIndent=12),
    "cap": ParagraphStyle("c", fontName="DV-I", fontSize=8.5, leading=11.5, alignment=TA_JUSTIFY, spaceAfter=8,
                          textColor=colors.HexColor("#333333")),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=8.3, leading=10.5),
    "cellb": ParagraphStyle("cellb", fontName="DV-B", fontSize=8.3, leading=10.5, textColor=colors.white),
}


def load():
    R = {}
    for k, f in [("A", "A_summary.json"), ("B", "B_linear_results.json"), ("C", "C_logistic_results.json")]:
        with open(os.path.join(RES_DIR, f), encoding="utf-8") as fh:
            R[k] = json.load(fh)
    return R


def P(t, s="p"):
    return Paragraph(t, ST[s])


def table(rows, widths, header=True):
    data = [[Paragraph(str(c), ST["cellb"] if (header and i == 0) else ST["cell"]) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    sty = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if header:
        sty.append(("BACKGROUND", (0, 0), (-1, 0), BLUE))
        for i in range(2, len(rows), 2):
            sty.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f1f4f9")))
    t.setStyle(TableStyle(sty))
    return t


def fig(name, caption, width=17.0):
    from PIL import Image as PI
    path = os.path.join(FIG_DIR, name)
    w, h = PI.open(path).size
    return KeepTogether([Image(path, width=width * cm, height=width * cm * h / w), Spacer(1, 3), P(caption, "cap")])


def f3(x):
    return f"{x:.3f}"


def f2(x):
    return f"{x:.2f}"


# --------------------------------------------------------------------------------------------
def build(lang):
    R = load()
    A, B, C = R["A"], R["B"], R["C"]
    T = TEXT[lang](A, B, C)
    out = os.path.join(ROOT, "report", T["filename"])
    os.makedirs(os.path.dirname(out), exist_ok=True)

    def footer(canv, doc):
        canv.saveState()
        canv.setFont("DV", 7.5)
        canv.setFillColor(colors.grey)
        canv.drawString(2 * cm, 1.2 * cm, T["footer"])
        canv.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"{doc.page}")
        canv.restoreState()

    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title=T["doc_title"], author="")
    story = []
    for kind, *args in T["story"]:
        if kind == "title":
            story += [Spacer(1, 3.2 * cm), P(args[0], "title"), Spacer(1, 10), P(args[1], "sub"), Spacer(1, 1.2 * cm)]
        elif kind == "h1":
            story.append(P(args[0], "h1"))
        elif kind == "h2":
            story.append(P(args[0], "h2"))
        elif kind == "p":
            story.append(P(args[0]))
        elif kind == "q":
            story.append(P(args[0], "q"))
        elif kind == "table":
            story += [table(*args), Spacer(1, 6)]
        elif kind == "tcap":
            story.append(P(args[0], "cap"))
        elif kind == "fig":
            story.append(fig(*args))
        elif kind == "sp":
            story.append(Spacer(1, args[0]))
        elif kind == "pb":
            story.append(PageBreak())
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("saved", out)


# ============================================================================================
def common_numbers(A, B, C):
    b1, b2, b3 = B["B1"], B["B2"], B["B3"]
    c1, c2, c3 = C["C1"], C["C2"], C["C3"]
    feats = list(b1["coef"].keys())
    return dict(b1=b1, b2=b2, b3=b3, c1=c1, c2=c2, c3=c3, feats=feats, gd=b2["gd"], runs=b3["runs"])


def tables(A, B, C, L):
    """Language-neutral tables with localised headers. L = dict of header labels."""
    n = common_numbers(A, B, C)
    b1, b2, c1, c2, c3 = n["b1"], n["b2"], n["c1"], n["c2"], n["c3"]
    reg = A["regression"]
    t = {}
    desc_names = L["reg_feat_desc"]
    rows = [L["h_feat"]]
    for f in n["feats"] + ["target"]:
        d = reg["describe"][f]
        r = reg["corr_with_target"].get(f)
        rows.append([f, desc_names[f], f2(d["mean"]), f2(d["std"]), f2(d["min"]), f2(d["max"]),
                     "—" if r is None else f2(r)])
    t["A_reg"] = (rows, [1.3, 6.2, 1.6, 1.6, 1.6, 1.6, 1.4])
    rows = [L["h_feat_c"]]
    for f, d in A["classification"]["describe"].items():
        rows.append([f, L["clf_feat_desc"][f], f"{d['mean']:.3f}", f"{d['std']:.3f}", f"{d['min']:.3f}",
                     f"{d['max']:.3f}"])
    t["A_clf"] = (rows, [3.3, 6.5, 1.8, 1.8, 1.8, 1.8])

    rows = [L["h_coef"]]
    for f in n["feats"]:
        rows.append([f, f"{b2['unscaled']['coef'][f]:.3f}", f"{b2['standardized']['coef'][f]:.2f}",
                     f"{b2['scaler_std'][f]:.2f}"])
    rows.append([L["intercept"], f"{b2['unscaled']['intercept']:.2f}", f"{b2['standardized']['intercept']:.2f}", "—"])
    t["B_coef"] = (rows, [3.0, 4.4, 4.4, 4.4])

    rows = [L["h_metrics"],
            [L["train"], f2(b1["train"]["MAE"]), f2(b1["train"]["MSE"]), f2(b1["train"]["RMSE"]), f3(b1["train"]["R2"])],
            [L["test"], f2(b1["test"]["MAE"]), f2(b1["test"]["MSE"]), f2(b1["test"]["RMSE"]), f3(b1["test"]["R2"])],
            [L["mean_pred"], f2(b1["baseline_mean_predictor_test"]["MAE"]), f2(b1["baseline_mean_predictor_test"]["MSE"]),
             f2(b1["baseline_mean_predictor_test"]["RMSE"]), f3(b1["baseline_mean_predictor_test"]["R2"])]]
    t["B_metrics"] = (rows, [5.2, 2.8, 2.8, 2.8, 2.8])

    gd = n["gd"]
    rows = [L["h_scaling"],
            [L["ols_raw"], f2(b2["unscaled"]["test"]["MAE"]), f2(b2["unscaled"]["test"]["MSE"]), f3(b2["unscaled"]["test"]["R2"]), "—"],
            [L["ols_std"], f2(b2["standardized"]["test"]["MAE"]), f2(b2["standardized"]["test"]["MSE"]), f3(b2["standardized"]["test"]["R2"]), "—"],
            [L["gd_raw"].format(lr=f"{gd['lr_unscaled']:.1e}"), f2(gd["test_unscaled"]["MAE"]), f2(gd["test_unscaled"]["MSE"]),
             f3(gd["test_unscaled"]["R2"]), f2(gd["final_train_mse_unscaled"])],
            [L["gd_std"], f2(gd["test_scaled"]["MAE"]), f2(gd["test_scaled"]["MSE"]), f3(gd["test_scaled"]["R2"]),
             f2(gd["final_train_mse_scaled"])]]
    t["B_scaling"] = (rows, [6.0, 2.4, 2.4, 2.2, 3.4])

    rows = [L["h_lr"]]
    for lr, r in n["runs"].items():
        if r["diverged"]:
            rows.append([lr, L["diverged"], "—", "—", "—"])
        else:
            it = r["iter_to_within_1pct_of_optimum"]
            rows.append([lr, L["converged"] if it else L["not_conv"], f2(r["final_train_mse"]),
                         str(it) if it else L["gt"].format(n=n["b3"]["iterations"]), f3(r["test"]["R2"])])
    t["B_lr"] = (rows, [2.0, 4.2, 3.0, 4.0, 2.6])

    ie = n["b3"]["iterations_effect"]
    rows = [L["h_iter"]]
    for k in ["10", "50", "100", "500", "2000", "5000"]:
        rows.append([k, f2(ie["0.01"][k]["train_MSE"]), f3(ie["0.01"][k]["test_R2"]), f2(ie["0.1"][k]["train_MSE"]),
                     f3(ie["0.1"][k]["test_R2"]), f2(ie["0.1"][k]["coef_s1"])])
    rows.append([L["closed"], f2(gd["closed_form_train_mse"]), f3(n["b3"]["closed_form_test_R2"]),
                 f2(gd["closed_form_train_mse"]), f3(n["b3"]["closed_form_test_R2"]), f2(n["b3"]["closed_form_coef_s1"])])
    t["B_iter"] = (rows, [2.4, 2.9, 2.6, 2.9, 2.6, 3.0])

    rows = [L["h_logcoef"]]
    for f in C["features_C1"]:
        rows.append([f, f"{c1['coef_standardized'][f]:.3f}", f"{c1['odds_ratio_per_std'][f]:.2f}",
                     f"{c1['coef_raw_units'][f]:.3f}", f"{c1['train_std'][f]:.4f}"])
    rows.append([L["intercept"], f"{c1['intercept_standardized']:.3f}", "—", f"{c1['intercept_raw_units']:.3f}", "—"])
    t["C_coef"] = (rows, [3.6, 3.2, 3.2, 3.4, 3.2])

    def mrow(name, m):
        return [name, f3(m["accuracy"]), f3(m["precision"]), f3(m["recall"]), f3(m["f1"]),
                str(m["TN"]), str(m["FP"]), str(m["FN"]), str(m["TP"])]
    m = c1["test@0.5"]
    t["C_metrics"] = ([L["h_clf"], mrow(L["test"] + " (t = 0.5)", m)], [3.6, 1.7, 1.7, 1.7, 1.7, 1.4, 1.4, 1.4, 1.4])
    rows = [L["h_clf"]]
    for th in ["0.3", "0.5", "0.7"]:
        rows.append(mrow(f"{L['train_cv']}, t = {th}", c2["train_cv"][th]))
    for th in ["0.3", "0.5", "0.7"]:
        rows.append(mrow(f"{L['test']}, t = {th}", c2["test"][th]))
    t["C_thr"] = (rows, [3.6, 1.7, 1.7, 1.7, 1.7, 1.4, 1.4, 1.4, 1.4])
    rows = [L["h_c3"]]
    for k, nm in [("one_feature", L["one_f"]), ("two_features", L["two_f"])]:
        r = c3[k]
        mm = r["test@0.5"]
        rows.append([nm, f3(mm["accuracy"]), f3(mm["precision"]), f3(mm["recall"]), f3(mm["f1"]),
                     f3(r["test_auc"]), f3(r["test_logloss"]), str(mm["FP"]), str(mm["FN"])])
    rows.append([L["five_f"], f3(c1["test@0.5"]["accuracy"]), f3(c1["test@0.5"]["precision"]),
                 f3(c1["test@0.5"]["recall"]), f3(c1["test@0.5"]["f1"]), f3(c1["test_auc"]), f3(c1["test_logloss"]),
                 str(c1["test@0.5"]["FP"]), str(c1["test@0.5"]["FN"])])
    t["C_c3"] = (rows, [4.4, 1.6, 1.6, 1.6, 1.5, 1.6, 1.7, 1.0, 1.0])
    return n, t


# ============================================================================================
REG_DESC_EN = {"age": "Age (years)", "sex": "Sex (coded 1 / 2)", "bmi": "Body-mass index (kg/m²)",
               "bp": "Average blood pressure (mm Hg)", "s1": "tc – total serum cholesterol",
               "s2": "ldl – low-density lipoproteins", "s3": "hdl – high-density lipoproteins",
               "s4": "tch – total cholesterol / HDL", "s5": "ltg – log of serum triglycerides",
               "s6": "glu – blood sugar level", "target": "Disease progression one year after baseline"}
REG_DESC_TR = {"age": "Yaş (yıl)", "sex": "Cinsiyet (1 / 2 kodlu)", "bmi": "Vücut kitle indeksi (kg/m²)",
               "bp": "Ortalama kan basıncı (mm Hg)", "s1": "tc – toplam serum kolesterolü",
               "s2": "ldl – düşük yoğunluklu lipoprotein", "s3": "hdl – yüksek yoğunluklu lipoprotein",
               "s4": "tch – toplam kolesterol / HDL", "s5": "ltg – serum trigliseridinin logaritması",
               "s6": "glu – kan şekeri", "target": "Başlangıçtan 1 yıl sonraki hastalık ilerlemesi"}
CLF_DESC_EN = {"mean radius": "Mean distance from centre to perimeter of nuclei",
               "mean texture": "Std. dev. of grey-scale values",
               "mean smoothness": "Local variation in radius lengths",
               "mean concave points": "Number of concave portions of the contour",
               "mean symmetry": "Symmetry of the nucleus"}
CLF_DESC_TR = {"mean radius": "Çekirdek merkezinden çevreye ortalama uzaklık",
               "mean texture": "Gri seviye değerlerinin standart sapması",
               "mean smoothness": "Yarıçap uzunluklarındaki yerel değişim",
               "mean concave points": "Kontürdeki içbükey bölge sayısı",
               "mean symmetry": "Çekirdeğin simetrisi"}

L_EN = dict(
    reg_feat_desc=REG_DESC_EN, clf_feat_desc=CLF_DESC_EN,
    h_feat=["Var.", "Description", "Mean", "Std", "Min", "Max", "r(y)"],
    h_feat_c=["Feature", "Description", "Mean", "Std", "Min", "Max"],
    h_coef=["Feature", "Coefficient – raw units", "Coefficient – standardised", "Training std. dev."],
    intercept="Intercept", h_metrics=["Model / data", "MAE", "MSE", "RMSE", "R²"], train="Training set",
    test="Test set", mean_pred="Test set – mean-only baseline",
    h_scaling=["Condition", "Test MAE", "Test MSE", "Test R²", "Final train MSE"],
    ols_raw="OLS, no scaling", ols_std="OLS, standardised",
    gd_raw="Grad. descent, no scaling (lr = {lr}, 5000 it.)", gd_std="Grad. descent, standardised (lr = 0.1, 5000 it.)",
    h_lr=["Learning rate", "Behaviour", "Final train MSE", "Iterations to ≤1 % of optimum", "Test R²"],
    diverged="Diverged (loss → ∞)", converged="Converged", not_conv="Not converged", gt="> {n}",
    h_iter=["Iterations", "Train MSE (lr 0.01)", "Test R² (lr 0.01)", "Train MSE (lr 0.1)", "Test R² (lr 0.1)",
            "s1 coef. (lr 0.1)"], closed="Closed form",
    h_logcoef=["Feature", "β (standardised)", "Odds ratio e<super>β</super> per 1 SD", "β (raw units)", "Training SD"],
    h_clf=["Setting", "Acc.", "Prec.", "Recall", "F1", "TN", "FP", "FN", "TP"], train_cv="Train 5-fold CV",
    h_c3=["Model (test set, t = 0.5)", "Acc.", "Prec.", "Recall", "F1", "ROC-AUC", "Log-loss", "FP", "FN"],
    one_f="1 feature: radius", two_f="2 features: radius + texture", five_f="Reference: 5 features (C1)",
)
L_TR = dict(
    reg_feat_desc=REG_DESC_TR, clf_feat_desc=CLF_DESC_TR,
    h_feat=["Değ.", "Açıklama", "Ort.", "Std", "Min", "Maks", "r(y)"],
    h_feat_c=["Öznitelik", "Açıklama", "Ort.", "Std", "Min", "Maks"],
    h_coef=["Öznitelik", "Katsayı – ham birim", "Katsayı – standartlaştırılmış", "Eğitim std. sapması"],
    intercept="Sabit terim (intercept)", h_metrics=["Model / veri", "MAE", "MSE", "RMSE", "R²"],
    train="Eğitim kümesi", test="Test kümesi", mean_pred="Test – yalnızca ortalama tahmini",
    h_scaling=["Koşul", "Test MAE", "Test MSE", "Test R²", "Son eğitim MSE"],
    ols_raw="OLS, ölçeklemesiz", ols_std="OLS, standartlaştırılmış",
    gd_raw="Gradyan inişi, ölçeklemesiz (lr = {lr}, 5000 it.)",
    gd_std="Gradyan inişi, standartlaştırılmış (lr = 0.1, 5000 it.)",
    h_lr=["Öğrenme oranı", "Davranış", "Son eğitim MSE", "Optimumun %1'ine iterasyon", "Test R²"],
    diverged="Iraksadı (kayıp → ∞)", converged="Yakınsadı", not_conv="Yakınsamadı", gt="> {n}",
    h_iter=["İterasyon", "Eğitim MSE (lr 0.01)", "Test R² (lr 0.01)", "Eğitim MSE (lr 0.1)", "Test R² (lr 0.1)",
            "s1 katsayısı (lr 0.1)"], closed="Kapalı form",
    h_logcoef=["Öznitelik", "β (standart)", "1 SS başına odds oranı e<super>β</super>", "β (ham birim)", "Eğitim SS"],
    h_clf=["Ayar", "Doğr.", "Kesin.", "Duyarl.", "F1", "TN", "FP", "FN", "TP"], train_cv="Eğitim 5-kat ÇD",
    h_c3=["Model (test, t = 0.5)", "Doğr.", "Kesin.", "Duyarl.", "F1", "ROC-AUC", "Log-loss", "FP", "FN"],
    one_f="1 öznitelik: radius", two_f="2 öznitelik: radius + texture", five_f="Referans: 5 öznitelik (C1)",
)


# ============================================================================================
def text_en(A, B, C):
    n, t = tables(A, B, C, L_EN)
    b1, b2, b3, gd, runs = n["b1"], n["b2"], n["b3"], n["gd"], n["runs"]
    c1, c2, c3 = n["c1"], n["c2"], n["c3"]
    reg, clf = A["regression"], A["classification"]
    m05 = c1["test@0.5"]
    ie = b3["iterations_effect"]
    ex = c1["examples"]
    s = [
        ("title", "Lab Assignment: Understanding Linear and Logistic Regression",
         "Machine Learning – Lab 1 Report<br/><br/>Student: ____________________ &nbsp;&nbsp; No: ______________<br/>"
         "Date: 24 October 2026"),
        ("p", "<b>Summary.</b> Two datasets were studied: the <i>Diabetes</i> dataset (442 patients, 10 clinical "
              "features, continuous target) for linear regression and the <i>Breast Cancer Wisconsin (Diagnostic)</i> "
              f"dataset (569 tumours, binary target) for logistic regression. The baseline linear model reaches a test "
              f"R² of {f3(b1['test']['R2'])} (MAE {f2(b1['test']['MAE'])}); standardisation leaves its predictions "
              f"unchanged but makes gradient descent converge roughly two orders of magnitude faster. A learning rate "
              f"of 0.1 converged fastest, 1.0 diverged. The five-feature logistic model reaches {f3(m05['accuracy'])} "
              f"accuracy and {f3(c1['test_auc'])} ROC-AUC on the test set; lowering the threshold to 0.3 trades "
              f"precision for recall, which is the preferred trade-off in cancer screening."),
        ("h2", "Reproducibility settings"),
        ("table", [["Item", "Setting"],
                   ["Software", "Python 3.13, scikit-learn 1.9.1, NumPy 2.5, pandas 3.0, Matplotlib 3.11"],
                   ["Linear models", "sklearn LinearRegression (closed-form least squares) + own NumPy batch "
                                     "gradient descent (loss = MSE/2, zero initialisation)"],
                   ["Logistic model", "sklearn LogisticRegression, solver = lbfgs, L2 penalty, C = 1.0, max_iter = 1000"],
                   ["Data split", "80 % training / 20 % test, random_state = 42 (stratified for classification)"],
                   ["Scaling", "StandardScaler fitted on the training set only, then applied to the test set"],
                   ["Model selection", "Threshold choice uses 5-fold cross-validation on the training set only; "
                                       "the test set is used only for the final evaluation"]], [3.5, 13.5]),
        ("pb",),
        # ---------------- PART A
        ("h1", "Part A — Dataset Selection"),
        ("h2", "A.1 Dataset 1 (linear regression): Diabetes"),
        ("p", "<b>Problem and source.</b> The Diabetes dataset of Efron, Hastie, Johnstone and Tibshirani (2004), "
              "distributed with scikit-learn (<i>load_diabetes(scaled=False)</i>, raw clinical units). For each of "
              f"{reg['n']} diabetes patients, ten baseline measurements were recorded; the target is a quantitative "
              f"measure of disease progression one year later (range {reg['target_min']:.0f}–{reg['target_max']:.0f}, "
              f"mean {reg['target_mean']:.1f}, std {reg['target_std']:.1f}). The task is to predict this progression score."),
        ("p", "<b>Features and target.</b> Inputs: age, sex, bmi, bp and six blood-serum measurements s1–s6 (Table 1). "
              "Target: disease progression (continuous)."),
        ("table",) + t["A_reg"],
        ("tcap", "Table 1. Diabetes dataset – variables, summary statistics and Pearson correlation r(y) with the target."),
        ("p", "<b>Why it is suitable.</b> The target is continuous, several features show a clear, roughly linear "
              f"relationship with it (bmi r = {reg['corr_with_target']['bmi']:.2f}, s5 r = "
              f"{reg['corr_with_target']['s5']:.2f}), there are more than 100 observations and more than two features. "
              "The features are also on very different scales (sex ≈ 1–2, s1 ≈ 97–301), which makes the dataset "
              "useful for the scaling experiment, and some features are strongly correlated with each other "
              "(s1 and s2), which helps to discuss coefficient interpretation."),
        ("fig", "A1_regression_eda.png", "Figure 1. (a) Body-mass index against disease progression with a "
                "least-squares line: higher BMI is associated with faster progression, but the scatter is large. "
                "(b) Correlation of every feature with the target; s3 (HDL, “good” cholesterol) is the only clearly "
                "negative relation."),
        ("p", f"<b>Preprocessing.</b> No missing values were found ({reg['missing']} missing cells). No outliers were "
              "removed because all values are physiologically plausible. The data were split 80/20 "
              f"({B['split']['train']} train / {B['split']['test']} test, random_state = 42). For the scaling and "
              "gradient-descent experiments the features were standardised (z = (x − μ)/σ) with μ and σ estimated on "
              "the training set only, to avoid information leakage from the test set."),
        ("h2", "A.2 Dataset 2 (logistic regression): Breast Cancer Wisconsin (Diagnostic)"),
        ("p", "<b>Problem and source.</b> UCI Machine Learning Repository dataset by Wolberg, Street and Mangasarian "
              f"(1995), shipped with scikit-learn (<i>load_breast_cancer</i>). Each of the {clf['n']} samples describes "
              "cell nuclei in a digitised image of a fine-needle aspirate of a breast mass with 30 real-valued "
              "features. The task is to classify the tumour as malignant or benign."),
        ("p", f"<b>Features and target.</b> Target: <i>malignant</i> = 1 ({clf['malignant']} samples, 37 %), benign = 0 "
              f"({clf['benign']}, 63 %). The original scikit-learn coding (0 = malignant) was inverted so that the "
              "positive class is the disease, which makes precision and recall medically meaningful. Five "
              "interpretable “mean” features were selected for the logistic experiments (Table 2)."),
        ("table",) + t["A_clf"],
        ("tcap", "Table 2. Selected features of the Breast Cancer dataset (all 569 samples)."),
        ("p", "<b>Why it is suitable.</b> The target is binary, classes are moderately imbalanced but not extreme, "
              "and Figure 2 shows that the classes are largely – but not perfectly – separable by a linear boundary, "
              "which is exactly the situation logistic regression is designed for. The overlap region provides "
              "realistic errors to analyse."),
        ("fig", "A2_classification_eda.png", "Figure 2. (a) Mean radius vs. mean texture coloured by diagnosis: "
                "malignant tumours tend to be larger and more textured, with an overlap zone around radius 13–16 mm. "
                "(b) Distribution of mean concave points: the two classes are well separated, so this feature is "
                "expected to receive a large coefficient."),
        ("p", f"<b>Preprocessing.</b> No missing values ({clf['missing']}). Stratified 80/20 split "
              f"({C['split']['train']} train / {C['split']['test']} test; {C['split']['test_malignant']} malignant in "
              "test) so that both sets keep the 37/63 class ratio. Features were standardised inside a scikit-learn "
              "Pipeline (scaler fitted on training folds only) because the raw features differ by three orders of "
              "magnitude (radius ≈ 14 vs. smoothness ≈ 0.1) and L2 regularisation penalises all coefficients equally."),
        ("pb",),
        # ---------------- PART B
        ("h1", "Part B — Linear Regression"),
        ("h2", "Experiment B1 — Model parameters and predictions"),
        ("p", "A baseline ordinary-least-squares model ŷ = b + Σ w<sub>j</sub>x<sub>j</sub> was trained on the raw "
              "(unscaled) features. Coefficients are listed in Table 4 (column “raw units”) and the error metrics in Table 3."),
        ("table",) + t["B_metrics"],
        ("tcap", "Table 3. B1 error metrics. The mean-only baseline always predicts the training mean."),
        ("fig", "B1_actual_vs_predicted.png", "Figure 3. B1 – (a) actual vs. predicted progression for training "
                "(light) and test (dark) points; points on the dashed line would be perfect. (b) Test residuals: "
                "no strong pattern, but the spread grows for larger predictions and high actual values are under-predicted."),
        ("p", "<b>1. What do the coefficients and intercept represent?</b> Each coefficient is the expected change in "
              "disease progression for a one-unit increase in that feature while all other features are held "
              f"constant. For example, w<sub>bmi</sub> = {b1['coef']['bmi']:.2f}: one extra kg/m² of BMI adds about "
              f"{b1['coef']['bmi']:.1f} progression points; w<sub>bp</sub> = {b1['coef']['bp']:.2f} per mm Hg; "
              f"w<sub>s5</sub> = {b1['coef']['s5']:.1f} per unit of log-triglycerides; w<sub>sex</sub> = "
              f"{b1['coef']['sex']:.1f} means the group coded 2 progresses about {abs(b1['coef']['sex']):.0f} points "
              f"less than group 1 with equal other values. The intercept ({b1['intercept']:.1f}) is the prediction "
              "when every feature equals zero – a point that is outside the data (nobody has BMI = 0 or blood "
              "pressure = 0), so it has no direct medical meaning; it only positions the regression plane."),
        ("p", "<b>2. How do the features influence predictions?</b> Raw coefficients cannot be compared directly "
              "because the units differ. Using the standardised coefficients (B2, Table 4) the most influential "
              f"features are s1 ({b2['standardized']['coef']['s1']:.1f}), s5 ({b2['standardized']['coef']['s5']:.1f}), "
              f"bmi ({b2['standardized']['coef']['bmi']:.1f}), s2 ({b2['standardized']['coef']['s2']:.1f}) and bp "
              f"({b2['standardized']['coef']['bp']:.1f}) per standard deviation; age and s6 have almost no effect once "
              "the others are known. Note that s1 has a positive correlation with the target (r = 0.21) but a large "
              "negative coefficient: s1 (total cholesterol) and s2 (LDL) are strongly correlated, so the model uses the "
              "difference between them. Coefficients therefore describe partial effects, not simple correlations."),
        ("p", f"<b>3. How accurately does it predict unseen data?</b> On the test set R² = {f3(b1['test']['R2'])}: the model "
              f"explains about {b1['test']['R2'] * 100:.0f} % of the variance of disease progression. The typical error is "
              f"MAE ≈ {b1['test']['MAE']:.0f} points (RMSE ≈ {b1['test']['RMSE']:.0f}) on a target whose standard deviation "
              f"is {reg['target_std']:.0f}. This is a clear improvement over the mean-only baseline (MAE "
              f"{b1['baseline_mean_predictor_test']['MAE']:.0f}, R² ≈ 0) but far from exact. Train and test errors are "
              f"similar (R² {f3(b1['train']['R2'])} vs. {f3(b1['test']['R2'])}), so the model is not overfitting; it is "
              "limited by the information in ten baseline measurements and by non-linear effects (Figure 3b shows that "
              "patients with very high progression are systematically under-predicted)."),
        ("h2", "Experiment B2 — Feature scaling"),
        ("p", "The OLS model was trained twice: on raw features and on standardised features (scaler fitted on the "
              "training set). In addition, to show the effect of scaling on the <i>training process</i>, the same "
              "linear model was trained with batch gradient descent (GD) for 5000 iterations under both conditions, "
              "each with the largest practical stable learning rate."),
        ("table",) + t["B_coef"],
        ("tcap", "Table 4. OLS coefficients before and after standardisation. Standardised coefficient = raw "
                 "coefficient × training standard deviation of the feature (e.g. bmi: 5.85 × 4.38 ≈ 25.6)."),
        ("table",) + t["B_scaling"],
        ("tcap", "Table 5. Test performance with and without scaling. The OLS optimum training MSE is "
                 f"{gd['closed_form_train_mse']:.2f}."),
        ("fig", "B2_scaling_comparison.png", "Figure 4. B2 – (a) coefficients in raw units and after "
                "standardisation; (b) training loss of gradient descent with and without scaling. Unscaled GD is "
                "still far from the optimum after 5000 iterations, while scaled GD reaches it after ~60 iterations."),
        ("p", "<b>1. How do the coefficients change?</b> Each coefficient is multiplied by its feature's standard "
              "deviation, and the intercept becomes the training mean of the target "
              f"({b2['standardized']['intercept']:.1f}) because all scaled features have mean zero. After scaling the "
              f"coefficients are comparable: s5 goes from {b2['unscaled']['coef']['s5']:.1f} to "
              f"{b2['standardized']['coef']['s5']:.1f} (s5 has a small std of 0.52), while s1 goes from "
              f"{b2['unscaled']['coef']['s1']:.2f} to {b2['standardized']['coef']['s1']:.1f} (s1 has a large std of "
              "34.6). The ranking of importance changes completely; the signs never change."),
        ("p", "<b>2. Does scaling change prediction accuracy?</b> For closed-form OLS – no. The largest difference "
              f"between the two models' test predictions is {b2['max_abs_prediction_difference']:.1e}, i.e. numerical "
              "round-off; MAE, MSE and R² are identical. Standardisation is an invertible linear transformation, and "
              "an unregularised linear model can absorb it into its weights. For gradient descent it <i>does</i> "
              f"matter in practice: after the same 5000 iterations unscaled GD reached test R² {f3(gd['test_unscaled']['R2'])} "
              f"against {f3(gd['test_scaled']['R2'])} for scaled GD."),
        ("p", "<b>3. Why is scaling important?</b> The speed of gradient descent is governed by the shape of the "
              "loss surface. Without scaling, the Hessian (1/n)XᵀX has largest eigenvalue "
              f"λ<sub>max</sub> ≈ {gd['lambda_max_unscaled']:.0f} and condition number ≈ {gd['cond_unscaled']:.1e}; the "
              f"surface is a very long, narrow valley. The step must stay below 2/λ<sub>max</sub> ≈ "
              f"{2 / gd['lambda_max_unscaled']:.1e} to be stable (a “normal” lr = 10<super>-4</super> diverged after "
              f"{gd['unscaled_lr_1e-4_diverged_at_iter']} iterations), and such a tiny step makes progress along the "
              "flat directions extremely slow. After standardisation λ<sub>max</sub> ≈ "
              f"{gd['lambda_max_scaled']:.2f} and the condition number drops to ≈ {gd['cond_scaled']:.0f}, so a "
              "single learning rate suits all directions. Scaling is also essential for regularised models (L1/L2 "
              "penalties treat all coefficients equally), for distance-based methods (k-NN, SVM, k-means) and for "
              "comparing coefficient magnitudes."),
        ("h2", "Experiment B3 — Learning rate and convergence"),
        ("p", "Batch gradient descent was run on the standardised training data with five learning rates "
              "(0.001, 0.01, 0.1, 0.5, 1.0), zero initialisation and 2000 iterations; everything else was kept "
              f"constant. The theoretical stability limit is 2/λ<sub>max</sub> = {b3['lr_stability_limit']:.3f}."),
        ("fig", "B3_learning_rate.png", "Figure 5. B3 – (a) training MSE vs. iteration for five learning rates "
                "(log–log axes); lr = 1.0 exceeds the stability limit and diverges. (b) Test R² of the model obtained "
                "after a given number of iterations for lr = 0.01 and lr = 0.1."),
        ("table",) + t["B_lr"],
        ("tcap", "Table 6. Learning-rate comparison after 2000 iterations."),
        ("table",) + t["B_iter"],
        ("tcap", "Table 7. Effect of the iteration budget (standardised data). The last column follows the s1 "
                 "coefficient, which converges very slowly."),
        ("p", "<b>1. Fastest stable convergence.</b> lr = 0.1 reached the optimum fastest "
              f"({runs['0.1']['iter_to_within_1pct_of_optimum']} iterations to come within 1 % of the optimal training "
              f"MSE). lr = 0.5 is larger but needed {runs['0.5']['iter_to_within_1pct_of_optimum']} iterations: it is "
              f"just below the stability limit ({b3['lr_stability_limit']:.3f}), so the loss first jumps and the weights "
              "oscillate along the steep direction before settling (visible as the kink in Figure 5a). "
              "It does, however, reach the closest final value after 2000 iterations."),
        ("p", f"<b>2. Too small / too large.</b> With lr = 0.001 the loss decreases monotonically but very slowly; "
              f"after 2000 iterations the training MSE is still {runs['0.001']['final_train_mse']:.0f} and the test R² "
              f"only {f3(runs['0.001']['test']['R2'])} – the model is under-trained. With lr = 1.0 each step overshoots "
              "the minimum by more than it corrects, the error grows geometrically and the loss explodes after a few "
              "iterations (divergence)."),
        ("p", "<b>3. Number of iterations.</b> With too few iterations the model is poor (lr = 0.1, 10 iterations: "
              f"test R² {f3(ie['0.1']['10']['test_R2'])}). The test error stabilises after ≈ 50 iterations for lr = 0.1 "
              "and ≈ 500 for lr = 0.01. Beyond that point the training loss keeps falling slowly while the coefficients "
              f"of the correlated pair s1/s2 are still changing (s1: {ie['0.1']['500']['coef_s1']:.1f} at 500 iterations, "
              f"{ie['0.1']['5000']['coef_s1']:.1f} at 5000, {b3['closed_form_coef_s1']:.1f} in closed form). Interestingly "
              f"the partially trained models have slightly <i>higher</i> test R² ({f3(ie['0.1']['100']['test_R2'])}) than the "
              f"exact solution ({f3(b3['closed_form_test_R2'])}): stopping early acts as implicit regularisation (see Part D)."),
        ("pb",),
        # ---------------- PART C
        ("h1", "Part C — Logistic Regression"),
        ("h2", "Experiment C1 — Model parameters and classification"),
        ("p", "A logistic regression model P(y = 1 | x) = σ(b + Σ w<sub>j</sub>x<sub>j</sub>), σ(z) = 1/(1 + e<super>−z</super>), "
              "was trained on the five standardised features of Table 2 and evaluated with threshold 0.5."),
        ("table",) + t["C_coef"],
        ("tcap", "Table 8. Logistic regression coefficients. Raw-unit β = standardised β / training SD."),
        ("table",) + t["C_metrics"],
        ("tcap", f"Table 9. C1 test performance (n = {C['split']['test']}). ROC-AUC = {f3(c1['test_auc'])}, "
                 f"log-loss = {f3(c1['test_logloss'])}, training accuracy = {f3(c1['train_accuracy'])}."),
        ("fig", "C1_confusion_matrix.png", "Figure 6. C1 – (a) confusion matrix on the test set at threshold 0.5. "
                "(b) Histogram of the predicted probabilities, i.e. the model output before thresholding; most "
                "samples get probabilities near 0 or 1, the errors come from the few samples in the middle."),
        ("p", "<b>1. Output before the threshold.</b> The model first computes a linear score (log-odds) "
              "z = b + wᵀx, which can be any real number, and then the sigmoid converts it into a probability in "
              "(0, 1). Three test patients illustrate this: z = "
              f"{ex[0]['z']:.2f} → p = {ex[0]['p']:.4f} (benign, correct); z = {ex[1]['z']:.2f} → p = {ex[1]['p']:.5f} "
              f"(malignant, correct); z = {ex[2]['z']:.2f} → p = {ex[2]['p']:.2f} (actually benign, but just above "
              "0.5, so it becomes a false positive). The class label only appears after the threshold is applied."),
        ("p", "<b>2. Effect of coefficients.</b> A coefficient is the change in log-odds per unit increase of the "
              "feature; e<super>β</super> is the corresponding odds ratio. All five coefficients are positive, so larger, "
              "rougher, more concave and less symmetric nuclei all increase the malignancy probability. "
              f"Per standard deviation, mean radius multiplies the odds by {c1['odds_ratio_per_std']['mean radius']:.1f}, "
              f"concave points by {c1['odds_ratio_per_std']['mean concave points']:.1f}, texture by "
              f"{c1['odds_ratio_per_std']['mean texture']:.1f}, while symmetry ({c1['odds_ratio_per_std']['mean symmetry']:.2f}) "
              "contributes little. The effect on probability is non-linear: the same Δz changes p strongly near "
              "p = 0.5 but hardly at all when p is already close to 0 or 1. The negative intercept "
              f"({c1['intercept_standardized']:.2f}) reflects that a tumour with average features is more likely benign "
              f"(σ({c1['intercept_standardized']:.2f}) ≈ 0.34, close to the 37 % prior)."),
        ("p", f"<b>3. Error types.</b> The model makes {m05['FP']} false positives (benign predicted as malignant) and "
              f"{m05['FN']} false negatives (malignant tumours missed). All {m05['FP'] + m05['FN']} errors are "
              "“borderline” tumours: the misclassified samples have mean radius between 13.4 and 16.2 mm, exactly in "
              "the overlap zone of Figure 2a. False positives are benign tumours that are large or highly textured "
              "(e.g. radius 13.4 mm, texture 30.7), while two of the false negatives are malignant tumours with "
              "concave points at or below the dataset average of 0.049 (0.041 and 0.051), so they look benign on the features used. In this "
              "application a false negative (missed cancer) is far more costly than a false positive (an extra biopsy)."),
        ("h2", "Experiment C2 — Decision threshold"),
        ("p", "The probabilities of the C1 model were re-used without retraining and thresholded at 0.3, 0.5 and 0.7. "
              "To respect the rule that the test set must not be used for configuration choices, the threshold was "
              "<i>selected</i> on 5-fold cross-validated (out-of-fold) probabilities of the training set; the test "
              "values are reported for evaluation only."),
        ("table",) + t["C_thr"],
        ("tcap", "Table 10. Effect of the threshold (training cross-validation and test set)."),
        ("fig", "C2_threshold.png", "Figure 7. C2 – (a) precision and recall on the test set for every threshold "
                "from 0.05 to 0.95; markers show 0.3, 0.5 and 0.7. (b) Number of false positives and false negatives "
                "at the three thresholds."),
        ("p", f"<b>1. Effect on FP and FN.</b> Lowering the threshold labels more samples as malignant: at 0.3 the "
              f"test set has {c2['test']['0.3']['FP']} FP and {c2['test']['0.3']['FN']} FN; at 0.5 "
              f"{c2['test']['0.5']['FP']} FP and {c2['test']['0.5']['FN']} FN; at 0.7 {c2['test']['0.7']['FP']} FP and "
              f"{c2['test']['0.7']['FN']} FN. False positives and false negatives move in opposite directions – the "
              "threshold only redistributes errors, it does not make the model better at separating the classes."),
        ("p", f"<b>2. Precision and recall.</b> Increasing the threshold raises precision "
              f"({f3(c2['test']['0.3']['precision'])} → {f3(c2['test']['0.5']['precision'])} → "
              f"{f3(c2['test']['0.7']['precision'])}) and lowers recall ({f3(c2['test']['0.3']['recall'])} → "
              f"{f3(c2['test']['0.5']['recall'])} → {f3(c2['test']['0.7']['recall'])}). The curves are step functions "
              "because the test set is small: each step is a single sample crossing the threshold. Accuracy is "
              "highest at 0.5 and F1 changes little, so these metrics hide the clinically important trade-off."),
        ("p", "<b>3. Selected threshold: 0.3.</b> For cancer screening a missed malignancy is much more dangerous "
              "than a false alarm, so recall is the priority. On the training cross-validation, 0.3 increases recall "
              f"from {f3(c2['train_cv']['0.5']['recall'])} to {f3(c2['train_cv']['0.3']['recall'])} (19 → 10 missed "
              "cancers out of 170) at the cost of 17 additional false alarms. The test set confirms the choice: recall "
              f"{f3(c2['test']['0.3']['recall'])}, only {c2['test']['0.3']['FN']} missed cancers out of "
              f"{C['split']['test_malignant']}. A threshold of 0.7 would be appropriate only if false positives were "
              "the expensive error (e.g. before an invasive treatment decision)."),
        ("h2", "Experiment C3 — Features and decision boundary"),
        ("p", "Two models were trained on the same split: one using only <i>mean radius</i>, and one using "
              "<i>mean radius</i> and <i>mean texture</i>. These two features were chosen because they are visually "
              "interpretable and only weakly correlated, so the second feature adds new information."),
        ("table",) + t["C_c3"],
        ("tcap", "Table 11. One vs. two features (test set, threshold 0.5). The five-feature C1 model is shown as a reference."),
        ("fig", "C3_decision_boundary.png", "Figure 8. C3 – (a) the one-feature model is a sigmoid along the radius "
                f"axis; its decision boundary is the single point radius = {c3['one_feature']['decision_point_raw']:.1f} mm. "
                "(b) The two-feature model in standardised coordinates (z-scores): background colour = predicted "
                "probability, solid line = decision boundary p = 0.5, dotted lines = p = 0.3 and 0.7; small faint "
                "points are training data, large points are test data, circled points are misclassified."),
        ("p", f"<b>1. Effect of the second feature.</b> Adding texture improved every metric: accuracy "
              f"{f3(c3['one_feature']['test@0.5']['accuracy'])} → {f3(c3['two_features']['test@0.5']['accuracy'])}, "
              f"recall {f3(c3['one_feature']['test@0.5']['recall'])} → {f3(c3['two_features']['test@0.5']['recall'])}, "
              f"ROC-AUC {f3(c3['one_feature']['test_auc'])} → {f3(c3['two_features']['test_auc'])}, log-loss "
              f"{f3(c3['one_feature']['test_logloss'])} → {f3(c3['two_features']['test_logloss'])}. The gain in accuracy is "
              "only one test sample, but the improvement in AUC and log-loss shows that the probabilities became "
              "better ranked and better calibrated. The texture coefficient "
              f"({c3['two_features']['coef_standardized'][1]:.2f}) is much smaller than the radius coefficient "
              f"({c3['two_features']['coef_standardized'][0]:.2f}), i.e. texture is a secondary signal. With five "
              f"features (C1) accuracy reaches {f3(m05['accuracy'])}, mainly thanks to concave points."),
        ("p", "<b>2. What the boundary represents.</b> The decision boundary is the set of points where the model is "
              "undecided: P = 0.5, i.e. b + w<sub>1</sub>x<sub>1</sub> + w<sub>2</sub>x<sub>2</sub> = 0. For "
              "logistic regression it is always a straight line (a hyperplane in more dimensions). Its slope shows "
              "the trade-off between features: a tumour with a smaller radius can still be classified as malignant "
              "if its texture is high enough. The p = 0.3 and p = 0.7 lines are parallel to it, so changing the "
              "threshold (C2) shifts the boundary without rotating it."),
        ("p", "<b>3. Difficult observations.</b> Samples close to the boundary are hard to classify. Of the "
              f"{c3['two_features']['n_within_0.5std_of_boundary']} test samples within 0.5 standard deviations of the "
              f"line, {c3['two_features']['error_rate_within_0.5std'] * 100:.0f} % are misclassified, compared with "
              f"{c3['two_features']['error_rate_beyond_0.5std'] * 100:.1f} % of the samples farther away (mean distance: "
              f"{c3['two_features']['mean_dist_wrong']:.2f} SD for errors vs. {c3['two_features']['mean_dist_correct']:.2f} "
              "SD for correct predictions). These are medium-sized tumours (radius ≈ 13–16 mm) where both classes "
              "overlap; radius and texture simply do not contain enough information to separate them, and no straight "
              "line can. Most of the errors are small malignant tumours below the line (false negatives)."),
        ("pb",),
        # ---------------- PART D
        ("h1", "Part D — Reflection and Comparison"),
        ("p", "<b>1. Linear vs. logistic regression output.</b> Linear regression outputs an unbounded real number "
              f"that is itself the prediction (e.g. a progression score of 180; the predictions in B1 ranged from "
              "about 48 to 291). Logistic regression also computes a linear score, but passes it through a sigmoid to "
              "obtain a probability between 0 and 1 (Figure 6b), and a class label is produced only after a "
              "threshold. Linear regression is fitted by minimising squared error; logistic regression by minimising "
              "log-loss (maximum likelihood). Both coefficients are “linear”, but in logistic regression they act on "
              "the log-odds, not on the output itself."),
        ("p", "<b>2. Parameter vs. hyperparameter.</b> Parameters are learned from the data during training: the "
              f"weights and intercept (e.g. w<sub>bmi</sub> = {b1['coef']['bmi']:.2f}, b = {b1['intercept']:.1f} in B1; "
              f"β<sub>radius</sub> = {c1['coef_standardized']['mean radius']:.2f} in C1). Hyperparameters are chosen by "
              "the user before training and control how learning happens: the learning rate (0.001–1.0 in B3), the "
              "number of iterations, whether to standardise, the regularisation strength C = 1.0, the solver, the "
              "train/test ratio and the random seed. The classification threshold (0.3/0.5/0.7) is a decision "
              "parameter applied after training, so it is also chosen by the user rather than learned."),
        ("p", "<b>3. Influence of the learning rate.</b> It sets the step size of every gradient update and therefore "
              "the trade-off between speed and stability (B3): 0.001 was too slow to converge in 2000 iterations, 0.1 "
              f"converged in {runs['0.1']['iter_to_within_1pct_of_optimum']} iterations, 0.5 oscillated before converging, "
              f"and 1.0 – above the limit 2/λ<sub>max</sub> = {b3['lr_stability_limit']:.2f} – diverged. The usable range "
              "depends on the data's scaling (B2: without standardisation the limit was ≈ 2.7·10<super>-5</super>)."),
        ("p", "<b>4. Why different metrics?</b> Regression errors are continuous distances, so MAE, MSE and R² "
              "measure <i>how far</i> predictions are from the truth (in target units or as explained variance). "
              "Classification outputs are categories, so the question is <i>how often and which way</i> the model is "
              "wrong: accuracy, precision, recall, F1 and the confusion matrix. Using MSE on 0/1 labels or accuracy on "
              "a continuous target would be meaningless. Moreover, accuracy alone can be misleading with class "
              "imbalance and unequal error costs; in C2 thresholds 0.3 and 0.7 had nearly the same accuracy but very "
              "different numbers of missed cancers."),
        ("p", "<b>5. Unexpected result.</b> In B3 the models stopped early had a slightly <i>better</i> test R² than "
              f"the exact least-squares solution (e.g. {f3(ie['0.1']['100']['test_R2'])} after 100 iterations vs. "
              f"{f3(b3['closed_form_test_R2'])}), even though their training loss was higher. At the same time the s1 "
              f"coefficient took thousands of iterations to move from ≈ {ie['0.1']['100']['coef_s1']:.0f} to its final "
              f"value of {b3['closed_form_coef_s1']:.0f}. Explanation: s1 and s2 are strongly correlated, which creates a "
              "very flat direction of the loss surface (small eigenvalue). Gradient descent starting from zero "
              "first fits the well-determined directions and only slowly moves along the flat one; stopping early "
              "keeps those unstable coefficients small, which acts like L2 (ridge) regularisation and reduces "
              "variance. The difference is small (≈ 0.003 R²) and on a test set of 89 patients could be noise, but it "
              "shows that the “optimal” training solution is not automatically the best on unseen data. A second, "
              "smaller surprise was that lr = 0.5 converged more slowly than lr = 0.1, although it is larger; this is "
              "because it is close to the stability limit and oscillates."),
        ("h1", "Conclusions"),
        ("p", "Linear regression on the Diabetes data gives interpretable partial effects and a moderate predictive "
              f"accuracy (test R² ≈ {b1['test']['R2']:.2f}); feature scaling does not change the OLS solution but is "
              "decisive for gradient-based training, where it reduced the condition number from ≈ 5·10<super>7</super> to "
              "≈ 430. The learning rate must be below the stability limit; within that range a moderate value "
              "converges fastest. Logistic regression separates malignant and benign tumours well "
              f"(AUC {c1['test_auc']:.2f}); its probabilities allow the decision threshold to be adapted to the "
              "application, and for screening a lower threshold (0.3) is preferable. Remaining errors lie along the "
              "linear decision boundary, where the classes overlap; more informative features (concave points) help "
              "more than tuning the threshold."),
        ("h1", "References"),
        ("p", "[1] B. Efron, T. Hastie, I. Johnstone, R. Tibshirani, “Least Angle Regression,” <i>Annals of Statistics</i>, "
              "32(2), 407–499, 2004. (Diabetes dataset)"),
        ("p", "[2] W. H. Wolberg, W. N. Street, O. L. Mangasarian, “Breast Cancer Wisconsin (Diagnostic),” UCI Machine "
              "Learning Repository, 1995. https://doi.org/10.24432/C5DW2B"),
        ("p", "[3] F. Pedregosa et al., “Scikit-learn: Machine Learning in Python,” <i>JMLR</i>, 12, 2825–2830, 2011."),
        ("p", "[4] G. James, D. Witten, T. Hastie, R. Tibshirani, <i>An Introduction to Statistical Learning</i>, 2nd ed., "
              "Springer, 2021 (Ch. 3 and 4)."),
        ("p", "[5] I. Goodfellow, Y. Bengio, A. Courville, <i>Deep Learning</i>, MIT Press, 2016 (Sec. 4.3, 7.8 – "
              "gradient descent and early stopping)."),
    ]
    return {"filename": "ML_Lab1_Report_EN.pdf", "footer": "ML Lab 1 – Linear and Logistic Regression",
            "doc_title": "ML Lab 1 – Linear and Logistic Regression", "story": s}


# ============================================================================================
def text_tr(A, B, C):
    n, t = tables(A, B, C, L_TR)
    b1, b2, b3, gd, runs = n["b1"], n["b2"], n["b3"], n["gd"], n["runs"]
    c1, c2, c3 = n["c1"], n["c2"], n["c3"]
    reg, clf = A["regression"], A["classification"]
    m05 = c1["test@0.5"]
    ie = b3["iterations_effect"]
    ex = c1["examples"]
    s = [
        ("title", "Laboratuvar Ödevi: Doğrusal ve Lojistik Regresyonu Anlamak",
         "Makine Öğrenmesi – Lab 1 Raporu<br/><br/>Öğrenci: ____________________ &nbsp;&nbsp; No: ______________<br/>"
         "Tarih: 24 Ekim 2026"),
        ("p", "<b>Özet.</b> İki veri seti incelenmiştir: doğrusal regresyon için <i>Diabetes</i> veri seti (442 hasta, "
              "10 klinik öznitelik, sürekli hedef) ve lojistik regresyon için <i>Breast Cancer Wisconsin (Diagnostic)</i> "
              f"veri seti (569 tümör, ikili hedef). Temel doğrusal model test kümesinde R² = {f3(b1['test']['R2'])} "
              f"(MAE {f2(b1['test']['MAE'])}) elde etmiştir; standartlaştırma tahminleri değiştirmemiş, ancak gradyan "
              "inişinin yaklaşık iki büyüklük mertebesi daha hızlı yakınsamasını sağlamıştır. En hızlı kararlı "
              "yakınsama 0.1 öğrenme oranında görülmüş, 1.0 ıraksamıştır. Beş öznitelikli lojistik model test "
              f"kümesinde {f3(m05['accuracy'])} doğruluk ve {f3(c1['test_auc'])} ROC-AUC değerine ulaşmıştır; eşiği 0.3'e "
              "düşürmek kesinlikten (precision) ödün vererek duyarlılığı (recall) artırır ki bu, kanser taramasında "
              "tercih edilen dengedir."),
        ("h2", "Tekrarlanabilirlik ayarları"),
        ("table", [["Öğe", "Ayar"],
                   ["Yazılım", "Python 3.13, scikit-learn 1.9.1, NumPy 2.5, pandas 3.0, Matplotlib 3.11"],
                   ["Doğrusal modeller", "sklearn LinearRegression (kapalı form en küçük kareler) + kendi yazdığımız "
                                         "NumPy toplu gradyan inişi (kayıp = MSE/2, sıfır başlangıç)"],
                   ["Lojistik model", "sklearn LogisticRegression, solver = lbfgs, L2 cezası, C = 1.0, max_iter = 1000"],
                   ["Veri bölme", "%80 eğitim / %20 test, random_state = 42 (sınıflandırmada tabakalı)"],
                   ["Ölçekleme", "StandardScaler yalnızca eğitim kümesine uydurulmuş, sonra test kümesine uygulanmıştır"],
                   ["Model seçimi", "Eşik seçimi yalnızca eğitim kümesi üzerinde 5-katlı çapraz doğrulama ile "
                                    "yapılmıştır; test kümesi yalnızca son değerlendirmede kullanılmıştır"]], [3.5, 13.5]),
        ("pb",),
        ("h1", "Bölüm A — Veri Seti Seçimi"),
        ("h2", "A.1 Veri seti 1 (doğrusal regresyon): Diabetes"),
        ("p", "<b>Problem ve kaynak.</b> Efron, Hastie, Johnstone ve Tibshirani (2004) tarafından yayımlanan ve "
              "scikit-learn ile birlikte dağıtılan Diabetes veri seti kullanılmıştır (<i>load_diabetes(scaled=False)</i>, "
              f"ham klinik birimler). {reg['n']} diyabet hastasının her biri için başlangıçta on ölçüm alınmıştır; hedef, "
              f"bir yıl sonraki hastalık ilerlemesinin nicel bir ölçüsüdür (aralık {reg['target_min']:.0f}–"
              f"{reg['target_max']:.0f}, ortalama {reg['target_mean']:.1f}, std {reg['target_std']:.1f}). Görev bu "
              "ilerleme skorunu tahmin etmektir."),
        ("p", "<b>Öznitelikler ve hedef.</b> Girdiler: yaş, cinsiyet, bmi, bp ve altı kan serumu ölçümü s1–s6 "
              "(Tablo 1). Hedef: hastalık ilerlemesi (sürekli)."),
        ("table",) + t["A_reg"],
        ("tcap", "Tablo 1. Diabetes veri seti – değişkenler, özet istatistikler ve hedefle Pearson korelasyonu r(y)."),
        ("p", "<b>Neden uygun?</b> Hedef süreklidir, birçok öznitelik hedefle belirgin ve yaklaşık doğrusal bir ilişki "
              f"gösterir (bmi r = {reg['corr_with_target']['bmi']:.2f}, s5 r = {reg['corr_with_target']['s5']:.2f}); "
              "100'den fazla gözlem ve ikiden fazla öznitelik vardır. Öznitelikler çok farklı ölçeklerdedir "
              "(sex ≈ 1–2, s1 ≈ 97–301), bu da ölçekleme deneyi için veri setini faydalı kılar; ayrıca bazı "
              "öznitelikler birbiriyle güçlü biçimde ilişkilidir (s1 ve s2), bu da katsayı yorumunu tartışmaya yardımcı olur."),
        ("fig", "A1_regression_eda.png", "Şekil 1. (a) Vücut kitle indeksi ile hastalık ilerlemesi ve en küçük "
                "kareler doğrusu: yüksek BMI daha hızlı ilerlemeyle ilişkilidir, ancak saçılma büyüktür. (b) Her "
                "özniteliğin hedefle korelasyonu; s3 (HDL, “iyi” kolesterol) belirgin negatif ilişkiye sahip tek özniteliktir."),
        ("p", f"<b>Ön işleme.</b> Eksik değer bulunmamıştır ({reg['missing']} eksik hücre). Tüm değerler fizyolojik "
              "olarak makul olduğundan aykırı değer çıkarılmamıştır. Veri %80/%20 oranında bölünmüştür "
              f"({B['split']['train']} eğitim / {B['split']['test']} test, random_state = 42). Ölçekleme ve gradyan "
              "inişi deneylerinde öznitelikler standartlaştırılmıştır (z = (x − μ)/σ); test kümesinden bilgi "
              "sızıntısını önlemek için μ ve σ yalnızca eğitim kümesinden hesaplanmıştır."),
        ("h2", "A.2 Veri seti 2 (lojistik regresyon): Breast Cancer Wisconsin (Diagnostic)"),
        ("p", "<b>Problem ve kaynak.</b> Wolberg, Street ve Mangasarian (1995) tarafından hazırlanan, UCI Machine "
              "Learning Repository veri seti; scikit-learn ile birlikte gelir (<i>load_breast_cancer</i>). "
              f"{clf['n']} örneğin her biri, bir meme kitlesinin ince iğne aspirasyonu görüntüsündeki hücre "
              "çekirdeklerini 30 gerçel değerli öznitelikle tanımlar. Görev tümörü kötü huylu (malignant) veya iyi "
              "huylu (benign) olarak sınıflandırmaktır."),
        ("p", f"<b>Öznitelikler ve hedef.</b> Hedef: <i>malignant</i> = 1 ({clf['malignant']} örnek, %37), benign = 0 "
              f"({clf['benign']}, %63). scikit-learn'deki orijinal kodlama (0 = malignant) ters çevrilmiştir; böylece "
              "pozitif sınıf hastalık olur ve kesinlik ile duyarlılık tıbbi açıdan anlamlı hâle gelir. Lojistik "
              "deneyler için yorumlanabilir beş “mean” özniteliği seçilmiştir (Tablo 2)."),
        ("table",) + t["A_clf"],
        ("tcap", "Tablo 2. Breast Cancer veri setinin seçilen öznitelikleri (569 örneğin tümü)."),
        ("p", "<b>Neden uygun?</b> Hedef ikilidir; sınıflar orta düzeyde dengesizdir ama aşırı değildir. Şekil 2, "
              "sınıfların doğrusal bir sınırla büyük ölçüde – ama kusursuz değil – ayrılabildiğini gösterir; bu, "
              "lojistik regresyonun tam olarak tasarlandığı durumdur. Örtüşme bölgesi analiz edilecek gerçekçi hatalar sağlar."),
        ("fig", "A2_classification_eda.png", "Şekil 2. (a) Tanıya göre renklendirilmiş mean radius – mean texture "
                "grafiği: kötü huylu tümörler daha büyük ve daha dokulu olma eğilimindedir; yarıçapın 13–16 mm "
                "civarında bir örtüşme bölgesi vardır. (b) Mean concave points dağılımı: iki sınıf iyi ayrışır, bu "
                "nedenle bu özniteliğin büyük bir katsayı alması beklenir."),
        ("p", f"<b>Ön işleme.</b> Eksik değer yoktur ({clf['missing']}). Her iki kümenin de %37/%63 sınıf oranını "
              f"koruması için tabakalı %80/%20 bölme yapılmıştır ({C['split']['train']} eğitim / {C['split']['test']} "
              f"test; testte {C['split']['test_malignant']} kötü huylu). Ham öznitelikler üç büyüklük mertebesi farklı "
              "olduğundan (radius ≈ 14, smoothness ≈ 0.1) ve L2 düzenlileştirme tüm katsayıları eşit cezalandırdığından, "
              "öznitelikler bir scikit-learn Pipeline içinde standartlaştırılmıştır (ölçekleyici yalnızca eğitim "
              "katlarına uydurulur)."),
        ("pb",),
        ("h1", "Bölüm B — Doğrusal Regresyon"),
        ("h2", "Deney B1 — Model parametreleri ve tahminler"),
        ("p", "Ham (ölçeklenmemiş) öznitelikler üzerinde temel bir sıradan en küçük kareler (OLS) modeli "
              "ŷ = b + Σ w<sub>j</sub>x<sub>j</sub> eğitilmiştir. Katsayılar Tablo 4'te (“ham birim” sütunu), hata "
              "metrikleri Tablo 3'te verilmiştir."),
        ("table",) + t["B_metrics"],
        ("tcap", "Tablo 3. B1 hata metrikleri. Yalnızca-ortalama temel model her zaman eğitim ortalamasını tahmin eder."),
        ("fig", "B1_actual_vs_predicted.png", "Şekil 3. B1 – (a) eğitim (açık) ve test (koyu) noktaları için gerçek "
                "ve tahmin edilen ilerleme; kesikli çizgi üzerindeki noktalar kusursuz tahmindir. (b) Test artıkları: "
                "belirgin bir desen yoktur, ancak büyük tahminlerde yayılım artar ve yüksek gerçek değerler eksik tahmin edilir."),
        ("p", "<b>1. Katsayılar ve sabit terim neyi temsil eder?</b> Her katsayı, diğer tüm öznitelikler sabit "
              "tutulurken o özniteliğin bir birim artmasının hastalık ilerlemesinde beklenen değişimidir. Örneğin "
              f"w<sub>bmi</sub> = {b1['coef']['bmi']:.2f}: BMI'daki her ek kg/m² ilerlemeye yaklaşık "
              f"{b1['coef']['bmi']:.1f} puan ekler; w<sub>bp</sub> = mm Hg başına {b1['coef']['bp']:.2f}; "
              f"w<sub>s5</sub> = log-trigliserid birimi başına {b1['coef']['s5']:.1f}; w<sub>sex</sub> = "
              f"{b1['coef']['sex']:.1f}, diğer değerler eşitken 2 kodlu grubun 1 kodlu gruba göre yaklaşık "
              f"{abs(b1['coef']['sex']):.0f} puan daha az ilerlediği anlamına gelir. Sabit terim ({b1['intercept']:.1f}), "
              "tüm özniteliklerin sıfır olduğu durumdaki tahmindir – veri aralığının dışında bir noktadır (kimsenin "
              "BMI'ı ya da kan basıncı 0 değildir), dolayısıyla doğrudan tıbbi anlamı yoktur; yalnızca regresyon "
              "düzleminin konumunu belirler."),
        ("p", "<b>2. Öznitelikler tahminleri nasıl etkiler?</b> Birimler farklı olduğu için ham katsayılar doğrudan "
              "karşılaştırılamaz. Standartlaştırılmış katsayılara göre (B2, Tablo 4) bir standart sapma başına en "
              f"etkili öznitelikler s1 ({b2['standardized']['coef']['s1']:.1f}), s5 ({b2['standardized']['coef']['s5']:.1f}), "
              f"bmi ({b2['standardized']['coef']['bmi']:.1f}), s2 ({b2['standardized']['coef']['s2']:.1f}) ve bp "
              f"({b2['standardized']['coef']['bp']:.1f}) özellikleridir; diğerleri bilindiğinde yaş ve s6'nın neredeyse "
              "hiç etkisi yoktur. Dikkat çekici olarak s1 hedefle pozitif korelasyonludur (r = 0.21) ama büyük negatif "
              "katsayıya sahiptir: s1 (toplam kolesterol) ve s2 (LDL) güçlü biçimde ilişkilidir, model ikisi "
              "arasındaki farkı kullanır. Dolayısıyla katsayılar basit korelasyonları değil kısmi etkileri ifade eder."),
        ("p", f"<b>3. Görülmemiş veride ne kadar doğru tahmin yapıyor?</b> Test kümesinde R² = {f3(b1['test']['R2'])}: "
              f"model hastalık ilerlemesindeki varyansın yaklaşık %{b1['test']['R2'] * 100:.0f}'ini açıklar. Tipik hata, "
              f"standart sapması {reg['target_std']:.0f} olan bir hedefte MAE ≈ {b1['test']['MAE']:.0f} puandır (RMSE ≈ "
              f"{b1['test']['RMSE']:.0f}). Bu, yalnızca-ortalama modele göre (MAE "
              f"{b1['baseline_mean_predictor_test']['MAE']:.0f}, R² ≈ 0) açık bir iyileşmedir, ancak kesin olmaktan uzaktır. "
              f"Eğitim ve test hataları benzerdir (R² {f3(b1['train']['R2'])} ve {f3(b1['test']['R2'])}), yani model aşırı "
              "öğrenme (overfitting) yapmıyor; sınırlama, on başlangıç ölçümündeki bilginin azlığından ve doğrusal "
              "olmayan etkilerden kaynaklanıyor (Şekil 3b, çok yüksek ilerlemeye sahip hastaların sistematik olarak "
              "eksik tahmin edildiğini gösterir)."),
        ("h2", "Deney B2 — Öznitelik ölçekleme"),
        ("p", "OLS modeli iki kez eğitilmiştir: ham öznitelikler ve standartlaştırılmış öznitelikler üzerinde "
              "(ölçekleyici eğitim kümesine uydurulmuştur). Ayrıca ölçeklemenin <i>eğitim sürecine</i> etkisini "
              "göstermek için aynı doğrusal model, her iki koşulda da pratik olarak kararlı en büyük öğrenme oranıyla "
              "5000 iterasyon boyunca toplu gradyan inişi (GD) ile eğitilmiştir."),
        ("table",) + t["B_coef"],
        ("tcap", "Tablo 4. Standartlaştırma öncesi ve sonrası OLS katsayıları. Standart katsayı = ham katsayı × "
                 "özniteliğin eğitimdeki standart sapması (ör. bmi: 5.85 × 4.38 ≈ 25.6)."),
        ("table",) + t["B_scaling"],
        ("tcap", f"Tablo 5. Ölçeklemeli ve ölçeklemesiz test başarımı. OLS optimum eğitim MSE değeri "
                 f"{gd['closed_form_train_mse']:.2f}'dir."),
        ("fig", "B2_scaling_comparison.png", "Şekil 4. B2 – (a) ham birimlerde ve standartlaştırma sonrası "
                "katsayılar; (b) ölçeklemeli ve ölçeklemesiz gradyan inişinin eğitim kaybı. Ölçeklemesiz GD 5000 "
                "iterasyondan sonra bile optimumdan uzaktır; ölçeklemeli GD ise ~60 iterasyonda optimuma ulaşır."),
        ("p", "<b>1. Katsayılar nasıl değişir?</b> Her katsayı özniteliğinin standart sapmasıyla çarpılır; tüm "
              "ölçeklenmiş özniteliklerin ortalaması sıfır olduğundan sabit terim, hedefin eğitim ortalamasına "
              f"({b2['standardized']['intercept']:.1f}) eşit olur. Ölçeklemeden sonra katsayılar karşılaştırılabilir hâle "
              f"gelir: s5 {b2['unscaled']['coef']['s5']:.1f}'den {b2['standardized']['coef']['s5']:.1f}'e düşer (s5'in "
              f"std'si 0.52 gibi küçük bir değerdir), s1 ise {b2['unscaled']['coef']['s1']:.2f}'den "
              f"{b2['standardized']['coef']['s1']:.1f}'e çıkar (s1'in std'si 34.6). Önem sıralaması tamamen değişir; "
              "işaretler ise hiç değişmez."),
        ("p", "<b>2. Ölçekleme tahmin doğruluğunu değiştirir mi?</b> Kapalı form OLS için – hayır. İki modelin test "
              f"tahminleri arasındaki en büyük fark {b2['max_abs_prediction_difference']:.1e}'dir, yani sayısal yuvarlama "
              "hatasıdır; MAE, MSE ve R² aynıdır. Standartlaştırma tersinir bir doğrusal dönüşümdür ve "
              "düzenlileştirilmemiş doğrusal model bunu ağırlıklarına yansıtabilir. Gradyan inişinde ise pratikte "
              f"<i>önemlidir</i>: aynı 5000 iterasyon sonunda ölçeklemesiz GD test R² = {f3(gd['test_unscaled']['R2'])}, "
              f"ölçeklemeli GD {f3(gd['test_scaled']['R2'])} değerine ulaşmıştır."),
        ("p", "<b>3. Ölçekleme neden önemlidir?</b> Gradyan inişinin hızı kayıp yüzeyinin şekline bağlıdır. "
              "Ölçeklemesiz durumda Hessian (1/n)XᵀX'in en büyük özdeğeri "
              f"λ<sub>maks</sub> ≈ {gd['lambda_max_unscaled']:.0f} ve koşul sayısı ≈ {gd['cond_unscaled']:.1e}'dir; yüzey "
              "çok uzun ve dar bir vadidir. Kararlılık için adım 2/λ<sub>maks</sub> ≈ "
              f"{2 / gd['lambda_max_unscaled']:.1e} değerinin altında kalmalıdır (“normal” görünen lr = 10<super>-4</super> "
              f"{gd['unscaled_lr_1e-4_diverged_at_iter']} iterasyonda ıraksamıştır) ve bu kadar küçük bir adım düz "
              "yönlerdeki ilerlemeyi aşırı yavaşlatır. Standartlaştırma sonrası λ<sub>maks</sub> ≈ "
              f"{gd['lambda_max_scaled']:.2f} ve koşul sayısı ≈ {gd['cond_scaled']:.0f}'e iner; böylece tek bir öğrenme "
              "oranı tüm yönlere uyar. Ölçekleme ayrıca düzenlileştirilmiş modeller (L1/L2 cezaları tüm katsayılara "
              "eşit davranır), uzaklık tabanlı yöntemler (k-NN, SVM, k-means) ve katsayı büyüklüklerinin "
              "karşılaştırılması için de gereklidir."),
        ("h2", "Deney B3 — Öğrenme oranı ve yakınsama"),
        ("p", "Toplu gradyan inişi, standartlaştırılmış eğitim verisi üzerinde beş öğrenme oranıyla (0.001, 0.01, "
              "0.1, 0.5, 1.0), sıfır başlangıçla ve 2000 iterasyon boyunca çalıştırılmıştır; diğer her şey sabit "
              f"tutulmuştur. Teorik kararlılık sınırı 2/λ<sub>maks</sub> = {b3['lr_stability_limit']:.3f}'tür."),
        ("fig", "B3_learning_rate.png", "Şekil 5. B3 – (a) beş öğrenme oranı için iterasyona karşı eğitim MSE "
                "(log–log eksenler); lr = 1.0 kararlılık sınırını aşar ve ıraksar. (b) lr = 0.01 ve lr = 0.1 için, "
                "belirli sayıda iterasyondan sonra elde edilen modelin test R² değeri."),
        ("table",) + t["B_lr"],
        ("tcap", "Tablo 6. 2000 iterasyon sonrası öğrenme oranı karşılaştırması."),
        ("table",) + t["B_iter"],
        ("tcap", "Tablo 7. İterasyon sayısının etkisi (standartlaştırılmış veri). Son sütun çok yavaş yakınsayan s1 "
                 "katsayısını takip eder."),
        ("p", "<b>1. En hızlı kararlı yakınsama.</b> lr = 0.1 optimuma en hızlı ulaşmıştır (optimum eğitim MSE'nin "
              f"%1 yakınına {runs['0.1']['iter_to_within_1pct_of_optimum']} iterasyonda). lr = 0.5 daha büyük olmasına "
              f"rağmen {runs['0.5']['iter_to_within_1pct_of_optimum']} iterasyon gerektirmiştir: kararlılık sınırının "
              f"({b3['lr_stability_limit']:.3f}) hemen altındadır, bu yüzden kayıp önce sıçrar ve ağırlıklar dik yön "
              "boyunca salınır, sonra oturur (Şekil 5a'daki kırılma). Bununla birlikte 2000 iterasyon sonunda en "
              "yakın son değere o ulaşmıştır."),
        ("p", "<b>2. Çok küçük / çok büyük.</b> lr = 0.001 ile kayıp monoton fakat çok yavaş azalır; 2000 iterasyon "
              f"sonunda eğitim MSE hâlâ {runs['0.001']['final_train_mse']:.0f} ve test R² yalnızca "
              f"{f3(runs['0.001']['test']['R2'])}'tür – model yetersiz eğitilmiştir. lr = 1.0 ile her adım minimumu "
              "düzelttiğinden fazla aşar, hata geometrik olarak büyür ve kayıp birkaç iterasyonda patlar (ıraksama)."),
        ("p", "<b>3. İterasyon sayısı.</b> Çok az iterasyonla model zayıftır (lr = 0.1, 10 iterasyon: test R² "
              f"{f3(ie['0.1']['10']['test_R2'])}). Test hatası lr = 0.1 için ≈ 50, lr = 0.01 için ≈ 500 iterasyondan sonra "
              "dengelenir. Bu noktadan sonra eğitim kaybı yavaşça düşmeye devam ederken, ilişkili s1/s2 çiftinin "
              f"katsayıları hâlâ değişmektedir (s1: 500 iterasyonda {ie['0.1']['500']['coef_s1']:.1f}, 5000'de "
              f"{ie['0.1']['5000']['coef_s1']:.1f}, kapalı formda {b3['closed_form_coef_s1']:.1f}). İlginç olarak kısmen "
              f"eğitilmiş modeller, kesin çözümden ({f3(b3['closed_form_test_R2'])}) biraz <i>daha yüksek</i> test R²'ye "
              f"sahiptir ({f3(ie['0.1']['100']['test_R2'])}): erken durdurma örtük bir düzenlileştirme gibi davranır (bkz. Bölüm D)."),
        ("pb",),
        ("h1", "Bölüm C — Lojistik Regresyon"),
        ("h2", "Deney C1 — Model parametreleri ve sınıflandırma"),
        ("p", "Lojistik regresyon modeli P(y = 1 | x) = σ(b + Σ w<sub>j</sub>x<sub>j</sub>), σ(z) = 1/(1 + e<super>−z</super>), "
              "Tablo 2'deki beş standartlaştırılmış öznitelik üzerinde eğitilmiş ve 0.5 eşiğiyle değerlendirilmiştir."),
        ("table",) + t["C_coef"],
        ("tcap", "Tablo 8. Lojistik regresyon katsayıları. Ham birim β = standart β / eğitim SS."),
        ("table",) + t["C_metrics"],
        ("tcap", f"Tablo 9. C1 test başarımı (n = {C['split']['test']}). ROC-AUC = {f3(c1['test_auc'])}, log-loss = "
                 f"{f3(c1['test_logloss'])}, eğitim doğruluğu = {f3(c1['train_accuracy'])}."),
        ("fig", "C1_confusion_matrix.png", "Şekil 6. C1 – (a) 0.5 eşiğinde test kümesi karışıklık matrisi. (b) "
                "Tahmin edilen olasılıkların histogramı, yani eşiklemeden önceki model çıktısı; örneklerin çoğu 0 "
                "ya da 1'e yakın olasılık alır, hatalar ortadaki az sayıdaki örnekten gelir."),
        ("p", "<b>1. Eşikten önceki çıktı.</b> Model önce herhangi bir gerçel sayı olabilen doğrusal bir skor "
              "(log-odds) z = b + wᵀx hesaplar, sonra sigmoid bunu (0, 1) aralığında bir olasılığa dönüştürür. "
              f"Üç test hastası bunu gösterir: z = {ex[0]['z']:.2f} → p = {ex[0]['p']:.4f} (iyi huylu, doğru); "
              f"z = {ex[1]['z']:.2f} → p = {ex[1]['p']:.5f} (kötü huylu, doğru); z = {ex[2]['z']:.2f} → p = "
              f"{ex[2]['p']:.2f} (aslında iyi huylu, ama 0.5'in biraz üzerinde olduğu için yanlış pozitif olur). Sınıf "
              "etiketi ancak eşik uygulandıktan sonra ortaya çıkar."),
        ("p", "<b>2. Katsayıların etkisi.</b> Bir katsayı, özniteliğin bir birim artışı başına log-odds'taki "
              "değişimdir; e<super>β</super> buna karşılık gelen odds oranıdır. Beş katsayının tamamı pozitiftir; "
              "dolayısıyla daha büyük, daha pürüzlü, daha içbükey ve daha az simetrik çekirdekler kötü huylu olma "
              "olasılığını artırır. Bir standart sapma başına mean radius odds'u "
              f"{c1['odds_ratio_per_std']['mean radius']:.1f}, concave points {c1['odds_ratio_per_std']['mean concave points']:.1f}, "
              f"texture {c1['odds_ratio_per_std']['mean texture']:.1f} katına çıkarırken symmetry "
              f"({c1['odds_ratio_per_std']['mean symmetry']:.2f}) az katkı sağlar. Olasılık üzerindeki etki doğrusal "
              "değildir: aynı Δz, p = 0.5 civarında p'yi güçlü biçimde değiştirirken p zaten 0 veya 1'e yakınken "
              f"neredeyse hiç değiştirmez. Negatif sabit terim ({c1['intercept_standardized']:.2f}), ortalama "
              f"özniteliklere sahip bir tümörün daha olası olarak iyi huylu olduğunu yansıtır (σ({c1['intercept_standardized']:.2f}) "
              "≈ 0.34, %37'lik önsel orana yakın)."),
        ("p", f"<b>3. Hata türleri.</b> Model {m05['FP']} yanlış pozitif (iyi huylu tümörü kötü huylu tahmin etme) ve "
              f"{m05['FN']} yanlış negatif (kaçırılan kötü huylu tümör) hata yapar. {m05['FP'] + m05['FN']} hatanın tamamı "
              "“sınırda” tümörlerdir: yanlış sınıflanan örneklerin mean radius değeri 13.4 ile 16.2 mm arasındadır, "
              "yani tam Şekil 2a'daki örtüşme bölgesindedir. Yanlış pozitifler büyük veya çok dokulu iyi huylu "
              "tümörlerdir (ör. yarıçap 13.4 mm, texture 30.7); yanlış negatiflerden ikisi ise concave points değeri "
              "veri seti ortalaması olan 0.049 civarında veya altında (0.041 ve 0.051) olan kötü huylu tümörlerdir, bu yüzden kullanılan özniteliklere "
              "göre iyi huylu görünürler. Bu uygulamada yanlış negatif (kaçırılan kanser), yanlış pozitiften (fazladan "
              "bir biyopsi) çok daha maliyetlidir."),
        ("h2", "Deney C2 — Karar eşiği"),
        ("p", "C1 modelinin olasılıkları yeniden eğitim yapılmadan kullanılmış ve 0.3, 0.5 ve 0.7 eşikleriyle "
              "sınıflandırılmıştır. Test kümesinin konfigürasyon seçiminde kullanılmaması kuralına uymak için eşik, "
              "eğitim kümesinin 5-katlı çapraz doğrulamayla elde edilen (out-of-fold) olasılıkları üzerinde "
              "<i>seçilmiştir</i>; test değerleri yalnızca değerlendirme amacıyla raporlanmıştır."),
        ("table",) + t["C_thr"],
        ("tcap", "Tablo 10. Eşiğin etkisi (eğitim çapraz doğrulaması ve test kümesi)."),
        ("fig", "C2_threshold.png", "Şekil 7. C2 – (a) 0.05'ten 0.95'e kadar her eşik için test kümesinde "
                "kesinlik ve duyarlılık; işaretler 0.3, 0.5 ve 0.7'yi gösterir. (b) Üç eşikte yanlış pozitif ve "
                "yanlış negatif sayıları."),
        ("p", f"<b>1. FP ve FN üzerindeki etki.</b> Eşiği düşürmek daha fazla örneği kötü huylu olarak etiketler: "
              f"0.3'te testte {c2['test']['0.3']['FP']} FP ve {c2['test']['0.3']['FN']} FN; 0.5'te "
              f"{c2['test']['0.5']['FP']} FP ve {c2['test']['0.5']['FN']} FN; 0.7'de {c2['test']['0.7']['FP']} FP ve "
              f"{c2['test']['0.7']['FN']} FN vardır. Yanlış pozitifler ve yanlış negatifler zıt yönlerde hareket eder – "
              "eşik yalnızca hataları yeniden dağıtır, modelin sınıfları ayırma yeteneğini iyileştirmez."),
        ("p", f"<b>2. Kesinlik ve duyarlılık.</b> Eşiği artırmak kesinliği yükseltir "
              f"({f3(c2['test']['0.3']['precision'])} → {f3(c2['test']['0.5']['precision'])} → "
              f"{f3(c2['test']['0.7']['precision'])}) ve duyarlılığı düşürür ({f3(c2['test']['0.3']['recall'])} → "
              f"{f3(c2['test']['0.5']['recall'])} → {f3(c2['test']['0.7']['recall'])}). Test kümesi küçük olduğu için "
              "eğriler basamak fonksiyonudur: her basamak tek bir örneğin eşiği geçmesidir. Doğruluk 0.5'te en "
              "yüksektir ve F1 az değişir; yani bu metrikler klinik açıdan önemli olan dengeyi gizler."),
        ("p", "<b>3. Seçilen eşik: 0.3.</b> Kanser taramasında kaçırılan bir kötü huylu tümör, yanlış alarmdan çok "
              "daha tehlikelidir; bu yüzden öncelik duyarlılıktır. Eğitim çapraz doğrulamasında 0.3, duyarlılığı "
              f"{f3(c2['train_cv']['0.5']['recall'])}'den {f3(c2['train_cv']['0.3']['recall'])}'e çıkarır (170 kanserden "
              "kaçırılan 19 → 10), bunun bedeli 17 ek yanlış alarmdır. Test kümesi bu seçimi doğrular: duyarlılık "
              f"{f3(c2['test']['0.3']['recall'])}, {C['split']['test_malignant']} kanserden yalnızca "
              f"{c2['test']['0.3']['FN']} tanesi kaçırılmıştır. 0.7 eşiği ancak yanlış pozitiflerin pahalı hata olduğu "
              "durumlarda (ör. invaziv bir tedavi kararından önce) uygun olurdu."),
        ("h2", "Deney C3 — Öznitelikler ve karar sınırı"),
        ("p", "Aynı bölme üzerinde iki model eğitilmiştir: biri yalnızca <i>mean radius</i>, diğeri <i>mean radius</i> "
              "ve <i>mean texture</i> kullanır. Bu iki öznitelik görsel olarak yorumlanabilir ve aralarında zayıf "
              "korelasyon olduğu için seçilmiştir; böylece ikinci öznitelik yeni bilgi ekler."),
        ("table",) + t["C_c3"],
        ("tcap", "Tablo 11. Bir ve iki öznitelik (test kümesi, eşik 0.5). Beş öznitelikli C1 modeli referans olarak gösterilmiştir."),
        ("fig", "C3_decision_boundary.png", "Şekil 8. C3 – (a) tek öznitelikli model, yarıçap ekseni boyunca bir "
                f"sigmoiddir; karar sınırı tek bir noktadır: radius = {c3['one_feature']['decision_point_raw']:.1f} mm. "
                "(b) Standartlaştırılmış koordinatlarda (z-skorları) iki öznitelikli model: arka plan rengi = tahmin "
                "edilen olasılık, düz çizgi = karar sınırı p = 0.5, noktalı çizgiler = p = 0.3 ve 0.7; küçük soluk "
                "noktalar eğitim verisi, büyük noktalar test verisi, halka içindekiler yanlış sınıflandırılmış örneklerdir."),
        ("p", f"<b>1. İkinci özniteliğin etkisi.</b> Texture eklemek tüm metrikleri iyileştirmiştir: doğruluk "
              f"{f3(c3['one_feature']['test@0.5']['accuracy'])} → {f3(c3['two_features']['test@0.5']['accuracy'])}, "
              f"duyarlılık {f3(c3['one_feature']['test@0.5']['recall'])} → {f3(c3['two_features']['test@0.5']['recall'])}, "
              f"ROC-AUC {f3(c3['one_feature']['test_auc'])} → {f3(c3['two_features']['test_auc'])}, log-loss "
              f"{f3(c3['one_feature']['test_logloss'])} → {f3(c3['two_features']['test_logloss'])}. Doğruluktaki kazanç "
              "yalnızca bir test örneğidir, ancak AUC ve log-loss'taki iyileşme olasılıkların daha iyi sıralandığını ve "
              f"daha iyi kalibre edildiğini gösterir. Texture katsayısı ({c3['two_features']['coef_standardized'][1]:.2f}), "
              f"radius katsayısından ({c3['two_features']['coef_standardized'][0]:.2f}) çok daha küçüktür; yani texture "
              f"ikincil bir sinyaldir. Beş öznitelikle (C1) doğruluk, büyük ölçüde concave points sayesinde "
              f"{f3(m05['accuracy'])}'e ulaşır."),
        ("p", "<b>2. Sınır neyi temsil eder?</b> Karar sınırı, modelin kararsız kaldığı noktaların kümesidir: P = 0.5, "
              "yani b + w<sub>1</sub>x<sub>1</sub> + w<sub>2</sub>x<sub>2</sub> = 0. Lojistik regresyonda bu her zaman bir "
              "doğrudur (daha yüksek boyutta bir hiperdüzlem). Eğimi öznitelikler arasındaki ödünleşimi gösterir: "
              "yarıçapı daha küçük bir tümör, texture değeri yeterince yüksekse yine de kötü huylu sınıflandırılabilir. "
              "p = 0.3 ve p = 0.7 çizgileri sınıra paraleldir; dolayısıyla eşiği değiştirmek (C2) sınırı döndürmeden kaydırır."),
        ("p", "<b>3. Zor gözlemler.</b> Sınıra yakın örneklerin sınıflandırılması zordur. Doğruya 0.5 standart "
              f"sapmadan daha yakın olan {c3['two_features']['n_within_0.5std_of_boundary']} test örneğinin "
              f"%{c3['two_features']['error_rate_within_0.5std'] * 100:.0f}'i yanlış sınıflandırılmışken, daha uzaktaki "
              f"örneklerde bu oran %{c3['two_features']['error_rate_beyond_0.5std'] * 100:.1f}'dir (ortalama uzaklık: "
              f"hatalarda {c3['two_features']['mean_dist_wrong']:.2f} SS, doğru tahminlerde "
              f"{c3['two_features']['mean_dist_correct']:.2f} SS). Bunlar iki sınıfın örtüştüğü orta boy tümörlerdir "
              "(yarıçap ≈ 13–16 mm); radius ve texture onları ayırmak için yeterli bilgi içermez ve hiçbir doğru "
              "onları ayıramaz. Hataların çoğu doğrunun altında kalan küçük kötü huylu tümörlerdir (yanlış negatifler)."),
        ("pb",),
        ("h1", "Bölüm D — Değerlendirme ve Karşılaştırma"),
        ("p", "<b>1. Doğrusal ve lojistik regresyon çıktısı.</b> Doğrusal regresyon, kendisi doğrudan tahmin olan "
              "sınırsız bir gerçel sayı üretir (ör. 180'lik bir ilerleme skoru; B1'deki tahminler yaklaşık 48 ile 291 "
              "arasındadır). Lojistik regresyon da doğrusal bir skor hesaplar, ancak bunu sigmoid fonksiyonundan "
              "geçirerek 0 ile 1 arasında bir olasılık elde eder (Şekil 6b); sınıf etiketi ancak eşikten sonra "
              "üretilir. Doğrusal regresyon karesel hatayı, lojistik regresyon log-loss'u (en çok olabilirlik) "
              "minimize ederek uydurulur. Her ikisinin katsayıları “doğrusal”dır, ancak lojistik regresyonda "
              "çıktının kendisine değil log-odds'a etki ederler."),
        ("p", "<b>2. Parametre ve hiperparametre farkı.</b> Parametreler eğitim sırasında veriden öğrenilir: "
              f"ağırlıklar ve sabit terim (ör. B1'de w<sub>bmi</sub> = {b1['coef']['bmi']:.2f}, b = {b1['intercept']:.1f}; "
              f"C1'de β<sub>radius</sub> = {c1['coef_standardized']['mean radius']:.2f}). Hiperparametreler eğitimden önce "
              "kullanıcı tarafından seçilir ve öğrenmenin nasıl gerçekleşeceğini kontrol eder: öğrenme oranı "
              "(B3'te 0.001–1.0), iterasyon sayısı, standartlaştırma yapılıp yapılmayacağı, düzenlileştirme gücü "
              "C = 1.0, çözücü (solver), eğitim/test oranı ve rastgele tohum. Sınıflandırma eşiği (0.3/0.5/0.7) "
              "eğitimden sonra uygulanan bir karar parametresidir; bu yüzden o da öğrenilmez, kullanıcı tarafından seçilir."),
        ("p", "<b>3. Öğrenme oranının etkisi.</b> Her gradyan güncellemesinin adım büyüklüğünü ve dolayısıyla hız ile "
              "kararlılık arasındaki dengeyi belirler (B3): 0.001, 2000 iterasyonda yakınsayamayacak kadar yavaştır; 0.1 "
              f"{runs['0.1']['iter_to_within_1pct_of_optimum']} iterasyonda yakınsamış, 0.5 yakınsamadan önce salınmış, "
              f"2/λ<sub>maks</sub> = {b3['lr_stability_limit']:.2f} sınırının üzerindeki 1.0 ise ıraksamıştır. Kullanılabilir "
              "aralık verinin ölçeklenmesine bağlıdır (B2: standartlaştırma olmadan sınır ≈ 2.7·10<super>-5</super> idi)."),
        ("p", "<b>4. Neden farklı metrikler?</b> Regresyon hataları sürekli uzaklıklardır; bu nedenle MAE, MSE ve R² "
              "tahminlerin gerçekten <i>ne kadar uzak</i> olduğunu ölçer (hedef biriminde ya da açıklanan varyans "
              "olarak). Sınıflandırma çıktıları kategoriler olduğundan soru, modelin <i>ne sıklıkla ve hangi yönde</i> "
              "hata yaptığıdır: doğruluk, kesinlik, duyarlılık, F1 ve karışıklık matrisi. 0/1 etiketlerinde MSE ya da "
              "sürekli bir hedefte doğruluk kullanmak anlamsız olur. Ayrıca sınıf dengesizliği ve eşit olmayan hata "
              "maliyetleri varken doğruluk tek başına yanıltıcı olabilir; C2'de 0.3 ve 0.7 eşikleri neredeyse aynı "
              "doğruluğa sahipken kaçırılan kanser sayıları çok farklıydı."),
        ("p", "<b>5. Beklenmeyen sonuç.</b> B3'te erken durdurulan modeller, eğitim kayıpları daha yüksek olmasına "
              f"rağmen kesin en küçük kareler çözümünden biraz <i>daha iyi</i> test R² değerine sahipti (ör. 100 "
              f"iterasyondan sonra {f3(ie['0.1']['100']['test_R2'])}, kesin çözüm {f3(b3['closed_form_test_R2'])}). Aynı "
              f"zamanda s1 katsayısının ≈ {ie['0.1']['100']['coef_s1']:.0f}'dan son değeri olan "
              f"{b3['closed_form_coef_s1']:.0f}'a ulaşması binlerce iterasyon sürdü. Açıklama: s1 ve s2 güçlü biçimde "
              "ilişkilidir; bu, kayıp yüzeyinde çok düz bir yön (küçük özdeğer) oluşturur. Sıfırdan başlayan gradyan "
              "inişi önce iyi belirlenmiş yönleri uydurur ve düz yön boyunca çok yavaş ilerler; erken durdurmak bu "
              "kararsız katsayıları küçük tutar, bu da L2 (ridge) düzenlileştirmesi gibi davranarak varyansı azaltır. "
              "Fark küçüktür (≈ 0.003 R²) ve 89 hastalık bir test kümesinde gürültü olabilir; yine de eğitimdeki "
              "“optimum” çözümün görülmemiş veride otomatik olarak en iyi olmadığını gösterir. Daha küçük ikinci bir "
              "sürpriz, lr = 0.5'in daha büyük olmasına rağmen lr = 0.1'den daha yavaş yakınsamasıydı; bunun nedeni "
              "kararlılık sınırına yakın olması ve salınım yapmasıdır."),
        ("h1", "Sonuçlar"),
        ("p", "Diabetes verisi üzerindeki doğrusal regresyon yorumlanabilir kısmi etkiler ve orta düzeyde tahmin "
              f"doğruluğu (test R² ≈ {b1['test']['R2']:.2f}) sağlar; öznitelik ölçekleme OLS çözümünü değiştirmez ama "
              "gradyan tabanlı eğitim için belirleyicidir; koşul sayısını ≈ 5·10<super>7</super>'den ≈ 430'a "
              "düşürmüştür. Öğrenme oranı kararlılık sınırının altında olmalıdır; bu aralıkta orta büyüklükte bir "
              "değer en hızlı yakınsar. Lojistik regresyon kötü ve iyi huylu tümörleri iyi ayırır "
              f"(AUC {c1['test_auc']:.2f}); ürettiği olasılıklar karar eşiğinin uygulamaya göre uyarlanmasına izin verir "
              "ve tarama için daha düşük bir eşik (0.3) tercih edilir. Kalan hatalar, sınıfların örtüştüğü doğrusal "
              "karar sınırı boyunca yer alır; daha bilgilendirici öznitelikler (concave points) eşiği ayarlamaktan "
              "daha fazla yardımcı olur."),
        ("h1", "Kaynaklar"),
        ("p", "[1] B. Efron, T. Hastie, I. Johnstone, R. Tibshirani, “Least Angle Regression,” <i>Annals of Statistics</i>, "
              "32(2), 407–499, 2004. (Diabetes veri seti)"),
        ("p", "[2] W. H. Wolberg, W. N. Street, O. L. Mangasarian, “Breast Cancer Wisconsin (Diagnostic),” UCI Machine "
              "Learning Repository, 1995. https://doi.org/10.24432/C5DW2B"),
        ("p", "[3] F. Pedregosa vd., “Scikit-learn: Machine Learning in Python,” <i>JMLR</i>, 12, 2825–2830, 2011."),
        ("p", "[4] G. James, D. Witten, T. Hastie, R. Tibshirani, <i>An Introduction to Statistical Learning</i>, 2. baskı, "
              "Springer, 2021 (Bölüm 3 ve 4)."),
        ("p", "[5] I. Goodfellow, Y. Bengio, A. Courville, <i>Deep Learning</i>, MIT Press, 2016 (Kısım 4.3, 7.8 – "
              "gradyan inişi ve erken durdurma)."),
    ]
    return {"filename": "ML_Lab1_Rapor_TR.pdf", "footer": "ML Lab 1 – Doğrusal ve Lojistik Regresyon",
            "doc_title": "ML Lab 1 – Doğrusal ve Lojistik Regresyon", "story": s}


TEXT = {"en": text_en, "tr": text_tr}

if __name__ == "__main__":
    for lg in (sys.argv[1:] or ["en", "tr"]):
        build(lg)
