"""
Streamlit app for visualizing CIS people data.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Page config
st.set_page_config(
    page_title="CIS People Directory",
    page_icon="👥",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    """Load people data from JSON file."""
    json_path = Path("people_data.json")
    csv_path = Path("people_data.csv")
    
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        st.error("No data file found. Please run scraper.py first.")
        st.stop()
        return None
    
    return df

# Main app
st.title("👥 CIS People Directory")
st.markdown("Browse and explore the School of Computing and Information Systems staff directory")

# Load data
df = load_data()

if df is not None and not df.empty:
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Category filter
    categories = ['All'] + sorted(df['category'].dropna().unique().tolist())
    selected_category = st.sidebar.selectbox("Category", categories)
    
    # Honorific filter
    honorifics = ['All'] + sorted([h for h in df['honorific'].dropna().unique().tolist() if h])
    selected_honorific = st.sidebar.selectbox("Honorific", honorifics)
    
    # Search
    search_term = st.sidebar.text_input("Search by name", "")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    if selected_honorific != 'All':
        filtered_df = filtered_df[filtered_df['honorific'] == selected_honorific]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_term, case=False, na=False)
        ]
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total People", len(filtered_df))
    
    with col2:
        st.metric("Categories", len(filtered_df['category'].unique()))
    
    with col3:
        st.metric("With Profile URLs", len(filtered_df[filtered_df['profile_url'] != 'N/A']))
    
    with col4:
        honorific_count = len(filtered_df[filtered_df['honorific'].notna() & (filtered_df['honorific'] != '')])
        st.metric("With Honorifics", honorific_count)
    
    # Charts
    st.header("📊 Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("People by Category")
        category_counts = filtered_df['category'].value_counts()
        st.bar_chart(category_counts)
    
    with col2:
        st.subheader("People by Honorific")
        honorific_counts = filtered_df['honorific'].value_counts()
        # Remove empty honorifics for cleaner chart
        honorific_counts = honorific_counts[honorific_counts.index != '']
        if not honorific_counts.empty:
            st.bar_chart(honorific_counts)
        else:
            st.info("No honorific data to display")
    
    # Data table
    st.header("📋 People List")
    
    # Format display name with honorific
    display_df = filtered_df.copy()
    display_df['display_name'] = display_df.apply(
        lambda row: f"{row['honorific']} {row['name']}".strip() if pd.notna(row['honorific']) and row['honorific'] else row['name'],
        axis=1
    )
    
    # Handle empty titles
    display_df['title'] = display_df['title'].fillna('N/A')
    display_df['title'] = display_df['title'].replace('', 'N/A')
    
    # Select columns to display
    columns_to_show = ['display_name', 'title', 'category', 'profile_url']
    display_df = display_df[columns_to_show].copy()
    display_df.columns = ['Name', 'Title', 'Category', 'Profile URL']
    
    # Format profile URLs for display
    def format_url(url):
        if url and url != 'N/A' and pd.notna(url):
            return f"🔗 [View Profile]({url})"
        return '—'
    
    display_df['Profile URL'] = display_df['Profile URL'].apply(format_url)
    
    # Display table using Streamlit's dataframe display
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Download button
    st.download_button(
        label="📥 Download filtered data as CSV",
        data=filtered_df.to_csv(index=False),
        file_name="cis_people_filtered.csv",
        mime="text/csv"
    )
    
else:
    st.warning("No data available. Please run scraper.py to generate the data files.")

