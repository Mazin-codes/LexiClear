LEGAL_ROUTE = {
    "employment_contract": [
        "employment",
        "contract_law"
    ],
    "rental_agreement": [
        "rental",
        "contract_law"
    ],
    "consumer_notice": [
        "consumer"
    ],
    "nda": [
        "privacy",
        "contract_law"
    ],
    "other": [
        "general"
    ]
}


def get_domains(document_type):
    return LEGAL_ROUTE.get(document_type, ["general"])