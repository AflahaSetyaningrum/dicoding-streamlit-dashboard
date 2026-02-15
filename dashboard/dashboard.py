import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="E-Commerce Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# LOAD DATA
# ============================================================================
@st.cache_data
def load_data():
    """Load all required datasets"""
    try:
        # Load raw data
        orders = pd.read_csv('data/olist_orders_dataset.csv')
        order_items = pd.read_csv('data/olist_order_items_dataset.csv')
        products = pd.read_csv('data/olist_products_dataset.csv')
        customers = pd.read_csv('data/olist_customers_dataset.csv')
        product_cat = pd.read_csv('data/product_category_name_translation.csv')
        
        # Merge datasets
        merged_df = orders.merge(order_items, on='order_id') \
            .merge(products, on='product_id') \
            .merge(customers, on='customer_id') \
            .merge(product_cat, on='product_category_name', how='left')
        
        # Parse datetime
        merged_df['order_purchase_timestamp'] = pd.to_datetime(merged_df['order_purchase_timestamp'])
        merged_df['order_month'] = merged_df['order_purchase_timestamp'].dt.to_period('M')
        
        # Calculate revenue
        merged_df['revenue'] = merged_df['price'] + merged_df['freight_value']
        
        # Clean category names
        merged_df['product_category_name_english'] = merged_df['product_category_name_english'].fillna('Unknown')
        
        return merged_df
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# ============================================================================
# CALCULATE RFM METRICS
# ============================================================================
@st.cache_data
def calculate_rfm(merged_df):
    """Calculate RFM segments"""
    snapshot_date = merged_df['order_purchase_timestamp'].max() + timedelta(days=1)
    
    rfm = merged_df.groupby('customer_id').agg({
        'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
        'order_id': 'nunique',
        'revenue': 'sum'
    }).reset_index()
    
    rfm.columns = ['customer_id', 'Recency', 'Frequency', 'Monetary']
    
    # Calculate RFM scores
    rfm['R_score'] = pd.qcut(rfm['Recency'].rank(method='first'), 4, labels=[4, 3, 2, 1], duplicates='drop')
    rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4], duplicates='drop')
    rfm['M_score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 4, labels=[1, 2, 3, 4], duplicates='drop')
    
    rfm['R_score'] = rfm['R_score'].astype(int)
    rfm['F_score'] = rfm['F_score'].astype(int)
    rfm['M_score'] = rfm['M_score'].astype(int)
    
    # Define segments
    def segment_customer(row):
        if row['R_score'] >= 3 and row['F_score'] >= 3 and row['M_score'] >= 3:
            return 'Champions'
        elif row['R_score'] >= 3 and row['F_score'] >= 2:
            return 'Loyal'
        elif row['R_score'] <= 2 and row['M_score'] >= 3:
            return 'At Risk'
        else:
            return 'Potential'
    
    rfm['segment'] = rfm.apply(segment_customer, axis=1)
    return rfm

# ============================================================================
# LOAD DATA
# ============================================================================
merged_df = load_data()

if merged_df is None:
    st.error("Failed to load data. Please ensure all CSV files are in the 'data' folder.")
    st.stop()

rfm = calculate_rfm(merged_df)
merged_df = merged_df.merge(rfm[['customer_id', 'segment']], on='customer_id', how='left')

# ============================================================================
# CUSTOM STYLING
# ============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .subheader {
        font-size: 1.5rem;
        color: #1f77b4;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================
st.markdown("""
<div class="main-header">
    📊 E-Commerce Interactive Dashboard
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.write("Dashboard ini menampilkan analisis interaktif dari E-Commerce dataset dengan fitur filtering real-time.")

# ============================================================================
# SIDEBAR - INTERACTIVE FILTERS
# ============================================================================
# Display logo at the top of sidebar
try:
    logo = Image.open('dashboard/logo1.png')
    with st.sidebar:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, width=180)
        st.markdown("<hr style='margin: 2px 0px; padding: 0px;'>", unsafe_allow_html=True)
except:
    st.sidebar.warning("⚠️ Logo tidak ditemukan. Pastikan 'dashboard/logo1.png' ada di folder.")
    st.markdown("<hr style='margin: 2px 0px; padding: 0px;'>", unsafe_allow_html=True)

# FILTER 1: Date Range (REQUIRED)
st.sidebar.markdown("### 📅 Filter 1: Rentang Tanggal")
min_date = merged_df['order_purchase_timestamp'].min()
max_date = merged_df['order_purchase_timestamp'].max()

date_range = st.sidebar.date_input(
    "Pilih rentang tanggal:",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date,
    help="Geser untuk memilih rentang tanggal analisis"
)

if len(date_range) == 2:
    start_date, end_date = date_range
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date) + timedelta(days=1)
else:
    start_date = min_date
    end_date = max_date

# FILTER 2: Product Category
st.sidebar.markdown("### 🏷️ Filter 2: Kategori Produk")
categories = ['Semua Kategori'] + sorted(merged_df['product_category_name_english'].unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Pilih kategori produk:",
    options=categories,
    default=['Semua Kategori'],
    help="Pilih satu atau lebih kategori untuk filter"
)

# FILTER 3: Geographic (State)
st.sidebar.markdown("### 🌍 Filter 3: Wilayah Geografis")
states = ['Semua Wilayah'] + sorted(merged_df['customer_state'].unique().tolist())
selected_states = st.sidebar.multiselect(
    "Pilih wilayah (state):",
    options=states,
    default=['Semua Wilayah'],
    help="Pilih satu atau lebih wilayah untuk filter"
)

# FILTER 4: Customer Segment (RFM)
st.sidebar.markdown("### 👥 Filter 4: Segmen Pelanggan (RFM)")
segments = ['Semua Segmen'] + sorted(merged_df['segment'].unique().tolist())
selected_segments = st.sidebar.multiselect(
    "Pilih segmen pelanggan:",
    options=segments,
    default=['Semua Segmen'],
    help="Champions, Loyal, At Risk, Potential"
)

st.sidebar.markdown("---")
st.sidebar.info("ℹ️ Semua filter di atas mempengaruhi visualisasi dashboard secara real-time")

# ============================================================================
# APPLY FILTERS TO DATA
# ============================================================================
# Create filter logic
filtered_df = merged_df.copy()

# Date filter
filtered_df = filtered_df[(filtered_df['order_purchase_timestamp'] >= start_date) & 
                          (filtered_df['order_purchase_timestamp'] < end_date)]

# Category filter
if 'Semua Kategori' not in selected_categories:
    filtered_df = filtered_df[filtered_df['product_category_name_english'].isin(selected_categories)]

# State filter
if 'Semua Wilayah' not in selected_states:
    filtered_df = filtered_df[filtered_df['customer_state'].isin(selected_states)]

# Segment filter
if 'Semua Segmen' not in selected_segments:
    filtered_df = filtered_df[filtered_df['segment'].isin(selected_segments)]

# ============================================================================
# DISPLAY FILTER STATUS & KPI CARDS
# ============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📦 Total Transaksi",
        f"{filtered_df['order_id'].nunique():,}",
        f"{filtered_df['order_id'].nunique() / merged_df['order_id'].nunique() * 100:.1f}% dari total"
    )

with col2:
    st.metric(
        "👥 Pelanggan Unik",
        f"{filtered_df['customer_id'].nunique():,}",
        f"{filtered_df['customer_id'].nunique() / merged_df['customer_id'].nunique() * 100:.1f}% dari total"
    )

with col3:
    total_revenue = filtered_df['revenue'].sum()
    st.metric(
        "💰 Total Revenue",
        f"Rp {total_revenue/1e9:.2f}B",
        f"{total_revenue / merged_df['revenue'].sum() * 100:.1f}% dari total"
    )

with col4:
    avg_revenue = filtered_df['revenue'].mean()
    st.metric(
        "📊 Rata-rata Revenue/Transaksi",
        f"Rp {avg_revenue/1000:.0f}K",
        f"dari Rp {merged_df['revenue'].mean()/1000:.0f}K (total)"
    )

st.markdown("---")

# ============================================================================
# VISUALIZATION 1: MONTHLY TREND (AFFECTED BY FILTERS)
# ============================================================================
st.markdown("<div class='subheader'>📈 Tren Bulanan Transaksi & Revenue</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    monthly_data = filtered_df.groupby(filtered_df['order_purchase_timestamp'].dt.to_period('M')).agg({
        'order_id': 'nunique',
        'revenue': 'sum'
    }).reset_index()
    monthly_data.columns = ['month', 'transaction_count', 'revenue']
    monthly_data['month'] = monthly_data['month'].astype(str)
    
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(range(len(monthly_data)), monthly_data['transaction_count'], color='#06A77D', alpha=0.8, edgecolor='black')
    ax1.set_xticks(range(len(monthly_data)))
    ax1.set_xticklabels(monthly_data['month'], rotation=45)
    ax1.set_title(f"Transaksi Bulanan (Terfilter)\nTotal: {monthly_data['transaction_count'].sum():,} transaksi", 
                  fontsize=12, fontweight='bold')
    ax1.set_ylabel('Jumlah Transaksi', fontsize=11)
    ax1.set_xlabel('Bulan', fontsize=11)
    ax1.grid(True, alpha=0.2, axis='y')
    plt.tight_layout()
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.bar(range(len(monthly_data)), monthly_data['revenue']/1e9, color='#D62828', alpha=0.8, edgecolor='black')
    ax2.set_xticks(range(len(monthly_data)))
    ax2.set_xticklabels(monthly_data['month'], rotation=45)
    ax2.set_title(f"Revenue Bulanan (Terfilter)\nTotal: Rp {monthly_data['revenue'].sum()/1e9:.2f}B", 
                  fontsize=12, fontweight='bold')
    ax2.set_ylabel('Revenue (Rp Miliar)', fontsize=11)
    ax2.set_xlabel('Bulan', fontsize=11)
    ax2.grid(True, alpha=0.2, axis='y')
    plt.tight_layout()
    st.pyplot(fig2)

st.info("✨ **Fitur Interaktif**: Ubah filter di sidebar untuk melihat perubahan grafik tren bulanan secara real-time")

# ============================================================================
# VISUALIZATION 2: TOP CATEGORIES (AFFECTED BY FILTERS)
# ============================================================================
st.markdown("<div class='subheader'>🏆 Top 10 Kategori Produk</div>", unsafe_allow_html=True)

category_data = filtered_df.groupby('product_category_name_english').agg({
    'order_id': 'nunique',
    'revenue': 'sum'
}).reset_index().sort_values('revenue', ascending=False).head(10)

col1, col2 = st.columns(2)

with col1:
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.barh(range(len(category_data)), category_data['order_id'], color='#06A77D', alpha=0.8, edgecolor='black')
    ax3.set_yticks(range(len(category_data)))
    ax3.set_yticklabels(category_data['product_category_name_english'], fontsize=10)
    ax3.set_title(f"Top 10 Kategori by Volume\nTotal: {category_data['order_id'].sum():,} orders", 
                  fontsize=12, fontweight='bold')
    ax3.set_xlabel('Jumlah Order', fontsize=11)
    ax3.invert_yaxis()
    ax3.grid(True, alpha=0.2, axis='x')
    plt.tight_layout()
    st.pyplot(fig3)

with col2:
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    ax4.barh(range(len(category_data)), category_data['revenue']/1e9, color='#D62828', alpha=0.8, edgecolor='black')
    ax4.set_yticks(range(len(category_data)))
    ax4.set_yticklabels(category_data['product_category_name_english'], fontsize=10)
    ax4.set_title(f"Top 10 Kategori by Revenue\nTotal: Rp {category_data['revenue'].sum()/1e9:.2f}B", 
                  fontsize=12, fontweight='bold')
    ax4.set_xlabel('Revenue (Rp Miliar)', fontsize=11)
    ax4.invert_yaxis()
    ax4.grid(True, alpha=0.2, axis='x')
    plt.tight_layout()
    st.pyplot(fig4)

st.info("✨ **Fitur Interaktif**: Filter kategori/tanggal akan mengupdate grafik kategori produk")

# ============================================================================
# VISUALIZATION 3: CUSTOMER SEGMENT DISTRIBUTION (AFFECTED BY FILTERS)
# ============================================================================
st.markdown("<div class='subheader'>👥 Distribusi Segmen Pelanggan (RFM)</div>", unsafe_allow_html=True)

segment_data = filtered_df.groupby('segment').agg({
    'customer_id': 'nunique',
    'revenue': 'sum'
}).reset_index()

col1, col2 = st.columns(2)

with col1:
    segment_colors = {
        'Champions': '#FF0000',
        'Loyal': '#4ECDC4',
        'At Risk': '#FF6B6B',
        'Potential': '#45B7D1'
    }
    colors = [segment_colors.get(seg, '#999999') for seg in segment_data['segment']]
    
    fig5, ax5 = plt.subplots(figsize=(10, 6))
    wedges, texts, autotexts = ax5.pie(segment_data['customer_id'], labels=segment_data['segment'], 
                                         autopct='%1.1f%%', colors=colors, startangle=90)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)
    ax5.set_title(f"Distribusi Pelanggan by Segment\nTotal: {segment_data['customer_id'].sum():,} pelanggan", 
                  fontsize=12, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig5)

with col2:
    fig6, ax6 = plt.subplots(figsize=(10, 6))
    ax6.bar(segment_data['segment'], segment_data['revenue']/1e9, color=colors, alpha=0.8, edgecolor='black')
    ax6.set_title(f"Revenue Contribution by Segment\nTotal: Rp {segment_data['revenue'].sum()/1e9:.2f}B", 
                  fontsize=12, fontweight='bold')
    ax6.set_ylabel('Revenue (Rp Miliar)', fontsize=11)
    ax6.tick_params(axis='x', rotation=45)
    ax6.grid(True, alpha=0.2, axis='y')
    plt.tight_layout()
    st.pyplot(fig6)

st.info("✨ **Fitur Interaktif**: Filter segmen pelanggan akan mengupdate pie chart dan bar chart revenue")

# ============================================================================
# VISUALIZATION 4: GEOGRAPHIC DISTRIBUTION (AFFECTED BY FILTERS)
# ============================================================================
st.markdown("<div class='subheader'>🌍 Distribusi Geografis (Top 15 States)</div>", unsafe_allow_html=True)

geo_data = filtered_df.groupby('customer_state').agg({
    'customer_id': 'nunique',
    'revenue': 'sum'
}).reset_index().sort_values('revenue', ascending=False).head(15)

col1, col2 = st.columns(2)

with col1:
    fig7, ax7 = plt.subplots(figsize=(10, 8))
    ax7.barh(range(len(geo_data)), geo_data['revenue']/1e9, color='#D62828', alpha=0.8, edgecolor='black')
    ax7.set_yticks(range(len(geo_data)))
    ax7.set_yticklabels(geo_data['customer_state'], fontsize=10)
    ax7.set_title(f"Top 15 States by Revenue\nTotal: Rp {geo_data['revenue'].sum()/1e9:.2f}B", 
                  fontsize=12, fontweight='bold')
    ax7.set_xlabel('Revenue (Rp Miliar)', fontsize=11)
    ax7.invert_yaxis()
    ax7.grid(True, alpha=0.2, axis='x')
    plt.tight_layout()
    st.pyplot(fig7)

with col2:
    fig8, ax8 = plt.subplots(figsize=(10, 8))
    revenue_per_cust = geo_data['revenue'] / geo_data['customer_id']
    avg_efficiency = revenue_per_cust.mean()
    colors_geo = ['#FFD700' if x > avg_efficiency * 1.1 else '#FFA07A' for x in revenue_per_cust]
    
    ax8.barh(range(len(geo_data)), revenue_per_cust/1000, color=colors_geo, alpha=0.8, edgecolor='black')
    ax8.set_yticks(range(len(geo_data)))
    ax8.set_yticklabels(geo_data['customer_state'], fontsize=10)
    ax8.set_title(f"Revenue per Customer by State\nAvg: Rp {avg_efficiency/1000:.0f}K", 
                  fontsize=12, fontweight='bold')
    ax8.set_xlabel('Revenue per Customer (Rp Ribu)', fontsize=11)
    ax8.invert_yaxis()
    ax8.axvline(x=avg_efficiency/1000, color='red', linestyle='--', alpha=0.5, linewidth=2)
    ax8.grid(True, alpha=0.2, axis='x')
    plt.tight_layout()
    st.pyplot(fig8)

st.info("✨ **Fitur Interaktif**: Filter wilayah akan mengupdate grafik geografis secara real-time")

# ============================================================================
# DATA TABLE - FILTERED DATA INSPECTION
# ============================================================================
st.markdown("<div class='subheader'>📋 Data Terfilter (Preview)</div>", unsafe_allow_html=True)

with st.expander("Klik untuk melihat data terfilter"):
    display_cols = ['order_id', 'customer_id', 'product_category_name_english', 
                    'customer_state', 'segment', 'revenue', 'order_purchase_timestamp']
    display_df = filtered_df[display_cols].head(100)
    st.dataframe(display_df, use_container_width=True, height=400)

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
st.markdown("---")
st.markdown("<div class='subheader'>📊 Ringkasan Statistik</div>", unsafe_allow_html=True)

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    st.write("**Perbandingan Filter dengan Total Dataset:**")
    comparison_data = {
        'Metrik': ['Transaksi', 'Pelanggan', 'Revenue (Rp)'],
        'Terfilter': [
            filtered_df['order_id'].nunique(),
            filtered_df['customer_id'].nunique(),
            filtered_df['revenue'].sum()
        ],
        'Total': [
            merged_df['order_id'].nunique(),
            merged_df['customer_id'].nunique(),
            merged_df['revenue'].sum()
        ]
    }
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df['% dari Total'] = [
        f"{filtered_df['order_id'].nunique() / merged_df['order_id'].nunique() * 100:.1f}%",
        f"{filtered_df['customer_id'].nunique() / merged_df['customer_id'].nunique() * 100:.1f}%",
        f"{filtered_df['revenue'].sum() / merged_df['revenue'].sum() * 100:.1f}%"
    ]
    st.dataframe(comparison_df, use_container_width=True)

with summary_col2:
    st.write("**Filter yang Aktif:**")
    active_filters = []
    if 'Semua Kategori' not in selected_categories:
        active_filters.append(f"✓ Kategori: {len(selected_categories)} kategori dipilih")
    if 'Semua Wilayah' not in selected_states:
        active_filters.append(f"✓ Wilayah: {len(selected_states)} wilayah dipilih")
    if 'Semua Segmen' not in selected_segments:
        active_filters.append(f"✓ Segmen: {len(selected_segments)} segmen dipilih")
    active_filters.append(f"✓ Tanggal: {start_date.date()} s/d {(end_date - timedelta(days=1)).date()}")
    
    for filter_info in active_filters:
        st.write(filter_info)

with summary_col3:
    st.write("**Periode Analisis:**")
    st.write(f"📅 Mulai: {start_date.date()}")
    st.write(f"📅 Selesai: {(end_date - timedelta(days=1)).date()}")
    st.write(f"📊 Durasi: {(end_date - start_date).days} hari")

st.markdown("---")
