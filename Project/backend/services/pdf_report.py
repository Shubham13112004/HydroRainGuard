import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from models.schemas import AssessmentResponse

PRIMARY = colors.HexColor('#0d5c8c')  # Dark blue
SECONDARY = colors.HexColor('#27ae60')  # Green
ACCENT = colors.HexColor('#e8f4fd')    # Light blue bg
GREY = colors.HexColor('#6c757d')
LIGHT_GREY = colors.HexColor('#f8f9fa')


def generate_pdf_report(assessment: AssessmentResponse) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Title'],
        fontSize=22, textColor=PRIMARY, spaceAfter=6, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=11, textColor=GREY, alignment=TA_CENTER, spaceAfter=20)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
        fontSize=13, textColor=PRIMARY, spaceBefore=16, spaceAfter=8,
        borderPad=4)
    normal_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=9, leading=14)
    small_style = ParagraphStyle('Small', parent=styles['Normal'],
        fontSize=8, textColor=GREY)
    
    req = assessment.request
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    
    # ── TITLE PAGE ──
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph('💧 HYDRO RAIN GUARD', title_style))
    story.append(Paragraph('Integrated Intelligent Assessment Report', subtitle_style))
    story.append(Paragraph('Rainwater Harvesting & Artificial Groundwater Recharge', subtitle_style))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY))
    story.append(Spacer(1, 0.5*cm))
    
    meta_data = [
        ['Project / Owner:', req.name],
        ['Location:', f"{req.location} ({req.latitude:.4f}°N, {req.longitude:.4f}°E)"],
        ['Report Generated:', datetime.now().strftime('%d %B %Y, %H:%M IST')],
        ['Assessment ID:', assessment.assessment_id],
        ['Weather Station:', assessment.weather.location_name],
    ]
    meta_table = Table(meta_data, colWidths=[5*cm, 11*cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0,0),(-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,-1), 9),
        ('TEXTCOLOR', (0,0),(0,-1), PRIMARY),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('TOPPADDING', (0,0),(-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=GREY))
    
    # ── EXECUTIVE SUMMARY ──
    story.append(Paragraph('Executive Summary', heading_style))
    r = assessment.runoff
    rc = assessment.recharge
    cb = assessment.cost_benefit
    
    summary_data = [
        ['Metric', 'Value', 'Unit'],
        ['Annual Rooftop Runoff', f"{r.annual_runoff_volume/1000:.1f}", 'KL/year'],
        ['Harvestable Volume', f"{r.harvestable_volume/1000:.1f}", 'KL/year'],
        ['Groundwater Recharge Potential', f"{rc.annual_recharge_potential/1000:.1f}", 'KL/year'],
        ['Recharge Feasibility Score', f"{rc.recharge_feasibility_score:.0f}/100", 'Score'],
        ['Annual Water Cost Savings', f"₹{cb.annual_savings_inr:,.0f}", 'INR/year'],
        ['Estimated Installation Cost', f"₹{cb.estimated_cost:,.0f}", 'INR'],
        ['Payback Period', f"{cb.payback_period_years:.1f}", 'Years'],
        ['10-Year ROI', f"{cb.roi_percentage:.1f}%", ''],
    ]
    summary_table = Table(summary_data, colWidths=[9*cm, 4*cm, 3*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0),(-1,0), colors.white),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0),(-1,-1), 9),
        ('ALIGN', (1,0),(-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [colors.white, ACCENT]),
        ('GRID', (0,0),(-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ]))
    story.append(summary_table)
    
    # ── INPUT PARAMETERS ──
    story.append(Paragraph('Input Parameters', heading_style))
    input_data = [
        ['Parameter', 'Value'],
        ['Roof Type', req.roof_type],
        ['Roof Area', f"{req.roof_area} m²"],
        ['Number of Occupants', str(req.num_people)],
        ['Open Space Area', f"{req.open_space_area} m²"],
        ['Soil Type', req.soil_type],
        ['Groundwater Depth', f"{req.groundwater_depth} m"],
        ['Annual Rainfall (Location)', f"{assessment.weather.annual_rainfall:.0f} mm"],
        ['Runoff Coefficient (C)', str(r.runoff_coefficient)],
        ['Soil Infiltration Rate', f"{rc.infiltration_rate} mm/hr"],
    ]
    input_table = Table(input_data, colWidths=[8*cm, 8*cm])
    input_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), SECONDARY),
        ('TEXTCOLOR', (0,0),(-1,0), colors.white),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1),(0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0),(-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [colors.white, LIGHT_GREY]),
        ('GRID', (0,0),(-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ]))
    story.append(input_table)
    
    # ── RAINFALL & RUNOFF ──
    story.append(Paragraph('Rainfall & Runoff Analysis', heading_style))
    story.append(Paragraph(f'Calculation Method: Rational Method (Q = C × i × A), C = {r.runoff_coefficient}', normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    monthly_data = [['Month', 'Rainfall (mm)', 'Runoff Volume (L)', 'Cost Savings (₹)']]
    for i, m in enumerate(months):
        rain = assessment.weather.monthly_rainfall[i]
        run = r.monthly_runoff[i]
        save = cb.monthly_savings[i]
        monthly_data.append([m, f"{rain:.1f}", f"{run:,.0f}", f"₹{save:,.1f}"])
    monthly_data.append(['ANNUAL', f"{assessment.weather.annual_rainfall:.0f}", f"{r.annual_runoff_volume:,.0f}", f"₹{cb.annual_savings_inr:,.0f}"])
    
    monthly_table = Table(monthly_data, colWidths=[3*cm, 4*cm, 5*cm, 4*cm])
    monthly_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0),(-1,0), colors.white),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1),(-1,-1), colors.HexColor('#e8f5e9')),
        ('FONTNAME', (0,-1),(-1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (0,1),(-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,0),(-1,-1), 8),
        ('ALIGN', (1,0),(-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1),(-1,-2), [colors.white, ACCENT]),
        ('GRID', (0,0),(-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
    ]))
    story.append(monthly_table)
    
    # ── GROUNDWATER RECHARGE ──
    story.append(Paragraph('Groundwater Recharge Assessment', heading_style))
    hg = assessment.hydrogeo_info
    recharge_data = [
        ['Parameter', 'Value'],
        ['Aquifer Type', rc.aquifer_type],
        ['Groundwater Depth', f"{req.groundwater_depth} m"],
        ['Soil Infiltration Rate', f"{rc.infiltration_rate} mm/hr"],
        ['Annual Recharge Potential', f"{rc.annual_recharge_potential/1000:.1f} KL/year"],
        ['Daily Recharge Rate', f"{rc.groundwater_recharge_rate:.1f} L/day"],
        ['Recharge Feasibility Score', f"{rc.recharge_feasibility_score:.0f} / 100"],
        ['Aquifer Permeability', hg.permeability],
        ['Groundwater Quality', hg.groundwater_quality],
        ['Seasonal Fluctuation', f"{hg.seasonal_fluctuation} m"],
    ]
    recharge_table = Table(recharge_data, colWidths=[8*cm, 8*cm])
    recharge_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), SECONDARY),
        ('TEXTCOLOR', (0,0),(-1,0), colors.white),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1),(0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0),(-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [colors.white, LIGHT_GREY]),
        ('GRID', (0,0),(-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ]))
    story.append(recharge_table)
    
    # ── RECOMMENDED STRUCTURES ──
    story.append(Paragraph('Recommended Recharge Structures', heading_style))
    for i, s in enumerate(assessment.recommended_structures[:3], 1):
        struct_data = [
            [f"#{i} {s.structure_type}", f"Suitability: {s.suitability_score:.0f}/100"],
            [Paragraph(s.description, small_style), ''],
            [Paragraph(f"<b>Installation:</b> {s.installation_notes}", small_style), ''],
        ]
        dims_str = ' | '.join([f"{k}: {v}" for k,v in s.dimensions.items()])
        struct_data.append([Paragraph(f"<b>Dimensions:</b> {dims_str}", small_style), ''])
        st = Table(struct_data, colWidths=[13*cm, 3*cm])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,0), ACCENT),
            ('FONTNAME', (0,0),(0,0), 'Helvetica-Bold'),
            ('FONTNAME', (1,0),(1,0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0),(-1,0), PRIMARY),
            ('FONTSIZE', (0,0),(-1,-1), 9),
            ('SPAN', (0,1),(1,1)),
            ('SPAN', (0,2),(1,2)),
            ('SPAN', (0,3),(1,3)),
            ('GRID', (0,0),(-1,-1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ]))
        story.append(KeepTogether([st, Spacer(1, 0.3*cm)]))
    
    # ── COST BENEFIT ──
    story.append(Paragraph('Cost-Benefit Analysis', heading_style))
    cb_data = [
        ['Item', 'Amount (INR)'],
        ['Total Installation Cost', f"₹{cb.estimated_cost:,.0f}"],
        ['Annual Water Savings (volume)', f"{cb.annual_water_savings_liters/1000:.1f} KL"],
        ['Annual Cost Savings', f"₹{cb.annual_savings_inr:,.0f}"],
        ['Annual Maintenance (2%)', f"₹{cb.estimated_cost*0.02:,.0f}"],
        ['Net Annual Savings', f"₹{(cb.annual_savings_inr - cb.estimated_cost*0.02):,.0f}"],
        ['Payback Period', f"{cb.payback_period_years:.1f} years"],
        ['10-Year ROI', f"{cb.roi_percentage:.1f}%"],
    ]
    cb_table = Table(cb_data, colWidths=[10*cm, 6*cm])
    cb_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0),(-1,0), colors.white),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1),(0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0),(-1,-1), 9),
        ('ALIGN', (1,0),(1,-1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [colors.white, LIGHT_GREY]),
        ('GRID', (0,0),(-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ]))
    story.append(cb_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=GREY))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        'Report generated by HYDRO RAIN GUARD | ICICIS Conference 2026 | JSPM Rajarshi Shahu College of Engineering, Pune',
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, textColor=GREY, alignment=TA_CENTER)
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
