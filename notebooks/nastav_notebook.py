
def nastav_pandas():
    import pandas as pd

    pd.options.display.max_colwidth = 1000
    pd.options.display.max_rows = 100


clean_layout = dict(
    plot_bgcolor="#FFFFFF",
)

y_spikes = dict(
    yaxis=dict(
        linecolor="#BCCCDC",
        showspikes=True,
        spikethickness=1,
        spikedash="dot",
        spikecolor="#999999",
        spikemode="across",
    )
)

x_spikes = dict(
    xaxis=dict(
        linecolor="#BCCCDC",
        showspikes=True,
        spikethickness=1,
        spikedash="dot",
        spikecolor="#999999",
        spikemode="across",
    )
)

clean_layout_with_x_spikes = {**clean_layout, **x_spikes}
clean_layout_with_y_spikes = {**clean_layout, **y_spikes}
clean_layout_with_xy_spikes = {**clean_layout, **x_spikes, **y_spikes}

categorical_scale1 = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
