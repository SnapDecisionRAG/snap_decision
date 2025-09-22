import chromadb
from pathlib import Path
from datetime import datetime

class VectorStore:
    def __init__(self, db_path):
        try:
            self.db_path = Path(db_path)
            self.db_path.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(self.db_path))
            self.collection_name = "fantasy_content"
            self.collection = self._get_collection()

            print(f"ChromaDB initialized at {self.db_path}")

        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise

    def _create_collection(self):
        collection = self.client.create_collection(
            name=self.collection_name,
            embedding_function=chromadb.utils.embedding_functions.DefaultEmbeddingFunction(),
            metadata={"description": "Fantasy football strategy and analysis content"}
        )

        return collection

    def _get_collection(self):
        try:
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
            )

            print(f"Using existing collection: {self.collection_name}")

        except ValueError:
            collection = self._create_collection()

            print(f"Created new collection: {self.collection_name}")

        return collection
    
    def add_documents(self, documents):
        try:
            if not documents:
                print("No documents to add")
                return True
            
            ids = []
            content = []
            metadata = []

            for doc in documents:
                if not all(key in doc for key in ['content', 'metadata', 'id']):
                    print(f"skipping invalid document: {doc.get('id', 'unknown')}")
                    continue

                ids.append(str(doc['id']))
                content.append(doc['content'])

                data = {k: str(v) for k, v in doc['metadata'].items() if v is not None}
                metadata.append(data)

            self.collection.add(
                documents=content,
                metadatas=metadata,
                ids=ids
            )

            print(f"Successfully added {len(ids)} documents to ChromaDB")
            return True
        
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            return False

    def search(self, query, limit=5, metadata_filters=None, min_similarity=0.0):
        try:
            query_params = {
                'query_texts': [query],
                'n_results': limit,
            }

            if metadata_filters:
                query_params['where'] = metadata_filters

            results = self.collection.query(**query_params)

            formatted_results = []
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            ids = results.get('ids', [[]])[0]

            if not (len(documents) == len(metadatas) == len(distances) == len(ids)):
                print("ChromaDB returned mismatched result lengths - data corrupted")
                return []

            for i, doc in enumerate(documents):
                similarity = 1.0 / (1.0 + distances[i]) if distances else 1.0
                if similarity < min_similarity:
                    continue

                formatted_results.append({
                    'content': doc,
                    'metadata': metadatas[i],
                    'similarity': similarity,
                    'id': ids[i],
                })

            formatted_results.sort(key=lambda x: (
                x['similarity'],
                x['metadata'].get('timestamp', '1901-01')
            ), reverse=True)

            return formatted_results
        
        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return []

    def get_collection_stats(self):
        count = self.collection.count()
        sample_results = self.collection.get(limit=min(100, count))
        content_types = {}

        for metadata in sample_results.get('metadatas', []):
            content_type = metadata.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1

        return {
            'total_documents': count,
            'content_types': content_types,
        }

    def search_by_content_type(self, query, content_type, limit=5):
        metadata_filters = {'content_type': content_type}
        return self.search(query, limit, metadata_filters)
    
    def get_recent_analysis(self, days=7, limit=10):
        try:
            cutoff_date = (datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')

            results = self.collection.get(
                where={'content_type': 'analysis', 'date': {'$gte': cutoff_date}},
                limit=limit
            )

            formatted_results = []
            documents = results.get('documents', [])
            metadatas = results.get('metadatas', [])
            ids = results.get('ids', [])

            if not (len(documents) == len(metadatas) == len(ids)):
                print("ChromaDB returned mismatched result lengths - data corrupted")
                return []

            for i, doc in enumerate(documents):

                formatted_results.append({
                    'content': doc,
                    'metadata': metadatas[i],
                    'similarity': 1.0,
                    'id': ids[i],
                })

            formatted_results.sort(key=lambda x: (
                x['metadata'].get('timestamp', '1901-01')
            ), reverse=True)

            return formatted_results
        
        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return []
        
    def reset_collection(self):
        self.client.delete_collection(name=self.collection_name)
        self.collection = self._get_collection()
        return True
