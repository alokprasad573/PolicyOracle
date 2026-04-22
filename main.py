import os, re, json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Check your .env file.")

# Global variables
vectorstore = None
general_exclusion_list = ["HIV/AIDS", "Parkinson's disease", "Alzheimer's disease","pregnancy", "substance abuse", "self-inflicted injuries", "sexually transmitted diseases(std)", "pre-existing conditions"]

def get_document_loader():
    loader = DirectoryLoader('documents', glob="**/*.pdf", show_progress=True, loader_cls=PyPDFLoader)
    docs = loader.load()
    return docs

def get_text_chunks(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

def init_vectorstore():
    global vectorstore
    if vectorstore is None:
        documents = get_document_loader()
        chunks = get_text_chunks(documents)
        vectorstore = FAISS.from_documents(
            chunks, HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        )
    return vectorstore

def get_claim_approval_context():
    db = init_vectorstore()
    context = db.similarity_search("What are the documents required for claim approval?")
    claim_approval_context = ""
    for x in context:
        claim_approval_context += x.page_content
    return claim_approval_context

def get_general_exclusion_context():
    db = init_vectorstore()
    context = db.similarity_search("Give a list of all general exclusions")
    general_exclusion_context = ""
    for x in context:
        general_exclusion_context += x.page_content
    return general_exclusion_context

def get_file_content(file):
    text = ""
    pdf = PdfReader(file)
    for page_num in range(len(pdf.pages)):
        page = pdf.pages[page_num]
        text += page.extract_text()
    return text

def get_bill_info(data):
    prompt_text = "Act as an expert in extracting information from medical invoices. You are given with the invoice details of a patient. Go through the given document carefully and extract the 'disease' and the 'expense amount' from the data. Return ONLY the data in json format = {'disease':\"\",'expense':\"\"}"
    
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile")
    user_content = f"INVOICE DETAILS: {data}"
    
    response = llm.invoke([
        ("system", prompt_text),
        ("user", user_content)
    ])
    
    content = response.content
    json_match = re.search(r'\{.*\}', content.strip(), re.DOTALL)
    if json_match:
        final_data = json.loads(json_match.group(0))
    else:
        try:
            final_data = json.loads(content)
        except:
            final_data = {"disease": "unknown", "expense": 0}
    return final_data

PROMPT = """You are an AI assistant for verifying health insurance claims. You are given with the references for approving the claim and the patient details. Analyse the given data and predict if the claim should be accepted or not. Use the following guidelines for your analysis.

1.Verify if the patient has provided all necessary information and all necessary documents
and if you find any incomplete information or required documents are not provided then set INFORMATION criteria as FALSE and REJECT the claim.
if patient has provided all required documents then set INFORMATION criteria as TRUE. 

2. If any disease mentioned in the medical bill of the patient is in the general exclusions list, set EXCLUSION criteria as FALSE and REJECT the claim.

Use this information to verify if the application is valid and to accept or reject the application.

DOCUMENTS FOR CLAIM APPROVAL: {claim_approval_context}
EXCLUSION LIST : {general_exclusion_context}
PATIENT INFO : {patient_info}
MEDICAL BILL : {medical_bill_info}

Use the above information to verify if the application is valid and decide if the application has to be accepted or rejected keeping the guidelines into consideration. 

Generate a detailed report about the claim and procedures you followed for accepting or rejecting the claim and the write the information you used for creating the report. 
Create a report in the following format

Write whether INFORMATION AND EXCLUSION are TRUE or FALSE 
Reject the claim if any of them is FALSE.
Write whether claim is accepted or not. If the claim has been accepted, the maximum amount which can be approved will be {max_amount}

Executive Summary
[Provide a Summary of the report.]

Introduction
[Write a paragraph about the aim of this report, and the state of the approval.]

Claim Details
[Provide details about the submitted claim]

Claim Description
[Write a short description about claim]

Document Verification
[Mentions which documents are submitted and if they are verified.] 

Document Summary
[Give a summary of everything here including the medical reports of the patient]

Please verify for any signs of fraud in the submitted claim if you find the documents required for accepting the claim for the medical treatment.
"""

def check_claim_rejection(claim_disease, general_exclusion_list, prompt_template, threshold=0.4):
    if not claim_disease or not isinstance(claim_disease, str) or claim_disease.strip() == "":
        return prompt_template
        
    try:
        vectorizer = CountVectorizer()
        patient_info_vector = vectorizer.fit_transform([claim_disease])

        for disease in general_exclusion_list:
            # Add vocabulary handling
            try:
                disease_vector = vectorizer.transform([disease])
                similarity = cosine_similarity(patient_info_vector, disease_vector)[0][0]
                if float(similarity) > float(threshold):
                    rejection_prompt = """You are an AI assistant for verifying health insurance claims. You are given with the references for approving the claim and the patient details. Analyse the given data and give a good rejection. You the following guidelines for your analysis.
                    PATIENT INFO : {patient_info}

                    Executive Summary
                        [Provide a Summary of the report.]

                        Introduction
                        [Write a paragraph about the aim of this report, and the state of the approval.]

                        Claim Details
                        [Provide details about the submitted claim]

                        Claim Description
                        [Write a short description about claim]

                        Document Verification
                        [Mentions which documents are submitted and if they are verified.] 

                        Document Summary
                        [Give a summary of everything here including the medical reports of the patient]
                    
                    CLAIM MUST BE REJECTED: Patient has """ + disease + """ which is present in the general exclusion list."""
                    return rejection_prompt
            except Exception as e:
                # Can be raised if the word is out of vocab for the vectorizer
                pass
                
        return prompt_template
    except Exception as e:
        print("Count vectorizer error:", e)
        return prompt_template

@app.route('/', methods=['GET'])
def index():
    return render_template('home.html')

@app.route('/process_claim', methods=['POST'])
def process_claim():
    try:
        name = request.form.get('name')
        address = request.form.get('address')
        claim_type = request.form.get('claim_type')
        claim_reason = request.form.get('claim_reason')
        date = request.form.get('date')
        medical_facility = request.form.get('medical_facility')
        total_claim_amount = request.form.get('total_claim_amount')
        description = request.form.get('description')
        
        medical_bill = request.files.get('receipt')

        if not medical_bill:
             return jsonify({"status": "error", "message": "No receipt file uploaded"}), 400

        # Read the file
        bill = get_file_content(medical_bill)
        bill_info = get_bill_info(bill)
        
        expense_val = str(bill_info.get('expense', '0')).replace(',', '')
        try:
            expense_val = float(expense_val)
        except ValueError:
            expense_val = 0
            
        total_claim_amount_val = float(total_claim_amount)

        # If input amount is more than the bill amount - REJECT
        if expense_val < total_claim_amount_val:
            output = "The amount mentioned for claiming is more than the billed amount. Claim Rejected."
            return jsonify({
                "status": "success",
                "analysis": output,
                "bill_expense": expense_val,
                "disease": bill_info.get('disease', 'unknown')
            })
            
        elif expense_val >= total_claim_amount_val:
            patient_info = f"Name: {name} \nAddress: {address} \nClaim type: {claim_type} \nClaim reason: {claim_reason}\nMedical facility: {medical_facility} \nDate : {date} \nTotal claim amount: {total_claim_amount}\nDescription: {description}"
            medical_bill_info = f"Medical Bill: {bill}"
            
            validated_prompt = check_claim_rejection(bill_info.get("disease", "None"), general_exclusion_list, PROMPT)
            
            # Need to specify proper input variables depending on which prompt was returned
            if "CLAIM MUST BE REJECTED" in validated_prompt:
                # Using the rejection prompt which only takes patient_info
                prompt_template = PromptTemplate(
                    input_variables=["patient_info"],
                    template=validated_prompt
                )
                invoke_args = {"patient_info": patient_info}
            else:
                prompt_template = PromptTemplate(
                    input_variables=["claim_approval_context", "general_exclusion_context", "patient_info", "medical_bill_info", "max_amount"],
                    template=validated_prompt
                )
                invoke_args = {
                    "claim_approval_context": get_claim_approval_context(),
                    "general_exclusion_context": get_general_exclusion_context(),
                    "patient_info": patient_info,
                    "medical_bill_info": medical_bill_info,
                    "max_amount": total_claim_amount
                }

            llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile")
            chain = prompt_template | llm
            
            response_msg = chain.invoke(invoke_args)
            output = response_msg.content
            output = re.sub(r'\n', '<br>', output)
            
            return jsonify({
                "status": "success",
                "analysis": output,
                "bill_expense": expense_val,
                "disease": bill_info.get("disease", "unknown")
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 3000))
    
    print("-" * 50)
    print(f"PolicyOracle Server is running!")
    print(f"Local:   http://localhost:{port}")
    print(f"Network: http://0.0.0.0:{port}")
    print("-" * 50)
    
    serve(app, host='0.0.0.0', port=port)
