import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(WORK_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

rcParams.update({
    "font.size": 12,
    "axes.labelsize": 13,
    "axes.titlesize": 14,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
})

EMIN, EMAX = -3.5, 3.5


def fmt_label(lbl):
    if not isinstance(lbl, str):
        return lbl
    lbl = lbl.strip()
    for src, dst in [("\\Gamma", "$\\Gamma$"), ("\\Sigma", "$\\Sigma$"),
                     ("\\Delta", "$\\Delta$"), ("\\Lambda", "$\\Lambda$")]:
        lbl = lbl.replace(src, dst)
    return lbl


def kpoint_ticks(kpoints_csv):
    df = pd.read_csv(kpoints_csv)
    labeled = df[df.Label.notna()]
    ticks = {}
    for _, row in labeled.iterrows():
        d = round(float(row.Distance), 8)
        lbl = str(row.Label).strip()
        if d in ticks:
            if ticks[d] != lbl:
                ticks[d] = f"{ticks[d]}|{lbl}"
        else:
            ticks[d] = lbl
    positions = sorted(ticks)
    labels = [fmt_label(ticks[p]) for p in positions]
    return positions, labels


def read_fermi(fermi_txt):
    with open(fermi_txt) as f:
        return float(f.read().split(":")[-1].strip())


def plot_band_dos(band_up_csv, dos_csv, kpoints_csv, fermi_txt,
                  title, color_up="steelblue", color_dn="tomato",
                  band_down_csv=None, outfile=None):

    fermi = read_fermi(fermi_txt)
    positions, labels = kpoint_ticks(kpoints_csv)

    band_up = pd.read_csv(band_up_csv)
    dist = band_up["Distance"].values
    band_cols = [c for c in band_up.columns if c != "Distance"]

    dos_df = pd.read_csv(dos_csv)
    energy = dos_df["Energy (eV)"].values  # already Fermi-referenced
    mask = (energy >= EMIN) & (energy <= EMAX)

    fig = plt.figure(figsize=(10, 5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1], wspace=0.04)
    ax_bs = fig.add_subplot(gs[0])
    ax_dos = fig.add_subplot(gs[1], sharey=ax_bs)

    # --- Band structure ---
    for col in band_cols:
        e = band_up[col].values - fermi
        ax_bs.plot(dist, e, color=color_up, lw=0.6, alpha=0.75)

    if band_down_csv:
        bd = pd.read_csv(band_down_csv)
        for col in [c for c in bd.columns if c != "Distance"]:
            e = bd[col].values - fermi
            ax_bs.plot(dist, e, color=color_dn, lw=0.6, alpha=0.75, ls="--")

    for pos in positions:
        ax_bs.axvline(pos, color="gray", lw=0.8, ls="--", alpha=0.5)
    ax_bs.axhline(0, color="red", lw=1.0, ls=":", alpha=0.8)
    ax_bs.set_xticks(positions)
    ax_bs.set_xticklabels(labels)
    ax_bs.set_xlim(dist[0], dist[-1])
    ax_bs.set_ylim(EMIN, EMAX)
    ax_bs.set_ylabel("E − E$_F$ (eV)")
    ax_bs.set_xlabel("Wave vector")
    ax_bs.set_title(title)

    # --- DOS ---
    dos_up = dos_df["DOS_up"].values[mask]
    ax_dos.fill_betweenx(energy[mask], 0, dos_up, alpha=0.55, color=color_up)
    ax_dos.plot(dos_up, energy[mask], color=color_up, lw=1.2, label="Spin ↑")

    if "DOS_down" in dos_df.columns:
        dos_dn = dos_df["DOS_down"].values[mask]  # already negative
        ax_dos.fill_betweenx(energy[mask], 0, dos_dn, alpha=0.55, color=color_dn)
        ax_dos.plot(dos_dn, energy[mask], color=color_dn, lw=1.2, label="Spin ↓")
        ax_dos.legend(loc="upper right")

    ax_dos.axhline(0, color="red", lw=1.0, ls=":", alpha=0.8)
    ax_dos.set_xlabel("DOS (states/eV)")
    ax_dos.yaxis.set_visible(False)
    ax_dos.set_title("DOS")
    ax_dos.axvline(0, color="gray", lw=0.6)

    plt.tight_layout()
    if outfile:
        fig.savefig(outfile, dpi=180, bbox_inches="tight")
        print(f"Saved: {outfile}")
    return fig


def band_gap_from_bands(band_csv, fermi_eV):
    """Return (VBM, CBM) relative to Fermi, from band CSV."""
    df = pd.read_csv(band_csv)
    band_cols = [c for c in df.columns if c != "Distance"]
    all_e = np.concatenate([df[c].values for c in band_cols]) - fermi_eV
    occ = all_e[all_e <= 0]
    unocc = all_e[all_e > 0]
    vbm = float(occ.max()) if len(occ) else None
    cbm = float(unocc.min()) if len(unocc) else None
    return vbm, cbm


def plot_band_alignment(materials, outfile=None):
    """
    materials: list of dicts with keys:
        label, vbm, cbm, color
    vbm/cbm are in eV relative to each material's own Fermi level.
    For alignment we align VBMs to the same absolute scale.
    """
    fig, ax = plt.subplots(figsize=(6, 5))
    bar_width = 0.5

    for i, mat in enumerate(materials):
        vbm = mat["vbm"]
        cbm = mat["cbm"]
        color = mat["color"]
        x = i + 1

        # Valence band (below VBM)
        ax.bar(x, abs(EMIN) + vbm, bottom=EMIN, width=bar_width,
               color=color, alpha=0.65, edgecolor="black", lw=0.8)

        # Conduction band (above CBM)
        ax.bar(x, EMAX - cbm, bottom=cbm, width=bar_width,
               color=color, alpha=0.35, edgecolor="black", lw=0.8, ls="--")

        # Band gap region (white)
        ax.bar(x, cbm - vbm, bottom=vbm, width=bar_width,
               color="white", edgecolor="black", lw=0.8)

        gap = round(cbm - vbm, 2)
        mid = (vbm + cbm) / 2
        ax.text(x, mid, f"Eg = {gap} eV", ha="center", va="center",
                fontsize=10, fontweight="bold")
        ax.text(x, vbm - 0.12, f"VBM = {vbm:.2f}", ha="center", va="top", fontsize=9)
        ax.text(x, cbm + 0.12, f"CBM = {cbm:.2f}", ha="center", va="bottom", fontsize=9)

    ax.axhline(0, color="red", ls=":", lw=1.2, label="E$_F$")
    ax.set_xticks(range(1, len(materials) + 1))
    ax.set_xticklabels([m["label"] for m in materials], fontsize=13)
    ax.set_ylabel("E − E$_F$ (eV)")
    ax.set_ylim(EMIN, EMAX)
    ax.set_title("Band Alignment")
    ax.legend()
    plt.tight_layout()
    if outfile:
        fig.savefig(outfile, dpi=180, bbox_inches="tight")
        print(f"Saved: {outfile}")
    return fig


# ── CuS ─────────────────────────────────────────────────────────────────────
plot_band_dos(
    band_up_csv=os.path.join(WORK_DIR, "mp-504_band_up.csv"),
    dos_csv=os.path.join(WORK_DIR, "mp-504_DOS.csv"),
    kpoints_csv=os.path.join(WORK_DIR, "mp-504_kpoints.csv"),
    fermi_txt=os.path.join(WORK_DIR, "mp-504_Fermi_energy.txt"),
    title="CuS — Band Structure",
    color_up="steelblue",
    outfile=os.path.join(FIG_DIR, "CuS_band_DOS.png"),
)

# ── MnFe2O4 ─────────────────────────────────────────────────────────────────
plot_band_dos(
    band_up_csv=os.path.join(WORK_DIR, "mp-18750_band_up.csv"),
    dos_csv=os.path.join(WORK_DIR, "mp-18750_DOS.csv"),
    kpoints_csv=os.path.join(WORK_DIR, "mp-18750_kpoints.csv"),
    fermi_txt=os.path.join(WORK_DIR, "mp-18750_Fermi_energy.txt"),
    title="MnFe₂O₄ — Band Structure",
    color_up="steelblue",
    color_dn="tomato",
    band_down_csv=os.path.join(WORK_DIR, "mp-18750_band_down.csv"),
    outfile=os.path.join(FIG_DIR, "MnFe2O4_band_DOS.png"),
)

# ── Band alignment ───────────────────────────────────────────────────────────
cus_fermi = read_fermi(os.path.join(WORK_DIR, "mp-504_Fermi_energy.txt"))
mno_fermi = read_fermi(os.path.join(WORK_DIR, "mp-18750_Fermi_energy.txt"))

cus_vbm, cus_cbm = band_gap_from_bands(
    os.path.join(WORK_DIR, "mp-504_band_up.csv"), cus_fermi)
mno_vbm, mno_cbm = band_gap_from_bands(
    os.path.join(WORK_DIR, "mp-18750_band_up.csv"), mno_fermi)

print(f"CuS:     VBM={cus_vbm:.3f} eV, CBM={cus_cbm:.3f} eV, gap={cus_cbm-cus_vbm:.3f} eV")
print(f"MnFe2O4: VBM={mno_vbm:.3f} eV, CBM={mno_cbm:.3f} eV, gap={mno_cbm-mno_vbm:.3f} eV")

plot_band_alignment(
    materials=[
        {"label": "CuS", "vbm": cus_vbm, "cbm": cus_cbm, "color": "steelblue"},
        {"label": "MnFe₂O₄", "vbm": mno_vbm, "cbm": mno_cbm, "color": "darkorange"},
    ],
    outfile=os.path.join(FIG_DIR, "band_alignment.png"),
)

print("All figures saved to:", FIG_DIR)
