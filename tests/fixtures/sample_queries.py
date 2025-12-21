"""Sample SearchQuery objects for testing."""

from rnc_mcp.schemas.schemas import (
    SearchQuery,
    TokenRequest,
    SubcorpusFilter,
    DateFilter,
    RncCorpusType,
)

# ==============================================================================
# Simple Queries
# ==============================================================================

SIMPLE_LEMMA_QUERY = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="дом")]
)

SIMPLE_WORDFORM_QUERY = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(wordform="бежал")]
)

SIMPLE_GRAMM_QUERY = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(gramm="S")]
)

# ==============================================================================
# Complex Multi-Token Queries
# ==============================================================================

COMPLEX_QUERY_WITH_SUBCORPUS = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[
        TokenRequest(lemma="идти", gramm="V"),
        TokenRequest(wordform="дождь", dist_min=1, dist_max=3)
    ],
    subcorpus=SubcorpusFilter(
        author="Пушкин",
        date_range=DateFilter(start_year=1810, end_year=1837),
        author_gender="male"
    ),
    sort="grcreated",
    page=0,
    per_page=20,
    return_examples=True
)

MULTITOKEN_SEMANTIC_QUERY = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[
        TokenRequest(semantic="t:hum"),
        TokenRequest(lemma="бежать", dist_min=1, dist_max=2),
        TokenRequest(semantic="r:concr", dist_min=1, dist_max=1)
    ]
)

# ==============================================================================
# Queries with Different Token Types
# ==============================================================================

QUERY_WITH_SYNTAX = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[
        TokenRequest(syntax="root"),
        TokenRequest(syntax="nsubj", dist_min=1, dist_max=5)
    ]
)

QUERY_WITH_FLAGS = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[
        TokenRequest(flags="capital"),
        TokenRequest(flags="lexred", dist_min=1, dist_max=10)
    ]
)

QUERY_WITH_ALL_TOKEN_FIELDS = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[
        TokenRequest(
            lemma="идти",
            wordform="идёт",
            gramm="V",
            syntax="root",
            flags="capital"
        )
    ]
)

# ==============================================================================
# Subcorpus Filter Queries
# ==============================================================================

QUERY_ALL_FILTERS = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="любовь")],
    subcorpus=SubcorpusFilter(
        author="Толстой",
        title="Война и мир",
        date_range=DateFilter(start_year=1860, end_year=1870),
        author_gender="male",
        author_birthyear_range=DateFilter(start_year=1828, end_year=1828),
        disambiguation="auto"
    )
)

QUERY_WITH_TITLE_FILTER = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="счастье")],
    subcorpus=SubcorpusFilter(title="Анна Каренина")
)

QUERY_WITH_DATE_RANGE = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="революция")],
    subcorpus=SubcorpusFilter(
        date_range=DateFilter(start_year=1917, end_year=1920)
    )
)

QUERY_WITH_FEMALE_AUTHOR = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="любовь")],
    subcorpus=SubcorpusFilter(author_gender="female")
)

QUERY_WITH_BIRTHYEAR_RANGE = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="поэзия")],
    subcorpus=SubcorpusFilter(
        author_birthyear_range=DateFilter(start_year=1799, end_year=1799)
    )
)

QUERY_WITH_DISAMBIGUATION = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="коса")],
    subcorpus=SubcorpusFilter(disambiguation="manual")
)

# ==============================================================================
# Pagination and Return Examples Queries
# ==============================================================================

STATISTICS_ONLY_QUERY = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="любовь")],
    return_examples=False
)

QUERY_WITH_CUSTOM_PAGINATION = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="весна")],
    page=2,
    per_page=50,
    return_examples=True
)

QUERY_FIRST_PAGE = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="счастье")],
    page=0,
    per_page=10
)

# ==============================================================================
# Different Corpus Types
# ==============================================================================

QUERY_PAPER_CORPUS = SearchQuery(
    corpus=RncCorpusType.PAPER,
    tokens=[TokenRequest(lemma="новость")]
)

QUERY_POETIC_CORPUS = SearchQuery(
    corpus=RncCorpusType.POETIC,
    tokens=[TokenRequest(lemma="душа")]
)

QUERY_SPOKEN_CORPUS = SearchQuery(
    corpus=RncCorpusType.SPOKEN,
    tokens=[TokenRequest(lemma="говорить")]
)

# ==============================================================================
# Distance Variations
# ==============================================================================

QUERY_ADJACENT_WORDS = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[
        TokenRequest(lemma="красный"),
        TokenRequest(lemma="цвет", dist_min=1, dist_max=1)
    ]
)

QUERY_WIDE_DISTANCE = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[
        TokenRequest(lemma="очень"),
        TokenRequest(lemma="красивый", dist_min=1, dist_max=5)
    ]
)

QUERY_NEGATIVE_DISTANCE = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[
        TokenRequest(lemma="быстро"),
        TokenRequest(lemma="бежать", dist_min=-2, dist_max=2)
    ]
)

# ==============================================================================
# Edge Cases
# ==============================================================================

QUERY_EMPTY_TOKEN = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest()]
)

QUERY_MULTIPLE_EMPTY_TOKENS = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(), TokenRequest(), TokenRequest()]
)

QUERY_WITH_SORT = SearchQuery(
    corpus=RncCorpusType.MAIN,
    tokens=[TokenRequest(lemma="тест")],
    sort="random"
)
