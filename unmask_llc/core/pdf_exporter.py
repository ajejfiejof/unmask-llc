"""PDF Organizing Dossier exporter using ReportLab."""

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from unmask_llc.core.models import TenantOrganizingPacket


class PDFDossierExporter:
    """Exports TenantOrganizingPacket objects into styled printable PDF documents."""

    def generate_pdf_bytes(self, packet: TenantOrganizingPacket) -> bytes:
        """Generates PDF dossier binary content."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#be123c"),
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
        )
        code_style = ParagraphStyle(
            "CodeBlock",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
            backColor=colors.HexColor("#f8fafc"),
            borderColor=colors.HexColor("#e2e8f0"),
            borderWidth=1,
            borderPadding=8,
            spaceBefore=6,
            spaceAfter=6,
        )

        story = []

        # Title Header
        story.append(Paragraph("TENANT ORGANIZING DOSSIER", title_style))
        story.append(
            Paragraph(
                f"Target Property: <b>{packet.target_property.address}</b> | Parent Entity: <b>{packet.parent_company_name}</b>",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1, 10))

        # Executive Risk Summary Box Table
        summary_data = [
            [
                Paragraph("<b>Monopoly Risk Level:</b>", body_style),
                Paragraph(f"<b>{packet.risk_summary.get('risk_level', 'N/A')}</b>", body_style),
                Paragraph("<b>Monopoly Score:</b>", body_style),
                Paragraph(f"<b>{packet.risk_summary.get('monopoly_score', 0)}/100</b>", body_style),
            ],
            [
                Paragraph("<b>Total Portfolio Units:</b>", body_style),
                Paragraph(str(packet.total_portfolio_units), body_style),
                Paragraph("<b>Portfolio Properties:</b>", body_style),
                Paragraph(str(packet.total_portfolio_properties), body_style),
            ],
        ]
        summary_table = Table(summary_data, colWidths=[130, 130, 130, 130])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # Strategic Action Plan Section
        story.append(Paragraph("Multi-Building Strategic Escalation Plan", h2_style))
        for step in packet.organizing_action_plan:
            story.append(Paragraph(f"• {step}", body_style))
            story.append(Spacer(1, 3))

        story.append(Spacer(1, 10))

        # Sister Properties Portfolio Table
        story.append(Paragraph("Discovered Portfolio Sister Properties", h2_style))
        prop_rows = [["Address", "City", "State", "Units", "Evictions (3yr)"]]
        for p in [packet.target_property] + packet.sister_properties[:6]:
            prop_rows.append([p.address, p.city, p.state, str(p.units), str(p.eviction_count_3yr)])

        prop_table = Table(prop_rows, colWidths=[200, 100, 50, 60, 110])
        prop_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("PADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(prop_table)
        story.append(Spacer(1, 12))

        # Collective Demand Letter Template
        story.append(Paragraph("Sample Collective Demand Letter", h2_style))
        # Format demand letter text into paragraphs
        letter_clean = packet.sample_demand_letter.replace("\n", "<br/>")
        story.append(Paragraph(letter_clean, code_style))

        # Build Document
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
