# Legacy Files Note

This project has been converted from a desktop Tkinter app to a Streamlit web app.

## Files No Longer Used (Available for Reference)

The following files are from the previous desktop implementation and are **no longer required** for running the app. They are kept in the repository for reference:

- `app.py` - Legacy Tkinter main entry point (replaced by `web_app.py`)
- `modules/ui.py` - Legacy Tkinter UI module (functionality now in `web_app.py`)
- `setup.py` - Legacy PyInstaller packaging script (no longer needed for web app)

## Current Entry Point

To run the application, use:
```bash
streamlit run web_app.py
```

All core logic modules (`config.py`, `logic.py`, `ai.py`, `pdf_generator.py`) remain unchanged and are fully utilized by the Streamlit web app.
