from pydantic import BaseModel, ConfigDict, Field


class ShippingOffer(BaseModel):
    """Uma opção de frete retornada pelo Melhor Envio (cotação)."""

    # Código do serviço/transportadora (ex.: "1" = Correios PAC, "2" = SEDEX).
    service_id: str = Field(description="Código do serviço na Melhor Envio")
    name: str = Field(description="Nome da transportadora/serviço (ex.: PAC)")
    company_name: str | None = Field(None, description="Nome da transportadora")
    # Preço final: usa `custom_price` quando presente (reflete taxas/descontos
    # da conta), senão o `price` original.
    price: float = Field(description="Preço do frete em BRL")
    # Prazo (dias): usa `custom_delivery_time` quando presente, senão o
    # `delivery_time` original.
    delivery_time: int | None = Field(None, description="Prazo em dias úteis")
    delivery_time_text: str | None = Field(None, description="Prazo textual da API")

    model_config = ConfigDict(from_attributes=True)


class ShippingCalculateResponse(BaseModel):
    """Resultado da cotação de frete de um pedido."""

    order_id: int
    offers: list[ShippingOffer] = Field(default_factory=list)
    # Index da oferta selecionada como a "melhor" (menor preço). None quando
    # não há ofertas disponíveis.
    best_offer_index: int | None = None
    # true quando o cálculo foi real (via Melhor Envio); false quando caiu no
    # fallback offline (frete fixo) por falta de configuração/dados.
    is_real: bool = True


class ShippingQuoteRequest(BaseModel):
    """Requisição de cotação pré-checkout (por CEP, sem criar pedido)."""

    postal_code: str = Field(
        description="CEP de entrega (usado no estado de origem -> destino)"
    )


class ShippingQuoteResponse(BaseModel):
    """Resultado da cotação pré-checkout (baseada no carrinho do usuário)."""

    postal_code: str = ""
    offers: list[ShippingOffer] = Field(default_factory=list)
    best_offer_index: int | None = None
    is_real: bool = True
    fallback_reason: str | None = Field(
        None, description="Motivo quando is_real=False (fallback offline)"
    )


class ShippingApplyRequest(BaseModel):
    order_id: int = Field(description="ID do pedido")
    price: float = Field(..., ge=0, description="Valor do frete a aplicar")
    # Opcional: prazo para exibir na confirmação (não persistem no Order).
    delivery_time: int | None = Field(None, description="Prazo em dias úteis")


class ShippingApplyResponse(BaseModel):
    order_id: int
    applied: bool
    shipping_cost: float
    total: float
    status: str
