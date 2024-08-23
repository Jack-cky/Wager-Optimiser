from datetime import date, datetime

import h2o
import mlflow
import pandas as pd
import streamlit as st
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient
from sklearn.metrics import classification_report, f1_score

from utils import st_current_date_time, st_message_box, st_row_spacing, st_subtitle_centre


mlflow.set_tracking_uri("backend/mlruns")

MSG_BTN_DISABLE = "Function is disabled in demo."


def st_experiment_selection() -> tuple[str | None, str | None]:
    EXPT = {
        "🎲 Probability Matrix": "Poisson models for goals probabilities.",
        "🎯 Handicap Prediction": "Classification models for handicap results.",
    }

    EXPT_MT = {
        "🎲 Probability Matrix": ("probability_matrix", "aic"),
        "🎯 Handicap Prediction": ("handicap_prediction", "logloss"),
    }
    
    task = st.radio(
        label="Select a machine learning task.",
        options=EXPT,
        captions=EXPT.values(),
        index=None,
        horizontal=True,
    )
    
    expt_metric = EXPT_MT[task] if task else (None, None)
    
    return expt_metric


def st_leaderboard(expt: str, metric: str) -> tuple[dict, list, list]:
    def get_leadboard(expt: str, metric: str) -> dict:
        client = MlflowClient()
        
        _ = mlflow.set_experiment(expt)
        
        runs = mlflow.search_runs(run_view_type=ViewType.ACTIVE_ONLY)
        
        runs["dt"] = runs["tags.mlflow.runName"].str[-12:]
        runs["Trained at"] = pd.to_datetime(runs["dt"], format="%Y%m%d%H%M") \
            .dt.strftime("%Y/%m/%d %H:%M")
        runs[f"{metric.upper()}"] = runs[f"metrics.{metric}"].round(2)
        runs = runs[["run_id", "Trained at", metric.upper()]].copy()
        
        data = [
            (model.version, model.aliases, model.run_id, model.tags["season"])
            for model in client.search_model_versions(f"name='{expt}'")
        ]
        smy = pd.DataFrame(data, columns=["Version", "In Use", "run_id", "Season"])
        smy["In Use"] = smy["In Use"].str.len() == 1
        
        smy = smy.merge(runs) \
            .assign(option=False) \
            .to_dict()
        
        return smy
    
    st_subtitle_centre("Leaderboard")
    
    response = get_leadboard(expt, metric)
    
    lb = pd.DataFrame() \
        .from_dict(response) \
        .sort_values(by=metric.upper())
    
    opts = st.data_editor(
        lb.drop(columns="run_id"),
        column_config={
            "option": st.column_config.CheckboxColumn(
                "Option",
                help="Select model(s) for the following actions.",
                default=False,
            )
        },
        disabled=["In Use"],
        hide_index=True,
        use_container_width=True,
    )
    
    run_ids = lb.loc[opts["option"], ["run_id", "In Use"]] \
        .set_index("run_id") \
        .to_dict()["In Use"]
    
    model_vers = lb.loc[opts["option"], "Version"] \
        .astype(str) \
        .to_list()
    
    model_seas = lb.loc[opts["option"], "Season"] \
        .astype(str) \
        .to_list()
    
    return run_ids, model_vers, model_seas


def st_training(expt: str, seas_curr: int=date.today().year) -> None:
    def get_pre_train_summary(expt: str, season: int) -> tuple[int, int]:
        if expt == "probability_matrix":
            df = pd.read_parquet("./data/featured/goals.parquet")[["season"]]
            
            train_size = len(df.query(f"season <= {season}"))
            dev_size = 0
        
        elif expt == "handicap_prediction":
            df = pd.read_parquet("./data/featured/j1_league.parquet")[["season"]]
            
            train_size = len(df.query(f"season <= {season-1}"))
            dev_size = len(df.query(f"season == {season}"))
        
        return train_size, dev_size
    
    def pre_train_summary(expt: str, seas: int) -> None:
        response = get_pre_train_summary(expt, seas)
        
        train_dev_size = response
        
        st.markdown(
            f"""
            Model will be trained in the following split size:
            - Train: {train_dev_size[0]:,}
            - Dev: {train_dev_size[1]:,}
            """
        )
    
    msg = None
    
    st_subtitle_centre("Model Training")
    
    with st.expander("Options", icon="🚀"):
        seasons = [seas for seas in range(seas_curr-1, 2012, -1)]
        season = st.selectbox("Select a season", seasons, index=None)
        
        st.button("Train a **SEASON** model", disabled=True, help=MSG_BTN_DISABLE, use_container_width=True)
        
        st.button("Train a **LATEST** model", disabled=True, help=MSG_BTN_DISABLE, use_container_width=True)
        
        if not season:
            season = seas_curr
        
        st.divider()
        st_subtitle_centre("Pre-Traing Summary")
        
        pre_train_summary(expt, season)
    
    return msg


def st_registration(run_ids: list) -> tuple[str, str]:
    msg = None
    
    n_ids = len(run_ids)
    
    st_subtitle_centre("Model Register")
    
    st.button("Register", disabled=True, help=MSG_BTN_DISABLE, use_container_width=True)
    
    return msg


def st_evaluation(expt: str, model_vers: list, model_seas: list) -> str | dict:
    def evaluate_handicap_model(version: str) -> list[str, float, str]:
        clf_hc = mlflow.h2o.load_model(f"models:/handicap_prediction/{version}")
        clf_bd = mlflow.h2o.load_model(f"models:/bet_decision/{version}")
        
        curr_seas = datetime.now().year
        
        test = pd.read_parquet("./data/featured/j1_league.parquet") \
            .query(f"season == {curr_seas}") \
            .drop(columns="season")
        
        # step 1 prediction
        test_h2o = h2o.H2OFrame(test)
        
        prediction = clf_hc.predict(test_h2o)
        
        # step 2 prediction
        test_pred = prediction.as_data_frame()
        test_pred["probability"] = test_pred[["A", "H"]].max(axis=1)
        test_pred["actual"] = test.reset_index(drop=True)["res"]
        
        dscn_h2o = h2o.H2OFrame(test_pred[["predict", "probability"]])
        dscn_pred = clf_bd.predict(dscn_h2o)
        
        test_pred["decision"] = dscn_pred.as_data_frame()["predict"]
        
        pred = test_pred.query("decision == 1")
        y_hat = pred["predict"]
        y_true = pred["actual"]
        
        # metrics
        f1 = f1_score(y_true, y_hat, pos_label="H", average="macro")
        f1 = round(f1, 2)
        
        report = classification_report(y_true, y_hat)
        
        return [version, f1, report]

    def evaluate_handicap_models(versions: list) -> dict:
        results = []
        for version in versions.split(","):
            result = evaluate_handicap_model(version)
            results.append(result)
        
        col = ["Version", "F1 Score", "report"]
        evaluation = pd.DataFrame(results, columns=col) \
            .to_dict()
        
        return evaluation
    
    msg = None
    
    n_ids = len(model_vers)
    
    if expt == "handicap_prediction":
        st_subtitle_centre("Model Evaluation")
        
        if st.button("Evaluate", use_container_width=True):
            if n_ids != 0:
                if n_ids <= 5 and "Latest" not in model_seas:
                    vers = ",".join(model_vers)
                    response = evaluate_handicap_models(vers)
                    
                    msg = response
            
            else:
                msg = "Evaluating models appears to be missing.", "warning"
    
    return msg


def st_system_response(msg_train: tuple, msg_register: tuple, msg_evaluate: tuple | dict) -> None:
    def evaluation_message(msg: dict) -> None:
        VERSION_MT = {1: "🥇", 2: "🥈", 3: "🥉", 4: "🤡", 5: "💩"}
        
        df = pd.DataFrame().from_dict(msg) \
            .sort_values(by="F1 Score", ascending=False) \
            .reset_index(drop=True)
        
        st_subtitle_centre("F1 Scores on Current Season")
        
        st.bar_chart(df, x="Version", y="F1 Score", horizontal=True)
        
        st_subtitle_centre("Classification Reports")
        
        for idx, rw in df.iterrows():
            rnk = VERSION_MT[idx+1]
            title = f"Model [{rw['Version']}]: Report Details"
            
            with st.expander(title, expanded=not idx, icon=rnk):
                with st.columns((1, 9))[1]:
                    report = f"Avg. F1-Scores: {rw['F1 Score']}\n\n" + rw["report"]
                    st.text(report)
    
    if msg_train:
        st_message_box(*msg_train)
    
    if msg_register:
        st_message_box(*msg_register)
    
    if msg_evaluate:
        if isinstance(msg_evaluate, tuple):
            st_message_box(*msg_evaluate)
        
        else:
            evaluation_message(msg_evaluate)
    
    if msg_train or msg_register or msg_evaluate:
        with st.columns(5)[4]:
            st.button("Refresh", use_container_width=True)


def mlops_menu() -> None:
    st.header(":rainbow[MLOps]")
    st.button("Update J1 data", disabled=True, help=MSG_BTN_DISABLE)
    st_row_spacing(3)
    
    expt, metric = st_experiment_selection()
    st_row_spacing(2)
    
    if expt:
        run_ids, model_vers, model_seas = st_leaderboard(expt, metric)
        st_row_spacing(2)
        
        div_left, div_middle, div_right = st.columns(3)
        with div_left:
            msg_train = st_training(expt)
        with div_middle:
            msg_register = st_registration(run_ids)
        with div_right:
            msg_evaluate = st_evaluation(expt, model_vers, model_seas)
        st_row_spacing(2)
        
        st_system_response(msg_train, msg_register, msg_evaluate)
    
    st_current_date_time()
