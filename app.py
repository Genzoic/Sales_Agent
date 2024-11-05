import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(layout="wide")
# Create pages
page = st.sidebar.selectbox("Choose a page", ["Setup", "Customizations"])
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

if page == "Setup":
    # Input for URLs
    st.title("Setup")
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
                        '''You are a skilled sales analyst. You will be given information about a company's products, services, and market. Analyze this data thoroughly and identify five relevant product or service titles that align with the company’s business offerings and the general market in this domain. The titles should be concise (maximum of 7 words) and highly relevant to the company’s market or business focus.

Ensure that the output is presented as a list of titles separated by commas, such as: title1, title2, title3, etc. Only provide the list of titles; do not include any additional details or explanations. Focus on relevance, conciseness, and potential for generating sales leads in the company's industry. Generate no more than five titles.
                    '''
                    ),
                    ("human", "{input}"),
                ]
            )
            
            chain = prompt | llm
            response = chain.invoke({"input": st.session_state.source_company_data})
            
            # Store leads in session state
            st.session_state.leads = [lead.strip() for lead in response.content.split(",") if lead.strip()]
            #st.write("Generated Leads:", st.session_state.leads)
    # Provide input box for final leads
   # st.write("Generated Leads:")
   

# Custom CSS to reduce vertical spacing, button size, and text size
    st.write("Generated Leads:")
    st.markdown(
        """
        <style>
        .lead-item {
            margin: 0;  
            padding: 2px 0;  
            font-size: 14px;  /* Adjust text size */
        }
        .stButton > button {
            height: 20px;  /* Set a smaller height */
            padding: 0;  /* Remove padding */
            font-size: 10px;  /* Adjust font size for button */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Loop through leads in session state
    for lead in st.session_state.leads:
        col1, col2 = st.columns([0.1, 0.9])
        
        with col1:
            if st.button("❌", key=f"remove_{lead}"):
                st.session_state.leads.remove(lead)
        
        with col2:
            st.markdown(f"<div class='lead-item'>{lead}</div>", unsafe_allow_html=True)
        #selected_leads = st.multiselect(
            #"Select from generated leads:",
            #options=st.session_state.leads
    #)

    additional_leads_input = st.text_area(
        "Enter additional leads (separated by commas,total leads should be at most 10):"
    )


    # Button to submit the final leads
    if st.button("Submit Leads"):
        # Combine selected leads and additional leads
        final_leads = st.session_state.leads + [lead.strip() for lead in additional_leads_input.split(",") if lead.strip()]

        # Limit the number of final leads to 10
        if len(final_leads) > 10:
            st.warning("You can enter at most 10 leads. Only the first 10 will be considered.")
            final_leads = final_leads[:10]

        # Update the leads variable with the final leads
        st.session_state.leads = final_leads
        st.write("Final Leads:", st.session_state.leads)

        print("Final leads are :", st.session_state.leads)

    # Button to submit the final leads


    # Limit the number of final leads to 10






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
                        '''You are a highly skilled sales strategist. You will receive information about two companies:

Source Company: Data describing the services or products offered by this company.
Target Company: Data detailing this company's business and its potential relation or needs concerning the source company's offerings.
Your task is to carefully analyze both data sets and craft a personalized sales email from the source company to the target company. The email should:

Be tailored and relevant—highlight only those services/products from the source company that align directly with the needs or business context of the target company.
Avoid a generic pitch—instead, focus on the specific value and advantages the source company's offerings can provide to the target company.
Maintain a professional, persuasive tone aimed at building a relationship and securing a sale.
Output format: Provide a single email message that includes an introductory greeting, a concise, relevant pitch, and a courteous closing statement.

Below are the data sets for the source and target companies: Source Company: {source_company_data} Target Company: {target_company_data}'''
                        ,
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

else:
    st.title("Customizations")