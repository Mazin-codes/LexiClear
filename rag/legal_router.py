LEGAL_ROUTE = {

    "employment_contract": [
        "labour_law",
        "contract_law"
    ],

    "rental_agreement": [
        "property",
        "contract_law"
    ],

    "consumer_notice": [
        "consumer_law",
        "contract_law"
    ],

    "nda": [
        "privacy",
        "contract_law"
    ],

    "service_agreement": [
        "contract_law"
    ],

    "other": [
        "general"
    ]
}


def get_domains(document_type):
    return LEGAL_ROUTE.get(document_type, ["general"])