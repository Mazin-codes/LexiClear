def get_retriever(db):

    retriever = db.as_retriever(
        search_kwargs={"k": 5}
    )

    return retriever