import polars as pl
import numpy as np
import opendp.prelude as dp

dp.enable_features("contrib")

size = 10_000
x = np.random.normal(size=size)
lf = pl.LazyFrame({"x": x})

mean = (
    dp.Context.compositor(
        data=pl.LazyFrame({"x": x}),
        privacy_unit=dp.unit_of(contributions=1),
        privacy_loss=dp.loss_of(epsilon=0.5),
        split_evenly_over=1,
        margins=[dp.polars.Margin(max_partition_length=size)],
    )
    .query()
    .select(pl.col("x").fill_nan(0).fill_null(0).dp.mean((-10, 10)))
    .release()
    .collect()
    .item()
)

print(mean)

var = (
    dp.Context.compositor(
        data=pl.LazyFrame({"devs": (x - mean) ** 2}),
        privacy_unit=dp.unit_of(contributions=1),
        privacy_loss=dp.loss_of(epsilon=0.5),
        split_evenly_over=1,
        margins=[dp.polars.Margin(max_partition_length=size)],
    )
    .query()
    .select(pl.col("devs").fill_nan(0).fill_null(0).dp.mean((-10, 10)))
    .release()
    .collect()
    .item()
)
print(np.sqrt(var))

"""
groups = GROUP_NAMES
QUERY_NAME = (
    context.query().group_by(groups).agg(EXPR_NAME)
    if groups
    else context.query().select(EXPR_NAME)
)
STATS_NAME = QUERY_NAME.release().collect()
STATS_NAME
"""
