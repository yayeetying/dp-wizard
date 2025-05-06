# See the OpenDP docs for more on making private Quantile releases:

EXPR_NAME = (
    pl.col(COLUMN_NAME)
    .cast(float)
    .fill_nan(0)
    .fill_null(0)
    .dp.quantile(0.75, make_cut_points(LOWER_BOUND, UPPER_BOUND, bin_count=100))
)
