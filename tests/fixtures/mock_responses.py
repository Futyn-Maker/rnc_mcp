"""Mock RNC API responses for testing."""

# ==============================================================================
# Concordance Responses
# ==============================================================================

CONCORDANCE_SUCCESS = {
    "corpusStats": {
        "textCount": 1000000,
        "wordUsageCount": 500000000
    },
    "subcorpStats": {
        "textCount": 50000,
        "wordUsageCount": 25000000
    },
    "queryStats": {
        "textCount": 150,
        "wordUsageCount": 250
    },
    "pagination": {
        "totalPageCount": 15
    },
    "groups": [
        {
            "docs": [
                {
                    "info": {
                        "title": "Test Document",
                        "docExplainInfo": {
                            "items": [
                                {
                                    "parsingFields": [
                                        {
                                            "name": "author",
                                            "value": [{"valString": {"v": "Пушкин А.С."}}]
                                        },
                                        {
                                            "name": "created",
                                            "value": [{"valString": {"v": "1837"}}]
                                        },
                                        {
                                            "name": "header",
                                            "value": [{"valString": {"v": "Евгений Онегин"}}]
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    "snippetGroups": [
                        {
                            "snippets": [
                                {
                                    "sequences": [
                                        {
                                            "words": [
                                                {"text": "Я", "displayParams": {}},
                                                {"text": " ", "displayParams": {}},
                                                {"text": "помню", "displayParams": {"hit": True}},
                                                {"text": " ", "displayParams": {}},
                                                {"text": "чудное", "displayParams": {"hit": True}},
                                                {"text": " ", "displayParams": {}},
                                                {"text": "мгновенье", "displayParams": {}}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

CONCORDANCE_EMPTY = {
    "corpusStats": {
        "textCount": 1000000,
        "wordUsageCount": 500000000
    },
    "subcorpStats": {
        "textCount": 0,
        "wordUsageCount": 0
    },
    "queryStats": {
        "textCount": 0,
        "wordUsageCount": 0
    },
    "pagination": {
        "totalPageCount": 0
    },
    "groups": []
}

CONCORDANCE_MISSING_METADATA = {
    "corpusStats": {
        "textCount": 1000000,
        "wordUsageCount": 500000000
    },
    "subcorpStats": {
        "textCount": 1,
        "wordUsageCount": 5
    },
    "queryStats": {
        "textCount": 1,
        "wordUsageCount": 5
    },
    "pagination": {
        "totalPageCount": 1
    },
    "groups": [
        {
            "docs": [
                {
                    "info": {
                        "title": "Document without metadata"
                    },
                    "snippetGroups": [
                        {
                            "snippets": [
                                {
                                    "sequences": [
                                        {
                                            "words": [
                                                {"text": "test", "displayParams": {"hit": True}}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

CONCORDANCE_NO_HITS = {
    "corpusStats": {
        "textCount": 1000000,
        "wordUsageCount": 500000000
    },
    "subcorpStats": {
        "textCount": 1,
        "wordUsageCount": 10
    },
    "queryStats": {
        "textCount": 1,
        "wordUsageCount": 10
    },
    "pagination": {
        "totalPageCount": 1
    },
    "groups": [
        {
            "docs": [
                {
                    "info": {
                        "title": "Document without hits",
                        "docExplainInfo": {
                            "items": [
                                {
                                    "parsingFields": [
                                        {
                                            "name": "author",
                                            "value": [{"valString": {"v": "Test Author"}}]
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    "snippetGroups": [
                        {
                            "snippets": [
                                {
                                    "sequences": [
                                        {
                                            "words": [
                                                {"text": "word1", "displayParams": {}},
                                                {"text": " ", "displayParams": {}},
                                                {"text": "word2", "displayParams": {}}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

CONCORDANCE_MULTIPLE_DOCS = {
    "corpusStats": {
        "textCount": 1000000,
        "wordUsageCount": 500000000
    },
    "subcorpStats": {
        "textCount": 100,
        "wordUsageCount": 1000
    },
    "queryStats": {
        "textCount": 3,
        "wordUsageCount": 15
    },
    "pagination": {
        "totalPageCount": 5
    },
    "groups": [
        {
            "docs": [
                {
                    "info": {
                        "title": "First Doc",
                        "docExplainInfo": {
                            "items": [
                                {
                                    "parsingFields": [
                                        {
                                            "name": "author",
                                            "value": [{"valString": {"v": "Author 1"}}]
                                        },
                                        {
                                            "name": "created",
                                            "value": [{"valString": {"v": "2000"}}]
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    "snippetGroups": [
                        {
                            "snippets": [
                                {
                                    "sequences": [
                                        {
                                            "words": [
                                                {"text": "example", "displayParams": {"hit": True}},
                                                {"text": " ", "displayParams": {}},
                                                {"text": "text", "displayParams": {}}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "info": {
                        "title": "Second Doc",
                        "docExplainInfo": {
                            "items": [
                                {
                                    "parsingFields": [
                                        {
                                            "name": "author",
                                            "value": [{"valString": {"v": "Author 2"}}]
                                        },
                                        {
                                            "name": "created",
                                            "value": [{"valString": {"v": "2010"}}]
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    "snippetGroups": [
                        {
                            "snippets": [
                                {
                                    "sequences": [
                                        {
                                            "words": [
                                                {"text": "another", "displayParams": {}},
                                                {"text": " ", "displayParams": {}},
                                                {"text": "example", "displayParams": {"hit": True}}
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "sequences": [
                                        {
                                            "words": [
                                                {"text": "second", "displayParams": {}},
                                                {"text": " ", "displayParams": {}},
                                                {"text": "snippet", "displayParams": {"hit": True}}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# ==============================================================================
# Corpus Configuration Responses
# ==============================================================================

CORPUS_CONFIG_MAIN = {
    "sortings": [
        {
            "name": "grcreated",
            "humanReadable": "По дате создания",
            "applicableTo": ["CONCORDANCE", "KWIC"]
        },
        {
            "name": "grauthor",
            "humanReadable": "По автору",
            "applicableTo": ["CONCORDANCE"]
        },
        {
            "name": "random",
            "humanReadable": "Случайный порядок",
            "applicableTo": ["CONCORDANCE", "KWIC", "DOCS"]
        }
    ]
}

CORPUS_CONFIG_NO_SORTINGS = {
    "sortings": []
}

# ==============================================================================
# Attributes Responses
# ==============================================================================

ATTRIBUTES_GRAMMAR = {
    "vals": [
        {
            "valOptions": {
                "v": {
                    "options": [
                        {
                            "value": "S",
                            "title": "Существительное",
                            "suboptions": {
                                "options": [
                                    {"value": "nom", "title": "Именительный падеж"},
                                    {"value": "gen", "title": "Родительный падеж"},
                                    {"value": "dat", "title": "Дательный падеж"},
                                    {"value": "acc", "title": "Винительный падеж"}
                                ]
                            }
                        },
                        {
                            "value": "V",
                            "title": "Глагол",
                            "suboptions": {
                                "options": [
                                    {"value": "praes", "title": "Настоящее время"},
                                    {"value": "praet", "title": "Прошедшее время"}
                                ]
                            }
                        },
                        {
                            "value": "A",
                            "title": "Прилагательное"
                        }
                    ]
                }
            }
        }
    ]
}

ATTRIBUTES_SEMANTIC = {
    "vals": [
        {
            "valOptions": {
                "v": {
                    "options": [
                        {
                            "title": "Таксономия",
                            "suboptions": {
                                "options": [
                                    {"value": "t:hum", "title": "Человек"},
                                    {"value": "t:animal", "title": "Животное"},
                                    {"value": "t:plant", "title": "Растение"}
                                ]
                            }
                        },
                        {
                            "value": "r:concr",
                            "title": "Конкретные предметы"
                        }
                    ]
                }
            }
        }
    ]
}

ATTRIBUTES_SYNTAX = {
    "vals": [
        {
            "valOptions": {
                "v": {
                    "options": [
                        {"value": "root", "title": "Корень предложения"},
                        {"value": "nsubj", "title": "Подлежащее"},
                        {"value": "obj", "title": "Дополнение"},
                        {
                            "value": "clause_main",
                            "title": "Главная клауза",
                            "suboptions": {
                                "options": [
                                    {"value": "clause_sub", "title": "Придаточная клауза"}
                                ]
                            }
                        }
                    ]
                }
            }
        }
    ]
}

ATTRIBUTES_FLAGS = {
    "vals": [
        {
            "valOptions": {
                "v": {
                    "options": [
                        {"value": "capital", "title": "Слово с заглавной буквы"},
                        {"value": "lexred", "title": "Лексический повтор"},
                        {"value": "first", "title": "Первое слово в предложении"},
                        {"value": "last", "title": "Последнее слово в предложении"}
                    ]
                }
            }
        }
    ]
}

ATTRIBUTES_EMPTY = {
    "vals": []
}

# ==============================================================================
# Error Responses
# ==============================================================================

ERROR_401_RESPONSE = {
    "detail": "Invalid authentication credentials"
}

ERROR_404_RESPONSE = {
    "detail": "Not found"
}

ERROR_500_RESPONSE = {
    "detail": "Internal server error"
}

ERROR_MALFORMED_JSON = "This is not valid JSON"
