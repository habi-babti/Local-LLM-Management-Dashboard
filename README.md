#  Local LLM Management Dashboard

A **Streamlit-based dashboard** for managing and monitoring **Ollama** Local LLM models.  
It allows you to:
- View all installed Ollama models.
- Check system resources (disk, RAM).
- Pull new models.
- Delete existing models.
- Monitor Ollama server connection status.

---

##  Preview
*(Optional — Add a screenshot of the dashboard here)*

---

##  Features
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

## 🛠 Requirements
- **Python** 3.8+
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Requests](https://docs.python-requests.org/)
- [psutil](https://pypi.org/project/psutil/)

---

##  Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/local-llm-dashboard.git
   cd local-llm-dashboard
