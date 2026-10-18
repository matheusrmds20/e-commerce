from pydantic import BaseModel, ConfigDict, Field


class ShippingOffer(BaseModel):


    service_id: str = Field(description="Código do serviço na Melhor Envio")
    name: str = Field(description="Nome da transportadora/serviço (ex.: PAC)")
    company_name: str | None = Field(None, description="Nome da transportadora")
    price: float = Field(description="Preço do frete em BRL")
    delivery_time: int | None = Field(None, description="Prazo em dias úteis")
    delivery_time_text: str | None = Field(None, description="Prazo textual da API")

    model_config = ConfigDict(from_attributes=True)


class ShippingCalculateResponse(BaseModel):
    """Resultado da cotação de frete de um pedido."""

    order_id: int
    offers: list[ShippingOffer] = Field(default_factory=list)
    best_offer_index: int | None = None
    is_real: bool = True


class ShippingQuoteRequest(BaseModel):


    postal_code: str = Field(
        description="CEP de entrega (usado no estado de origem -> destino)"
    )


class ShippingQuoteResponse(BaseModel):


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
