import uuid, time
from pinecone import Pinecone, ServerlessSpec

class PineconeManager:
    def __init__(self, api_key: str, index_name: str, dimension: int, embeddings_manager):
        self.pc = Pinecone(api_key=api_key) 
        self.index_name = index_name
        self.dimension = dimension
        self._initialize_index()
        self.embeddings_manager = embeddings_manager
        self.index = self.pc.Index(index_name)
        
    def _initialize_index(self):
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        if self.index_name not in existing_indexes:
            print(f"Creating index: {self.index_name}...")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
        else:
            print(f"Connecting to existing index: {self.index_name}")
            
    def upsert_embeddings(self, chunks, namespace="pdf-documents"):
        vectors_to_upsert = [] 
        for doc in chunks:
            # Generate embedding
            vectors = self.embeddings_manager.generate_embedding(doc.page_content).tolist()
            vectors_id = str(uuid.uuid4())
            vector_metadata = {
                "text": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page_label", 0)
            }
            vectors_to_upsert.append((vectors_id, vectors, vector_metadata))
            
            # Batch upsert every 100 vectors
            if len(vectors_to_upsert) >= 100:
                self.index.upsert(vectors=vectors_to_upsert, namespace=namespace)
                vectors_to_upsert = []
                
        if len(vectors_to_upsert) > 0:
            self.index.upsert(vectors=vectors_to_upsert, namespace=namespace)
            
        print(f"Successfully uploaded {len(chunks)} chunks to Pinecone.")
        
    def retrieve(self, query_text: str, top_k: int = 5, namespace: str = "pdf-documents"):
        query_vector = self.embeddings_manager.generate_embedding(query_text).tolist()
        
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            namespace="pdf-documents"
        )

        return results