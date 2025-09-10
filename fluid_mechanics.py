import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from scipy import stats
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from io import BytesIO
import base64
import os
from datetime import datetime

class PitotTubeExperiment:
    """
    Fluid Mechanics: Pitot Tube - Determination of Velocity Coefficient (Cv)
    """
    
    # Standard constants (can be overridden by user)
    DEFAULT_CONSTANTS = {
        'Cd0': 0.62,  # Discharge coefficient
        'd0': 30,  # Orifice diameter in mm
        'D': 35,  # Pipe diameter in mm
        'rho_m': 1000,  # Density of manometer fluid (kg/m³)
        'rho': 1.2,  # Density of air (kg/m³)
        'g': 9.81,  # Gravity (m/s²)
        'sin25': 0.422,  # sin(25°)
        'sin15': 0.258  # sin(15°)
    }
    
    def __init__(self, constants=None):
        """Initialize with default or custom constants"""
        self.constants = self.DEFAULT_CONSTANTS.copy()
        if constants:
            self.constants.update(constants)
        
        # Calculate areas
        self.constants['Ao'] = np.pi * (self.constants['d0'] / 1000) ** 2 / 4  # m²
        self.constants['A'] = np.pi * (self.constants['D'] / 1000) ** 2 / 4  # m²
    
    def calculate_single_reading(self, l1o, l2o, l1p, l2p):
        """
        Calculate Ha0, Vo, Hap, Vp, and Cv for a single set of readings
        """
        # Extract constants
        sin25 = self.constants['sin25']
        sin15 = self.constants['sin15']
        rho_m = self.constants['rho_m']
        rho = self.constants['rho']
        g = self.constants['g']
        Cd0 = self.constants['Cd0']
        Ao = self.constants['Ao']
        A = self.constants['A']
        
        # Calculate Ha0 (Head at orifice)
        Ha0 = ((l2o - l1o) * sin25 * rho_m) / (100 * rho)
        
        # Ensure Ha0 is non-negative for velocity calculation
        if Ha0 < 0:
            Ha0 = 0
        
        # Calculate V0 (Velocity at orifice)
        V0 = (Cd0 * Ao * np.sqrt(2 * g * Ha0)) / A if Ha0 >= 0 else 0
        
        # Calculate Hap (Head at pitot tube)
        Hap = ((l2p - l1p) * sin15 * rho_m) / (100 * rho)
        
        # Ensure Hap is non-negative for velocity calculation
        if Hap < 0:
            Hap = 0
        
        # Calculate Vp (Velocity at pitot tube)
        Vp = np.sqrt(2 * g * Hap) if Hap >= 0 else 0
        
        # Calculate Cv (Velocity coefficient)
        Cv = V0 / Vp if Vp > 0 else 0
        
        return {
            'l1o': l1o,
            'l2o': l2o,
            'l1p': l1p,
            'l2p': l2p,
            'Ha0': Ha0,
            'V0': V0,
            'Hap': Hap,
            'Vp': Vp,
            'Cv': Cv
        }
    
    def process_multiple_readings(self, orifice_readings, pitot_readings):
        """
        Process multiple sets of readings
        
        Args:
            orifice_readings: List of tuples (l1o, l2o)
            pitot_readings: List of tuples (l1p, l2p)
        
        Returns:
            List of calculation results
        """
        results = []
        for (l1o, l2o), (l1p, l2p) in zip(orifice_readings, pitot_readings):
            result = self.calculate_single_reading(l1o, l2o, l1p, l2p)
            results.append(result)
        return results
    
    def get_model_calculation_text(self, result):
        """
        Generate step-by-step calculation text for the first reading
        """
        calc_text = f"""
Model Calculation for Reading 1:

Given:
- Orifice manometer readings: l<sub>1o</sub> = {result['l1o']} mm, l<sub>2o</sub> = {result['l2o']} mm
- Pitot tube manometer readings: l<sub>1p</sub> = {result['l1p']} mm, l<sub>2p</sub> = {result['l2p']} mm
- Constants: Cd<sub>0</sub> = {self.constants['Cd0']}, d<sub>0</sub> = {self.constants['d0']} mm, D = {self.constants['D']} mm
- &rho;<sub>m</sub> = {self.constants['rho_m']} kg/m&sup3;, &rho; = {self.constants['rho']} kg/m&sup3;, g = {self.constants['g']} m/s&sup2;

Step 1: Calculate areas
A<sub>o</sub> = &pi; &times; (d<sub>0</sub>/1000)&sup2; / 4 = &pi; &times; ({self.constants['d0']}/1000)&sup2; / 4 = {self.constants['Ao']:.6f} m&sup2;
A = &pi; &times; (D/1000)&sup2; / 4 = &pi; &times; ({self.constants['D']}/1000)&sup2; / 4 = {self.constants['A']:.6f} m&sup2;

Step 2: Calculate Ha<sub>0</sub> (Head at orifice)
Ha<sub>0</sub> = [(l<sub>2o</sub> - l<sub>1o</sub>) &times; sin25&deg; &times; &rho;<sub>m</sub>] / (100 &times; &rho;)
Ha<sub>0</sub> = [({result['l2o']} - {result['l1o']}) &times; {self.constants['sin25']} &times; {self.constants['rho_m']}] / (100 &times; {self.constants['rho']})
Ha<sub>0</sub> = [{result['l2o'] - result['l1o']} &times; {self.constants['sin25']} &times; {self.constants['rho_m']}] / {100 * self.constants['rho']}
Ha<sub>0</sub> = {result['Ha0']:.4f} m

Step 3: Calculate V<sub>0</sub> (Velocity at orifice)
V<sub>0</sub> = [Cd<sub>0</sub> &times; A<sub>o</sub> &times; &radic;(2 &times; g &times; Ha<sub>0</sub>)] / A
V<sub>0</sub> = [{self.constants['Cd0']} &times; {self.constants['Ao']:.6f} &times; &radic;(2 &times; {self.constants['g']} &times; {result['Ha0']:.4f})] / {self.constants['A']:.6f}
V<sub>0</sub> = {result['V0']:.4f} m/s

Step 4: Calculate Ha<sub>p</sub> (Head at pitot tube)
Ha<sub>p</sub> = [(l<sub>2p</sub> - l<sub>1p</sub>) &times; sin15&deg; &times; &rho;<sub>m</sub>] / (100 &times; &rho;)
Ha<sub>p</sub> = [({result['l2p']} - {result['l1p']}) &times; {self.constants['sin15']} &times; {self.constants['rho_m']}] / (100 &times; {self.constants['rho']})
Ha<sub>p</sub> = [{result['l2p'] - result['l1p']} &times; {self.constants['sin15']} &times; {self.constants['rho_m']}] / {100 * self.constants['rho']}
Ha<sub>p</sub> = {result['Hap']:.4f} m

Step 5: Calculate V<sub>p</sub> (Velocity at pitot tube)
V<sub>p</sub> = &radic;(2 &times; g &times; Ha<sub>p</sub>)
V<sub>p</sub> = &radic;(2 &times; {self.constants['g']} &times; {result['Hap']:.4f})
V<sub>p</sub> = {result['Vp']:.4f} m/s

Step 6: Calculate C<sub>v</sub> (Velocity coefficient)
C<sub>v</sub> = V<sub>0</sub> / V<sub>p</sub>
C<sub>v</sub> = {result['V0']:.4f} / {result['Vp']:.4f}
C<sub>v</sub> = {result['Cv']:.4f}
"""
        return calc_text
    
    def create_graph(self, results, x_param, y_param):
        """
        Create a graph between two specified parameters
        
        Args:
            results: List of calculation results
            x_param: Parameter for X-axis ('V0', 'Vp', 'Ha0', 'Hap')
            y_param: Parameter for Y-axis ('V0', 'Vp', 'Ha0', 'Hap')
        
        Returns:
            Base64 encoded image string
        """
        # Extract data
        x_data = np.array([r[x_param] for r in results])
        y_data = np.array([r[y_param] for r in results])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot data points
        ax.scatter(x_data, y_data, color='blue', s=100, label='Data points', zorder=5)
        
        # Calculate best-fit line
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
        line = slope * x_data + intercept
        
        # Plot best-fit line
        ax.plot(x_data, line, 'r-', label=f'Best fit: y = {slope:.4f}x + {intercept:.4f}', linewidth=2)
        
        # Labels and formatting
        param_labels = {
            'V0': 'V₀ (m/s)',
            'Vp': 'Vₚ (m/s)',
            'Ha0': 'Ha₀ (m)',
            'Hap': 'Haₚ (m)'
        }
        
        ax.set_xlabel(param_labels.get(x_param, x_param), fontsize=12)
        ax.set_ylabel(param_labels.get(y_param, y_param), fontsize=12)
        ax.set_title(f'Graph between {param_labels.get(x_param, x_param)} and {param_labels.get(y_param, y_param)}', fontsize=14, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add legend
        ax.legend()
        
        # Add slope annotation
        ax.text(0.05, 0.95, f'Slope: {slope:.4f}\nR² = {r_value**2:.4f}', 
                transform=ax.transAxes, fontsize=11,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def generate_report_html(self, results, graph_base64, model_calc_text, mean_cv):
        """
        Generate HTML report
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pitot Tube Experiment Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; text-align: center; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
                th {{ background-color: #3498db; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .model-calc {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }}
                .graph-container {{ text-align: center; margin: 30px 0; }}
                .summary {{ background-color: #e8f5e9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .header-info {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <h1>Pitot Tube - Determination of Velocity Coefficient (Cᵥ)</h1>
            <div class="header-info">
                <p>Fluid Mechanics Laboratory Experiment</p>
                <p>Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</p>
            </div>
            
            <h2>Experimental Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Reading</th>
                        <th>l₁o (mm)</th>
                        <th>l₂o (mm)</th>
                        <th>l₁p (mm)</th>
                        <th>l₂p (mm)</th>
                        <th>Ha₀ (m)</th>
                        <th>V₀ (m/s)</th>
                        <th>Haₚ (m)</th>
                        <th>Vₚ (m/s)</th>
                        <th>Cᵥ</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i, result in enumerate(results, 1):
            html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{result['l1o']:.1f}</td>
                        <td>{result['l2o']:.1f}</td>
                        <td>{result['l1p']:.1f}</td>
                        <td>{result['l2p']:.1f}</td>
                        <td>{result['Ha0']:.4f}</td>
                        <td>{result['V0']:.4f}</td>
                        <td>{result['Hap']:.4f}</td>
                        <td>{result['Vp']:.4f}</td>
                        <td>{result['Cv']:.4f}</td>
                    </tr>
            """
        
        html_content += f"""
                </tbody>
            </table>
            
            <div class="summary">
                <h3>Summary</h3>
                <p><strong>Mean Velocity Coefficient (Cᵥ): {mean_cv:.4f}</strong></p>
                <p>Number of readings: {len(results)}</p>
            </div>
            
            <h2>Model Calculation (Reading 1)</h2>
            <div class="model-calc">{model_calc_text}</div>
            
            <h2>Graph</h2>
            <div class="graph-container">
                <img src="data:image/png;base64,{graph_base64}" alt="Experimental Graph" style="max-width: 100%; height: auto;">
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_pdf_report(self, results, graph_base64, model_calc_text, mean_cv, filename=None):
        """
        Generate PDF report using ReportLab
        
        Args:
            results: List of calculation results
            graph_base64: Base64 encoded graph image
            model_calc_text: Model calculation text
            mean_cv: Mean velocity coefficient
            filename: Optional filename for the PDF
        
        Returns:
            BytesIO object containing the PDF
        """
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        import io
        
        # Create BytesIO buffer for PDF
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Pitot Tube - Determination of Velocity Coefficient (C<sub>v</sub>)", title_style))
        story.append(Paragraph("Fluid Mechanics Laboratory Experiment", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Summary
        story.append(Paragraph("Summary", heading_style))
        story.append(Paragraph(f"Mean Velocity Coefficient (C<sub>v</sub>): <b>{mean_cv:.4f}</b>", normal_style))
        story.append(Paragraph(f"Number of readings: {len(results)}", normal_style))
        story.append(Spacer(1, 12))
        
        # Results table
        story.append(Paragraph("Experimental Results", heading_style))
        
        # Create table data
        table_data = [['Reading', 'l<sub>1o</sub> (mm)', 'l<sub>2o</sub> (mm)', 'l<sub>1p</sub> (mm)', 'l<sub>2p</sub> (mm)', 
                      'Ha<sub>0</sub> (m)', 'V<sub>0</sub> (m/s)', 'Ha<sub>p</sub> (m)', 'V<sub>p</sub> (m/s)', 'C<sub>v</sub>']]
        
        for i, result in enumerate(results):
            table_data.append([
                str(i + 1),
                f"{result['l1o']:.1f}",
                f"{result['l2o']:.1f}",
                f"{result['l1p']:.1f}",
                f"{result['l2p']:.1f}",
                f"{result['Ha0']:.4f}",
                f"{result['V0']:.4f}",
                f"{result['Hap']:.4f}",
                f"{result['Vp']:.4f}",
                f"{result['Cv']:.4f}"
            ])
        
        # Create table
        table = Table(table_data, colWidths=[0.6*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch,
                                           0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.6*inch])
        
        # Style the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Graph
        if graph_base64:
            story.append(Paragraph("Graph", heading_style))
            try:
                # Decode base64 image
                image_data = base64.b64decode(graph_base64)
                img_buffer = BytesIO(image_data)
                
                # Create ReportLab Image
                img = Image(img_buffer, width=6*inch, height=3.6*inch)
                story.append(img)
                story.append(Spacer(1, 20))
            except Exception as e:
                story.append(Paragraph(f"Graph could not be included: {str(e)}", normal_style))
        
        # Model calculation
        if model_calc_text:
            story.append(Paragraph("Model Calculation", heading_style))
            # Split model calculation into paragraphs
            calc_lines = model_calc_text.strip().split('\n')
            for line in calc_lines:
                if line.strip():
                    story.append(Paragraph(line.strip(), normal_style))
                else:
                    story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        
        # Reset buffer position
        buffer.seek(0)
        return buffer

def process_experiment_data(orifice_readings, pitot_readings, graph_params=('V0', 'Vp'), custom_constants=None):
    """
    Main function to process the experiment data
    
    Args:
        orifice_readings: List of tuples (l1o, l2o)
        pitot_readings: List of tuples (l1p, l2p)
        graph_params: Tuple of (x_param, y_param) for graphing
        custom_constants: Dict of custom constants (optional)
    
    Returns:
        Dict containing all results and generated files
    """
    import math
    
    # Helper function to clean NaN and Inf values
    def clean_value(value):
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return 0.0
        return value
    
    def clean_dict(d):
        return {k: clean_value(v) for k, v in d.items()}
    
    # Initialize experiment
    experiment = PitotTubeExperiment(custom_constants)
    
    # Process readings
    results = experiment.process_multiple_readings(orifice_readings, pitot_readings)
    
    # Clean results to remove NaN/Inf values
    results = [clean_dict(r) for r in results]
    
    # Calculate mean Cv (excluding zeros)
    cv_values = [r['Cv'] for r in results if r['Cv'] > 0]
    mean_cv = np.mean(cv_values) if cv_values else 0
    mean_cv = clean_value(mean_cv)
    
    # Generate model calculation text
    model_calc_text = experiment.get_model_calculation_text(results[0]) if results else ""
    
    # Create graph only if we have valid data
    try:
        graph_base64 = experiment.create_graph(results, graph_params[0], graph_params[1])
    except Exception as e:
        # If graph creation fails, create a simple placeholder
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Invalid data for graph generation', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)
        ax.set_title('Graph could not be generated')
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        graph_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
    
    # Generate PDF report
    pdf_buffer = experiment.generate_pdf_report(results, graph_base64, model_calc_text, mean_cv)
    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()
    
    return {
        'results': results,
        'mean_cv': mean_cv,
        'model_calculation': model_calc_text,
        'graph_base64': graph_base64,
        'pdf_base64': pdf_base64,
        'graph_params': graph_params
    }