from datetime import datetime

from app.api.exceptions import (
    AddressForbiddenException,
    AddressNotFoundException,
    BadRequestException,
    CouponNotAssignedException,
    CouponNotFoundException,
    ForbiddenException,
    InsufficientStockException,
    InvalidCouponException,
    NotFoundException,
    OrderNotFoundException,
    ProductInactiveException,
    ProductNotFoundException,
    UserNotFoundException,
)
from app.models.order import Order, OrderStatus
from app.repositories.address_repo import AddressRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.coupon_repo import CouponRepository
from app.repositories.order_item import OrderItemRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.user_coupon_repo import UserCouponRepository
from app.repositories.user_repo import UserRepository
from app.services.order_state_machine import assert_client_transition
from app.services.pricing import calcular_totais
from app.utils.email import build_order_details, send_order_confirmation_email


class OrderService:
    def __init__(self, db):
        self.repo = OrderRepository(db)
        self.order_item_repo = OrderItemRepository(db)
        self.address_repo = AddressRepository(db)
        self.coupon_repo = CouponRepository(db)
        self.user_coupon_repo = UserCouponRepository(db)
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
                raise ProductNotFoundException()

            if not product.is_active:
                raise ProductInactiveException(
                    f"O produto '{product.title}' está indisponível no momento.",
                )

            # Soma o que já foi reservado para este mesmo produto em outra
            # linha do payload.
            ja_reservado = sum(
                q for p, q in baixas_de_estoque if p.id == product.id
            )

            if product.stock_qty < item.quantity + ja_reservado:
                raise InsufficientStockException(
                    product.title, product.stock_qty
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



    def _validate_coupon(self, coupon_id, items, user_id, for_update=False):
        """Valida o cupom e devolve ``(coupon, vinculo)``.

        ``vinculo`` é o ``UserCoupon`` (ownership) — devolvido para que o
        checkout possa marcar ``used_at`` quando o cupom for de uso único por
        cliente. Quando não há cupom, devolve ``(None, None)``.
        """

        if coupon_id is None:
            return None, None

        # No checkout (`for_update=True`) a linha do cupom é travada até o
        # commit, para que a checagem de `max_uses` + incremento sejam atômicos
        # e dois pedidos concorrentes não ultrapassem o limite.
        if for_update:
            coupon = self.coupon_repo.get_by_id_for_update(coupon_id)
            vinculo = self.user_coupon_repo.get_by_user_and_coupon_for_update(
                user_id, coupon_id
            )
        else:
            coupon = self.coupon_repo.get_by_id(coupon_id)
            vinculo = self.user_coupon_repo.get_by_user_and_coupon(
                user_id, coupon_id
            )

        if coupon is None:
            raise CouponNotFoundException()

        # Ownership: o cupom precisa estar atribuído ao usuário do pedido.
        if vinculo is None:
            raise CouponNotAssignedException()

        if not coupon.is_active:
            raise InvalidCouponException(
                f"O cupom '{coupon.code}' não está ativo."
            )

        if coupon.valid_until < datetime.now():
            raise InvalidCouponException(
                f"O cupom '{coupon.code}' expirou."
            )

        # Uso único por cliente: cada usuário consome o cupom uma vez.
        if getattr(coupon, "single_use_per_user", False) and vinculo.used_at is not None:
            raise InvalidCouponException(
                f"O cupom '{coupon.code}' já foi utilizado."
            )

        # Limite de usos: antes `max_uses` era gravado e nunca lido, então o
        # mesmo cupom podia ser aplicado infinitas vezes.
        if coupon.max_uses is not None and (coupon.used_count or 0) >= coupon.max_uses:
            raise InvalidCouponException(
                f"O cupom '{coupon.code}' atingiu o limite de usos."
            )

        if coupon.product_id is not None:
            product_ids = {i.product_id for i in items}
            if coupon.product_id not in product_ids:
                raise InvalidCouponException(
                    f"O cupom '{coupon.code}' não se aplica a nenhum produto deste pedido."
                )

        return coupon, vinculo




    def _calculate_totals(self, items, coupon=None):
        """Delegado ao helper único ``app.services.pricing.calcular_totais``.

        A regra de desconto estava duplicada aqui e em ``create``; manter as
        duas em sincronia era fonte de divergência (e ambas sofriam deriva de
        centavos por usarem ``float``). O frete começa em 0 e é aplicado depois
        pelo fluxo de shipping.
        """
        return calcular_totais(items, coupon=coupon, shipping_cost=0)



    def get_by_user_id(self, user_id: int) -> list:
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundException(user_id=user_id)

        # `get_by_user_id_eager` carrega os itens numa segunda query, em vez de
        # 1 por pedido ao serializar (N+1).
        return self.repo.get_by_user_id_eager(user_id)

    def get_paginated_by_user_id(
        self, user_id: int, page: int = 1, per_page: int = 20
    ) -> dict:
        """Pedidos do usuário paginados no envelope ``Page[T]``.

        Substitui o retorno ilimitado de ``/orders/list`` para contas antigas.
        A contagem e o ``offset``/``limit`` rodam no banco.
        """
        from app.schemas.common import montar_pagina

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id=user_id)

        items, total = self.repo.paginate_by_user_id(user_id, page, per_page)
        return montar_pagina(items, page, per_page, total)

    def create(self, user_id: int, data) -> Order:
        with self.session.begin():

            address = self.address_repo.get_by_id(data.address_id)

            if address is None:
                raise AddressNotFoundException()

            if address.user_id != user_id:
                raise AddressForbiddenException()

            if not data.items:
                raise BadRequestException(
                    "O pedido deve conter ao menos um item.",
                    code="EMPTY_ORDER",
                )

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
                    raise ProductNotFoundException()

                if not product.is_active:
                    raise ProductInactiveException(
                        f"O produto '{product.title}' está indisponível no momento.",
                    )

                if product.stock_qty < item.quantity:
                    raise InsufficientStockException(product.title, product.stock_qty)

                # Defesa contra o mesmo produto repetido em `items` (ex.: duas
                # linhas do produto 5 com 3 e 4 unidades). Cada linha passaria
                # na validação isoladamente, mas a baixa somaria 7.
                ja_reservado = sum(
                    q for p, q in baixas_de_estoque if p.id == product.id
                )

                if product.stock_qty < item.quantity + ja_reservado:
                    raise InsufficientStockException(
                        product.title, product.stock_qty
                    )

                baixas_de_estoque.append((product, item.quantity))

                itens_validados.append(
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "price": product.price,
                    }
                )

            # `for_update=True`: trava a linha do cupom até o commit, tornando
            # a validação + o incremento de `used_count` atômicos.
            coupon, vinculo = self._validate_coupon(
                data.coupon_id, data.items, user_id, for_update=True
            )

            # Cálculo único (Decimal, arredondado a centavos). Substitui o
            # bloco duplicado que somava em float e podia divergir do
            # `_calculate_totals` usado no update.
            subtotal, discount_amount, shipping_cost, total = calcular_totais(
                itens_validados, coupon=coupon, shipping_cost=0
            )

            # Consome o cupom (contador global + marca de uso do cliente).
            self._consumir_cupom(coupon, vinculo)

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
                raise OrderNotFoundException()

            if order.user_id != user_id:
                raise ForbiddenException(
                    "Este pedido pertence a outro usuário.",
                    code="ORDER_FORBIDDEN",
                )

            if data.address_id is not None:
                address = self.address_repo.get_by_id(data.address_id)

                if address is None:
                    raise AddressNotFoundException()

                if address.user_id != user_id:
                    raise AddressForbiddenException()

            if data.status is not None and order.status == "cancelled":
                raise BadRequestException(
                    "Não é possível alterar um pedido cancelado.",
                    code="ORDER_CANCELLED",
                )

            if data.items is not None:
                order_items = self._update_items(order, data.items)
            else:
                order_items = self.repo.get_with_items(order_id)

                if not order_items:
                    raise NotFoundException(
                        f"Nenhum item encontrado no pedido {order_id}.",
                        code="ORDER_ITEM_NOT_FOUND",
                    )

            # O cupom só é revalidado quando o payload o informa. Antes a
            # validação rodava sempre com `order.coupon_id`, então editar um
            # campo qualquer (ex.: `notes`) de um pedido cujo cupom expirou
            # desde a compra falhava com INVALID_COUPON.
            cupom_alterado = "coupon_id" in data.model_fields_set
            coupon_id_novo = data.coupon_id if cupom_alterado else order.coupon_id

            coupon, vinculo = self._validate_coupon(
                coupon_id_novo, order_items, user_id, for_update=cupom_alterado
            )

            # Consome apenas quando o cupom realmente entrou/trocou neste
            # update (senão um update de endereço queimaria um uso).
            if cupom_alterado and coupon is not None and coupon.id != order.coupon_id:
                self._consumir_cupom(coupon, vinculo)

            subtotal, discount_amount, shipping_cost, total = self._calculate_totals(order_items, coupon)

            order.subtotal = subtotal
            order.discount_amount = discount_amount
            order.shipping_cost = shipping_cost
            order.total = total
            order.coupon_id = coupon.id if coupon else None

            update_data = data.model_dump(exclude_unset=True, exclude={"items"})

            status_anterior = order.status

            raw_target_status = update_data.pop("status", None)

            # O cliente pode apenas CANCELAR o próprio pedido, e somente de um
            # estado em aberto. A máquina de estados rejeita qualquer outra
            # mudança de status (R2/R3) e preserva os efeitos colaterais de
            # cancelamento abaixo.
            if raw_target_status is not None:
                assert_client_transition(status_anterior, raw_target_status)
                order.status = raw_target_status

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

                # Devolve a unidade do cupom consumida na criação do pedido.
                # Sem isso, cancelar um pedido "gastava" para sempre um uso do
                # cupom, esgotando `max_uses` sem venda correspondente.
                self._devolver_uso_do_cupom(order.coupon_id, order.user_id)

            for field, value in update_data.items():
                setattr(order, field, value)


            return order

    def _consumir_cupom(self, coupon, vinculo) -> None:
        """Registra o uso do cupom: contador global + marca por cliente.

        Chamado só depois de TODAS as validações (estoque, cupom, mínimo de
        compra), então um checkout que falha não queima uso.
        """
        if coupon is not None:
            # `or 0` cobre linhas legadas/instâncias sem o contador hidratado
            # (o default do Column só vale no INSERT).
            coupon.used_count = (coupon.used_count or 0) + 1
            self.session.add(coupon)

        # Marca o uso para o limite "uma vez por cliente".
        if vinculo is not None:
            vinculo.used_at = datetime.now()
            self.session.add(vinculo)

    def _devolver_uso_do_cupom(
        self, coupon_id: int | None, user_id: int | None = None
    ) -> None:
        """Devolve o uso do cupom quando o pedido é cancelado/excluído.

        Espelha a reposição de estoque: cancelar/excluir um pedido desfaz os
        consumos que ele causou. Trava as linhas (``FOR UPDATE``) para não
        perder a devolução numa corrida com outro checkout do mesmo cupom.
        """
        if coupon_id is None:
            return

        coupon = self.coupon_repo.get_by_id_for_update(coupon_id)

        if coupon is not None:

            coupon.used_count = max((coupon.used_count or 0) - 1, 0)
            self.session.add(coupon)

        # Libera o cupom para o cliente poder usá-lo de novo.
        if user_id is not None:
            vinculo = self.user_coupon_repo.get_by_user_and_coupon_for_update(
                user_id, coupon_id
            )
            if vinculo is not None:
                vinculo.used_at = None
                self.session.add(vinculo)

    def delete(self, order_id: int, user_id: int) -> dict:
        with self.session.begin():

            order = self.repo.get_by_id(order_id)

            if order is None:
                raise OrderNotFoundException()

            if order.user_id != user_id:
                raise ForbiddenException(
                    "Este pedido pertence a outro usuário.",
                    code="ORDER_FORBIDDEN",
                )

            # Devolve a unidade do cupom antes de remover o pedido: depois do
            # delete não haveria mais `order.coupon_id` para consultar.
            self._devolver_uso_do_cupom(order.coupon_id, order.user_id)

            self.repo.delete(order)
            return order


    def get_receipt_path(self, order_id: int, user_id: int) -> str:
        """Retorna o caminho do comprovante PDF de um pedido do usuário.

        Valida que o pedido existe e pertence ao usuário (anti-IDOR). Se o
        comprovante ainda não foi gerado (task ainda não rodou ou falhou),
        levanta ``NotFoundException`` (404).
        """
        order = self.repo.get_by_id(order_id)

        if order is None:
            raise OrderNotFoundException()

        if order.user_id != user_id:
            raise ForbiddenException(
                "Este pedido pertence a outro usuário.",
                code="ORDER_FORBIDDEN",
            )

        if not order.receipt_path:
            raise NotFoundException(
                f"O comprovante do pedido {order_id} ainda não foi gerado.",
                code="RECEIPT_NOT_FOUND",
            )

        return order.receipt_path


    async def send_confirmation_email(self, order_id: int, user):
        order = self.repo.get_by_id(order_id)

        if not order:
            raise OrderNotFoundException()

        if order.status != OrderStatus.COMPLETED:
            raise BadRequestException(
                f"O pedido {order_id} ainda não foi concluído.",
                code="ORDER_NOT_COMPLETED",
            )

        if order.user_id != user.id:
            raise ForbiddenException(
                "Este pedido pertence a outro usuário.",
                code="ORDER_FORBIDDEN",
            )

        sended = send_order_confirmation_email.delay(
            order_id,
            user.email,
            build_order_details(order),
        )

        return {"status": "success", "sended": sended.id}

    async def get_task_status(self, task_id: str):
        task = send_order_confirmation_email.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None,
        }

