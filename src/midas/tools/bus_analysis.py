import os

import matplotlib.pyplot as plt
import numpy as np
from natsort import natsorted


def analyze_buses(data, report_file, name, output_path, full_report):

    data = data[[col for col in data.columns if "vm_pu" in col]]

    fails = 0
    total = 0

    report_file.append("## Bus Analysis\n")
    data = data[natsorted(data.columns)]
    for col in data.columns:
        vm_pus = data[col].values
        key = col.split(".")[0]
        total += len(vm_pus)
        fails += _voltage_violation_report(vm_pus, key, report_file)
        if not full_report:
            continue

        annual = np.sort(vm_pus)[::-1]
        fig, axes = plt.subplots(2, 1, figsize=(9, 9))
        for ax, series, title in zip(
            axes, [vm_pus, annual], [f"{key} vm_pu", f"{key} vm_pu annual"]
        ):
            ax.plot(series)
            ax.axhline(y=1.1, color="red")
            ax.axhline(y=1.04, linestyle="--", color="red")
            ax.axhline(y=0.96, linestyle="--", color="red")
            ax.axhline(y=0.9, color="red")

            ax.set_title(title)
            ax.set_ylabel("voltage magnitude p.u.")
            ax.set_xlabel("time (15 minute steps)")

        plt.savefig(
            os.path.join(output_path, f"{name}_{key}_vmpu.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    report_file.append("")

    aggregated = data.mean(axis=1).values
    annual = np.sort(aggregated)[::-1]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    ax1.plot(aggregated)
    ax1.axhline(y=1.1, color="red")
    ax1.axhline(y=1.04, linestyle="--", color="red")
    ax1.axhline(y=0.96, linestyle="--", color="red")
    ax1.axhline(y=0.9, color="red")
    ax1.set_title("0-buses vm_pu")
    # ax1.set_xlabel("time (15 minute steps")
    ax1.set_ylabel("voltage magnitude p.u.")
    ax2.plot(annual)
    ax2.axhline(y=1.1, color="red")
    ax2.axhline(y=1.04, linestyle="--", color="red")
    ax2.axhline(y=0.96, linestyle="--", color="red")
    ax2.axhline(y=0.9, color="red")
    ax2.set_title("0-buses annual curve vm_pu")
    ax2.set_xlabel("time (15 minute steps")
    ax2.set_ylabel("voltage magnitude p.u.")
    img_path = os.path.join(output_path, f"{name}_0-buses_vmpu.png")
    plt.savefig(img_path, dpi=300, bbox_inches="tight")
    plt.close()

    report_file.append(f"\n![Total_Bus_vm_pu]({img_path})" + "{width=100%}\n")

    # report_file.append(
    #     f'\n<img src="{img_path}" width="150" height="200" />\n'
    # )
    score = 100 * (1.0 - (fails / total))
    return score


# def _plot_series(data, col, name, output_path):


def _voltage_violation_report(vm_pus, key, report_file):

    too_high10 = (vm_pus > 1.1).sum()
    too_high4 = (vm_pus > 1.04).sum()
    too_low10 = (vm_pus < 0.9).sum()
    too_low4 = (vm_pus < 0.96).sum()

    if too_high10 > 0:
        score = 100 * too_high10 / len(vm_pus)
        report_file.append(
            f"* [{key}] {too_high10} values > 1.1 ({score:.3f} %)"
        )
    if too_high4 - too_high10 > 0:
        score = 100 * (too_high4 - too_high10) / len(vm_pus)
        report_file.append(
            f"* [{key}] {too_high4-too_high10} values > 1.04 ({score:.3f} %)"
        )
    if too_low10 > 0:
        score = 100 * too_low10 / len(vm_pus)
        report_file.append(
            f"* [{key}] {too_low10} values < 0.9 ({score:.3f} %)"
        )
    if too_low4 - too_low10 > 0:
        score = 100 * (too_low4 - too_low10) / len(vm_pus)
        report_file.append(
            f"* [{key}] {too_low4-too_low10} values < 0.96 ({score:.3f} %)"
        )

    return too_low4 + too_high4
