"""Broadway Concierge - show recommender web page. Run with: streamlit run streamlit_app.py"""
import streamlit as st

from app import DEALBREAKERS, LONG_RUNTIME_MIN, recommend_shows

st.set_page_config(page_title="Broadway Concierge", page_icon="🎭")

st.title("🎭 Broadway Concierge")
st.write("Tell us about your night and get 3 Broadway shows that fit your group, mood and budget.")

text = st.text_area(
    "Tell us about your night",
    placeholder="Taking my mom for her birthday. We loved Wicked, I hate jukebox musicals, and we want to laugh.",
    height=120,
)

st.caption("Optional: the more you tell us, the better the picks.")
col1, col2 = st.columns(2)
with col1:
    who = st.selectbox("Who's going?", ["(not sure)", "solo", "date", "friends", "family"])
    kids_ages = ""
    if who == "family":
        kids_ages = st.text_input("Kids' ages (if any)", placeholder="e.g. 6, 10")
    mood = st.selectbox("Mood", ["(any)", "laugh", "cry", "be wowed", "sing along", "something different"])
    first_show = st.radio("First Broadway show?", ["Not said", "Yes", "No"], horizontal=True)
with col2:
    no_limit = st.checkbox("No budget limit", value=False)
    max_price = None if no_limit else st.slider("Max price per ticket ($)", 40, 400, 150, step=10)
    dealbreakers = st.multiselect(
        "Dealbreakers",
        DEALBREAKERS,
        help=(f"'long runtime' means {LONG_RUNTIME_MIN // 60}h{LONG_RUNTIME_MIN % 60}m or more. "
              "'no intermission' means you only want shows that run straight through."),
    )

if st.button("Find my shows", type="primary"):
    if not text.strip():
        st.warning("Write a sentence or two about your night first.")
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
            )
        except RuntimeError as e:  # missing API key
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Something went wrong talking to the AI: {e}")
            st.stop()

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
