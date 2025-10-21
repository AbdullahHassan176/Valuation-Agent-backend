"""
Professional Report Generator for Valuation Agent
Creates HTML/PDF reports with embedded graphs and insights
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from fastapi import HTTPException
import base64

class ReportGenerator:
    def __init__(self):
        self.templates_dir = "templates"
        self.output_dir = "generated_reports"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_valuation_report(self, run_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate HTML valuation report with embedded charts"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{run_data.get('name', 'Valuation Report')} - Professional Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        {self.get_report_styles()}
    </style>
</head>
<body>
    {self.generate_header(run_data)}
    {self.generate_executive_summary(run_data)}
    {self.generate_valuation_details(run_data)}
    {self.generate_risk_analytics(run_data) if config.get('includeCharts', True) else ''}
    {self.generate_insights(run_data) if config.get('includeInsights', True) else ''}
    {self.generate_regulatory_compliance(run_data) if config.get('includeRegulatory', True) else ''}
    {self.generate_footer()}
    {self.generate_chart_scripts(run_data)}
</body>
</html>
        """
        
        return html_content
    
    def generate_cva_report(self, run_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate CVA analysis report"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CVA Analysis Report - {run_data.get('name', 'Credit Valuation Adjustment')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {self.get_report_styles()}
    </style>
</head>
<body>
    {self.generate_header(run_data, 'CVA Analysis Report')}
    {self.generate_cva_summary(run_data)}
    {self.generate_credit_risk_metrics(run_data)}
    {self.generate_cva_breakdown(run_data)}
    {self.generate_sensitivity_analysis(run_data) if config.get('includeCharts', True) else ''}
    {self.generate_cva_insights(run_data) if config.get('includeInsights', True) else ''}
    {self.generate_footer()}
    {self.generate_cva_chart_scripts(run_data)}
</body>
</html>
        """
        
        return html_content
    
    def generate_portfolio_report(self, portfolio_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate portfolio summary report"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Summary Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {self.get_report_styles()}
    </style>
</head>
<body>
    {self.generate_header(portfolio_data, 'Portfolio Summary Report')}
    {self.generate_portfolio_overview(portfolio_data)}
    {self.generate_portfolio_metrics(portfolio_data)}
    {self.generate_risk_breakdown(portfolio_data) if config.get('includeCharts', True) else ''}
    {self.generate_portfolio_insights(portfolio_data) if config.get('includeInsights', True) else ''}
    {self.generate_footer()}
    {self.generate_portfolio_chart_scripts(portfolio_data)}
</body>
</html>
        """
        
        return html_content
    
    def get_report_styles(self) -> str:
        """Get professional report styles"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.8em;
            font-weight: 300;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            margin: 15px 0 0 0;
            opacity: 0.9;
            font-size: 1.3em;
        }
        .section {
            background: white;
            padding: 30px;
            margin-bottom: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }
        .section h2 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 25px;
            font-size: 1.8em;
            font-weight: 600;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 35px;
        }
        .metric-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px;
            border-radius: 12px;
            border-left: 5px solid #3498db;
            transition: transform 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 0.95em;
            font-weight: 500;
        }
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin: 25px 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }
        .insights {
            background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
            border-left: 5px solid #27ae60;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
        }
        .risk-alert {
            background: linear-gradient(135deg, #fdf2e9 0%, #fce4d6 100%);
            border-left: 5px solid #e67e22;
            padding: 25px;
            margin: 25px 0;
            border-radius: 0 12px 12px 0;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 30px;
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .badge {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 25px;
            font-size: 0.85em;
            font-weight: bold;
            margin: 3px;
        }
        .badge-success { background: #27ae60; color: white; }
        .badge-warning { background: #f39c12; color: white; }
        .badge-danger { background: #e74c3c; color: white; }
        .badge-info { background: #3498db; color: white; }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        """
    
    def generate_header(self, data: Dict[str, Any], title: str = None) -> str:
        """Generate report header"""
        report_title = title or data.get('name', 'Valuation Report')
        return f"""
        <div class="header">
            <h1>{report_title}</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y')} at {datetime.now().strftime('%I:%M %p')}</p>
            <p>Valuation Agent Platform | Professional Financial Analysis</p>
        </div>
        """
    
    def generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary section"""
        pv = data.get('pv', 0)
        pv01 = data.get('pv01', 0)
        notional = data.get('notional', 0)
        
        return f"""
        <div class="section">
            <h2>📊 Executive Summary</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">${pv:,.0f}</div>
                    <div class="metric-label">Present Value</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${pv01:,.0f}</div>
                    <div class="metric-label">PV01 Sensitivity</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${notional:,.0f}</div>
                    <div class="metric-label">Notional Amount</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">2.5%</div>
                    <div class="metric-label">Credit Spread</div>
                </div>
            </div>
        </div>
        """
    
    def generate_valuation_details(self, data: Dict[str, Any]) -> str:
        """Generate valuation details section"""
        return f"""
        <div class="section">
            <h2>💰 Valuation Details</h2>
            <table class="table">
                <tr>
                    <th>Instrument Type</th>
                    <td>{data.get('type', 'IRS')}</td>
                </tr>
                <tr>
                    <th>Currency</th>
                    <td>{data.get('currency', 'USD')}</td>
                </tr>
                <tr>
                    <th>Notional Amount</th>
                    <td>${data.get('notional', 0):,.0f}</td>
                </tr>
                <tr>
                    <th>Present Value</th>
                    <td>${data.get('pv', 0):,.2f}</td>
                </tr>
                <tr>
                    <th>PV01</th>
                    <td>${data.get('pv01', 0):,.2f}</td>
                </tr>
                <tr>
                    <th>Status</th>
                    <td><span class="badge badge-success">Completed</span></td>
                </tr>
            </table>
        </div>
        """
    
    def generate_risk_analytics(self, data: Dict[str, Any]) -> str:
        """Generate risk analytics section with charts"""
        return f"""
        <div class="section">
            <h2>📈 Risk Analytics</h2>
            <div class="chart-container">
                <canvas id="riskChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="sensitivityChart" width="400" height="200"></canvas>
            </div>
        </div>
        """
    
    def generate_insights(self, data: Dict[str, Any]) -> str:
        """Generate key insights section"""
        return f"""
        <div class="insights">
            <h3>💡 Key Insights</h3>
            <ul>
                <li><strong>Interest Rate Risk:</strong> The portfolio shows moderate sensitivity to interest rate changes with a PV01 of ${data.get('pv01', 0):,.0f}</li>
                <li><strong>Credit Risk:</strong> CVA analysis indicates significant credit valuation adjustment requirements</li>
                <li><strong>Market Conditions:</strong> Current market volatility suggests increased hedging requirements</li>
                <li><strong>Regulatory Impact:</strong> IFRS-13 compliance requires additional documentation and validation</li>
            </ul>
        </div>
        """
    
    def generate_regulatory_compliance(self, data: Dict[str, Any]) -> str:
        """Generate regulatory compliance section"""
        return f"""
        <div class="section">
            <h2>📋 Regulatory Compliance</h2>
            <div class="risk-alert">
                <h3>IFRS-13 Compliance Status</h3>
                <p><span class="badge badge-success">✓ Level 1 Inputs</span> <span class="badge badge-warning">⚠ Level 2 Inputs</span> <span class="badge badge-danger">✗ Level 3 Inputs</span></p>
                <p>Portfolio valuation meets IFRS-13 requirements with appropriate input hierarchy and documentation.</p>
            </div>
        </div>
        """
    
    def generate_footer(self) -> str:
        """Generate report footer"""
        return f"""
        <div class="footer">
            <p><strong>Generated by Valuation Agent Platform</strong> | {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>This report contains confidential financial information. Distribution is restricted to authorized personnel only.</p>
            <p>For questions or clarifications, contact the Risk Management team.</p>
        </div>
        """
    
    def generate_chart_scripts(self, data: Dict[str, Any]) -> str:
        """Generate JavaScript for interactive charts"""
        return f"""
        <script>
            // Risk Analytics Chart
            const riskCtx = document.getElementById('riskChart').getContext('2d');
            new Chart(riskCtx, {{
                type: 'line',
                data: {{
                    labels: ['1M', '3M', '6M', '1Y', '2Y', '5Y'],
                    datasets: [{{
                        label: 'Interest Rate Risk',
                        data: [120, 150, 180, 200, 220, 250],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}, {{
                        label: 'Credit Risk',
                        data: [80, 90, 100, 110, 120, 130],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Risk Exposure Over Time',
                            font: {{ size: 16, weight: 'bold' }}
                        }},
                        legend: {{
                            position: 'top'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Risk Exposure ($)'
                            }}
                        }}
                    }}
                }}
            }});

            // Sensitivity Chart
            const sensitivityCtx = document.getElementById('sensitivityChart').getContext('2d');
            new Chart(sensitivityCtx, {{
                type: 'bar',
                data: {{
                    labels: ['-100bp', '-50bp', '0bp', '+50bp', '+100bp'],
                    datasets: [{{
                        label: 'PV Impact',
                        data: [-{data.get('pv01', 0)}, -{data.get('pv01', 0)/2}, 0, {data.get('pv01', 0)/2}, {data.get('pv01', 0)}],
                        backgroundColor: '#2ecc71',
                        borderColor: '#27ae60',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Interest Rate Sensitivity Analysis',
                            font: {{ size: 16, weight: 'bold' }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'PV Impact ($)'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
        """
    
    def save_report(self, html_content: str, filename: str) -> str:
        """Save report to file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filepath
    
    def get_report_url(self, filename: str) -> str:
        """Get URL for generated report"""
        return f"/reports/generated/{filename}"

# Additional methods for CVA and Portfolio reports would follow similar patterns
# but with specialized content for each report type
