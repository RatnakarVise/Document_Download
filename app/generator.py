import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load env vars from .env
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
# groq_api_key = os.getenv("GROQ_API_KEY")
if langchain_api_key:
    os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
# if groq_api_key:
#     os.environ["GROQ_API_KEY"] = groq_api_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
def build_template_retriever(template: str):
    """Build a retriever for the passed-in template string."""
    documents = [Document(page_content=template)]
    splitter = RecursiveCharacterTextSplitter(chunk_size=20000, chunk_overlap=200)
    docs = splitter.split_documents(documents)
    # embedding = OpenAIEmbeddings()
    embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
    )
    vectorstore = Chroma.from_documents(docs, embedding)
    return vectorstore.as_retriever()

def generate_fs_from_requirement(
    requirement: str,
    fs_template: str
) -> str:
    """
    Given ABAP code, and a template (provided by the user each call),
    use RAG retrieval of template and generate a doc strictly following it.
    """
    retriever = build_template_retriever(fs_template)
    retrieved_docs = retriever.get_relevant_documents(requirement)
    # Should always retrieve the template, since it's the only doc.
    retrieved_template = "\n\n".join(doc.page_content for doc in retrieved_docs)
    if not retrieved_template.strip():
        return "No functional specification template found in RAG."

    prompt_template = ChatPromptTemplate.from_template(
        "You are an SAP Functional Consultant. Strictly use the TEMPLATE structure and headings provided below.\n\n"
        "ABAP CODE:\n{requirement}\n\n"
        "TEMPLATE (STRICTLY FOLLOW):\n{fs_template}\n\n"
        "Write a Functional Specification Document for business stakeholders, strictly following the TEMPLATE headings and order (do not change them), "
        "and filling every section thoroughly and professionally, referencing the ABAP code where relevant. MS Word compatible formatting (headings, subheadings, spacing)."
    )
    messages = prompt_template.format_messages(
        requirement=requirement,
        fs_template=retrieved_template
    )
    llm =  ChatGroq(  model_name="llama3-70b-8192")
    # llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def generate_ts_from_requirement(
    requirement: str,
    ts_template: str
) -> str:
    """
    Given user requirement and a template (provided per call),
    use RAG retrieval of template and generate a technical specification strictly following it.
    """
    retriever = build_template_retriever(ts_template)
    retrieved_docs = retriever.get_relevant_documents(requirement)
    # Should always retrieve the template, since it's the only doc.
    retrieved_template = "\n\n".join(doc.page_content for doc in retrieved_docs)
    if not retrieved_template.strip():
        return "No technical specification template found in RAG."

    prompt_template = ChatPromptTemplate.from_template(
        "You are an SAP Technical Consultant. Strictly use the TEMPLATE structure and headings provided below.\n\n"
        "REQUIREMENT:\n{requirement}\n\n"
        "TEMPLATE (STRICTLY FOLLOW):\n{ts_template}\n\n"
        "Write a Technical Specification Document for technical stakeholders (developers, analysts), strictly following the TEMPLATE headings and order (do not change them), "
        "and filling every section thoroughly and professionally, referencing the requirement where relevant. Use MS Word–compatible formatting (headings, subheadings, spacing)."
    )
    messages = prompt_template.format_messages(
        requirement=requirement,
        ts_template=retrieved_template
    )
    llm =  ChatGroq(  model_name="llama3-70b-8192")
    # llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def generate_abap_code_from_requirement(
    requirement: str,
    abap_template: str
) -> str:
    """
    Given a requirement and an ABAP template,
    use RAG retrieval of template and generate ABAP code strictly following it.
    """
    retriever = build_template_retriever(abap_template)
    retrieved_docs = retriever.get_relevant_documents(requirement)
    # Should always retrieve the template, since it's the only doc.
    retrieved_template = "\n\n".join(doc.page_content for doc in retrieved_docs)
    if not retrieved_template.strip():
        return "No ABAP template found in RAG."

    prompt_template = ChatPromptTemplate.from_template(
        "You are an expert ABAP developer. Strictly use the TEMPLATE structure and comments provided below as a template.\n\n"
        "REQUIREMENT:\n{requirement}\n\n"
        "ABAP CODE TEMPLATE (STRICTLY FOLLOW):\n{abap_template}\n\n"
        "Write production-ready, well-commented ABAP code to fulfill the REQUIREMENT above. "
        "Strictly follow the CODE TEMPLATE structure, style, headers, and comments. "
        "Do not add or omit code sections that are in the template. Use modern, readable ABAP and include meaningful comments. "
        "Only output the ABAP code."
    )
    messages = prompt_template.format_messages(
        requirement=requirement,
        abap_template=retrieved_template
    )
    llm =  ChatGroq(  model_name="llama3-70b-8192")
    # llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)