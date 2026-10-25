# ML Lab 1 – Linear and Logistic Regression / Doğrusal ve Lojistik Regresyon

## Contents / İçerik

| Folder | Content |
|---|---|
| `report/ML_Lab1_Report_EN.pdf` | Final report (English) – the file to submit |
| `report/ML_Lab1_Rapor_TR.pdf` | Same report in Turkish / Raporun Türkçe sürümü |
| `data/` | Both datasets as CSV (`diabetes_regression.csv`, `breast_cancer_classification.csv`) |
| `code/` | Python source code for every experiment and the report |
| `figures/` | All figures (PNG, 200 dpi) used in the report |
| `results/` | All numeric results (JSON / CSV) the report is generated from |

## Datasets / Veri setleri
- **Linear regression:** Diabetes dataset (Efron et al., 2004) – 442 patients, 10 features, continuous target. Raw units via `sklearn.datasets.load_diabetes(scaled=False)`.
- **Logistic regression:** Breast Cancer Wisconsin (Diagnostic), UCI – 569 samples, binary target (malignant = 1). Via `sklearn.datasets.load_breast_cancer()`.

Both datasets ship with scikit-learn, so no download is needed. Also available on Kaggle/UCI.

## How to reproduce / Nasıl çalıştırılır
```bash
pip install -r requirements.txt
cd code
python run_all.py
```
This regenerates `data/`, `figures/`, `results/` and both PDFs.

| Script | Part |
|---|---|
| `common.py` | paths, random seed (42), test size (0.20), plot style |
| `part_a_data.py` | Part A – datasets, CSV export, exploration figures |
| `part_b_linear.py` | Part B – B1 baseline OLS, B2 scaling, B3 learning rate (own NumPy gradient descent) |
| `part_c_logistic.py` | Part C – C1 model, C2 thresholds (selected with 5-fold CV on training data), C3 one vs. two features + decision boundary |
| `build_report.py` | Builds the English and Turkish PDF reports from `results/` and `figures/` |

Settings: Python 3.13, scikit-learn 1.9.1, 80/20 split, `random_state=42`, StandardScaler fitted on training data only, LogisticRegression(lbfgs, C=1.0).

**Note:** Fill in your name and student number on the report cover page (`build_report.py`, search for "Student" / "Öğrenci").
