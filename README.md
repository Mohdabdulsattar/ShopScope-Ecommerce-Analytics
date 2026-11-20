# ShopScope – E-Commerce Customer Behaviour Analytics

A no-login analytics website built with Flask, PostgreSQL, Pandas and Chart.js.

## Features
- Overview KPIs: revenue, orders, unique customers, average order value
- Monthly revenue trend, category mix, customer segments and top products
- Customer leaderboard with search
- Product performance table
- CSV import and CSV export
- Automatically generated demo transactions on first run
- PostgreSQL support; SQLite fallback for a quick local preview

## 1. Requirements
Install Python 3.10+ and PostgreSQL. Open PowerShell in this folder.

## 2. Create a virtual environment
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```
If script execution is blocked, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## 3. Install packages
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Quick local preview (SQLite)
No database setup is required for the preview:
```powershell
python app.py
```
Open http://127.0.0.1:5000

## 5. Use PostgreSQL
Create a database in pgAdmin or psql:
```sql
CREATE DATABASE shopscope;
```
Set the connection string in PowerShell (replace YOUR_PASSWORD):
```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/shopscope"
$env:SECRET_KEY="replace-this-with-a-long-random-value"
python app.py
```
The tables and sample data are created automatically on first start.

## 6. Upload your own CSV
Use the upload section on the dashboard. Required column names:
`order_date, customer_id, customer_name, product, category, quantity, unit_price`
Optional: `region`. See `sample_data.csv`.

The import adds records to the existing database; it does not delete demo data.

## 7. Deploy publicly on Render
1. Push this folder to a GitHub repository.
2. In Render, choose **New → Blueprint** and connect the repository.
3. Render reads `render.yaml` and provisions the web service and PostgreSQL database.
4. Deploy. The generated `onrender.com` URL can be shared publicly.
5. Before production use, set a strong `SECRET_KEY`, review database backups and add access controls if the data is private.

## Important
This is a starter analytics project with synthetic demo transactions, not real customer data. The sample dataset is illustrative. The demo app has no login as requested; do not upload sensitive customer information to a public deployment.
