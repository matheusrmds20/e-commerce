"""Seed de demonstração do Papiro.

Popula categorias e livros para a Home e o Acervo terem conteúdo real em
ambiente de desenvolvimento, sem depender de dados inseridos à mão.

Como rodar (a partir de `backend/`):

    python -m scripts.seed            # insere o que faltar (idempotente)
    python -m scripts.seed --reset    # apaga produtos/categorias e recria

Decisões de conteúdo (e por quê):

- **Títulos e autores são reais.** Nome de obra e nome de autor são fatos e não
  são objeto de proteção autoral — toda livraria, biblioteca ou catálogo os
  cita. O que NÃO fazemos:
- **Descrições e sinopses são escritas por nós**, não copiadas de contracapa,
  site de editora ou resenha. Texto de terceiros é obra protegida.
- **Capas são imagens de stock (Unsplash)**, não as capas oficiais das edições.
  A arte da capa pertence ao ilustrador/editora; usar a oficial seria
  reprodução de obra de terceiros.
- Priorizamos **obras em domínio público** e clássicos brasileiros, o que
  combina com o posicionamento editorial do Papiro.

O script é idempotente: rodar duas vezes não duplica registros. A chave natural
é o `slug` de cada produto/categoria.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# O console do Windows costuma usar cp1252, que não cobre acentos nem símbolos
# como "✓". Sem isto, o script executa o seed mas quebra no `print` final.
# `reconfigure` existe a partir do Python 3.7 e é no-op em streams sem suporte.
try:  # pragma: no cover - depende do terminal
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # pragma: no cover
    pass

# Permite rodar tanto `python -m scripts.seed` (a partir de backend/) quanto
# `python backend/scripts/seed.py` (a partir da raiz do repositório).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Importa todos os models para que o registry do SQLAlchemy resolva os
# `relationship()` (Product -> Coupon, Order, CartItem, ...). Sem isso a
# primeira query estoura InvalidRequestError.
import app.models.address  # noqa: F401,E402
import app.models.cart  # noqa: F401,E402
import app.models.cart_item  # noqa: F401,E402
import app.models.category  # noqa: F401,E402
import app.models.coupon  # noqa: F401,E402
import app.models.order  # noqa: F401,E402
import app.models.order_item  # noqa: F401,E402
import app.models.product  # noqa: F401,E402
import app.models.review  # noqa: F401,E402
import app.models.user  # noqa: F401,E402
import app.models.wishlist  # noqa: F401,E402
from app.db.database import SessionLocal  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.product import Product  # noqa: E402

# --------------------------------------------------------------------------
# Imagens de stock (Unsplash — licença livre para uso).
# Reaproveitamos as mesmas URLs que os componentes do front já usam, para o
# visual ficar coerente entre Home, Acervo e Detalhe.
# --------------------------------------------------------------------------
IMG = {
    "biblioteca": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=800&q=80",
    "livro_aberto": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=800&q=80",
    "estante": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=800&q=80",
    "mesa": "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=800&q=80",
    "pilha": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=800&q=80",
    "leitura": "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?auto=format&fit=crop&w=800&q=80",
}

CATEGORIAS = [
    {
        "name": "Ficção",
        "slug": "ficcao",
        "description": "Romances e narrativas que atravessam vidas inteiras.",
        "image_url": IMG["biblioteca"],
    },
    {
        "name": "Não-ficção",
        "slug": "nao-ficcao",
        "description": "Ensaios, história e ideias para pensar o mundo.",
        "image_url": IMG["mesa"],
    },
    {
        "name": "Clássicos",
        "slug": "classicos",
        "description": "Obras que o tempo não conseguiu tornar obsoletas.",
        "image_url": IMG["estante"],
    },
    {
        "name": "Poesia",
        "slug": "poesia",
        "description": "Versos para ler devagar, em voz baixa.",
        "image_url": IMG["livro_aberto"],
    },
]

# --------------------------------------------------------------------------
# Catálogo. `descricao` e `sinopse` são texto nosso (ver nota no topo do
# arquivo). `destaque`/`mais_vendido` alimentam as vitrines da Home.
# Preços são fictícios, apenas para a demonstração fazer sentido.
# --------------------------------------------------------------------------
LIVROS = [
    # ---------------- Ficção ----------------
    {
        "categoria": "ficcao",
        "title": "Dom Casmurro",
        "slug": "dom-casmurro",
        "author": "Machado de Assis",
        "publisher": "Editora Papiro",
        "publication_year": 1899,
        "pages": 256,
        "language": "pt-BR",
        "price": 42.90,
        "discount_pct": 15,
        "stock_qty": 24,
        "description": "Bentinho relembra a juventude e a paixão por Capitu, num dos maiores enigmas da literatura brasileira.",
        "sinopse": "A dúvida que consome o narrador contamina o leitor: traição ou ciúme? Um clássico sobre memória e desconfiança.",
        "image": IMG["pilha"],
        "destaque": True,
        "mais_vendido": True,
    },
    {
        "categoria": "ficcao",
        "title": "A Hora da Estrela",
        "slug": "a-hora-da-estrela",
        "author": "Clarice Lispector",
        "publisher": "Editora Papiro",
        "publication_year": 1977,
        "pages": 96,
        "language": "pt-BR",
        "price": 38.50,
        "stock_qty": 18,
        "description": "Macabéa, nordestina no Rio, vive uma existência quase invisível até um instante de revelação.",
        "sinopse": "O último romance de Clarice, escrito às vésperas de sua morte, sobre a dignidade de uma vida mínima.",
        "image": IMG["livro_aberto"],
        "destaque": True,
    },
    {
        "categoria": "ficcao",
        "title": "Grande Sertão: Veredas",
        "slug": "grande-sertao-veredas",
        "author": "João Guimarães Rosa",
        "publisher": "Editora Papiro",
        "publication_year": 1956,
        "pages": 624,
        "language": "pt-BR",
        "price": 79.90,
        "discount_pct": 10,
        "stock_qty": 12,
        "description": "Riobaldo narra suas andanças de jagunço e a obsessão por Diadorim, numa língua inventada e vertiginosa.",
        "sinopse": "Um monólogo monumental sobre o sertão, o pacto com o diabo e o amor impossível.",
        "image": IMG["estante"],
        "mais_vendido": True,
    },
    {
        "categoria": "ficcao",
        "title": "Vidas Secas",
        "slug": "vidas-secas",
        "author": "Graciliano Ramos",
        "publisher": "Editora Papiro",
        "publication_year": 1938,
        "pages": 176,
        "language": "pt-BR",
        "price": 35.90,
        "stock_qty": 20,
        "description": "A família de Fabiano atravessa o agreste fugindo da seca, com a fome como companheira constante.",
        "sinopse": "Retrato cru e econômico da miséria nordestina, narrado quase sem adjetivos.",
        "image": IMG["biblioteca"],
    },
    {
        "categoria": "ficcao",
        "title": "O Cortiço",
        "slug": "o-cortico",
        "author": "Aluísio Azevedo",
        "publisher": "Editora Papiro",
        "publication_year": 1890,
        "pages": 304,
        "language": "pt-BR",
        "price": 44.00,
        "stock_qty": 16,
        "description": "A vida de uma habitação coletiva onde ambição, desejo e sobrevivência se misturam sem cerimônia.",
        "sinopse": "Marco do naturalismo brasileiro, em que o ambiente molda — e devora — seus personagens.",
        "image": IMG["mesa"],
    },
    {
        "categoria": "ficcao",
        "title": "Memórias Póstumas de Brás Cubas",
        "slug": "memorias-postumas-de-bras-cubas",
        "author": "Machado de Assis",
        "publisher": "Editora Papiro",
        "publication_year": 1881,
        "pages": 368,
        "language": "pt-BR",
        "price": 46.50,
        "discount_pct": 20,
        "stock_qty": 22,
        "description": "Um defunto autor conta, com ironia fina, as tolices de uma vida que não chegou a ser trágica.",
        "sinopse": "O narrador morto inaugura a digressão como método e a ironia como forma de olhar o Brasil.",
        "image": IMG["leitura"],
        "destaque": True,
        "mais_vendido": True,
    },
    # ---------------- Não-ficção ----------------
    {
        "categoria": "nao-ficcao",
        "title": "Raízes do Brasil",
        "slug": "raizes-do-brasil",
        "author": "Sérgio Buarque de Holanda",
        "publisher": "Editora Papiro",
        "publication_year": 1936,
        "pages": 256,
        "language": "pt-BR",
        "price": 58.00,
        "stock_qty": 14,
        "description": "Ensaio clássico sobre o homem cordial e as heranças ibéricas que moldaram a sociedade brasileira.",
        "sinopse": "Uma chave de leitura para entender o Brasil moderno a partir de suas raízes coloniais.",
        "image": IMG["mesa"],
        "destaque": True,
    },
    {
        "categoria": "nao-ficcao",
        "title": "Casa-Grande e Senzala",
        "slug": "casa-grande-e-senzala",
        "author": "Gilberto Freyre",
        "publisher": "Editora Papiro",
        "publication_year": 1933,
        "pages": 528,
        "language": "pt-BR",
        "price": 72.00,
        "discount_pct": 12,
        "stock_qty": 10,
        "description": "Estudo pioneiro sobre a formação da família brasileira sob o regime da economia patriarcal.",
        "sinopse": "Obra fundadora da sociologia brasileira, ainda hoje centro de debates intensos.",
        "image": IMG["biblioteca"],
        "mais_vendido": True,
    },
    {
        "categoria": "nao-ficcao",
        "title": "A Arte da Guerra",
        "slug": "a-arte-da-guerra",
        "author": "Sun Tzu",
        "publisher": "Editora Papiro",
        "publication_year": 2010,
        "pages": 128,
        "language": "pt-BR",
        "price": 29.90,
        "stock_qty": 30,
        "description": "Tratado militar chinês que se tornou manual de estratégia para negócios e decisões difíceis.",
        "sinopse": "Treze capítulos curtos sobre vencer sem lutar — texto de domínio público em nova tradução.",
        "image": IMG["livro_aberto"],
    },
    {
        "categoria": "nao-ficcao",
        "title": "A República",
        "slug": "a-republica",
        "author": "Platão",
        "publisher": "Editora Papiro",
        "publication_year": 2008,
        "pages": 416,
        "language": "pt-BR",
        "price": 64.00,
        "stock_qty": 11,
        "description": "Diálogo sobre justiça, educação e o papel do filósofo na condução da cidade.",
        "sinopse": "A alegoria da caverna e a primeira grande utopia política do Ocidente.",
        "image": IMG["estante"],
    },
    {
        "categoria": "nao-ficcao",
        "title": "Meditações",
        "slug": "meditacoes",
        "author": "Marco Aurélio",
        "publisher": "Editora Papiro",
        "publication_year": 2009,
        "pages": 208,
        "language": "pt-BR",
        "price": 39.90,
        "discount_pct": 18,
        "stock_qty": 26,
        "description": "Anotações privadas de um imperador romano sobre dever, mortalidade e serenidade.",
        "sinopse": "O estoicismo em primeira pessoa: um diário escrito para si mesmo, nunca para publicar.",
        "image": IMG["pilha"],
        "destaque": True,
    },
    {
        "categoria": "nao-ficcao",
        "title": "Ética a Nicômaco",
        "slug": "etica-a-nicomaco",
        "author": "Aristóteles",
        "publisher": "Editora Papiro",
        "publication_year": 2009,
        "pages": 320,
        "language": "pt-BR",
        "price": 59.00,
        "stock_qty": 13,
        "description": "Investigação sobre o bem humano, a virtude como hábito e o sentido da felicidade.",
        "sinopse": "O texto que fundou a ética ocidental, ainda hoje base de qualquer debate sobre caráter.",
        "image": IMG["leitura"],
    },
    # ---------------- Clássicos ----------------
    {
        "categoria": "classicos",
        "title": "Os Lusíadas",
        "slug": "os-lusiadas",
        "author": "Luís de Camões",
        "publisher": "Editora Papiro",
        "publication_year": 1572,
        "pages": 480,
        "language": "pt",
        "price": 68.00,
        "stock_qty": 9,
        "description": "A epopeia das navegações portuguesas, entre mitologia clássica e história marítima.",
        "sinopse": "A obra fundadora da literatura em língua portuguesa, em edição anotada.",
        "image": IMG["estante"],
        "destaque": True,
    },
    {
        "categoria": "classicos",
        "title": "Crime e Castigo",
        "slug": "crime-e-castigo",
        "author": "Fiódor Dostoiévski",
        "publisher": "Editora Papiro",
        "publication_year": 1866,
        "pages": 592,
        "language": "pt-BR",
        "price": 74.90,
        "discount_pct": 15,
        "stock_qty": 15,
        "description": "Raskólnikov comete um assassinato para provar uma teoria e descobre que a culpa cobra juros.",
        "sinopse": "O romance que inaugura a literatura psicológica moderna.",
        "image": IMG["pilha"],
        "mais_vendido": True,
    },
    {
        "categoria": "classicos",
        "title": "Orgulho e Preconceito",
        "slug": "orgulho-e-preconceito",
        "author": "Jane Austen",
        "publisher": "Editora Papiro",
        "publication_year": 1813,
        "pages": 424,
        "language": "pt-BR",
        "price": 52.00,
        "stock_qty": 21,
        "description": "Elizabeth Bennet e o sr. Darcy medem forças entre convenções sociais e vontade própria.",
        "sinopse": "A comédia de costumes que definiu o romance de formação feminino.",
        "image": IMG["livro_aberto"],
        "destaque": True,
        "mais_vendido": True,
    },
    {
        "categoria": "classicos",
        "title": "O Retrato de Dorian Gray",
        "slug": "o-retrato-de-dorian-gray",
        "author": "Oscar Wilde",
        "publisher": "Editora Papiro",
        "publication_year": 1890,
        "pages": 288,
        "language": "pt-BR",
        "price": 48.90,
        "stock_qty": 17,
        "description": "Um jovem permanece belo enquanto seu retrato envelhece e carrega o peso de seus atos.",
        "sinopse": "Fábula moral sobre vaidade e corrupção, escrita com o melhor veneno de Wilde.",
        "image": IMG["mesa"],
    },
    {
        "categoria": "classicos",
        "title": "Moby Dick",
        "slug": "moby-dick",
        "author": "Herman Melville",
        "publisher": "Editora Papiro",
        "publication_year": 1851,
        "pages": 656,
        "language": "pt-BR",
        "price": 84.00,
        "discount_pct": 12,
        "stock_qty": 8,
        "description": "O capitão Ahab persegue a baleia branca que lhe custou a perna, arrastando toda a tripulação.",
        "sinopse": "Aventura marítima e tratado sobre obsessão, em prosa que muda de forma a cada capítulo.",
        "image": IMG["biblioteca"],
    },
    {
        "categoria": "classicos",
        "title": "O Processo",
        "slug": "o-processo",
        "author": "Franz Kafka",
        "publisher": "Editora Papiro",
        "publication_year": 1925,
        "pages": 304,
        "language": "pt-BR",
        "price": 49.90,
        "stock_qty": 19,
        "description": "Josef K. é acusado sem saber de quê e percorre uma burocracia que nunca revela sua regra.",
        "sinopse": "A parábola definitiva sobre o poder anônimo e a culpa sem crime.",
        "image": IMG["leitura"],
        "mais_vendido": True,
    },
    # ---------------- Poesia ----------------
    {
        "categoria": "poesia",
        "title": "Morte e Vida Severina",
        "slug": "morte-e-vida-severina",
        "author": "João Cabral de Melo Neto",
        "publisher": "Editora Papiro",
        "publication_year": 1955,
        "pages": 96,
        "language": "pt-BR",
        "price": 34.90,
        "stock_qty": 23,
        "description": "Um retirante desce o sertão em busca de vida e encontra, a cada passo, a morte como vizinha.",
        "sinopse": "Poema dramático que virou marco da poesia brasileira moderna.",
        "image": IMG["livro_aberto"],
        "destaque": True,
        "mais_vendido": True,
    },
    {
        "categoria": "poesia",
        "title": "A Rosa do Povo",
        "slug": "a-rosa-do-povo",
        "author": "Carlos Drummond de Andrade",
        "publisher": "Editora Papiro",
        "publication_year": 1945,
        "pages": 200,
        "language": "pt-BR",
        "price": 45.00,
        "discount_pct": 10,
        "stock_qty": 18,
        "description": "Poemas escritos durante a guerra, divididos entre o mundo e a consciência de estar nele.",
        "sinopse": "A obra em que Drummond assume a voz coletiva sem abandonar a dúvida pessoal.",
        "image": IMG["pilha"],
        "destaque": True,
    },
    {
        "categoria": "poesia",
        "title": "Poemas Completos de Alberto Caeiro",
        "slug": "poemas-completos-de-alberto-caeiro",
        "author": "Fernando Pessoa",
        "publisher": "Editora Papiro",
        "publication_year": 1946,
        "pages": 176,
        "language": "pt",
        "price": 43.50,
        "stock_qty": 16,
        "description": "O heterônimo que dizia não pensar: apenas ver as coisas como elas são, sem metáfora.",
        "sinopse": "A poesia mais simples e mais radical de Pessoa, assinada por seu mestre fictício.",
        "image": IMG["mesa"],
    },
    {
        "categoria": "poesia",
        "title": "Sonetos",
        "slug": "sonetos-luis-de-camoes",
        "author": "Luís de Camões",
        "publisher": "Editora Papiro",
        "publication_year": 2007,
        "pages": 160,
        "language": "pt",
        "price": 32.00,
        "stock_qty": 25,
        "description": "Versos sobre amor, desconcerto do mundo e o passar implacável do tempo.",
        "sinopse": "O lirismo camoniano reunido, em edição de bolso.",
        "image": IMG["biblioteca"],
    },
    {
        "categoria": "poesia",
        "title": "Toda Poesia",
        "slug": "toda-poesia-paulo-leminski",
        "author": "Paulo Leminski",
        "publisher": "Editora Papiro",
        "publication_year": 2013,
        "pages": 424,
        "language": "pt-BR",
        "price": 66.00,
        "discount_pct": 20,
        "stock_qty": 20,
        "description": "A obra poética reunida de quem fazia do verso curto uma forma de precisão e humor.",
        "sinopse": "Do haikai ao poema longo, o percurso completo de um dos poetas mais populares do Brasil.",
        "image": IMG["leitura"],
        "mais_vendido": True,
    },
    {
        "categoria": "poesia",
        "title": "Poesia Completa",
        "slug": "poesia-completa-cecilia-meireles",
        "author": "Cecília Meireles",
        "publisher": "Editora Papiro",
        "publication_year": 2001,
        "pages": 720,
        "language": "pt-BR",
        "price": 89.00,
        "stock_qty": 7,
        "description": "A trajetória inteira de uma poeta que fez da musicalidade sua assinatura.",
        "sinopse": "Volume definitivo para quem quer ler Cecília do começo ao fim.",
        "image": IMG["estante"],
        "destaque": True,
    },
]


def seed(reset: bool = False) -> None:
    """Cria categorias e produtos. Idempotente por `slug`."""
    db = SessionLocal()
    try:
        if reset:
            print("  --reset: removendo produtos e categorias existentes...")
            db.query(Product).delete()
            db.query(Category).delete()
            db.commit()

        # --- Categorias ---
        ids_por_slug: dict[str, int] = {}
        criadas = 0
        for dados in CATEGORIAS:
            existente = (
                db.query(Category).filter(Category.slug == dados["slug"]).first()
            )
            if existente:
                ids_por_slug[dados["slug"]] = existente.id
                continue
            cat = Category(**dados, is_active=True)
            db.add(cat)
            db.flush()
            ids_por_slug[dados["slug"]] = cat.id
            criadas += 1

        # --- Produtos ---
        inseridos = 0
        for item in LIVROS:
            if db.query(Product).filter(Product.slug == item["slug"]).first():
                continue

            db.add(
                Product(
                    category_id=ids_por_slug[item["categoria"]],
                    title=item["title"],
                    slug=item["slug"],
                    description=item["description"],
                    author=item["author"],
                    publisher=item.get("publisher"),
                    publication_year=item.get("publication_year"),
                    pages=item.get("pages"),
                    language=item.get("language"),
                    synopsis=item.get("sinopse"),
                    price=item["price"],
                    discount_pct=item.get("discount_pct"),
                    stock_qty=item["stock_qty"],
                    image_url=item.get("image"),
                    is_active=True,
                    is_featured=item.get("destaque", False),
                    is_bestseller=item.get("mais_vendido", False),
                )
            )
            inseridos += 1

        db.commit()

        total_p = db.query(Product).count()
        total_c = db.query(Category).count()
        print(f"  categorias: {criadas} criadas (total {total_c})")
        print(f"  produtos:   {inseridos} inseridos (total {total_p})")
        if not inseridos and not criadas:
            print("  (nada a fazer - o seed ja havia sido aplicado)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Popula o banco com dados de demonstração.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="apaga produtos e categorias antes de reinserir",
    )
    args = parser.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
