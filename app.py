import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

st.set_page_config(page_title="KG DEI", page_icon=":bar_chart:", layout="wide")

from streamlit_gsheets import GSheetsConnection

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

# Replace NaN values in the 'layer' column with "N-A" for display and filtering purposes
df['layer'] = df['layer'].fillna("N-A")

st.sidebar.header('KG DEI Dashboard')
st.sidebar.header('Metrics')

# Page selection with a blank option
pages = ['', 'Gender', 'Generation', 'Religion', 'Tenure', 'Region', 'Age']
selected_page = st.sidebar.selectbox("Choose the Metrics you want to display:", pages)

st.sidebar.header('Breakdown Variable')

# Add Breakdown Variable Selection
breakdown_options = ['unit', 'subunit', 'layer']
selected_breakdown = st.sidebar.selectbox("Breakdown Variable", breakdown_options)

# Sidebar Widgets
st.sidebar.header('Filters')

# Unit, Subunit, and Layer Filters using multiselect without "All" option
unit_options = df['unit'].unique().tolist()
subunit_options = df['subunit'].unique().tolist() if 'subunit' in df.columns else []
layer_options = df['layer'].unique().tolist() if 'layer' in df.columns else []

# Multiselect filters for Unit, Subunit, and Layer
selected_units = st.sidebar.multiselect("Select Unit(s)", unit_options)
selected_subunits = st.sidebar.multiselect("Select Subunit(s)", subunit_options)
selected_layers = st.sidebar.multiselect("Select Layer(s)", layer_options)

# Additional Filters for Gender, Generation, Religion, and Tenure
gender_options = df['gender'].unique().tolist() if 'gender' in df.columns else []
generation_options = df['generation'].unique().tolist() if 'generation' in df.columns else []
religion_options = df['Religious Denomination Key'].unique().tolist() if 'Religious Denomination Key' in df.columns else []
tenure_options = ['<1 Year', '1-3 Year', '4-6 Year', '6-10 Year', '11-15 Year', '16-20 Year', '20-25 Year', '>25 Year']

# Multiselect filters for Gender, Generation, Religion, and Tenure
selected_genders = st.sidebar.multiselect("Select Gender(s)", gender_options)
selected_generations = st.sidebar.multiselect("Select Generation(s)", generation_options)
selected_religions = st.sidebar.multiselect("Select Religion(s)", religion_options)
selected_tenures = st.sidebar.multiselect("Select Tenure(s)", tenure_options)

# Filter the data based on selected units, subunits, layers, and additional criteria
filtered_df = df.copy()

# Apply filters only if specific options are selected; otherwise, keep the full dataset
if selected_units:
    filtered_df = filtered_df[filtered_df['unit'].isin(selected_units)]

if selected_subunits and 'subunit' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['subunit'].isin(selected_subunits)]

# Adjust filter logic for 'layer' to include "N-A" option for missing data
if selected_layers and 'layer' in filtered_df.columns:
    if "N-A" in selected_layers:
        filtered_df = filtered_df[filtered_df['layer'].isin(selected_layers) | (filtered_df['layer'] == "N-A")]
    else:
        filtered_df = filtered_df[filtered_df['layer'].isin(selected_layers)]

# Filter for Gender, Generation, Religion, and Tenure
if selected_genders and 'gender' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['gender'].isin(selected_genders)]

if selected_generations and 'generation' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['generation'].isin(selected_generations)]

if selected_religions and 'Religious Denomination Key' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Religious Denomination Key'].isin(selected_religions)]

# For tenure, categorize 'Years' column and filter based on selected tenure groups
bins = [-1, 1, 3, 6, 10, 15, 20, 25, float('inf')]
labels = ['<1 Year', '1-3 Year', '4-6 Year', '6-10 Year', '11-15 Year', '16-20 Year', '20-25 Year', '>25 Year']
filtered_df['Service_Group'] = pd.cut(filtered_df['Years'], bins=bins, labels=labels, right=False)

if selected_tenures:
    filtered_df = filtered_df[filtered_df['Service_Group'].isin(selected_tenures)]

# Display total employee count
def display_total_employees_with_breakdown():
    total_employees = len(filtered_df)
    st.title("Total Employees")
    st.subheader(f"{total_employees:,}")
    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)
    
    # Group by the selected breakdown and count employees
    breakdown_counts = (
        filtered_df.groupby(selected_breakdown)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    breakdown_counts.rename(columns={selected_breakdown: selected_breakdown.capitalize()}, inplace=True)
    
    # Convert the Count column to integer for clean display
    breakdown_counts["Count"] = breakdown_counts["Count"].astype(int)
    
    # Display the counts in two columns
    st.markdown("### Employee Count by Breakdown")
    col1, col2 = st.columns(2)
    midpoint = len(breakdown_counts) // 2 + len(breakdown_counts) % 2  # Split data into two parts
    for i, row in breakdown_counts.iterrows():
        if i < midpoint:
            col1.write(f"**{row[selected_breakdown.capitalize()]}**: {row['Count']:,}")
        else:
            col2.write(f"**{row[selected_breakdown.capitalize()]}**: {row['Count']:,}")
    
    # Create a horizontal bar chart
    fig = px.bar(
        breakdown_counts,
        x="Count",
        y=selected_breakdown.capitalize(),
        orientation="h",
        text="Count",
        labels={"Count": "Employee Count"},
    )
    
    fig.update_traces(textposition="inside")
    fig.update_layout(
        title=f"Employee Distribution by {selected_breakdown.capitalize()}",
        xaxis_title="Count",
        yaxis_title=selected_breakdown.capitalize(),
        bargap=0.2,
        height=600,
        width=800,
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

# Function to display gender summary
def display_gender_summary():
    # Replace missing values in 'layer' column with "N-A"
    df['layer'] = df['layer'].fillna("N-A")
    filtered_df['layer'] = filtered_df['layer'].fillna("N-A")

    # Select the correct DataFrame based on filters
    display_df = filtered_df.copy()

    # Group by the selected breakdown variable and calculate gender distribution
    gender_counts = display_df.groupby([selected_breakdown, 'gender']).size().unstack().fillna(0)

    # Ensure that 'Male' and 'Female' exist in the groupby result
    if 'Male' not in gender_counts.columns:
        gender_counts['Male'] = 0
    if 'Female' not in gender_counts.columns:
        gender_counts['Female'] = 0

    # Calculate percentages for each gender
    gender_percentage = gender_counts.div(gender_counts.sum(axis=1), axis=0) * 100
    gender_percentage = gender_percentage.reset_index()

    # Combine count and percentage data
    gender_combined = gender_percentage.melt(id_vars=[selected_breakdown], value_vars=['Male', 'Female'],
                                             var_name='Gender', value_name='Percentage')
    gender_combined = gender_combined.merge(
        gender_counts.reset_index().melt(id_vars=[selected_breakdown], value_vars=['Male', 'Female'],
                                         var_name='Gender', value_name='Count'),
        on=[selected_breakdown, 'Gender']
    )
    gender_combined['Label'] = gender_combined.apply(
        lambda row: f"{int(row['Count'])} ({row['Percentage']:.1f}%)", axis=1
    )

    # Display title with filter details
    title_text = "Gender Metrics (All Units)" if not selected_units and not selected_subunits and not selected_layers else f"Gender Metrics (Filtered by {', '.join(selected_units)}, {', '.join(selected_subunits)}, {', '.join(selected_layers)})"
    st.title(title_text)
    st.subheader(f"Percentage of Gender by {selected_breakdown}")

    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)

    # Display total counts and percentages
    total_male = gender_counts['Male'].sum()
    total_female = gender_counts['Female'].sum()
    total_people = total_male + total_female
    male_percentage = (total_male / total_people * 100).round(2) if total_people > 0 else 0
    female_percentage = (total_female / total_people * 100).round(2) if total_people > 0 else 0

    col1, col2 = st.columns(2)
    col1.markdown(f"<div style='text-align: center'><h5>Male</h5><h1><strong>{male_percentage}%</strong></h1><p>{int(total_male)}</p></div>", unsafe_allow_html=True)
    col2.markdown(f"<div style='text-align: center'><h5>Female</h5><h1><strong>{female_percentage}%</strong></h1><p>{int(total_female)}</p></div>", unsafe_allow_html=True)

    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)

    # Plotly stacked bar chart
    fig = px.bar(
        gender_combined,
        x="Percentage",
        y=selected_breakdown,
        color="Gender",
        orientation="h",
        text="Label",
        color_discrete_map={'Male': '#90d5ff', 'Female': '#ffb5c0'},
        labels={
            "Percentage": "Percentage (%)",
            selected_breakdown: selected_breakdown.capitalize(),
            "Gender": "Gender"
        },
    )

    # Update layout to improve readability
    fig.update_traces(textposition="inside", insidetextanchor="middle")
    fig.update_layout(
        title=f"Gender Distribution by {selected_breakdown}",
        xaxis_title="Percentage (%)",
        yaxis_title=selected_breakdown.capitalize(),
        bargap=0.2,
        height=600,
        width=800,
        legend_title="Gender"
    )

    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

# Function to display generation summary
def display_generation_summary():
    # Replace missing values in 'layer' column with "N-A"
    df['layer'] = df['layer'].fillna("N-A")
    filtered_df['layer'] = filtered_df['layer'].fillna("N-A")

    # Select the correct DataFrame based on filters
    display_df = filtered_df.copy()

    # Group by the selected breakdown and calculate generation distribution
    generation_counts = display_df.groupby([selected_breakdown, 'generation']).size().unstack().fillna(0)

    # Define color map for generations
    color_map = {
        'POST WAR': '#9467bd',  # Purple
        'BOOMERS': '#1f77b4',  # Blue
        'GEN X': '#ff7f0e',    # Orange
        'GEN Y': '#2ca02c',    # Green
        'GEN Z': '#d62728'     # Red
    }

    # Ensure all generations are represented in the data
    for generation in color_map.keys():
        if generation not in generation_counts.columns:
            generation_counts[generation] = 0

    # Calculate percentages for each generation
    generation_percentage = generation_counts.div(generation_counts.sum(axis=1), axis=0) * 100
    generation_percentage = generation_percentage.reset_index()

    # Combine count and percentage data for tooltips and text labels
    generation_combined = generation_percentage.melt(id_vars=[selected_breakdown], value_vars=list(color_map.keys()),
                                                     var_name='Generation', value_name='Percentage')
    generation_combined = generation_combined.merge(
        generation_counts.reset_index().melt(id_vars=[selected_breakdown], value_vars=list(color_map.keys()),
                                             var_name='Generation', value_name='Count'),
        on=[selected_breakdown, 'Generation']
    )
    generation_combined['Label'] = generation_combined.apply(
        lambda row: f"{int(row['Count'])} ({row['Percentage']:.1f}%)", axis=1
    )

    # Display title with filter details
    title_text = "Generation Metrics (All Units)" if not selected_units and not selected_subunits and not selected_layers else f"Generation Metrics (Filtered by {', '.join(selected_units)}, {', '.join(selected_subunits)}, {', '.join(selected_layers)})"
    st.title(title_text)
    st.subheader(f"Percentage of Generation by {selected_breakdown}")

    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)

    # Display total counts and percentages with birth year ranges
    total_counts = generation_counts.sum().sum()
    total_percentage = {gen: (generation_counts[gen].sum() / total_counts * 100).round(2) if total_counts > 0 else 0 for gen in color_map.keys()}

    # Define birth year ranges for each generation
    birth_year_ranges = {
        'POST WAR': '(1928-1945)',
        'BOOMERS': '(1946-1964)',
        'GEN X': '(1965-1980)',
        'GEN Y': '(1981-1996)',
        'GEN Z': '(1997-2012)'
    }

    # Display generation information with birth years
    cols = st.columns(len(color_map.keys()))
    for i, (gen, color) in enumerate(color_map.items()):
        birth_year_range = birth_year_ranges.get(gen, "")
        cols[i].markdown(f"""
            <div style='text-align: center'>
                <h5 style="margin-bottom: 0;">{gen}</h5>
                <h5 style='margin-top: 0; margin-bottom: 0;'>{birth_year_range}</h5>
                <h1><strong>{total_percentage[gen]}%</strong></h1>
                <p>{int(generation_counts[gen].sum())}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)

    # Plotly stacked bar chart
    fig = px.bar(
        generation_combined,
        x="Percentage",
        y=selected_breakdown,
        color="Generation",
        orientation="h",
        text="Label",
        color_discrete_map=color_map,
        labels={
            "Percentage": "Percentage (%)",
            selected_breakdown: selected_breakdown.capitalize(),
            "Generation": "Generation"
        },
    )

    # Update layout to improve readability
    fig.update_traces(textposition="inside", insidetextanchor="middle")
    fig.update_layout(
        title=f"Generation Distribution by {selected_breakdown}",
        xaxis_title="Percentage (%)",
        yaxis_title=selected_breakdown.capitalize(),
        bargap=0.2,
        height=600,
        width=800,
        legend_title="Generation"
    )

    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

# Function to display religion summary
def display_religion_summary():
    # Replace missing values in 'layer' column with "N-A"
    df['layer'] = df['layer'].fillna("N-A")
    filtered_df['layer'] = filtered_df['layer'].fillna("N-A")

    # Select the correct DataFrame based on filters
    display_df = filtered_df.copy()

    # Calculate religion distribution by selected breakdown
    religion_counts = display_df.groupby([selected_breakdown, 'Religious Denomination Key']).size().unstack().fillna(0)

    # Define color map for religions
    color_map = {
        'Islam': '#1f77b4',       # Blue
        'Kristen': '#ff7f0e',     # Orange
        'Katholik': '#2ca02c',    # Green
        'Hindu': '#d62728',       # Red
        'Buddha': '#9467bd',      # Purple
        'Kepercayaan': '#8c564b', # Brown
        'Kong Hu Cu': '#e377c2'   # Pink
    }

    # Ensure all religions are present in the data
    for religion in color_map.keys():
        if religion not in religion_counts.columns:
            religion_counts[religion] = 0

    # Calculate religion percentages
    religion_percentage = religion_counts.div(religion_counts.sum(axis=1), axis=0) * 100
    religion_percentage = religion_percentage.reset_index()

    # Combine count and percentage data for tooltips and text labels
    religion_combined = religion_percentage.melt(id_vars=[selected_breakdown], value_vars=list(color_map.keys()),
                                                 var_name='Religion', value_name='Percentage')
    religion_combined = religion_combined.merge(
        religion_counts.reset_index().melt(id_vars=[selected_breakdown], value_vars=list(color_map.keys()),
                                           var_name='Religion', value_name='Count'),
        on=[selected_breakdown, 'Religion']
    )
    religion_combined['Label'] = religion_combined.apply(
        lambda row: f"{int(row['Count'])} ({row['Percentage']:.1f}%)", axis=1
    )

    # Display title with filter details
    title_text = "Religion Metrics (All Units)" if not selected_units and not selected_subunits and not selected_layers else f"Religion Metrics (Filtered by {', '.join(selected_units)}, {', '.join(selected_subunits)}, {', '.join(selected_layers)})"
    st.title(title_text)
    st.subheader(f"Percentage of Religion by {selected_breakdown}")

    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)

    # Display total counts and percentages
    total_counts = religion_counts.sum().sum()
    total_percentage = {rel: (religion_counts[rel].sum() / total_counts * 100).round(2) if total_counts > 0 else 0 for rel in color_map.keys()}

    # Display religion summary with percentages and counts
    cols = st.columns(len(color_map.keys()))
    for i, (rel, color) in enumerate(color_map.items()):
        cols[i].markdown(f"""
            <div style='text-align: center'>
                <h5 style="margin-bottom: 0;">{rel}</h5>
                <h1><strong>{total_percentage[rel]}%</strong></h1>
                <p>{int(religion_counts[rel].sum())}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)

    # Plotly stacked bar chart
    fig = px.bar(
        religion_combined,
        x="Percentage",
        y=selected_breakdown,
        color="Religion",
        orientation="h",
        text="Label",
        color_discrete_map=color_map,
        labels={
            "Percentage": "Percentage (%)",
            selected_breakdown: selected_breakdown.capitalize(),
            "Religion": "Religion"
        },
    )

    # Update layout to improve readability
    fig.update_traces(textposition="inside", insidetextanchor="middle")
    fig.update_layout(
        title=f"Religion Distribution by {selected_breakdown}",
        xaxis_title="Percentage (%)",
        yaxis_title=selected_breakdown.capitalize(),
        bargap=0.2,
        height=600,
        width=800,
        legend_title="Religion"
    )

    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

# Function to display tenure summary
def display_tenure_summary():
    # Replace missing values in 'layer' column with "N-A"
    df['layer'] = df['layer'].fillna("N-A")
    filtered_df['layer'] = filtered_df['layer'].fillna("N-A")

    # Select the correct DataFrame based on filters
    display_df = filtered_df.copy()

    # Define tenure groups and categorize them
    bins = [-1, 1, 3, 6, 10, 15, 20, 25, float('inf')]
    labels = ['<1 Year', '1-3 Year', '4-6 Year', '6-10 Year', '11-15 Year', '16-20 Year', '20-25 Year', '>25 Year']
    display_df['Service_Group'] = pd.cut(display_df['Years'], bins=bins, labels=labels, right=False)

    # Calculate tenure distribution by selected breakdown
    tenure_counts = display_df.groupby([selected_breakdown, 'Service_Group']).size().unstack().fillna(0)

    # Define color map for tenure groups
    color_map = {
        '<1 Year': '#1f77b4', '1-3 Year': '#ff7f0e', '4-6 Year': '#2ca02c', '6-10 Year': '#d62728',
        '11-15 Year': '#9467bd', '16-20 Year': '#8c564b', '20-25 Year': '#e377c2', '>25 Year': '#7f7f7f'
    }

    # Ensure all tenure groups are present in the data
    for tenure_group in color_map.keys():
        if tenure_group not in tenure_counts.columns:
            tenure_counts[tenure_group] = 0

    # Calculate tenure percentages
    tenure_percentage = tenure_counts.div(tenure_counts.sum(axis=1), axis=0) * 100
    tenure_percentage = tenure_percentage.reset_index()

    # Combine count and percentage data for tooltips and text labels
    tenure_combined = tenure_percentage.melt(id_vars=[selected_breakdown], value_vars=list(color_map.keys()),
                                             var_name='Tenure Group', value_name='Percentage')
    tenure_combined = tenure_combined.merge(
        tenure_counts.reset_index().melt(id_vars=[selected_breakdown], value_vars=list(color_map.keys()),
                                         var_name='Tenure Group', value_name='Count'),
        on=[selected_breakdown, 'Tenure Group']
    )
    tenure_combined['Label'] = tenure_combined.apply(
        lambda row: f"{int(row['Count'])} ({row['Percentage']:.1f}%)", axis=1
    )

    # Display title with filter details
    title_text = "Tenure Metrics (All Units)" if not selected_units and not selected_subunits and not selected_layers else f"Tenure Metrics (Filtered by {', '.join(selected_units)}, {', '.join(selected_subunits)}, {', '.join(selected_layers)})"
    st.title(title_text)
    st.subheader(f"Percentage of Tenure by {selected_breakdown}")

    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)

    # Display total counts and percentages
    total_counts = tenure_counts.sum().sum()
    total_percentage = {tenure: (tenure_counts[tenure].sum() / total_counts * 100).round(2) if total_counts > 0 else 0 for tenure in color_map.keys()}

    cols = st.columns(len(color_map.keys()))
    for i, (tenure, color) in enumerate(color_map.items()):
        cols[i].markdown(f"""
            <div style='text-align: center'>
                <h5 style="margin-bottom: 0;">{tenure}</h5>
                <h1><strong>{total_percentage[tenure]}%</strong></h1>
                <p>{int(tenure_counts[tenure].sum())}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border:1px solid #000'>", unsafe_allow_html=True)

    # Plotly stacked bar chart
    fig = px.bar(
        tenure_combined,
        x="Percentage",
        y=selected_breakdown,
        color="Tenure Group",
        orientation="h",
        text="Label",
        color_discrete_map=color_map,
        labels={
            "Percentage": "Percentage (%)",
            selected_breakdown: selected_breakdown.capitalize(),
            "Tenure Group": "Tenure Group"
        },
    )

    # Update layout to improve readability
    fig.update_traces(textposition="inside", insidetextanchor="middle")
    fig.update_layout(
        title=f"Tenure Distribution by {selected_breakdown}",
        xaxis_title="Percentage (%)",
        yaxis_title=selected_breakdown.capitalize(),
        bargap=0.2,
        height=600,
        width=800,
        legend_title="Tenure Group"
    )

    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

def display_region_summary():
    # Ensure the region column exists and filter the data
    if "region" not in df.columns:
        st.error("The 'region' column is not available in the dataset.")
        return

    display_df = filtered_df.copy()

    # Group by region and count the employees
    region_counts = (
        display_df.groupby("region")
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    region_counts.rename(columns={"region": "Region"}, inplace=True)

    # Display the table in three columns
    st.markdown("### Employee Count by Region")
    num_rows = len(region_counts)
    col1, col2, col3 = st.columns(3)

    with col1:
        for i in range(0, num_rows, 3):  # First column: every 3rd item starting from 0
            if i < num_rows:
                st.write(f"**{region_counts.iloc[i]['Region']}**: {region_counts.iloc[i]['Count']}")

    with col2:
        for i in range(1, num_rows, 3):  # Second column: every 3rd item starting from 1
            if i < num_rows:
                st.write(f"**{region_counts.iloc[i]['Region']}**: {region_counts.iloc[i]['Count']}")

    with col3:
        for i in range(2, num_rows, 3):  # Third column: every 3rd item starting from 2
            if i < num_rows:
                st.write(f"**{region_counts.iloc[i]['Region']}**: {region_counts.iloc[i]['Count']}")

    # Plotly bar chart for region distribution
    fig = px.bar(
        region_counts,
        x="Count",
        y="Region",
        orientation="h",
        text="Count",
        color="Region",
        color_discrete_sequence=px.colors.qualitative.Plotly,
        labels={"Count": "Employee Count", "Region": "Region"},
    )

    # Update chart layout
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title="Region-wise Employee Distribution",
        xaxis_title="Employee Count",
        yaxis_title="Region",
        height=600,
        width=800,
        showlegend=False,
    )

    # Display the bar chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

def display_age_summary():
    # Ensure the 'Age' column exists
    if "Age" not in df.columns:
        st.error("The 'Age' column is not available in the dataset.")
        return

    # Filter the dataset
    display_df = filtered_df.copy()

    # Count employees by individual age
    age_counts = (
        display_df.groupby("Age")
        .size()
        .reset_index(name="Count")
        .sort_values("Age")
    )

    # Convert Count to integer for display
    age_counts["Count"] = age_counts["Count"].astype(int)

    # Split table into columns for better readability
    st.markdown("### Employee Count by Age")
    col1, col2, col3 = st.columns(3)

    num_rows = len(age_counts)
    for i, col in enumerate([col1, col2, col3]):
        with col:
            for j in range(i, num_rows, 3):  # Distribute rows across three columns
                st.write(f"**{int(age_counts.iloc[j]['Age'])}**: {int(age_counts.iloc[j]['Count'])}")

    # Plotly bar chart for individual age distribution
    fig = px.bar(
        age_counts,
        x="Count",
        y="Age",
        orientation="h",
        text="Count",
        color="Age",
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={"Count": "Employee Count", "Age": "Age"},
    )

    # Update chart layout
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title="Age-wise Employee Distribution",
        xaxis_title="Employee Count",
        yaxis_title="Age",
        height=600,
        width=800,
        showlegend=False,
    )

    # Display the bar chart
    st.plotly_chart(fig, use_container_width=True)


# Main logic to display the selected page's content
if selected_page == '':
    display_total_employees_with_breakdown()
elif selected_page == 'Gender':
    display_gender_summary()
elif selected_page == 'Generation':
    display_generation_summary()
elif selected_page == 'Religion':
    display_religion_summary()
elif selected_page == 'Tenure':
    display_tenure_summary()
elif selected_page == 'Region':
    display_region_summary()
elif selected_page == 'Age':
    display_age_summary()
