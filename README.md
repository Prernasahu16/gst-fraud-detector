GST Fraud Detector

Detect Potential GST Fraud Using Data Analytics & Visualization

Overview

This project analyzes GST (Goods and Services Tax) data in India to detect suspicious transactions and potential fraud patterns. It combines data cleaning, clustering, and visualization to provide interactive dashboards and actionable insights.

Features
Data Cleaning: Standardizes raw GST data (clean_data.py)
Clustering Analysis: Groups states and sectors using KMeans to spot anomalies (kmeans_clustering.py)
Visualization & Dashboards: Generates charts for sector and state analysis (generate_charts.py)
Interactive Web App: Explore data and risk patterns with app.py (Streamlit)
Automated Workflow: run_all.py runs the full pipeline end-to-end


Project Structure
gst_project/
├── app.py
├── clean_data.py
├── kmeans_clustering.py
├── generate_charts.py
├── run_all.py
├── data/
│   ├── gst_raw.csv
│   ├── gst_clean.csv
│   └── state_clusters.csv
├── visuals/
│   ├── 01_master_dashboard.png
│   ├── 02_sector_deep_dive.png
│   └── 03_state_scorecard.png
├── gst_fraud_queries.sql
├── requirements.txt
└── README.md


How to Run
Clone the repository:
git clone https://github.com/yourusername/gst-fraud-detector.git
cd gst-fraud-detector/gst_project
Install dependencies:
pip install -r requirements.txt
Run the Streamlit app:
streamlit run app.py
Explore dashboards and fraud insights interactively.

