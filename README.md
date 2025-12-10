# Local LLM Management Dashboard

A Streamlit-based dashboard for managing and monitoring Ollama Local LLM models.  
It allows you to:
- View all installed Ollama models.
- Check system resources (disk, RAM).
- Pull new models.
- Delete existing models.
- Monitor Ollama server connection status.

---

## Preview
<img width="1903" height="906" alt="image" src="https://github.com/user-attachments/assets/184a5d3e-b5ab-469b-91f2-11d60bf15c22" />
---

## Features
- **Ollama Server Connection Check**  
  Instantly verify if your Ollama instance is running and reachable.

- **Model Management**  
  - Pull new models by name (e.g., `llama3:8b`, `mistral`).
  - Delete unwanted models directly from the dashboard.

- **System Monitoring**  
  View real-time disk and memory usage using `psutil`.

- **Multiple View Modes**  
  - Table view for quick sorting/filtering.
  - Card view for a visually appealing layout.

- **Auto-refresh**  
  Cached data refreshes periodically or manually via the refresh button.

---

## Requirements
- **Python** 3.8+
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Requests](https://docs.python-requests.org/)
- [psutil](https://pypi.org/project/psutil/)

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/habi-babti/Local-LLM-Management-Dashboard.git
   cd local-llm-dashboard
   ```

2. **Create and activate a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/Mac
   venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install streamlit pandas requests psutil
   ```

---

## Usage

1. **Start Ollama**
   In your terminal:
   ```bash
   ollama serve
   ```

2. **Run the Streamlit app**
   ```bash
   streamlit run Dashboard.py
   ```
  

3. **Access in browser**
   Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Configuration

* **Ollama Server URL** can be set in the sidebar.
  Default: `http://localhost:11434`

---

## License

MIT License. See `LICENSE` file for details.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## Notes

* Deleting a model is irreversible — proceed with caution.
* Large models may take significant time and disk space to pull.
