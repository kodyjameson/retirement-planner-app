import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

# Native Streamlit Title
st.title("My DV Retirement Roadmap 🚀")

st.markdown("""<style>.block-container {padding-top: 1rem !important;}</style>""", unsafe_allow_html=True)

# Sidebar Inputs
st.sidebar.header("User Inputs")
current_age = st.sidebar.number_input("Current Age", min_value=18, max_value=100, value=30)
retirement_age = st.sidebar.number_input("Target Retirement Age", min_value=current_age+1, max_value=100, value=65)
starting_balance = st.sidebar.number_input("Current Retirement Balance ($)", min_value=0, value=40000)
monthly_contribution = st.sidebar.number_input("Monthly Retirement Contribution ($)", min_value=0, value=400)
growth_rate = st.sidebar.slider("Annual Growth Rate (%)", min_value=1.0, max_value=12.0, value=7.0) / 100
withdrawal_rate = st.sidebar.slider("Withdrawal Rate After Retirement (%)", min_value=1.0, max_value=10.0, value=4.0) / 100
inflation_rate = st.sidebar.slider("Inflation Rate (%)", min_value=0.0, max_value=10.0, value=2.5) / 100

# Employer Match Inputs
st.sidebar.header("Employer Match")
employer_match_percent = st.sidebar.slider("Employer Match (% of your contribution)", min_value=0, max_value=100, value=100) / 100
employer_match_cap = st.sidebar.number_input("Employer Match Cap ($ per month)", min_value=0, value=400)

# VA Disability Inputs
st.sidebar.header("VA Disability")
married = st.sidebar.checkbox("Married?", value=True)
num_children = st.sidebar.number_input("Number of Dependent Children", min_value=0, value=0)
use_va_table = st.sidebar.checkbox("Use VA Rate Table", value=True)
custom_va_monthly = st.sidebar.number_input("Custom VA Monthly Benefit ($)", min_value=0, value=3877 if not use_va_table else 0)

# Lump Sum Inputs
st.sidebar.header("Lump Sum Contributions")
lump_sum_age = st.sidebar.number_input("Lump Sum Contribution Age", min_value=current_age, max_value=retirement_age, value=current_age)
lump_sum_amount = st.sidebar.number_input("Lump Sum Amount ($)", min_value=0, value=0)

# Social Security Inputs
st.sidebar.header("Social Security")
use_ss = st.sidebar.checkbox("Enable Social Security", value=False)
ss_monthly = st.sidebar.number_input("Monthly Social Security Benefit ($)", min_value=0, value=2200) if use_ss else 0
ss_start_age = st.sidebar.number_input("Social Security Start Age", min_value=retirement_age, max_value=100, value=67) if use_ss else 0

# VA Monthly Benefits Table (2025 estimates)
va_benefits_single = {
    0: 0.00,
    10: 171.23,
    20: 338.49,
    30: 529.83,
    40: 755.28,
    50: 1075.16,
    60: 1350.90,
    70: 1701.48,
    80: 1980.46,
    90: 2232.75,
    100: 3627.22
}

va_benefits_married = {
    0: 0.00,
    10: 171.23,
    20: 338.49,
    30: 529.83,
    40: 755.28,
    50: 1075.16,
    60: 1350.90,
    70: 1701.48,
    80: 1980.46,
    90: 2232.75,
    100: 3877.22
}

va_disability_percent = st.sidebar.selectbox("VA Disability %", list(va_benefits_single.keys()), index=10)
if married:
    va_monthly_base = va_benefits_married[va_disability_percent]
else:
    va_monthly_base = va_benefits_single[va_disability_percent]

va_monthly = va_monthly_base if use_va_table else custom_va_monthly

# Calculations
years = np.arange(current_age, 101)
balances = []
va_income_stream = []
retirement_income_stream = []
retirement_plus_va_stream = []
retirement_plus_va_plus_ss_stream = []
withdrawals = []

balance = starting_balance

for year in years:
    if year == lump_sum_age:
        balance += lump_sum_amount

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
    withdrawals.append(withdrawal)
    va_income_stream.append(va_monthly)
    retirement_income_stream.append(retirement_income)
    retirement_plus_va_stream.append(total_va_retirement)
    retirement_plus_va_plus_ss_stream.append(total_va_retirement_ss)

# DataFrame
df = pd.DataFrame({
    "Age": years,
    "Retirement Balance ($)": balances,
    "Annual Withdrawal ($)": withdrawals,
    "VA Monthly ($)": va_income_stream,
    "Retirement Monthly ($)": retirement_income_stream,
    "VA + Retirement ($)": retirement_plus_va_stream,
    "VA + Retirement + SS ($)": retirement_plus_va_plus_ss_stream
})

# Charts
st.markdown("### Retirement Account Balance Over Time")
config = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
    "displaylogo": False
}

balance_fig = go.Figure()
balance_fig.add_trace(go.Scatter(x=df["Age"], y=df["Retirement Balance ($)"], mode='lines', name='Balance',
    hovertemplate = "$%{y:,.0f}"))
balance_fig.update_layout(title="", xaxis_title="Age", yaxis_title="Balance ($)", yaxis=dict(rangemode='tozero'), template="plotly_white")
st.plotly_chart(balance_fig, use_container_width=True, config=config)

st.markdown("### Monthly Income Streams Over Time")
income_fig = go.Figure()
income_fig.add_trace(go.Scatter(x=df["Age"], y=df["VA Monthly ($)"], mode='lines', name='VA Monthly Income', line=dict(color='green'),
    hovertemplate = "$%{y:,.0f}"))
income_fig.add_trace(go.Scatter(x=df["Age"], y=df["VA + Retirement ($)"], mode='lines', name='VA + Retirement Income', line=dict(color='orange'),
    hovertemplate = "$%{y:,.0f}"))

if use_ss:
    income_fig.add_trace(go.Scatter(x=df["Age"], y=df["VA + Retirement + SS ($)"], mode='lines', name='VA + Retirement + SS Income', line=dict(color='blue'),
    hovertemplate = "$%{y:,.0f}"))

income_fig.update_layout(title="", xaxis_title="Age", yaxis_title="Monthly Income ($)", yaxis=dict(rangemode='tozero'), template="plotly_white")
st.plotly_chart(income_fig, use_container_width=True, config=config)

# Summary
st.markdown("### Summary at Retirement Age")
retirement_balance = df.loc[df['Age'] == retirement_age, 'Retirement Balance ($)'].values[0]
retirement_withdrawal = retirement_balance * withdrawal_rate
retirement_monthly_withdrawal = retirement_withdrawal / 12
monthly_income_at_retirement = va_monthly + retirement_monthly_withdrawal
st.write(f"**Projected Retirement Savings at Age {retirement_age}:** ${retirement_balance:,.2f}")
st.write(f"**Monthly Income at Retirement (VA + Withdrawals):** ${monthly_income_at_retirement:,.2f}")

# CSV Download
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(df)
st.download_button(
    label="Download Full Projection as CSV",
    data=csv,
    file_name='retirement_projection.csv',
    mime='text/csv',
)

# Show Table
st.markdown("### Detailed Year-by-Year Table")
st.dataframe(df.style.format({
    "Retirement Balance ($)": "${:,.2f}",
    "Annual Withdrawal ($)": "${:,.2f}",
    "VA Monthly ($)": "${:,.2f}",
    "Retirement Monthly ($)": "${:,.2f}",
    "VA + Retirement ($)": "${:,.2f}",
    "VA + Retirement + SS ($)": "${:,.2f}"
}))