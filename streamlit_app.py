import streamlit as st
import pandas as pd
import altair as alt

# Load and clean data
df = pd.read_csv("listings.csv")

# Clean and preprocess
df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)
df['id'] = df['id'].astype(str)
df['host_is_superhost'] = df['host_is_superhost'].map({'t': 'Yes', 'f': 'No'})

# Drop essential missing values
df.dropna(subset=['price', 'room_type', 'host_neighbourhood', 'host_is_superhost'], inplace=True)

# Define review score columns
review_columns = [
    'review_scores_rating', 'review_scores_accuracy', 'review_scores_cleanliness',
    'review_scores_checkin', 'review_scores_communication', 'review_scores_location'
]
df.dropna(subset=review_columns, inplace=True)
df['avg_review_score'] = df[review_columns].mean(axis=1)

# Clean tooltip-related columns
tooltip_columns = ['picture_url', 'host_url', 'host_response_rate']
df.dropna(subset=tooltip_columns, inplace=True)

# --------------------------
# SIDEBAR FILTERS: Step 1
# --------------------------
st.sidebar.header("Step 1: Filter by Price and Superhost")

price_min, price_max = int(df['price'].min()), int(df['price'].max())
selected_price = st.sidebar.slider(
    "Select Price Range", min_value=price_min, max_value=price_max, value=(price_min, price_max)
)
selected_superhost = st.sidebar.selectbox("Is Superhost?", options=['Yes', 'No'])

# Filter dataset based on Step 1
base_df = df[
    (df['price'] >= selected_price[0]) &
    (df['price'] <= selected_price[1]) &
    (df['host_is_superhost'] == selected_superhost)
]

# --------------------------
# PAGE TITLE
# --------------------------
st.title("Airbnb Searching Dashboard")
st.markdown("""
Welcome! Let's help you search Airbnb listings based on you preference on price, room type, neighborhood, and review scores.
Let's start by filtering the price and superhost status on the left!
""")

# --------------------------
# CHART 1: Boxplot + Avg Price Bar Chart
# --------------------------
if not base_df.empty:
    st.subheader("Price Distribution by Room Type")

    boxplot_room = alt.Chart(base_df).mark_boxplot().encode(
        x=alt.X('room_type:N', title='Room Type'),
        y=alt.Y('price:Q', title='Price'),
        color=alt.Color('room_type:N', legend=None)
    ).properties(
        width=700,
        height=400,
        title='Boxplot of Price by Room Type'
    )
    st.altair_chart(boxplot_room, use_container_width=True)

    st.subheader("Average Price by Neighborhood")

    neighborhood_avg = (
        base_df.groupby('neighbourhood_cleansed', as_index=False)['price']
        .mean()
        .sort_values('price', ascending=False)
    )

    bar_avg_price = alt.Chart(neighborhood_avg).mark_bar().encode(
        x=alt.X('price:Q', title='Average Price'),
        y=alt.Y('neighbourhood_cleansed:N', sort='-x', title='Neighborhood'),
        tooltip=['neighbourhood_cleansed:N', 'price:Q'],
        color=alt.Color('price:Q', scale=alt.Scale(scheme='blues'))
    ).properties(
        width=700,
        title='Average Price by Neighbourhood (Filtered)'
    )
    st.altair_chart(bar_avg_price, use_container_width=True)

    # --------------------------
    # SIDEBAR FILTERS: Step 2
    # --------------------------
    st.sidebar.header("Step 2: Choose Room Type and Neighborhood")
    available_rooms = sorted(base_df['room_type'].unique().tolist())
    selected_room = st.sidebar.selectbox("Select Room Type", options=available_rooms)

    available_neighborhoods = sorted(base_df['neighbourhood_cleansed'].unique().tolist())
    selected_neighborhood = st.sidebar.selectbox("Select Neighborhood", options=available_neighborhoods)

    filtered_df = base_df[
        (base_df['room_type'] == selected_room) &
        (base_df['neighbourhood_cleansed'] == selected_neighborhood)
    ]

    # --------------------------
    # CHART 2: Price vs Avg Review Score
    # --------------------------
    if not filtered_df.empty:
        st.subheader("Price vs. Average Review Score")

        scatter_score = alt.Chart(filtered_df).mark_circle(size=60).encode(
            x=alt.X('price:Q', title='Price'),
            y=alt.Y('avg_review_score:Q', title='Average Review Score'),
            tooltip=[
                alt.Tooltip('id:N', title='Listing ID'),
                alt.Tooltip('picture_url:N', title='Picture URL'),
                alt.Tooltip('host_url:N', title='Host URL'),
                alt.Tooltip('host_response_rate:N', title='Host Response Rate')
            ],
            href='picture_url:N'
        ).properties(
            width=700,
            height=400,
            title=f'Price vs. Review Score in {selected_neighborhood} ({selected_room})'
        ).interactive()

        st.altair_chart(scatter_score, use_container_width=True)

        # --------------------------
        # Step 3: Select ID → Review + Host Info
        # --------------------------
        st.sidebar.header("Step 3: Choose a Listing to Explore")
        available_ids = filtered_df['id'].unique().tolist()
        selected_id = st.sidebar.selectbox("Select Listing ID", options=available_ids)

        selected_row = filtered_df[filtered_df['id'] == selected_id].iloc[0]

        # Review score breakdown chart
        review_scores = pd.DataFrame({
            'Category': ['Rating', 'Accuracy', 'Cleanliness', 'Check-in', 'Communication', 'Location'],
            'Score': [
                selected_row['review_scores_rating'],
                selected_row['review_scores_accuracy'],
                selected_row['review_scores_cleanliness'],
                selected_row['review_scores_checkin'],
                selected_row['review_scores_communication'],
                selected_row['review_scores_location']
            ]
        })

        st.subheader(f"Review Breakdown for Listing ID {selected_id}")
        review_bar = alt.Chart(review_scores).mark_bar().encode(
            x=alt.X('Category:N', title='Review Category'),
            y=alt.Y('Score:Q', title='Score'),
            tooltip=['Score']
        ).properties(
            width=600,
            height=300
        )
        st.altair_chart(review_bar, use_container_width=True)

        # Host Info
        st.subheader(f"Host Information:{selected_id}")
        host_fields = ['host_name', 'host_response_rate', 'host_acceptance_rate']
        for field in host_fields:
            value = selected_row.get(field, 'Not Available')
            st.write(f"**{field.replace('_', ' ').title()}:** {value}")
    else:
        st.warning("No listings match your selected room type and neighborhood.")
else:
    st.warning("No listings match your price and superhost filter.")
