import re
from pathlib import Path

import pandas as pd
import streamlit as st

from lib.app_shell import init_state, hide_default_streamlit_pages_nav, render_sidebar


# -----------------------------
# Page shell
# -----------------------------
st.set_page_config(page_title="🧑‍💼 Find Agent", layout="wide")
init_state()
hide_default_streamlit_pages_nav()
render_sidebar()


# -----------------------------
# Helpers
# -----------------------------
def clean_email(x):
    if pd.isna(x):
        return None
    x = str(x).strip().lower()
    return x if x and x != "nan" else None


def clean_phone(x):
    if pd.isna(x):
        return None
    digits = re.sub(r"\D+", "", str(x))
    return digits if len(digits) >= 10 else None


def clean_text(x):
    if pd.isna(x):
        return None
    x = str(x).strip()
    return x if x and x.lower() != "nan" else None


def clean_url(x):
    if pd.isna(x):
        return None
    x = str(x).strip()
    if not x or x.lower() == "nan":
        return None
    if x.startswith("www."):
        x = "https://" + x
    if not (x.startswith("http://") or x.startswith("https://")):
        if "." in x:
            x = "https://" + x
    return x


def fmt_phone(digits):
    if not digits:
        return "—"
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    return digits


def fmt_money(x):
    if pd.isna(x):
        return "—"
    try:
        return f"${float(x):,.0f}"
    except Exception:
        return str(x)


def fmt_num(x):
    if pd.isna(x):
        return "—"
    try:
        return f"{float(x):,.0f}"
    except Exception:
        return str(x)


def safe_loc(city, state, zipc):
    parts = [city, state, zipc]
    parts = [
        str(x).strip()
        for x in parts
        if x is not None and str(x).strip() and str(x).lower() != "nan"
    ]
    return " • ".join(parts) if parts else None


def html_link_button(label: str, url: str, *, new_tab: bool = False):
    # Not a Streamlit widget → no duplicate-ID problems inside loops.
    target = "_blank" if new_tab else "_self"
    st.markdown(
        f"""
        <a href="{url}" target="{target}" style="text-decoration:none;">
            <button style="
                width:100%;
                padding:0.5rem 0.75rem;
                border-radius:0.5rem;
                border:1px solid rgba(49, 51, 63, 0.2);
                background: white;
                cursor: pointer;">
                {label}
            </button>
        </a>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Load listings table (deploy/Agent.csv)
# -----------------------------
@st.cache_data(show_spinner=False)
def load_listings() -> pd.DataFrame:
    base_dir = Path(__file__).resolve().parents[1]  # .../deploy
    csv_path = base_dir / "Agent.csv"
    return pd.read_csv(csv_path)


def build_agent_directory(listings: pd.DataFrame) -> pd.DataFrame:
    df = listings.copy()

    # Normalize fields we’ll use
    df["agent_name"] = df["LISTINGAGENT_NAME"].apply(clean_text)
    df["agent_email"] = df["LISTINGAGENT_EMAIL"].apply(clean_email)
    df["agent_phone"] = df["LISTINGAGENT_PHONE"].apply(clean_phone)
    df["agent_website"] = df["LISTINGAGENT_WEBSITE"].apply(clean_url)

    df["office_name"] = df["LISTINGOFFICE_NAME"].apply(clean_text)
    df["office_email"] = df["LISTINGOFFICE_EMAIL"].apply(clean_email)
    df["office_phone"] = df["LISTINGOFFICE_PHONE"].apply(clean_phone)
    df["office_website"] = df["LISTINGOFFICE_WEBSITE"].apply(clean_url)

    # Ensure ZIPCODE doesn't break joins/displays
    df["ZIPCODE"] = df["ZIPCODE"].astype("string")

    # Numeric columns
    df["PRICE"] = pd.to_numeric(df["PRICE"], errors="coerce")
    df["DAYSONMARKET"] = pd.to_numeric(df["DAYSONMARKET"], errors="coerce")

    # Build agent_key (email → phone → name|office)
    df["agent_key"] = df["agent_email"]
    df.loc[df["agent_key"].isna(), "agent_key"] = df.loc[df["agent_key"].isna(), "agent_phone"]
    df.loc[df["agent_key"].isna(), "agent_key"] = (
        df.loc[df["agent_key"].isna(), "agent_name"].fillna("") + "|" +
        df.loc[df["agent_key"].isna(), "office_name"].fillna("")
    )

    # Keep rows with some agent identity
    df = df[df["agent_name"].notna() | df["agent_email"].notna() | df["agent_phone"].notna()].copy()

    def mode_nonnull(s):
        s = s.dropna()
        if s.empty:
            return None
        m = s.mode()
        return m.iloc[0] if not m.empty else s.iloc[0]

    def count_active(s):
        s = s.astype("string").str.lower()
        return int((s == "active").sum())

    agents = (
        df.groupby("agent_key", dropna=False)
        .agg(
            agent_name=("agent_name", mode_nonnull),
            agent_email=("agent_email", mode_nonnull),
            agent_phone=("agent_phone", mode_nonnull),
            agent_website=("agent_website", mode_nonnull),

            office_name=("office_name", mode_nonnull),
            office_email=("office_email", mode_nonnull),
            office_phone=("office_phone", mode_nonnull),
            office_website=("office_website", mode_nonnull),

            top_city=("CITY", mode_nonnull),
            top_state=("STATE", mode_nonnull),
            top_zip=("ZIPCODE", mode_nonnull),

            total_listings=("MLSNUMBER", "nunique"),
            active_listings=("STATUS", count_active),
            median_price=("PRICE", "median"),
            median_dom=("DAYSONMARKET", "median"),

            property_types=("PROPERTYTYPE", lambda s: sorted([x for x in s.dropna().unique()])),
            statuses=("STATUS", lambda s: sorted([x for x in s.dropna().unique()])),
        )
        .reset_index()
    )

    agents["has_contact"] = (
        agents["agent_email"].notna() |
        agents["agent_phone"].notna() |
        agents["agent_website"].notna()
    )

    return agents.sort_values(
        by=["has_contact", "active_listings", "total_listings"],
        ascending=[False, False, False],
        kind="mergesort",
    )


# -----------------------------
# UI
# -----------------------------
st.title("🧑‍💼 Find Agent")
st.caption("Agents are derived from the listings table (grouped by email/phone/name+office).")

try:
    listings = load_listings()
except Exception as e:
    st.error("Could not load deploy/Agent.csv. Make sure it exists next to Home.py.")
    st.exception(e)
    st.stop()

agents = build_agent_directory(listings)

# Top controls
q = st.text_input("Search agent / office / email / city", placeholder="e.g. Sarah, Keller, dallas, @gmail.com")

c1, c2, c3, c4, c5 = st.columns([1.2, 1.4, 1.4, 1.4, 1.6])
with c1:
    contact_only = st.checkbox("Only with contact", value=True)

with c2:
    state_options = ["All"] + sorted([x for x in agents["top_state"].dropna().unique()])
    state_choice = st.selectbox("State", state_options, index=0)

with c3:
    city_options = ["All"] + sorted([x for x in agents["top_city"].dropna().unique()])
    city_choice = st.selectbox("City", city_options, index=0)

with c4:
    view = st.selectbox("View", ["Cards", "Table"], index=0)

with c5:
    max_show = st.selectbox("Max results", [10, 25, 50, 100, 200], index=1)

# Optional filters on portfolio (property type / status)
f1, f2 = st.columns(2)
with f1:
    prop_options = sorted({p for lst in agents["property_types"].dropna() for p in (lst or [])})
    prop_choice = st.selectbox("Property type (portfolio)", ["All"] + prop_options, index=0)

with f2:
    status_options = sorted({s for lst in agents["statuses"].dropna() for s in (lst or [])})
    status_choice = st.selectbox("Status (portfolio)", ["All"] + status_options, index=0)

# Filter
filtered = agents.copy()

if contact_only:
    filtered = filtered[filtered["has_contact"]]

if state_choice != "All":
    filtered = filtered[filtered["top_state"] == state_choice]

if city_choice != "All":
    filtered = filtered[filtered["top_city"] == city_choice]

if prop_choice != "All":
    filtered = filtered[filtered["property_types"].apply(lambda lst: prop_choice in (lst or []))]

if status_choice != "All":
    filtered = filtered[filtered["statuses"].apply(lambda lst: status_choice in (lst or []))]

if q.strip():
    qq = q.strip().lower()

    def match_row(r):
        hay = " ".join([
            str(r.get("agent_name") or ""),
            str(r.get("office_name") or ""),
            str(r.get("agent_email") or ""),
            str(r.get("top_city") or ""),
            str(r.get("top_state") or ""),
        ]).lower()
        return qq in hay

    filtered = filtered[filtered.apply(match_row, axis=1)]

# Limit
filtered = filtered.head(max_show)

st.divider()

# Summary + download
m1, m2, m3 = st.columns(3)
m1.metric("Agents found", len(filtered))
m2.metric("Contactable", int(filtered["has_contact"].sum()) if len(filtered) else 0)
m3.metric("Listings represented", int(filtered["total_listings"].sum()) if len(filtered) else 0)

# Prepare downloadable table (works for both views)
download_cols = [
    "agent_name", "office_name", "top_city", "top_state", "top_zip",
    "agent_phone", "agent_email", "agent_website",
    "active_listings", "total_listings", "median_price", "median_dom"
]
download_cols = [c for c in download_cols if c in filtered.columns]
download_df = filtered[download_cols].copy()

# Format a bit for export (optional)
if "agent_phone" in download_df.columns:
    download_df["agent_phone"] = download_df["agent_phone"].apply(fmt_phone)

csv_bytes = download_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download results (CSV)",
    data=csv_bytes,
    file_name="find_agent_results.csv",
    mime="text/csv",
    use_container_width=True,
)

# -----------------------------
# Display
# -----------------------------
if view == "Table":
    table_df = filtered.copy()
    if "agent_phone" in table_df.columns:
        table_df["agent_phone"] = table_df["agent_phone"].apply(fmt_phone)
    if "median_price" in table_df.columns:
        table_df["median_price"] = table_df["median_price"].apply(fmt_money)
    if "median_dom" in table_df.columns:
        table_df["median_dom"] = table_df["median_dom"].apply(fmt_num)

    show_cols = [
        "agent_name", "office_name", "top_city", "top_state", "top_zip",
        "agent_phone", "agent_email", "agent_website",
        "active_listings", "total_listings", "median_price", "median_dom",
    ]
    show_cols = [c for c in show_cols if c in table_df.columns]
    st.dataframe(table_df[show_cols], use_container_width=True)

else:
    for i, (_, r) in enumerate(filtered.iterrows()):
        name = r.get("agent_name") or "Unknown agent"
        office = r.get("office_name") or "—"

        phone = r.get("agent_phone")
        email = r.get("agent_email")
        web = r.get("agent_website")

        loc = safe_loc(r.get("top_city"), r.get("top_state"), r.get("top_zip"))

        with st.container(border=True):
            top = st.columns([3, 2], gap="large")

            with top[0]:
                st.markdown(f"### {name}")
                st.write(f"**Office:** {office}")
                if loc:
                    st.caption(f"📍 {loc}")

                st.caption(
                    f"Median price: **{fmt_money(r.get('median_price'))}** • "
                    f"Median DOM: **{fmt_num(r.get('median_dom'))}**"
                )

            with top[1]:
                st.metric("Active", int(r.get("active_listings") or 0))
                st.metric("Total", int(r.get("total_listings") or 0))

            actions = st.columns(3)

            with actions[0]:
                if phone:
                    html_link_button("📞 Call", f"tel:{phone}", new_tab=False)
                else:
                    st.button("📞 Call", disabled=True, use_container_width=True, key=f"call_disabled_{i}")

            with actions[1]:
                if email:
                    html_link_button("✉️ Email", f"mailto:{email}", new_tab=False)
                else:
                    st.button("✉️ Email", disabled=True, use_container_width=True, key=f"email_disabled_{i}")

            with actions[2]:
                if web:
                    html_link_button("🌐 Website", web, new_tab=True)
                else:
                    st.button("🌐 Website", disabled=True, use_container_width=True, key=f"web_disabled_{i}")
