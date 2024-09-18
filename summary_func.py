import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
import time
import os
from dotenv import load_dotenv
from prompts import *
import logging


load_dotenv()
# Get the OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')

# Set up your OpenAI API key
openai.api_key = api_key


def call_openai(prompt, model="gpt-3.5-turbo", max_retries=10, timeout_duration=15):
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    
    start_time = time.time()
    attempt = 0
    
    while attempt < max_retries:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                timeout=timeout_duration
            )
            return response.choices[0].message.content.strip()
        
        except (openai.error.RateLimitError, openai.error.APIError, openai.error.ServiceUnavailableError) as e:
            logging.error(f"Error occurred: {str(e)}, retrying...")
            attempt += 1
            time.sleep(2 ** attempt)  # exponential backoff
        
        except openai.error.TimeoutError as e:
            elapsed_time = time.time() - start_time
            if elapsed_time < timeout_duration * max_retries:
                logging.error(f"Request timed out after {timeout_duration} seconds, sending a new request...")
                attempt += 1
                continue
            else:
                raise e  # re-raise the exception if we're out of time
        
        except Exception as e:
            logging.error(f"Unexpected error occurred: {str(e)}")
            raise e
    
    raise Exception("Failed to get a response within the time limit after multiple retries.")









def map_summary(article, summary_type='deep', model='gpt-3.5-turbo', chunk_size=3000, chunk_overlap=200, verbose=False):

    """
    Performs a map-reduce summarization on the given text with a structured output format.

    Args:
    article (Article): The article object to summarize.
    summary_type (str): The type of summary to generate ('deep', 'mid', or 'shallow').
    model (str): The OpenAI model to use for summarization.
    chunk_size (int): The size of text chunks for splitting.
    chunk_overlap (int): The overlap between text chunks.
    verbose (bool): Whether to print verbose output.

    Returns:
    dict: The structured summary with a title and bullet points.
    """

    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = [Document(page_content=t) for t in text_splitter.split_text(article.content)]  # Access content with dot notation
    
    # Adjust the summary type based on the number of documents
    if summary_type == 'deep' and len(docs) > 20:
        summary_type = 'mid'
        docs = docs[:6] + docs[6:-5:2] + docs[-5:]
    if summary_type == 'mid' and len(docs) >= 40:
        docs = docs[:10] + docs[10:-5:3] + docs[-5:]

    print(article.content)
    # Define prompt templates
    map_prompt = PromptTemplate(template=get_map_prompt_template(article.content, summary_type), input_variables=["text"])
    combine_prompt = PromptTemplate(template=get_combine_prompt_template(), input_variables=["text"])


    summary_chain = load_summarize_chain(
        ChatOpenAI(temperature=0, model_name=model, request_timeout=1000, openai_api_key=api_key),
        chain_type="map_reduce",
        map_prompt=map_prompt,
        combine_prompt=combine_prompt,
        verbose=verbose,
    )

    # Running the summarization process and returning results
    print(f"Summarizing {len(docs)} documents using {summary_type} summary type.")
    print(docs)
    return summary_chain.run(docs)

def get_map_prompt_template(text, summary_type):
    if '***' in text[:5]:
        return f"""
        Below are existing summaries of government releases, separated by '***'.
        After the summary is new, unsummarized text, starting with 'NEW TEXT'.
        Please update the existing summaries with a {summary_type} level summary of the NEW TEXT
        following these guidelines:
        1) Pertains to domestic and global markets only.
        2) Reflects the context of the original document.
        3) Is valuable to an investor.
        4) Adheres to the New York Times' style of writing.
        5) Ends the summary with '***'

        TEXT: 
        {{text}}
        RESPONSE:
        """
    else:
        return f"""
        Below is text from a government document.
        Provide a New York Times style {summary_type} level summary with the following criteria:
        1) Pertains to domestic and global markets only.
        2) Reflects the context of the original document.
        3) Is valuable to an investor.
        4) Provide the summary in structured format with a title and 3-5 bullet points.

        TEXT: 
        {{text}}
        RESPONSE:
        """

def get_combine_prompt_template():
    return """
    Below is a list of excerpts, separated by '***', from a government document.
    Provide a bullet point summary by doing the following:
        1) State a general, actionable title (few words) that the summary is about then list the bullets below it:
        Title: actionable title  
          - Bullet 1
          - Bullet 2 
        2) Do not use more than 10 bullets total. 
        
    EXCERPTS:
    {text}
    RESPONSE:
    """