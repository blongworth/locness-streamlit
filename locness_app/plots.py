import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def create_map_plot(df, selected_params):
    if df.empty:
        return go.Figure()
    track_data = df
    fig = go.Figure()
    if selected_params and selected_params[0] in track_data.columns:
        color_param = selected_params[0]
        color_vals = track_data[color_param]
        qmin = color_vals.quantile(0.05)
        qmax = color_vals.quantile(0.95)
        if qmin == qmax:
            qmin = color_vals.min()
            qmax = color_vals.max()
        scatter = go.Scattermap(
            lat=track_data['latitude'],
            lon=track_data['longitude'],
            mode='markers+lines',
            marker=dict(
                size=10,
                color=color_vals,
                colorscale='Viridis',
                cmin=qmin,
                cmax=qmax,
                colorbar=dict(title=color_param.capitalize()),
                showscale=True
            ),
            name=f'Track ({color_param})',
            text=[f"{color_param}: {v:.2f}" for v in color_vals],
            hovertemplate=
                'Lat: %{latitude:.4f}<br>' +
                'Lon: %{longitude:.4f}<br>' +
                f'{color_param}: %{{marker.color:.2f}}<extra></extra>'
        )
        fig.add_trace(scatter)
    else:
        fig.add_trace(go.Scattermap(
            lat=track_data['latitude'],
            lon=track_data['longitude'],
            mode='lines',
            line=dict(width=2, color='blue'),
            name='Track',
            hoverinfo='skip'
        ))
    if not df.empty:
        latest = df.iloc[-1]
        fig.add_trace(go.Scattermap(
            lat=[latest['latitude']],
            lon=[latest['longitude']],
            mode='markers',
            marker=dict(size=15, color='red'),
            name='Current Position',
            hovertemplate='<b>Current Position</b><br>' +
                         'Lat: %{latitude:.4f}<br>' +
                         'Lon: %{longitude:.4f}<br>' +
                         f'Temp: {latest["temp"]:.1f}°C<br>' +
                         f'Salinity: {latest["salinity"]:.1f}<br>' +
                         f'pH: {latest["ph_corrected"]:.2f}<extra></extra>' +
                         f'Average pH: {latest["ph_corrected_ma"]:.2f}<extra></extra>'
        ))
    if not track_data.empty:
        min_lat = track_data['latitude'].min()
        max_lat = track_data['latitude'].max()
        min_lon = track_data['longitude'].min()
        max_lon = track_data['longitude'].max()
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        max_range = max(lat_range, lon_range)
        if max_range < 0.002:
            zoom = 15
        elif max_range < 0.01:
            zoom = 13
        elif max_range < 0.05:
            zoom = 11
        elif max_range < 0.2:
            zoom = 9
        else:
            zoom = 7
    else:
        center_lat, center_lon = 42.3601, -71.0589
        zoom = 12
    fig.update_layout(
        map=dict(
            style="dark",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        height=800,
    )
    return fig

def create_timeseries_plot(df, selected_params):
    if df.empty:
        return go.Figure()
    fig = make_subplots(
        rows=len(selected_params), 
        cols=1,
        subplot_titles=selected_params,
        shared_xaxes=True,
        vertical_spacing=0.05
    )
    colors = px.colors.qualitative.Set1
    for i, param in enumerate(selected_params):
        if param in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[param],
                    name=param,
                    line=dict(color=colors[i % len(colors)]),
                    mode='lines+markers',
                    marker=dict(size=3)
                ),
                row=i+1, col=1
            )
    fig.update_layout(
        height=150 + 200 * len(selected_params),
        showlegend=False,
    )
    for i in range(1, len(selected_params) + 1):
        fig.update_xaxes(
            title_text="",
            row=i, col=1,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=12, label="12h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            ) if i == 1 else None,
            rangeslider=dict(visible=(i == len(selected_params))),
            type="date"
        )
    return fig

def create_ph_timeseries_plot(df):
    if df.empty:
        return go.Figure()
    colors = px.colors.qualitative.Set1
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['ph_corrected_ma'],
            name='pH moving average',
            line=dict(color=colors[0]),
            mode='lines+markers',
            marker=dict(size=3)
        ),
    )
    fig.update_layout(
        height=350,
        showlegend=False,
    )
    fig.update_xaxes(
        title_text="",
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1h", step="hour", stepmode="backward"),
                dict(count=6, label="6h", step="hour", stepmode="backward"),
                dict(count=12, label="12h", step="hour", stepmode="backward"),
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(step="all")
            ])
        ),
        type="date"
    )
    return fig
