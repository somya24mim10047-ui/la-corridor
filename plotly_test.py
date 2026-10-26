import streamlit as st
import plotly.express as px
import pandas as pd

st.title("Plotly Rendering Test")
df = pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 3]})
fig = px.scatter(df, x="x", y="y", title="Basic Plotly Test")
st.plotly_chart(fig, width="stretch")
