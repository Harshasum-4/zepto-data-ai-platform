# Module 2 — Titanic Analytics Report

## Dataset, profiling and cleaning
Raw dataset shape: **(891, 15)**. `info()` and `describe()` are saved in `artifacts/profile.txt`. Missing percentages: {'age': 19.87, 'embarked': 0.22, 'deck': 77.22, 'embark_town': 0.22}. `embarked` is below 5%, so its missing rows are dropped; `age` is between 5% and 30%, so EDA uses median imputation; `deck` is above 30%, so it is retained as the explicit `Missing` category rather than unreliable imputation. `titanic.csv` is the committed offline fallback and is created from the only `sns.load_dataset('titanic')` load.

## Univariate findings
IQR outliers: **age=65**, **fare=114**. Fare mean=32.10, median=14.45, mode=8.05; mean > median > mode, therefore fare is **right-skewed**. Z-score check:

|      |   before_mean |   before_std |      z_mean |   z_std |
|:-----|--------------:|-------------:|------------:|--------:|
| age  |       29.3152 |      12.9776 | 2.71749e-16 |       1 |
| fare |       32.0967 |      49.6695 | 1.39871e-16 |       1 |.

## Bivariate findings
Survival by sex: {'male': np.float64(0.18890814558058924), 'female': np.float64(0.7403846153846154)}. By class: {1: np.float64(0.6261682242990654), 2: np.float64(0.47282608695652173), 3: np.float64(0.24236252545824846)}. By sex and class: {('male', 1): np.float64(0.36885245901639346), ('male', 2): np.float64(0.1574074074074074), ('male', 3): np.float64(0.13544668587896252), ('female', 1): np.float64(0.967391304347826), ('female', 2): np.float64(0.9210526315789473), ('female', 3): np.float64(0.5)}. The correlation matrix uses exactly survived, pclass, age, sibsp, parch and fare; strongest absolute feature pairs are [('fare', 'pclass', np.float64(-0.548)), ('parch', 'sibsp', np.float64(0.415))]. The pclass/fare relationship reflects ticket-class pricing, while the other leading pair indicates family-travel structure associated with the Titanic manifest.

## Four-chart data story
1. `survival_by_sex_class.png`: Women have visibly higher survival across classes. First-class women are the strongest-surviving subgroup, showing both sex and class effects.
2. `fare_class_survival.png`: Higher fares cluster in first class. This chart supports the class-survival gap but does not claim fare itself caused survival.
3. `age_fare_survival.png`: Survivors occur at many ages, while class/fare separation remains visible. Age alone is less decisive than sex and passenger class.
4. `embarked_sex_survival.png`: Survival differs by embarkation port, but the sex gap persists. This suggests port is a contextual feature, not a substitute for sex/class.

## Modeling and recommendation
Class balance: {0: 549, 1: 340} (survived proportion 0.382); stratification preserves this target ratio in both train and test splits. Preprocessing is fit only inside pipelines on `Xtr`, then transformed on `Xte`.

### Classifier metrics
| model               |   accuracy |   precision |   recall |    f1 |   auc |
|:--------------------|-----------:|------------:|---------:|------:|------:|
| Logistic Regression |      0.78  |       0.714 |    0.706 | 0.71  | 0.836 |
| Decision Tree       |      0.785 |       0.825 |    0.553 | 0.662 | 0.806 |
| Random Forest       |      0.771 |       0.685 |    0.741 | 0.712 | 0.827 |

### Imbalance strategies
| strategy               |   precision |   recall |    f1 |
|:-----------------------|------------:|---------:|------:|
| Baseline               |       0.714 |    0.706 | 0.71  |
| Class weight balanced  |       0.681 |    0.753 | 0.715 |
| SMOTE on training fold |       0.691 |    0.765 | 0.726 |

### Random Forest tuning
Best parameters: `{'model__max_depth': 10, 'model__max_features': None, 'model__n_estimators': 400}`. OOB score: **0.833**.

### Regression metrics (separate scale)
|    MAE |   RMSE |    R2 |   Adjusted R2 |
|-------:|-------:|------:|--------------:|
| 19.981 | 38.462 | 0.357 |          0.33 |

### Final grouped model comparison
| model                    |   accuracy |   precision |   recall |      f1 |     auc |     MAE |    RMSE |      R2 |   Adjusted R2 |
|:-------------------------|-----------:|------------:|---------:|--------:|--------:|--------:|--------:|--------:|--------------:|
| Logistic Regression      |      0.78  |       0.714 |    0.706 |   0.71  |   0.836 | nan     | nan     | nan     |        nan    |
| Decision Tree            |      0.785 |       0.825 |    0.553 |   0.662 |   0.806 | nan     | nan     | nan     |        nan    |
| Random Forest            |      0.771 |       0.685 |    0.741 |   0.712 |   0.827 | nan     | nan     | nan     |        nan    |
| Linear Regression (fare) |    nan     |     nan     |  nan     | nan     | nan     |  19.981 |  38.462 |   0.357 |          0.33 |

The residual plot is inspected for a widening/non-random residual spread; fare's long right tail commonly produces **heteroscedasticity**, so predictions are less stable for expensive tickets. I recommend the Random Forest pipeline when it has the best held-out F1/AUC in the table, because it captures nonlinear interactions while using the same leakage-safe preprocessing as the other models. If recall is the operational priority, select the imbalance variant with the highest recall and explicitly accept its precision trade-off. The serialized complete pipeline is `artifacts/best_titanic_pipeline.joblib`; it reloaded successfully and predicted `0` for one raw test row.
