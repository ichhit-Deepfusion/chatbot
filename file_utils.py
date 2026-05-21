import pypdf
import docx

def extract_text_from_file(uploaded_file) -> str:
    """
    Extract text content from an uploaded file-like object.
    Supports PDF, DOCX, and TXT formats.
    """
    filename = uploaded_file.name.lower()
    try:
        if filename.endswith('.pdf'):
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
            
        elif filename.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
            
        elif filename.endswith('.txt'):
            content = uploaded_file.read()
            if isinstance(content, bytes):
                return content.decode('utf-8')
            return str(content)
            
        else:
            return f"Error: Unsupported file type for {uploaded_file.name}. Only PDF, DOCX, and TXT are supported."
            
    except Exception as e:
        return f"Error reading file {uploaded_file.name}: {str(e)}"
