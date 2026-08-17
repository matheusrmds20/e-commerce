# 📚 BookCommerce – Plano de Arquitetura de E-commerce de Livros

> Documento de planejamento arquitetural completo.  
> **Stack:** FastAPI + React + PostgreSQL + Docker  
> **Autor:** Tech Lead / Arquiteto de Software  
> **Data:** Agosto de 2026

---

## Sumário

1. [Análise dos Requisitos](#1-análise-dos-requisitos)
2. [Funcionalidades Sugeridas (Faltantes)](#2-funcionalidades-sugeridas-faltantes)
3. [Arquitetura do Backend](#3-arquitetura-do-backend)
4. [Arquitetura do Frontend](#4-arquitetura-do-frontend)
5. [Estrutura de Pastas](#5-estrutura-de-pastas)
6. [Modelagem do Banco de Dados](#6-modelagem-do-banco-de-dados)
7. [Fluxo de Autenticação](#7-fluxo-de-autenticação)
8. [Fluxo de Compra (Checkout)](#8-fluxo-de-compra-checkout)
9. [Regras de Negócio por Entidade](#9-regras-de-negócio-por-entidade)
10. [Organização das Rotas da API](#10-organização-das-rotas-da-api)
11. [Estratégia de Tratamento de Erros](#11-estratégia-de-tratamento-de-erros)
12. [Estratégia de Validação](#12-estratégia-de-validação)
13. [Estratégia de Segurança](#13-estratégia-de-segurança)
14. [Estratégia de Testes](#14-estratégia-de-testes)
15. [Roadmap de Implementação](#15-roadmap-de-implementação)

---

## 1. Análise dos Requisitos

### 1.1 Requisitos Funcionais (RF)

| ID | Descrição | Prioridade |
|----|-----------|------------|
| RF01 | Listar livros com paginação | P0 |
| RF02 | Pesquisar livros por título, autor, ISBN | P0 |
| RF03 | Filtrar livros por categoria, faixa de preço, disponibilidade | P0 |
| RF04 | Exibir página de detalhes do livro (sinopse, specs, avaliações) | P0 |
| RF05 | Cadastro de cliente (nome, e-mail, senha) | P0 |
| RF06 | Login com e-mail + senha (retorna JWT) | P0 |
| RF07 | Refresh token para renovar sessão | P1 |
| RF08 | Perfil do usuário (visualizar e editar) | P0 |
| RF09 | Carrinho de compras (adicionar, remover, alterar qtd) | P0 |
| RF10 | Checkout com cálculo de frete e resumo do pedido | P0 |
| RF11 | Histórico de pedidos do cliente | P0 |
| RF12 | CRUD de produtos (admin) | P0 |
| RF13 | CRUD de categorias (admin) | P0 |
| RF14 | CRUD de usuários (admin) | P1 |
| RF15 | Gerenciamento de pedidos – atualizar status (admin) | P0 |
| RF16 | Upload de imagem de capa do livro | P1 |
| RF17 | Gerenciamento de estoque | P0 |
| RF18 | Listagem de pedidos com filtros (admin) | P1 |

### 1.2 Requisitos Não Funcionais (RNF)

| ID | Descrição | Prioridade |
|----|-----------|------------|
| RNF01 | API RESTful seguindo boas práticas (nouns, HTTP verbs, status codes) | P0 |
| RNF02 | Arquitetura em camadas: Router → Service → Repository → Model | P0 |
| RNF03 | Validação de entrada com Pydantic Schemas | P0 |
| RNF04 | Autenticação JWT com access + refresh token | P0 |
| RNF05 | Autorização baseada em papéis (RBAC): `customer`, `admin` | P0 |
| RNF06 | Senhas hasheadas com bcrypt | P0 |
| RNF07 | Migrations com Alembic | P0 |
| RNF08 | Containerização com Docker + docker-compose | P0 |
| RNF09 | Tratamento centralizado de exceções | P0 |
| RNF10 | Logging estruturado | P1 |
| RNF11 | CORS configurado adequadamente | P0 |
| RNF12 | Rate limiting em endpoints públicos | P1 |
| RNF13 | Testes unitários (pytest) e de integração | P1 |
| RNF14 | Variáveis de ambiente para configuração sensível | P0 |
| RNF15 | Paginação em todos os endpoints de listagem | P0 |
| RNF16 | Ordenação configurável (sort by field, asc/desc) | P2 |

---

## 2. Funcionalidades Sugeridas (Faltantes)

Analisando os requisitos fornecidos, identifico lacunas importantes para tornar o produto próximo do real:

### 2.1 Área Pública

| # | Funcionalidade | Justificativa |
|---|---------------|---------------|
| 1 | **Avaliações e comentários** | Essencial em e-commerce de livros. Clientes avaliam com 1–5 estrelas e escrevem resenhas. Aumenta engajamento e confiança. |
| 2 | **Lista de desejos (wishlist)** | Permite salvar livros para comprar depois. Funcionalidade comum e de baixa complexidade. |
| 3 | **Destaques da home** | Seção de "Mais vendidos", "Lançamentos", "Ofertas". Curadoria que enriquece a experiência. |
| 4 | **Busca por autor** | Além do título, busca dedicada por autor com página própria listando todos os livros do autor. |

### 2.2 Cliente

| # | Funcionalidade | Justificativa |
|---|---------------|---------------|
| 5 | **Recuperação de senha** | Fluxo "esqueci minha senha" com envio de e-mail (token temporário). Essencial para produto real. |
| 6 | **Confirmação de e-mail** | Verificar e-mail no cadastro para evitar contas falsas. Importante para segurança e comunicação. |
| 7 | **Múltiplos endereços** | Cliente pode ter N endereços salvos (casa, trabalho, etc.). Experiência real de e-commerce. |
| 8 | **Cupons de desconto** | Sistema de cupons (percentual ou valor fixo) aplicável ao carrinho. Essencial para estratégias de marketing. |
| 9 | **Notificações de status do pedido** | E-mails transacionais: pedido confirmado, enviado, entregue. |

### 2.3 Administrador

| # | Funcionalidade | Justificativa |
|---|---------------|---------------|
| 10 | **Dashboard com métricas** | Visão geral: total de vendas, pedidos do dia, produtos mais vendidos, receita. Essencial para gestão. |
| 11 | **Relatório de vendas** | Exportação de relatórios (CSV/PDF) com filtro por período. |
| 12 | **Gerenciamento de cupons** | CRUD de cupons vinculado à funcionalidade de cupons. |
| 13 | **Gerenciamento de banners** | Upload e agendamento de banners da home (carrossel promocional). |
| 14 | **Controle de estoque com alertas** | Notificação quando estoque baixo (threshold configurável). |

### 2.4 Técnicas / Infra

| # | Funcionalidade | Justificativa |
|---|---------------|---------------|
| 15 | **Cache com Redis** | Cache de listagens de produtos, categorias e sessões. Reduz carga no banco. |
| 16 | **Filas assíncronas (Celery/RQ)** | Para envio de e-mails, geração de relatórios, processamento de imagens. |
| 17 | **Upload de imagens com redimensionamento** | Múltiplos tamanhos (thumbnail, médio, full) para otimizar carregamento. |
| 18 | **SEO básico** | Meta tags dinâmicas, sitemap.xml, robots.txt, URLs amigáveis. |
| 19 | **Modo escuro** | Alternância dark/light mode no frontend. Diferencial visual simples. |
| 20 | **Testes E2E com Playwright** | Testes end-to-end automatizados cobrindo fluxos críticos. |

---

## 3. Arquitetura do Backend

### 3.1 Visão Geral

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                      │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   Nginx (Reverse Proxy)                  │
│            Rate Limiting | CORS | Static Files           │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Application (Uvicorn)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ Routers  │→ │ Services │→ │ Repositories         │   │
│  │ (API)    │  │ (Business│  │ (Data Access)         │   │
│  │          │  │  Logic)  │  │                      │   │
│  └──────────┘  └──────────┘  └──────────┬───────────┘   │
│                                         │               │
│  ┌──────────────────────────────────────┘               │
│  │  ┌───────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  │  Models   │  │ Schemas  │  │  Dependencies    │   │
│  │  │ (ORM)     │  │(Pydantic)│  │  (DI)            │   │
│  │  └───────────┘  └──────────┘  └──────────────────┘   │
│  └───────────┬──────────────────────────────────────┘   │
└──────────────┼──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL 16                         │
│         ┌──────────────────────────────┐                │
│         │  Redis (Cache / Sessions)     │               │
│         └──────────────────────────────┘                │
│         ┌──────────────────────────────┐                │
│         │  Celery + Redis (Async Tasks) │               │
│         └──────────────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Arquitetura em Camadas (Layered Architecture)

**Decisão:** Adotamos arquitetura em camadas (n-tier) em vez de Clean Architecture/Hexagonal.

**Justificativa:**
- Clean Architecture adiciona complexidade (use cases, ports, adapters) que para este tamanho de projeto não agrega valor proporcional.
- Arquitetura em camadas bem implementada (com inversão de dependência via repositórios) atinge 90% dos benefícios com 50% da complexidade.
- Se o projeto crescer para microsserviços, migrar de camadas para hexagonal é mais simples do que começar com hexagonal e não precisar.

```
Camada de Apresentação (Routers)
    │  Recebe HTTP request, extrai parâmetros, chama service, retorna resposta.
    │  NÃO contém lógica de negócio.
    ▼
Camada de Serviço (Services)
    │  Orquestra a lógica de negócio.
    │  Coordena múltiplos repositórios.
    │  Aplica regras de negócio.
    │  Levanta exceções de domínio.
    ▼
Camada de Acesso a Dados (Repositories)
    │  Abstrai queries do banco.
    │  Retorna Models SQLAlchemy.
    │  NÃO contém lógica de negócio.
    ▼
Camada de Dados (Models)
       Definições SQLAlchemy ORM.
       Mapeamento objeto-relacional.
```

### 3.3 Princípios SOLID Aplicados

| Princípio | Aplicação |
|-----------|-----------|
| **S** – Single Responsibility | Cada camada tem uma responsabilidade clara. Services não fazem queries diretas. Routers não têm lógica de negócio. |
| **O** – Open/Closed | Estratégias de frete, desconto e pagamento são implementadas com polimorfismo (classe base + subclasses), permitindo extensão sem modificação. |
| **L** – Liskov Substitution | Repositórios implementam interface/protocolo comum. Qualquer implementação concreta pode substituir a abstração. |
| **I** – Interface Segregation | Schemas Pydantic específicos por operação (Create, Update, Response, ListItem) em vez de um schema monolítico. |
| **D** – Dependency Inversion | Services dependem de abstrações (Protocol/ABC de Repository), não de implementações concretas. Injeção via FastAPI `Depends()`. |

### 3.4 Diagrama de Componentes Backend

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── router.py          # Agrega todos os routers
│   │   │   ├── auth.py            # POST /login, /register, /refresh
│   │   │   ├── users.py           # CRUD usuários (admin + me)
│   │   │   ├── products.py        # CRUD produtos + busca pública
│   │   │   ├── categories.py      # CRUD categorias
│   │   │   ├── cart.py            # Carrinho
│   │   │   ├── orders.py          # Pedidos
│   │   │   ├── reviews.py         # Avaliações
│   │   │   ├── addresses.py       # Endereços
│   │   │   ├── coupons.py         # Cupons
│   │   │   ├── wishlist.py        # Lista de desejos
│   │   │   └── dashboard.py      # Dashboard admin
│   │   └── deps.py               # Dependências FastAPI compartilhadas
│   ├── core/
│   │   ├── config.py             # Settings (pydantic-settings)
│   │   ├── security.py           # JWT, hash, permissões
│   │   ├── exceptions.py         # Exceções customizadas
│   │   └── database.py           # Session factory, engine
│   ├── models/
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   ├── cart_item.py
│   │   ├── order.py
│   │   ├── order_item.py
│   │   ├── address.py
│   │   ├── review.py
│   │   ├── coupon.py
│   │   └── wishlist.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   ├── order.py
│   │   ├── address.py
│   │   ├── review.py
│   │   ├── coupon.py
│   │   ├── auth.py
│   │   └── common.py            # Paginação, respostas genéricas
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── product_service.py
│   │   ├── category_service.py
│   │   ├── cart_service.py
│   │   ├── order_service.py
│   │   ├── review_service.py
│   │   ├── address_service.py
│   │   ├── coupon_service.py
│   │   ├── wishlist_service.py
│   │   └── dashboard_service.py
│   ├── repositories/
│   │   ├── base.py              # Repository genérico
│   │   ├── user_repo.py
│   │   ├── product_repo.py
│   │   ├── category_repo.py
│   │   ├── cart_repo.py
│   │   ├── order_repo.py
│   │   ├── address_repo.py
│   │   ├── review_repo.py
│   │   ├── coupon_repo.py
│   │   └── wishlist_repo.py
│   └── utils/
│       ├── pagination.py        # Utilitários de paginação
│       ├── validators.py        # Validadores reutilizáveis
│       └── email.py             # Envio de e-mails
├── migrations/                   # Alembic
├── tests/
│   ├── unit/
│   └── integration/
├── alembic.ini
├── Dockerfile
├── pyproject.toml
└── docker-compose.yml
```

---

## 4. Arquitetura do Frontend

### 4.1 Visão Geral

**Decisão:** Utilizar estrutura baseada em features (feature-based) em vez de pasta por tipo (components, pages, hooks).

**Justificativa:**
- Projetos que crescem se beneficiam de co-localização: componentes, hooks, tipos e testes de uma feature ficam juntos.
- Facilita code splitting e lazy loading por feature.
- Melhor para times com múltiplos desenvolvedores (menos conflitos de merge).
- Itens verdadeiramente compartilhados vão para `shared/` ou `common/`.

```
src/
├── features/
│   ├── auth/           # Login, registro, recuperação de senha
│   ├── products/       # Listagem, busca, detalhes
│   ├── cart/           # Carrinho, mini-cart
│   ├── checkout/       # Checkout, seleção de endereço
│   ├── orders/         # Histórico, detalhes do pedido
│   ├── profile/        # Perfil, endereços, wishlist
│   ├── admin/          # Dashboard, CRUDs admin
│   └── home/           # Página inicial, destaques
├── shared/
│   ├── components/     # Button, Input, Modal, Card etc.
│   ├── hooks/          # useDebounce, useMediaQuery etc.
│   ├── utils/          # formatCurrency, formatDate etc.
│   ├── types/          # Tipos TypeScript globais
│   └── constants/      # Constantes
├── lib/                # Configurações de libs
│   ├── api.ts          # Instância Axios configurada
│   ├── query-client.ts # Config TanStack Query
│   └── auth.ts         # Gerenciamento de token
├── routes/             # Config React Router
└── styles/             # Config Tailwind global
```

### 4.2 Estrutura Interna de uma Feature

```
feature/
├── components/         # Componentes específicos da feature
├── hooks/              # Hooks específicos da feature
├── services/           # Chamadas API específicas
├── types/              # Tipos/interfaces locais
├── schemas/            # Schemas Zod (validação de formulários)
├── index.ts            # Barrel export
└── __tests__/          # Testes da feature
```

### 4.3 Gerenciamento de Estado

| Tipo de Estado | Tecnologia | Justificativa |
|----------------|------------|---------------|
| Estado de servidor (dados assíncronos) | **TanStack Query** | Cache, revalidação, paginação, mutações otimistas. Lida com 90% do estado da aplicação. |
| Estado de formulário | **React Hook Form + Zod** | Performance (uncontrolled), validação integrada, tipagem forte. |
| Estado global de UI | **React Context** (mínimo) | Apenas para: autenticação (currentUser), tema (dark/light), carrinho (contador). |
| Estado local de componente | **useState / useReducer** | Para estados que não precisam ser compartilhados. |

### 4.4 Diagrama de Fluxo de Dados Frontend

```
Componente React
    │  Usa hooks (useQuery, useMutation)
    ▼
Hook (ex: useProducts)
    │  Chama service layer
    ▼
Service (ex: productService.ts)
    │  Chama api.ts (Axios) → faz HTTP request
    ▼
API Backend (FastAPI)
    │  Retorna JSON
    ▼
TanStack Query Cache
    │  Armazena, revalida, fornece ao componente
    ▼
Componente re-renderiza com dados
```

### 4.5 Estratégia de Roteamento

```
/                           → HomePage (pública)
/livros                     → ProductListPage (pública)
/livros/:slug               → ProductDetailPage (pública)
/livros/busca?q=            → ProductSearchPage (pública)
/categorias/:slug           → CategoryPage (pública)

/login                      → LoginPage (pública)
/cadastro                   → RegisterPage (pública)
/recuperar-senha            → ForgotPasswordPage (pública)

/conta                      → ProfilePage (auth required)
/conta/pedidos              → OrderHistoryPage (auth required)
/conta/pedidos/:id          → OrderDetailPage (auth required)
/conta/enderecos            → AddressListPage (auth required)
/conta/wishlist             → WishlistPage (auth required)

/carrinho                   → CartPage (pública, persiste em localStorage + API)
/checkout                   → CheckoutPage (auth required)

/admin                      → AdminDashboard (admin required)
/admin/produtos             → AdminProductsPage (admin required)
/admin/produtos/novo        → AdminProductCreatePage (admin required)
/admin/produtos/:id/editar  → AdminProductEditPage (admin required)
/admin/categorias           → AdminCategoriesPage (admin required)
/admin/pedidos              → AdminOrdersPage (admin required)
/admin/pedidos/:id          → AdminOrderDetailPage (admin required)
/admin/usuarios             → AdminUsersPage (admin required)
/admin/cupons               → AdminCouponsPage (admin required)
```

---

## 5. Estrutura de Pastas Completa

```
bookcommerce/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── products.py
│   │   │   │   ├── categories.py
│   │   │   │   ├── cart.py
│   │   │   │   ├── orders.py
│   │   │   │   ├── reviews.py
│   │   │   │   ├── addresses.py
│   │   │   │   ├── coupons.py
│   │   │   │   ├── wishlist.py
│   │   │   │   └── dashboard.py
│   │   │   ├── deps.py
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── exceptions.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── category.py
│   │   │   ├── product.py
│   │   │   ├── cart.py
│   │   │   ├── cart_item.py
│   │   │   ├── order.py
│   │   │   ├── order_item.py
│   │   │   ├── address.py
│   │   │   ├── review.py
│   │   │   ├── coupon.py
│   │   │   └── wishlist.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── category.py
│   │   │   ├── product.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   ├── address.py
│   │   │   ├── review.py
│   │   │   └── coupon.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── product_service.py
│   │   │   ├── category_service.py
│   │   │   ├── cart_service.py
│   │   │   ├── order_service.py
│   │   │   ├── review_service.py
│   │   │   ├── address_service.py
│   │   │   ├── coupon_service.py
│   │   │   ├── wishlist_service.py
│   │   │   └── dashboard_service.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user_repo.py
│   │   │   ├── product_repo.py
│   │   │   ├── category_repo.py
│   │   │   ├── cart_repo.py
│   │   │   ├── order_repo.py
│   │   │   ├── address_repo.py
│   │   │   ├── review_repo.py
│   │   │   ├── coupon_repo.py
│   │   │   └── wishlist_repo.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── pagination.py
│   │   │   ├── validators.py
│   │   │   ├── email.py
│   │   │   └── file_storage.py
│   │   └── __init__.py
│   ├── migrations/
│   │   ├── versions/
│   │   ├── env.py
│   │   ├── alembic.ini
│   │   └── script.py.mako
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── factories/             # Factory Boy factories
│   │   ├── unit/
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_product_service.py
│   │   │   ├── test_cart_service.py
│   │   │   ├── test_order_service.py
│   │   │   └── test_security.py
│   │   └── integration/
│   │       ├── test_auth_routes.py
│   │       ├── test_product_routes.py
│   │       ├── test_cart_routes.py
│   │       ├── test_order_routes.py
│   │       └── test_admin_routes.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   ├── components/
│   │   │   │   │   ├── LoginForm.tsx
│   │   │   │   │   ├── RegisterForm.tsx
│   │   │   │   │   └── ForgotPasswordForm.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useLogin.ts
│   │   │   │   │   ├── useRegister.ts
│   │   │   │   │   └── useLogout.ts
│   │   │   │   ├── services/
│   │   │   │   │   └── authService.ts
│   │   │   │   ├── schemas/
│   │   │   │   │   ├── loginSchema.ts
│   │   │   │   │   └── registerSchema.ts
│   │   │   │   ├── types/
│   │   │   │   │   └── index.ts
│   │   │   │   └── index.ts
│   │   │   ├── products/
│   │   │   │   ├── components/
│   │   │   │   │   ├── ProductCard.tsx
│   │   │   │   │   ├── ProductGrid.tsx
│   │   │   │   │   ├── ProductFilters.tsx
│   │   │   │   │   ├── ProductSearch.tsx
│   │   │   │   │   ├── ProductReviews.tsx
│   │   │   │   │   └── ProductRating.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useProducts.ts
│   │   │   │   │   ├── useProduct.ts
│   │   │   │   │   ├── useProductSearch.ts
│   │   │   │   │   └── useProductFilters.ts
│   │   │   │   ├── services/
│   │   │   │   │   └── productService.ts
│   │   │   │   ├── types/
│   │   │   │   │   └── index.ts
│   │   │   │   └── index.ts
│   │   │   ├── cart/
│   │   │   │   ├── components/
│   │   │   │   │   ├── CartItem.tsx
│   │   │   │   │   ├── CartSummary.tsx
│   │   │   │   │   ├── MiniCart.tsx
│   │   │   │   │   └── AddToCartButton.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useCart.ts
│   │   │   │   │   ├── useAddToCart.ts
│   │   │   │   │   └── useRemoveFromCart.ts
│   │   │   │   ├── services/
│   │   │   │   │   └── cartService.ts
│   │   │   │   ├── context/
│   │   │   │   │   └── CartContext.tsx
│   │   │   │   ├── types/
│   │   │   │   │   └── index.ts
│   │   │   │   └── index.ts
│   │   │   ├── checkout/
│   │   │   │   ├── components/
│   │   │   │   │   ├── ShippingForm.tsx
│   │   │   │   │   ├── AddressSelector.tsx
│   │   │   │   │   ├── PaymentSummary.tsx
│   │   │   │   │   └── CouponInput.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useCheckout.ts
│   │   │   │   │   └── useShipping.ts
│   │   │   │   ├── services/
│   │   │   │   │   └── checkoutService.ts
│   │   │   │   ├── schemas/
│   │   │   │   │   └── checkoutSchema.ts
│   │   │   │   ├── types/
│   │   │   │   │   └── index.ts
│   │   │   │   └── index.ts
│   │   │   ├── orders/
│   │   │   │   ├── components/
│   │   │   │   │   ├── OrderCard.tsx
│   │   │   │   │   ├── OrderTimeline.tsx
│   │   │   │   │   └── OrderItemsList.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useOrders.ts
│   │   │   │   │   └── useOrder.ts
│   │   │   │   ├── services/
│   │   │   │   │   └── orderService.ts
│   │   │   │   ├── types/
│   │   │   │   │   └── index.ts
│   │   │   │   └── index.ts
│   │   │   ├── profile/
│   │   │   │   ├── components/
│   │   │   │   │   ├── ProfileForm.tsx
│   │   │   │   │   ├── AddressForm.tsx
│   │   │   │   │   ├── AddressList.tsx
│   │   │   │   │   └── WishlistGrid.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useProfile.ts
│   │   │   │   │   ├── useAddresses.ts
│   │   │   │   │   └── useWishlist.ts
│   │   │   │   ├── services/
│   │   │   │   │   ├── profileService.ts
│   │   │   │   │   ├── addressService.ts
│   │   │   │   │   └── wishlistService.ts
│   │   │   │   ├── schemas/
│   │   │   │   │   └── profileSchema.ts
│   │   │   │   ├── types/
│   │   │   │   │   └── index.ts
│   │   │   │   └── index.ts
│   │   │   ├── admin/
│   │   │   │   ├── components/
│   │   │   │   │   ├── AdminLayout.tsx
│   │   │   │   │   ├── AdminSidebar.tsx
│   │   │   │   │   ├── ProductForm.tsx
│   │   │   │   │   ├── ProductTable.tsx
│   │   │   │   │   ├── CategoryForm.tsx
│   │   │   │   │   ├── CategoryTable.tsx
│   │   │   │   │   ├── OrderTable.tsx
│   │   │   │   │   ├── OrderStatusUpdate.tsx
│   │   │   │   │   ├── UserTable.tsx
│   │   │   │   │   ├── CouponForm.tsx
│   │   │   │   │   ├── CouponTable.tsx
│   │   │   │   │   ├── DashboardStats.tsx
│   │   │   │   │   └── SalesChart.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useAdminProducts.ts
│   │   │   │   │   ├── useAdminCategories.ts
│   │   │   │   │   ├── useAdminOrders.ts
│   │   │   │   │   ├── useAdminUsers.ts
│   │   │   │   │   ├── useAdminCoupons.ts
│   │   │   │   │   └── useDashboard.ts
│   │   │   │   ├── services/
│   │   │   │   │   ├── adminProductService.ts
│   │   │   │   │   ├── adminCategoryService.ts
│   │   │   │   │   ├── adminOrderService.ts
│   │   │   │   │   ├── adminUserService.ts
│   │   │   │   │   ├── adminCouponService.ts
│   │   │   │   │   └── dashboardService.ts
│   │   │   │   ├── schemas/
│   │   │   │   │   └── adminSchemas.ts
│   │   │   │   ├── types/
│   │   │   │   │   └── index.ts
│   │   │   │   └── index.ts
│   │   │   └── home/
│   │   │       ├── components/
│   │   │       │   ├── HeroBanner.tsx
│   │   │       │   ├── FeaturedBooks.tsx
│   │   │       │   ├── NewReleases.tsx
│   │   │       │   ├── BestSellers.tsx
│   │   │       │   ├── CategoryShowcase.tsx
│   │   │       │   └── PromotionBanner.tsx
│   │   │       ├── hooks/
│   │   │       │   └── useHomeData.ts
│   │   │       ├── services/
│   │   │       │   └── homeService.ts
│   │   │       ├── types/
│   │   │       │   └── index.ts
│   │   │       └── index.ts
│   │   ├── shared/
│   │   │   ├── components/
│   │   │   │   ├── ui/
│   │   │   │   │   ├── Button.tsx
│   │   │   │   │   ├── Input.tsx
│   │   │   │   │   ├── Select.tsx
│   │   │   │   │   ├── Textarea.tsx
│   │   │   │   │   ├── Checkbox.tsx
│   │   │   │   │   ├── Modal.tsx
│   │   │   │   │   ├── Spinner.tsx
│   │   │   │   │   ├── Badge.tsx
│   │   │   │   │   ├── StarRating.tsx
│   │   │   │   │   ├── Pagination.tsx
│   │   │   │   │   ├── EmptyState.tsx
│   │   │   │   │   ├── ErrorState.tsx
│   │   │   │   │   ├── Toast.tsx
│   │   │   │   │   ├── Skeleton.tsx
│   │   │   │   │   └── ImageWithFallback.tsx
│   │   │   │   └── layout/
│   │   │   │       ├── Header.tsx
│   │   │   │       ├── Footer.tsx
│   │   │   │       ├── MainLayout.tsx
│   │   │   │       ├── AdminLayout.tsx
│   │   │   │       └── ProtectedRoute.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useDebounce.ts
│   │   │   │   ├── useMediaQuery.ts
│   │   │   │   ├── useLocalStorage.ts
│   │   │   │   └── useClickOutside.ts
│   │   │   ├── utils/
│   │   │   │   ├── formatCurrency.ts
│   │   │   │   ├── formatDate.ts
│   │   │   │   ├── cn.ts               # clsx + tailwind-merge
│   │   │   │   └── storage.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── constants/
│   │   │       ├── routes.ts
│   │   │       └── api.ts
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── query-client.ts
│   │   │   └── auth.ts
│   │   ├── routes/
│   │   │   ├── index.tsx
│   │   │   ├── PublicRoutes.tsx
│   │   │   ├── ProtectedRoutes.tsx
│   │   │   └── AdminRoutes.tsx
│   │   ├── styles/
│   │   │   └── globals.css
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── .env.example
│   ├── Dockerfile
│   └── README.md
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 6. Modelagem do Banco de Dados

### 6.1 Diagrama Entidade-Relacionamento (DER)

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│    User      │       │     Address       │       │   Category   │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ id (PK)      │──┐    │ id (PK)           │       │ id (PK)      │
│ email        │  │    │ user_id (FK)      │       │ name         │
│ password_hash│  └───→│ street            │       │ slug         │
│ full_name    │       │ number            │       │ description  │
│ role         │       │ complement        │       │ image_url    │
│ is_active    │       │ neighborhood      │       │ is_active    │
│ created_at   │       │ city              │       │ created_at   │
│ updated_at   │       │ state             │       │ updated_at   │
└──────┬───────┘       │ zip_code          │       └──────┬───────┘
       │               │ is_default        │              │
       │               │ created_at        │              │
       │               └──────────────────┘              │
       │                                                 │
       │  ┌──────────────────┐                          │
       │  │      Cart         │                          │
       │  ├──────────────────┤                          │
       ├──│ id (PK)           │                          │
       │  │ user_id (FK) UQ   │                          │
       │  │ created_at        │                          │
       │  │ updated_at        │                          │
       │  └────────┬─────────┘                          │
       │           │                                    │
       │  ┌────────┴─────────┐       ┌──────────────┐   │
       │  │    CartItem       │       │   Product     │   │
       │  ├──────────────────┤       ├──────────────┤   │
       │  │ id (PK)           │       │ id (PK)       │───┘
       │  │ cart_id (FK)      │       │ category_id   │
       │  │ product_id (FK)   │──────→│ (FK)          │
       │  │ quantity          │       │ title         │
       │  │ created_at        │       │ slug          │
       │  │ updated_at        │       │ author        │
       │  └──────────────────┘       │ isbn          │
       │                             │ publisher     │
       │  ┌──────────────────┐       │ publication_yr│
       │  │     Order         │       │ pages         │
       │  ├──────────────────┤       │ language      │
       ├──│ id (PK)           │       │ synopsis      │
       │  │ user_id (FK)      │       │ price         │
       │  │ address_id (FK)   │       │ discount_pct  │
       │  │ coupon_id (FK)    │       │ stock_qty     │
       │  │ status            │       │ image_url     │
       │  │ subtotal          │       │ is_active     │
       │  │ discount_amount   │       │ created_at    │
       │  │ shipping_cost     │       │ updated_at    │
       │  │ total             │       └──────┬────────┘
       │  │ notes             │              │
       │  │ created_at        │              │
       │  │ updated_at        │              │
       │  └────────┬─────────┘              │
       │           │                        │
       │  ┌────────┴─────────┐              │
       │  │   OrderItem       │              │
       │  ├──────────────────┤              │
       │  │ id (PK)           │              │
       │  │ order_id (FK)     │              │
       │  │ product_id (FK)   │──────────────┘
       │  │ quantity          │
       │  │ unit_price        │
       │  │ total_price       │
       │  └──────────────────┘
       │
       │  ┌──────────────────┐       ┌──────────────┐
       │  │     Review        │       │   Coupon      │
       │  ├──────────────────┤       ├──────────────┤
       ├──│ id (PK)           │       │ id (PK)       │
       │  │ user_id (FK)      │       │ code          │
       │  │ product_id (FK)   │──┐    │ discount_type │
       │  │ rating (1-5)      │  │    │ discount_value│
       │  │ comment           │  │    │ min_purchase  │
       │  │ created_at        │  │    │ max_discount  │
       │  └──────────────────┘  │ 
       │                        │    │ valid_until   │
       │  ┌──────────────────┐  │    │ max_uses      │
       │  │    Wishlist       │  │    │ used_count    │
       │  ├──────────────────┤  │    │ is_active     │
       ├──│ id (PK)           │  │    │ created_at    │
       │  │ user_id (FK)      │  │    └──────────────┘
       │  │ product_id (FK)   │──┘
       │  │ created_at        │
       │  └──────────────────┘
       │
       │  ┌──────────────────┐
       │  │  PasswordReset    │
       │  ├──────────────────┤
       └──│ id (PK)           │
          │ user_id (FK)      │
          │ token             │
          │ expires_at        │
          │ is_used           │
          │ created_at        │
          └──────────────────┘
```

### 6.2 Dicionário de Dados

#### User
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK, default uuid4 | Identificador único |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | E-mail do usuário |
| password_hash | VARCHAR(255) | NOT NULL | Hash bcrypt da senha |
| full_name | VARCHAR(255) | NOT NULL | Nome completo |
| role | VARCHAR(20) | NOT NULL, CHECK IN ('customer','admin') | Papel do usuário |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Usuário ativo/inativo |
| email_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | E-mail verificado |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Data de criação |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW(), ON UPDATE | Data de atualização |

#### Category
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Nome da categoria |
| slug | VARCHAR(120) | UNIQUE, NOT NULL, INDEX | Slug para URL |
| description | TEXT | NULLABLE | Descrição da categoria |
| image_url | VARCHAR(500) | NULLABLE | URL da imagem |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Categoria ativa |
| parent_id | UUID | FK → Category.id, NULLABLE | Categoria pai (subcategoria) |
| created_at | TIMESTAMP | NOT NULL | Data de criação |
| updated_at | TIMESTAMP | NOT NULL | Data de atualização |

#### Product
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| category_id | UUID | FK → Category.id, NOT NULL, INDEX | Categoria do livro |
| title | VARCHAR(255) | NOT NULL, INDEX | Título do livro |
| slug | VARCHAR(300) | UNIQUE, NOT NULL, INDEX | Slug para URL |
| author | VARCHAR(255) | NOT NULL, INDEX | Autor(es) |
| isbn | VARCHAR(20) | UNIQUE, NULLABLE | ISBN-10 ou ISBN-13 |
| publisher | VARCHAR(150) | NULLABLE | Editora |
| publication_year | INTEGER | NULLABLE | Ano de publicação |
| pages | INTEGER | NULLABLE | Número de páginas |
| language | VARCHAR(50) | NULLABLE, DEFAULT 'Português' | Idioma |
| synopsis | TEXT | NULLABLE | Sinopse |
| price | DECIMAL(10,2) | NOT NULL, CHECK > 0 | Preço de venda |
| discount_pct | DECIMAL(5,2) | NULLABLE, DEFAULT 0, CHECK 0-100 | Percentual de desconto |
| stock_qty | INTEGER | NOT NULL, DEFAULT 0, CHECK >= 0 | Quantidade em estoque |
| image_url | VARCHAR(500) | NULLABLE | URL da imagem de capa |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Produto ativo/desativado |
| created_at | TIMESTAMP | NOT NULL | Data de criação |
| updated_at | TIMESTAMP | NOT NULL | Data de atualização |

#### Cart
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| user_id | UUID | FK → User.id, UNIQUE, NOT NULL | Dono do carrinho |
| created_at | TIMESTAMP | NOT NULL | Data de criação |
| updated_at | TIMESTAMP | NOT NULL | Data de atualização |

#### CartItem
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| cart_id | UUID | FK → Cart.id, NOT NULL, INDEX | Carrinho |
| product_id | UUID | FK → Product.id, NOT NULL | Produto |
| quantity | INTEGER | NOT NULL, CHECK >= 1 | Quantidade |
| created_at | TIMESTAMP | NOT NULL | Data de adição |
| updated_at | TIMESTAMP | NOT NULL | Data de atualização |

**Constraint:** UNIQUE(cart_id, product_id)

#### Order
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| user_id | UUID | FK → User.id, NOT NULL, INDEX | Cliente |
| address_id | UUID | FK → Address.id, NOT NULL | Endereço de entrega |
| coupon_id | UUID | FK → Coupon.id, NULLABLE | Cupom aplicado |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'pending', INDEX | Status do pedido |
| subtotal | DECIMAL(10,2) | NOT NULL | Soma dos itens |
| discount_amount | DECIMAL(10,2) | NOT NULL, DEFAULT 0 | Desconto aplicado |
| shipping_cost | DECIMAL(10,2) | NOT NULL, DEFAULT 0 | Custo do frete |
| total | DECIMAL(10,2) | NOT NULL | Total final |
| notes | TEXT | NULLABLE | Observações |
| created_at | TIMESTAMP | NOT NULL | Data do pedido |
| updated_at | TIMESTAMP | NOT NULL | Data de atualização |

**Status possíveis:** `pending` → `confirmed` → `shipped` → `delivered` | `cancelled` | `returned`

#### OrderItem
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| order_id | UUID | FK → Order.id, NOT NULL, INDEX | Pedido |
| product_id | UUID | FK → Product.id, NOT NULL | Produto |
| quantity | INTEGER | NOT NULL, CHECK >= 1 | Quantidade |
| unit_price | DECIMAL(10,2) | NOT NULL | Preço unitário no momento da compra |
| total_price | DECIMAL(10,2) | NOT NULL | unit_price * quantity |

#### Address
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| user_id | UUID | FK → User.id, NOT NULL, INDEX | Usuário |
| street | VARCHAR(255) | NOT NULL | Logradouro |
| number | VARCHAR(20) | NOT NULL | Número |
| complement | VARCHAR(100) | NULLABLE | Complemento |
| neighborhood | VARCHAR(150) | NOT NULL | Bairro |
| city | VARCHAR(150) | NOT NULL | Cidade |
| state | VARCHAR(2) | NOT NULL | UF (sigla) |
| zip_code | VARCHAR(9) | NOT NULL | CEP (formato: 00000-000) |
| is_default | BOOLEAN | NOT NULL, DEFAULT FALSE | Endereço padrão |
| created_at | TIMESTAMP | NOT NULL | Data de criação |
| updated_at | TIMESTAMP | NOT NULL | Data de atualização |

#### Review
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| user_id | UUID | FK → User.id, NOT NULL | Autor da avaliação |
| product_id | UUID | FK → Product.id, NOT NULL, INDEX | Produto avaliado |
| rating | INTEGER | NOT NULL, CHECK 1-5 | Nota (1 a 5 estrelas) |
| comment | TEXT | NULLABLE | Comentário/Resenha |
| created_at | TIMESTAMP | NOT NULL | Data da avaliação |

**Constraint:** UNIQUE(user_id, product_id) – um usuário só pode avaliar um produto uma vez.

#### Coupon
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| code | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Código do cupom |
| discount_type | VARCHAR(20) | NOT NULL, CHECK IN ('percentage','fixed') | Tipo de desconto |
| discount_value | DECIMAL(10,2) | NOT NULL, CHECK > 0 | Valor do desconto |
| min_purchase | DECIMAL(10,2) | NULLABLE | Valor mínimo de compra |
| max_discount | DECIMAL(10,2) | NULLABLE | Teto máximo de desconto |
| valid_from | TIMESTAMP | NOT NULL | Início da validade |
| valid_until | TIMESTAMP | NOT NULL | Fim da validade |
| max_uses | INTEGER | NULLABLE | Limite total de usos |
| used_count | INTEGER | NOT NULL, DEFAULT 0 | Usos já realizados |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Cupom ativo |
| created_at | TIMESTAMP | NOT NULL | Data de criação |

#### Wishlist
| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | UUID | PK | Identificador único |
| user_id | UUID | FK → User.id, NOT NULL | Usuário |
| product_id | UUID | FK → Product.id, NOT NULL | Produto |
| created_at | TIMESTAMP | NOT NULL | Data de adição |

**Constraint:** UNIQUE(user_id, product_id)

### 6.3 Considerações de Modelagem

- **UUIDs como PK:** Melhor que auto-increment para APIs públicas (não expõe volume de dados), facilita sharding futuro, evita race conditions em ambientes distribuídos.
- **Preço histórico no OrderItem:** `unit_price` é salvo no momento da compra. Se o preço do produto mudar depois, o pedido mantém o valor original.
- **Soft delete vs Hard delete:** Produtos e categorias usam `is_active` (soft delete). Pedidos NUNCA são deletados. Usuários podem ser desativados mas não deletados (integridade referencial).
- **Slug para URLs amigáveis:** Gerado automaticamente a partir do título/nome. Único e indexado para busca eficiente.

---

## 7. Fluxo de Autenticação

### 7.1 Visão Geral do Fluxo

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Cliente  │     │  Backend  │     │  Database │     │  Cliente  │
│ (Browser) │     │ (FastAPI) │     │ (Postgres)│     │ (Armaz.)  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                 │               │                 │
     │ 1. POST /auth/register         │                 │
     │ {email, password, name}        │                 │
     │────────────────▶│               │                 │
     │                 │ 2. Valida dados                │
     │                 │ 3. Hash senha (bcrypt)         │
     │                 │ 4. Insere user                 │
     │                 │──────────────▶│                 │
     │                 │ 5. User criado                 │
     │                 │◀──────────────│                 │
     │ 6. 201 Created  │               │                 │
     │◀────────────────│               │                 │
     │                 │               │                 │
     │ 7. POST /auth/login            │                 │
     │ {email, password}              │                 │
     │────────────────▶│               │                 │
     │                 │ 8. Busca user por email         │
     │                 │──────────────▶│                 │
     │                 │ 9. Retorna user                 │
     │                 │◀──────────────│                 │
     │                 │ 10. Verifica senha (bcrypt)     │
     │                 │ 11. Gera Access Token (15min)   │
     │                 │ 12. Gera Refresh Token (7d)     │
     │ 13. 200 OK      │               │                 │
     │ {access_token,  │               │                 │
     │  refresh_token} │               │                 │
     │◀────────────────│               │                 │
     │                 │               │                 │
     │ 14. Armazena tokens            │                 │
     │ access → mem   │               │                 │
     │ refresh →      │               │                 │
     │ httpOnly cookie│               │                 │
     │─────────────────────────────────────────────────▶│
     │                 │               │                 │
     │ 15. GET /api/v1/users/me       │                 │
     │ Authorization: Bearer <access> │                 │
     │────────────────▶│               │                 │
     │                 │ 16. Decodifica JWT              │
     │                 │ 17. Busca user por sub (id)     │
     │                 │──────────────▶│                 │
     │                 │ 18. Retorna user                │
     │                 │◀──────────────│                 │
     │ 19. 200 OK      │               │                 │
     │ {user data}     │               │                 │
     │◀────────────────│               │                 │
     │                 │               │                 │
     │ [Quando access expira]         │                 │
     │ 20. POST /auth/refresh         │                 │
     │ Cookie: refresh_token          │                 │
     │────────────────▶│               │                 │
     │                 │ 21. Valida refresh token        │
     │                 │ 22. Gera novos tokens           │
     │ 23. 200 OK      │               │                 │
     │ {new_access,    │               │                 │
     │  new_refresh}   │               │                 │
     │◀────────────────│               │                 │
```

### 7.2 Detalhamento Técnico

#### Registro (POST /auth/register)
1. Cliente envia `{email, password, full_name}`
2. Backend valida:
   - E-mail formato válido
   - Senha ≥ 8 caracteres, contém letra e número
   - E-mail não cadastrado
3. `password_hash = bcrypt.hash(password, rounds=12)`
4. Cria User com `role='customer'`, `is_active=True`, `email_verified=False`
5. **Fase 2:** Envia e-mail de verificação com token assinado (JWT curto, 1h)
6. Retorna 201 com dados do usuário (sem password_hash)

#### Login (POST /auth/login)
1. Cliente envia `{email, password}`
2. Busca User por e-mail (incluindo inativos)
3. Verifica `is_active` → 403 se inativo
4. Verifica `bcrypt.verify(password, user.password_hash)`
5. Gera tokens:
   - **Access Token:** JWT com payload `{sub: user.id, role: user.role, type: 'access'}`. Expira em 15 minutos.
   - **Refresh Token:** JWT com payload `{sub: user.id, type: 'refresh', jti: uuid4()}`. Expira em 7 dias.
6. **Comparação: storage do refresh token**
   - **Opção A (escolhida):** Stateless – refresh token é auto-contido (JWT com JTI). Revogação via blacklist em Redis (TTL = exp do token).
   - **Opção B:** Armazenar hash do refresh token no banco (tabela `refresh_tokens`). Mais seguro (revogação trivial), mas adiciona complexidade.
   - **Justificativa:** Opção A é suficiente para projeto portfólio. Em produção de larga escala, Opção B seria preferível.
7. Retorna tokens. Access token no body JSON. Refresh token em cookie `httpOnly; Secure; SameSite=Strict; Path=/auth`.

#### Refresh (POST /auth/refresh)
1. Lê refresh_token do cookie httpOnly
2. Decodifica e valida JWT (assinatura, expiração, type=refresh)
3. Verifica se JTI não está na blacklist (Redis)
4. Adiciona JTI antigo à blacklist (rotation – um refresh token só pode ser usado uma vez)
5. Gera novo par de tokens
6. Retorna nova access token + seta novo cookie

#### Logout (POST /auth/logout)
1. Lê refresh_token do cookie
2. Adiciona JTI à blacklist no Redis
3. Remove cookie
4. Retorna 204

### 7.3 Middleware de Autorização

```python
# deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Decodifica JWT e retorna User. Levanta 401 se inválido."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Garante que o usuário é admin. Levanta 403 se não for."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user
```

---

## 8. Fluxo de Compra (Checkout)

### 8.1 Diagrama de Sequência

```
Cliente          Frontend           Backend              Database
  │                 │                  │                    │
  │ 1. Adiciona    │                  │                    │
  │ itens ao       │                  │                    │
  │ carrinho       │                  │                    │
  │────────────────▶│                  │                    │
  │                 │ 2. POST /cart/items                 │
  │                 │─────────────────▶│                    │
  │                 │                  │ 3. Valida estoque  │
  │                 │                  │───────────────────▶│
  │                 │                  │ 4. Cria/atualiza   │
  │                 │                  │ CartItem           │
  │                 │                  │───────────────────▶│
  │                 │ 5. 200 OK        │                    │
  │                 │◀─────────────────│                    │
  │                 │                  │                    │
  │ 6. Clica em    │                  │                    │
  │ "Finalizar     │                  │                    │
  │  Compra"       │                  │                    │
  │────────────────▶│                  │                    │
  │                 │ 7. GET /cart (valida estoque)       │
  │                 │─────────────────▶│                    │
  │                 │ 8. Retorna itens atualizados        │
  │                 │◀─────────────────│                    │
  │                 │                  │                    │
  │                 │ 9. GET /addresses                    │
  │                 │─────────────────▶│                    │
  │                 │ 10. Retorna endereços               │
  │                 │◀─────────────────│                    │
  │                 │                  │                    │
  │ 11. Seleciona   │                  │                    │
  │ endereço,       │                  │                    │
  │ aplica cupom,   │                  │                    │
  │ confirma        │                  │                    │
  │────────────────▶│                  │                    │
  │                 │ 12. POST /orders/checkout           │
  │                 │ {address_id, coupon_code?}          │
  │                 │─────────────────▶│                    │
  │                 │                  │ 13. INICIA TRANSAÇÃO
  │                 │                  │───────────────────▶│
  │                 │                  │ 14. Bloqueia       │
  │                 │                  │ SELECT ... FOR UPDATE
  │                 │                  │ (cart_items + products)
  │                 │                  │───────────────────▶│
  │                 │                  │                    │
  │                 │                  │ 15. Validações:    │
  │                 │                  │ - Carrinho vazio?  │
  │                 │                  │ - EstoqueOK?       │
  │                 │                  │ - Cupom válido?    │
  │                 │                  │ - Endereço é do    │
  │                 │                  │   usuário?         │
  │                 │                  │                    │
  │                 │                  │ 16. Cria Order +   │
  │                 │                  │ OrderItems         │
  │                 │                  │───────────────────▶│
  │                 │                  │                    │
  │                 │                  │ 17. Decrementa     │
  │                 │                  │ estoque            │
  │                 │                  │───────────────────▶│
  │                 │                  │                    │
  │                 │                  │ 18. Limpa carrinho │
  │                 │                  │───────────────────▶│
  │                 │                  │                    │
  │                 │                  │ 19. Incrementa     │
  │                 │                  │ uso do cupom       │
  │                 │                  │───────────────────▶│
  │                 │                  │                    │
  │                 │                  │ 20. COMMIT         │
  │                 │                  │───────────────────▶│
  │                 │                  │                    │
  │                 │ 21. 201 Created  │                    │
  │                 │ {order details}  │                    │
  │                 │◀─────────────────│                    │
  │                 │                  │                    │
  │ 22. Página de   │                  │                    │
  │ confirmação     │                  │                    │
  │◀────────────────│                  │                    │
```

### 8.2 Regras de Negócio do Checkout

1. **Atomicidade:** Todo o checkout ocorre dentro de uma transação SQL. Se qualquer passo falhar, faz ROLLBACK completo.
2. **Lock otimista vs pessimista:**
   - Usamos `SELECT ... FOR UPDATE` (pessimista) nos registros de `cart_items` e `products` afetados. Isso previne race conditions onde dois checkouts simultâneos poderiam vender o mesmo estoque.
   - Alternativa seria optimistic locking com `version` column – mais performático para alta concorrência, mas mais complexo de implementar. Para portfólio, lock pessimista é suficiente e mais seguro.
3. **Validação de estoque:** Se `product.stock_qty < cart_item.quantity` para qualquer item, retorna erro 409 e informa quais itens estão sem estoque.
4. **Cálculo de preço:**
   - `subtotal = sum(item.product.price * item.quantity)`
   - Se produto tem `discount_pct > 0`: `item_price = price * (1 - discount_pct/100)`
   - Cupom aplicado sobre o subtotal (após descontos de produto)
   - Se cupom for `percentage`: `discount = subtotal * (discount_value/100)`, limitado a `max_discount`
   - Se cupom for `fixed`: `discount = discount_value`
   - `total = subtotal - discount_amount + shipping_cost`
5. **Frete:** Na versão inicial, frete fixo por região (tabela de frete simples). Em versão futura, integração com API dos Correios (PicPay ou Melhor Envio).
6. **Cupom:** Validar `valid_from <= now <= valid_until`, `is_active=True`, `(max_uses is None OR used_count < max_uses)`, `min_purchase <= subtotal`.

---

## 9. Regras de Negócio por Entidade

### 9.1 User

| Regra | Descrição |
|-------|-----------|
| R01 | E-mail deve ser único no sistema (case-insensitive) |
| R02 | Senha deve ter no mínimo 8 caracteres, conter ao menos 1 letra e 1 número |
| R03 | Senha é armazenada apenas como hash bcrypt (nunca texto plano) |
| R04 | Ao criar usuário, role padrão é 'customer' |
| R05 | Apenas admins podem criar usuários com role 'admin' |
| R06 | Usuário pode editar apenas seus próprios dados (nome, senha) |
| R07 | Usuário não pode alterar o próprio e-mail sem re-verificação |
| R08 | Usuário não pode alterar a própria role |
| R09 | Ao "deletar", usuário é soft-deleted (`is_active=False`) |
| R10 | Não é possível re-registrar um e-mail de usuário inativo (reativação via suporte/admin) |

### 9.2 Category

| Regra | Descrição |
|-------|-----------|
| R11 | Nome e slug devem ser únicos |
| R12 | Slug é gerado automaticamente do nome (lowercase, hífens) |
| R13 | Uma categoria pode ter subcategorias (self-referencial via `parent_id`) |
| R14 | Ao desativar categoria, produtos vinculados NÃO são afetados (continuam existindo, mas sem categoria visível) |
| R15 | Não é possível deletar categoria com produtos ativos vinculados (deve reassociar ou desativar) |
| R16 | Máximo de 2 níveis de profundidade (categoria → subcategoria). Validar ao criar. |

### 9.3 Product

| Regra | Descrição |
|-------|-----------|
| R17 | Título e slug são obrigatórios e únicos |
| R18 | Slug gerado do título + autor se necessário para evitar colisão |
| R19 | `price` deve ser > 0 |
| R20 | `discount_pct` entre 0 e 100 |
| R21 | `stock_qty` não pode ser negativo |
| R22 | `current_price` (calculado) = `price * (1 - discount_pct / 100)` |
| R23 | Ao listar publicamente, apenas produtos `is_active=True` e `stock_qty > 0` (ou com flag `show_out_of_stock`) |
| R24 | Ao desativar produto, ele não aparece em buscas/listagens públicas |
| R25 | Produtos no carrinho de alguém continuam existindo mesmo se desativados (tratamento no checkout) |

### 9.4 Cart

| Regra | Descrição |
|-------|-----------|
| R26 | Cada usuário tem exatamente 1 carrinho (criado automaticamente no primeiro add) |
| R27 | Carrinho pode ter N itens (CartItem) |
| R28 | Adicionar produto já existente incrementa a quantidade |
| R29 | Quantidade máxima por item: 99 (evita abuso) |
| R30 | Se `quantity` chega a 0, o CartItem é removido |
| R31 | Ao adicionar ao carrinho, validar se produto existe e está ativo |
| R32 | Ao adicionar ao carrinho, NÃO validar estoque (apenas no checkout) – UX melhor |
| R33 | Carrinhos de usuários inativos há 30+ dias podem ser limpos (tarefa assíncrona) |

### 9.5 Order

| Regra | Descrição |
|-------|-----------|
| R34 | Pedido é imutável após criação (exceto status e notes) |
| R35 | Status segue a máquina de estados: `pending → confirmed → shipped → delivered` |
| R36 | Status pode ir para `cancelled` a partir de `pending` ou `confirmed` |
| R37 | Status `returned` só pode vir de `delivered` |
| R38 | Ao cancelar, estoque é reposto (rollback de inventário) |
| R39 | `total` é calculado e salvo no momento da criação (não recalculado depois) |
| R40 | Cliente só pode ver os próprios pedidos |
| R41 | Admin pode ver todos os pedidos e alterar status |
| R42 | Mudança de status registrada em log/histórico (fase 2) |

### 9.6 Review

| Regra | Descrição |
|-------|-----------|
| R43 | Apenas usuários autenticados podem avaliar |
| R44 | Um usuário só pode avaliar um produto uma vez (UNIQUE constraint) |
| R45 | `rating` deve ser inteiro entre 1 e 5 |
| R46 | `comment` é opcional, máximo 2000 caracteres |
| R47 | Usuário pode editar a própria avaliação (mas não pode reavaliar outro produto no lugar) |
| R48 | Usuário pode excluir a própria avaliação |
| R49 | Média de avaliações do produto é calculada (pode ser materializada ou calculada em query) |

### 9.7 Address

| Regra | Descrição |
|-------|-----------|
| R50 | Usuário pode ter múltiplos endereços |
| R51 | Apenas um endereço pode ser `is_default=True` por usuário |
| R52 | Ao criar primeiro endereço, automaticamente é default |
| R53 | Ao definir novo endereço como default, desmarcar o anterior |
| R54 | CEP validado no formato 00000-000 |
| R55 | Usuário só pode manipular os próprios endereços |

### 9.8 Coupon

| Regra | Descrição |
|-------|-----------|
| R56 | Código do cupom é único e case-insensitive |
| R57 | `discount_type` é 'percentage' ou 'fixed' |
| R58 | Se 'percentage', `discount_value` é tratado como percentual (ex: 10 = 10%) |
| R59 | Se 'fixed', `discount_value` é valor em reais |
| R60 | `max_discount` é opcional, aplicável apenas para percentage |
| R61 | Cupom válido se: `is_active=True`, `valid_from <= now <= valid_until`, `used_count < max_uses` (se definido) |
| R62 | `min_purchase` é validado contra o subtotal do pedido (antes do desconto) |
| R63 | `used_count` é incrementado atomicamente no checkout |
| R64 | Apenas 1 cupom por pedido |

### 9.9 Wishlist

| Regra | Descrição |
|-------|-----------|
| R65 | Um usuário não pode adicionar o mesmo produto duas vezes |
| R66 | Produto inativo pode permanecer na wishlist (tratamento visual: "indisponível") |
| R67 | Sem limite de itens na wishlist |
| R68 | Da wishlist, usuário pode adicionar ao carrinho ou remover |

---

## 10. Organização das Rotas da API

### 10.1 Convenções

- **Base URL:** `/api/v1`
- **Formato de resposta padrão:**
  ```json
  {
    "data": { ... } | [ ... ],
    "meta": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "total_pages": 8
    }
  }
  ```
- **Erros:**
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Erro de validação",
      "details": [ ... ]
    }
  }
  ```

### 10.2 Catálogo de Rotas

#### Autenticação – `/api/v1/auth`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/auth/register` | Não | Cadastro de cliente |
| POST | `/auth/login` | Não | Login, retorna tokens |
| POST | `/auth/refresh` | Não (cookie) | Renova tokens |
| POST | `/auth/logout` | Sim | Invalida refresh token |
| POST | `/auth/verify-email` | Não | Verificar e-mail (token) |
| POST | `/auth/forgot-password` | Não | Solicitar reset de senha |
| POST | `/auth/reset-password` | Não | Resetar senha (token) |

#### Usuários – `/api/v1/users`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/users/me` | Sim | Perfil do usuário logado |
| PUT | `/users/me` | Sim | Atualizar perfil |
| PUT | `/users/me/password` | Sim | Alterar senha |
| GET | `/users` | Admin | Listar usuários |
| GET | `/users/{id}` | Admin | Detalhes de usuário |
| PUT | `/users/{id}` | Admin | Atualizar usuário |
| DELETE | `/users/{id}` | Admin | Desativar usuário |

#### Produtos – `/api/v1/products`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/products` | Não | Listar produtos (público) |
| GET | `/products/{slug}` | Não | Detalhes do produto |
| GET | `/products/{slug}/reviews` | Não | Avaliações do produto |
| POST | `/products` | Admin | Criar produto |
| PUT | `/products/{id}` | Admin | Atualizar produto |
| DELETE | `/products/{id}` | Admin | Desativar produto |
| POST | `/products/{id}/image` | Admin | Upload de imagem |

#### Categorias – `/api/v1/categories`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/categories` | Não | Listar categorias |
| GET | `/categories/{slug}` | Não | Detalhes da categoria + produtos |
| GET | `/categories/tree` | Não | Árvore de categorias |
| POST | `/categories` | Admin | Criar categoria |
| PUT | `/categories/{id}` | Admin | Atualizar categoria |
| DELETE | `/categories/{id}` | Admin | Desativar categoria |

#### Carrinho – `/api/v1/cart`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/cart` | Sim | Ver carrinho |
| POST | `/cart/items` | Sim | Adicionar item |
| PUT | `/cart/items/{id}` | Sim | Atualizar quantidade |
| DELETE | `/cart/items/{id}` | Sim | Remover item |
| DELETE | `/cart` | Sim | Limpar carrinho |

#### Pedidos – `/api/v1/orders`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/orders/checkout` | Sim | Criar pedido (checkout) |
| GET | `/orders` | Sim | Meus pedidos |
| GET | `/orders/{id}` | Sim | Detalhes do pedido |
| GET | `/orders/{id}/cancel` | Sim | Solicitar cancelamento |
| GET | `/admin/orders` | Admin | Listar todos pedidos |
| GET | `/admin/orders/{id}` | Admin | Detalhes de qualquer pedido |
| PUT | `/admin/orders/{id}/status` | Admin | Atualizar status |

#### Endereços – `/api/v1/addresses`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/addresses` | Sim | Listar endereços |
| POST | `/addresses` | Sim | Criar endereço |
| PUT | `/addresses/{id}` | Sim | Atualizar endereço |
| DELETE | `/addresses/{id}` | Sim | Remover endereço |
| PUT | `/addresses/{id}/default` | Sim | Definir como padrão |

#### Avaliações – `/api/v1/reviews`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/reviews` | Sim | Criar avaliação |
| PUT | `/reviews/{id}` | Sim | Editar avaliação |
| DELETE | `/reviews/{id}` | Sim | Excluir avaliação |

#### Wishlist – `/api/v1/wishlist`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/wishlist` | Sim | Listar wishlist |
| POST | `/wishlist` | Sim | Adicionar produto |
| DELETE | `/wishlist/{product_id}` | Sim | Remover produto |

#### Cupons – `/api/v1/coupons`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/coupons/validate` | Sim | Validar cupom |
| GET | `/admin/coupons` | Admin | Listar cupons |
| POST | `/admin/coupons` | Admin | Criar cupom |
| PUT | `/admin/coupons/{id}` | Admin | Atualizar cupom |
| DELETE | `/admin/coupons/{id}` | Admin | Desativar cupom |

#### Dashboard – `/api/v1/admin/dashboard`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/admin/dashboard/stats` | Admin | Métricas gerais |
| GET | `/admin/dashboard/sales` | Admin | Vendas por período |
| GET | `/admin/dashboard/top-products` | Admin | Produtos mais vendidos |

---

## 11. Estratégia de Tratamento de Erros

### 11.1 Pirâmide de Exceções

```
Exception
 └── BookCommerceException (base)
      ├── NotFoundException (404)
      │    ├── UserNotFoundException
      │    ├── ProductNotFoundException
      │    ├── CategoryNotFoundException
      │    └── OrderNotFoundException
      ├── ConflictException (409)
      │    ├── EmailAlreadyExistsException
      │    ├── InsufficientStockException
      │    └── DuplicateReviewException
      ├── UnauthorizedException (401)
      │    ├── InvalidCredentialsException
      │    └── TokenExpiredException
      ├── ForbiddenException (403)
      │    ├── InsufficientPermissionException
      │    └── InactiveUserException
      ├── BadRequestException (400)
      │    ├── InvalidCouponException
      │    ├── EmptyCartException
      │    └── InvalidStateTransitionException
      └── ValidationException (422)
```

### 11.2 Exception Handler Global

```python
# core/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class BookCommerceException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

# No main.py ou __init__.py da app
app.add_exception_handler(BookCommerceException, bookcommerce_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

### 11.3 Logging

- Exceções 5xx logadas como ERROR com stacktrace completo
- Exceções 4xx logadas como WARNING (esperadas)
- Logs estruturados em JSON (para ELK/CloudWatch): timestamp, level, request_id, user_id, path, method, status_code, error_code, message
- Em desenvolvimento: logs coloridos no console (rich ou similar)

---

## 12. Estratégia de Validação

### 12.1 Camadas de Validação

| Camada | Responsabilidade | Ferramenta |
|--------|-----------------|------------|
| **Schemas Pydantic** | Tipos, formatos, constraints de entrada | Pydantic v2 (field validators, model validators) |
| **Services** | Regras de negócio, validações cross-field, integridade | Exceções customizadas |
| **Database** | Constraints UNIQUE, CHECK, FK | PostgreSQL |

### 12.2 Padrões Pydantic

```python
# Exemplo: Schema de criação de produto
class ProductCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, pattern=r'^\d{10}|\d{13}$')  # ISBN-10 ou ISBN-13
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    discount_pct: Optional[Decimal] = Field(0, ge=0, le=100)
    stock_qty: int = Field(0, ge=0)
    category_id: UUID
    pages: Optional[int] = Field(None, gt=0)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)

    @field_validator('isbn')
    @classmethod
    def validate_isbn(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Remove hífens e espaços
            v = v.replace('-', '').replace(' ', '')
            if len(v) not in (10, 13):
                raise ValueError('ISBN deve ter 10 ou 13 dígitos')
        return v

    @model_validator(mode='after')
    def validate_discount(self):
        if self.discount_pct and self.discount_pct > 0:
            # Exemplo: livros com desconto > 50% precisam de flag especial
            pass
        return self
```

### 12.3 Frontend – Zod Schemas

```typescript
// Exemplo: Schema de formulário de checkout
const checkoutSchema = z.object({
  address_id: z.string().uuid('Endereço inválido'),
  coupon_code: z.string().max(50).nullable().optional(),
  notes: z.string().max(500).optional(),
});

type CheckoutFormData = z.infer<typeof checkoutSchema>;
```

---

## 13. Estratégia de Segurança

### 13.1 Autenticação e Sessão

| Item | Decisão | Justificativa |
|------|---------|---------------|
| Hash de senha | bcrypt com cost 12 | Padrão da indústria. 12 rounds equilibra segurança e performance (~300ms). |
| Algoritmo JWT | HS256 (simétrico) | Suficiente para monólito. RS256 seria necessário para microsserviços. |
| Access Token TTL | 15 minutos | Curto para limitar janela de ataque. |
| Refresh Token TTL | 7 dias | Balanceia UX (não precisa logar toda hora) e segurança. |
| Refresh Token rotação | Sim | Cada uso gera novo refresh token e invalida o anterior. |
| Refresh Token storage | Cookie httpOnly, Secure, SameSite=Strict | Previne XSS (não acessível via JS) e CSRF (SameSite). |

### 13.2 Autorização (RBAC)

- Roles: `customer`, `admin`
- Implementado via dependências FastAPI: `get_current_user`, `get_current_admin`
- Rotas públicas não exigem autenticação
- Rotas de cliente exigem `get_current_user`
- Rotas de admin exigem `get_current_admin`
- Recurso ownership: usuário só acessa seus próprios pedidos/endereços/carrinho

### 13.3 CORS

```python
# Configuração restritiva
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://bookcommerce.com.br"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

### 13.4 Rate Limiting

| Endpoint | Limite | Janela | Justificativa |
|----------|--------|--------|---------------|
| POST `/auth/login` | 5 | 1 minuto | Prevenir brute force |
| POST `/auth/register` | 3 | 1 hora | Prevenir criação de contas falsas |
| POST `/auth/forgot-password` | 3 | 1 hora | Prevenir spam |
| GET `/products` (público) | 100 | 1 minuto | Proteção contra scraping |
| Demais endpoints autenticados | 60 | 1 minuto | Uso normal |

**Ferramenta:** `slowapi` (integra bem com FastAPI, suporta Redis backend).

### 13.5 Upload de Imagens

- Tamanho máximo: 5 MB
- Formatos permitidos: JPEG, PNG, WebP
- Validação de tipo MIME real (não confiar na extensão), usando `python-magic`
- Armazenamento: disco local em desenvolvimento (com volume Docker), S3 em produção
- Nome do arquivo: UUID aleatório (nunca usar nome original)
- Scan de malware? Não necessário para projeto portfólio

### 13.6 Proteções Adicionais

| Proteção | Implementação |
|----------|---------------|
| SQL Injection | SQLAlchemy ORM (parameterized queries por padrão) |
| XSS | Escapamento automático do React. Headers: `X-Content-Type-Options: nosniff` |
| CSRF | SameSite=Strict nos cookies. Token CSRF não necessário pois o refresh token não é usado diretamente em requests. |
| Clickjacking | Header `X-Frame-Options: DENY` |
| Sniffing | Header `X-Content-Type-Options: nosniff` |
| HSTS | Em produção com HTTPS, header `Strict-Transport-Security` |
| Secrets | Todas as secrets via variáveis de ambiente (`.env`). `.env` no `.gitignore`. `.env.example` com placeholders. |
| Docker | Rodar como usuário não-root. Imagens slim/alpine. Health checks. |

### 13.7 Headers de Segurança (via middleware)

```python
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response
```

---

## 14. Estratégia de Testes

### 14.1 Pirâmide de Testes

```
        ┌──────┐
        │ E2E  │  ← Playwright (fluxos críticos)
        ├──────┤
        │ INT  │  ← pytest + TestClient (rotas, DB real em Docker)
        ├──────┤
        │ UNIT │  ← pytest + mocks (services, utils, validators)
        └──────┘
```

### 14.2 Distribuição

| Camada | Peso | O que testa | Exemplo |
|--------|------|-------------|---------|
| Unitários | 60% | Services (com repo mock), validators, security, utils | `test_cart_service.py`: adicionar item, remover item, validar quantidade |
| Integração | 30% | Rotas completas (HTTP → DB → HTTP), fluxos multi-etapa | `test_order_routes.py`: criar pedido, verificar estoque decrementado, verificar carrinho limpo |
| E2E | 10% | Fluxos de negócio completos no navegador | Registro → login → busca → add carrinho → checkout |

### 14.3 Ferramentas e Configuração

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def engine():
    """Cria engine para banco de teste (PostgreSQL em Docker)."""
    return create_engine(os.getenv("TEST_DATABASE_URL"))

@pytest.fixture(scope="function")
def db_session(engine):
    """Sessão de banco isolada por teste. Rollback automático."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()  # Desfaz tudo
    connection.close()

@pytest.fixture
def client(db_session):
    """TestClient com override de dependência."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client, db_session):
    """Cria usuário e retorna headers com token."""
    # Registra e loga, retorna {"Authorization": "Bearer <token>"}
    ...
```

### 14.4 Exemplos de Testes por Camada

#### Unitário (Service)
```python
def test_add_to_cart_creates_new_item(mock_cart_repo, mock_product_repo, cart_service):
    mock_product_repo.get_by_id.return_value = Product(id="p1", price=50, stock_qty=10)
    mock_cart_repo.get_or_create.return_value = Cart(id="c1", user_id="u1")

    result = cart_service.add_item(user_id="u1", product_id="p1", quantity=2)

    assert result.product_id == "p1"
    assert result.quantity == 2
```

#### Integração (Rota)
```python
def test_checkout_success(client, auth_headers, db_session):
    # Arrange: criar produto, adicionar ao carrinho, criar endereço
    product = create_test_product(db_session, price=50, stock_qty=10)
    add_to_cart(client, auth_headers, product.id, quantity=2)
    
    # Act
    response = client.post("/api/v1/orders/checkout", headers=auth_headers, json={
        "address_id": str(address.id)
    })
    
    # Assert
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["total"] == "100.00"
    
    # Verifica side effects
    updated_product = db_session.get(Product, product.id)
    assert updated_product.stock_qty == 8
```

### 14.5 Factories

Usar `factory_boy` para criar dados de teste:

```python
import factory
from app.models import Product, Category

class CategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Category
        sqlalchemy_session_persistence = "flush"
    
    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))
```

### 14.6 Testes E2E (Playwright)

Focar em 3 fluxos críticos:
1. **Registro + primeira compra:** Cadastro → busca → carrinho → checkout → confirmação
2. **Admin CRUD:** Login admin → criar categoria → criar produto → editar → listar
3. **Autenticação:** Login → expiração → refresh → logout

---

## 15. Roadmap de Implementação

### Fase 0 – Setup do Projeto (Dias 1-2)

- [x] Inicializar repositório Git
- [ ] Criar `docker-compose.yml` (PostgreSQL + Redis + backend + frontend)
- [ ] Configurar `.env.example` e `.gitignore`
- [ ] Inicializar projeto FastAPI com `pyproject.toml`
- [ ] Configurar Alembic e criar migration inicial
- [ ] Inicializar projeto React com Vite + TypeScript + Tailwind
- [ ] Configurar ESLint, Prettier (backend e frontend)

**Entregável:** Projeto rodando no Docker. `docker-compose up` sobe backend (hello world), frontend (vite), PostgreSQL e Redis.

### Fase 1 – Fundação do Backend (Dias 3-5)

- [ ] `core/config.py` – Settings com pydantic-settings
- [ ] `core/database.py` – Engine, SessionLocal, Base
- [ ] `core/exceptions.py` – Hierarchy de exceções + handlers globais
- [ ] `core/security.py` – JWT create/decode, bcrypt hash/verify, dependências
- [ ] `models/base.py` – Base model com UUID, created_at, updated_at
- [ ] `models/user.py` – User model
- [ ] `repositories/base.py` – Repository genérico
- [ ] `schemas/common.py` – Paginação, respostas padronizadas
- [ ] `schemas/user.py` – UserCreate, UserResponse, UserUpdate
- [ ] `schemas/auth.py` – LoginRequest, TokenResponse
- [ ] `services/auth_service.py` – Register, login, refresh, logout
- [ ] `api/v1/auth.py` – Rotas de autenticação
- [ ] `api/deps.py` – get_db, get_current_user
- [ ] `api/v1/router.py` – Agregador de routers
- [ ] `main.py` – App factory, middlewares (CORS, security headers), startup/shutdown

**Entregável:** Sistema de autenticação completo. POST /auth/register, POST /auth/login funcionando. Migrations rodando.

### Fase 2 – CRUD de Produtos e Categorias (Dias 6-8)

- [ ] `models/category.py`
- [ ] `models/product.py`
- [ ] `repositories/category_repo.py`
- [ ] `repositories/product_repo.py` (com busca, filtros, paginação)
- [ ] `schemas/category.py`
- [ ] `schemas/product.py`
- [ ] `services/category_service.py`
- [ ] `services/product_service.py`
- [ ] `api/v1/categories.py` – CRUD admin + listagem pública
- [ ] `api/v1/products.py` – CRUD admin + listagem/busca/filtro público
- [ ] `utils/pagination.py`
- [ ] `utils/validators.py` (ISBN validator)

**Entregável:** Produtos e categorias 100% funcionais na API.

### Fase 3 – Frontend Fundação + Área Pública (Dias 9-14)

- [ ] Configurar Axios (`lib/api.ts`)
- [ ] Configurar TanStack Query (`lib/query-client.ts`)
- [ ] Configurar React Router (`routes/`)
- [ ] Componentes de UI (`shared/components/ui/`): Button, Input, Select, Modal, Spinner, Pagination, Skeleton, StarRating
- [ ] Layout (`shared/components/layout/`): Header, Footer, MainLayout
- [ ] Página Home com destaques (mock ou API)
- [ ] Feature `products/`: ProductCard, ProductGrid, ProductFilters, ProductSearch
- [ ] Página de listagem de produtos com paginação, busca e filtros
- [ ] Página de detalhes do produto
- [ ] Página de categoria (lista produtos da categoria)

**Entregável:** Frontend com navegação funcional. Usuário anônimo pode navegar, buscar, filtrar e ver detalhes dos produtos.

### Fase 4 – Autenticação no Frontend (Dias 15-17)

- [ ] `lib/auth.ts` – store token, refresh interceptor
- [ ] Contexto de autenticação (AuthContext)
- [ ] Feature `auth/`: LoginForm, RegisterForm, ForgotPasswordForm
- [ ] `ProtectedRoute` – redireciona para login se não autenticado
- [ ] Páginas de login, cadastro
- [ ] Header condicional (login/logout, nome do usuário)
- [ ] Interceptor Axios: refresh automático quando 401

**Entregável:** Fluxo completo de autenticação no frontend.

### Fase 5 – Carrinho (Dias 18-20)

**Backend:**
- [ ] `models/cart.py`, `models/cart_item.py`
- [ ] `repositories/cart_repo.py`
- [ ] `schemas/cart.py`
- [ ] `services/cart_service.py`
- [ ] `api/v1/cart.py`

**Frontend:**
- [ ] CartContext (contador no header)
- [ ] Feature `cart/`: CartItem, CartSummary, AddToCartButton, MiniCart
- [ ] Página do carrinho
- [ ] Funcionalidade: alterar qtd, remover item, limpar carrinho

**Entregável:** Carrinho funcional, persistido no backend.

### Fase 6 – Checkout e Pedidos (Dias 21-25)

**Backend:**
- [ ] `models/address.py`, `models/order.py`, `models/order_item.py`
- [ ] `repositories/address_repo.py`, `repositories/order_repo.py`
- [ ] `repositories/coupon_repo.py` (básico para cupom)
- [ ] `models/coupon.py` (básico)
- [ ] `schemas/address.py`, `schemas/order.py`
- [ ] `services/order_service.py` – checkout com transação
- [ ] `services/address_service.py`
- [ ] `api/v1/addresses.py`
- [ ] `api/v1/orders.py`
- [ ] `services/coupon_service.py` (validate)

**Frontend:**
- [ ] Feature `profile/` (endereços): AddressForm, AddressList
- [ ] Feature `checkout/`: ShippingForm, AddressSelector, PaymentSummary, CouponInput
- [ ] Página de checkout (multi-step ou single page)
- [ ] Feature `orders/`: OrderCard, OrderTimeline, OrderItemsList
- [ ] Página de histórico de pedidos
- [ ] Página de detalhes do pedido

**Entregável:** Fluxo de compra completo. Cliente pode fazer checkout e ver histórico.

### Fase 7 – Área Administrativa (Dias 26-32)

**Backend:**
- [ ] Rotas admin de produtos, categorias (já existem, talvez refinar)
- [ ] Rotas admin de usuários
- [ ] Rotas admin de pedidos (listar, atualizar status)
- [ ] Rotas admin de cupons (CRUD completo)
- [ ] `services/dashboard_service.py`
- [ ] `api/v1/dashboard.py`

**Frontend:**
- [ ] `AdminLayout` com sidebar
- [ ] Feature `admin/`: AdminSidebar, ProductForm, ProductTable, CategoryForm, CategoryTable, OrderTable, OrderStatusUpdate, UserTable, CouponForm, CouponTable, DashboardStats, SalesChart
- [ ] Página Dashboard admin
- [ ] CRUD de produtos (admin)
- [ ] CRUD de categorias (admin)
- [ ] Gerenciamento de pedidos (admin)
- [ ] CRUD de usuários (admin)
- [ ] CRUD de cupons (admin)

**Entregável:** Painel admin completo.

### Fase 8 – Funcionalidades Complementares (Dias 33-38)

- [ ] Avaliações (backend + frontend)
- [ ] Wishlist (backend + frontend)
- [ ] Recuperação de senha (backend + frontend)
- [ ] Upload de imagens de produtos
- [ ] Modo escuro
- [ ] Toast notifications (react-hot-toast)
- [ ] SEO básico (react-helmet-async)

**Entregável:** Sistema com funcionalidades de produto real.

### Fase 9 – Qualidade e Deploy (Dias 39-42)

- [ ] Testes unitários (services principais)
- [ ] Testes de integração (fluxos de auth, produtos, checkout)
- [ ] Testes E2E com Playwright (3 fluxos críticos)
- [ ] Rate limiting
- [ ] Logging estruturado
- [ ] Dockerfile produção (multi-stage build)
- [ ] docker-compose de produção
- [ ] CI/CD pipeline (GitHub Actions): lint → test → build → deploy
- [ ] Documentação da API (Swagger/OpenAPI – já vem com FastAPI)
- [ ] README.md completo

**Entregável:** Projeto pronto para portfólio, com testes e deploy documentado.

---

## Apêndice A: Decisões Arquiteturais (ADR)

### ADR-001: UUID vs Auto-Increment para PK
**Decisão:** UUID v4
**Justificativa:** Não expõe volume de dados, facilita sharding/distribuição futura, seguro para APIs públicas.
**Trade-off:** Ocupa mais espaço (16 bytes vs 4-8 bytes) e índices são ligeiramente mais lentos. Aceitável para escala de e-commerce de livros.

### ADR-002: Arquitetura em Camadas vs Clean Architecture
**Decisão:** Camadas (Layered)
**Justificativa:** Menor complexidade inicial, 90% dos benefícios. Migrar para Clean/Hexagonal depois é possível e incremental.

### ADR-003: PostgreSQL vs MongoDB
**Decisão:** PostgreSQL (relacional)
**Justificativa:** Dados fortemente relacionais (pedidos, produtos, usuários). Integridade referencial e transações ACID são críticas para e-commerce.

### ADR-004: FastAPI vs Django REST Framework
**Decisão:** FastAPI
**Justificativa:** Performance (async nativo), validação automática via Pydantic, OpenAPI/Swagger built-in, tipagem forte. Mais moderno e com melhor DX para APIs REST.

### ADR-005: Tailwind CSS vs CSS Modules vs Styled Components
**Decisão:** Tailwind CSS
**Justificativa:** Produtividade (utility-first), consistência visual (design system via config), zero runtime cost, ótimo DX com Vite. Padrão da indústria em 2026.

### ADR-006: Feature-based vs Type-based folder structure no Frontend
**Decisão:** Feature-based
**Justificativa:** Melhor escalabilidade, co-localização de código relacionado, facilita code splitting e lazy loading, menos conflitos de merge em times.

---

## Apêndice B: Estilo de Código e Convenções

### Backend (Python)
- **Formatter:** Black (line length 100)
- **Linter:** Ruff
- **Type checker:** MyPy (strict mode gradual)
- **Import order:** isort (compatível com Black)
- **Naming:** snake_case para variáveis/funções, PascalCase para classes, UPPER_CASE para constantes
- **Docstrings:** Google style
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)

### Frontend (TypeScript + React)
- **Formatter:** Prettier
- **Linter:** ESLint (config strict)
- **Naming:** camelCase para variáveis/funções, PascalCase para componentes/tipos, SCREAMING_SNAKE_CASE para constantes
- **Componentes:** Função com arrow function ou named function (consistente por arquivo)
- **Imports:** Ordem: React → libs externas → features → shared → tipos
- **Commits:** Conventional Commits

---

> **Fim do documento de arquitetura.** Todas as decisões aqui documentadas foram ponderadas considerando o contexto de um projeto de portfólio que busca proximidade com ambiente profissional real, equilibrando complexidade, aprendizado e qualidade de código.