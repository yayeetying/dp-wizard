from typing import Protocol

from dp_wizard.utils.code_generators.abstract_generator import AbstractGenerator


class Analysis(Protocol):  # pragma: no cover
    # There should also be a "name".
    # @property can't be combined with @staticmethod,
    # so we can't make that explicit here.

    @staticmethod
    def has_bins() -> bool: ...

    @staticmethod
    def make_query(
        code_gen: AbstractGenerator,
        identifier: str,
        accuracy_name: str,
        stats_name: str,
    ) -> str: ...

    @staticmethod
    def make_output(
        code_gen: AbstractGenerator,
        column_name: str,
        accuracy_name: str,
        stats_name: str,
    ) -> str: ...

    @staticmethod
    def make_report_kv(
        name: str,
        confidence: float,
        identifier: str,
    ) -> str: ...

    @staticmethod
    def make_column_config_block(
        column_name: str,
        lower_bound: float,
        upper_bound: float,
        bin_count: int,
    ) -> str: ...


def get_analysis_by_name(name) -> Analysis:  # pragma: no cover
    # Avoid circular import:
    from dp_wizard.utils.code_generators.analyses import (
        histogram,
        mean,
        median,
        count,
        quantile,
        stdeviation,
    )

    match name:
        case histogram.name:
            return histogram
        case mean.name:
            return mean
        case median.name:
            return median
        case count.name:
            return count
        case quantile.name:
            return quantile
        case stdeviation.name:
            return stdeviation
        case _:
            raise Exception("Unrecognized analysis")
