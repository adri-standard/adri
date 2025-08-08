"""
LlamaIndex Basic Example with ADRI Protection

This example shows how to protect LlamaIndex RAG applications from bad data
using the @adri_protected decorator.
"""

import pandas as pd

from adri.decorators.guard import adri_protected

# Mock LlamaIndex imports for demonstration
# In real usage, you would import from actual LlamaIndex packages
try:
    from llama_index.core import Document, VectorStoreIndex
    from llama_index.core.query_engine import RetrieverQueryEngine
except ImportError:
    # Mock classes for when LlamaIndex is not installed
    class Document:
        def __init__(self, text, metadata=None):
            self.text = text
            self.metadata = metadata or {}

    class VectorStoreIndex:
        def __init__(self, documents):
            self.documents = documents

        @classmethod
        def from_documents(cls, documents):
            return cls(documents)

        def as_query_engine(self):
            return MockQueryEngine()

    class MockQueryEngine:
        def query(self, query_str):
            return f"LlamaIndex RAG result for: {query_str[:50]}..."


@adri_protected(data_param="document_data")
def rag_query_engine(document_data):
    """
    LlamaIndex RAG query engine with ADRI protection.

    This function demonstrates how to protect LlamaIndex RAG:
    1. The @adri_protected decorator checks data quality first
    2. Only good quality data reaches your LlamaIndex code
    3. Your existing LlamaIndex code stays exactly the same

    Args:
        document_data (pd.DataFrame): Document data for RAG

    Returns:
        object: LlamaIndex query engine
    """
    # Convert DataFrame to LlamaIndex documents
    documents = []
    for _, row in document_data.iterrows():
        doc = Document(
            text=row["content"],
            metadata={
                "title": row["title"],
                "source": row["source"],
                "category": row.get("category", "general"),
            },
        )
        documents.append(doc)

    # Create vector store index
    index = VectorStoreIndex.from_documents(documents)

    # Create query engine
    query_engine = index.as_query_engine()

    return query_engine


@adri_protected(data_param="knowledge_data", min_score=90, verbose=True)
def enterprise_knowledge_base(knowledge_data):
    """
    Enterprise knowledge base with strict quality requirements.
    """
    # Convert to documents with enhanced metadata
    documents = []
    for _, row in knowledge_data.iterrows():
        doc = Document(
            text=row["content"],
            metadata={
                "title": row["title"],
                "department": row["department"],
                "classification": row["classification"],
                "last_updated": row["last_updated"],
                "author": row["author"],
            },
        )
        documents.append(doc)

    # Create enterprise-grade index
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()

    return query_engine


def demonstrate_llamaindex_protection():
    """Demonstrate LlamaIndex protection with good and bad data."""

    print("🦙 LlamaIndex + ADRI Protection Demo")
    print("=" * 40)

    # Good document data
    good_docs = pd.DataFrame(
        {
            "title": ["AI Overview", "Machine Learning Basics", "Data Science Guide"],
            "content": [
                "Artificial Intelligence is transforming industries...",
                "Machine learning algorithms learn from data...",
                "Data science combines statistics and programming...",
            ],
            "source": ["internal_wiki", "training_docs", "handbook"],
            "category": ["AI", "ML", "DataScience"],
            "author": ["Dr. Smith", "Prof. Johnson", "Team Lead"],
        }
    )

    # Bad document data
    bad_docs = pd.DataFrame(
        {
            "title": [None, "Machine Learning Basics", ""],
            "content": ["", None, "Data science combines..."],
            "source": ["", "training_docs", None],
            "category": [None, "ML", ""],
            "author": ["", "Prof. Johnson", None],
        }
    )

    print("\n1️⃣ Testing RAG engine with GOOD documents...")
    try:
        query_engine = rag_query_engine(good_docs)
        result = query_engine.query("What is artificial intelligence?")
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n2️⃣ Testing RAG engine with BAD documents...")
    try:
        query_engine = rag_query_engine(bad_docs)
        result = query_engine.query("What is machine learning?")
        print(f"✅ Unexpected success: {result}")
    except Exception as e:
        print(f"🛡️ ADRI Protection activated: {str(e)[:100]}...")

    # Good enterprise knowledge data
    good_knowledge = pd.DataFrame(
        {
            "title": ["Security Policy", "HR Guidelines", "Tech Standards"],
            "content": [
                "Company security policies and procedures...",
                "Human resources guidelines and policies...",
                "Technical standards and best practices...",
            ],
            "department": ["Security", "HR", "Engineering"],
            "classification": ["Confidential", "Internal", "Internal"],
            "last_updated": ["2024-01-15", "2024-01-10", "2024-01-20"],
            "author": ["Security Team", "HR Team", "Tech Team"],
        }
    )

    print("\n3️⃣ Testing enterprise knowledge base with good data...")
    try:
        kb_engine = enterprise_knowledge_base(good_knowledge)
        result = kb_engine.query("What are the security policies?")
        print(f"✅ Enterprise KB success: {result}")
    except Exception as e:
        print(f"❌ Enterprise KB error: {e}")


if __name__ == "__main__":
    demonstrate_llamaindex_protection()
