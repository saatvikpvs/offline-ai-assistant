def route_query(query):

    query = query.lower()

    if any(word in query for word in ["study","learn","math","science"]):
        return "education"

    if any(word in query for word in ["doctor","health","medicine","fever"]):
        return "medical"

    if any(word in query for word in ["government","scheme","policy"]):
        return "governance"

    return "education"