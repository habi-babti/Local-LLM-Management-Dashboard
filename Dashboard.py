import streamlit as st
import requests
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
        date_str = date_str.replace('Z', '+00:00')
        dt_object = datetime.fromisoformat(date_str)
        return dt_object.strftime("%d %b %Y, %H:%M:%S")
    except ValueError:
        return "Invalid Date"


# --- API Communication ---
@st.cache_data(ttl=10)
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


@st.cache_data(ttl=60)
def get_ollama_models(base_url):
    """Fetches the list of installed models from the Ollama API."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        response.raise_for_status()
        models_data = response.json().get('models', [])

        if not models_data:
            return []

        processed_models = []
        for model in models_data:
            processed_models.append({
                "name": model.get('name'),
                "size": model.get('size', 0),
                "size_formatted": format_bytes(model.get('size', 0)),
                "modified": model.get('modified_at', ''),
                "modified_formatted": parse_iso_date(model.get('modified_at', '')),
                "family": model.get('details', {}).get('family', 'N/A'),
                "parameters": model.get('details', {}).get('parameter_size', 'N/A'),
                "quantization": model.get('details', {}).get('quantization_level', 'N/A'),
            })

        return sorted(processed_models, key=lambda x: x['name'])

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch models: {e}")
        return []


def pull_model(base_url, model_name):
    """Pulls a new model using the Ollama API."""
    try:
        with st.spinner(f"Pulling model '{model_name}'... This may take a while."):
            response = requests.post(
                f"{base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=None
            )
            response.raise_for_status()
        st.success(f"Successfully pulled model '{model_name}'!")
        st.cache_data.clear()
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
        st.cache_data.clear()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to delete model: {e}")


# --- Sidebar ---
st.sidebar.title("⚙️ Configuration")

if 'ollama_url' not in st.session_state:
    st.session_state.ollama_url = "http://localhost:11434"

st.session_state.ollama_url = st.sidebar.text_input(
    "Ollama Server URL",
    value=st.session_state.ollama_url
)

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Make sure Ollama is running with `ollama serve`")


# --- Main Application ---
st.title("🤖 Local LLM Management Dashboard")

# Check connection
is_connected, message = check_ollama_connection(st.session_state.ollama_url)
status_color = "green" if is_connected else "red"

st.markdown(f"### Status: :{status_color}[{message}]")
st.divider()

if not is_connected:
    st.error("Could not connect to the Ollama server. Please ensure Ollama is running and the URL is correct.")
    st.info("To start Ollama, open your terminal and run `ollama serve`.")
    st.stop()

# Fetch models
models = get_ollama_models(st.session_state.ollama_url)

# --- Dashboard Metrics ---
if models:
    total_models = len(models)
    total_size = sum(m['size'] for m in models)

    col1, col2 = st.columns(2)
    col1.metric("📦 Total Models", f"{total_models}")
    col2.metric("💾 Total Disk Space", format_bytes(total_size))
else:
    st.info("No models found on the Ollama server.")

st.divider()

# --- Model Management Section ---
st.subheader("🔧 Manage Models")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Pull New Model**")
    with st.form("pull_model_form"):
        new_model_name = st.text_input(
            "Model Name",
            placeholder="e.g., llama3:8b, mistral, gemma:2b"
        )
        submitted_pull = st.form_submit_button("⬇️ Pull Model", use_container_width=True)
        if submitted_pull and new_model_name:
            pull_model(st.session_state.ollama_url, new_model_name)
            st.rerun()

with col2:
    st.markdown("**Delete Model**")
    if models:
        model_names = [m['name'] for m in models]
        model_to_delete = st.selectbox(
            "Select Model",
            options=model_names,
            label_visibility="collapsed"
        )
        if st.button("🗑️ Delete Model", type="primary", use_container_width=True):
            if st.session_state.get('confirm_delete') == model_to_delete:
                delete_model(st.session_state.ollama_url, model_to_delete)
                st.session_state.confirm_delete = None
                st.rerun()
            else:
                st.session_state.confirm_delete = model_to_delete
                st.warning(f"⚠️ Click again to confirm deletion of **{model_to_delete}**")
    else:
        st.info("No models to delete")

st.divider()

# --- Models Display ---
st.subheader("📚 Installed Models")

if models:
    view_mode = st.radio(
        "View Mode",
        ["Table View", "Card View"],
        horizontal=True
    )

    if view_mode == "Table View":
        # Create table manually
        st.markdown("| Name | Size | Family | Parameters | Quantization | Modified |")
        st.markdown("|------|------|--------|------------|--------------|----------|")
        for model in models:
            st.markdown(
                f"| {model['name']} | {model['size_formatted']} | "
                f"{model['family']} | {model['parameters']} | "
                f"{model['quantization']} | {model['modified_formatted']} |"
            )

    else:  # Card View
        cols = st.columns(3)
        for idx, model in enumerate(models):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {model['name']}")
                    st.markdown(f"**Size:** {model['size_formatted']}")
                    st.markdown(f"**Family:** {model['family']}")
                    st.caption(f"Modified: {model['modified_formatted']}")
                    
                    with st.expander("📋 Details"):
                        st.write(f"**Parameters:** {model['parameters']}")
                        st.write(f"**Quantization:** {model['quantization']}")
else:
    st.info("No models installed. Pull a model to get started!")

# Footer
st.divider()
st.caption("Built with Streamlit and Requests • Managing Ollama Models")
