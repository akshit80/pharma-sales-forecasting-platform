import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.database.database import Base, engine
from backend.api.router import api_router
from backend.api.datasets import router as datasets_router
from backend.api.eda import router as eda_router
from backend.api.forecast import router as forecast_router
from backend.api.scenarios import router as scenarios_router
from backend.api.reports import router as reports_router

# Auto-create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pharmaceutical Sales Forecasting & Decision Intelligence Platform",
    description="Commercial forecasting and analytics platform.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers at both /api/v1 and root level for maximum Vercel URL resilience
app.include_router(api_router)
app.include_router(datasets_router)
app.include_router(eda_router)
app.include_router(forecast_router)
app.include_router(scenarios_router)
app.include_router(reports_router)

def get_html_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pharma Commercial Analytics Platform</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        </style>
    </head>
    <body class="text-slate-800">
        <!-- Top Navbar -->
        <nav class="bg-blue-900 text-white px-6 py-4 flex justify-between items-center shadow-md">
            <div class="flex items-center space-x-3">
                <span class="text-2xl">💊</span>
                <div>
                    <h1 class="font-bold text-lg leading-tight">Pharma Commercial Analytics & Demand Forecasting</h1>
                    <p class="text-xs text-blue-200">Decision Intelligence Platform</p>
                </div>
            </div>
            <div class="flex space-x-4 text-sm font-medium">
                <a href="/docs" target="_blank" class="bg-blue-800 hover:bg-blue-700 px-3 py-1.5 rounded transition">API Docs</a>
            </div>
        </nav>

        <div class="max-w-7xl mx-auto px-6 py-8">
            <!-- Quick Start Banner -->
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                    <h2 class="text-xl font-bold text-blue-900 mb-1">Commercial Sales Analytics Studio</h2>
                    <p class="text-sm text-slate-600">Analyze historical sales, run Prophet & XGBoost time-series forecasts, simulate pricing scenarios, and generate executive insights.</p>
                </div>
                <div class="flex gap-3">
                    <button onclick="loadSampleData()" id="btn-sample" class="bg-blue-900 hover:bg-blue-800 text-white font-semibold px-5 py-2.5 rounded-lg shadow-sm transition flex items-center gap-2">
                        <span>⚡ Load Sample Data</span>
                    </button>
                </div>
            </div>

            <!-- Dashboard Content Grid -->
            <div id="dashboard-content" class="space-y-8 hidden">
                <!-- KPI Row -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <p class="text-xs font-semibold text-slate-500 uppercase">Total Revenue</p>
                        <h3 id="kpi-revenue" class="text-2xl font-bold text-blue-900 mt-1">$0.00</h3>
                    </div>
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <p class="text-xs font-semibold text-slate-500 uppercase">Total Sales Volume</p>
                        <h3 id="kpi-volume" class="text-2xl font-bold text-teal-600 mt-1">0 units</h3>
                    </div>
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <p class="text-xs font-semibold text-slate-500 uppercase">Active Products</p>
                        <h3 id="kpi-products" class="text-2xl font-bold text-slate-800 mt-1">0</h3>
                    </div>
                    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <p class="text-xs font-semibold text-slate-500 uppercase">Geographic Regions</p>
                        <h3 id="kpi-regions" class="text-2xl font-bold text-slate-800 mt-1">0</h3>
                    </div>
                </div>

                <!-- Charts Row 1 -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <h3 class="font-bold text-blue-900 mb-4">Historical Monthly Sales Trend</h3>
                        <div id="chart-trend" class="h-72"></div>
                    </div>
                    <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <h3 class="font-bold text-blue-900 mb-4">Annual Seasonality Distribution</h3>
                        <div id="chart-season" class="h-72"></div>
                    </div>
                </div>

                <!-- Forecast & Scenario Section -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <!-- Control Panel -->
                    <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                        <h3 class="font-bold text-blue-900 border-b pb-2">Forecasting & What-If Controls</h3>
                        <div>
                            <label class="text-xs font-semibold text-slate-600 block mb-1">Forecast Model</label>
                            <select id="select-model" class="w-full border rounded-lg p-2 text-sm">
                                <option value="XGBoost">XGBoost Regressor</option>
                                <option value="Prophet">Facebook Prophet</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs font-semibold text-slate-600 block mb-1">Forecast Horizon</label>
                            <select id="select-horizon" class="w-full border rounded-lg p-2 text-sm">
                                <option value="3">3 Months</option>
                                <option value="6" selected>6 Months</option>
                                <option value="12">12 Months</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs font-semibold text-slate-600 block mb-1">Price Change: <span id="val-price">0</span>%</label>
                            <input type="range" id="range-price" min="-20" max="30" value="0" class="w-full" oninput="document.getElementById('val-price').innerText=this.value">
                        </div>
                        <div>
                            <label class="text-xs font-semibold text-slate-600 block mb-1">Marketing Change: <span id="val-mkt">0</span>%</label>
                            <input type="range" id="range-mkt" min="-50" max="50" value="0" class="w-full" oninput="document.getElementById('val-mkt').innerText=this.value">
                        </div>
                        <button onclick="runForecastAndScenario()" class="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2 rounded-lg transition">
                            Run Model & Scenario
                        </button>
                    </div>

                    <!-- Forecast Chart -->
                    <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm md:col-span-2">
                        <div class="flex justify-between items-center mb-2">
                            <h3 class="font-bold text-blue-900">Demand Forecast Projection</h3>
                            <div id="metrics-badge" class="text-xs bg-slate-100 px-3 py-1 rounded font-semibold text-slate-700"></div>
                        </div>
                        <div id="chart-forecast" class="h-72"></div>
                    </div>
                </div>

                <!-- Decision Intelligence Section -->
                <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="font-bold text-blue-900 text-lg">🧠 Rule-Based Decision Intelligence Recommendations</h3>
                        <button onclick="downloadReport()" class="bg-blue-900 hover:bg-blue-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition">
                            📄 Export PDF Report
                        </button>
                    </div>
                    <div id="recommendations-list" class="grid grid-cols-1 md:grid-cols-2 gap-4"></div>
                </div>
            </div>
        </div>

        <script>
            let currentDatasetId = null;

            async function apiFetch(path, options={}) {
                let res = await fetch(path, options);
                if (res.status === 404 && !path.startsWith('/api/v1')) {
                    res = await fetch('/api/v1' + path, options);
                }
                return res;
            }

            async function loadSampleData() {
                document.getElementById('btn-sample').innerText = '⏳ Loading...';
                try {
                    let uploadRes = await apiFetch('/datasets/upload_sample', { method: 'POST' });
                    if (!uploadRes.ok) {
                        uploadRes = await apiFetch('/api/v1/datasets/upload_sample', { method: 'POST' });
                    }
                    const ds = await uploadRes.json();
                    currentDatasetId = ds.id;
                    
                    document.getElementById('dashboard-content').classList.remove('hidden');
                    document.getElementById('btn-sample').innerText = '✓ Dataset Active';
                    
                    await loadEDA();
                    await runForecastAndScenario();
                } catch(e) {
                    console.error(e);
                    alert('Error loading sample dataset: ' + e);
                }
            }

            async function loadEDA() {
                const res = await apiFetch(`/eda/${currentDatasetId}`);
                const data = await res.json();

                document.getElementById('kpi-revenue').innerText = '$' + data.total_revenue.toLocaleString();
                document.getElementById('kpi-volume').innerText = Math.round(data.total_sales_units).toLocaleString() + ' units';
                document.getElementById('kpi-products').innerText = data.products.length;
                document.getElementById('kpi-regions').innerText = data.regions.length;

                const months = data.monthly_sales.map(m => m.month_str);
                const sales = data.monthly_sales.map(m => m.sales_units);
                Plotly.newPlot('chart-trend', [{
                    x: months, y: sales, type: 'scatter', mode: 'lines+markers',
                    line: { color: '#1E3A8A', width: 3 }
                }], { margin: { t: 10, b: 30, l: 40, r: 10 } });

                const seasonMonths = data.seasonality.map(s => s.month_name);
                const seasonAvg = data.seasonality.map(s => s.sales_units);
                Plotly.newPlot('chart-season', [{
                    x: seasonMonths, y: seasonAvg, type: 'bar',
                    marker: { color: '#0D9488' }
                }], { margin: { t: 10, b: 30, l: 40, r: 10 } });
            }

            async function runForecastAndScenario() {
                const model = document.getElementById('select-model').value;
                const horizon = parseInt(document.getElementById('select-horizon').value);

                const fcRes = await apiFetch('/forecast/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dataset_id: currentDatasetId, model_name: model, horizon_months: horizon })
                });
                const fc = await fcRes.json();

                document.getElementById('metrics-badge').innerText = `MAE: ${fc.mae} | RMSE: ${fc.rmse} | MAPE: ${fc.mape}%`;

                const fcDates = fc.predictions.map(p => p.date);
                const fcUnits = fc.predictions.map(p => p.predicted_units);

                Plotly.newPlot('chart-forecast', [{
                    x: fcDates, y: fcUnits, type: 'scatter', mode: 'lines+markers', name: 'Forecast',
                    line: { color: '#0D9488', width: 3, dash: 'dash' }
                }], { margin: { t: 10, b: 30, l: 40, r: 10 } });

                const recRes = await apiFetch(`/forecast/decision_intelligence/${currentDatasetId}`);
                const recData = await recRes.json();
                
                const recContainer = document.getElementById('recommendations-list');
                recContainer.innerHTML = '';
                recData.recommendations.forEach(r => {
                    const card = document.createElement('div');
                    card.className = 'border-l-4 border-blue-900 bg-slate-50 p-4 rounded-r-lg';
                    card.innerHTML = `
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-bold text-blue-900 text-sm">${r.category}</span>
                            <span class="text-xs px-2 py-0.5 rounded font-bold ${r.priority === 'High' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}">${r.priority}</span>
                        </div>
                        <p class="font-semibold text-slate-800 text-sm">👉 ${r.recommendation}</p>
                        <p class="text-xs text-slate-600 mt-1"><b>Reason:</b> ${r.reasoning}</p>
                        <p class="text-xs text-emerald-700 mt-1"><b>Impact:</b> ${r.impact}</p>
                    `;
                    recContainer.appendChild(card);
                });
            }

            async function downloadReport() {
                const model = document.getElementById('select-model').value;
                const horizon = document.getElementById('select-horizon').value;
                const res = await apiFetch(`/reports/generate?dataset_id=${currentDatasetId}&model_name=${model}&horizon_months=${horizon}`, { method: 'POST' });
                const report = await res.json();
                window.open(`/reports/download/${report.id}`, '_blank');
            }
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/index.py", response_class=HTMLResponse)
def serve_root():
    return HTMLResponse(content=get_html_dashboard())
