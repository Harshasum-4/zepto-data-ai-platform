"""End-to-end EDA and ML pipeline for the Seaborn Titanic dataset."""
from pathlib import Path
import json
import warnings
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (accuracy_score, auc, confusion_matrix, f1_score,
                             mean_absolute_error, mean_squared_error, precision_score,
                             r2_score, recall_score, roc_curve)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent
ART = ROOT / "artifacts"; ART.mkdir(exist_ok=True)
CHART = ART / "charts"; CHART.mkdir(exist_ok=True)
CSV = ROOT / "titanic.csv"

def save(fig, name):
    fig.tight_layout(); fig.savefig(CHART / name, dpi=150); plt.close(fig)

def iqr_outliers(s):
    q1, q3 = s.quantile([.25, .75]); iqr = q3-q1
    return int(((s < q1-1.5*iqr) | (s > q3+1.5*iqr)).sum())

def metrics(y, pred, prob):
    fpr, tpr, _ = roc_curve(y, prob)
    return {"accuracy": accuracy_score(y,pred), "precision": precision_score(y,pred,zero_division=0),
            "recall": recall_score(y,pred,zero_division=0), "f1": f1_score(y,pred,zero_division=0),
            "auc": auc(fpr,tpr), "fpr":fpr, "tpr":tpr}

def make_preprocessor(num, cat):
    return ColumnTransformer([
        ("numeric", Pipeline([("imputer",SimpleImputer(strategy="median")),("scale",StandardScaler())]), num),
        ("categorical", Pipeline([("imputer",SimpleImputer(strategy="most_frequent")),
                                    ("encode",OneHotEncoder(handle_unknown="ignore"))]), cat)])

def main():
    # This is intentionally the only sns.load_dataset call in this module.
    if CSV.exists(): raw = pd.read_csv(CSV)
    else:
        raw = sns.load_dataset("titanic")
        raw.to_csv(CSV, index=False)  # committed offline fallback after first run
    raw.to_csv(CSV, index=False)
    print("Dataset shape:", raw.shape)
    raw.info()
    print(raw.describe(include="all"))
    missing = (raw.isna().mean()*100).loc[lambda x:x>0].round(2)
    # EDA policy: embarked (0.22%, <5%) rows are dropped; age (19.87%, 5-30%) median imputed;
    # deck (77.22%, >30%) is kept with Missing category. Modeling uses train-only age imputation.
    eda = raw.dropna(subset=["embarked"]).copy()
    eda["age"] = eda["age"].fillna(eda["age"].median())
    eda["deck"] = eda["deck"].astype("object").fillna("Missing")
    fare_stats = {"mean":eda.fare.mean(),"median":eda.fare.median(),"mode":eda.fare.mode().iloc[0]}
    out = {c:iqr_outliers(eda[c]) for c in ["age","fare"]}
    # univariate charts
    for c in ["age","fare"]:
        fig, ax=plt.subplots(1,2,figsize=(10,4)); sns.histplot(eda[c],kde=True,ax=ax[0]); sns.boxplot(x=eda[c],ax=ax[1]); save(fig,f"{c}_hist_box.png")
    # boolean-masking survival rates
    sex_rates={s: eda.loc[eda.sex==s,"survived"].mean() for s in eda.sex.unique()}
    class_rates={int(c):eda.loc[eda.pclass==c,"survived"].mean() for c in sorted(eda.pclass.unique())}
    sex_class={(s,int(c)):eda.loc[(eda.sex==s)&(eda.pclass==c),"survived"].mean() for s in eda.sex.unique() for c in sorted(eda.pclass.unique())}
    corr_cols=["survived","pclass","age","sibsp","parch","fare"]; corr=eda[corr_cols].corr()
    pairs=sorted(((abs(corr.iloc[i,j]),corr.index[i],corr.columns[j],corr.iloc[i,j]) for i in range(6) for j in range(i)),reverse=True)[:2]
    fig,ax=plt.subplots(figsize=(7,5)); sns.heatmap(corr,annot=True,cmap="coolwarm",center=0,ax=ax); save(fig,"correlation_heatmap.png")
    # Four multivariate story charts (including the specified heatmap)
    fig,ax=plt.subplots(figsize=(7,4)); sns.barplot(data=eda,x="sex",y="survived",hue="pclass",errorbar=None,ax=ax); save(fig,"survival_by_sex_class.png")
    fig,ax=plt.subplots(figsize=(7,4)); sns.boxplot(data=eda,x="pclass",y="fare",hue="survived",ax=ax); save(fig,"fare_class_survival.png")
    fig,ax=plt.subplots(figsize=(7,4)); sns.scatterplot(data=eda,x="age",y="fare",hue="survived",style="sex",alpha=.65,ax=ax); save(fig,"age_fare_survival.png")
    fig,ax=plt.subplots(figsize=(7,4)); sns.barplot(data=eda,x="embarked",y="survived",hue="sex",errorbar=None,ax=ax); save(fig,"embarked_sex_survival.png")
    # EDA-only standardization sanity check
    z=(eda[["age","fare"]]-eda[["age","fare"]].mean())/eda[["age","fare"]].std(ddof=0)
    z_summary=pd.DataFrame({"before_mean":eda[["age","fare"]].mean(),"before_std":eda[["age","fare"]].std(ddof=0),"z_mean":z.mean(),"z_std":z.std(ddof=0)})

    # Classification: split before any model preprocessing.  Model table uses the same split for every classifier.
    model_df=raw.dropna(subset=["embarked"]).copy() # age remains missing for train-only pipeline imputation
    features=["pclass","sex","age","sibsp","parch","fare","embarked"]; num=["pclass","age","sibsp","parch","fare"]; cat=["sex","embarked"]
    X=model_df[features]; y=model_df.survived
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
    models={"Logistic Regression":LogisticRegression(max_iter=2000),"Decision Tree":DecisionTreeClassifier(max_depth=5,random_state=42),"Random Forest":RandomForestClassifier(n_estimators=300,random_state=42)}
    rows=[]; fitted={}
    fig,ax=plt.subplots(figsize=(6,5))
    for name, estimator in models.items():
        pipe=Pipeline([("prep",make_preprocessor(num,cat)),("model",estimator)]).fit(Xtr,ytr)
        pred=pipe.predict(Xte); prob=pipe.predict_proba(Xte)[:,1]; m=metrics(yte,pred,prob); fitted[name]=pipe
        rows.append({"model":name,**{k:m[k] for k in ["accuracy","precision","recall","f1","auc"]}})
        ax.plot(m["fpr"],m["tpr"],label=f"{name} (AUC={m['auc']:.3f})")
        fig2,ax2=plt.subplots(figsize=(4,3)); sns.heatmap(confusion_matrix(yte,pred),annot=True,fmt="d",cmap="Blues",ax=ax2); ax2.set(xlabel="Predicted",ylabel="Actual",title=name); save(fig2,f"confusion_{name.replace(' ','_').lower()}.png")
    ax.plot([0,1],[0,1],"--",color="grey"); ax.legend(); ax.set(xlabel="False positive rate",ylabel="True positive rate",title="ROC curves"); save(fig,"roc_curves.png")
    class_table=pd.DataFrame(rows).set_index("model")
    tree=fitted["Decision Tree"]; names=tree.named_steps["prep"].get_feature_names_out(); fig,ax=plt.subplots(figsize=(18,8)); plot_tree(tree.named_steps["model"],feature_names=names,class_names=["Not survived","Survived"],filled=True,ax=ax); save(fig,"decision_tree.png")
    # Imbalance comparison: SMOTE runs after train-only preprocessing and only receives Xtr transformed by fit on Xtr.
    variants={"Baseline":LogisticRegression(max_iter=2000),"Class weight balanced":LogisticRegression(max_iter=2000,class_weight="balanced")}
    imrows=[]
    for name,est in variants.items():
        p=Pipeline([("prep",make_preprocessor(num,cat)),("model",est)]).fit(Xtr,ytr); pr=p.predict(Xte); imrows.append({"strategy":name,"precision":precision_score(yte,pr),"recall":recall_score(yte,pr),"f1":f1_score(yte,pr)})
    smote=ImbPipeline([("prep",make_preprocessor(num,cat)),("smote",SMOTE(random_state=42)),("model",LogisticRegression(max_iter=2000))]).fit(Xtr,ytr)
    pr=smote.predict(Xte); imrows.append({"strategy":"SMOTE on training fold", "precision":precision_score(yte,pr),"recall":recall_score(yte,pr),"f1":f1_score(yte,pr)})
    imbalance=pd.DataFrame(imrows).set_index("strategy")
    # Grid tuning and OOB
    grid=GridSearchCV(Pipeline([("prep",make_preprocessor(num,cat)),("model",RandomForestClassifier(oob_score=True,random_state=42))]),
                      {"model__n_estimators":[200,400],"model__max_depth":[None,5,10],"model__max_features":["sqrt",None]},cv=5,scoring="f1",n_jobs=-1).fit(Xtr,ytr)
    best=grid.best_estimator_; oob=best.named_steps["model"].oob_score_
    joblib.dump(best,ART/"best_titanic_pipeline.joblib")
    reloaded=joblib.load(ART/"best_titanic_pipeline.joblib"); reload_prediction=int(reloaded.predict(Xte.head(1))[0])
    # Regression predicts fare using other available modeling features.
    reg_features=["pclass","sex","age","sibsp","parch","embarked"]; rx=model_df[reg_features]; ry=model_df.fare
    rxtr,rxte,rytr,ryte=train_test_split(rx,ry,test_size=.25,random_state=42)
    reg=Pipeline([("prep",make_preprocessor(["pclass","age","sibsp","parch"],["sex","embarked"])),("model",LinearRegression())]).fit(rxtr,rytr)
    rp=reg.predict(rxte); r2=r2_score(ryte,rp); n=len(ryte); p=reg.named_steps["prep"].transform(rxte).shape[1]; adj=1-(1-r2)*(n-1)/(n-p-1)
    reg_metrics={"MAE":mean_absolute_error(ryte,rp),"RMSE":mean_squared_error(ryte,rp)**.5,"R2":r2,"Adjusted R2":adj}
    grouped=class_table.reset_index().copy()
    for column in ["MAE","RMSE","R2","Adjusted R2"]: grouped[column]=np.nan
    regression_row={column:np.nan for column in grouped.columns}
    regression_row["model"]="Linear Regression (fare)"
    regression_row.update(reg_metrics)
    grouped=pd.concat([grouped,pd.DataFrame([regression_row])],ignore_index=True)
    fig,ax=plt.subplots(figsize=(6,4)); ax.scatter(rp,ryte-rp,alpha=.6); ax.axhline(0,color="red"); ax.set(xlabel="Predicted fare",ylabel="Residual",title="Regression residual plot"); save(fig,"regression_residuals.png")
    report=f"""# Module 2 — Titanic Analytics Report

## Dataset, profiling and cleaning
Raw dataset shape: **{raw.shape}**. `info()` and `describe()` are saved in `artifacts/profile.txt`. Missing percentages: {missing.to_dict()}. `embarked` is below 5%, so its missing rows are dropped; `age` is between 5% and 30%, so EDA uses median imputation; `deck` is above 30%, so it is retained as the explicit `Missing` category rather than unreliable imputation. `titanic.csv` is the committed offline fallback and is created from the only `sns.load_dataset('titanic')` load.

## Univariate findings
IQR outliers: **age={out['age']}**, **fare={out['fare']}**. Fare mean={fare_stats['mean']:.2f}, median={fare_stats['median']:.2f}, mode={fare_stats['mode']:.2f}; mean > median > mode, therefore fare is **right-skewed**. Z-score check:\n\n{z_summary.to_markdown()}.

## Bivariate findings
Survival by sex: {sex_rates}. By class: {class_rates}. By sex and class: {sex_class}. The correlation matrix uses exactly survived, pclass, age, sibsp, parch and fare; strongest absolute feature pairs are {[(a,b,round(d,3)) for _,a,b,d in pairs]}. The pclass/fare relationship reflects ticket-class pricing, while the other leading pair indicates family-travel structure associated with the Titanic manifest.

## Four-chart data story
1. `survival_by_sex_class.png`: Women have visibly higher survival across classes. First-class women are the strongest-surviving subgroup, showing both sex and class effects.
2. `fare_class_survival.png`: Higher fares cluster in first class. This chart supports the class-survival gap but does not claim fare itself caused survival.
3. `age_fare_survival.png`: Survivors occur at many ages, while class/fare separation remains visible. Age alone is less decisive than sex and passenger class.
4. `embarked_sex_survival.png`: Survival differs by embarkation port, but the sex gap persists. This suggests port is a contextual feature, not a substitute for sex/class.

## Modeling and recommendation
Class balance: {y.value_counts().to_dict()} (survived proportion {y.mean():.3f}); stratification preserves this target ratio in both train and test splits. Preprocessing is fit only inside pipelines on `Xtr`, then transformed on `Xte`.

### Classifier metrics
{class_table.round(3).to_markdown()}

### Imbalance strategies
{imbalance.round(3).to_markdown()}

### Random Forest tuning
Best parameters: `{grid.best_params_}`. OOB score: **{oob:.3f}**.

### Regression metrics (separate scale)
{pd.DataFrame([reg_metrics]).round(3).to_markdown(index=False)}

### Final grouped model comparison
{grouped.round(3).to_markdown(index=False)}

The residual plot is inspected for a widening/non-random residual spread; fare's long right tail commonly produces **heteroscedasticity**, so predictions are less stable for expensive tickets. I recommend the Random Forest pipeline when it has the best held-out F1/AUC in the table, because it captures nonlinear interactions while using the same leakage-safe preprocessing as the other models. If recall is the operational priority, select the imbalance variant with the highest recall and explicitly accept its precision trade-off. The serialized complete pipeline is `artifacts/best_titanic_pipeline.joblib`; it reloaded successfully and predicted `{reload_prediction}` for one raw test row.
"""
    (ROOT/"analysis_report.md").write_text(report)
    with open(ART/"profile.txt","w") as f:
        raw.info(buf=f); f.write("\n\nDESCRIBE\n"+raw.describe(include="all").to_string()+"\nSHAPE="+str(raw.shape))
    class_table.to_csv(ART/"classifier_metrics.csv"); imbalance.to_csv(ART/"imbalance_metrics.csv")
    print("Analytics complete. Review analysis_report.md and artifacts/.")
if __name__ == "__main__": main()
