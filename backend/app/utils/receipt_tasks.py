
import logging

from celery import shared_task
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.models.address import Address
from app.models.order import Order
from app.utils import storage
from app.utils.email import build_order_details
from app.utils.pdf import generate_receipt_bytes

logger = logging.getLogger(__name__)

FILENAME_TEMPLATE = "comprovante_order_{order_id}.pdf"


def _formatar_endereco(address: Address | None) -> str:
    if not address:
        return "-"
    return (
        f"{address.street}, {address.number} - {address.neighborhood}, "
        f"{address.city}/{address.state} - {address.zip_code}"
    )


@shared_task(bind=True, max_retries=3)
def generate_order_receipt(self, order_id: int) -> dict:
    db = SessionLocal()
    try:
        order = (
            db.query(Order)
            .options(
                selectinload(Order.order_items),
                selectinload(Order.users),
                selectinload(Order.addresses),
            )
            .filter(Order.id == order_id)
            .first()
        )
        if not order:
            raise ValueError(f"No order found with id {order_id}")

        details = build_order_details(order)
        payload = {
            "order_id": order.id,
            "created_at": order.created_at.strftime("%d/%m/%Y %H:%M"),
            "status": str(order.status.value) if hasattr(order.status, "value") else str(order.status),
            "customer_name": order.users.full_name if order.users else "-",
            "customer_email": order.users.email if order.users else "-",
            "address": _formatar_endereco(order.addresses),
            "subtotal": order.subtotal,
            "shipping_cost": order.shipping_cost,
            "discount_amount": order.discount_amount,
            "total": order.total,
            "items": details["items"],
        }

        filename = FILENAME_TEMPLATE.format(order_id=order.id)
        content = generate_receipt_bytes(payload)
        storage_path = f"{get_settings().SUPABASE_STORAGE_BUCKET}/{filename}"
        storage.upload_receipt(storage_path, content)

        order.receipt_path = storage_path
        db.commit()

        return {
            "status": "success",
            "order_id": order.id,
            "receipt_path": order.receipt_path,
        }

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) from exc
    finally:
        db.close()
