"""Broadway Concierge - show recommender web page. Run with: streamlit run streamlit_app.py"""
import streamlit as st

import datetime as dt
import time

from analytics import new_visitor_id, track
from app import (DEALBREAKERS, LONG_RUNTIME_MIN, RateLimiter, active_deals, featured_picks, fmt_day, fmt_time, infer_answers,
                 load_featured, load_shows, recommend_shows)

st.set_page_config(page_title="Broadway Concierge", page_icon="🎭")


@st.cache_resource
def rate_limiter():
    """One limiter shared by every visitor session on this server."""
    return RateLimiter()


def visitor_key():
    """Who to rate-limit: the visitor's IP when hosted, otherwise this browser session."""
    try:
        forwarded = (st.context.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        ip = forwarded or getattr(st.context, "ip_address", None)
    except Exception:
        ip = None
    if isinstance(ip, str) and ip.strip():
        return f"ip:{ip.strip()}"
    return f"session:{st.session_state.visitor}"

if "visitor" not in st.session_state:
    st.session_state.visitor = new_visitor_id()
    st.session_state.started = time.time()
    st.session_state.shown_once = False
    track(st.session_state.visitor, "app_opened")

st.title("🎭 Broadway Concierge")
st.write("Tell us about your night and get 3 Broadway shows that fit your group, mood and budget.")

# Form defaults live in session_state so the description can fill them in.
DEFAULTS = {"who": "(not sure)", "kids_ages": "", "mood": "(any)", "show_type": "Either", "first_show": "Not said",
            "no_limit": False, "max_price": 150, "dealbreakers": [], "go_date": None, "time_of_day": "Any time"}
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
    if "date" in got:
        put("go_date", dt.date.fromisoformat(got["date"]))
    if "timeOfDay" in got:
        put("time_of_day", got["timeOfDay"].capitalize())
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
          "max_price": "max price", "no_limit": "no budget limit", "go_date": "date", "time_of_day": "time of day", "first_show": "first Broadway show", "dealbreakers": "dealbreakers"}
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
    go_date = st.date_input("When are you going? (optional)", key="go_date", min_value=dt.date.today(),
                            format="MM/DD/YYYY", on_change=mark_manual, args=("go_date",),
                            help="Only shows playing that day are picked. Times come from a regular week; "
                                 "holiday weeks can differ, so confirm on the show's site.")
    time_of_day = "Any time"
    if go_date:
        time_of_day = st.radio("Time of day", ["Any time", "Matinee", "Evening"], horizontal=True, key="time_of_day",
                               on_change=mark_manual, args=("time_of_day",))
    seen = st.multiselect("Shows you've already seen (optional)", sorted(s["title"] for s in load_shows()), key="seen",
                          help="We won't suggest these.")
    dealbreakers = st.multiselect(
        "Dealbreakers",
        DEALBREAKERS,
        key="dealbreakers",
        on_change=mark_manual, args=("dealbreakers",),
        help=(f"'long runtime' means longer than {(LONG_RUNTIME_MIN - 1) // 60}h{(LONG_RUNTIME_MIN - 1) % 60}m. "
              "'adult themes' means death, violence, abuse or war. "
              "'no intermission' means you only want shows that run straight through."),
    )

CATALOG = {s["title"]: s for s in load_shows()}
TODAY = dt.date.today().isoformat()


def show_card(i, p):
    """One pick: title, what the show is about, any deal running now, why it fits, and the official site."""
    show = CATALOG.get(p["title"], {})
    with st.container(border=True):
        if p.get("featured"):
            label = f"  ·  {p['featured_label']}"
        else:
            label = "" if p["fits_all_limits"] else "  ·  ⚠️ near miss"
        st.subheader(f"{i}. {p['title']}{label}")
        st.caption(p["theater"])
        if show.get("about"):
            st.write(show["about"])
        deals = active_deals(show, TODAY)[:2]
        if deals:
            st.success("\n\n".join(f"🏷️ **{d.get('label', 'Deal')}:** {d['text']}. **Ends {fmt_day(d['ends'])}.** [Details]({d['source']})"
                                     for d in deals))
        st.write(("**Why it's here:** " if p.get("featured") else "") + p["why_it_fits"])
        if p.get("caution"):
            st.write(f"**Heads up:** {p['caution']}")
        st.write(f"**Price:** {p['price_range']}")
        if p.get("performances"):
            st.write(f"**{fmt_day(p['date'])}:** " + " & ".join(fmt_time(t) for t in p["performances"]))
        if p["rush_or_lottery"]:
            st.write("🎟️ Rush or lottery tickets are often available. Check the official show site.")
        if p.get("official_url"):
            st.link_button("Get tickets on the official site ↗", p["official_url"])


clicked = st.button("Find my shows", type="primary")
if not clicked:
    # Before anyone asks: this week's best seller, the newest show and the best deal (no Claude call, no cost).
    picks = featured_picks(list(CATALOG.values()), load_featured(), TODAY, exclude=seen)
    if picks:
        st.markdown("#### Popular right now  \n:gray[Not personalized yet. Describe your night and click **Find my shows** for picks made for you.]")
        if not st.session_state.get("featured_sent"):
            st.session_state.featured_sent = True
            track(st.session_state.visitor, "featured_shown", picks=[p["title"] for p in picks], kinds=[p["featured"] for p in picks])
        cols = st.columns(len(picks))
        for i, (col, p) in enumerate(zip(cols, picks), 1):
            show = CATALOG.get(p["title"], {})
            with col, st.container(border=True):
                st.caption(f"**{p['featured_label'].upper()}**")
                st.markdown(f"**{p['title']}**")
                deal = (active_deals(show, TODAY) or [None])[0]
                deal_price = deal.get("from_price") if deal and deal.get("from_price") and deal["from_price"] < show.get("price_low", 0) else None
                st.markdown(f":red[**From ${deal_price} with deal**]" if deal_price else f":red[**${show.get('price_low')} to ${show.get('price_high')}**]")
                if show.get("about"):
                    st.caption(show["about"])
                if deal:
                    st.markdown(f":green-background[🏷️ Deal · ends {fmt_day(deal['ends'])}]")
                with st.expander("Details"):
                    st.write(p["why_it_fits"])
                    st.write(f"**Price:** {p['price_range']}")
                    if deal:
                        st.write(f"**{deal.get('label', 'Deal')}:** {deal['text']}. [Details]({deal['source']})")
                    if p.get("official_url"):
                        st.link_button("Official site ↗", p["official_url"])

if clicked:
    if not text.strip():
        st.warning("Write a sentence or two about your night first.")
        track(st.session_state.visitor, "find_clicked_empty")
        st.stop()
    allowed, wait, reason = rate_limiter().check(visitor_key())
    if not allowed:
        minutes = max(1, round(wait / 60))
        if reason == "global":
            st.warning(f"Broadway Concierge is busy right now. Please try again in about {minutes} min.")
        else:
            st.warning(f"You've asked for a lot of picks in a short time. Please try again in about {minutes} min.")
        track(st.session_state.visitor, "rate_limited", reason=reason, wait_seconds=wait)
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
                date=go_date.isoformat() if go_date else None,
                time_of_day=time_of_day.lower() if go_date and time_of_day != "Any time" else None,
                exclude=seen,
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
        who=who, mood=mood, show_type=show_type, date_set=bool(go_date), seen_count=len(seen),
        days_ahead=(go_date - dt.date.today()).days if go_date else None, max_price=max_price if max_price is not None else "any",
        dealbreakers=list(dealbreakers), first_show=first_show,
        has_kids_ages=bool(kids_ages.strip()), text_length=len(text.strip()),
        picks=[p["title"] for p in result["picks"]],
        near_misses=sum(1 for p in result["picks"] if not p["fits_all_limits"]),
        seconds_to_first_picks=round(time.time() - st.session_state.started, 1) if first else None,
    )

    if result["message"]:
        st.info(result["message"])
    for i, p in enumerate(result["picks"], 1):
        show_card(i, p)
    if result["assumptions"]:
        st.caption(f"Assumptions we made: {result['assumptions']}")
    st.caption("Prices are typical ranges from a hand-built catalog, not live. Always confirm on the official ticket seller.")
