
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

# Import components
try:
    from database.vector_store import vector_store
    from database.sqlite_manager import db_manager
    from agents.account_agent import account_agent
    from agents.policy_agent import policy_agent
    from agents.graph import multi_agent_graph
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def print_header(title):
    print(f"\n{'='*50}")
    print(f" TESTING: {title}")
    print(f"{'='*50}")

def test_embedding_function():
    print_header("Embedding Function Interface")
    ef = vector_store.embedding_function
    
    queries = ["test query", "another query"]
    
    # Test 1: embed_query (positional)
    try:
        res = ef.embed_query(queries[0])
        print(f"✅ embed_query(text) works. Type: {type(res)}, Len: {len(res) if isinstance(res, list) else 'N/A'}")
    except Exception as e:
        print(f"❌ embed_query(text) failed: {e}")

    # Test 2: embed_query (keyword)
    try:
        res = ef.embed_query(input=queries[0])
        print(f"✅ embed_query(input=...) works. Type: {type(res)}")
    except Exception as e:
        print(f"❌ embed_query(input=...) failed: {e}")

    # Test 3: embed_documents
    try:
        res = ef.embed_documents(queries)
        print(f"✅ embed_documents(texts) works. Result count: {len(res)}")
    except Exception as e:
        print(f"❌ embed_documents(texts) failed: {e}")

def test_account_agent():
    print_header("Account Agent (SQL)")
    
    scenarios = [
        "Show breakdown of Refund requests by Product",
        "How many Critical tickets are there?",
        "List all tickets for customer 'John Doe' (Expect empty if not exists)" 
    ]
    
    for query in scenarios:
        print(f"\n🔸 Query: {query}")
        try:
            # 1. Generate SQL
            sql = account_agent.generate_sql(query)
            print(f"   📝 Generated SQL: {sql}")
            
            if not sql:
                print("   ⚠️ SQL generation returned empty string (Model might be refusing or failing)")
                continue

            # 2. Execute SQL
            results = account_agent.execute_query(sql)
            print(f"   📊 Results: {len(results)} rows found")
            if results:
                print(f"   First row: {results[0]}")
            else:
                print("   ℹ️  No rows returned (Valid for negative tests)")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")

def test_router():
    print_header("Router Classification")
    
    tests = {
        "Show me tickets for Adobe": "AccountAgent",
        "What is the refund policy?": "PolicyAgent",
        "How many customers bought GoPro?": "AccountAgent",
        "Can I return a broken item after 30 days?": "PolicyAgent",
        "Show me my recent tickets and explain the refund policy": "Both"
    }
    
    for query, expected in tests.items():
        try:
            # We explicitly test the router node logic logic from graph
            # Or use graph.run to see final state? graph.run executes the agent too.
            # Let's just use the router logic if possible, or run graph and check first node?
            # Accessing router_node directly needs a state
            from agents.state import AgentState
            state = AgentState(query=query, messages=[], agent_type=None)
            
            # Run router node
            result_state = multi_agent_graph.router_node(state)
            detected = result_state.get('agent_type')
            
            status = "✅" if detected == expected else "❌"
            print(f"{status} Query: '{query}' -> Detected: {detected} (Expected: {expected})")
        except Exception as e:
            print(f"❌ Router failed for '{query}': {e}")

def test_policy_agent_mock():
    print_header("Policy Agent (Vector Search)")
    
    # 1. Insert dummy doc
    print("🔹 Inserting dummy policy document...")
    dummy_text = "The refund policy states that customers can return items within 30 days of purchase for a full refund."
    try:
        vector_store.add_pdf_chunks(
            chunks=[dummy_text],
            filename="dummy_policy.pdf"
        )
        print("   ✅ Dummy doc inserted")
    except Exception as e:
        print(f"   ❌ Insert failed: {e}")
        return

    # 2. Search
    query = "What is the return window?"
    print(f"\n🔹 Searching: '{query}'")
    try:
        # Search directly via vector store
        results = vector_store.search(query, n_results=1)
        docs = results['documents']
        print(f"   📊 Found {len(docs)} results")
        if docs:
            print(f"   Top match: {docs[0]}")
            if "30 days" in docs[0]:
                print("   ✅ Semantic search match confirmed!")
            else:
                print("   ⚠️ Match found but might not be relevant (check content)")
        else:
            print("   ❌ No results found (Embedding failure?)")

    except Exception as e:
        print(f"   ❌ Search failed: {e}")

    # 3. Cleanup
    try:
        vector_store.delete_by_metadata({"filename": "dummy_policy.pdf"})
        print("   🧹 Dummy doc cleaned up")
    except Exception as e:
        print(f"   ⚠️ Cleanup failed: {e}")

if __name__ == "__main__":
    print("🚀 STARTING SYSTEM VERIFICATION")
    
    test_embedding_function()
    test_router()
    test_account_agent()
    test_policy_agent_mock()
    
    print("\n✅ VERIFICATION COMPLETE")
