# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git workflow

Every change must be committed with a clean message and pushed immediately:
```bash
git add <files>
git commit -m "imperative-mood summary under 72 chars"
git push
```
Never leave the session with uncommitted or unpushed changes.

## Commands

**Regenerate all figures from existing CSV data:**
```bash
python generate_figures.py
```

**Fetch fresh data from Materials Project** (requires API key, internet access):
Run the cells in `CuS_MnFe2O4.ipynb` — the data-download cells write the CSV files that `generate_figures.py` reads.

**Launch Jupyter:**
```bash
jupyter notebook
```

## Architecture

Data flows in two stages:

```
Materials Project API
        │  (notebooks fetch via mp_api MPRester)
        ▼
CSV files (mp-504_*, mp-18750_*)
        │  (generate_figures.py reads these)
        ▼
figures/  (CuS_band_DOS.png, MnFe2O4_band_DOS.png, band_alignment.png)
```

### CSV data conventions — critical for correct plotting

| File pattern | Energy reference | Notes |
|---|---|---|
| `*_band_up.csv`, `*_band_down.csv` | **Absolute** (eV) | Must subtract Fermi from `*_Fermi_energy.txt` before plotting |
| `*_DOS.csv` | **Fermi-referenced** (already `E - E_F`) | Do NOT subtract Fermi again |
| `*_DOS.csv` → `DOS_down` column | Already **negated** | Stored as negative values for mirrored spin-down plot |
| `*_kpoints.csv` → `Label` column | — | `NaN` for non-high-symmetry points; duplicate `Distance` values mark segment boundaries between two different k-points |

### Materials

| Material | MP ID | Magnetic | Files |
|---|---|---|---|
| CuS | mp-504 | No (spin-up only) | `mp-504_*` |
| MnFe₂O₄ | mp-18750 | Yes (spin-up + spin-down) | `mp-18750_*` |

### generate_figures.py key functions

- `plot_band_dos()` — combined band structure + DOS panel (3:1 width ratio, shared y-axis)
- `band_gap_from_bands()` — extracts VBM/CBM by scanning all band energies relative to Fermi
- `plot_band_alignment()` — bar diagram comparing VBM/CBM across materials
- `kpoint_ticks()` — collapses duplicate-distance labels into `"Label1|Label2"` for segment boundaries; converts `\Gamma` → `$\Gamma$` etc.
- `EMIN`/`EMAX` = ±3.5 eV — global energy window applied to all plots

### Known issue in CuS_MnFe2O4.ipynb

The PDOS export cell fails with `AttributeError: 'Dos' object has no attribute 'structure'` because `mpr.get_dos_by_material_id()` returns a plain `pymatgen.electronic_structure.dos.Dos` (not `CompleteDos`). To get element-resolved PDOS, use `mpr.get_dos_by_material_id(..., fields=["complete_dos"])` or access `CompleteDos` through the electronic structure summary endpoint.
