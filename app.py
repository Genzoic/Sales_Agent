import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# Set up session state to store data between interactions
if 'source_company_data' not in st.session_state:
    st.session_state.source_company_data = ""
if 'target_company_data' not in st.session_state:
    st.session_state.target_company_data = ""
if 'leads' not in st.session_state:
    st.session_state.leads = []

# Initialize ChatGroq
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Function to extract text content from a single page
def get_text_from_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extract all text from the page
            text = ' '.join([p.get_text() for p in soup.find_all('p')])
            return text
        else:
            return ""
    except requests.RequestException as e:
        return ""

# Input for URLs
input_urls = st.text_area("Enter URLs (separated by newline, comma, or space):")
urls = [url.strip() for url in input_urls.replace(",", "\n").replace(" ", "\n").splitlines() if url.strip()]

# Button to trigger extraction
if st.button("Extract Text"):
    if not urls:
        st.warning("Please enter at least one URL.")
    else:
        # Clear previous data
        st.session_state.source_company_data = ""
        
        # Loop through each URL to extract text content
        for url in urls:
            st.subheader(f"Text content from {url}")
            text = get_text_from_page(url)
            if text:
                st.session_state.source_company_data += text + " "
                st.write(text)
            else:
                st.write("No text content found.")
        
        # Check if `source_company_data` has accumulated content
        if st.session_state.source_company_data.strip():
            st.write("Source Company Data Collected:")
            st.write(st.session_state.source_company_data)
        else:
            st.warning("Source company data is empty.")

        # Generate leads
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    '''You are an expert sales agent. You will be provided data regarding a company and you have to analyze it thoroughly and provide relevant product/service titles having word length at most 7. No need to describe these titles.
                      Also, remember these titles will be searched over the internet to generate sales leads, so they should be relevant to the company's business.Try to analyze and find out any services that are being offered in the market of that domain.
                    Make sure the output is in the form of a list of titles, separated by commas such as , title1, title2, title3,.......... Just provide the titles, no need to provide any other information.
                    Gnerate at most 10 titles, which should be relevant to the company's business.'''
                ),
                ("human", "{input}"),
            ]
        )
        
        chain = prompt | llm
        response = chain.invoke({"input": st.session_state.source_company_data})
        
        # Store leads in session state
        st.session_state.leads = [lead.strip() for lead in response.content.split(",") if lead.strip()]
        st.write("Generated Leads:", st.session_state.leads)

# Input for target company name
company_name = st.text_input("Enter name of target company:")

# Button to generate email
if st.button("Generate Email"):
    if not company_name:
        st.warning("Please enter a target company name.")
    else:
        # Initialize TavilyClient for search
        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Clear previous target company data
        st.session_state.target_company_data = ""
        
        # Search for each lead's relevance with the target company
        print("Leads are :",st.session_state.leads)
        for lead in st.session_state.leads:
            response = tavily_client.get_search_context(f"{company_name} {lead}")
            print(response)
            st.session_state.target_company_data += response + ""

        # Check if `target_company_data` has accumulated content
        if st.session_state.target_company_data.strip():
            st.write("Target Company Data Collected:")
            st.write(st.session_state.target_company_data)
        else:
            st.warning("Target company data is empty.")
        
        # Prompt to generate personalized email
        prompt_1 = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    '''You are an expert sales agent. You will be provided data regarding a source company, outlining the services/products it offers. You will also be provided with data about a target company and its relation to the services provided by the source company. Analyze both data sets and write a personalized email on behalf of the source company, pitching its products to the target company to land a sale. Ensure the email is tailored and only pitches relevant services, according to the target company's needs.
                    Below are the source company and target company data:
                    {source_company_data},
                    {target_company_data}''',
                ),
            ]
        )
        
        chain_1 = prompt_1 | llm
        final_response = chain_1.invoke({
            "source_company_data": st.session_state.source_company_data,
            "target_company_data": st.session_state.target_company_data
        })
        
        st.write("Generated Email:")
        st.write(final_response.content)
