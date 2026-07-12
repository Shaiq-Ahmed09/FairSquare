"""
run.py — Smart Real Estate Deal Finder (India)
Datasets: Chennai/Multi (V21) + Delhi + Pune
Steps: preprocess -> train -> predict -> serve dashboard
"""

import io
import os
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import webbrowser
import threading
import http.server
import socketserver

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# -- Paths ------------------------------------------------------------------
V21_PATH     = 'dataset/Real Estate Data V21.csv'
DELHI_PATH   = 'dataset/Delhi_v2.csv'
PUNE_PATH    = 'dataset/pune_house_prices.csv'
MODEL_PATH   = 'models/fmv_model.pkl'
ENCODER_PATH = 'models/encoders.pkl'
DEALS_PATH   = 'dashboard/deals.json'
DASHBOARD    = os.path.abspath('dashboard')
PORT         = 8765


def sep(text=''):
    print(f"\n{'='*55}")
    if text:
        print(f"  {text}")
        print(f"{'='*55}")


def main():
    sep()
    print("  Smart Real Estate Deal Finder -- India")
    print("  Chennai + Delhi + Pune | XGBoost FMV Engine")
    sep()

    force = '--retrain' in sys.argv

    # -- Step 1: Train or reuse --------------------------------------------
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH) and not force:
        sep(">> Existing model found -- skipping training")
        print(f"     Model    : {MODEL_PATH}")
        print(f"     Encoders : {ENCODER_PATH}")
        print("     Pass --retrain to force retraining.")
        metrics = {}
        if os.path.exists(DEALS_PATH):
            try:
                with open(DEALS_PATH) as f:
                    prev = json.load(f)
                metrics = {
                    'r2':   prev['meta'].get('model_r2', 0),
                    'rmse': prev['meta'].get('model_rmse_l', 0) * 1e5,
                }
            except Exception:
                pass
    else:
        sep("Step 1/2 -- Training XGBoost on merged dataset")
        from train_model import train
        _, _, _, metrics = train(V21_PATH, DELHI_PATH, PUNE_PATH)

    # -- Step 2: Predict & export ------------------------------------------
    sep("Step 2/2 -- Predicting FMV & scoring deals")
    from predict import predict_and_export
    result = predict_and_export(
        v21_path=V21_PATH, delhi_path=DELHI_PATH, pune_path=PUNE_PATH,
        model_path=MODEL_PATH, encoder_path=ENCODER_PATH,
        output_path=DEALS_PATH, metrics=metrics,
    )

    meta = result['meta']
    sep("Pipeline complete")
    print(f"  Total Listings : {meta['total_listings']:,}")
    print(f"  Hot Deals      : {meta['hot_deals']:,}")
    print(f"  Good Deals     : {meta['good_deals']:,}")
    print(f"  Model R2       : {meta['model_r2']}")
    print(f"  Sources        : {meta['sources']}")

    # -- Step 3: Serve dashboard -------------------------------------------
    sep(f"Launching Dashboard -> http://localhost:{PORT}")

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=DASHBOARD, **kwargs)
        def log_message(self, *args):
            pass

    def open_browser():
        import time; time.sleep(0.9)
        webbrowser.open(f'http://localhost:{PORT}')

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"  http://localhost:{PORT}  (Ctrl+C to stop)\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")


if __name__ == '__main__':
    main()
