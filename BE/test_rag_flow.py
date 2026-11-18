import asyncio
import os
import sys
from dotenv import load_dotenv

be_dir = os.path.dirname(os.path.abspath(__file__))
if be_dir not in sys.path:
    sys.path.insert(0, be_dir)

# Load environment variables
load_dotenv(os.path.join(be_dir, ".env"), override=True)

from app.services.rag import rag_service

async def run_rag_flow():
    # Test 1: Relevant query for content in database
    q1 = "Who is Nick Vujicic?"
    print(f"=== TEST 1: Relevant Query ('{q1}') ===")
    r1 = await rag_service.query(q1, top_k=2)
    print(f"Sources retrieved: {len(r1['sources'])}")
    for src in r1["sources"]:
        print(f"  -> [Source {src['source_num']}] {src['title']} ({src['similarity_score']}% Match)")
        print(f"     Snippet preview: {src['snippet'][:100]}...\n")
    print(f"Answer:\n{r1['answer']}\n")

    # Test 2: Irrelevant query for content NOT in database
    q2 = "How to bake a chocolate cake with frosting?"
    print(f"=== TEST 2: Irrelevant / Out-of-Domain Query ('{q2}') ===")
    r2 = await rag_service.query(q2, top_k=2)
    print(f"Sources retrieved: {len(r2['sources'])} (Must be 0 unwanted sources)")
    print(f"Answer:\n{r2['answer']}\n")

if __name__ == "__main__":
    asyncio.run(run_rag_flow())
