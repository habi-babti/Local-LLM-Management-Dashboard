import streamlit as st
import requests
import pandas as pd
import psutil
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Local LLM Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- Helper Functions ---
def format_bytes(size):
    """Converts bytes to a human-readable format (KB, MB, GB)."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"
    else:
        return f"{size / (1024 ** 3):.2f} GB"


def parse_iso_date(date_str):
    """Parses ISO 8601 date string and formats it nicely."""
    try:
        # Handle the 'Z' for UTC and potential microseconds
        date_str = date_str.replace('Z', '+00:00')
        dt_object = datetime.fromisoformat(date_str)
        return dt_object.strftime("%d %b %Y, %H:%M:%S")
    except ValueError:
        return "Invalid Date"


# --- API Communication ---
@st.cache_data(ttl=10)  # Cache for 10 seconds
def check_ollama_connection(base_url):
    """Checks if the Ollama server is running and accessible."""
    try:
        response = requests.get(base_url, timeout=5)
        response.raise_for_status()
        if "Ollama is running" in response.text:
            return True, "Connected to Ollama"
        return False, "Unexpected response from Ollama"
    except requests.exceptions.RequestException as e:
        return False, f"Connection failed: {e}"


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_ollama_models(base_url):
    """Fetches the list of installed models from the Ollama API."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        response.raise_for_status()
        models_data = response.json().get('models', [])

        if not models_data:
            return pd.DataFrame()

        # Process data for display
        processed_models = []
        for model in models_data:
            processed_models.append({
                "Name": model.get('name'),
                "Size": format_bytes(model.get('size', 0)),
                "Modified": parse_iso_date(model.get('modified_at', '')),
                "Family": model.get('details', {}).get('family', 'N/A'),
                "Parameters": model.get('details', {}).get('parameter_size', 'N/A'),
                "Quantization": model.get('details', {}).get('quantization_level', 'N/A'),
                "_size_bytes": model.get('size', 0),  # For sorting
                "_modified_raw": model.get('modified_at', '')
            })

        df = pd.DataFrame(processed_models)
        return df.sort_values(by="Name").reset_index(drop=True)

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch models: {e}")
        return pd.DataFrame()


def pull_model(base_url, model_name):
    """Pulls a new model using the Ollama API."""
    try:
        with st.spinner(f"Pulling model '{model_name}'... This may take a while."):
            response = requests.post(
                f"{base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=None  # No timeout for potentially long downloads
            )
            response.raise_for_status()
        st.success(f"Successfully pulled model '{model_name}'!")
        st.cache_data.clear()  # Clear cache to refresh model list
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to pull model: {e}")


def delete_model(base_url, model_name):
    """Deletes a model using the Ollama API."""
    try:
        response = requests.delete(
            f"{base_url}/api/delete",
            json={"name": model_name},
            timeout=30
        )
        response.raise_for_status()
        st.success(f"Successfully deleted model '{model_name}'!")
        st.cache_data.clear()  # Clear cache
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to delete model: {e}")


# --- Sidebar ---
st.sidebar.title("Configuration")

if 'ollama_url' not in st.session_state:
    st.session_state.ollama_url = "http://localhost:11434"

st.session_state.ollama_url = st.sidebar.text_input(
    "Ollama Server URL",
    value=st.session_state.ollama_url
)

# Refresh button
if st.sidebar.button(" Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("️ System Info")

try:
    # System info using psutil
    disk = psutil.disk_usage('/')
    ram = psutil.virtual_memory()

    st.sidebar.write(f"**Disk Usage** (`/`)")
    st.sidebar.progress(disk.percent / 100)
    st.sidebar.write(f"{format_bytes(disk.free)} free of {format_bytes(disk.total)}")

    st.sidebar.write("**RAM Usage**")
    st.sidebar.progress(ram.percent / 100)
    st.sidebar.write(f"{format_bytes(ram.available)} available of {format_bytes(ram.total)}")
except Exception as e:
    st.sidebar.warning(f"Could not retrieve system info: {e}")

# --- Main Application ---
st.title(" Local LLM Management Dashboard")

# Check connection and display status
is_connected, message = check_ollama_connection(st.session_state.ollama_url)
status_color = "success" if is_connected else "error"
st.header(f"Ollama Status: :{status_color}[{message}]", divider="rainbow")

if not is_connected:
    st.error("Could not connect to the Ollama server. Please ensure Ollama is running and the URL is correct.")
    st.info("To start Ollama, open your terminal and run `ollama serve`.")
    st.stop()

# If connected, fetch and display models
models_df = get_ollama_models(st.session_state.ollama_url)

# --- Dashboard Metrics ---
if not models_df.empty:
    total_models = len(models_df)
    total_size = models_df['_size_bytes'].sum()

    col1, col2 = st.columns(2)
    col1.metric("Total Models", f"{total_models}")
    col2.metric("Total Disk Space", format_bytes(total_size))
else:
    st.info("No models found on the Ollama server.")

# --- Model Management Section ---
with st.expander("Manage Models"):
    col1, col2 = st.columns([3, 1])
    with col1:
        with st.form("pull_model_form"):
            new_model_name = st.text_input("Model Name to Pull", placeholder="e.g., llama3:8b, mistral, etc.")
            submitted_pull = st.form_submit_button("Pull Model")
            if submitted_pull and new_model_name:
                pull_model(st.session_state.ollama_url, new_model_name)
                st.rerun()

    with col2:
        with st.form("delete_model_form"):
            model_to_delete = st.selectbox("Select Model to Delete",
                                           options=models_df['Name'].tolist() if not models_df.empty else [])
            submitted_delete = st.form_submit_button("Delete Model", type="primary")
            if submitted_delete and model_to_delete:
                st.warning(f"Are you sure you want to delete **{model_to_delete}**? This cannot be undone.", icon="⚠️")
                if st.button("Yes, permanently delete"):
                    delete_model(st.session_state.ollama_url, model_to_delete)
                    st.rerun()

# --- Models Display ---
st.header("Installed Models", divider="gray")

if not models_df.empty:
    view_mode = st.radio("Select View", ["Table View", "Card View"], horizontal=True, label_visibility="collapsed")

    if view_mode == "Table View":
        st.dataframe(
            models_df[['Name', 'Size', 'Family', 'Parameters', 'Quantization', 'Modified']],
            use_container_width=True,
            hide_index=True,
        )

    elif view_mode == "Card View":
        cols = st.columns(3)
        col_idx = 0
        for index, row in models_df.iterrows():
            with cols[col_idx]:
                with st.container(border=True):
                    st.subheader(row['Name'])
                    st.text(f"Size: {row['Size']}")
                    st.text(f"Family: {row['Family']}")
                    st.caption(f"Modified: {row['Modified']}")
                    with st.expander("More Details"):
                        st.write(f"**Parameters:** {row['Parameters']}")
                        st.write(f"**Quantization:** {row['Quantization']}")
            col_idx = (col_idx + 1) % 3
