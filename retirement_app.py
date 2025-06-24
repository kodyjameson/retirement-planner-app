import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

# SaaS Guided Flow Onboarding State
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'data' not in st.session_state:
    st.session_state.data = {}

def next_step():
    st.session_state.step += 1

def reset():
    st.session_state.step = 1
    st.session_state.data = {}

# Reset button for development
st.sidebar.button("Restart", on_click=reset)

# Onboarding Flow
st.title("My DV Retirement Roadmap 🚀")

if st.session_state.step == 1:
    st.header("Welcome!")
    st.write("Let's build your personalized retirement projection. Just answer a few quick questions.")
    st.button("Start", on_click=next_step)

elif st.session_state.step == 2:
    current_age = st.number_input("How old are you today?", min_value=18, max_value=100, value=30)
    if st.button("Next"):
        st.session_state.data['current_age'] = current_age
        next_step()

elif st.session_state.step == 3:
    retirement_choice = st.radio(
        "Do you know your target retirement age?",
        ("Yes, I know my retirement age", "I'm not sure yet — show me scenarios")
    )
    st.session_state.data['retirement_choice'] = retirement_choice
    if retirement_choice == "Yes, I know my retirement age":
        retirement_age = st.number_input("At what age would you like to retire?", min_value=st.session_state.data['current_age']+1, max_value=100, value=65)
        if st.button("Next"):
            st.session_state.data['retirement_age'] = retirement_age
            next_step()
    else:
        if st.button("Next"):
            next_step()

elif st.session_state.step == 4:
    starting_balance = st.number_input("How much do you currently have saved for retirement? ($)", min_value=0, value=40000)
    if st.button("Next"):
        st.session_state.data['starting_balance'] = starting_balance
        next_step()

elif st.session_state.step == 5:
    monthly_contribution = st.number_input("How much do you contribute monthly? ($)", min_value=0, value=400)
    if st.button("Next"):
        st.session_state.data['monthly_contribution'] = monthly_contribution
        next_step()

elif st.session_state.step == 6:
    employer_match_percent = st.slider("Employer match (% of your contribution)", min_value=0, max_value=100, value=100)
    employer_match_cap = st.number_input("Employer match cap ($ per month)", min_value=0, value=400)
    if st.button("Next"):
        st.session_state.data['employer_match_percent'] = employer_match_percent
        st.session_state.data['employer_match_cap'] = employer_match_cap
        next_step()

elif st.session_state.step == 7:
    married = st.checkbox("Are you married?", value=True)
    va_disability_percent = st.selectbox("What is your VA Disability %?", [0,10,20,30,40,50,60,70,80,90,100], index=10)
    if st.button("Next"):
        st.session_state.data['married'] = married
        st.session_state.data['va_disability_percent'] = va_disability_percent
        next_step()

elif st.session_state.step == 8:
    use_ss = st.checkbox("Do you plan to take Social Security?", value=True)
    if use_ss:
        ss_monthly = st.number_input("Estimated Monthly Social Security Benefit ($)", min_value=0, value=2200)
        ss_start_age = st.number_input("At what age would you like to start Social Security?", min_value=st.session_state.data['current_age'], max_value=100, value=67)
    else:
        ss_monthly = 0
        ss_start_age = 0
    if st.button("Finish"):
        st.session_state.data['use_ss'] = use_ss
        st.session_state.data['ss_monthly'] = ss_monthly
        st.session_state.data['ss_start_age'] = ss_start_age
        next_step()

# Modeling After Onboarding
if st.session_state.step >= 9:

    # Assign defaults if user didn't select retirement age
    current_age = st.session_state.data['current_age']
    if st.session_state.data['retirement_choice'] == "Yes, I know my retirement age":
        retirement_age = st.session_state.data['retirement_age']
    else:
        retirement_age = 65  # Default for modeling multiple scenarios later

    starting_balance = st.session_state.data['starting_balance']
    monthly_contribution = st.session_state.data['monthly_contribution']
    employer_match_percent = st.session_state.data['employer_match_percent'] / 100
    employer_match_cap = st.session_state.data['employer_match_cap']
    married = st.session_state.data['married']
    va_disability_percent = st.session_state.data['va_disability_percent']
    use_ss = st.session_state.data['use_ss']
    ss_monthly = st.session_state.data['ss_monthly']
    ss_start_age = st.session_state.data['ss_start_age']

    growth_rate = 0.07
    withdrawal_rate = 0.04

    va_benefits_single = {0:0.00,10:171.23,20:338.49,30:529.83,40:755.28,50:1075.16,60:1350.90,70:1701.48,80:1980.46,90:2232.75,100:3627.22}
    va_benefits_married = {0:0.00,10:171.23,20:338.49,30:529.83,40:755.28,50:1075.16,60:1350.90,70:1701.48,80:1980.46,90:2232.75,100:3877.22}

    va_monthly = va_benefits_married[va_disability_percent] if married else va_benefits_single[va_disability_percent]

    years = np.arange(current_age, 101)
    balances, va_income_stream, retirement_plus_va_stream, retirement_plus_va_plus_ss_stream = [], [], [], []
    balance = starting_balance

    for year in years:
        if year <= retirement_age:
            employer_match = min(monthly_contribution * employer_match_percent, employer_match_cap)
            total_monthly_contribution = monthly_contribution + employer_match
            balance = balance * (1 + growth_rate) + (total_monthly_contribution * 12)
            withdrawal = 0
            retirement_income = 0
        else:
            withdrawal = balance * withdrawal_rate
            balance = balance * (1 + growth_rate) - withdrawal
            balance = max(balance, 0)
            retirement_income = withdrawal / 12

        total_va_retirement = va_monthly + retirement_income
        total_va_retirement_ss = total_va_retirement
        if use_ss and year >= ss_start_age:
            total_va_retirement_ss += ss_monthly

        balances.append(balance)
        va_income_stream.append(va_monthly)
        retirement_plus_va_stream.append(total_va_retirement)
        retirement_plus_va_plus_ss_stream.append(total_va_retirement_ss)

    df = pd.DataFrame({
        "Age": years,
        "Retirement Balance ($)": balances,
        "VA Monthly ($)": va_income_stream,
        "VA + Retirement ($)": retirement_plus_va_stream,
        "VA + Retirement + SS ($)": retirement_plus_va_plus_ss_stream
    })

    st.subheader("Retirement Account Balance Over Time")
    balance_fig = go.Figure()
    balance_fig.add_trace(go.Scatter(x=df["Age"], y=df["Retirement Balance ($)"], mode='lines', name='Balance',
        hovertemplate = "$%{y:,.0f}"))
    balance_fig.update_layout(template="plotly_white", yaxis=dict(rangemode='tozero'))
    st.plotly_chart(balance_fig, use_container_width=True)

    st.subheader("Monthly Income Streams Over Time")
    income_fig = go.Figure()
    income_fig.add_trace(go.Scatter(x=df["Age"], y=df["VA Monthly ($)"], mode='lines', name='VA Monthly Income', line=dict(color='green')))
    income_fig.add_trace(go.Scatter(x=df["Age"], y=df["VA + Retirement ($)"], mode='lines', name='VA + Retirement Income', line=dict(color='orange')))
    if use_ss:
        income_fig.add_trace(go.Scatter(x=df["Age"], y=df["VA + Retirement + SS ($)"], mode='lines', name='VA + Retirement + SS Income', line=dict(color='blue')))
    income_fig.update_layout(template="plotly_white", yaxis=dict(rangemode='tozero'))
    st.plotly_chart(income_fig, use_container_width=True)

    st.success("Model complete! Use the Restart button if you'd like to update your scenario.")
