import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models import User, Calculation, ActivityLog, Experiment, ChatMessage
from chemical_database import CHEMICAL_DATABASE, calculate_reagent
from fluid_mechanics import process_experiment_data
from enhanced_chatbot import enhanced_chatbot
from pubchem_fetcher import fetch_chemical_data
from enhanced_chemical_database import get_chemical_data, search_chemicals, get_chemical_properties_summary, calculate_reagent_enhanced
from chemllm_integration import chemllm, is_chemllm_available, generate_chemllm_response, get_chemllm_info

def log_activity(user_id, action_type, description):
    """Helper function to log user activities"""
    activity = ActivityLog(
        user_id=user_id,
        action_type=action_type,
        description=description
    )
    db.session.add(activity)
    db.session.commit()

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('frontpage.html')
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        institution = request.form.get('institution', '')
        
        # Create or get user
        user = User.query.filter_by(name=name, role=role).first()
        if not user:
            user = User(name=name, role=role, institution=institution)
            db.session.add(user)
            db.session.commit()
        
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_role'] = user.role
        
        log_activity(user.id, 'Authentication', f'User {user.name} ({user.role}) logged in')
        
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_activity(session['user_id'], 'Authentication', f'User {session["user_name"]} logged out')
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get recent calculations
    recent_calculations = Calculation.query.filter_by(user_id=user_id).order_by(Calculation.created_at.desc()).limit(5).all()
    
    # Get recent activities
    recent_activities = ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).limit(5).all()
    
    # Get statistics
    total_calculations = Calculation.query.filter_by(user_id=user_id).count()
    total_activities = ActivityLog.query.filter_by(user_id=user_id).count()
    
    return render_template('dashboard.html', 
                         recent_calculations=recent_calculations,
                         recent_activities=recent_activities,
                         total_calculations=total_calculations,
                         total_activities=total_activities)

@app.route('/calculator')
def calculator():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user wants fluid mechanics calculator
    calc_type = request.args.get('type', 'chemistry')
    if calc_type == 'fluid':
        return render_template('fluid_calculator.html')
    return render_template('calculator.html', chemicals=CHEMICAL_DATABASE)

@app.route('/unit_converter')
def unit_converter():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('unit_converter.html')

@app.route('/fluid_calculate', methods=['POST'])
def fluid_calculate():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        data = request.get_json()
        
        # Parse input data
        orifice_readings = data.get('orifice_readings', [])
        pitot_readings = data.get('pitot_readings', [])
        graph_params = data.get('graph_params', ['V0', 'Vp'])
        custom_constants = data.get('constants', None)
        
        # Validate input data
        if not orifice_readings or not pitot_readings:
            return jsonify({'success': False, 'error': 'No readings provided'}), 400
        
        if len(orifice_readings) != len(pitot_readings):
            return jsonify({'success': False, 'error': 'Mismatched number of orifice and pitot readings'}), 400
        
        # Convert readings to float tuples and validate
        try:
            orifice_readings = [(float(r[0]), float(r[1])) for r in orifice_readings]
            pitot_readings = [(float(r[0]), float(r[1])) for r in pitot_readings]
        except (ValueError, TypeError, IndexError) as e:
            return jsonify({'success': False, 'error': 'Invalid reading format. All values must be numbers.'}), 400
        
        # Process experiment data
        result = process_experiment_data(
            orifice_readings,
            pitot_readings,
            tuple(graph_params),
            custom_constants
        )
        
        # Log activity
        log_activity(session['user_id'], 'Fluid Calculation', 
                    f'Pitot Tube experiment with {len(orifice_readings)} readings')
        
        # Create a simple calculation record
        calculation = Calculation(
            user_id=session['user_id'],
            reagent='Pitot Tube Experiment',
            formula='Cv = V0/Vp',
            molarity=0,  # Not applicable for fluid mechanics
            volume=0,  # Not applicable  
            mass_needed=result['mean_cv']  # Store mean Cv here
        )
        db.session.add(calculation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': result['results'],
            'mean_cv': result['mean_cv'],
            'model_calculation': result['model_calculation'],
            'graph_base64': result['graph_base64'],
            'pdf_base64': result['pdf_base64']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        data = request.get_json()
        pdf_base64 = data.get('pdf_base64')
        
        if not pdf_base64:
            return jsonify({'success': False, 'error': 'No PDF data provided'}), 400
        
        # Decode base64 PDF
        import base64
        pdf_data = base64.b64decode(pdf_base64)
        
        # Create response
        from flask import make_response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=pitot_tube_report_{datetime.now().strftime("%d%m%Y_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_calculations_pdf')
def export_calculations_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        import base64
        
        # Get user's calculations
        calculations = Calculation.query.filter_by(user_id=session['user_id']).order_by(Calculation.created_at.desc()).all()
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        story = []
        story.append(Paragraph("LabMateAI - Calculations Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"User: {session.get('user_name', 'Unknown')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        if calculations:
            # Create calculations table
            table_data = [['Date', 'Reagent', 'Formula', 'Molarity (M)', 'Volume (mL)', 'Mass Needed (g)']]
            
            for calc in calculations:
                table_data.append([
                    calc.created_at.strftime('%d-%m-%Y %H:%M'),
                    calc.reagent,
                    calc.formula or 'N/A',
                    f"{calc.molarity:.2f}" if calc.molarity else 'N/A',
                    f"{calc.volume:.2f}" if calc.volume else 'N/A',
                    f"{calc.mass_needed:.4f}" if calc.mass_needed else 'N/A'
                ])
            
            table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch])
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
        else:
            story.append(Paragraph("No calculations found.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        # Create response
        from flask import make_response
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=calculations_report_{datetime.now().strftime("%d%m%Y_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_lab_report_pdf')
def export_lab_report_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        
        # Get user's experiments
        experiments = Experiment.query.filter_by(user_id=session['user_id']).order_by(Experiment.created_at.desc()).all()
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        story = []
        story.append(Paragraph("LabMateAI - Laboratory Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"User: {session.get('user_name', 'Unknown')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        if experiments:
            for i, exp in enumerate(experiments):
                story.append(Paragraph(f"<b>Experiment {i+1}: {exp.title}</b>", styles['Heading2']))
                story.append(Paragraph(f"<b>Date:</b> {exp.created_at.strftime('%d-%m-%Y %H:%M')}", styles['Normal']))
                
                if exp.description:
                    story.append(Paragraph(f"<b>Description:</b> {exp.description}", styles['Normal']))
                
                if exp.procedures:
                    story.append(Paragraph(f"<b>Procedures:</b> {exp.procedures}", styles['Normal']))
                
                if exp.observations:
                    story.append(Paragraph(f"<b>Observations:</b> {exp.observations}", styles['Normal']))
                
                if exp.results:
                    story.append(Paragraph(f"<b>Results:</b> {exp.results}", styles['Normal']))
                
                story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("No experiments found.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        # Create response
        from flask import make_response
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=lab_report_{datetime.now().strftime("%d%m%Y_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_current_experiment_pdf')
def export_current_experiment_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        
        # Get latest experiment
        latest_experiment = Experiment.query.filter_by(user_id=session['user_id']).order_by(Experiment.created_at.desc()).first()
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        story = []
        story.append(Paragraph("LabMateAI - Current Experiment Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"User: {session.get('user_name', 'Unknown')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        if latest_experiment:
            story.append(Paragraph(f"<b>Experiment Title:</b> {latest_experiment.title}", styles['Heading2']))
            story.append(Paragraph(f"<b>Date:</b> {latest_experiment.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            
            if latest_experiment.description:
                story.append(Paragraph(f"<b>Description:</b> {latest_experiment.description}", styles['Normal']))
            
            if latest_experiment.procedures:
                story.append(Paragraph(f"<b>Procedures:</b> {latest_experiment.procedures}", styles['Normal']))
            
            if latest_experiment.observations:
                story.append(Paragraph(f"<b>Observations:</b> {latest_experiment.observations}", styles['Normal']))
            
            if latest_experiment.results:
                story.append(Paragraph(f"<b>Results:</b> {latest_experiment.results}", styles['Normal']))
        else:
            story.append(Paragraph("No current experiment found.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        # Create response
        from flask import make_response
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=current_experiment_{datetime.now().strftime("%d%m%Y_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_experiment_pdf/<int:experiment_id>')
def export_experiment_pdf(experiment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        
        # Get specific experiment
        experiment = Experiment.query.filter_by(id=experiment_id, user_id=session['user_id']).first()
        
        if not experiment:
            return jsonify({'success': False, 'error': 'Experiment not found'}), 404
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        story = []
        story.append(Paragraph("LabMateAI - Experiment Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"User: {session.get('user_name', 'Unknown')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph(f"<b>Experiment Title:</b> {experiment.title}", styles['Heading2']))
        story.append(Paragraph(f"<b>Date:</b> {experiment.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        
        if experiment.description:
            story.append(Paragraph(f"<b>Description:</b> {experiment.description}", styles['Normal']))
        
        if experiment.procedures:
            story.append(Paragraph(f"<b>Procedures:</b> {experiment.procedures}", styles['Normal']))
        
        if experiment.observations:
            story.append(Paragraph(f"<b>Observations:</b> {experiment.observations}", styles['Normal']))
        
        if experiment.results:
            story.append(Paragraph(f"<b>Results:</b> {experiment.results}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        # Create response
        from flask import make_response
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=experiment_{experiment_id}_{datetime.now().strftime("%d%m%Y_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_activity_logs_pdf')
def export_activity_logs_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        
        # Get user's activity logs
        activities = ActivityLog.query.filter_by(user_id=session['user_id']).order_by(ActivityLog.timestamp.desc()).all()
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        story = []
        story.append(Paragraph("LabMateAI - Activity Logs Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"User: {session.get('user_name', 'Unknown')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        if activities:
            # Create activity logs table
            table_data = [['Timestamp', 'Action Type', 'Description']]
            
            for activity in activities:
                table_data.append([
                    activity.timestamp.strftime('%d-%m-%Y %H:%M:%S'),
                    activity.action_type,
                    activity.description
                ])
            
            table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 3.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            story.append(table)
            
            # Add summary statistics
            story.append(Spacer(1, 20))
            story.append(Paragraph("Summary Statistics", styles['Heading2']))
            
            # Count activities by type
            action_counts = {}
            for activity in activities:
                action_type = activity.action_type
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            summary_data = [['Action Type', 'Count']]
            for action_type, count in action_counts.items():
                summary_data.append([action_type, str(count)])
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
        else:
            story.append(Paragraph("No activity logs found.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        # Create response
        from flask import make_response
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=activity_logs_{datetime.now().strftime("%d%m%Y_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/delete_experiment/<int:experiment_id>', methods=['DELETE'])
def delete_experiment(experiment_id):
    """Delete an experiment"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Find the experiment
        experiment = Experiment.query.filter_by(id=experiment_id, user_id=session['user_id']).first()
        
        if not experiment:
            return jsonify({'success': False, 'error': 'Experiment not found'}), 404
        
        # Store experiment title for logging
        experiment_title = experiment.title
        
        # Delete the experiment
        db.session.delete(experiment)
        db.session.commit()
        
        # Log the deletion
        log_activity(session['user_id'], 'Experiment Deletion', 
                    f'Deleted experiment: {experiment_title}')
        
        return jsonify({
            'success': True,
            'message': f'Experiment "{experiment_title}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/calculate', methods=['POST'])
def calculate():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    data = request.get_json() if request.is_json else request.form
    reagent = data.get('reagent')
    molarity = float(data.get('molarity', 0))
    volume = float(data.get('volume', 0))
    
    if reagent in CHEMICAL_DATABASE:
        result = calculate_reagent(reagent, molarity, volume)
        
        # Save calculation
        calculation = Calculation(
            user_id=session['user_id'],
            reagent=reagent,
            formula=CHEMICAL_DATABASE[reagent]['formula'],
            molarity=molarity,
            volume=volume,
            mass_needed=result['mass_needed']
        )
        db.session.add(calculation)
        db.session.commit()
        
        log_activity(session['user_id'], 'Calculation', 
                    f'Calculated {reagent}: {result["mass_needed"]:.2f}g for {molarity}M in {volume}mL')
        
        if request.is_json:
            return jsonify(result)
        else:
            flash(f'Calculation complete: {result["mass_needed"]:.2f}g of {reagent} needed')
            return redirect(url_for('calculator'))
    
    error = {'error': 'Chemical not found in database'}
    if request.is_json:
        return jsonify(error), 400
    else:
        flash('Chemical not found in database')
        return redirect(url_for('calculator'))

@app.route('/msds')
def msds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('msds.html', chemicals=CHEMICAL_DATABASE)

@app.route('/msds_search')
def msds_search():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').lower()
    use_gemini = request.args.get('gemini', 'false').lower() == 'true'
    results = []
    
    if query:
        # First search local database
        for name, data in CHEMICAL_DATABASE.items():
            if query in name.lower() or query in data.get('formula', '').lower():
                results.append({
                    'name': name,
                    'formula': data.get('formula', ''),
                    'molar_mass': data.get('molar_mass', 0),
                    'hazards': data.get('hazards', []),
                    'source': 'local'
                })
        
        # If Gemini is requested and no local results found, use Gemini
        if use_gemini and len(results) == 0:
            try:
                gemini_result = _search_msds_with_gemini(query)
                if gemini_result:
                    results.append(gemini_result)
            except Exception as e:
                print(f"Error with Gemini search: {e}")
                # Continue without Gemini result
        
        log_activity(session['user_id'], 'MSDS Lookup', f'Searched MSDS for: {query} (Gemini: {use_gemini})')
    
    return jsonify(results)

def _search_msds_with_gemini(query):
    """Search MSDS information using Gemini API"""
    try:
        import google.generativeai as genai
        import os
        
        api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyCeo5U96gMxO1h248cPdLG46l-wWQbQQUU')
        if not api_key:
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Provide comprehensive MSDS (Material Safety Data Sheet) information for the chemical: {query}
        
        Focus on SAFETY and HAZARD information first, then provide additional chemical details.
        
        Please provide the following information in JSON format:
        {{
            "name": "Chemical name",
            "formula": "Chemical formula", 
            "molar_mass": "Molar mass in g/mol",
            "hazards": ["List of primary hazards - prioritize safety warnings"],
            "safety_precautions": ["Critical safety precautions and handling procedures"],
            "first_aid": ["Emergency first aid measures"],
            "storage_requirements": ["Safe storage conditions and requirements"],
            "disposal_methods": ["Proper disposal procedures"],
            "health_effects": ["Health effects and symptoms of exposure"],
            "fire_fighting": ["Fire fighting measures and extinguishing agents"],
            "spill_procedures": ["Spill cleanup procedures"],
            "personal_protection": ["Required personal protective equipment"],
            "source": "gemini"
        }}
        
        Prioritize safety information and MSDS-specific data. If the chemical is not found or you're unsure, return null.
        """
        
        response = model.generate_content(prompt)
        
        # Try to parse JSON response
        import json
        try:
            # Extract JSON from response text
            response_text = response.text
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_text = response_text[json_start:json_end]
            else:
                return None
                
            result = json.loads(json_text)
            return result
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic response
            return {
                "name": query.title(),
                "formula": "Unknown",
                "molar_mass": 0,
                "hazards": ["Unknown hazards - consult official MSDS"],
                "safety_precautions": ["Use standard laboratory safety practices"],
                "first_aid": ["Consult medical professional"],
                "storage_requirements": ["Store according to standard laboratory protocols"],
                "disposal_methods": ["Follow local regulations"],
                "source": "gemini"
            }
            
    except Exception as e:
        print(f"Error with Gemini MSDS search: {e}")
        return None

@app.route('/msds_enhanced_search', methods=['POST'])
def msds_enhanced_search():
    """Enhanced MSDS search with Gemini AI integration"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        use_gemini = data.get('use_gemini', True)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        results = []
        
        # Search local database first
        for name, data in CHEMICAL_DATABASE.items():
            if query.lower() in name.lower() or query.lower() in data.get('formula', '').lower():
                results.append({
                    'name': name,
                    'formula': data.get('formula', ''),
                    'molar_mass': data.get('molar_mass', 0),
                    'hazards': data.get('hazards', []),
                    'source': 'local'
                })
        
        # If Gemini is enabled and no local results, or if specifically requested
        if use_gemini and (len(results) == 0 or data.get('force_gemini', False)):
            gemini_result = _search_msds_with_gemini(query)
            if gemini_result:
                results.append(gemini_result)
        
        # Log activity
        log_activity(session['user_id'], 'Enhanced MSDS Search', 
                    f'Searched for: {query} (Gemini: {use_gemini}, Results: {len(results)})')
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results),
            'gemini_used': use_gemini
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/safety')
def safety():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('safety.html')

@app.route('/documentation')
def documentation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    experiments = Experiment.query.filter_by(user_id=session['user_id']).order_by(Experiment.created_at.desc()).all()
    return render_template('documentation.html', experiments=experiments)

@app.route('/new_experiment', methods=['GET', 'POST'])
def new_experiment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        experiment = Experiment(
            user_id=session['user_id'],
            title=request.form['title'],
            description=request.form.get('description', ''),
            procedures=request.form.get('procedures', ''),
            observations=request.form.get('observations', ''),
            results=request.form.get('results', '')
        )
        db.session.add(experiment)
        db.session.commit()
        
        log_activity(session['user_id'], 'Experiment', f'Created new experiment: {experiment.title}')
        flash('Experiment log created successfully!')
        return redirect(url_for('documentation'))
    
    return render_template('new_experiment.html')

@app.route('/activity_logs')
def activity_logs():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    action_type = request.args.get('action_type', '')
    date_filter = request.args.get('date', '')
    
    # Build query with filters
    query = ActivityLog.query.filter_by(user_id=session['user_id'])
    
    if search:
        query = query.filter(ActivityLog.description.contains(search))
    
    if action_type:
        query = query.filter(ActivityLog.action_type == action_type)
    
    if date_filter:
        from datetime import datetime
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(db.func.date(ActivityLog.timestamp) == filter_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    activities = query.order_by(ActivityLog.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('activity_logs.html', activities=activities, 
                         search=search, action_type=action_type, date_filter=date_filter)

# Chatbot page removed - using floating widget only

@app.route('/chatbot/send', methods=['POST'])
def send_chat_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Process message with enhanced chatbot
        bot_response = enhanced_chatbot.process_message(user_message, session['user_id'], db)
        
        # Save conversation to database
        enhanced_chatbot.save_conversation(session['user_id'], user_message, bot_response, db)
        
        # Log activity
        log_activity(session['user_id'], 'Chatbot', f'Asked: {user_message[:50]}...')
        
        return jsonify({
            'success': True,
            'response': bot_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chatbot/history')
def get_chat_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        messages = ChatMessage.query.filter_by(user_id=session['user_id']).order_by(ChatMessage.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        chat_history = []
        for msg in messages.items:
            chat_history.append({
                'id': msg.id,
                'message': msg.message,
                'response': msg.response,
                'is_user_message': msg.is_user_message,
                'timestamp': msg.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'messages': chat_history,
            'has_next': messages.has_next,
            'has_prev': messages.has_prev,
            'page': page,
            'pages': messages.pages
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chatbot/clear', methods=['POST'])
def clear_chat_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Delete all chat messages for this user
        ChatMessage.query.filter_by(user_id=session['user_id']).delete()
        db.session.commit()
        
        # Log activity
        log_activity(session['user_id'], 'Chatbot', 'Cleared chat history')
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/pubchem/fetch', methods=['POST'])
def fetch_pubchem_data():
    """
    Fetch chemical data from PubChem API
    
    Expected JSON payload:
    {
        "chemical_name": "water"
    }
    
    Returns structured JSON with chemical properties
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        chemical_name = data.get('chemical_name', '').strip()
        
        if not chemical_name:
            return jsonify({'error': 'Chemical name is required'}), 400
        
        # Fetch data from PubChem
        result = fetch_chemical_data(chemical_name)
        
        # Log activity
        if result['status'] == 'success':
            log_activity(session['user_id'], 'PubChem Lookup', 
                        f'Fetched data for: {chemical_name} (CID: {result.get("pubchem_cid", "N/A")})')
        else:
            log_activity(session['user_id'], 'PubChem Lookup', 
                        f'Failed to fetch data for: {chemical_name} - {result.get("error_message", "Unknown error")}')
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/pubchem/test')
def pubchem_test():
    """Test page for PubChem functionality"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('pubchem_test.html')

@app.route('/chemical/enhanced_search', methods=['POST'])
def enhanced_chemical_search():
    """
    Enhanced chemical search across all databases
    
    Expected JSON payload:
    {
        "query": "metal"
    }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search across all databases
        results = search_chemicals(query)
        
        # Log activity
        log_activity(session['user_id'], 'Chemical Search', 
                    f'Searched for: {query} (found {len(results)} results)')
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chemical/enhanced_data', methods=['POST'])
def enhanced_chemical_data():
    """
    Get enhanced chemical data from all sources
    
    Expected JSON payload:
    {
        "chemical_name": "water",
        "use_pubchem": true
    }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        chemical_name = data.get('chemical_name', '').strip()
        use_pubchem = data.get('use_pubchem', True)
        
        if not chemical_name:
            return jsonify({'error': 'Chemical name is required'}), 400
        
        # Get enhanced chemical data
        result = get_chemical_data(chemical_name, use_pubchem)
        
        # Log activity
        if result['status'] == 'success':
            log_activity(session['user_id'], 'Enhanced Chemical Lookup', 
                        f'Retrieved data for: {chemical_name} from {result.get("source", "unknown")}')
        else:
            log_activity(session['user_id'], 'Enhanced Chemical Lookup', 
                        f'Failed to get data for: {chemical_name} - {result.get("error_message", "Unknown error")}')
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chemical/properties_summary', methods=['POST'])
def chemical_properties_summary():
    """
    Get comprehensive chemical properties summary
    
    Expected JSON payload:
    {
        "chemical_name": "water"
    }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        chemical_name = data.get('chemical_name', '').strip()
        
        if not chemical_name:
            return jsonify({'error': 'Chemical name is required'}), 400
        
        # Get properties summary
        summary = get_chemical_properties_summary(chemical_name)
        
        # Log activity
        if summary.get('status') != 'error':
            log_activity(session['user_id'], 'Chemical Properties Summary', 
                        f'Generated summary for: {chemical_name}')
        else:
            log_activity(session['user_id'], 'Chemical Properties Summary', 
                        f'Failed to generate summary for: {chemical_name}')
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chemical/enhanced_calculate', methods=['POST'])
def enhanced_calculate():
    """
    Enhanced reagent calculation with additional data
    
    Expected JSON payload:
    {
        "reagent": "Sodium Chloride",
        "molarity": 1.0,
        "volume": 1000
    }
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        data = request.get_json() if request.is_json else request.form
        reagent = data.get('reagent') or data.get('reagent_name')
        molarity = float(data.get('molarity', 0))
        volume = float(data.get('volume', 0))
        
        if not reagent:
            return jsonify({'error': 'Reagent name is required'}), 400
        
        # Enhanced calculation
        result = calculate_reagent_enhanced(reagent, molarity, volume)
        
        if 'error' not in result:
            # Save calculation
            calculation = Calculation(
                user_id=session['user_id'],
                reagent=reagent,
                formula=result.get('formula'),
                molarity=molarity,
                volume=volume,
                mass_needed=result['mass_needed']
            )
            db.session.add(calculation)
            db.session.commit()
            
            log_activity(session['user_id'], 'Enhanced Calculation', 
                        f'Calculated {reagent}: {result["mass_needed"]:.2f}g for {molarity}M in {volume}mL')
        
        if request.is_json:
            return jsonify(result)
        else:
            if 'error' in result:
                flash(result['error'])
            else:
                flash(f'Enhanced calculation complete: {result["mass_needed"]:.2f}g of {reagent} needed')
            return redirect(url_for('calculator'))
        
    except Exception as e:
        error_msg = str(e)
        if request.is_json:
            return jsonify({'error': error_msg}), 400
        else:
            flash(error_msg)
            return redirect(url_for('calculator'))

@app.route('/api/calculation-history')
def get_calculation_history():
    """API endpoint to get user's calculation history"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get user's calculations
        calculations = Calculation.query.filter_by(user_id=session['user_id']).order_by(Calculation.created_at.desc()).limit(50).all()
        
        # Convert to JSON-serializable format
        calculations_data = []
        for calc in calculations:
            calculations_data.append({
                'id': calc.id,
                'reagent': calc.reagent,
                'formula': calc.formula,
                'molarity': calc.molarity,
                'volume': calc.volume,
                'mass_needed': calc.mass_needed,
                'created_at': calc.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'calculations': calculations_data,
            'count': len(calculations_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/periodic-table-data')
def get_periodic_table_data():
    """API endpoint to serve periodic table data from CSV"""
    try:
        import csv
        elements = []
        
        with open('PubChemElements_all.csv', 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            
            for row in csv_reader:
                element_data = {
                    'atomic_number': int(row['AtomicNumber']) if row['AtomicNumber'] else None,
                    'symbol': row['Symbol'],
                    'name': row['Name'],
                    'atomic_mass': float(row['AtomicMass']) if row['AtomicMass'] else None,
                    'cpk_hex_color': row['CPKHexColor'],
                    'electron_configuration': row['ElectronConfiguration'],
                    'electronegativity': float(row['Electronegativity']) if row['Electronegativity'] else None,
                    'atomic_radius': float(row['AtomicRadius']) if row['AtomicRadius'] else None,
                    'ionization_energy': float(row['IonizationEnergy']) if row['IonizationEnergy'] else None,
                    'electron_affinity': float(row['ElectronAffinity']) if row['ElectronAffinity'] else None,
                    'oxidation_states': row['OxidationStates'],
                    'standard_state': row['StandardState'],
                    'melting_point_k': float(row['MeltingPoint']) if row['MeltingPoint'] else None,
                    'boiling_point_k': float(row['BoilingPoint']) if row['BoilingPoint'] else None,
                    'density_g_cm3': float(row['Density']) if row['Density'] else None,
                    'group_block': row['GroupBlock'],
                    'year_discovered': row['YearDiscovered']
                }
                
                # Convert temperatures from Kelvin to Celsius
                if element_data['melting_point_k']:
                    element_data['melting_point_c'] = element_data['melting_point_k'] - 273.15
                if element_data['boiling_point_k']:
                    element_data['boiling_point_c'] = element_data['boiling_point_k'] - 273.15
                
                elements.append(element_data)
        
        return jsonify(elements)
        
    except FileNotFoundError:
        return jsonify({'error': 'CSV file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chemllm')
def chemllm_page():
    """ChemLLM page for advanced chemistry AI assistance"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get model status
    model_info = get_chemllm_info()
    
    return render_template('chemllm.html', model_info=model_info)

@app.route('/chemllm/status')
def chemllm_status():
    """Get ChemLLM model status"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        model_info = get_chemllm_info()
        return jsonify({
            'success': True,
            'model_info': model_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chemllm/generate', methods=['POST'])
def chemllm_generate():
    """Generate response using ChemLLM"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        max_length = data.get('max_length', 512)
        temperature = data.get('temperature', 0.7)
        top_p = data.get('top_p', 0.9)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Check if ChemLLM is available
        if not is_chemllm_available():
            return jsonify({
                'error': 'ChemLLM model is not available. Please check the model installation.',
                'model_status': get_chemllm_info()
            }), 503
        
        # Generate response
        response = generate_chemllm_response(
            prompt=prompt,
            max_length=max_length,
            temperature=temperature,
            top_p=top_p
        )
        
        # Log activity
        log_activity(session['user_id'], 'ChemLLM Query', 
                    f'Generated response for: {prompt[:50]}...')
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'model_info': get_chemllm_info()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
