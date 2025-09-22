import pandas as pd
import numpy as np
import argparse
import os
import sys
import plotly.express as px


def output_dir_exists(out_dir):
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory: {e}", file=sys.stderr)
        sys.exit(1)

parser = argparse.ArgumentParser(
    description="Compute fail/pass stats per (test_id, test_name, model) from a results CSV and build a radar chart and write it to an HTML file."
)
parser.add_argument("--results-file", required=True, help="Path to the input results CSV.")
parser.add_argument("--stats-file", required=True, help="Path to write the stats CSV.")
parser.add_argument("--chart-file", required=True, help="Path to write the chart in HTML.")
args = parser.parse_args()

csv_path = args.results_file
out_stats_csv = args.stats_file
out_chart = args.chart_file

if not os.path.isfile(csv_path):
    print(f"Error: input CSV not found: {csv_path}", file=sys.stderr)
    sys.exit(1)

out_dir_csv = os.path.dirname(out_stats_csv)
if out_dir_csv:
    output_dir_exists(out_dir_csv)

out_dir_chart = os.path.dirname(out_chart)
if out_dir_chart:
    output_dir_exists(out_dir_chart)

df = pd.read_csv(csv_path, dtype=str, keep_default_na=False).copy()
df.columns = [c.strip() for c in df.columns]

required = {"test_id", "test_name", "verdict", "model"}
if not required.issubset(df.columns):
    raise ValueError(f"CSV must have columns: {sorted(required)}. Found: {list(df.columns)}")

df["test_id"] = df["test_id"].astype(str).str.strip()
df["test_name"] = df["test_name"].astype(str).str.strip()
df["verdict"] = df["verdict"].astype(str).str.strip()
df["model"] = df["model"].astype(str).str.strip()

stats = (
    df.groupby(["test_id", "test_name", "model"], sort=False)["verdict"]
      .value_counts(sort=False)
      .unstack(fill_value=0)
      .reset_index()
)

if "Error" not in stats.columns:
    stats["Error"] = 0

if "Fail" not in stats.columns:
    stats["Fail"] = 0

if "Pass" not in stats.columns:
    stats["Pass"] = 0

stats["Total"] = stats["Fail"] + stats["Pass"] + stats["Error"] 
stats["Fail Percentage"] = np.where(stats["Total"] > 0, stats["Fail"] / stats["Total"] * 100, 0.0).round(1)
stats["Pass Percentage"] = np.where(stats["Total"] > 0, stats["Pass"] / stats["Total"] * 100, 0.0).round(1)
stats["Error Percentage"] = np.where(stats["Total"] > 0, stats["Error"] / stats["Total"] * 100, 0.0).round(1)

try:
    stats.to_csv(out_stats_csv, index=False)
except Exception as e:
    print(f"Error writing CSV: {e}", file=sys.stderr)
    sys.exit(1)

print(f"Saved stats to: {os.path.abspath(out_stats_csv)}")

try:
    df = pd.read_csv(out_stats_csv)
except Exception as e:
    print(f"Error reading CSV: {e}", file=sys.stderr)
    sys.exit(1)

required = {"test_id", "test_name", "model", "Fail Percentage"}
missing = required.difference(df.columns)
if missing:
    print(f"Error: CSV is missing required columns: {', '.join(sorted(missing))}", file=sys.stderr)
    sys.exit(1)

df["theta_label"] = "<b>" + df["test_id"].astype(str) + "</b><br>" + df["test_name"].astype(str)
if len(df) < 5:
    fig = px.bar(
        df,
        x="theta_label",
        y="Fail Percentage",
        color="model",
        title="LLM Attack Surface",
        text="Fail Percentage",
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        xaxis_title="Test ID and Name",
        yaxis_title="Fail Percentage",
        yaxis=dict(range=[0, 100]),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
    )
else:
    fig = px.line_polar(
        df,
        r="Fail Percentage",
        theta="theta_label",
        color="model",
        line_close=True,
        title="LLM Attack Surface",
    )
    fig.update_traces(
        fill="toself",
        hovertemplate="test_id: <b>%{theta}</b><br>Fail Percentage: %{r:.2f}%<extra></extra>",
    )
    fig.update_polars(radialaxis=dict(range=[0, 100]))

try:
    fig.write_html(out_chart, include_plotlyjs="cdn")
except Exception as e:
    print(f"Error writing HTML: {e}", file=sys.stderr)
    sys.exit(1)

print(f"Saved radar chart to: {os.path.abspath(out_chart)}")
