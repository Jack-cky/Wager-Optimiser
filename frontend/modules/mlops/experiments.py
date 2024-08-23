import streamlit as st


EXPT = {
    "🎲 Probability Matrix": "Poisson models for goals probabilities.",
    "🎯 Handicap Prediction": "Classification models for handicap results.",
}

EXPT_MT = {
    "🎲 Probability Matrix": ("probability_matrix", "aic"),
    "🎯 Handicap Prediction": ("handicap_prediction", "logloss"),
}


def st_experiment_selection() -> tuple[str | None, str | None]:
    task = st.radio(
        label="Select a machine learning task.",
        options=EXPT,
        captions=EXPT.values(),
        index=None,
        horizontal=True,
    )
    
    expt_metric = EXPT_MT[task] if task else (None, None)
    
    return expt_metric
