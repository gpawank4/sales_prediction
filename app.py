import streamlit as st
import pandas as pd
import plotly.express as px

# =============================================================================
# Data Loading and Preprocessing Functions
# =============================================================================

@st.cache_data
def load_data(file_path):
    """
    Loads Excel data and converts date columns (if present) to datetime.
    Adjust the column names ('Date' or 'Order Date') as per your file.
    """
    df = pd.read_excel(file_path)
    
    # Format the date column if exists
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    return df

def clean_data(df):
    """
    Cleans the data:
      - Replaces empty (NaN) sales values with 0.
      - Removes rows where sales are negative.
    Assumes the sales column is named 'Sales'.
    """
    if 'Sales' in df.columns:
        # Replace empty values with 0
        df['Sales'] = df['Sales'].fillna(0)
        # Delete rows with negative sales
        df = df[df['Sales'] >= 0]
    return df

def add_aggregated_features(df):
    """
    Adds aggregate features:
      - Computes average sales and total sales per Country and Segment.
      - Calculates sales_ratio (row's sales divided by total sales in its group).
    Assumes columns 'Country', 'Segment', and 'Sales' are present.
    """
    group_df = df.groupby(['Country', 'Segment'])['Sales'].agg(['mean', 'sum']).reset_index()
    group_df.rename(columns={'mean': 'avg_sales_by_group', 'sum': 'total_sales_by_group'}, inplace=True)
    
    # Merge the aggregated values back into the original DataFrame
    df = pd.merge(df, group_df, on=['Country', 'Segment'], how='left')
    
    # Compute sales ratio for each row (avoid division by zero)
    df['sales_ratio'] = df.apply(
        lambda row: row['Sales'] / row['total_sales_by_group'] if row['total_sales_by_group'] != 0 else 0, 
        axis=1
    )
    return df

# =============================================================================
# Main Dashboard Function
# =============================================================================

def main():
    st.title("Sales Data Visualization Dashboard")
    st.subheader("Internship Assessment for Smith+Nephew by G Pawan Kumar Reddy, VIT")
    
    # -----------------------------------------------------------------------------
    # Floating Help Icon (using custom HTML and CSS)
    # -----------------------------------------------------------------------------
    st.markdown("""
        <style>
        .floating-icon {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            background-color: #007BFF;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 50px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.3);
            z-index: 1000;
        }
        .floating-icon:hover .tooltip {
            visibility: visible;
            opacity: 1;
        }
        .tooltip {
            visibility: hidden;
            width: 220px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px 0;
            position: absolute;
            z-index: 1;
            bottom: 70px;
            right: 0;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 18px;
        }
        </style>
        <div class="floating-icon">
            ?
            <div class="tooltip">This dashboard is made towards the completion of Internship Assessment for Smith+Nephew by G Pawan Kumar Reddy, VIT</div>
        </div>
    """, unsafe_allow_html=True)
    
    # -----------------------------------------------------------------------------
    # Data Loading, Cleaning & Feature Engineering
    # -----------------------------------------------------------------------------

    # Replace with your GitHub raw URL
    github_url = "https://raw.githubusercontent.com/gpawank4/sales_prediction/main/data.xlsx"

    try:
        response = requests.get(github_url)
        response.raise_for_status()  # Raise an exception for bad status codes

        data = pd.read_excel(io.StringIO(response.text))

    except requests.exceptions.RequestException as e:
        st.error(f"Error loading data: {e}")
    
    data = clean_data(data)
    data = add_aggregated_features(data)
    
    st.markdown("## Data Preview")
    st.dataframe(data.head())
    
    st.markdown("## Aggregated Metrics by Country and Segment")
    agg_data = data.groupby(['Country', 'Segment'])[['Sales', 'avg_sales_by_group', 'total_sales_by_group']].first().reset_index()
    st.dataframe(agg_data)
    
    # =============================================================================
    # Visualizations Section
    # =============================================================================
    st.markdown("## Visualizations")
    
    # 1. Scatter Plot between Two Numeric Columns
    st.markdown("### Scatter Plot between Two Numeric Columns")
    numeric_columns = data.select_dtypes(include=['int64', 'float64']).columns.tolist()
    if len(numeric_columns) >= 2:
        col_x = st.selectbox("Select X-axis", options=numeric_columns, key="scatter_x")
        col_y_options = [col for col in numeric_columns if col != col_x]
        col_y = st.selectbox("Select Y-axis", options=col_y_options, key="scatter_y")
        scatter_fig = px.scatter(
            data, x=col_x, y=col_y, 
            title=f"Scatter Plot: {col_x} vs {col_y}",
            hover_data=["Country", "Segment"]
        )
        st.plotly_chart(scatter_fig)
        st.markdown("""
            **Chart Explanation:**  
            This scatter plot shows the relationship between two numeric variables.  
            * Dropdowns can be used to select different variables for the X and Y axes.  
            * Hover over the data points to see detailed information including the Country and Segment.
        """)
    else:
        st.warning("Not enough numeric columns available for scatter plots.")
    
    # 2. Total Sales by Country (Bar Chart)
    st.markdown("### Total Sales by Country")
    sales_by_country = data.groupby("Country")["Sales"].sum().reset_index().sort_values(by="Sales", ascending=False)
    fig_country = px.bar(sales_by_country, x="Country", y="Sales", title="Total Sales by Country")
    st.plotly_chart(fig_country)
    st.markdown("""
        **Chart Explanation:**  
        This bar chart displays the total sales aggregated by Country.  
        * Hover over each bar to see the exact sales figures.  
        * Use this to compare performance across different countries.
    """)
    
    # 3. Total Sales by Segment (Bar Chart)
    st.markdown("### Total Sales by Segment")
    sales_by_segment = data.groupby("Segment")["Sales"].sum().reset_index().sort_values(by="Sales", ascending=False)
    fig_segment = px.bar(sales_by_segment, x="Segment", y="Sales", title="Total Sales by Segment")
    st.plotly_chart(fig_segment)
    st.markdown("""
        **Chart Explanation:**  
        This chart aggregates total sales by Segment.  
        * Hover over bars to view the sales figures.  
        * This view helps you quickly identify which customer segment contributes most to the overall sales.
    """)
    
    # 4. Compare Average Sales and Sales Ratio
    st.markdown("### Average Sales vs. Sales Ratio")
    fig_avg_ratio = px.scatter(
        data, x="avg_sales_by_group", y="sales_ratio",
        color="Country", title="Average Sales vs. Sales Ratio by Country",
        hover_data=["Segment"]
    )
    st.plotly_chart(fig_avg_ratio)
    st.markdown("""
        **Chart Explanation:**  
        This scatter plot compares average sales per group with the sales ratio (the contribution of each sale to its group's total sales).  
        * The chart uses color to differentiate between countries.  
        * Hover on the points for detailed segment information.
    """)
    
    # 5. Explore Relationships Between Any Two Columns
    st.markdown("### Explore Relationships Between Columns")
    all_columns = data.columns.tolist()
    col_a = st.selectbox("Select column for X-axis", options=all_columns, key="col_a")
    col_b_options = [col for col in all_columns if col != col_a]
    col_b = st.selectbox("Select column for Y-axis", options=col_b_options, key="col_b")
    
    if pd.api.types.is_numeric_dtype(data[col_a]) and pd.api.types.is_numeric_dtype(data[col_b]):
        fig_relation = px.scatter(
            data, x=col_a, y=col_b,
            title=f"Scatter Plot: {col_a} vs {col_b}",
            hover_data=["Country", "Segment"]
        )
    else:
        count_data = data.groupby([col_a, col_b]).size().reset_index(name="Count")
        fig_relation = px.bar(
            count_data, x=col_a, y="Count", color=col_b,
            barmode="group", title=f"Bar Chart: {col_a} vs {col_b}"
        )
    st.plotly_chart(fig_relation)
    st.markdown("""
        **Chart Explanation:**  
        This interactive visualization lets you choose any two columns to explore their relationship.  
        * If both columns are numeric, a scatter plot is displayed.  
        * If one or both columns are categorical, a grouped bar chart is used instead.  
        * Use this chart to discover trends, correlations, or distribution patterns across different dimensions.
    """)

if __name__ == "__main__":
    main()
