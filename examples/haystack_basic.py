"""
Haystack Basic Example with ADRI Protection

This example shows how to protect Haystack search pipelines from bad data
using the @adri_protected decorator.
"""

import pandas as pd

from adri.decorators.guard import adri_protected

# Mock Haystack imports for demonstration
try:
    from haystack import Document, Pipeline
    from haystack.components.retrievers import InMemoryBM25Retriever
    from haystack.document_stores.in_memory import InMemoryDocumentStore
except ImportError:
    # Mock classes for when Haystack is not installed
    class Document:
        def __init__(self, content, meta=None):
            self.content = content
            self.meta = meta or {}

    class InMemoryDocumentStore:
        def __init__(self):
            self.documents = []

        def write_documents(self, documents):
            self.documents.extend(documents)

    class InMemoryBM25Retriever:
        def __init__(self, document_store):
            self.document_store = document_store

        def run(self, query):
            return {"documents": [f"Haystack search result for: {query[:50]}..."]}

    class Pipeline:
        def __init__(self):
            self.components = {}

        def add_component(self, name, component):
            self.components[name] = component

        def run(self, data):
            return {"retriever": {"documents": ["Haystack pipeline result"]}}


@adri_protected(data_param="search_data")
def document_search_pipeline(search_data):
    """
    Haystack document search pipeline with ADRI protection.

    Args:
        search_data (pd.DataFrame): Document data for search

    Returns:
        object: Haystack search pipeline
    """
    # Convert DataFrame to Haystack documents
    documents = []
    for _, row in search_data.iterrows():
        doc = Document(
            content=row["content"],
            meta={
                "title": row["title"],
                "category": row["category"],
                "source": row["source"],
            },
        )
        documents.append(doc)

    # Create document store and add documents
    document_store = InMemoryDocumentStore()
    document_store.write_documents(documents)

    # Create retriever
    retriever = InMemoryBM25Retriever(document_store=document_store)

    # Create pipeline
    pipeline = Pipeline()
    pipeline.add_component("retriever", retriever)

    return pipeline


def demonstrate_haystack_protection():
    """Demonstrate Haystack protection with good and bad data."""

    print("🔍 Haystack + ADRI Protection Demo")
    print("=" * 40)

    # Good search data
    good_data = pd.DataFrame(
        {
            "title": ["Python Guide", "AI Basics", "Data Analysis"],
            "content": [
                "Python programming fundamentals and best practices...",
                "Introduction to artificial intelligence concepts...",
                "Data analysis techniques and methodologies...",
            ],
            "category": ["Programming", "AI", "Analytics"],
            "source": ["docs", "tutorial", "guide"],
        }
    )

    print("\n1️⃣ Testing Haystack pipeline with GOOD data...")
    try:
        pipeline = document_search_pipeline(good_data)
        result = pipeline.run({"retriever": {"query": "Python programming"}})
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    demonstrate_haystack_protection()
