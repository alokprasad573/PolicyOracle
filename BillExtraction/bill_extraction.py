from PyPDF2 import PdfReader
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
import json
from dotenv import load_dotenv
import os
import re

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found in environment variables. Check your .env file."
    )


def get_bill_text(file_path: str) -> str:
    text = ""
    pdf = PdfReader(file_path)
    for page_num in range(len(pdf.pages)):
        page = pdf.pages[page_num]
        page_text = page.extract_text()
        text += page_text
    return text


def get_invoice_info(data):
    prompt_text = """
                    Extract the diagnosis and total cost from the following medical invoice.

                    Requirements:
                    1. Identify the 'disease' and the total 'expense' amount.
                    2. Provide the 'expense' as a number only (no currency symbols).
                    3. Return ONLY a JSON object. No preamble, no explanation.

                    Format:
                    {"disease": "...", "expense": ...}
    """

    llm = ChatGroq(api_key=api_key, model_name="llama-3.3-70b-versatile")
    user_content = f"INVOICE DETAILS: {data}"
    response = llm.invoke([("system", prompt_text), ("user", user_content)])

    content = response.content
    # Extract the first JSON-like object found in the content, including multi-line blocks
    json_match = re.search(r"\{.*\}", content.strip(), re.DOTALL)
    if json_match:
        final_data = json.loads(json_match.group(0))
    else:
        final_data = json.loads(content)
    return final_data


if __name__ == "__main__":
    bill_folder = "Bills"
    bill_name = "HIV.pdf"

    bill_path = os.path.join(bill_folder, bill_name)
    if not os.path.exists(bill_path):
        print(f"Error: Bill not found at {bill_path}")
    else:
        bill_text = get_bill_text(bill_path)
        invoice_info = get_invoice_info(bill_text)

        print(f"Disease: {invoice_info['disease']}")
        print(f"Expense: {invoice_info['expense']}")
