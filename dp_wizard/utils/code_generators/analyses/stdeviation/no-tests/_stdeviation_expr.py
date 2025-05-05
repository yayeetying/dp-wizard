# See the OpenDP docs for more on making private Standard Devation releases:

# Standard Deviation
EXPR_NAME = pl.col(COLUMN_NAME).cast(float).fill_nan(0).fill_null(0).std()
