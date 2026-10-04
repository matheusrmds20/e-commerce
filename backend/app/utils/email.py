from celery import shared_task
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings


settings = get_settings()


def build_order_details(order) -> dict:
    """Monta o payload serializável de um pedido para o Celery.

    Aceita um modelo ``Order`` (SQLAlchemy) e devolve um dict de primitivos
    (sem objetos SQLAlchemy), pronto para ser enfileirado no broker e lido
    pelo template de e-mail.
    """
    return {
        "total": order.total,
        "subtotal": order.subtotal,
        "items": [
            {
                "name": item.products.title,
                "quantity": item.quantity,
                "price": item.price,
            }
            for item in order.order_items
        ],
    }


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id: int, user_email: str, order_details):

    try:
        smtp_host = settings.SMTP_HOST
        smtp_port = int(settings.SMTP_PORT)
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD


        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Confirmacao de Pedido"
        msg["From"] = smtp_user
        msg["To"] = user_email

        itens_html = "".join(
            f"<li>{i.get('quantity', 0)}x {i.get('name', '-')} — R$ {i.get('price', '0.00')}</li>"
            for i in order_details.get('items', [])
        )
        total = order_details.get('total', '0.00')
        subtotal = order_details.get('subtotal', '0.00')
        html = f"""
        <html>
          <body>
            <h2>Obrigado pela sua compra!</h2>
            <p>Pedido: <strong>{order_id}</strong></p>
            <p>Subtotal: R$ {subtotal}</p>
            <p>Valor total: R$ {total}</p>
            <p>Itens:</p>
            <ul>{itens_html}</ul>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))


        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, user_email, msg.as_string())

        return {"status": "success", "order_id": order_id}

    except Exception as exc:

        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
