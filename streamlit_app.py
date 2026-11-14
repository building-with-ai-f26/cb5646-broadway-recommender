"""Broadway Concierge - show recommender web page. Run with: streamlit run streamlit_app.py"""
import streamlit as st

import time

from analytics import new_visitor_id, track
from app import DEALBREAKERS, LONG_RUNTIME_MIN, infer_answers, recommend_shows

st.set_page_config(page_title="Broadway Concierge", page_icon="🎭")

if "visitor" not in st.session_state:
    st.session_state.visitor = new_visitor_id()
    st.session_state.started = time.time()
    st.session_state.shown_once = False
    track(st.session_state.visitor, "app_opened")

st.title("🎭 Broadway Concierge")
st.write("Tell us about your night and get 3 Broadway shows that fit your group, mood and budget.")

# Form defaults live in session_state so the description can fill them in.
DEFAULTS = {"who": "(not sure)", "kids_ages": "", "mood": "(any)", "show_type": "Either", "first_show": "Not said",
            "no_limit": False, "max_price": 150, "dealbreakers": []}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)
st.session_state.setdefault("manual", set())   # fields the person changed by hand: never overwritten
st.session_state.setdefault("filled", [])      # fields filled in from the description


def mark_manual(key):
    st.session_state.manual.add(key)


def prefill():
    """Fill the form from the description, skipping anything the person set by hand."""
    got = infer_answers(st.session_state.text)
    ss, filled = st.session_state, []

    def put(key, value):
        if key not in ss.manual:
            ss[key] = value
            filled.append(key)

    if "who" in got:
        put("who", got["who"])
    if "age" in got:
        put("kids_ages", str(got["age"]))
    if "mood" in got:
        put("mood", "something different" if got["mood"] == "surprise" else got["mood"])
    if "showType" in got:
        put("show_type", got["showType"].capitalize())
    if "budget" in got:
        if got["budget"] is None:
            put("no_limit", True)
        elif "no_limit" not in ss.manual and "max_price" not in ss.manual:
            ss.no_limit = False
            ss.max_price = max(40, min(400, round(got["budget"] / 10) * 10))
            filled.append("max_price")
    if got.get("first") == "yes":
        put("first_show", "Yes")
    if got.get("rules") and "dealbreakers" not in ss.manual:
        ss.dealbreakers = sorted(set(ss.dealbreakers) | set(got["rules"]), key=DEALBREAKERS.index)
        filled.append("dealbreakers")
    ss.filled = filled
    if filled:
        track(ss.visitor, "answers_prefilled", fields=filled)


text = st.text_area(
    "Tell us about your night",
    key="text",
    on_change=prefill,
    placeholder="Taking my mom for her birthday. She loved Wicked, we want to laugh, and $150 a ticket is our max.",
    height=120,
)
LABELS = {"who": "who's going", "kids_ages": "kids' ages", "mood": "mood", "show_type": "musical or play",
          "max_price": "max price", "no_limit": "no budget limit", "first_show": "first Broadway show", "dealbreakers": "dealbreakers"}
if st.session_state.filled:
    st.caption("✨ Filled in from your description: " + ", ".join(LABELS[k] for k in st.session_state.filled)
               + ". Change anything below.")
else:
    st.caption("Click outside the box (or press Ctrl+Enter) and we fill in the form below from what you wrote.")

col1, col2 = st.columns(2)
with col1:
    who = st.selectbox("Who's going?", ["(not sure)", "solo", "date", "friends", "family", "kids"], key="who",
                       format_func=lambda w: {"family": "family (adults only)", "kids": "taking kids"}.get(w, w),
                       on_change=mark_manual, args=("who",))
    kids_ages = ""
    if who == "kids":
        kids_ages = st.text_input("Kids' ages (if any)", placeholder="e.g. 6, 10", key="kids_ages",
                                  on_change=mark_manual, args=("kids_ages",))
    mood = st.selectbox("Mood", ["(any)", "laugh", "cry", "be wowed", "sing along", "something different"], key="mood",
                        on_change=mark_manual, args=("mood",))
    show_type = st.radio("Musical or play?", ["Either", "Musical", "Play"], horizontal=True, key="show_type",
                         on_change=mark_manual, args=("show_type",))
    first_show = st.radio("First Broadway show?", ["Not said", "Yes", "No"], horizontal=True, key="first_show",
                          on_change=mark_manual, args=("first_show",))
with col2:
    no_limit = st.checkbox("No budget limit", key="no_limit", on_change=mark_manual, args=("no_limit",))
    max_price = None if no_limit else st.slider("Max price per ticket ($)", 40, 400, step=10, key="max_price",
                                                on_change=mark_manual, args=("max_price",))
    dealbreakers = st.multiselect(
        "Dealbreakers",
        DEALBREAKERS,
        key="dealbreakers",
        on_change=mark_manual, args=("dealbreakers",),
        help=(f"'long runtime' means longer than {(LONG_RUNTIME_MIN - 1) // 60}h{(LONG_RUNTIME_MIN - 1) % 60}m. "
              "'adult themes' means death, violence, abuse or war. "
              "'no intermission' means you only want shows that run straight through."),
    )

if st.button("Find my shows", type="primary"):
    if not text.strip():
        st.warning("Write a sentence or two about your night first.")
        track(st.session_state.visitor, "find_clicked_empty")
        st.stop()
    with st.spinner("Picking your shows..."):
        try:
            result = recommend_shows(
                text.strip(),
                who=None if who == "(not sure)" else who,
                kids_ages=kids_ages,
                mood=None if mood == "(any)" else mood,
                max_price=max_price,
                dealbreakers=dealbreakers,
                first_show={"Yes": True, "No": False}.get(first_show),
                show_type=show_type.lower() if show_type != "Either" else None,
            )
        except RuntimeError as e:  # missing API key
            st.error(str(e))
            track(st.session_state.visitor, "recommend_failed", reason="missing_api_key")
            st.stop()
        except Exception as e:
            st.error(f"Something went wrong talking to the AI: {e}")
            track(st.session_state.visitor, "recommend_failed", reason="error")
            st.stop()

    first = not st.session_state.shown_once
    st.session_state.shown_once = True
    track(
        st.session_state.visitor, "picks_shown",
        who=who, mood=mood, show_type=show_type, max_price=max_price if max_price is not None else "any",
        dealbreakers=list(dealbreakers), first_show=first_show,
        has_kids_ages=bool(kids_ages.strip()), text_length=len(text.strip()),
        picks=[p["title"] for p in result["picks"]],
        near_misses=sum(1 for p in result["picks"] if not p["fits_all_limits"]),
        seconds_to_first_picks=round(time.time() - st.session_state.started, 1) if first else None,
    )

    if result["message"]:
        st.info(result["message"])
    for i, p in enumerate(result["picks"], 1):
        with st.container(border=True):
            label = "" if p["fits_all_limits"] else "  ·  ⚠️ near miss"
            st.subheader(f"{i}. {p['title']}{label}")
            st.caption(p["theater"])
            st.write(p["why_it_fits"])
            st.write(f"**Heads up:** {p['caution']}")
            st.write(f"**Price:** {p['price_range']}")
            if p["rush_or_lottery"]:
                st.write("🎟️ Rush or lottery tickets are often available. Check the official show site.")
    if result["assumptions"]:
        st.caption(f"Assumptions we made: {result['assumptions']}")
    st.caption("Prices are typical ranges from a hand-built catalog, not live. Always confirm on the official ticket seller.")
