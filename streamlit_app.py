import streamlit as st
import pandas as pd

st.set_page_config(title="Abfall-Navigator", page_icon="♻️", layout="wide")

st.title("♻️ Abfall-Navigator für die Baustelle")
st.markdown(
    """
    Mit dieser App finden Sie auf einen Blick die wichtigsten Vorgaben und Empfehlungen
    für gängige Bau- und Abbruchabfälle. Wählen Sie einen Stoff aus oder filtern Sie nach
    Stichworten, um Anforderungen an Analysen, Transporte und Containergrößen zu sehen.
    """
)

materials = [
    {
        "name": "Baumischabfall",
        "category": "Gemischt",
        "description": "Gemischte Bau- und Abbruchabfälle mit Anteilen aus Holz, Kunststoff, Metall, Tapeten oder Putz.",
        "analysis": "In der Regel keine Laboranalyse nötig, solange keine Schadstoffe vermutet werden. Bei Brandschäden oder Verdacht auf teerhaltige Stoffe Kurzcheck durch Labor anfragen.",
        "analysis_need": "Nur bei Verdacht auf Schadstoffe",
        "transport": "Container sind Standard; Sattelkipper nur bei homogener und grober Mischung. Saubere Beladung und Ladungssicherung notwendig.",
        "recommended_container": "Absetzcontainer 7–10 m³ oder Abrollcontainer 20 m³ je nach Platz.",
        "allowed": [
            "Gemischte Baustellenreste ohne gefährliche Stoffe",
            "Tapeten, Kunststoffe, Folien",
            "Metall- und Kabelreste",
            "Kleinere Holz- und Dämmstoffanteile"
        ],
        "not_allowed": [
            "Asbest, Dämmung mit HBCD",
            "Teerhaltige Stoffe, Dachpappe",
            "Flüssigkeiten, Farben, Spraydosen",
            "Elektroschrott und Batterien"
        ],
        "documents": "Begleitschein nur bei Einstufung als gefährlicher Abfall; sonst Lieferschein mit Herkunft und AVV 17 09 04.",
        "tips": [
            "Je weniger Feinanteile, desto günstiger die Entsorgung.",
            "Container mit Planen abdecken, um Flugmüll zu vermeiden.",
            "Vorab Metalle separieren, um Kosten zu sparen."
        ],
        "vehicle_hint": "Sattelkipper nur nach Absprache, wenn Material grobkörnig und trocken ist.",
    },
    {
        "name": "Bauschutt",
        "category": "Mineralisch",
        "description": "Mineralische, sortenreine Fraktion aus Ziegeln, Betonbruch, Keramik und Mauerwerk ohne Störstoffe.",
        "analysis": "Keine Analyse für übliche Mengen; bei Rückbau alter Industriebauten oder Verdacht auf PCB/PAK punktuell beproben.",
        "analysis_need": "Nur bei Verdacht (PCB/PAK)",
        "transport": "Sattelkipper sehr gut geeignet (hohe Dichte). Container ebenfalls möglich.",
        "recommended_container": "Abrollcontainer 10–20 m³ oder Sattelkipper bei großen Mengen.",
        "allowed": [
            "Beton- und Ziegelbruch",
            "Mauerwerksreste und Dachziegel",
            "Fliesen und Keramik",
            "Naturstein"
        ],
        "not_allowed": [
            "Gipskarton oder Ytong",
            "Holz, Kunststoffe, Dämmung",
            "Asbesthaltige Baustoffe",
            "Teerhaltige Materialien"
        ],
        "documents": "AVV 17 01 07; Wiegeschein reicht. Recyclingquote meist >90%.",
        "tips": [
            "Metallteile und Folien vorab aussortieren.",
            "Feine Gipsanteile vermeiden, um Deponieanforderungen einzuhalten.",
            "Container nicht über Oberkante beladen."
        ],
        "vehicle_hint": "Schüttgut ideal für Kipper; bei steilen Zufahrten Container wählen.",
    },
    {
        "name": "Beton (rein)",
        "category": "Mineralisch",
        "description": "Sortenreiner, armierten oder unbewehrten Betonbruch ohne Anhaftungen.",
        "analysis": "Keine Analyse bei üblichen Baustellen; bei Anstrichen mit PCB/PAK oder Estrich mit Klebstoff Rückstellprobe klären.",
        "analysis_need": "Nur bei beschichteten/verdächtigen Flächen",
        "transport": "Sattelkipper oder Container gleichermaßen möglich. Hohe Dichte beachten (Gewichtsgrenze!).",
        "recommended_container": "Abrollcontainer 10–15 m³ wegen Gewichtsbeschränkung.",
        "allowed": [
            "Betonplatten und Stürze",
            "Fundamente, Estriche",
            "Armierter Beton nach Zerkleinerung"
        ],
        "not_allowed": [
            "Bitumenreste oder Kleber",
            "Boden und Muttererde",
            "Holz- oder Kunststoffeinschlüsse"
        ],
        "documents": "AVV 17 01 01; Lieferschein/Wiegeschein genügt.",
        "tips": [
            "Große Brocken vor Ort brechen lassen, um Gewicht gleichmäßig zu verteilen.",
            "Bei dicken Eisenanteilen Bauschuttcontainer bestellen und mit Bagger vorsichtig verladen.",
            "Container wegen Gewicht nicht größer als 15 m³ wählen."
        ],
        "vehicle_hint": "Kipper möglich, solange Verladegerät vorhanden ist und Material nicht klebt.",
    },
    {
        "name": "Boden/Aushub",
        "category": "Boden",
        "description": "Naturbelassener oder geringer belasteter Boden, Lehm oder Sand aus Baugruben und Leitungsgräben.",
        "analysis": "Für Bauvorhaben >30 m³ meist eine Haufwerksanalyse nach LAGA M20 oder Bundesland-Vorgaben notwendig. Kleinmengen oft ohne Labor, wenn Herkunft klar ist.",
        "analysis_need": "Ja, ab ca. 30 m³ oder bei Unsicherheit",
        "transport": "Sattelkipper üblich. Container bei Platzmangel oder kurzen Distanzen.",
        "recommended_container": "Abrollcontainer 10–20 m³ oder Kipper; bei feuchtem Material gegen Abrinnen sichern.",
        "allowed": [
            "Naturbelassener Boden, Sand, Kies",
            "Geringer Wurzel- und Steingehalt",
            "Unbelasteter Oberboden"
        ],
        "not_allowed": [
            "Boden mit Bauschutt- oder Asphaltanteilen",
            "Boden mit Geruch (Öl, Benzin)",
            "Torfiges oder organisch belastetes Material"
        ],
        "documents": "Analysebericht und Einstufung (z.B. Z0–Z2), Lieferschein mit Herkunft.",
        "tips": [
            "Haufwerke getrennt lagern, wenn unterschiedliche Bodenschichten anfallen.",
            "Feuchte Haufen abdecken, um Auswaschung zu vermeiden.",
            "Vor Abfuhr Abstimmung mit Deponie oder Verwerter einholen."
        ],
        "vehicle_hint": "Kipper bevorzugt; Container bei engen Zufahrten oder Mengen <20 m³.",
    },
    {
        "name": "Holz (A1–A3)",
        "category": "Holz",
        "description": "Unbehandeltes oder schwach behandeltes Bauholz wie Bretter, Schalungen, Paletten ohne Holzschutzmittel.",
        "analysis": "Keine Analyse für A1–A3. Bei Verdacht auf Holzschutzmittel (A4) oder Brandschäden Laborprüfung auf PCP/PAK.",
        "analysis_need": "Nein, außer bei Verdacht auf Holzschutzmittel",
        "transport": "Container oder Kipper möglich; Holz ist leicht und volumenlastig.",
        "recommended_container": "Absetzcontainer 7–10 m³ oder Abrollcontainer 20–35 m³.",
        "allowed": [
            "Paletten, Bretter, Latten",
            "Konstruktionsholz ohne Anstrich",
            "Möbelholz ohne Glas und Polster"
        ],
        "not_allowed": [
            "Bahnschwellen, mit Teer/Creosot behandeltes Holz",
            "HBCD-haltige Dämmung oder teerhaltige Dachpappe",
            "Fenster mit Glas (separat listen)",
            "Verbundplatten mit PVC"
        ],
        "documents": "AVV 17 02 01 für A1–A3; bei A4 als gefährlicher Abfall mit Nachweis.",
        "tips": [
            "Lange Teile kürzen, damit sie in den Container passen.",
            "Nasse Mengen vermeiden, um Schimmelbildung und Mehrgewicht zu reduzieren.",
            "Metallbeschläge grob entfernen, wenn möglich."
        ],
        "vehicle_hint": "Große Volumina passen besser in Abrollcontainer mit hohen Bordwänden.",
    },
    {
        "name": "Fenster und Türen",
        "category": "Gemischt",
        "description": "Ausgebaute Fenster- oder Türelemente aus Holz, Kunststoff oder Aluminium, oft mit Glas und Beschlägen.",
        "analysis": "Keine Analyse nötig. Bei Altbauten auf PCB-haltige Fugenmassen achten; ggf. Rücksprache mit Entsorger.",
        "analysis_need": "Nein, PCB-Fugen bei Altbauten prüfen",
        "transport": "Container mit Stapelschutz oder geschlossene Mulden nutzen, um Glasbruch zu sichern.",
        "recommended_container": "Absetzcontainer 7–10 m³; bei größeren Mengen Gitterboxen oder Glascontainer abklären.",
        "allowed": [
            "Komplette Elemente mit Rahmen",
            "Isolier- und Einfachglas",
            "Metall- oder Kunststoffbeschläge"
        ],
        "not_allowed": [
            "Asbesthaltige Fensterbänke",
            "Rollläden mit PU-Schaumfüllung (separat erfassen)",
            "Elektrische Bauteile wie Motoren ohne Ausbau"
        ],
        "documents": "AVV 17 02 04 (Metall) oder 17 02 01 (Holz) je nach Materialanteil; Herkunftsdokumentation hilft bei Verwertern.",
        "tips": [
            "Glasflächen mit Klebeband sichern, um Splittern vorzubeugen.",
            "Elemente stapeln und mit Holzlatten trennen, um Bruch zu vermeiden.",
            "Rahmenmaterial grob sortieren (Holz/Metall), um bessere Verwertung zu ermöglichen."
        ],
        "vehicle_hint": "Geschlossene Container oder Mulden bevorzugen; Kipper nur bei großen, massiven Posten ohne Glas.",
    },
    {
        "name": "Sperrmüll von Baustellen",
        "category": "Gemischt",
        "description": "Große, nicht mehr benötigte Gegenstände wie Möbel, Teppiche, Sanitärkeramik oder Verpackungen aus Ausbauarbeiten.",
        "analysis": "Keine Analyse erforderlich. Prüfen, ob Elektrogeräte separat gesammelt werden müssen.",
        "analysis_need": "Nein",
        "transport": "Container bevorzugt, da Stückgut. Bei großen Mengen Presscontainer erwägen.",
        "recommended_container": "Absetzcontainer 7–10 m³ oder Abrollcontainer 20 m³.",
        "allowed": [
            "Möbel, Teppiche, Matratzen",
            "Keramik (Waschbecken, WCs)",
            "Kunststoffteile und Verpackungen",
            "Großes Stückgut ohne Schadstoffe"
        ],
        "not_allowed": [
            "Elektrogeräte und Leuchtstoffröhren",
            "Farben, Lacke, Spraydosen",
            "Bauschutt oder Boden",
            "Gefahrstoffe (Öle, Chemikalien)"
        ],
        "documents": "AVV 20 03 07; Lieferschein reicht. Elektrogeräte separat nach ElektroG.",
        "tips": [
            "Polster und Textilien trocken lagern, um Schimmel zu vermeiden.",
            "Beim Beladen schwere Teile unten, leichte oben stapeln.",
            "Bruchgefährliche Keramik mit Decken oder Karton trennen."
        ],
        "vehicle_hint": "Container ist am sichersten; offener Kipper nur mit Sicherung und Plane.",
    },
]

categories = sorted({item["category"] for item in materials})

with st.sidebar:
    st.header("Filter")
    search = st.text_input("Suche nach Material oder Stichwort", placeholder="z.B. Beton, Holz, Analyse")
    category_filter = st.multiselect("Kategorie auswählen", options=categories, default=categories)
    transport_pref = st.selectbox(
        "Transportpräferenz",
        ["Alle", "Container bevorzugt", "Kipper möglich"],
        help="Filtern Sie nach Empfehlungen für Container oder Sattelkipper."
    )


def matches_transport(material: dict, preference: str) -> bool:
    if preference == "Alle":
        return True
    if preference == "Container bevorzugt":
        return "Container" in material["transport"] or "Container" in material["vehicle_hint"]
    if preference == "Kipper möglich":
        return "Kipper" in material["transport"] or "Kipper" in material["vehicle_hint"]
    return True


def filter_materials(data: list, term: str, selected_categories: list, preference: str) -> list:
    term_lower = term.lower()
    results = []
    for item in data:
        if item["category"] not in selected_categories:
            continue
        text = " ".join(
            [
                item["name"],
                item["description"],
                item["analysis"],
                item["analysis_need"],
                item["transport"],
                " ".join(item.get("allowed", [])),
                " ".join(item.get("not_allowed", [])),
            ]
        ).lower()
        if term_lower and term_lower not in text:
            continue
        if not matches_transport(item, preference):
            continue
        results.append(item)
    return sorted(results, key=lambda x: x["name"])


def render_material_card(material: dict) -> None:
    st.subheader(material["name"])
    st.caption(f"Kategorie: {material['category']}")
    st.markdown(material["description"])

    top_cols = st.columns([1, 1, 1])
    top_cols[0].info(f"**Analyse:** {material['analysis']}")
    top_cols[1].success(f"**Transport:** {material['transport']}")
    top_cols[2].warning(f"**Container:** {material['recommended_container']}")

    list_cols = st.columns(2)
    list_cols[0].markdown("**Erlaubt:**")
    list_cols[0].markdown("\n".join([f"- {entry}" for entry in material["allowed"]]))

    list_cols[1].markdown("**Nicht geeignet:**")
    list_cols[1].markdown("\n".join([f"- {entry}" for entry in material["not_allowed"]]))

    st.markdown("**Dokumente & Codes:**")
    st.markdown(material["documents"])

    st.markdown("**Tipps für die Praxis:**")
    st.markdown("\n".join([f"- {tip}" for tip in material["tips"]]))

    st.info(material["vehicle_hint"])

    st.divider()


filtered_materials = filter_materials(materials, search, category_filter, transport_pref)

if not filtered_materials:
    st.warning("Keine Treffer für die aktuelle Auswahl. Bitte Filter anpassen.")
else:
    summary_df = pd.DataFrame(
        [
            {
                "Material": item["name"],
                "Kategorie": item["category"],
                "Analyse nötig?": item["analysis_need"],
                "Transportempfehlung": item["transport"],
                "Container": item["recommended_container"],
            }
            for item in filtered_materials
        ]
    )

    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("### Detailinformationen")
    for material in filtered_materials:
        render_material_card(material)

st.markdown(
    """
    _Hinweis: Angaben ohne Gewähr. Regionale Annahmebedingungen können abweichen – bitte lokale Vorgaben
    und Entsorger-Anforderungen prüfen, insbesondere bei belastetem Boden, teerhaltigen Stoffen
    oder asbesthaltigen Materialien._
    """
)
