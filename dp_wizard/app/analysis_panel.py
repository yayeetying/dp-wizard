from math import pow
from typing import Iterable, Any
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


from htmltools import tags
from shiny import ui, reactive, render, Inputs, Outputs, Session

from dp_wizard.app.components.inputs import log_slider
from dp_wizard.app.components.column_module import column_ui, column_server
from dp_wizard.utils.csv_helper import (
    id_names_dict_from_names,
    id_labels_dict_from_names,
    get_csv_row_count,
)
from dp_wizard.app.components.outputs import (
    output_code_sample,
    demo_tooltip,
    nav_button,
)
from dp_wizard.utils.code_generators import make_privacy_loss_block


def analysis_ui():
    return ui.nav_panel(
        "Define Analysis",
        ui.layout_columns(
            ui.card(
                ui.card_header("Grouping"),
                ui.markdown(
                    """
                    Select columns to group by, or leave empty
                    to calculate statistics across the entire dataset.

                    Groups aren't applied to the previews on this page
                    but will be used in the final release.
                    """
                ),
                ui.input_selectize(
                    "groups_selectize",
                    "Group by",
                    [],
                    multiple=True,
                ),
            ),
            ui.card(
                ui.card_header("Columns"),
                ui.markdown("Select columns to calculate statistics on."),
                ui.input_selectize(
                    "columns_selectize",
                    ["Columns", ui.output_ui("columns_selectize_tooltip_ui")],
                    [],
                    multiple=True,
                ),
            ),
            ui.card(
                ui.card_header("Privacy Budget"),
                ui.input_numeric(
                    "total_budget_input",
                    "Enter Total Budget (ε)",
                    value=1.0,
                    min=0.01,
                    max=100.0,
                    step=0.01,
                ),
                ui.output_text("remaining_budget_text"),
                ui.markdown(
                    """
                    What is your privacy budget for this release?
                    Many factors including the sensitivity of your data,
                    the frequency of DP releases,
                    and the regulatory landscape can be considered.
                    Consider how your budget compares to that of
                    <a href="https://registry.oblivious.com/#public-dp"
                       target="_blank">other projects</a>.
                    """
                ),
                log_slider("log_epsilon_slider", 0.1, 10.0),
                ui.output_ui("epsilon_ui"),
                ui.output_ui("budget_status_ui"),
                ui.input_action_button("confirm_button", "Confirm Budget"),
                ui.output_text("confirmed_epsilon_text"),
                output_code_sample("Privacy Loss", "privacy_loss_python"),
            ),
            ui.card(
                ui.card_header("Privacy-Utility Visualization"),
                ui.output_plot("epsilon_visualization"),
                ui.output_ui("epsilon_text_description"),
            ),
            ui.card(
                ui.card_header("Simulation"),
                ui.output_ui("simulation_card_ui"),
            ),
            col_widths={
                "sm": [12, 12, 12, 12],  # 4 rows
                "md": [6, 6, 6, 6],  # 2 rows
                "xxl": [3, 3, 3, 3],  # 1 row
            },
        ),
        ui.output_ui("columns_ui"),
        ui.output_ui("download_results_button_ui"),
        value="analysis_panel",
    )


def _cleanup_reactive_dict(
    reactive_dict: reactive.Value[dict[str, Any]], keys_to_keep: Iterable[str]
):  # pragma: no cover
    reactive_dict_copy = {**reactive_dict()}
    keys_to_del = set(reactive_dict_copy.keys()) - set(keys_to_keep)
    for key in keys_to_del:
        del reactive_dict_copy[key]
    reactive_dict.set(reactive_dict_copy)


def analysis_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    public_csv_path: reactive.Value[str],
    # private_csv_path is not needed, since we have the column_names.
    column_names: reactive.Value[list[str]],
    contributions: reactive.Value[int],
    is_demo: bool,
    analysis_types: reactive.Value[dict[str, str]],
    lower_bounds: reactive.Value[dict[str, float]],
    upper_bounds: reactive.Value[dict[str, float]],
    bin_counts: reactive.Value[dict[str, int]],
    groups: reactive.Value[list[str]],
    weights: reactive.Value[dict[str, str]],
    epsilon: reactive.Value[float],
):  # pragma: no cover
    @reactive.calc
    def button_enabled():
        column_ids_selected = input.columns_selectize()
        return len(column_ids_selected) > 0

    @reactive.effect
    def _update_columns():
        csv_ids_labels = csv_ids_labels_calc()
        ui.update_selectize(
            "groups_selectize",
            label=None,
            choices=csv_ids_labels,
        )
        ui.update_selectize(
            "columns_selectize",
            label=None,
            choices=csv_ids_labels,
        )

    @reactive.effect
    @reactive.event(input.groups_selectize)
    def _on_groups_change():
        group_ids_selected = input.groups_selectize()
        column_ids_to_names = csv_ids_names_calc()
        groups.set([column_ids_to_names[id] for id in group_ids_selected])

    @reactive.effect
    @reactive.event(input.columns_selectize)
    def _on_columns_change():
        column_ids_selected = input.columns_selectize()
        # We only clean up the weights, and everything else is left in place,
        # so if you restore a column, you see the original values.
        # (Except for weight, which goes back to the default.)
        _cleanup_reactive_dict(weights, column_ids_selected)

    @render.ui
    def columns_selectize_tooltip_ui():
        return demo_tooltip(
            is_demo,
            """
            Not all columns need analysis. For this demo, just check
            "class_year" and "grade". With more columns selected,
            each column has a smaller share of the privacy budget.
            """,
        )

    @render.ui
    def simulation_card_ui():
        if public_csv_path():
            row_count = get_csv_row_count(Path(public_csv_path()))
            return [
                ui.markdown(
                    f"""
                    Because you've provided a public CSV,
                    it *will be read* to generate previews.

                    The confidence interval depends on the number of rows.
                    Your public CSV has {row_count} rows,
                    but if you believe the private CSV will be
                    much larger or smaller, please update.
                    """
                ),
                ui.input_select(
                    "row_count",
                    "Estimated Rows",
                    choices=[row_count, "100", "1000", "10000"],
                    selected=row_count,
                ),
            ]
        else:
            return [
                ui.markdown(
                    """
                    This simulation will assume a normal distribution
                    between the specified lower and upper bounds.
                    Until you make a release, your CSV will not be
                    read except to determine the columns.

                    What is the approximate number of rows in the dataset?
                    This number is only used for the simulation
                    and not the final calculation.
                    """
                ),
                ui.input_select(
                    "row_count",
                    "Estimated Rows",
                    choices=["100", "1000", "10000"],
                    selected="100",
                ),
            ]

    @render.ui
    def columns_ui():
        column_ids = input.columns_selectize()
        column_ids_to_names = csv_ids_names_calc()
        for column_id in column_ids:
            column_server(
                column_id,
                public_csv_path=public_csv_path(),
                name=column_ids_to_names[column_id],
                contributions=contributions(),
                epsilon=epsilon(),
                # saved_epsilon=saved_epsilon,
                row_count=int(input.row_count()),
                analysis_types=analysis_types,
                lower_bounds=lower_bounds,
                upper_bounds=upper_bounds,
                bin_counts=bin_counts,
                weights=weights,
                is_demo=is_demo,
                is_single_column=len(column_ids) == 1,
            )
        return [column_ui(column_id) for column_id in column_ids]

    @reactive.calc
    def csv_ids_names_calc():
        return id_names_dict_from_names(column_names())

    @reactive.calc
    def csv_ids_labels_calc():
        return id_labels_dict_from_names(column_names())

    @reactive.effect
    @reactive.event(input.log_epsilon_slider)
    def _set_epsilon():
        epsilon.set(pow(10, input.log_epsilon_slider()))

    @render.ui
    def epsilon_ui():
        return tags.label(
            f"Epsilon: {epsilon():0.3} ",
            demo_tooltip(
                is_demo,
                """
                If you set epsilon above one, you'll see that the distribution
                becomes less noisy, and the confidence intervals become smaller...
                but increased accuracy risks revealing personal information.
                """,
            ),
        )

    @render.code
    def privacy_loss_python():
        return make_privacy_loss_block(epsilon())

    @reactive.effect
    @reactive.event(input.go_to_results)
    def go_to_results():
        ui.update_navs("top_level_nav", selected="results_panel")

    @render.ui
    def download_results_button_ui():
        button = nav_button(
            "go_to_results", "Download Results", disabled=not button_enabled()
        )

        if button_enabled():
            return button
        return [
            button,
            "Select one or more columns before proceeding.",
        ]

    @render.plot
    def epsilon_visualization():
        # Prior adversary success probability (50%)
        base_risk = 0.5

        # Build ε grid and curves
        epsilons = np.linspace(0.01, 10, 500)
        accuracy = 1 - np.exp(-epsilons)
        dp_risk = (np.exp(epsilons) * base_risk) / (
            np.exp(epsilons) * base_risk + (1 - base_risk)
        )

        # Current ε from slider
        eps = epsilon()

        # Set up twin axes
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()

        # Use log scale on x-axis for better spread at low ε
        ax1.set_xscale("log")
        ax1.set_xlim(epsilons[0], epsilons[-1])

        # Plot
        ax1.plot(epsilons, accuracy, color="tab:blue", label="Accuracy")
        ax2.plot(
            epsilons,
            dp_risk,
            color="tab:red",
            linestyle="--",
            label=f"Max Adversary Success (p₀={base_risk:.1f})",
        )

        # Vertical guide line
        for ax in (ax1, ax2):
            ax.axvline(eps, color="gray", linestyle="--", linewidth=1)

        # Compute & mark points at ε
        acc_at_eps = np.interp(eps, epsilons, accuracy)
        risk_at_eps = (np.exp(eps) * base_risk) / (
            np.exp(eps) * base_risk + (1 - base_risk)
        )
        ax1.scatter([eps], [acc_at_eps], color="tab:blue", zorder=5)
        ax2.scatter([eps], [risk_at_eps], color="tab:red", zorder=5)

        # Label as percentages
        ax1.text(
            eps,
            acc_at_eps,
            f"{acc_at_eps*100:.1f}%",
            va="bottom",
            ha="left",
            fontsize=9,
        )
        ax2.text(
            eps,
            risk_at_eps,
            f"{risk_at_eps*100:.1f}%",
            va="bottom",
            ha="left",
            fontsize=9,
        )

        # Annotate ε on x-axis
        ax1.text(
            eps,
            ax1.get_ylim()[0],
            f"ε = {eps:.2f}",
            va="bottom",
            ha="center",
            fontsize=9,
        )

        # Axis labels
        ax1.set_xlabel("Epsilon (ε)")
        ax1.set_ylabel("Accuracy*", color="tab:blue")
        ax2.set_ylabel("Privacy Risk*", color="tab:red")
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ax2.tick_params(axis="y", labelcolor="tab:red")
        ax1.set_ylim(0, 1.05)
        ax2.set_ylim(0, 1.05)

        # Combine legends and place at bottom
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        fig.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc="lower center",
            ncol=2,
            bbox_to_anchor=(0.5, -0.2),
        )
        fig.subplots_adjust(bottom=0.25)
        fig.tight_layout()
        return fig

    @render.ui
    def epsilon_text_description():
        eps_val = epsilon()
        acc = (1 - np.exp(-eps_val)) * 100
        risk = (np.exp(eps_val) * 0.5) / (np.exp(eps_val) * 0.5 + 0.5) * 100

        # Determine bottom-line summary
        if acc < 50 and risk < 60:
            bottom = "Strong privacy protection, but data accuracy is very low."
        elif acc < 50 and risk >= 60:
            bottom = "Privacy remains strong, but the results may not be very accurate."
        elif acc < 80 and risk < 60:
            bottom = "Moderate accuracy with strong privacy protection."
        elif acc < 80 and risk >= 60:
            bottom = "Moderate privacy protection with acceptable accuracy."
        elif acc < 95 and risk < 80:
            bottom = "Good accuracy with some privacy risk."
        else:
            bottom = "High accuracy with significant risk of individual data leakage."

        return ui.markdown(
            f"""
**Current ε = {eps_val:.2f}**

- At this setting, your *noisy result* will lie within ±1 unit of the true value about **{acc:.1f}% of the time**.
- An adversary with no prior knowledge (50% guess-rate) can at most raise their success to **{risk:.1f}%** after seeing your DP output.

**Bottom line:** {bottom}

> ⚠️ **Note:* There is no universally accepted definition for accuracy or privacy risk metrics; these values are ballpark estimates.
Here, "accuracy" is modeled from the standard deviation of a Laplace model, and "privacy risk" is modeled using the adversary-success probability bound from Franzen et al. (2024), DOI: 10.1145/3637309.
"""
        )

    @output
    @render.ui
    def budget_status_ui():
        current_epsilon = epsilon()
        if current_epsilon > input.total_budget_input():
            return ui.markdown("**🔴 Budget is exhausted.**")
        else:
            return ui.markdown("")

    saved_epsilon = reactive.Value(0.0)

    # When user clicks "confirm", save the current slider value
    @reactive.effect
    @reactive.event(input.confirm_button)
    def save_epsilon():
        saved_epsilon.set(10 ** input.log_epsilon_slider())

    # Display the saved epsilon
    @output
    @render.text
    def confirmed_epsilon_text():
        epsilon = saved_epsilon.get()
        if epsilon is None:
            return "No budget confirmed yet."
        else:
            return f"✅ Confirmed Epsilon: {epsilon:.3f}"

    @output
    @render.text
    def remaining_budget_text():
        total = input.total_budget_input()
        confirmed = saved_epsilon.get()
        remaining = total - confirmed
        return f"🔒 Remaining Budget: {remaining:.3f}"
