# Importar TODOS os modelos aqui é obrigatório para o SQLAlchemy.
#
# Os relacionamentos são declarados por nome (string, ex. "Payment") e só são
# resolvidos no momento do mapeamento (`configure_mappers`). Um modelo só entra
# no registry quando o seu módulo é importado.
#
# Sem o `Payment` aqui, o mapper de `Order` falhava com:
#   "expression 'Payment' failed to locate a name" — em QUALQUER teste que
#   importasse um repositório, pois `app/repositories/__init__.py` importa todos
#   os repositórios (incluindo `order_repo`), que importam `app.models.order`.
#   Como `payment_repo` não estava no __init__ dos repositórios, o módulo
#   `app.models.payment` nunca era carregado e o relacionamento falhava.
#
# Os aliases redundantes (`as Address as Address`) seguem o padrão de
# `app/repositories/__init__.py` e silenciam o F401 do ruff: a importação aqui
# é proposital (registro de mapeamento), não um uso.
from app.models.address import Address as Address
from app.models.cart import Cart as Cart
from app.models.cart_item import CartItem as CartItem
from app.models.category import Category as Category
from app.models.coupon import Coupon as Coupon
from app.models.newsletter import NewsletterSubscriber as NewsletterSubscriber
from app.models.order import Order as Order
from app.models.order_item import OrderItem as OrderItem
from app.models.payment import Payment as Payment
from app.models.product import Product as Product
from app.models.review import Review as Review
from app.models.user import User as User
from app.models.user_coupon import UserCoupon as UserCoupon
from app.models.wishlist import Wishlist as Wishlist

__all__ = [
    "Address",
    "Cart",
    "CartItem",
    "Category",
    "Coupon",
    "NewsletterSubscriber",
    "Order",
    "OrderItem",
    "Payment",
    "Product",
    "Review",
    "User",
    "UserCoupon",
    "Wishlist",
]
