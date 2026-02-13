import streamlit as st
from estimator import evaluate

st.set_page_config(page_title="Back-of-the-Envelope Calculator", layout="wide")
st.title("Back-of-the-Envelope Calculator")
st.caption("Quick estimations for system design")

# --- State ---
if "estimates" not in st.session_state:
    st.session_state.estimates = []
if "last_error" not in st.session_state:
    st.session_state.last_error = None

# Handle reset: set defaults *before* widgets are instantiated
if st.session_state.get("_reset"):
    st.session_state["_reset"] = False
    st.session_state["form_label"] = ""
    st.session_state["form_expr"] = ""
    st.session_state["form_unit"] = "auto"
    st.session_state["form_rate"] = "none"
    st.session_state.last_error = None

left, right = st.columns([1, 1], gap="large")

# --- Left: Input form ---
with left:
    with st.form("calc_form", clear_on_submit=False):
        label = st.text_input("Label", placeholder="e.g. Writes per second", key="form_label")
        expression = st.text_input(
            "Expression",
            placeholder="e.g. 500 million / month, 30 billion * 500 bytes",
            key="form_expr",
        )
        col1, col2 = st.columns(2)
        with col1:
            target_unit = st.selectbox("Unit", ["auto", "bytes", "KB", "MB", "GB", "TB", "PB", "none"], key="form_unit")
        with col2:
            rate = st.selectbox("Rate", ["none", "/s", "/min", "/hour", "/day", "/month", "/year"], key="form_rate")
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            submitted = st.form_submit_button("Add Estimate", use_container_width=True)
        with btn_col2:
            reset = st.form_submit_button("Reset Fields", use_container_width=True)

    if reset:
        st.session_state["_reset"] = True
        st.rerun()

    if submitted and expression:
        try:
            result = evaluate(expression, target_unit, rate)
            result["label"] = label or expression
            st.session_state.estimates.append(result)
            st.session_state.last_error = None
        except Exception as e:
            st.session_state.last_error = str(e)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

# --- Right: Estimates + Summary ---
with right:
    if st.session_state.estimates:
        st.subheader("Estimates")
        to_delete = None
        for i, est in enumerate(st.session_state.estimates):
            col_text, col_btn = st.columns([6, 1])
            with col_text:
                st.markdown(f"**{i + 1}. {est['label']}:** {est['expression']} = **{est['result_display']}**")
            with col_btn:
                if st.button("x", key=f"del_{i}"):
                    to_delete = i

        if to_delete is not None:
            st.session_state.estimates.pop(to_delete)
            st.rerun()

        st.divider()
        st.subheader("Summary")
        summary_lines = []
        for est in st.session_state.estimates:
            summary_lines.append(f"{est['label']}: {est['expression']} = {est['result_display']}")
        st.code("\n".join(summary_lines), language=None)
    else:
        st.info("Estimates will appear here as you add them.")
