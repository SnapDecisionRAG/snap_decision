import os
from datetime import datetime
from typing import ClassVar, Type
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

from src.sql_database.sql_db_manager import SQLDBManager
from src.vector_database.vector_db_manager import VectorDBManager
from src.config import CHROMA_DB_DIR

load_dotenv()

class SQLQueryInput(BaseModel):
    query: str = Field(description="Natural language query that needs statistical data from the fantasy football database")

class VectorSearchInput(BaseModel):
    query: str = Field(description="Natural language query about fantasy football strategy, rules, or advice")

class SQLTool(BaseTool):
    name: ClassVar[str] = "sql_query"
    description: ClassVar[str] = """
        Query the fantasy football SQL database for:
        - Player statistics and performance data
        - Weekly projections and actual scores  
        - Injury reports and latest news
        - Weather forecasts for games
        - Team schedules and matchups
        - Historical player performance analysis

        Use this tool for question about specific stats, numbers, comparisons, and data-driven analysis
    """
    args_schema: Type[SQLQueryInput] = SQLQueryInput

    _db: SQLDBManager
    _llm: ChatOpenAI
    _schema_info: str

    def __init__(self, db_manager):
        super().__init__()
        self._db = db_manager
        self._llm = ChatOpenAI(model="gpt-4", temperature=0)
        self._schema_info = self._get_table_schemas()

    def _run(self, query):
        try:
            sql_query = self._natural_language_to_sql(query)

            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                results = cursor.fetchall()

                if not results:
                    return f"No data found for query: {query}"

                return self._format_sql_results(results, query)

        except Exception as e:
            return f"Error executing SQL query: {str(e)}"
        
    def _natural_language_to_sql(self, query):
        prompt = f"""
            Convert this natural language query to SQL for a fantasy football database.

            Query: "{query}"

            Available tables and their key columns:
            {self._schema_info}

            Rules:
            - Only use tables/columns listed above
            - Return ONLY the SQL query, no explanation or markdown
            - Use LIMIT 10 for player lists unless user specifies otherwise
            - For fantasy points, cast to REAL: CAST(fantasy_points AS REAL)
            - For numeric columns stored as text, cast appropriately
            - Use current week data when possible (highest week number)
            - For comparisons, join tables as needed

            SQL Query:
        """

        try:
            response = self._llm.invoke(prompt)
            sql_query = response.content.strip()
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            return sql_query
        
        except Exception as e:
            print(f"LLM SQL generation failed: {e}")
            return """
                SELECT player_name, position, team, fantasy_points 
                FROM projections 
                WHERE week = (SELECT MAX(week) FROM projections) 
                ORDER BY CAST(fantasy_points AS REAL) DESC 
                LIMIT 10
            """
        
    def _get_table_schemas(self):
        return """
            PROJECTIONS TABLE:
            - player_name (TEXT): Player's full name
            - position (TEXT): QB, RB, WR, TE, K, D/ST
            - team (TEXT): 3-letter team abbreviation
            - week (INTEGER): NFL week number
            - fantasy_points (TEXT): Projected fantasy points
            - passing_yards, passing_tds, interceptions_thrown (TEXT)
            - rushing_attempts, rushing_yards, rushing_tds (TEXT) 
            - receptions, receiving_yards, receiving_tds, targets (TEXT)

            HISTORICAL_STATS TABLE:
            - player_name (TEXT): Player's full name
            - position (TEXT): QB, RB, WR, TE, K
            - team (TEXT): 3-letter team abbreviation
            - season (INTEGER): NFL season year
            - week (INTEGER): NFL week number
            - game_date (DATE): Game date
            - fantasy_points (REAL): Actual fantasy points scored
            - ppr_points (REAL): PPR fantasy points
            - passing_completions, passing_attempts, passing_yards, passing_tds, interceptions (INTEGER)
            - rushing_attempts, rushing_yards, rushing_tds (INTEGER)
            - receptions, receiving_yards, receiving_tds, targets (INTEGER)
            - opponent (TEXT): Opponent team

            ACTUAL_SCORES TABLE:
            - player_name (TEXT): Player's full name  
            - position (TEXT): Position
            - week (INTEGER): NFL week number
            - fantasy_points (REAL): Actual fantasy points scored
            - opponent (TEXT): Opponent team
            - status (TEXT): Player status

            WEATHER TABLE:
            - week (INTEGER): NFL week number
            - away_team, home_team (TEXT): Team names
            - stadium (TEXT): Stadium name
            - covered_dome (BOOLEAN): Is stadium covered/dome
            - temperature, wind_mph, precipitation_percent_chance (JSON): Hourly weather data

            INJURIES TABLE:
            - player_name (TEXT): Player's full name
            - title (TEXT): Injury report title
            - summary (TEXT): Injury details
            - published (TEXT): Publication date

            LATEST_NEWS TABLE:
            - player_or_team (TEXT): Subject of news
            - title (TEXT): News headline  
            - summary (TEXT): News summary
            - published (TEXT): Publication date

            SCHEDULE TABLE:
            - week (INTEGER): NFL week number
            - away_team, home_team (TEXT): Team names
            - game_date (DATE): Game date
            - time_et (TEXT): Game time
        """
    
    def _format_sql_results(self, results, query):
        if not results:
            return "No results found"

        columns = list(results[0].keys())
        formatted = f"Found {len(results)} results:\n\n"

        for i, row in enumerate(results, 1):
            formatted +=  f"{i}. "
            row_parts = []
            for col in columns:
                if row[col] is not None:
                    row_parts.append(f"{col}: {row[col]}")
            formatted += " | ".join(row_parts) + "\n"

        return formatted

class VectorTool(BaseTool):
    name: ClassVar[str] = "vector_query"
    description: ClassVar[str] = """
        Search the fantasy football knowledge base for:
        - Draft strategy and player evaluation advice
        - Waiver wire and free agency tips
        - Trade evaluation and roster management
        - Scoring system explanations (PPR vs Standard)
        - Weather impact analysis on player performance
        - League rules and settings guidance
        - Season-long strategy and championship advice
        
        Use this tool for questions about strategy, advice, rules, and general fantasy football guidance.
    """

    args_schema: Type[VectorSearchInput] = VectorSearchInput

    _db: VectorDBManager

    def __init__(self, db_manager):
        super().__init__()
        self._db = db_manager

    def _run(self, query):
        try:
            results = self._db.search(query, limit=5, min_similarity=0.3)

            if not results:
                return f"No relevant strategy content found for: {query}"
            
            response = f"Found {len(results)} relevant strategy insights:\n\n"

            for i, result in enumerate(results, 1):
                content_type = result['metadata'].get('content_type', 'strategy')
                section_title = result['metadata'].get('section_title', 'General Advice')
                similarity = result.get('similarity', 0)
                
                response += f"{i}. **{section_title}** ({content_type}):\n"
                response += f"{result['content'][:500]}...\n"  # Truncate long content
                response += f"(Relevance: {similarity:.2f})\n\n"
            
            return response
        
        except Exception as e:
            return f"Error searching vector database: {str(e)}"
        
class ChatSession:
    def __init__(self):
        self.conversation_history = []
        self.start_time = datetime.now()

    def add_message(self, role, content):
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now()
        })

    def get_recent_context(self, num_messages = 6):
        if self.conversation_history:
            return self.conversation_history[-num_messages:]
        else:
            return []

    def format_recent_history(self):
        messages = []
        for msg in self.get_recent_context():
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))

        return messages

class Chatbot:
    def __init__(self):
        self.sql_db = SQLDBManager()
        self.vector_db = VectorDBManager(CHROMA_DB_DIR)
        self.session = ChatSession()

        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("Please set OPENAI_API_KEY environment variable")
        
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=1000
        )

        self.sql_tool = SQLTool(self.sql_db)
        self.vector_tool = VectorTool(self.vector_db)
        self.tools = [self.sql_tool, self.vector_tool]

        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True, # show reasoning steps
            max_iterations=3,
            handle_parsing_errors=True
        )

    def _create_agent(self):
        system_prompt = ChatPromptTemplate.from_messages([
            ("system", """
                You are an expert fantasy football advisor with access to comprehensive data and strategy knowledge.

                You have two main tools:
                1. **sql_query**: For statistical data, projections, weather, injuries, and quantitative analysis
                2. **vector_query**: For draft advice, strategy tips, rules explanations, and qualitative guidance

                Guidelines:
                - Be conversational and helpful, like talking to a knowledgeable friend
                - For statistical questions, use the SQL tool to get specific data
                - For strategy questions, use the vector search tool for expert advice  
                - For complex questions, you can use both tools and synthesize the information
                - Always provide actionable advice when possible
                - If a question is unclear, ask for clarification
                - Keep responses concise but informative

                Current context: This is an ongoing conversation, so reference previous messages when relevant.
            """),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        return create_openai_tools_agent(self.llm, self.tools, system_prompt)

    def chat(self, user_input):
        self.session.add_message('user', user_input)

        try:
            chat_history = self.session.format_recent_history()
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history
            })

            assistant_response = response['output']
            self.session.add_message('assistant', assistant_response)
            return assistant_response

        except Exception as e:
            error_response = f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
            self.session.add_message('assistant', error_response)
            return error_response

    def get_stats(self):
        sql_stats = None
        try:
            with self.sql_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as total FROM historical_stats")
                historical_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) as total FROM projections")
                projections_count = cursor.fetchone()[0]
                
                sql_stats = {
                    'historical_records': historical_count,
                    'projection_records': projections_count
                }
        except Exception as e:
            sql_stats = {'error': str(e)}
        
        vector_stats = self.vector_db.get_collection_stats()
        
        return {
            'session_started': self.session.start_time.isoformat(),
            'messages_exchanged': len(self.session.conversation_history),
            'sql_database': sql_stats,
            'vector_database': vector_stats
        }

def main():
    print("🏈 Fantasy Football Expert Chatbot")
    print("=" * 50)
    print("Ask me anything about fantasy football!")
    print("Examples:")
    print("- 'Show me QB projections for this week'")
    print("- 'Should I draft RBs early?'")  
    print("- 'How does weather affect kickers?'")
    print("- 'What are the injury reports today?'")
    print("\nType 'quit' to exit, 'stats' for database info, 'clear' to reset conversation\n")

    try:
        chatbot = Chatbot()
        print("✅ Chatbot initialized successfully!")

        stats = chatbot.get_stats()
        print(f"📊 Loaded {stats['sql_database']['historical_records']} historical records")
        print(f"📚 Loaded {stats['vector_database']['total_documents']} strategy documents\n")

    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        print("Please check your OpenAI API key and database setup.")
        return
    
    while True:
        try:
            user_input = input("Future Champion: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Thanks for using Fantasy Football Expert! Good luck out there! 🏈")
                break

            if user_input.lower() == 'stats':
                stats = chatbot.get_stats()
                print(f"\n📊 Chatbot Statistics:")
                print(f"Messages in conversation: {stats['messages_exchanged']}")
                print(f"SQL records available: {stats['sql_database']['historical_records']}")
                print(f"Strategy documents: {stats['vector_database']['total_documents']}")
                print()
                continue

            if user_input.lower() == 'clear':
                chatbot.session = ChatSession()
                print("🔄 Conversation cleared!\n")
                continue

            if not user_input.strip():
                print("I think you accidentally hit enter.")
                continue

            print("\n🤔 Thinking...")
            response = chatbot.chat(user_input)
            print(f"\n🏈 Expert: {response}\n")

        except KeyboardInterrupt:
            print("\n\nThanks for using Fantasy Football Expert! 🏈")
            break

        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again or type 'quit' to exit.\n")

if __name__ == "__main__":
    main()
