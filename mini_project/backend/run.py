"""
Simple launcher that starts the Flask dev server.
Run:  python run.py
"""
from app import app

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Devanagari Classifier — Flask Backend")
    print("="*60)
    print("  API running at  http://localhost:5000")
    print("  Frontend at     http://localhost:5000/")
    print("  Press Ctrl+C to stop.")
    print("="*60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
