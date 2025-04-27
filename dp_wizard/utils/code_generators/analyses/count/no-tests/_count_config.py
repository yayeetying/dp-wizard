CONFIG_NAME = pl.col(COLUMN_NAME).cast(float).fill_nan(0).fill_null(0).dp.len()
