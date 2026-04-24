import os, re, json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# Custom Modules
from embedding import EmbeddingManager
from knowledgebase import PineconeManager
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize Managers
groq_api_key = os.getenv("GROQ_API_KEY")
pine_api_key = os.getenv("PINNECONE_API_KEY")

pc_manager = PineconeManager(
    api_key=pine_api_key, 
    index_name="pdf-search-index", 
    dimension=384, 
    embeddings_manager=EmbeddingManager()
)

def extract_pdf_text(file):
    text = ""
    pdf = PdfReader(file)
    for page in pdf.pages:
        text += page.extract_text() or ""
    return text

def get_structured_bill_data(raw_text):
    """Pass 1: Use LLM to extract data from raw PDF text."""
    llm = ChatGroq(api_key=groq_api_key, model_name="llama-3.3-70b-versatile")
    prompt = (
        "Extract the following from the medical invoice text: "
        "1. Patient Name, 2. Diagnosis/Disease, 3. Total Amount, 4. Provider Name. "
        "Return ONLY a JSON object: {\"bill_name\": \"...\", \"disease\": \"...\", \"expense\": 0.0, \"provider\": \"...\"}"
    )
    response = llm.invoke([("system", prompt), ("user", raw_text)])
    match = re.search(r"\{.*\}", response.content, re.DOTALL)
    return json.loads(match.group(0)) if match else None

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/process_claim', methods=['POST'])
def process_claim():
    try:
        # 1. Capture Form Inputs
        form_data = {
            "name": request.form.get('name'),
            "claim_type": request.form.get('claim_type'),
            "date": request.form.get('date'),
            "claim_reason": request.form.get('claim_reason'),
            "total_claim_amount": request.form.get('total_claim_amount'),
            "medical_facility": request.form.get('medical_facility')
        }

        # 2. Validation: Check if any form field is empty
        if not all(form_data.values()):
            return jsonify({
                "status": "success", 
                "output": "<b>REJECTION:</b> One or more form fields are empty. All information is required for processing."
            })

        # 3. Extract & Structure Bill Data
        medical_bill = request.files.get('receipt')
        if not medical_bill:
             return jsonify({"status": "error", "message": "No file uploaded"}), 400
             
        bill_text = extract_pdf_text(medical_bill)
        bill_data = get_structured_bill_data(bill_text)
        
        query_texts = [form_data['claim_reason'], "What are the documents required for claim approval?", "Give a list of all general exclusions"]
        policy_context = []
        
        for query in query_texts:
            search_results = pc_manager.retrieve(query_text=query, top_k=3)
            context = "\n".join([m['metadata']['text'] for m in search_results['matches']])
            policy_context.append(context)
        
        # 5. Pass 2: AI Final Reasoning (The Decision Maker)
        llm = ChatGroq(api_key=groq_api_key, model_name="llama-3.3-70b-versatile", temperature=0)
        
        system_instruction = """
        You are a Health Insurance Auditor. Compare the FORM DATA with the BILL DATA using the POLICY CONTEXT.
        
        CRETERIA OF ACCEPTANCE/REJECTION OF CLAIM:
        1. IDENTITY MATCH: All {form_data} should match with the data in the {bill_text}. If they are different, REJECT.
        2. FINANCIAL MATCH: The 'total_claim_amount' in the form MUST NOT be greater than the 'expense' in the bill.
        3. POLICY CHECK: Check if the 'disease' or 'claim_reason' is an exclusion in the POLICY CONTEXT.
        
        If any rule fails, start your response with 'DECISION: REJECTED' and explain why.
        Otherwise, start with 'DECISION: ACCEPTED', explain why, and calculate the amount payable based on the policy terms and conditions.
        """

        user_payload = f"""
        POLICY CONTEXT: {policy_context}
        FORM DATA: {json.dumps(form_data)}
        BILL TEXT: {bill_text}
        """

        final_decision = llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=user_payload)
        ])

        return jsonify({
            "status": "success",
            "output": final_decision.content.replace("\n", "<br>"),
            "extracted_disease": bill_data['disease'],
            "actual_expense": bill_data['expense']
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    from waitress import serve
    port = int(os.getenv("PORT", 5000))
    serve(app, host='0.0.0', port=port)