def generate_summary_prompt(article):
    prompt = f"""
    Please summarize the following article.
    Title: {article.title}
    Date: {article.date}
    Content: {article.content}
    """
    return prompt

def generate_keywords_prompt(article):
    prompt = f"""
    Please generate a list of 5 to 10 key words that best represent the most significant concepts, ideas, and entities in the article below, which will eventually be used for sparse vector search. 
    Focus on important terms and the source related to the article's subject matter, and avoid generic words like 'update', 'also', 'important', 'recent', or common stop words.
    The words should help a user retrieve data based on semantic search.  
    
    Title: {article.title}
    Date: {article.date}
    Content: {article.summary}
    
    The keywords should be specific and relevant to the article's core ideas.
    """
    
    return prompt
