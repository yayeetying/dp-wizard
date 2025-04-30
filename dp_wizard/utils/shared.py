# These functions are used both in the application
# and in generated notebooks.
from polars import DataFrame


def make_cut_points(lower_bound: float, upper_bound: float, bin_count: int):
    """
    Returns one more cut point than the bin_count.
    (There are actually two more bins, extending to
    -inf and +inf, but we'll ignore those.)
    Cut points are evenly spaced from lower_bound to upper_bound.
    >>> make_cut_points(0, 10, 2)
    [0.0, 5.0, 10.0]
    """
    bin_width = (upper_bound - lower_bound) / bin_count
    return [round(lower_bound + i * bin_width, 2) for i in range(bin_count + 1)]


def interval_bottom(interval: str):
    """
    >>> interval_bottom("(10, 20]")
    10.0
    >>> interval_bottom("-10")
    -10.0
    >>> interval_bottom("unexpected")
    0.0
    """
    # Intervals from Polars are always open on the left,
    # so that's the only case we cover with replace().
    try:
        return float(interval.split(",")[0].replace("(", ""))
    except ValueError:
        return 0.0


def df_to_columns(df: DataFrame):
    """
    Transform a Dataframe into a format that is easier to plot,
    parsing the interval strings to sort them as numbers.
    """
    merged_key_rows = [
        (" ".join(str(k) for k in keys), value) for (*keys, value) in df.rows()
    ]
    sorted_rows = sorted(merged_key_rows, key=lambda row: interval_bottom(row[0]))
    transposed = tuple(zip(*sorted_rows))
    return transposed if transposed else (tuple(), tuple())


import matplotlib.pyplot as plt
from polars import DataFrame
from matplotlib.colors import LinearSegmentedColormap


def plot_bars(df: DataFrame, error: float, cutoff: float, title: str, epsilon: float):
    """
    Graph is blue when epsilon < 1 to show strong privacy
    Then red to dark red for when epsilon is greater than 1 as there is less privacy
    """
    bins, values = df_to_columns(df)
    fig, ax = plt.subplots(figsize=(12, 4))

    if epsilon <= 1:
        bar_color = "blue"
        # normalizes eps from 1 to 10 to 0 to 1
        norm_eps = min((epsilon - 1) / 9, 1)
        # blue gradient from dark to lighter
        blue_map = LinearSegmentedColormap.from_list(
            "blue_scale", ["#5b45ff", "#1e00ff"]
        )
        bar_color = blue_map(norm_eps)
    else:
        # normalizes eps from 1 to 10 to 0 to 1
        norm_eps = min((epsilon - 1) / 9, 1)
        # red goes from light to darker
        red_map = LinearSegmentedColormap.from_list("red_scale", ["#f54747", "#8B0000"])
        bar_color = red_map(norm_eps)

    bars = ax.bar(
        bins,
        values,
        color=bar_color,
        yerr=error,
        capsize=6,
        edgecolor="black",
        linewidth=1.2,
        error_kw={"elinewidth": 2.5, "ecolor": "black"},
    )

    ax.axhline(cutoff, color="gray", linestyle="--", linewidth=1.2)
    ax.set_xticks(range(len(bins)))
    ax.set_xticklabels(bins, rotation=45, ha="right")
    ax.set_ylim(bottom=0)
    ax.set_title(title, fontsize=14, pad=12)

    fig.tight_layout()
    return fig
