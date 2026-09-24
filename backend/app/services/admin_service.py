from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminOrderResponse,
    AdminOrderUser,
    AdminUserResponse,
    DashboardStatsResponse,
    LowStockProduct,
    WeeklySale,
)


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self) -> DashboardStatsResponse:
        """Calcula métricas agregadas globais para a visão geral do administrador."""
        # 1. Faturamento total e pedidos
        revenue_row = (
            self.db.query(
                func.coalesce(func.sum(Order.total), 0.0).label("revenue"),
                func.count(Order.id).label("total_orders"),
            )
            .filter(Order.status != OrderStatus.CANCELLED)
            .first()
        )
        total_revenue = float(revenue_row.revenue) if revenue_row else 0.0
        total_orders = int(revenue_row.total_orders) if revenue_row else 0

        # 2. Pedidos pendentes / em processamento
        pending_orders = (
            self.db.query(func.count(Order.id))
            .filter(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.PROCESSING])
            )
            .scalar()
            or 0
        )

        # 3. Produtos e estoque total
        prod_stats = (
            self.db.query(
                func.count(Product.id).label("total_products"),
                func.coalesce(func.sum(Product.stock_qty), 0).label("total_stock"),
            )
            .filter(Product.is_active.is_(True))
            .first()
        )
        total_products = int(prod_stats.total_products) if prod_stats else 0
        total_stock = int(prod_stats.total_stock) if prod_stats else 0

        # 4. Ticket Médio
        average_ticket = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

        # 5. Obras com baixo estoque (<= 3 unidades)
        low_stock_records = (
            self.db.query(Product)
            .options(joinedload(Product.categories))
            .filter(Product.is_active.is_(True), Product.stock_qty <= 3)
            .order_by(Product.stock_qty.asc())
            .limit(10)
            .all()
        )
        low_stock_list = [
            LowStockProduct(
                id=p.id,
                title=p.title,
                author=p.author,
                price=float(p.price),
                stock_qty=p.stock_qty,
                category_name=p.categories.name if p.categories else None,
            )
            for p in low_stock_records
        ]

        # 6. Fluxo semanal de vendas (últimas 4 semanas)
        now = datetime.now()
        weekly_sales: list[WeeklySale] = []
        for i in range(4, 0, -1):
            start_date = now - timedelta(days=i * 7)
            end_date = now - timedelta(days=(i - 1) * 7)
            w_stats = (
                self.db.query(
                    func.coalesce(func.sum(Order.total), 0.0).label("amount"),
                    func.count(Order.id).label("count"),
                )
                .filter(
                    Order.created_at >= start_date,
                    Order.created_at < end_date,
                    Order.status != OrderStatus.CANCELLED,
                )
                .first()
            )
            weekly_sales.append(
                WeeklySale(
                    label=f"Sem {5 - i}",
                    amount=float(w_stats.amount) if w_stats else 0.0,
                    orders_count=int(w_stats.count) if w_stats else 0,
                )
            )

        return DashboardStatsResponse(
            total_revenue=round(total_revenue, 2),
            total_orders=total_orders,
            pending_orders=pending_orders,
            total_products=total_products,
            total_stock=total_stock,
            average_ticket=average_ticket,
            low_stock_products=low_stock_list,
            weekly_sales=weekly_sales,
        )

    def list_all_orders(
        self,
        page: int = 1,
        per_page: int = 20,
        status_filter: str | None = None,
    ) -> list[AdminOrderResponse]:
        """Lista todos os pedidos de todos os usuários para o painel de controle."""
        query = (
            self.db.query(Order)
            .options(
                joinedload(Order.users),
                joinedload(Order.order_items).joinedload(OrderItem.products),
            )
            .order_by(Order.created_at.desc())
        )

        if status_filter:
            try:
                valid_status = OrderStatus(status_filter.lower())
                query = query.filter(Order.status == valid_status)
            except ValueError:
                pass

        offset = (page - 1) * per_page
        orders = query.offset(offset).limit(per_page).all()

        results: list[AdminOrderResponse] = []
        for o in orders:
            user_info = None
            if o.users:
                user_info = AdminOrderUser(
                    id=o.users.id,
                    full_name=o.users.full_name,
                    email=o.users.email,
                )

            # Itens resumo
            items = o.order_items or []
            item_names = [
                f"{item.products.title if item.products else 'Livro'} (x{item.quantity})"
                for item in items[:2]
            ]
            if len(items) > 2:
                item_names.append(f"+{len(items) - 2} outro(s)")

            summary_text = ", ".join(item_names) if item_names else "Sem itens"

            results.append(
                AdminOrderResponse(
                    id=o.id,
                    user_id=o.user_id,
                    user=user_info,
                    status=o.status.value if hasattr(o.status, "value") else str(o.status),
                    subtotal=float(o.subtotal),
                    discount_amount=float(o.discount_amount),
                    shipping_cost=float(o.shipping_cost),
                    total=float(o.total),
                    notes=o.notes,
                    items_count=len(items),
                    items_summary=summary_text,
                    created_at=o.created_at,
                    updated_at=o.updated_at,
                )
            )

        return results

    def update_order_status(self, order_id: int, new_status: str) -> AdminOrderResponse:
        """Atualiza o status de um pedido como administrador."""
        order = (
            self.db.query(Order)
            .options(
                joinedload(Order.users),
                joinedload(Order.order_items).joinedload(OrderItem.products),
            )
            .filter(Order.id == order_id)
            .first()
        )
        if not order:
            raise ValueError(f"Pedido #{order_id} não encontrado")

        try:
            status_enum = OrderStatus(new_status.lower())
        except ValueError:
            raise ValueError(f"Status '{new_status}' inválido")

        order.status = status_enum
        order.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(order)

        user_info = None
        if order.users:
            user_info = AdminOrderUser(
                id=order.users.id,
                full_name=order.users.full_name,
                email=order.users.email,
            )

        items = order.order_items or []
        item_names = [
            f"{item.products.title if item.products else 'Livro'} (x{item.quantity})"
            for item in items[:2]
        ]
        summary_text = ", ".join(item_names) if item_names else "Sem itens"

        return AdminOrderResponse(
            id=order.id,
            user_id=order.user_id,
            user=user_info,
            status=order.status.value if hasattr(order.status, "value") else str(order.status),
            subtotal=float(order.subtotal),
            discount_amount=float(order.discount_amount),
            shipping_cost=float(order.shipping_cost),
            total=float(order.total),
            notes=order.notes,
            items_count=len(items),
            items_summary=summary_text,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    def list_users(self) -> list[AdminUserResponse]:
        """Lista clientes e usuários cadastrados com contagem de pedidos."""
        users = (
            self.db.query(User)
            .options(joinedload(User.orders))
            .order_by(User.created_at.desc())
            .all()
        )

        return [
            AdminUserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role.value if hasattr(u.role, "value") else str(u.role),
                is_active=u.is_active,
                orders_count=len(u.orders) if u.orders else 0,
                created_at=u.created_at,
            )
            for u in users
        ]
