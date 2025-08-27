import requests
import os
import pandas as pd
from deep_translator import GoogleTranslator

def get_soup(url,payload):
    response = requests.post(url,headers=headers, json=payload)
    data = response.json()
    return data

def get_json_payload(keyword,start_value):
    payload = {
        "size": 50,
        "from": start_value,
        "aggs": {
            "results_language_oc": {
                "filter": {
                    "match_all": {}
                },
                "aggs": {
                    "http://publications.europa.eu/resource/authority/language/DEU": {
                        "filter": {
                            "bool": {
                                "should": [{
                                    "exists": {
                                        "field": "deContent"
                                    }
                                }, {
                                    "term": {
                                        "facets.language.keyword": "http://publications.europa.eu/resource/authority/language/DEU"
                                    }
                                }, {
                                    "exists": {
                                        "field": "facets.title.de"
                                    }
                                }, {
                                    "term": {
                                        "included.references.language.keyword": "http://publications.europa.eu/resource/authority/language/DEU"
                                    }
                                }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    },
                    "http://publications.europa.eu/resource/authority/language/FRA": {
                        "filter": {
                            "bool": {
                                "should": [{
                                    "exists": {
                                        "field": "frContent"
                                    }
                                }, {
                                    "term": {
                                        "facets.language.keyword": "http://publications.europa.eu/resource/authority/language/FRA"
                                    }
                                }, {
                                    "exists": {
                                        "field": "facets.title.fr"
                                    }
                                }, {
                                    "term": {
                                        "included.references.language.keyword": "http://publications.europa.eu/resource/authority/language/FRA"
                                    }
                                }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    },
                    "http://publications.europa.eu/resource/authority/language/ITA": {
                        "filter": {
                            "bool": {
                                "should": [{
                                    "exists": {
                                        "field": "itContent"
                                    }
                                }, {
                                    "term": {
                                        "facets.language.keyword": "http://publications.europa.eu/resource/authority/language/ITA"
                                    }
                                }, {
                                    "exists": {
                                        "field": "facets.title.it"
                                    }
                                }, {
                                    "term": {
                                        "included.references.language.keyword": "http://publications.europa.eu/resource/authority/language/ITA"
                                    }
                                }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    },
                    "http://publications.europa.eu/resource/authority/language/ROH": {
                        "filter": {
                            "bool": {
                                "should": [{
                                    "exists": {
                                        "field": "rmContent"
                                    }
                                }, {
                                    "term": {
                                        "facets.language.keyword": "http://publications.europa.eu/resource/authority/language/ROH"
                                    }
                                }, {
                                    "exists": {
                                        "field": "facets.title.rm"
                                    }
                                }, {
                                    "term": {
                                        "included.references.language.keyword": "http://publications.europa.eu/resource/authority/language/ROH"
                                    }
                                }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    },
                    "http://publications.europa.eu/resource/authority/language/ENG": {
                        "filter": {
                            "bool": {
                                "should": [{
                                    "exists": {
                                        "field": "enContent"
                                    }
                                }, {
                                    "term": {
                                        "facets.language.keyword": "http://publications.europa.eu/resource/authority/language/ENG"
                                    }
                                }, {
                                    "exists": {
                                        "field": "facets.title.en"
                                    }
                                }, {
                                    "term": {
                                        "included.references.language.keyword": "http://publications.europa.eu/resource/authority/language/ENG"
                                    }
                                }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    }
                }
            },
            "in_force_title": {
                "filter": {
                    "exists": {
                        "field": "data.attributes.dateEntryInForce.xsd:date"
                    }
                },
                "aggs": {
                    "in_force": {
                        "filter": {
                            "bool": {
                                "minimum_should_match": 1,
                                "should": [{
                                    "bool": {
                                        "must_not": {
                                            "term": {
                                                "data.references.inForceStatus.keyword": "https://fedlex.data.admin.ch/vocabulary/enforcement-status/1"
                                            }
                                        },
                                        "must": [{
                                            "range": {
                                                "data.attributes.dateEntryInForce.xsd:date": {
                                                    "lte": "now"
                                                }
                                            }
                                        }, {
                                            "bool": {
                                                "minimum_should_match": 1,
                                                "should": [{
                                                    "bool": {
                                                        "must_not": {
                                                            "exists": {
                                                                "field": "data.attributes.dateEndApplicability.xsd:date"
                                                            }
                                                        }
                                                    }
                                                }, {
                                                    "range": {
                                                        "data.attributes.dateEndApplicability.xsd:date": {
                                                            "gte": "now"
                                                        }
                                                    }
                                                }
                                                ]
                                            }
                                        }, {
                                            "bool": {
                                                "minimum_should_match": 1,
                                                "should": [{
                                                    "bool": {
                                                        "must_not": {
                                                            "exists": {
                                                                "field": "data.attributes.dateNoLongerInForce.xsd:date"
                                                            }
                                                        }
                                                    }
                                                }, {
                                                    "range": {
                                                        "data.attributes.dateNoLongerInForce.xsd:date": {
                                                            "gt": "now"
                                                        }
                                                    }
                                                }
                                                ]
                                            }
                                        }
                                        ]
                                    }
                                }
                                ]
                            }
                        }
                    },
                    "not_in_force": {
                        "filter": {
                            "bool": {
                                "minimum_should_match": 1,
                                "should": [{
                                    "bool": {
                                        "must": [{
                                            "exists": {
                                                "field": "data.attributes.dateEndApplicability.xsd:date"
                                            }
                                        }, {
                                            "bool": {
                                                "must": {
                                                    "range": {
                                                        "data.attributes.dateEndApplicability.xsd:date": {
                                                            "lte": "now"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        ]
                                    }
                                }, {
                                    "bool": {
                                        "must": [{
                                            "exists": {
                                                "field": "data.attributes.dateNoLongerInForce.xsd:date"
                                            }
                                        }, {
                                            "bool": {
                                                "must": {
                                                    "range": {
                                                        "data.attributes.dateNoLongerInForce.xsd:date": {
                                                            "lte": "now"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        ]
                                    }
                                }, {
                                    "bool": {
                                        "must": [{
                                            "exists": {
                                                "field": "data.references.inForceStatus.keyword"
                                            }
                                        }, {
                                            "bool": {
                                                "must": {
                                                    "term": {
                                                        "data.references.inForceStatus.keyword": "https://fedlex.data.admin.ch/vocabulary/enforcement-status/1"
                                                    }
                                                }
                                            }
                                        }
                                        ]
                                    }
                                }
                                ]
                            }
                        }
                    },
                    "not_yet_in_force": {
                        "filter": {
                            "bool": {
                                "must_not": {
                                    "term": {
                                        "data.references.inForceStatus.keyword": "https://fedlex.data.admin.ch/vocabulary/enforcement-status/1"
                                    }
                                },
                                "must": {
                                    "range": {
                                        "data.attributes.dateEntryInForce.xsd:date": {
                                            "gte": "now"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "facets.typeDocumentBroader.keyword": {
                "terms": {
                    "field": "facets.typeDocumentBroader.keyword",
                    "size": 500
                }
            },
            "data.attributes.typeDocument.rdfs:Resource.keyword": {
                "terms": {
                    "field": "data.attributes.typeDocument.rdfs:Resource.keyword",
                    "size": 500
                }
            },
            "data.attributes.processType.rdfs:Resource.keyword": {
                "terms": {
                    "field": "data.attributes.processType.rdfs:Resource.keyword",
                    "size": 500
                }
            },
            "facets.basicAct.processType.keyword": {
                "terms": {
                    "field": "facets.basicAct.processType.keyword",
                    "size": 500
                }
            },
            "data.references.legalResourcePublicationCompleteness.keyword": {
                "terms": {
                    "field": "data.references.legalResourcePublicationCompleteness.keyword",
                    "size": 500
                }
            },
            "facets.publicationCompleteness.keyword": {
                "terms": {
                    "field": "facets.publicationCompleteness.keyword",
                    "size": 500
                }
            },
            "data.attributes.legalResourceGenre.rdfs:Resource.keyword": {
                "terms": {
                    "field": "data.attributes.legalResourceGenre.rdfs:Resource.keyword",
                    "size": 500
                }
            },
            "facets.explanatoryReportListPerLanguage.fr": {
                "terms": {
                    "field": "facets.explanatoryReportListPerLanguage.fr",
                    "size": 500
                }
            },
            "rights_collections": {
                "filter": {
                    "bool": {
                        "should": [{
                            "exists": {
                                "field": "facets.theme.themeId"
                            }
                        }, {
                            "exists": {
                                "field": "facets.taxonomyId"
                            }
                        }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "aggs": {
                    "internal": {
                        "filter": {
                            "bool": {
                                "must_not": [{
                                    "bool": {
                                        "filter": {
                                            "prefix": {
                                                "facets.theme.themeId": "0."
                                            }
                                        }
                                    }
                                }, {
                                    "bool": {
                                        "filter": {
                                            "prefix": {
                                                "facets.taxonomyId": "0."
                                            }
                                        }
                                    }
                                }
                                ]
                            }
                        }
                    },
                    "international": {
                        "filter": {
                            "bool": {
                                "should": [{
                                    "bool": {
                                        "filter": {
                                            "prefix": {
                                                "facets.theme.themeId": "0."
                                            }
                                        }
                                    }
                                }, {
                                    "bool": {
                                        "filter": {
                                            "prefix": {
                                                "facets.taxonomyId": "0."
                                            }
                                        }
                                    }
                                }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    }
                }
            },
            "facets.theme.themeUri.keyword": {
                "terms": {
                    "field": "facets.theme.themeUri.keyword",
                    "size": 500
                }
            },
            "data.references.responsibilityOf.keyword": {
                "terms": {
                    "field": "data.references.responsibilityOf.keyword",
                    "size": 500
                }
            },
            "facets.basicAct.responsibilityOf.keyword": {
                "terms": {
                    "field": "facets.basicAct.responsibilityOf.keyword",
                    "size": 500
                }
            },
            "result_count": {
                "value_count": {
                    "field": "data.uri.keyword"
                }
            }
        },
        "query": {
            "bool": {
                "filter": [{
                    "bool": {
                        "filter": [{
                            "terms": {
                                "data.type.keyword": ["Act"]
                            }
                        }, {
                            "bool": {
                                "minimum_should_match": 1,
                                "should": [{
                                    "match": {
                                        "included.attributes.memorialName.xsd:string.keyword": "RO"
                                    }
                                }, {
                                    "match": {
                                        "included.attributes.memorialName.xsd:string.keyword": "AS"
                                    }
                                }, {
                                    "match": {
                                        "included.attributes.memorialName.xsd:string.keyword": "RU"
                                    }
                                }, {
                                    "match": {
                                        "included.attributes.memorialName.xsd:string.keyword": "OC"
                                    }
                                }, {
                                    "match": {
                                        "included.attributes.memorialName.xsd:string.keyword": "CU"
                                    }
                                }
                                ]
                            }
                        }
                        ]
                    }
                }, {
                    "bool": {
                        "should": [{
                            "exists": {
                                "field": "frContent"
                            }
                        }, {
                            "term": {
                                "facets.language.keyword": "http://publications.europa.eu/resource/authority/language/FRA"
                            }
                        }, {
                            "exists": {
                                "field": "facets.title.fr"
                            }
                        }, {
                            "term": {
                                "included.references.language.keyword": "http://publications.europa.eu/resource/authority/language/FRA"
                            }
                        }
                        ],
                        "minimum_should_match": 1
                    }
                }, {
                    "terms": {
                        "data.attributes.typeDocument.rdfs:Resource.keyword": [
                            "https://fedlex.data.admin.ch/vocabulary/resource-type/29",
                            "https://fedlex.data.admin.ch/vocabulary/resource-type/21",
                            "https://fedlex.data.admin.ch/vocabulary/resource-type/28",
                            "https://fedlex.data.admin.ch/vocabulary/resource-type/22"]
                    }
                }
                ],
                "must": [{
                    "match_all": {}
                }, {
                    "bool": {
                        "should": [{
                            "bool": {
                                "should": [{
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [[{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["deContent.content", "deContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "german_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["frContent.content", "frContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "french_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["itContent.content", "itContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "italian_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["rmContent.content", "rmContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "romansh_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["enContent.content", "enContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "english_standard"
                                            }
                                        }
                                        ]]
                                    }
                                }, {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [[{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["deContent.content", "deContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "german_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["frContent.content", "frContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "french_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["itContent.content", "itContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "italian_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["rmContent.content", "rmContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "romansh_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["enContent.content", "enContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "english_standard"
                                            }
                                        }
                                        ]]
                                    }
                                }, {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [[{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["deContent.content", "deContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "german_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["frContent.content", "frContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "french_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["itContent.content", "itContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "italian_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["rmContent.content", "rmContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "romansh_standard"
                                            }
                                        }
                                        ], [{
                                            "simple_query_string": {
                                                "query": keyword,
                                                "fields": ["enContent.content", "enContent.title"],
                                                "default_operator": "OR",
                                                "boost": 1000,
                                                "analyzer": "english_standard"
                                            }
                                        }
                                        ]]
                                    }
                                }
                                ],
                                "minimum_should_match": 1
                            }
                        }, {
                            "multi_match": {
                                "query": keyword,
                                "fields": ["facets.title.de^100", "facets.titleAlternative.de", "facets.titleShort.de",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/DEU^100",
                                           "facets.title.fr^100", "facets.titleAlternative.fr", "facets.titleShort.fr",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/FRA^100",
                                           "facets.title.it^100", "facets.titleAlternative.it", "facets.titleShort.it",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/ITA^100",
                                           "facets.title.rm^100", "facets.titleAlternative.rm", "facets.titleShort.rm",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/ROH^100",
                                           "facets.title.en^100", "facets.titleAlternative.en", "facets.titleShort.en",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/ENG^100"],
                                "boost": 10,
                                "type": "phrase_prefix"
                            }
                        }, {
                            "query_string": {
                                "query": keyword,
                                "fields": ["facets.title.de^100", "facets.titleAlternative.de", "facets.titleShort.de",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/DEU^100",
                                           "facets.title.fr^100", "facets.titleAlternative.fr", "facets.titleShort.fr",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/FRA^100",
                                           "facets.title.it^100", "facets.titleAlternative.it", "facets.titleShort.it",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/ITA^100",
                                           "facets.title.rm^100", "facets.titleAlternative.rm", "facets.titleShort.rm",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/ROH^100",
                                           "facets.title.en^100", "facets.titleAlternative.en", "facets.titleShort.en",
                                           "facets.memorialLabel.http://publications.europa.eu/resource/authority/language/ENG^100"],
                                "default_operator": "and",
                                "boost": 1000
                            }
                        }, {
                            "bool": {
                                "must": [{
                                    "bool": {
                                        "should": [{
                                            "has_child": {
                                                "type": "text_content",
                                                "query": {
                                                    "nested": {
                                                        "path": "deContent",
                                                        "query": {
                                                            "simple_query_string": {
                                                                "query": keyword,
                                                                "fields": ["deContent.content", "deContent.title"],
                                                                "default_operator": "OR",
                                                                "boost": 1000,
                                                                "analyzer": "french_standard"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }, {
                                            "has_child": {
                                                "type": "text_content",
                                                "query": {
                                                    "nested": {
                                                        "path": "frContent",
                                                        "query": {
                                                            "simple_query_string": {
                                                                "query": keyword,
                                                                "fields": ["frContent.content", "frContent.title"],
                                                                "default_operator": "OR",
                                                                "boost": 1000,
                                                                "analyzer": "french_standard"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }, {
                                            "has_child": {
                                                "type": "text_content",
                                                "query": {
                                                    "nested": {
                                                        "path": "itContent",
                                                        "query": {
                                                            "simple_query_string": {
                                                                "query": keyword,
                                                                "fields": ["itContent.content", "itContent.title"],
                                                                "default_operator": "OR",
                                                                "boost": 1000,
                                                                "analyzer": "french_standard"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }, {
                                            "has_child": {
                                                "type": "text_content",
                                                "query": {
                                                    "nested": {
                                                        "path": "rmContent",
                                                        "query": {
                                                            "simple_query_string": {
                                                                "query": keyword,
                                                                "fields": ["rmContent.content", "rmContent.title"],
                                                                "default_operator": "OR",
                                                                "boost": 1000,
                                                                "analyzer": "french_standard"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }, {
                                            "has_child": {
                                                "type": "text_content",
                                                "query": {
                                                    "nested": {
                                                        "path": "enContent",
                                                        "query": {
                                                            "simple_query_string": {
                                                                "query": keyword,
                                                                "fields": ["enContent.content", "enContent.title"],
                                                                "default_operator": "OR",
                                                                "boost": 1000,
                                                                "analyzer": "french_standard"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        ],
                                        "minimum_should_match": 1
                                    }
                                }
                                ]
                            }
                        }
                        ],
                        "minimum_should_match": 1
                    }
                }, {
                    "bool": {
                        "should": [[{
                            "bool": {
                                "must_not": {
                                    "term": {
                                        "data.references.inForceStatus.keyword": "https://fedlex.data.admin.ch/vocabulary/enforcement-status/1"
                                    }
                                },
                                "must": [{
                                    "range": {
                                        "data.attributes.dateEntryInForce.xsd:date": {
                                            "lte": "now"
                                        }
                                    }
                                }, {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [{
                                            "bool": {
                                                "must_not": {
                                                    "exists": {
                                                        "field": "data.attributes.dateEndApplicability.xsd:date"
                                                    }
                                                }
                                            }
                                        }, {
                                            "range": {
                                                "data.attributes.dateEndApplicability.xsd:date": {
                                                    "gte": "now"
                                                }
                                            }
                                        }
                                        ]
                                    }
                                }, {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [{
                                            "bool": {
                                                "must_not": {
                                                    "exists": {
                                                        "field": "data.attributes.dateNoLongerInForce.xsd:date"
                                                    }
                                                }
                                            }
                                        }, {
                                            "range": {
                                                "data.attributes.dateNoLongerInForce.xsd:date": {
                                                    "gt": "now"
                                                }
                                            }
                                        }
                                        ]
                                    }
                                }
                                ]
                            }
                        }
                        ]],
                        "minimum_should_match": 1
                    }
                }
                ],
                "should": []
            }
        },
        "highlight": {
            "pre_tags": ["<span class=\"app-highlighted\">"],
            "post_tags": ["</span>"],
            "fields": {
                "facets.title.fr": {
                    "number_of_fragments": 0
                },
                "facets.title.fr.exact": {
                    "number_of_fragments": 0
                }
            }
        },
        "sort": {
            "_score": {
                "order": "desc"
            }
        }
    }
    return payload

def get_english_text(text):
    translated_text = GoogleTranslator(source='fr', target='en').translate(text)
    return translated_text

def get_regulation_type(text):
    text_lower = text.lower()
    if "loi" in text_lower:
        return "Law",True
    elif "ordonnance" in text_lower:
        return "Ordinance",True
    else:
        return "Unknown",False

def get_dates(source_link):
    link_values = source_link.split("/")
    first_value, second_value = link_values[-3], link_values[-2]

    url = 'https://www.fedlex.admin.ch/elasticsearch/proxy/_search?index=data'
    payload = {"size": 1, "query": {"match": {"data.uri.keyword": f"https://fedlex.data.admin.ch/eli/oc/{first_value}/{second_value}"}}}
    data = get_soup(url,payload)

    adoption_date = data["hits"]["hits"][0]["_source"]["data"]["attributes"]["dateDocument"]["xsd:date"]
    entry_date = data["hits"]["hits"][0]["_source"]["data"]["attributes"]["dateEntryInForce"]["xsd:date"]

    return adoption_date,entry_date

def is_valid_title(title):
    title_lower = title.lower()
    return not any(word.lower() in title_lower for word in excluded_list)

def read_json_content(all_data,key_word):
    for sin_data in all_data:
        try:
            title = sin_data["_source"]["facets"]["title"]["fr"]
            source_link = sin_data["_source"]["graph"].replace("graph", "fr").replace("fedlex.data.admin.ch", "www.fedlex.admin.ch")
            english_title = get_english_text(title)
            reg_type, reg_check = get_regulation_type(title)
            adoption_date, entry_date = get_dates(source_link)
            excluded_check = is_valid_title(title)
            entry = {
                "Jurisdiction": "Switzerland",
                "Original Title": title,
                "English Translation": english_title,
                "Type of Regulation": reg_type,
                "Source": source_link,
                "Date of adoption": adoption_date,
                "Entry Into Force Date": entry_date,
                "Remarks": key_word
            }
            if (excluded_check and reg_check and entry["Source"] not in completed_sources and entry["Original Title"] not in completed_list):
                print(entry)
                results.append(entry)
                completed_list.append(entry["Original Title"])
                completed_sources.append(entry["Source"])

        except Exception as error:
            error_list.append(str(error))


headers = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "connection": "keep-alive",
    "content-length": "13994",
    "content-type": "application/json",
    "host": "www.fedlex.admin.ch",
    "origin": "https://www.fedlex.admin.ch",
    "pragma": "no-cache",
    "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}

excluded_list = ["modification","appropriation","budget","révoqué","aéroport","compagnie aérienne","rendez-vous","nommé","patient","coronavirus","COVID-19"]

base_url = "https://laws-lois.justice.gc.ca"
results = []
error_list = []
completed_list =[]
completed_sources = []
out_excel_file = os.path.join(os.getcwd(), "Switzerland.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def main():
    for sin_key in keyword_list:
        try:
            corrected_keyword = f"\"{sin_key}\""
            starting_value = "0"
            while True:
                json_payload = get_json_payload(corrected_keyword,starting_value)
                url = 'https://www.fedlex.admin.ch/elasticsearch/proxy/_search?index=data'
                last_data_collection = get_soup(url,json_payload)
                data = last_data_collection["hits"]["hits"]
                if not data:
                    break
                starting_value = int(starting_value)+50
                read_json_content(data,sin_key)

        except Exception as error:
            error_list.append(str(error))

    df = pd.DataFrame(results)
    df.to_excel(out_excel_file, index=False)

if __name__ == "__main__":
    main()