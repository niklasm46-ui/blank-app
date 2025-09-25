import io
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader


st.set_page_config(
    page_title="Boden- & Bauschuttanalyse (NRW)",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 Boden- und Bauschuttanalysen auswerten")
st.caption(
    "Auswertung gemäß typischen Grenzwerten der BBodSchV (Deutschland/NRW) und LAGA M20."
)

# ---------------------------------------------------------------------------
# Datenmodelle und Konstanten
# ---------------------------------------------------------------------------

REGULATION_INFO = {
    "soil": {
        "label": "Boden (BBodSchV)",
        "description": "Bundes-Bodenschutz- und Altlastenverordnung – typische Prüfwerte für A, B und C Nutzungskategorien.",
    },
    "construction": {
        "label": "Bauschutt (LAGA M20)",
        "description": "Leitfaden für das Recycling von mineralischen Abfällen – Zuordnungswerte Z0 bis Z2.",
    },
}

SOIL_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "A": {
        "Arsen": 20.0,
        "Blei": 100.0,
        "Cadmium": 1.0,
        "Chrom gesamt": 100.0,
        "Kupfer": 60.0,
        "Nickel": 50.0,
        "Quecksilber": 1.0,
        "Zink": 150.0,
        "Benzo[a]pyren": 0.5,
        "Summe PAK": 2.0,
    },
    "B": {
        "Arsen": 40.0,
        "Blei": 200.0,
        "Cadmium": 5.0,
        "Chrom gesamt": 200.0,
        "Kupfer": 100.0,
        "Nickel": 70.0,
        "Quecksilber": 2.0,
        "Zink": 400.0,
        "Benzo[a]pyren": 1.0,
        "Summe PAK": 10.0,
    },
    "C": {
        "Arsen": 100.0,
        "Blei": 400.0,
        "Cadmium": 10.0,
        "Chrom gesamt": 400.0,
        "Kupfer": 200.0,
        "Nickel": 140.0,
        "Quecksilber": 4.0,
        "Zink": 600.0,
        "Benzo[a]pyren": 4.0,
        "Summe PAK": 50.0,
    },
}

CONSTRUCTION_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "Z0": {
        "Arsen": 20.0,
        "Blei": 150.0,
        "Cadmium": 1.0,
        "Chrom gesamt": 100.0,
        "Kupfer": 60.0,
        "Nickel": 70.0,
        "Quecksilber": 1.0,
        "Zink": 200.0,
        "Summe PAK (EPA16)": 20.0,
        "PCB (Summe)": 0.02,
        "Sulfat wasserlöslich": 5000.0,
    },
    "Z1.1": {
        "Arsen": 30.0,
        "Blei": 200.0,
        "Cadmium": 2.0,
        "Chrom gesamt": 200.0,
        "Kupfer": 100.0,
        "Nickel": 90.0,
        "Quecksilber": 1.5,
        "Zink": 300.0,
        "Summe PAK (EPA16)": 40.0,
        "PCB (Summe)": 0.06,
        "Sulfat wasserlöslich": 10000.0,
    },
    "Z1.2": {
        "Arsen": 40.0,
        "Blei": 400.0,
        "Cadmium": 3.0,
        "Chrom gesamt": 300.0,
        "Kupfer": 150.0,
        "Nickel": 120.0,
        "Quecksilber": 2.0,
        "Zink": 500.0,
        "Summe PAK (EPA16)": 60.0,
        "PCB (Summe)": 0.1,
        "Sulfat wasserlöslich": 20000.0,
    },
    "Z2": {
        "Arsen": 50.0,
        "Blei": 500.0,
        "Cadmium": 5.0,
        "Chrom gesamt": 400.0,
        "Kupfer": 200.0,
        "Nickel": 150.0,
        "Quecksilber": 3.0,
        "Zink": 800.0,
        "Summe PAK (EPA16)": 80.0,
        "PCB (Summe)": 0.2,
        "Sulfat wasserlöslich": 40000.0,
    },
}

DEFAULT_UNITS = {
    "Arsen": "mg/kg",
    "Blei": "mg/kg",
    "Cadmium": "mg/kg",
    "Chrom gesamt": "mg/kg",
    "Kupfer": "mg/kg",
    "Nickel": "mg/kg",
    "Quecksilber": "mg/kg",
    "Zink": "mg/kg",
    "Benzo[a]pyren": "mg/kg",
    "Summe PAK": "mg/kg",
    "Summe PAK (EPA16)": "mg/kg",
    "PCB (Summe)": "mg/kg",
    "Sulfat wasserlöslich": "mg/kg",
}


@dataclass
class Measurement:
    parameter: str
    value: float
    unit: Optional[str] = None
    source: Optional[str] = None


# ---------------------------------------------------------------------------
# Utility Funktionen
# ---------------------------------------------------------------------------

def normalise_number(value: str) -> Optional[float]:
    value = value.strip().replace(" ", "")
    value = value.replace("<", "")  # für Angaben wie "<0,01"
    value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def parse_structured_line(line: str) -> Optional[Tuple[str, float, Optional[str]]]:
    """Parst Zeilen im Format "Parameter;Wert;Einheit" oder "Parameter\tWert"."""
    separators = [";", "\t", "|"]
    for sep in separators:
        if sep in line:
            parts = [p.strip() for p in line.split(sep) if p.strip()]
            if len(parts) >= 2:
                parameter = parts[0]
                value = normalise_number(parts[1])
                unit = parts[2] if len(parts) > 2 else None
                if parameter and value is not None:
                    return parameter, value, unit
    return None


def parse_regex_line(line: str) -> Optional[Tuple[str, float, Optional[str]]]:
    pattern = re.compile(
        r"^([A-Za-zÄÖÜäöüß0-9\-/\s\(\)\[\]\.]*)[\s:]+([0-9.,<>]+)\s*(mg/kg|mg/l|µg/l|g/kg|%)?",
        re.IGNORECASE,
    )
    match = pattern.match(line)
    if match:
        parameter = match.group(1).strip()
        value = normalise_number(match.group(2))
        unit = match.group(3)
        if parameter and value is not None:
            return parameter, value, unit
    return None


def parse_measurement_text(text: str, source: str) -> Tuple[List[Measurement], List[str]]:
    measurements: List[Measurement] = []
    skipped: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or len(line) < 3:
            continue
        parsed = parse_structured_line(line) or parse_regex_line(line)
        if parsed:
            parameter, value, unit = parsed
            measurements.append(Measurement(parameter=parameter, value=value, unit=unit, source=source))
        else:
            skipped.append(line)
    return measurements, skipped


def parse_pdf(file: io.BytesIO) -> Tuple[List[Measurement], List[str]]:
    try:
        pdf = PdfReader(file)
    except Exception as exc:  # pragma: no cover - defensive
        return [], [f"PDF konnte nicht gelesen werden: {exc}"]

    collected_measurements: List[Measurement] = []
    skipped: List[str] = []
    for page_no, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        page_measurements, page_skipped = parse_measurement_text(text, source=f"PDF Seite {page_no}")
        collected_measurements.extend(page_measurements)
        skipped.extend(page_skipped)
    return collected_measurements, skipped


def get_thresholds(regulation: str, category: str) -> Dict[str, float]:
    if regulation == "soil":
        return SOIL_THRESHOLDS.get(category, {})
    if regulation == "construction":
        return CONSTRUCTION_THRESHOLDS.get(category, {})
    return {}


def evaluate_measurements(
    measurements: List[Measurement], thresholds: Dict[str, float]
) -> pd.DataFrame:
    records = []
    for measurement in measurements:
        parameter = measurement.parameter
        value = measurement.value
        unit = measurement.unit or DEFAULT_UNITS.get(parameter, "mg/kg")
        threshold = thresholds.get(parameter)
        if threshold is not None:
            delta = value - threshold
            status = "⚠️ Überschreitung" if value > threshold else "✅ i.O."
            exceedance_percent = (value / threshold - 1) * 100 if threshold else None
        else:
            delta = None
            status = "ℹ️ Kein Grenzwert hinterlegt"
            exceedance_percent = None

        records.append(
            {
                "Parameter": parameter,
                "Messwert": value,
                "Einheit": unit,
                "Grenzwert": threshold,
                "Abweichung": delta,
                "Abweichung [%]": exceedance_percent,
                "Status": status,
                "Quelle": measurement.source,
            }
        )

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values(by=["Status", "Parameter"]).reset_index(drop=True)
    return df


def summarise_results(df: pd.DataFrame) -> Dict[str, int]:
    if df.empty:
        return {"total": 0, "exceedances": 0, "ok": 0, "missing": 0}
    exceedances = int((df["Status"] == "⚠️ Überschreitung").sum())
    ok = int((df["Status"] == "✅ i.O.").sum())
    missing = int((df["Status"] == "ℹ️ Kein Grenzwert hinterlegt").sum())
    return {"total": len(df), "exceedances": exceedances, "ok": ok, "missing": missing}


# ---------------------------------------------------------------------------
# Session State initialisieren
# ---------------------------------------------------------------------------

if "projects" not in st.session_state:
    st.session_state.projects = {}

if "active_project" not in st.session_state:
    st.session_state.active_project = "Standard"


# ---------------------------------------------------------------------------
# Sidebar – Projektverwaltung
# ---------------------------------------------------------------------------

st.sidebar.header("Projektverwaltung")

project_names = ["Standard"] + sorted(st.session_state.projects.keys())
active_project = st.sidebar.selectbox(
    "Aktive Auswertung",
    project_names,
    index=project_names.index(st.session_state.active_project)
    if st.session_state.active_project in project_names
    else 0,
)
st.session_state.active_project = active_project

with st.sidebar.expander("Neues Projekt anlegen", expanded=False):
    with st.form("create_project_form", clear_on_submit=True):
        project_name = st.text_input("Projektname", placeholder="z. B. Neubau Musterstraße")
        regulation_choice = st.selectbox(
            "Regelwerk",
            options=["soil", "construction"],
            format_func=lambda key: REGULATION_INFO[key]["label"],
        )
        category_options = (
            list(SOIL_THRESHOLDS.keys()) if regulation_choice == "soil" else list(CONSTRUCTION_THRESHOLDS.keys())
        )
        category = st.selectbox(
            "Kategorie",
            options=category_options,
            index=0,
        )

        base_thresholds = get_thresholds(regulation_choice, category)
        st.markdown("**Grenzwerte anpassen (mg/kg, mg/l etc.)**")
        override_values: Dict[str, float] = {}
        for parameter, limit in base_thresholds.items():
            override_values[parameter] = st.number_input(
                parameter,
                value=float(limit),
                key=f"override_{regulation_choice}_{category}_{parameter}",
                help="Grenzwert für dieses Projekt anpassen",
            )

        additional_limits_text = st.text_area(
            "Weitere Grenzwerte (optional)",
            help="Format pro Zeile: Parameter;Grenzwert;Einheit",
        )

        submitted = st.form_submit_button("Projekt speichern")

    if submitted:
        if not project_name:
            st.warning("Bitte einen Projektnamen angeben.")
        elif project_name in st.session_state.projects:
            st.warning("Projektname existiert bereits.")
        else:
            additional_limits: Dict[str, float] = {}
            if additional_limits_text.strip():
                extra_measurements, skipped_extra = parse_measurement_text(
                    additional_limits_text, source="Projektdefinition"
                )
                for measurement in extra_measurements:
                    additional_limits[measurement.parameter] = measurement.value
                if skipped_extra:
                    st.info(
                        "Folgende Zeilen konnten nicht als Grenzwert interpretiert werden: "
                        + ", ".join(skipped_extra)
                    )

            combined_thresholds = {**base_thresholds, **override_values, **additional_limits}
            st.session_state.projects[project_name] = {
                "regulation": regulation_choice,
                "category": category,
                "thresholds": combined_thresholds,
            }
            st.session_state.active_project = project_name
            st.success(f"Projekt '{project_name}' gespeichert und aktiviert.")

if active_project != "Standard":
    if st.sidebar.button("Projekt löschen", type="secondary"):
        del st.session_state.projects[active_project]
        st.session_state.active_project = "Standard"
        st.experimental_rerun()

# ---------------------------------------------------------------------------
# Hauptbereich – Auswertung
# ---------------------------------------------------------------------------

st.subheader("1. Analyse-Daten bereitstellen")
col_upload, col_manual = st.columns(2)

measurements: List[Measurement] = []
skipped_lines: List[str] = []

with col_upload:
    uploaded_file = st.file_uploader("PDF-Analyse hochladen", type=["pdf"], accept_multiple_files=False)
    if uploaded_file is not None:
        pdf_measurements, pdf_skipped = parse_pdf(uploaded_file)
        measurements.extend(pdf_measurements)
        if pdf_skipped:
            skipped_lines.extend(pdf_skipped)

with col_manual:
    manual_text = st.text_area(
        "Messwerte manuell einfügen",
        placeholder="z. B.\nArsen;35;mg/kg\nBlei;220;mg/kg",
        help="Unterstützte Formate: Parameter;Wert;Einheit oder Parameter Wert Einheit",
    )
    if manual_text.strip():
        manual_measurements, manual_skipped = parse_measurement_text(manual_text, source="Manuelle Eingabe")
        measurements.extend(manual_measurements)
        if manual_skipped:
            skipped_lines.extend(manual_skipped)

if skipped_lines:
    with st.expander("Nicht interpretierbare Zeilen", expanded=False):
        st.write("\n".join(skipped_lines))

st.subheader("2. Regelwerk & Grenzwerte wählen")

if st.session_state.active_project != "Standard":
    project = st.session_state.projects[st.session_state.active_project]
    regulation_choice = project["regulation"]
    category = project["category"]
    thresholds = project["thresholds"]
    st.info(
        f"Aktives Projekt: **{st.session_state.active_project}** – "
        f"{REGULATION_INFO[regulation_choice]['label']} Kategorie {category}."
    )
else:
    regulation_choice = st.radio(
        "Regelwerk",
        options=["soil", "construction"],
        format_func=lambda key: REGULATION_INFO[key]["label"],
        horizontal=True,
    )
    available_categories = (
        list(SOIL_THRESHOLDS.keys()) if regulation_choice == "soil" else list(CONSTRUCTION_THRESHOLDS.keys())
    )
    category = st.selectbox("Kategorie", options=available_categories)
    thresholds = get_thresholds(regulation_choice, category)
    st.caption(REGULATION_INFO[regulation_choice]["description"])

if thresholds:
    threshold_df = pd.DataFrame(
        {
            "Parameter": list(thresholds.keys()),
            "Grenzwert": list(thresholds.values()),
            "Einheit": [DEFAULT_UNITS.get(param, "mg/kg") for param in thresholds.keys()],
        }
    )
    with st.expander("Hinterlegte Grenzwerte", expanded=False):
        st.dataframe(threshold_df, use_container_width=True, hide_index=True)
else:
    st.warning("Für die gewählte Kombination sind keine Grenzwerte hinterlegt.")

st.subheader("3. Ergebnisse")

if measurements:
    result_df = evaluate_measurements(measurements, thresholds)
    summary = summarise_results(result_df)

    col_summary_1, col_summary_2, col_summary_3, col_summary_4 = st.columns(4)
    col_summary_1.metric("Messwerte gesamt", summary["total"])
    col_summary_2.metric("Überschreitungen", summary["exceedances"], delta=None)
    col_summary_3.metric("i.O.", summary["ok"])
    col_summary_4.metric("Ohne Grenzwert", summary["missing"])

    st.dataframe(result_df, use_container_width=True, hide_index=True)

    csv_data = result_df.to_csv(index=False, decimal=",", sep=";")
    st.download_button(
        "Ergebnis als CSV herunterladen",
        data=csv_data,
        file_name="auswertung.csv",
        mime="text/csv",
    )
else:
    st.info("Bitte eine PDF-Datei hochladen oder Messwerte manuell eingeben.")

st.markdown("---")
st.markdown(
    "💡 **Hinweis:** Die hinterlegten Grenzwerte dienen als Orientierung. "
    "Für verbindliche Bewertungen sollten stets die aktuellen gesetzlichen Vorgaben, behördliche Auflagen und projektbezogene Vereinbarungen geprüft werden."
)
