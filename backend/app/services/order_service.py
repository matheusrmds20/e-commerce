from datetime import datetime
from app.models.order import Order, OrderStatus
from app.models.coupon import DiscountType
from app.repositories.address_repo import AddressRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.coupon_repo import CouponRepository
from app.repositories.order_item import OrderItemRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository


class OrderService:
    def __init__(self, db):
        self.repo = OrderRepository(db)
        self.order_item_repo = OrderItemRepository(db)
        self.address_repo = AddressRepository(db)
        self.coupon_repo = CouponRepository(db)
        self.product_repo = ProductRepository(db)
        self.user_repo = UserRepository(db)
        self.cart_repo = CartRepository(db)
        self.session = db

    def _update_items(self, order, items):
        """Substitui os itens do pedido ajustando o estoque.

        A edição de itens precisa reconciliar o inventário em dois passos:
        1. **devolve** o estoque dos itens que existiam (eles saem do pedido);
        2. **baixa** o estoque dos novos itens.

        Sem isso, editar um pedido de 1 para 5 unidades baixaria 5 numa segunda
        vez, dobrando o débito. Tudo dentro da mesma transação do `update`.
        """
        existing_items = self.repo.get_with_items(order.id)

        # 1. Devolve o estoque do que será substituído.
        for existing_item in existing_items:
            product = self.product_repo.get_by_id_for_update(
                existing_item.product_id
            )

            if product is not None:
                self.product_repo.restock(product, existing_item.quantity)

            self.order_item_repo.delete_item(existing_item.id)

        order_items = []
        baixas_de_estoque = []

        for item in items:
            # FOR UPDATE: trava a linha do produto até o commit.
            product = self.product_repo.get_by_id_for_update(item.product_id)

            if product is None:
                raise ValueError(f"No product found with id {item.product_id}")

            if not product.is_active:
                raise ValueError(f"Product '{product.title}' is not active")

            # Soma o que já foi reservado para este mesmo produto em outra
            # linha do payload.
            ja_reservado = sum(
                q for p, q in baixas_de_estoque if p.id == product.id
            )

            if product.stock_qty < item.quantity + ja_reservado:
                raise ValueError(
                    f"Insufficient stock for '{product.title}'. "
                    f"Available: {product.stock_qty}, requested: "
                    f"{item.quantity + ja_reservado}"
                )

            baixas_de_estoque.append((product, item.quantity))

            order_item = self.order_item_repo.create_order_item(
                product_id=item.product_id,
                quantity=item.quantity,
                price=product.price,
            )

            order_item.order_id = order.id
            order_items.append(order_item)

        # 2. Baixa o estoque dos novos itens.
        for product, quantidade in baixas_de_estoque:
            self.product_repo.decrement_stock(product, quantidade)

        return order_items

        

    def _validate_coupon(self, coupon_id, items):

        if coupon_id is None:
            return None

        coupon = self.coupon_repo.get_by_id(coupon_id)

        if coupon is None:
            raise ValueError(f"No coupon found with id {coupon_id}")

        if not coupon.is_active:
            raise ValueError(f"Coupon with code '{coupon.code}' is not active")

        if coupon.valid_until < datetime.now():
            raise ValueError(f"Coupon with code '{coupon.code}' has expired")

        if coupon.product_id is not None:
            product_ids = {i.product_id for i in items}
            if coupon.product_id not in product_ids:
                raise ValueError(
                    f"Coupon '{coupon.code}' is not applicable to any "
                    f"product in this order"
                )

        return coupon




    def _calculate_totals(self, items, coupon=None):
        subtotal = 0.0

        for item in items:
            subtotal += item.price * item.quantity

        discount_amount = 0.0

        if coupon is not None and subtotal < (coupon.min_purchase or 0):
            raise ValueError(
                f"Coupon '{coupon.code}' requires a minimum purchase "
                f"of {coupon.min_purchase}"
        )

        if coupon is not None and coupon.discount_type == DiscountType.PERCENTAGE:
            discount_amount = subtotal * (coupon.discount_value / 100)
        elif coupon is not None:
            discount_amount = coupon.discount_value

        if coupon is not None and coupon.max_discount is not None:
            discount_amount = min(discount_amount, coupon.max_discount)

        shipping_cost = 0.0

        total = subtotal - discount_amount + shipping_cost

        return subtotal, discount_amount, shipping_cost, total

    

    def get_by_id(self, order_id: int, user_id: int) -> dict:
        order = self.repo.get_by_id(order_id)

        if not order:
            raise ValueError(f"No order found with id {order_id}")

        if order.user_id != user_id:
            raise ValueError("Order is not owned by user")

        return order

    def get_by_user_id(self, user_id: int) -> list:
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise ValueError(f"No user found with id {user_id}")

        orders = user.orders

        if not orders:
            raise ValueError(f"No orders found with user_id {user_id}")

        return orders

    def get_with_items(self, order_id: int, user_id: int) -> list:
        order = self.repo.get_by_id(order_id)

        if not order:
            raise ValueError(f"No order found with id {order_id}")

        if order.user_id != user_id:
            raise ValueError("Order is not owned by user")

        items = self.repo.get_with_items(order_id)

        if not items:
            raise ValueError(f"No items found in order with id {order_id}")

        return items


    def create(self, user_id: int, data) -> Order:
        with self.session.begin():

            address = self.address_repo.get_by_id(data.address_id)

            if address is None:
                raise ValueError(f"No address found with id {data.address_id}")

            if address.user_id != user_id:
                raise ValueError("Address is not owned by user")

            if not data.items:
                raise ValueError("Order must have at least one item")

            # Guarda os itens validados como (product_id, quantity, price).
            # Eles só viram linhas de `order_items` DEPOIS que o pedido existe:
            # `OrderItem.order_id` é NOT NULL e o repositório faz flush, então
            # criar os itens antes do `Order` estoura IntegrityError.
            itens_validados = []
            # Guarda (produto, quantidade) para dar baixa no estoque só depois
            # de TODAS as validações passarem — assim nenhum item é debitado se
            # um item posterior do pedido falhar.
            baixas_de_estoque = []

            for item in data.items:
                # FOR UPDATE: impede que dois checkouts simultâneos validem o
                # mesmo estoque e vendam o último exemplar duas vezes.
                product = self.product_repo.get_by_id_for_update(item.product_id)

                if product is None:
                    raise ValueError(f"No product found with id {item.product_id}")

                if not product.is_active:
                    raise ValueError(f"Product '{product.title}' is not active")

                if product.stock_qty < item.quantity:
                    raise ValueError(
                        f"Insufficient stock for '{product.title}'. "
                        f"Available: {product.stock_qty}"
                    )

                # Defesa contra o mesmo produto repetido em `items` (ex.: duas
                # linhas do produto 5 com 3 e 4 unidades). Cada linha passaria
                # na validação isoladamente, mas a baixa somaria 7.
                ja_reservado = sum(
                    q for p, q in baixas_de_estoque if p.id == product.id
                )

                if product.stock_qty < item.quantity + ja_reservado:
                    raise ValueError(
                        f"Insufficient stock for '{product.title}'. "
                        f"Available: {product.stock_qty}, requested: "
                        f"{item.quantity + ja_reservado}"
                    )

                baixas_de_estoque.append((product, item.quantity))

                itens_validados.append(
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "price": product.price,
                    }
                )

            coupon = self._validate_coupon(data.coupon_id, data.items)

            # `_calculate_totals` só lê `price` e `quantity` de cada item.
            subtotal = sum(i["price"] * i["quantity"] for i in itens_validados)
            discount_amount = 0.0

            if coupon is not None:
                if subtotal < (coupon.min_purchase or 0):
                    raise ValueError(
                        f"Coupon '{coupon.code}' requires a minimum purchase "
                        f"of {coupon.min_purchase}"
                    )

                if coupon.discount_type == DiscountType.PERCENTAGE:
                    discount_amount = subtotal * (coupon.discount_value / 100)
                else:
                    discount_amount = coupon.discount_value

                if coupon.max_discount is not None:
                    discount_amount = min(discount_amount, coupon.max_discount)

            shipping_cost = 0.0
            total = subtotal - discount_amount + shipping_cost

            order_data = Order(
                user_id=user_id,
                address_id=data.address_id,
                coupon_id=coupon.id if coupon else None,
                notes=data.notes,
                subtotal=subtotal,
                discount_amount=discount_amount,
                shipping_cost=shipping_cost,
                total=total,
            )

            # 1. O pedido precisa existir (e ter id) antes dos itens.
            order = self.repo.create(order_data)

            # 2. Agora sim os itens, já com order_id e dentro da mesma transação.
            order_items = []

            for item in itens_validados:
                order_item = self.order_item_repo.create_order_item(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"],
                )
                order_item.order_id = order.id
                order_items.append(order_item)

            self.session.flush()

            # Baixa de estoque — passo 17 do fluxo de checkout (seção 8.1).
            # Ocorre dentro da mesma transação: qualquer erro posterior faz
            # rollback do estoque junto com o pedido.
            for product, quantidade in baixas_de_estoque:
                self.product_repo.decrement_stock(product, quantidade)

            # Limpa a sacola — passo 18 do fluxo de checkout (seção 8.1).
            # Dentro da mesma transação: se algo falhar depois, o carrinho
            # também volta ao estado anterior (rollback).
            self._limpar_carrinho(user_id)

            return order

    def _limpar_carrinho(self, user_id: int) -> None:
        """Esvazia o carrinho do usuário após o checkout.

        Sem isso, os itens permanecem na sacola e uma nova compra repetiria o
        mesmo pedido. O carrinho em si é **mantido** (só os itens saem): o
        modelo tem relação 1:1 com o usuário e `CartService.create` recusa um
        segundo carrinho ("User already has a cart").

        Ausência de carrinho não é erro: um checkout pode ter sido feito com
        itens vindos do client, sem sacola persistida.
        """
        user = self.user_repo.get_by_id(user_id)

        if user is None or user.cart is None:
            return

        self.cart_repo.clear(user.cart.id)


    def update(self, order_id: int, user_id: int, data) -> dict:
        with self.session.begin():

            order = self.repo.get_by_id(order_id)

            if order is None:
                raise ValueError(f"No order found with id {order_id}")

            if order.user_id != user_id:
                raise ValueError("Order is not owned by user")

            if data.address_id is not None:
                address = self.address_repo.get_by_id(data.address_id)

                if address is None:
                    raise ValueError(f"No address found with id {data.address_id}")

                if address.user_id != user_id:
                    raise ValueError("Address is not owned by user")

            if data.status is not None and order.status == "cancelled":
                raise ValueError("Cannot update a cancelled order")

            if data.items is not None:
                order_items = self._update_items(order, data.items)
            else:
                order_items = self.repo.get_with_items(order_id)

                if not order_items:
                    raise ValueError(f"No items found in order with id {order_id}")

            coupon = self._validate_coupon(order.coupon_id, order_items)

            subtotal, discount_amount, shipping_cost, total = self._calculate_totals(order_items, coupon)

            order.subtotal = subtotal
            order.discount_amount = discount_amount
            order.shipping_cost = shipping_cost
            order.total = total
            order.coupon_id = coupon.id if coupon else None

            update_data = data.model_dump(exclude_unset=True, exclude={"items"})

            status_anterior = order.status

            if update_data.get("status") is not None:
                order.status = update_data.pop("status")

            # R38: ao cancelar, o estoque é reposto (rollback de inventário).
            # `OrderStatus.CANCELLED` é StrEnum, então compara com "cancelled".
            virou_cancelado = (
                status_anterior != OrderStatus.CANCELLED
                and order.status == OrderStatus.CANCELLED
            )

            if virou_cancelado:
                for order_item in order_items:
                    product = self.product_repo.get_by_id_for_update(
                        order_item.product_id
                    )

                    if product is not None:
                        self.product_repo.restock(product, order_item.quantity)

            for field, value in update_data.items():
                setattr(order, field, value)


            return order

    def delete(self, order_id: int, user_id: int) -> dict:
        with self.session.begin():

            order = self.repo.get_by_id(order_id)

            if order is None:
                raise ValueError(f"No order found with id {order_id}")

            if order.user_id != user_id:
                raise ValueError("Order is not owned by user")

            self.repo.delete(order)
            return order