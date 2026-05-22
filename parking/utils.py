import os, uuid, json, random, string
from django.conf import settings
from django.utils import timezone


def send_iot_command(session, command_type):
    """Send command to IoT controller (MQTT or HTTP fallback)."""
    from .models import IoTCommand
    slot = session.slot
    cmd = IoTCommand.objects.create(
        session=session,
        command=command_type,
        target_level=slot.level,
        target_column=slot.column,
        status='queued',
        payload={
            'session_id': str(session.session_id),
            'level': slot.level,
            'column': slot.column,
            'slot': slot.slot_number,
            'plate': session.vehicle_plate,
            'action': command_type,
        }
    )
    try:
        _mqtt_publish(cmd)
        cmd.status = 'sent'
    except Exception:
        # If MQTT broker not available, mark as simulated
        cmd.status = 'ack'
        cmd.response = {'simulated': True, 'note': 'MQTT broker not connected — command logged only'}
    cmd.save()
    return cmd


def _mqtt_publish(cmd):
    """Publish command to MQTT broker (requires paho-mqtt installed and broker running)."""
    try:
        import paho.mqtt.publish as publish
        topic = f"smartpark/commands/{cmd.target_level}/{cmd.target_column}"
        payload = json.dumps({
            'cmd_id': cmd.id,
            'action': cmd.command,
            'level': cmd.target_level,
            'column': cmd.target_column,
            **cmd.payload
        })
        publish.single(
            topic, payload,
            hostname=getattr(settings, 'IOT_BROKER_HOST', 'localhost'),
            port=getattr(settings, 'IOT_BROKER_PORT', 1883),
        )
    except ImportError:
        raise Exception("paho-mqtt not installed")
    except Exception as e:
        raise Exception(f"MQTT error: {e}")


def simulate_payment(payment, method):
    """Simulate payment gateway response. Replace with real MTN/Airtel Money API."""
    # In production, call Africa's Talking, Flutterwave, or MTN MoMo API here
    ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return {'success': True, 'ref': ref, 'method': method}


def generate_receipt_pdf(receipt):
    """Generate a PDF receipt using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A5
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        import os

        payment = receipt.payment
        session = payment.session
        media_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
        os.makedirs(media_dir, exist_ok=True)
        filename = f"receipt_{receipt.receipt_number}.pdf"
        filepath = os.path.join(media_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A5,
                                 leftMargin=1.5*cm, rightMargin=1.5*cm,
                                 topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('title', parent=styles['Heading1'],
                                      fontSize=18, textColor=colors.HexColor('#1a1a2e'),
                                      alignment=TA_CENTER, spaceAfter=4)
        sub_style = ParagraphStyle('sub', parent=styles['Normal'],
                                    fontSize=9, textColor=colors.HexColor('#666'),
                                    alignment=TA_CENTER, spaceAfter=2)
        label_style = ParagraphStyle('label', parent=styles['Normal'],
                                      fontSize=10, textColor=colors.HexColor('#333'))
        total_style = ParagraphStyle('total', parent=styles['Normal'],
                                      fontSize=14, fontName='Helvetica-Bold',
                                      textColor=colors.HexColor('#1a1a2e'), alignment=TA_RIGHT)

        elements = []
        elements.append(Paragraph("SmartPark", title_style))
        elements.append(Paragraph("Automated Parking System — Kampala", sub_style))
        elements.append(Paragraph(f"Receipt #{receipt.receipt_number}", sub_style))
        elements.append(Spacer(1, 0.4*cm))

        # Info table
        cols_map = {1: 'A', 2: 'B', 3: 'C'}
        data = [
            ['Date', receipt.issued_at.strftime('%d %b %Y, %H:%M')],
            ['Slot', f"Level {session.slot.level} — Column {cols_map.get(session.slot.column, session.slot.column)}"],
            ['Vehicle', session.vehicle_plate],
            ['Check-in', session.check_in.strftime('%H:%M')],
            ['Check-out', (session.check_out or timezone.now()).strftime('%H:%M')],
            ['Duration', f"{session.duration_minutes} min"],
            ['Method', payment.get_method_display()],
            ['Ref', payment.transaction_ref[:12] if payment.transaction_ref else 'N/A'],
        ]
        table = Table(data, colWidths=[4*cm, 7*cm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#888')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#222')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f9f9f9'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e0e0e0')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.4*cm))
        elements.append(Paragraph(f"TOTAL: UGX {int(payment.amount_ugx):,}", total_style))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph("Thank you for using SmartPark.", sub_style))
        elements.append(Paragraph("This is an automatically generated receipt.", sub_style))

        doc.build(elements)
        return f"receipts/{filename}"
    except Exception as e:
        print(f"PDF generation error: {e}")
        return None
