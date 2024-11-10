import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from tavily import TavilyClient
from dotenv import load_dotenv
from sheet import *
import sqlite3 
from Mail import *  # Add this import
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
import time

# ... existing code ...
sender_details = {"sender_name": "Shrey", "sender_email": "shreyas.joshi@genzoic.com"}
# Function to initialize the SQLite database and create the table
def init_db():
    conn = sqlite3.connect('company_details.db')  # Connect to SQLite database
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            member_name TEXT NOT NULL,
            member_email TEXT NOT NULL,
            member_linkedin TEXT,
            linkedin_profile TEXT,
            first_email TEXT,
            first_email_date DATE,
            first_email_time TIME,
            follow_up_email TEXT,
            follow_up_email_date DATE,
            follow_up_email_time TIME,
            second_follow_up_email TEXT,
            second_follow_up_email_date DATE,
            second_follow_up_email_time TIME
        )
    ''')
    conn.commit()
    conn.close()

# Call the function to initialize the database
init_db()

conn = sqlite3.connect('company_details.db')
cursor = conn.cursor()

# ... existing code ...
def insert_company_detail(company_name, member_name, member_email, member_linkedin, linkedin_profile, first_email, first_email_date, first_email_time, follow_up_email, follow_up_email_date, follow_up_email_time, second_follow_up_email, second_follow_up_email_date, second_follow_up_email_time):
    cursor.execute('''
        SELECT * FROM company_details WHERE company_name=? AND member_name=? AND member_email=?
    ''', (company_name, member_name, member_email))
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO company_details (company_name, member_name, member_email, member_linkedin, linkedin_profile, first_email, first_email_date, first_email_time, follow_up_email, follow_up_email_date, follow_up_email_time, second_follow_up_email, second_follow_up_email_date, second_follow_up_email_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (company_name, member_name, member_email, member_linkedin, linkedin_profile, first_email, first_email_date, first_email_time, follow_up_email, follow_up_email_date, follow_up_email_time, second_follow_up_email, second_follow_up_email_date, second_follow_up_email_time))
        conn.commit()
    else:
        print("Company detail already exists in the database.")

   

def insert_email(company_name, member_name, member_email, email_type, email):
    conn = sqlite3.connect('company_details.db')
    cursor = conn.cursor()
    query = f"UPDATE company_details SET {email_type} = ? WHERE company_name = ? AND member_name = ? AND member_email = ?"
    cursor.execute(query, (email, company_name, member_name, member_email))
    conn.commit()
    conn.close()
# ... existing code ...
load_dotenv()
st.set_page_config(layout="wide")
# Create pages
page = st.sidebar.selectbox("Choose a page", ["Configurations", "Customizations"])
# Set up session state to store data between interactions
if 'source_company_data' not in st.session_state:
    st.session_state.source_company_data = ""
if 'target_company_data' not in st.session_state:
    st.session_state.target_company_data = ""
if 'leads' not in st.session_state:
    st.session_state.leads = set()
if 'previous_leads' not in st.session_state:
     st.session_state.previous_leads = []

if os.path.exists("leads.txt"):
    g=open("leads.txt","r") 
    previous_leads=g.read()
    if previous_leads:
        #st.session_state.leads.extend(previous_leads.split(","))  
        st.session_state.leads.update(previous_leads.split(","))  
        st.session_state.previous_leads=previous_leads.split(",")
    print("leads",st.session_state.leads)
    print("previous leads",st.session_state.previous_leads)
    g.close()
# Initialize ChatGroq
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
class Email(BaseModel):
    subject: str = Field(description="subject of email")
    body: str = Field(description="body of email")

parser = JsonOutputParser(pydantic_object=Email)
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


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

prompt_1 = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        '''You are a highly skilled sales strategist. You will receive information about two companies as well as details of the representative of the target comapny:

Source Company: Data describing the services or products offered by this company.
Target Company: Data detailing this company's business and its potential relation or needs concerning the source company's offerings.
Your task is to carefully analyze both data sets as well as profile of representative of target company and craft a personalized sales email from the source company to the target company. The email should:

Be tailored and relevant—highlight only those services/products from the source company that align directly with the needs or business context of the target company.
Avoid a generic pitch—instead, focus on the specific value and advantages the source company's offerings can provide to the target company.
Maintain a professional, persuasive tone aimed at building a relationship and securing a sale.
Output format: Provide a single email message that includes an introductory greeting, a concise, relevant pitch, and a courteous closing statement.

** Make sure you use only those details of the commpany representatvie, which allign with the target comapny data** 
You should only provide the email, no other content should be provided as output.

You need to return the output in json format having keys as subject and body of email. DO NOT return anything else.
You will also be provided with reciever name and sender name for email
Reciver Name:{reciever_name}, Sender Name : {sender_name}  

Below are the data sets for the source and target companies: Source Company: {source_company_data} Target Company: {target_company_data}
Below is the data regarding target comapny representative : {member_details}'''
                        ,
                    ),
                ]
            )
            
chain_1 = prompt_1 | llm|parser

prompt_2 = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        '''You are a highly skilled sales strategist. You will receive information about two companies:

Source Company: Data describing the services or products offered by this company.
Target Company: Data detailing this company's business and its potential relation or needs concerning the source company's offerings.
You will also recieve previous mails sent to the target company.
Your task is to carefully analyze both data sets as well as profile of representative of target company and craft a personalized sales email from the source company to the target company. The email should:

Be tailored and relevant—highlight only those services/products from the source company that align directly with the needs or business context of the target company.
Avoid a generic pitch—instead, focus on the specific value and advantages the source company's offerings can provide to the target company.
Maintain a professional, persuasive tone aimed at building a relationship and securing a sale.
Output format: Provide a single email message that includes an introductory greeting, a concise, relevant pitch, and a courteous closing statement.

** Make sure you use only those details of the commpany representatvie, which allign with the target comapny data** 

You should only provide the email, no other content should be provided as output.
You need to return the output in json format having keys as subject and body of email.DO NOT return anything else
You will also be provided with reciever name and sender name for email
Reciver Name:{reciever_name}, Sender Name : {sender_name}  

Below are the data sets for the source and target companies: Source Company: {source_company_data} Target Company: {target_company_data}
Below is the data regarding target comapny representative : {member_details}
Below are the emails. 
{email}'''

                        ,
                    ),
                ]
            )
            
chain_2 = prompt_2 | llm|parser
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

if page == "Configurations":
    # Input for URLs
    st.title("Configurations")
    present_urls=""
    if os.path.exists("urls.txt"):
        f=open("urls.txt","r")
        present_urls=f.read()
        f.close()
        #print("present_urls",present_urls)
    

    
    input_urls = st.text_area("Enter URLs (separated by newline, comma, or space):", present_urls)

    urls = [url.strip() for url in input_urls.replace(",", "\n").replace(" ", "\n").splitlines() if url.strip()]
    if present_urls!="":
        for url in urls:
                #st.subheader(f"Text content from {url}")
                text = get_text_from_page(url)
                if text:
                    st.session_state.source_company_data += text + " "
                    #st.write(text)
                else:
                    st.write("No text content found.")
    #print(st.session_state.source_company_data)
    
    
    # Button to trigger extraction
    if st.button("Extract Text"):
        if not urls:
            st.warning("Please enter at least one URL.")
        else:
            # Clear previous data
            st.session_state.source_company_data = ""
           
            f=open("urls.txt","w")
      
            # Loop through each URL to extract text content
            for url in urls:
                f.write(url+"\n")
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
           
            response = chain.invoke({"input": st.session_state.source_company_data})
            
            # Store leads in session state

            #st.session_state.leads.extend( [lead.strip() for lead in response.content.split(",") if lead.strip()])
            st.session_state.leads.update( [lead.strip() for lead in response.content.split(",") if lead.strip()])
            #st.write("Generated Leads:", st.session_state.leads)
    # Provide input box for final leads
   # st.write("Generated Leads:")
   

# Custom CSS to reduce vertical spacing, button size, and text size
    st.write("\n\n\n\n")
    st.write("Generated Search Terms:")
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

    # Loop through leads in session state with enumeration
    for idx, lead in enumerate(st.session_state.leads):
        col1, col2 = st.columns([0.1, 0.9])
        
        with col1:
            if st.button("❌", key=f"remove_{idx}"):  # Use index in the key instead of lead text
                leads_list = list(st.session_state.leads)
                leads_list.remove(lead)
                st.session_state.leads = set(leads_list)
                if(lead in st.session_state.previous_leads):
                    st.session_state.previous_leads.remove(lead)
                    g=open("leads.txt",'w')
                    g.write("\n".join(st.session_state.previous_leads))
                    g.close()
                #st.session_state.leads.pop(idx)  # Use pop with index instead of remove
                st.rerun()  # Rerun the app to refresh the display
        
        with col2:
            st.markdown(f"<div class='lead-item'>{lead}</div>", unsafe_allow_html=True)
        #selected_leads = st.multiselect(
            #"Select from generated leads:",
            #options=st.session_state.leads
    #)
    st.write("\n\n")
    additional_leads_input = st.text_area(
        "Enter additional key words (separated by commas,total leads should be at most 10):"
    )


    # Button to submit the final leads
    st.write("\n\n\n")
    if st.button("Submit Search Terms"):
        # Combine selected leads and additional leads
        final_leads = list(st.session_state.leads) + [lead.strip() for lead in additional_leads_input.split(",") if lead.strip()]
        #final_leads = st.session_state.leads + [lead.strip() for lead in additional_leads_input.split(",") if lead.strip()]

        # Limit the number of final leads to 10
        if len(final_leads) > 10:
            st.warning("You can enter at most 10 leads. Only the first 10 will be considered.")
            final_leads = final_leads[:10]
        
        #st.session_state.previous_leads=final_leads
        
        g=open("leads.txt","w")
        for lead in final_leads:
                g.write(lead+"\n")

        # Update the leads variable with the final leads
        #st.session_state.leads = final_leads
        st.session_state.leads=set(final_leads)
         
        
       
        #st.write("Final Key words to search each lead comppany with:", st.session_state.leads)
        st.rerun()
        print("Final leads are :", st.session_state.leads)


    # Button to submit the final leads


    # Limit the number of final leads to 10






    # Input for target company name
    #company_name = st.text_input("Enter name of target company:")

    # Button to generate email
    
    if 'sheet_url' not in st.session_state:
        st.session_state.sheet_url = ''
    if 'spreadsheet_id' not in st.session_state:
        st.session_state.spreadsheet_id = ''
    if 'creds' not in st.session_state:
        st.session_state.creds = None
    if 'service' not in st.session_state:
        st.session_state.service = None
    if 'preview' not in st.session_state:
        st.session_state.preview = False
    if 'records' not in st.session_state:
        st.session_state.records = []
    if 'num_records' not in st.session_state:
        st.session_state.num_records = 5
    if 'follow_up' not in st.session_state:
        st.session_state.follow_up = False
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'header' not in st.session_state:
        st.session_state.header = None
    
    present_sheet_url=""
    if os.path.exists("sheet_url.txt"):
        k=open("sheet_url.txt","r")
        present_sheet_url=k.read()
        if present_sheet_url:
            st.session_state.sheet_url=present_sheet_url
        k.close()

    # Initialize empty list to store lead data
    st.session_state.records = []
    url_key = 'sheet_url'
    st.write("\n\n\n\n")
    provided_sheet_url = st.text_input("Enter Google Sheet URL",key='sheet_url',value=present_sheet_url)
    st.session_state['url_key']=provided_sheet_url
    k=open("sheet_url.txt","w")
    k.write(st.session_state['url_key'])
    k.close()
    
  
            # Submit button
    if st.button("Submit Sheet URL") or st.session_state['url_key']:
        #st.write("Submit button pressed.")  # Debugging statement
        #if st.session_state[url_key]:
            #st.write("Google Sheet URL provided.")  # Debugging statement
            try:
                st.session_state.spreadsheet_id = get_spreadsheet_id(st.session_state['url_key'])
                st.session_state.creds = authenticate()
                st.session_state.service = build('sheets', 'v4', credentials=st.session_state.creds)
                st.session_state.df = display_sheet_records(st.session_state.service, st.session_state.spreadsheet_id)
                st.session_state.preview = True
                st.session_state.follow_up = True
                st.write("Google Sheet data loaded successfully.")
                #st.write(st.session_state.df)  # Debugging statement
                
                # Add details to the company database
                for index, row in st.session_state.df.iterrows():
                    company_name = row['Company Name']
                    member_name = row['Member Name']
                    member_email = row['Member Email']
                    member_linkedin = row['Member Linkedin']
                    linkedin_profile = None  # Add this new field
                    first_email = None
                    first_email_date = None
                    first_email_time = None
                    follow_up_email = None
                    follow_up_email_date = None
                    follow_up_email_time = None
                    second_follow_up_email = None
                    second_follow_up_email_date = None
                    second_follow_up_email_time = None
                    
                    cursor.execute('''SELECT * FROM company_details WHERE company_name=? AND member_name=? AND member_email=?''', 
                                (company_name, member_name, member_email))
                    if cursor.fetchone() is None:
                        insert_company_detail(
                            company_name, member_name, member_email, member_linkedin, linkedin_profile,
                            first_email, first_email_date, first_email_time,
                            follow_up_email, follow_up_email_date, follow_up_email_time,
                            second_follow_up_email, second_follow_up_email_date, second_follow_up_email_time
                        )
            except Exception as e:
                st.error(f"An error occurred: {e}")  # Error handling
    else:
                st.warning("Please enter a valid Google Sheet URL.") 
        
        
                
    
            
    
                                   
    f.close()
    g.close()                                


    if st.button("Clear Sheet Values"):
        print("Clear sheet values pressed")
        if os.path.exists("urls.txt"):
            f=open("urls.txt",'w')
            f.write('')
        if os.path.exists("leads.txt"):
            k=open('leads.txt','w')
            k.write('')
        if os.path.exists("sheet_url.txt"):
            
            h=open('sheet_url.txt','w')
            print(h)
            h.write('')
        f.close()
        k.close()
        h.close()
        st.session_state.leads=[]
        st.session_state.url_key=''
        
        st.rerun()

elif page == "Customizations":

    st.title("Customizations")
    if st.session_state.preview:
        with st.expander("Preview"):
            #st.subheader("Preview")
            # st.dataframe(st.session_state.df)
            if 'selected_row' not in st.session_state:
                st.session_state.selected_row = None
            cursor.execute("SELECT * FROM company_details")
            rows = cursor.fetchall()
            st.session_state.df = pd.DataFrame(rows, columns=['id', 'Company Name', 'Member Name', 'Member Email', 'Member Linkedin','Linkedin Profile', 'first_email', 'first_email_date', 'first_email_time', 'follow_up_email', 'follow_up_email_date', 'follow_up_email_time', 'second_follow_up_email', 'second_follow_up_email_date', 'second_follow_up_email_time'])
            #st.session_state.df = pd.DataFrame(rows, columns=['id', 'Company Name', 'Member Name', 'Member Email', 'Member Linkedin', 'first_email', 'follow_up_email', 'second_follow_up_email'])
           
            
            
                
        with st.sidebar:
            st.write("## Company Details")
            
            # Custom CSS for table layout
            st.markdown("""
                <style>
                .company-table {
                    margin-top: 0;
                    padding-top: 0;
                }
                .company-table button {
                    background: none;
                    border: none;
                    padding: 2px 0;
                    width: 100%;
                    text-align: left;
                }
                .header-row {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    padding: 5px 0;
                    border-bottom: 1px solid #ddd;
                    font-weight: bold;
                }
                .data-row {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    padding: 2px 0;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Table header with grid layout
            st.markdown('<div class="header-row"><div>Company Name</div><div>Member Name</div></div>', unsafe_allow_html=True)
            
            # Create selectable rows with grid layout
            for idx, row in st.session_state.df.iterrows():
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        f"{row['Company Name']}", 
                        key=f"row_{idx}",
                        use_container_width=True
                    ):
                        st.session_state.selected_row = row
                        st.rerun()
                with col2:
                    st.write(row['Member Name'])
        # Main area display (right side)
        

        # Main area display (right side)
        if st.session_state.selected_row is not None:
                st.write(f"Details for {st.session_state.selected_row['Company Name']}:")
                selected_df = st.session_state.df.loc[st.session_state.df['Company Name'] == st.session_state.selected_row['Company Name']]
                st.dataframe(selected_df[['Company Name', 'Member Name', 'Member Email', 'Member Linkedin']])

                cursor.execute("SELECT * FROM company_details WHERE company_name=? AND member_name=? AND member_email=?", 
                            (st.session_state.selected_row['Company Name'], 
                            st.session_state.selected_row['Member Name'], 
                            st.session_state.selected_row['Member Email']))
                fetched_row = cursor.fetchone()
                
                #print(row,type(row))
                # Add these to your session state initializations at the start of your script
                if 'generated_email' not in st.session_state:
                    st.session_state.generated_email = None
                if 'show_send_buttons' not in st.session_state:
                    st.session_state.show_send_buttons = False

                # Separate the email gener ation button
                print("source_data", st.session_state.source_company_data)
                print(fetched_row[3])
                #if fetched_row[7] is not None :
                    #st.warning(f"No response has been recieved from {fetched_row[1]}")

    
                if fetched_row[6] is None:
                   
                        # Insert code for generating follow up email here
                 if st.button("Generate Personalized Email", key="generate_email"):
                    try:
                        
                        with st.spinner(f"Researching {st.session_state.selected_row['Company Name']} in the areas..."):
                            st.session_state.target_company_data = ""
                            for lead in st.session_state.leads:
                                response = tavily_client.get_search_context(f"{st.session_state.selected_row['Company Name']} {lead}")
                                st.session_state.target_company_data += response + " "
                        
                        print("target comapny data")
                        #print(st.session_state.target_company_data)
                        if(st.session_state.target_company_data!=''):
                          st.text_area("Target Company Data", value=st.session_state.target_company_data, height=100, disabled=True)
                        
                        with st.spinner(f"Researching {st.session_state.selected_row['Member Name']} details..."):
                            time.sleep(2)
                        
                        st.text_area("Company Member Details", value=st.session_state.selected_row['Linkedin Profile'], height=100, disabled=True)
                            
                        with st.spinner("Creating personalized email with all the information..."):
                            final_response = chain_1.invoke({
                                "source_company_data": st.session_state.source_company_data,
                                "target_company_data": st.session_state.target_company_data,
                                "sender_name":"Genzoic",
                                "reciever_name":st.session_state.selected_row['Member Name'],
                                "member_details":st.session_state.selected_row['Linkedin Profile']
                            })
                        
                        # Store the generated email in session state
                       
                        st.session_state.generated_email = final_response
                        st.session_state.show_send_buttons = True
                        
                    except Exception as e:
                        st.error(f"An error occurred during email generation: {e}")
                        print(f"Error: {e}")
                else:
                    # Use an expander to show the previous email
                    #with st.expander("Previous Email Sent", expanded=False):
                        #st.markdown(fetched_row[5]) 
               
                    # Display the previous email in a smaller text area
                    
                    #st.text_area("First Email Sent", value=fetched_row[5], height=100, disabled=True)
                    #if(fetched_row[9] is not None):
                          #st.text_area("Follow up Email Sent", value=fetched_row[6], height=100, disabled=True)
                      
                    if fetched_row[6] is not None:

                        st.text_area(f"First Email Sent on  {fetched_row[7]} at {fetched_row[8]}", value=fetched_row[6], height=150, disabled=True)
                        
                    if fetched_row[9] is not None:
                    
                        st.text_area(f"Follow up Email Sent on {fetched_row[10]} at {fetched_row[11]}", value={fetched_row[9]}, height=150, disabled=True)
                            
                    if fetched_row[12] is not None:
                       
                        st.text_area(f"Second Follow up Email Sent on {fetched_row[13]} at {fetched_row[14]}", value={fetched_row[12]}, height=150, disabled=True)  
                      # Adjust height as needed
# ... existing code ... # Display the previous email
                    if st.button("Generate Personalized Follow-Up Email", key="generate_follow_up_email"):
                     try:
                        with st.spinner(f"Researching {st.session_state.selected_row['Company Name']} in the areas..."):
                            st.session_state.target_company_data = ""
                            for lead in st.session_state.leads:
                                response = tavily_client.get_search_context(f"{st.session_state.selected_row['Company Name']} {lead}")
                                st.session_state.target_company_data += response + " "
                        
                        print("target comapny data")
                        
                        if(st.session_state.target_company_data!=''):
                         st.text_area("Target Company Data", value=st.session_state.target_company_data, height=100, disabled=True)
                        

                        with st.spinner(f"Researching {st.session_state.selected_row['Member Name']} details..."):
                            time.sleep(2)
                        
                        st.text_area("Comapany Member Details", value=st.session_state.selected_row['Linkedin Profile'], height=100, disabled=True)
                        
                        with st.spinner("Creating personalized email with all the information..."):
                            final_response = chain_2.invoke({
                                "source_company_data": st.session_state.source_company_data,
                                "target_company_data": st.session_state.target_company_data,
                                "email":fetched_row[6]+'/n/n'+''if fetched_row[9] is None else fetched_row[9],
                                "sender_name":"Genzoic",
                                "reciever_name":st.session_state.selected_row['Member Name'],
                                "member_details":st.session_state.selected_row['Linkedin Profile']
                            })
                        
                        # Store the generated email in session state
                        #print(type(final_response))
                        #print(final_response)
                        st.session_state.generated_email = final_response
                        st.session_state.show_send_buttons = True
                        #print(type(final_response.content),type(st.session_state.generated_email))
                        
                     except Exception as e:
                        st.error(f"An error occurred during email generation: {e}")
                        print(f"Error: {e}")


                # Show the generated email if it exists
                if st.session_state.generated_email:
                  st.write("Generated Email:")
                  st.write(f"Subject :{st.session_state.generated_email.get('subject', '')}")
                  st.write(st.session_state.generated_email['body'])

                # Show send/cancel buttons if email was generated
                if st.session_state.show_send_buttons:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Send Email", key="send_email"):
                            try:
                                current_time = time.localtime()
                                current_date = time.strftime('%Y-%m-%d', current_time)
                                current_time_str = time.strftime('%H:%M:%S', current_time)
                                
                                send_email('smtp.gmail.com', 587, sender_details["sender_email"], os.getenv('password'), 
                                          sender_details["sender_email"], fetched_row[3], 
                                          st.session_state.generated_email["subject"], 
                                          st.session_state.generated_email["body"])
                                
                                if fetched_row[6] is None:
                                    cursor.execute('''
                                        UPDATE company_details 
                                        SET first_email = ?, first_email_date = ?, first_email_time = ?
                                        WHERE company_name = ? AND member_name = ? AND member_email = ?
                                    ''', (
                                        st.session_state.generated_email["subject"] + "\n" + st.session_state.generated_email['body'],
                                        current_date,
                                        current_time_str,
                                        st.session_state.selected_row['Company Name'],
                                        st.session_state.selected_row['Member Name'],
                                        st.session_state.selected_row['Member Email']
                                    ))
                                elif fetched_row[9] is None:
                                    cursor.execute('''
                                        UPDATE company_details 
                                        SET follow_up_email = ?, follow_up_email_date = ?, follow_up_email_time = ?
                                        WHERE company_name = ? AND member_name = ? AND member_email = ?
                                    ''', (
                                        st.session_state.generated_email["subject"] + "\n" + st.session_state.generated_email['body'],
                                        current_date,
                                        current_time_str,
                                        st.session_state.selected_row['Company Name'],
                                        st.session_state.selected_row['Member Name'],
                                        st.session_state.selected_row['Member Email']
                                    ))
                                else:
                                    cursor.execute('''
                                        UPDATE company_details 
                                        SET second_follow_up_email = ?, second_follow_up_email_date = ?, second_follow_up_email_time = ?
                                        WHERE company_name = ? AND member_name = ? AND member_email = ?
                                    ''', (
                                        st.session_state.generated_email["subject"] + "\n" + st.session_state.generated_email['body'],
                                        current_date,
                                        current_time_str,
                                        st.session_state.selected_row['Company Name'],
                                        st.session_state.selected_row['Member Name'],
                                        st.session_state.selected_row['Member Email']
                                    ))
                                conn.commit()
                                st.success("Email sent successfully!")
                                # Reset states after successful send
                                st.session_state.generated_email = None
                                st.session_state.show_send_buttons = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error sending email: {e}")
                    
                    with col2:
                        if st.button("Cancel", key="cancel_email"):
                            st.session_state.generated_email = None
                            st.session_state.show_send_buttons = False
                            st.rerun()
                    
                    