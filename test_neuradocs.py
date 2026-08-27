"""
NeuraDocs - Automated Verification Suite
"""

import os
import sys
import unittest

# Ensure NeuraDocs root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.models import Chunk, DocumentRecord, ChatSession, ChatMessage
from documents.loader import extract_document
from documents.chunker import StructureAwareChunker
from rag.embeddings import EmbeddingEngine
from rag.vector_store import VectorStore
from rag.hybrid_search import HybridRetriever
from rag.reranker import Reranker
from rag_engine import extract_text_from_file, chunk_text, VectorIndex


class TestNeuraDocs(unittest.TestCase):
    def setUp(self):
        self.db = Database(db_path=":memory:")
        self.sample_text = """
# Quarterly Financial Report Q4
Revenue increased by 25% to $12.5M in the fourth quarter.
Key growth drivers included enterprise software subscriptions.

### Operating Expenses
Operating expenses totaled $4.2M, with R&D accounting for $2.1M.
Net profit reached $3.8M, representing a 15% increase year-over-year.
"""

    def test_document_extraction_and_chunking(self):
        doc = extract_document(self.sample_text.encode("utf-8"), "financial_report.md")
        self.assertEqual(doc.filename, "financial_report.md")
        self.assertGreater(len(doc.pages), 0)

        chunker = StructureAwareChunker(chunk_size=300, overlap=50)
        chunks = chunker.chunk_document(doc)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0].source, "financial_report.md")

    def test_database_persistence(self):
        doc_record = DocumentRecord(
            doc_id="test-doc-1",
            filename="report.md",
            file_type="md",
            file_size_bytes=len(self.sample_text),
            chunk_count=2,
            page_count=1,
            status="indexed",
        )
        chunks = [
            Chunk(text="Chunk 1", source="report.md", chunk_id=0, page_number=1),
            Chunk(text="Chunk 2", source="report.md", chunk_id=1, page_number=1),
        ]
        self.db.save_document(doc_record, chunks)

        loaded_docs = self.db.get_documents()
        self.assertEqual(len(loaded_docs), 1)
        self.assertEqual(loaded_docs[0].filename, "report.md")

        loaded_chunks = self.db.get_all_chunks()
        self.assertEqual(len(loaded_chunks), 2)

    def test_hybrid_search_and_rrf(self):
        chunks = [
            Chunk(text="Apple revenue was 90 billion dollars in fiscal 2023.", source="apple.txt", chunk_id=0),
            Chunk(text="Microsoft Cloud segment generated 30 billion dollars.", source="msft.txt", chunk_id=1),
            Chunk(text="Google advertising revenues reached 65 billion.", source="goog.txt", chunk_id=2),
        ]
        store = VectorStore()
        store.rebuild_index(chunks)
        
        retriever = HybridRetriever(store)
        results = retriever.search("Microsoft Cloud", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].chunk.source, "msft.txt")

    def test_reranker(self):
        chunks = [
            Chunk(text="General corporate overview of technology industry.", source="tech.txt", chunk_id=0),
            Chunk(text="Specific financial details: net margin was 28.5%.", source="finance.txt", chunk_id=1),
        ]
        store = VectorStore()
        store.rebuild_index(chunks)
        retriever = HybridRetriever(store)
        candidates = retriever.search("net margin financial", top_k=2)

        reranker = Reranker()
        reranked = reranker.rerank("net margin financial", candidates, top_k=2)
        self.assertGreater(len(reranked), 0)
        self.assertEqual(reranked[0].chunk.source, "finance.txt")

    def test_backward_compatibility(self):
        raw_text = extract_text_from_file(self.sample_text.encode("utf-8"), "test.txt")
        self.assertIn("Quarterly Financial Report", raw_text)

        chunks = chunk_text(self.sample_text, "test.txt", chunk_size=400, overlap=50)
        self.assertGreater(len(chunks), 0)

        legacy_index = VectorIndex()
        legacy_index.build(chunks)
        self.assertTrue(legacy_index.is_ready())
        search_res = legacy_index.search("Operating expenses", top_k=2)
        self.assertGreater(len(search_res), 0)


if __name__ == "__main__":
    unittest.main()
