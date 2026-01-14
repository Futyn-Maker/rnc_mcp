"""E2E test query fixtures as raw JSON dictionaries.

Queries are wrapped in {"query": {...}} as expected by the concordance tool.
"""

# ==============================================================================
# All Supported Corpus Types
# ==============================================================================

ALL_CORPUS_TYPES = [
    "MAIN", "PAPER", "POETIC", "SPOKEN", "DIALECT", "SCHOOL",
    "SYNTAX", "MULTI", "ACCENT", "MULTIPARC", "KIDS", "CLASSICS", "BLOGS",
]

# ==============================================================================
# Simple Queries
# ==============================================================================

SIMPLE_LEMMA_QUERY = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "дом"}],
    }
}

SIMPLE_WORDFORM_QUERY = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"wordform": "бежал"}],
    }
}

SIMPLE_GRAMM_QUERY = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"gramm": "S"}],
    }
}

# ==============================================================================
# Complex Multi-Token Queries
# ==============================================================================

COMPLEX_QUERY_WITH_SUBCORPUS = {
    "query": {
        "corpus": "MAIN",
        "tokens": [
            {"lemma": "идти", "gramm": "V"},
            {"wordform": "дождь", "dist_min": 1, "dist_max": 3},
        ],
        "subcorpus": {
            "author": "Пушкин",
            "date_range": {"start_year": 1810, "end_year": 1837},
            "author_gender": "male",
        },
        "sort": "grcreated",
        "page": 0,
        "per_page": 20,
        "return_examples": True,
    }
}

MULTITOKEN_SEMANTIC_QUERY = {
    "query": {
        "corpus": "MAIN",
        "tokens": [
            {"semantic": "t:hum"},
            {"lemma": "бежать", "dist_min": 1, "dist_max": 2},
            {"semantic": "r:concr", "dist_min": 1, "dist_max": 1},
        ],
    }
}

# ==============================================================================
# Queries with Different Token Types
# ==============================================================================

QUERY_WITH_SYNTAX = {
    "query": {
        "corpus": "MAIN",
        "tokens": [
            {"syntax": "root"},
            {"syntax": "nsubj", "dist_min": 1, "dist_max": 5},
        ],
    }
}

QUERY_WITH_FLAGS = {
    "query": {
        "corpus": "MAIN",
        "tokens": [
            {"flags": "capital"},
            {"flags": "lexred", "dist_min": 1, "dist_max": 10},
        ],
    }
}

QUERY_WITH_ALL_TOKEN_FIELDS = {
    "query": {
        "corpus": "MAIN",
        "tokens": [
            {
                "lemma": "идти",
                "wordform": "идёт",
                "gramm": "V",
                "syntax": "root",
                "flags": "capital",
            }
        ],
    }
}

# ==============================================================================
# Subcorpus Filter Queries
# ==============================================================================

QUERY_ALL_FILTERS = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "любовь"}],
        "subcorpus": {
            "author": "Толстой",
            "title": "Война и мир",
            "date_range": {"start_year": 1860, "end_year": 1870},
            "author_gender": "male",
            "author_birthyear_range": {"start_year": 1828, "end_year": 1828},
            "disambiguation": "auto",
        },
    }
}

QUERY_WITH_TITLE_FILTER = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "счастье"}],
        "subcorpus": {"title": "Анна Каренина"},
    }
}

QUERY_WITH_DATE_RANGE = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "революция"}],
        "subcorpus": {"date_range": {"start_year": 1917, "end_year": 1920}},
    }
}

QUERY_WITH_FEMALE_AUTHOR = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "любовь"}],
        "subcorpus": {"author_gender": "female"},
    }
}

QUERY_WITH_BIRTHYEAR_RANGE = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "поэзия"}],
        "subcorpus": {"author_birthyear_range": {"start_year": 1799, "end_year": 1799}},
    }
}

QUERY_WITH_DISAMBIGUATION = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "коса"}],
        "subcorpus": {"disambiguation": "manual"},
    }
}

# ==============================================================================
# Pagination and Return Examples Queries
# ==============================================================================

STATISTICS_ONLY_QUERY = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "любовь"}],
        "return_examples": False,
    }
}

QUERY_WITH_CUSTOM_PAGINATION = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "весна"}],
        "page": 2,
        "per_page": 50,
        "return_examples": True,
    }
}

QUERY_FIRST_PAGE = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "счастье"}],
        "page": 0,
        "per_page": 10,
    }
}

# ==============================================================================
# Distance Variations
# ==============================================================================

QUERY_ADJACENT_WORDS = {
    "query": {
        "corpus": "MAIN",
        "tokens": [
            {"lemma": "красный"},
            {"lemma": "цвет", "dist_min": 1, "dist_max": 1},
        ],
    }
}

QUERY_WIDE_DISTANCE = {
    "query": {
        "corpus": "MAIN",
        "tokens": [
            {"lemma": "очень"},
            {"lemma": "красивый", "dist_min": 1, "dist_max": 5},
        ],
    }
}

QUERY_NEGATIVE_DISTANCE = {
    "query": {
        "corpus": "MAIN",
        "tokens": [
            {"lemma": "быстро"},
            {"lemma": "бежать", "dist_min": -2, "dist_max": 2},
        ],
    }
}

# ==============================================================================
# Edge Cases
# ==============================================================================

QUERY_EMPTY_TOKEN = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{}],
    }
}

QUERY_MULTIPLE_EMPTY_TOKENS = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{}, {}, {}],
    }
}

QUERY_WITH_SORT = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "тест"}],
        "sort": "random",
    }
}

# ==============================================================================
# Corpus-Specific Queries
# ==============================================================================

# PAPER (Media)
PAPER_SIMPLE = {
    "query": {
        "corpus": "PAPER",
        "tokens": [{"lemma": "новость"}],
    }
}

PAPER_WITH_DATE = {
    "query": {
        "corpus": "PAPER",
        "tokens": [{"lemma": "экономика"}],
        "subcorpus": {"date_range": {"start_year": 2010, "end_year": 2020}},
    }
}

# POETIC - Pushkin queries
POETIC_PUSHKIN = {
    "query": {
        "corpus": "POETIC",
        "tokens": [{"lemma": "душа"}],
        "subcorpus": {"author": "Пушкин"},
    }
}

POETIC_EUGENE_ONEGIN = {
    "query": {
        "corpus": "POETIC",
        "tokens": [{"lemma": "любовь"}],
        "subcorpus": {"author": "Пушкин", "title": "Евгений Онегин"},
    }
}

# POETIC - кофе/кофий test case
POETIC_KOFE = {
    "query": {
        "corpus": "POETIC",
        "tokens": [{"lemma": "кофе"}],
    }
}

POETIC_KOFIY = {
    "query": {
        "corpus": "POETIC",
        "tokens": [{"lemma": "кофий"}],
    }
}

# SPOKEN
SPOKEN_SIMPLE = {
    "query": {
        "corpus": "SPOKEN",
        "tokens": [{"lemma": "говорить"}],
    }
}

SPOKEN_WITH_GENDER = {
    "query": {
        "corpus": "SPOKEN",
        "tokens": [{"lemma": "понимать"}],
        "subcorpus": {"author_gender": "male"},
    }
}

# DIALECT
DIALECT_SIMPLE = {
    "query": {
        "corpus": "DIALECT",
        "tokens": [{"lemma": "изба"}],
    }
}

DIALECT_WITH_GENDER = {
    "query": {
        "corpus": "DIALECT",
        "tokens": [{"lemma": "деревня"}],
        "subcorpus": {"author_gender": "female"},
    }
}

# SCHOOL
SCHOOL_SIMPLE = {
    "query": {
        "corpus": "SCHOOL",
        "tokens": [{"lemma": "учитель"}],
    }
}

SCHOOL_WITH_DATE = {
    "query": {
        "corpus": "SCHOOL",
        "tokens": [{"lemma": "книга"}],
        "subcorpus": {"date_range": {"start_year": 1950, "end_year": 2000}},
    }
}

# SYNTAX (SynTagRus)
SYNTAX_SIMPLE = {
    "query": {
        "corpus": "SYNTAX",
        "tokens": [{"lemma": "человек"}],
    }
}

SYNTAX_WITH_TAGS = {
    "query": {
        "corpus": "SYNTAX",
        "tokens": [
            {"syntax": "root"},
            {"syntax": "nsubj", "dist_min": 1, "dist_max": 5},
        ],
    }
}

# MULTI (Multimedia)
MULTI_SIMPLE = {
    "query": {
        "corpus": "MULTI",
        "tokens": [{"lemma": "смотреть"}],
    }
}

MULTI_WITH_GENDER = {
    "query": {
        "corpus": "MULTI",
        "tokens": [{"lemma": "видеть"}],
        "subcorpus": {"author_gender": "male"},
    }
}

# ACCENT
ACCENT_SIMPLE = {
    "query": {
        "corpus": "ACCENT",
        "tokens": [{"lemma": "слово"}],
    }
}

ACCENT_WITH_DATE = {
    "query": {
        "corpus": "ACCENT",
        "tokens": [{"lemma": "говорить"}],
        "subcorpus": {"date_range": {"start_year": 1900, "end_year": 2000}},
    }
}

# MULTIPARC
MULTIPARC_SIMPLE = {
    "query": {
        "corpus": "MULTIPARC",
        "tokens": [{"lemma": "время"}],
    }
}

MULTIPARC_WITH_DATE = {
    "query": {
        "corpus": "MULTIPARC",
        "tokens": [{"lemma": "мир"}],
        "subcorpus": {"date_range": {"start_year": 1800, "end_year": 1900}},
    }
}

# KIDS
KIDS_SIMPLE = {
    "query": {
        "corpus": "KIDS",
        "tokens": [{"lemma": "мама"}],
    }
}

KIDS_WITH_GENDER = {
    "query": {
        "corpus": "KIDS",
        "tokens": [{"lemma": "играть"}],
        "subcorpus": {"author_gender": "female"},
    }
}

# CLASSICS
CLASSICS_SIMPLE = {
    "query": {
        "corpus": "CLASSICS",
        "tokens": [{"lemma": "война"}],
    }
}

CLASSICS_WITH_DATE_GENDER = {
    "query": {
        "corpus": "CLASSICS",
        "tokens": [{"lemma": "любовь"}],
        "subcorpus": {
            "date_range": {"start_year": 1850, "end_year": 1900},
            "author_gender": "male",
        },
    }
}

# BLOGS
BLOGS_SIMPLE = {
    "query": {
        "corpus": "BLOGS",
        "tokens": [{"lemma": "писать"}],
    }
}

BLOGS_WITH_DATE = {
    "query": {
        "corpus": "BLOGS",
        "tokens": [{"lemma": "жизнь"}],
        "subcorpus": {"date_range": {"start_year": 2015, "end_year": 2020}},
    }
}

# ==============================================================================
# Zero-Result Edge Cases
# ==============================================================================

NONEXISTENT_WORD = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"wordform": "абвгдежзийклмнопрстуфхцчшщ"}],
    }
}

IMPOSSIBLE_GRAMM = {
    "query": {
        "corpus": "MAIN",
        "tokens": [{"lemma": "собака", "gramm": "V"}],  # собака is not a verb
    }
}

# ==============================================================================
# Query Collections for Parametrized Tests
# ==============================================================================

SIMPLE_QUERIES = {
    "MAIN": SIMPLE_LEMMA_QUERY,
    "PAPER": PAPER_SIMPLE,
    "POETIC": POETIC_PUSHKIN,
    "SPOKEN": SPOKEN_SIMPLE,
    "DIALECT": DIALECT_SIMPLE,
    "SCHOOL": SCHOOL_SIMPLE,
    "SYNTAX": SYNTAX_SIMPLE,
    "MULTI": MULTI_SIMPLE,
    "ACCENT": ACCENT_SIMPLE,
    "MULTIPARC": MULTIPARC_SIMPLE,
    "KIDS": KIDS_SIMPLE,
    "CLASSICS": CLASSICS_SIMPLE,
    "BLOGS": BLOGS_SIMPLE,
}

SUBCORPUS_QUERIES = {
    "MAIN": QUERY_WITH_DATE_RANGE,
    "PAPER": PAPER_WITH_DATE,
    "POETIC": POETIC_EUGENE_ONEGIN,
    "SPOKEN": SPOKEN_WITH_GENDER,
    "DIALECT": DIALECT_WITH_GENDER,
    "SCHOOL": SCHOOL_WITH_DATE,
    "SYNTAX": SYNTAX_WITH_TAGS,
    "MULTI": MULTI_WITH_GENDER,
    "ACCENT": ACCENT_WITH_DATE,
    "MULTIPARC": MULTIPARC_WITH_DATE,
    "KIDS": KIDS_WITH_GENDER,
    "CLASSICS": CLASSICS_WITH_DATE_GENDER,
    "BLOGS": BLOGS_WITH_DATE,
}

ZERO_RESULT_QUERIES = [
    ("nonexistent_word", NONEXISTENT_WORD),
    ("impossible_gramm", IMPOSSIBLE_GRAMM),
]

POETRY_SPECIAL = [
    ("kofe", POETIC_KOFE),
    ("kofiy", POETIC_KOFIY),
]

ADVANCED_QUERIES = [
    ("multitoken", MULTITOKEN_SEMANTIC_QUERY),
    ("syntax", QUERY_WITH_SYNTAX),
    ("flags", QUERY_WITH_FLAGS),
    ("all_fields", QUERY_WITH_ALL_TOKEN_FIELDS),
    ("adjacent", QUERY_ADJACENT_WORDS),
    ("wide_distance", QUERY_WIDE_DISTANCE),
    ("negative_distance", QUERY_NEGATIVE_DISTANCE),
    ("statistics_only", STATISTICS_ONLY_QUERY),
    ("pagination", QUERY_WITH_CUSTOM_PAGINATION),
    ("sorted", QUERY_WITH_SORT),
]
