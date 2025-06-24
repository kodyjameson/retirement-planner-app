import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import json

# Initialize state for SaaS Scenario Engine
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'data' not in st.session_state:
    st.session_state.data = {}
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = {}

# Callback functions for clean step transitions
def go_to_step(step_num):
    st.session_state.step = step_num

def reset():
    st.session_state.step = 1
    st.session_state.data = {}

# Scenario Engine UI
st.sidebar.header("Scenario Manager")
if st.sidebar.button("Start New Scenario"):
    reset()

if st.session_state.scenarios:
    selected = st.sidebar.selectbox("Load Saved Scenario", list(st.session_state.scenarios.keys()))
    if st.sidebar.button("Load Scenario"):
        st.session_state.data = json.loads(st.session_state.scenarios[selected])
        st.session_state.step = 9

# SaaS Guided Onboarding Flow
st.markdown("""<h1 style='text-align: center; color: #ffffff;'>My DV Retirement Roadmap 🚀</h1>""", unsafe_allow_html=True)

# Visual progress bar
progress = (st.session_state.step - 1) / 8 if st.session_state.step <= 9 else 1
st.progress(progress)

if st.session_state.step == 1:
    st.header("Welcome!")
    st.write("Let's build your personalized retirement projection. Just answer a few quick questions.")
    st.button("Start", on_click=lambda: go_to_step(2))

elif st.session_state.step == 2:
    current_age = st.number_input("How old are you today?", min_value=18, max_value=100, value=30)
    st.button("Next", on_click=lambda: (st.session_state.data.update({'current_age': current_age}), go_to_step(3)))

elif st.session_state.step == 3:
    retirement_choice = st.radio("Do you know your target retirement age?", ("Yes, I know my retirement age", "I'm not sure yet — show me scenarios"))
    st.session_state.data['retirement_choice'] = retirement_choice
    if retirement_choice == "Yes, I know my retirement age":
        retirement_age = st.number_input("At what age would you like to retire?", min_value=st.session_state.data['current_age']+1, max_value=100, value=65)
        st.button("Next", on_click=lambda: (st.session_state.data.update({'retirement_age': retirement_age}), go_to_step(4)))
    else:
        st.button("Next", on_click=lambda: go_to_step(4))

elif st.session_state.step == 4:
    starting_balance = st.number_input("How much do you currently have saved for retirement? ($)", min_value=0, value=40000)
    st.button("Next", on_click=lambda: (st.session_state.data.update({'starting_balance': starting_balance}), go_to_step(5)))

elif st.session_state.step == 5:
    monthly_contribution = st.number_input("How much do you contribute monthly? ($)", min_value=0, value=400)
    st.button("Next", on_click=lambda: (st.session_state.data.update({'monthly_contribution': monthly_contribution}), go_to_step(6)))

elif st.session_state.step == 6:
    employer_match_percent = st.slider("Employer match (% of your contribution)", min_value=0, max_value=100, value=100)
    employer_match_cap = st.number_input("Employer match cap ($ per month)", min_value=0, value=400)
    st.button("Next", on_click=lambda: (st.session_state.data.update({'employer_match_percent': employer_match_percent, 'employer_match_cap': employer_match_cap}), go_to_step(7)))

elif st.session_state.step == 7:
    married = st.checkbox("Are you married?", value=True)
    va_disability_percent = st.selectbox("What is your VA Disability %?", [0,10,20,30,40,50,60,70,80,90,100], index=10)
    st.button("Next", on_click=lambda: (st.session_state.data.update({'married': married, 'va_disability_percent': va_disability_percent}), go_to_step(8)))

elif st.session_state.step == 8:
    use_ss = st.checkbox("Do you plan to take Social Security?", value=True)
    if use_ss:
        ss_monthly = st.number_input("Estimated Monthly Social Security Benefit ($)", min_value=0, value=2200)
        ss_start_age = st.number_input("At what age would you like to start Social Security?", min_value=st.session_state.data['current_age'], max_value=100, value=67)
    else:
        ss_monthly, ss_start_age = 0, 0
    st.button("Finish", on_click=lambda: (st.session_state.data.update({'use_ss': use_ss, 'ss_monthly': ss_monthly, 'ss_start_age': ss_start_age}), go_to_step(9)))

# Modeling and Save Scenario
if st.session_state.step >= 9:

    current_age = st.session_state.data['current_age']
    retirement_age = st.session_state.data.get('retirement_age', 65)
    starting_balance = st.session_state.data['starting_balance']
    monthly_contribution = st.session_state.data['monthly_contribution']
    employer_match_percent = st.session_state.data['employer_match_percent'] / 100
    employer_match_cap = st.session_state.data['employer_match_cap']
    married = st.session_state.data['married']
    va_disability_percent = st.session_state.data['va_disability_percent']
    use_ss = st.session_state.data['use_ss']
    ss_monthly = st.session_state.data['ss_monthly']
    ss_start_age = st.session_state.data['ss_start_age']

    growth_rate, withdrawal_rate = 0.07, 0.04

    va_benefits_single = {0:0,10:171.23,20:338.49,30:529.83,40:755.28,50:1075.16,60:1350.90,70:1701.48,80:1980.46,90:2232.75,100:3627.22}
    va_benefits_married = {0:0,10:171.23,20:338.49,30:529.83,40:755.28,50:1075.16,60:1350.90,70:1701.48,80:1980.46,90:2232.75,100:3877.22}
    va_monthly = va_benefits_married[va_disability_percent] if married else va_benefits_single[va_disability_percent]

    years = np.arange(current_age, 101)
    balances, va_stream, total_income, total_with_ss = [], [], [], []
    balance = starting_balance

    for year in years:
        if year <= retirement_age:
            match = min(monthly_contribution * employer_match_percent, employer_match_cap)
            total_contribution = monthly_contribution + match
            balance = balance * (1 + growth_rate) + (total_contribution * 12)
            withdrawal, retirement_income = 0, 0
        else:
            withdrawal = balance * withdrawal_rate
            balance = balance * (1 + growth_rate) - withdrawal
            balance = max(balance, 0)
            retirement_income = withdrawal / 12

        income = va_monthly + retirement_income
        income_ss = income + (ss_monthly if use_ss and year >= ss_start_age else 0)

        balances.append(balance)
        va_stream.append(va_monthly)
        total_income.append(income)
        total_with_ss.append(income_ss)

    df = pd.DataFrame({
        "Age": years,
        "Retirement Balance ($)": balances,
        "VA Income ($)": va_stream,
        "VA + Retirement Income ($)": total_income,
        "VA + Retirement + SS ($)": total_with_ss
    })

    # Retirement Balance Chart
    st.subheader("Retirement Balance Over Time")
    fig_bal = go.Figure()
    fig_bal.add_trace(go.Scatter(x=df["Age"], y=df["Retirement Balance ($)"], mode='lines+markers', name='Balance', line=dict(color='#0080FF', shape='spline', smoothing=1.3), marker=dict(size=4, color='#0080FF')))
    fig_bal.update_layout(template="plotly_dark", yaxis_title="Balance ($)", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    st.plotly_chart(fig_bal, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    age_select_bal = st.slider("Select Age for Balance", int(current_age), 100, int(retirement_age))
    selected_row_bal = df[df["Age"] == age_select_bal].iloc[0]
    st.info(f"At age {age_select_bal}, Retirement Balance: ${selected_row_bal['Retirement Balance ($)']:,.0f}")

    # Income Chart
    st.subheader("Monthly Income Over Time")
    fig_inc = go.Figure()
    fig_inc.add_trace(go.Scatter(x=df["Age"], y=df["VA Income ($)"], mode='lines+markers', name='VA Income', line=dict(color='lime', shape='spline', smoothing=1.3), marker=dict(size=4, color='lime')))
    fig_inc.add_trace(go.Scatter(x=df["Age"], y=df["VA + Retirement Income ($)"], mode='lines+markers', name='VA + Retirement', line=dict(color='orange', shape='spline', smoothing=1.3), marker=dict(size=4, color='orange')))
    fig_inc.add_trace(go.Scatter(x=df["Age"], y=df["VA + Retirement + SS ($)"], mode='lines+markers', name='With SS', line=dict(color='deepskyblue', shape='spline', smoothing=1.3), marker=dict(size=4, color='deepskyblue')))
    fig_inc.update_layout(template="plotly_dark", yaxis_title="Monthly Income ($)", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    st.plotly_chart(fig_inc, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    age_select_inc = st.slider("Select Age for Income", int(current_age), 100, int(retirement_age))
    selected_row_inc = df[df["Age"] == age_select_inc].iloc[0]
    st.info(f"At age {age_select_inc}: VA Income: ${selected_row_inc['VA Income ($)']:,.0f}, VA+Retirement: ${selected_row_inc['VA + Retirement Income ($)']:,.0f}, VA+Retirement+SS: ${selected_row_inc['VA + Retirement + SS ($)']:,.0f}")

    st.success("Model complete! Save this scenario below.")

    scenario_name = st.text_input("Scenario Name")
    if st.button("Save Scenario") and scenario_name:
        st.session_state.scenarios[scenario_name] = json.dumps(st.session_state.data)
        st.success(f"Scenario '{scenario_name}' saved!")