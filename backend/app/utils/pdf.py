"""Geração de comprovante/recibo de pedido em PDF (reportlab).

O gerador é uma função pura: recebe um payload ``dict`` com os dados do pedido
e grava o PDF num caminho. Não conhece ORM/banco — isso fica na task Celery
(``app.utils.receipt_tasks``) que monta o payload e chama esta função.

O payload esperado (primitivos serializáveis) é montado por
``build_order_details`` (itens/totais) combinado com dados de cliente e
endereço:
    {
        "order_id": int,
        "created_at": datetime/str,
        "status": str,
        "customer_name": str,
        "customer_email": str,
        "address": "Rua X, 10 - Centro, São Paulo/SP - 01001000",
        "subtotal": float,
        "shipping_cost": float,
        "discount_amount": float,
        "total": float,
        "items": [{"name": str, "quantity": int, "price": float}, ...],
    }
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _fmt_br(value: float) -> str:
    """Formata um valor como moeda brasileira (R$ 1.234,56)."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_receipt(payload: dict, output_path: str | Path) -> Path:
    """Gera um comprovante simples de pedido e grava em ``output_path``.

    Garante que o diretório exista e retorna o ``Path`` do arquivo.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        textColor=colors.grey,
        fontSize=10,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
    )

    items = payload.get("items", [])

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    # --- Cabeçalho
    story.append(Paragraph("Comprovante de Pedido", title_style))
    story.append(Paragraph(
        f"Pedido nº {payload.get('order_id', '-')}",
        ParagraphStyle("Pedido", parent=sub_style, fontSize=12, textColor=colors.black),
    ))
    story.append(Spacer(1, 6))

    # --- Cliente e endereço
    story.append(Paragraph("Cliente", label_style))
    story.append(Paragraph(payload.get("customer_name", "-"), styles["Normal"]))
    story.append(Paragraph(payload.get("customer_email", "-"), sub_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Endereço de entrega", label_style))
    story.append(Paragraph(payload.get("address", "-"), styles["Normal"]))
    story.append(Paragraph(
        f"Data: {payload.get('created_at', '-')}   Status: {payload.get('status', '-')}",
        sub_style,
    ))
    story.append(Spacer(1, 12))

    # --- Tabela de itens
    table_data = [["Item", "Qtd", "Preço unit.", "Subtotal"]]
    for item in items:
        price = float(item.get("price") or 0)
        qty = int(item.get("quantity") or 0)
        table_data.append([
            item.get("name", "-"),
            str(qty),
            _fmt_br(price),
            _fmt_br(price * qty),
        ])

    table = Table(table_data, colWidths=[78 * mm, 20 * mm, 35 * mm, 35 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # --- Totais
    tot_data = [
        ["Subtotal", _fmt_br(payload.get("subtotal", 0))],
        ["Frete", _fmt_br(payload.get("shipping_cost", 0))],
        ["Desconto", f"- {_fmt_br(payload.get('discount_amount', 0))}"],
    ]
    tot_table = Table(tot_data, colWidths=[78 * mm, 90 * mm])
    tot_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, 1), (-1, 1), 0.2, colors.grey),
    ]))
    story.append(tot_table)
    story.append(Spacer(1, 4))

    # Linha de total em destaque
    total_tbl = Table(
        [["TOTAL", _fmt_br(payload.get("total", 0))]],
        colWidths=[78 * mm, 90 * mm],
    )
    total_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f2f2")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(total_tbl)

    doc.build(story)
    return output_path
