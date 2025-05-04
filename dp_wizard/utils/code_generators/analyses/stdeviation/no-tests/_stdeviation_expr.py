# See the OpenDP docs for more on making private Standard Devation releases:

"""
from opendp.mod import enable_features
from opendp.transformations import make_variance
from opendp.measurements import make_laplace
from opendp.metrics import SymmetricDistance
from opendp.prelude import atom_domain, vector_domain
import math

enable_features("contrib")
"""

import polars as pl
import pandas as pd
import numpy as np


def private_std(data):
    data = np.clip(data, LOWER_BOUND, UPPER_BOUND)
    mean = sum(data) / len(data)
    squared_devs = [(x - mean) ** 2 for x in data]
    stdeviation = sum(squared_devs) / len(data)
    return stdeviation


# arr = np.array(pl.col(COLUMN_NAME).cast(float).fill_nan(0).fill_null(0).to_numpy())

EXPR_NAME = (
    pl.col(COLUMN_NAME)
    .cast(float)
    .fill_nan(0)
    .fill_null(0)
    .dp.mean((LOWER_BOUND, UPPER_BOUND))
    .alias("standard_deviation")
)

"""
import polars as pl

EXPR_NAME = (
    pl.col(COLUMN_NAME)
      .cast(float)
      .fill_nan(0.0)
      .fill_null(0.0)
      .clip(LOWER_BOUND, UPPER_BOUND)
      .dp.mean((LOWER_BOUND, UPPER_BOUND))
      # .std(ddof=0)
      .alias("private_standard_deviation")
)
"""

"""
def dp_var(data, lower, upper, size=100, epsilon=1):
    float_dom = atom_domain(T=float, nan=False, bounds=(lower, upper))
    # Size is dependent on size of dataset
    vec_dom = vector_domain(float_dom, size=size)
    metric = SymmetricDistance()
    bounded_variance = make_variance(input_domain=vec_dom, input_metric=metric)

    # Add Laplace noise; scale should be b = sensitivity (10; number of contributions) / epsilon
    dp_variance = make_laplace(bounded_variance, scale= 1 / epsilon)
    return dp_variance

EXPR_NAME = math.sqrt(
    dp_var(pl.col(COLUMN_NAME).cast(float).fill_nan(0).fill_null(0), LOWER_BOUND, UPPER_BOUND)
)
"""

"""
# Variance Transformation
# Calculate bounded domain
float_dom = atom_domain(T=float, nan=False, bounds=(LOWER_BOUND, UPPER_BOUND))
# Size is dependent on size of dataset
vec_dom = vector_domain(float_dom, size=100)
metric = SymmetricDistance()
bounded_variance = make_variance(
    input_domain=vec_dom,
    input_metric=metric
)

# Build a Laplace mechanism that accepts bounded_variance's output
# Add Laplace noise; scale should be b = sensitivity (10; number of contributions) / epsilon
lap_mech = make_laplace(
    bounded_variance.output_domain,
    bounded_variance.output_metric,
    scale= 1 / epsilon
)

def dp_variance(dataset):
    return bounded_variance >> lap_mech

# Standard Deviation
EXPR_NAME = math.sqrt(
    dp_variance(pl.col(COLUMN_NAME).cast(float).fill_nan(0).fill_null(0))
)
"""
"""
import polars as pl
import opendp.prelude as dp
from opendp.extras.polars import make_private_lazyframe
from opendp.domains        import atom_domain, vector_domain
from opendp.metrics        import symmetric_distance
import pandas as pd


# 2. build a private measurement over your LazyFrame
private = make_private_lazyframe(
    input_domain  = vector_domain(atom_domain(T=float, bounds=(LOWER_BOUND, UPPER_BOUND))),
    input_metric  = symmetric_distance(),
    output_measure= dp.loss_of(epsilon=1),
    lazyframe     = df.lazy(),
)

# 3. write your query entirely in Polars + `.dp`
EXPR_NAME = (
    private
      .query()
      .with_columns(
         pl.col(COLUMN_NAME)
           .cast(float)
           .fill_nan(0)
           .fill_null(0)
           .dp.sum((LOWER_BOUND, UPPER_BOUND))   # sum of squared deviations... etc.
           .dp.noise()                            # or `.dp.laplace()` directly
           # you can even build variance then sqrt with standard Polars methods
      )
      .release()
)
"""
