[33m1233100[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mFrontend[m[33m, [m[1;31morigin/Backend[m[33m, [m[1;32mBackend[m[33m)[m pequenas mudancas
[33m9de3d1b[m adicionado react-router, exceptions de integracao frete e webhook nao aceitando qualquer http response, remocao de comentarios
[33ma895713[m[33m ([m[1;31morigin/Frontend[m[33m)[m fix:E2E
[33m05d66da[m fix:ruff
[33m2407422[m adiciona branch Backend no CI
[33madb8c7a[m fix: fix e refatoracao do projeto + rate limit + maquina de estado
[33m2a13caf[m docs: adiciona README do projeto
[33m8afe730[m fix(cors): restaura origens de dev e torna CORS configuravel por env
[33m37e7cd2[m fix: correcao do ruff
[33mfbff9ec[m fix: webhook travando a fila de execucoes + pequenos fixes
[33m87eafba[m fix: calculo do frete na tela de checkout
[33mb559b5e[m test(shipping): adiciona testes HTTP de integração das rotas de frete
[33m1735e86[m test(shipping): adiciona testes de schema e serviço de frete Melhor Envio
[33m70a5816[m feat(shipping): integra cotação de frete via Melhor Envio
[33m11c3d22[m[33m ([m[1;32mmain[m[33m)[m Merge pull request #4 from matheusrmds20/Backend
[33m6975823[m fix:lint do frontend
[33m624d1ab[m Merge pull request #3 from matheusrmds20/Backend
[33m1b44596[m fix:correcao de bug visual
[33mab7b0bc[m refactor: centraliza exception no service
[33m3c9fa42[m feat(health): adiciona o endpoint health para resposta rapida da api e db
[33md9b5448[m Merge pull request #2 from matheusrmds20/Backend
[33madc00dd[m test(e2e): adapta helpers/specs ao token em memoria + cookie httpOnly
[33mbf041df[m feat(auth, frontend): access token em memoria + refresh silencioso e retry 401
[33m30f7412[m fix(auth): corrige Path do cookie de refresh para /api/v1/auth
[33md778850[m chore(ci): alinha config de tokens dos jobs com o backend (15min / refresh 7d)
[33mf9075c6[m feat(auth, backend): add refresh token (cookie httpOnly) + /auth/refresh e /auth/logout
[33mc732ad9[m Merge pull request #1 from matheusrmds20/Frontend
[33mad39d8b[m fix(e2e): cria fixture emailUnico com padrao de objeto valido
[33md44f821[m fix(deps): declara pwdlib[argon2] e mercadopago no pyproject
[33m3595e01[m fix(ci): nao cancela runs em andamento e usa python -m alembic
[33mc3c036d[m fix(ci): cita os valores de env que quebravam o parse do YAML
[33m623c604[m ci: define as settings obrigatorias tambem no job de testes
[33ma7febb7[m ci: adiciona job E2E (Playwright) com Postgres e Redis
[33mf7fdbc7[m style(backend): zera o ruff (106 -> 0) para o CI nascer verde
[33m4248923[m ci: adiciona pipeline do GitHub Actions (ruff+pytest / eslint+build)
[33m4c63e86[m chore(seguranca): remove credenciais de docs/codigo e exige POSTGRES_PASSWORD no compose
[33m12bbd92[m docs: marca limpeza de historico como concluida e atualiza hashes pos filter-repo
[33m5eff46d[m chore(gitignore): bloqueia bancos locais, chaves e backups apos limpeza do historico
[33mf2d1379[m fix(db): adiciona constraint única em payments(provider, provider_payment_id) ausente das migrations
[33m3e98777[m chore(utils): remove utilitários órfãos não utilizados
[33m1c02d9f[m feat(comprovante): gera recibo PDF por pedido via worker Celery após pagamento aprovado
[33m4c1432f[m fix(email): usa STARTTLS na conexão SMTP (corrige envio no Mailtrap Sandbox)
[33m19f6b38[m feat(email): envia confirmação de pedido via worker Celery ao aprovar pagamento
[33ma193409[m test(carrinho): concorrência real contra Postgres (integracao deselecionada por padrao)
[33md2960f0[m fix(alembic): renomeia constraint de cart_items para unique_cart_item (sincroniza banco com modelo)
[33ma76b118[m feat(carrinho): hardening de concorrência + constraints únicas + fixes de mapeamento e E2E
[33mdb150d9[m fix(pagamentos): usa sandbox_init_point no checkout
[33m02d1b23[m feat(pagamentos): integra Mercado Pago Checkout Pro
[33mab82eeb[m docs: atualiza tabela de services e marca endpoints mantidos por decisao
[33m4ad19af[m docs: registra pendencia de limpeza de historico antes de tornar publico
[33m04abe6f[m chore: adiciona .gitignore e remove artefatos do controle de versao
[33m656e3a0[m feat: edicao de produtos no Admin + limpeza de endpoints orfaos
[33m2cba25d[m FIX: bugs backend
[33m0f05205[m Features
[33meb8294b[m backup
[33m5454c37[m features: modais de endereco e pagamento
[33m1097b4f[m Fix: carrinho agora com itens
[33m7f9b60a[m features: tela de resgistro
[33m4639aec[m Finishing home
[33mb2acc62[m Home
[33m21097b4[m first commit frontend
[33md888636[m first commit
