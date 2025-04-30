# See the OpenDP docs for more on making private Standard Devation releases:
# https://docs.opendp.org/en/stable/getting-started/tabular-data/essential-statistics.html#Mean

from opendp.mod import enable_features
from opendp.transformations import make_clamp, make_bounded_variance
from opendp.measurements import make_base_laplace
import math

enable_features("contrib")

# Clamp data between lower and upper bounds
clamp = make_clamp(LOWER_BOUND, UPPER_BOUND)

# Build DP bounded variance function
bounded_variance = make_bounded_variance((LOWER_BOUND, UPPER_BOUND))

# Add Laplace noise
dp_variance = make_base_laplace(bounded_variance, scale=1 / epsilon)

# Standard Deviation
EXPR_NAME = math.sqrt(
    dp_variance(pl.col(COLUMN_NAME).cast(float).fill_nan(0).fill_null(0))
)
