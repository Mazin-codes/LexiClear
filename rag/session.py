DOCUMENT_SESSION = {
    "document_type": None,
}


def set_document_type(document_type):
    """
    Store the current uploaded document type.
    """
    DOCUMENT_SESSION["document_type"] = document_type


def get_document_type():
    """
    Return the current uploaded document type.
    """
    return DOCUMENT_SESSION["document_type"]