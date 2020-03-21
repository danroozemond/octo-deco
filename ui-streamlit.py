import time, math, numpy as np;
import streamlit as st;
import UI, DiveProfile;

#Run as: streamlit run abc.py

st.sidebar.text("Hello, sidebar!");

dp = DiveProfile();
dp.append_section(40,25);
dp.append_section(30,10);

UI.plot_profile( st, dp );

chart = st.line_chart()

def doplot(nrows):
    progress_bar.progress(0);
    last_rows = np.random.randn(1, 1)
    N = math.ceil(nrows/5);
    for i in range(1, N+1):
        new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
        status_text.text("%i%% Complete" % (100.0 * i / N));
        chart.add_rows(new_rows)
        progress_bar.progress(i / N)
        last_rows = new_rows
        time.sleep(0.05)

    progress_bar.empty()

st.button("Re-plot");

doplot(add_slider);
