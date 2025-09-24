# 🏈 Fantasy Football RAG Expert

A Retrieval-Augmented Generation (RAG) application that provides intelligent fantasy football decision-making assistance by combining historical player data with real-time information and expert strategy advice scraped from ESPN & multiple RSS Feeds.

## 🚀 Features

### 📊 **Comprehensive Data Analysis**
- 21,500+ historical player records across all fantasy positions in the last 3 seasons
- Real-time projections and actual scores from ESPN
- Weather forecasts updated daily for all NFL games with impact analysis
- Latest injury reports and breaking news updated every time the app is ran
- Expert analysis articles from fantasy football professionals updated daily

### 🤖 Intelligent Chat Interface
- Natural language queries - Ask questions in plain English
- Hybrid AI routing - Automatically selects the right data sources
- Context-aware conversations - Remembers your discussion in each chat session
- Actionable recommendations - Get specific advice, not just data

### 🎯 **Smart Query Types**
- Player Analysis: "Show me Josh Allen's performance in cold weather"
- Draft Strategy: "Should I draft running backs early in PPR?"
- Lineup Decisions: "Start Tua or Josh Allen with this week's weather?"
- Waiver Wire: "Who are the best pickups considering recent injuries?"

## 📋 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Chrome browser (for web scraping)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/fantasy-football-rag.git
   cd fantasy-football-rag
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your OpenAI API key**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

That's it! The app will automatically:
- Set up databases
- Load historical data
- Collect current information
- Start the chat interface

## 💬 Usage Examples

### Statistical Queries
```
Future Champion: "Show me QB projections for this week"
Expert: Found 32 quarterbacks projected for Week 4:
1. Josh Allen (BUF): 22.3 projected points | 285 pass yards, 2.1 TDs...
```

### Strategy Advice  
```
You: "Should I draft RBs early in my draft?"
Expert: Based on expert analysis, early RB strategy is recommended because:
- Volume is king in fantasy football
- RB committees are increasingly common
- Workhorse backs who get 70%+ of touches are rare...
```

### Weather Impact Analysis
```
You: "How does weather affect kicker performance?"
Expert: Weather significantly impacts kickers:
- Wind above 15mph reduces accuracy by 12%
- Cold temperatures below 32°F decrease range
- Dome games provide 8% higher scoring consistency...
```

## 🏗️ Architecture

### Hybrid RAG System
- **SQL Database** - 21,500+ structured records for precise analysis
- **Vector Database** - Strategy documents for semantic search
- **LangChain Agent** - Intelligent tool routing and response synthesis

### Data Sources
- **Historical Stats** - Multi-season player performance data via stathead
- **Live Data** - ESPN projections, ESPN scores, weather, injuries, news
- **Expert Content** - Fantasy rules, strategy guides and professional analysis

### Smart Data Collection
- Automated scrapers with duplicate detection
- Daily updates for time-sensitive information  

## 📁 Project Structure

```
fantasy-football-rag/
├── main.py                     # Application entry point
├── chatbot.py                  # LangChain chatbot implementation
├── scraper_controller.py       # Data collection orchestration
├── requirements.txt            # Python dependencies
├── src/
│   ├── config.py               # Configuration and paths
│   ├── sql_database/           # SQLite database management
│   ├── vector_database/        # ChromaDB vector storage
│   ├── scrapers/               # Web scraping modules
│   └── utils/                  # Utility functions
├── data/
│   ├── sql/                    # Historical and weekly scraped CSV files 
│   └── vector/                 # Historical and weekly scraped CSV & Markdown files
└── database/
    ├── ff_sql.db               # SQLite database
    └── ff_vector/              # ChromaDB storage
```

## 🛠️ Available Commands

While chatting with the expert:
- **`stats`** - Show database statistics
- **`clear`** - Reset conversation history
- **`quit`** - Exit the application

## 🔧 Advanced Configuration

### LLM Configuration
Modify chatbot settings in `chatbot.py`:
```python
self.llm = ChatOpenAI(
    model="gpt-4",           # Change model
    temperature=0.1,         # Adjust creativity
    max_tokens=1000          # Response length limit
)
```

## 🚨 Troubleshooting

### Common Issues

**"OpenAI API key not found"**
```bash
export OPENAI_API_KEY='your-actual-key'
# Or check your .env file
```

**Scraper errors**
- Ensure Chrome browser is installed
- If a scraper fails app continues with available data

**Database issues**
```bash
# Reset databases
rm -rf database/
python main.py  # Will recreate everything
```

**Import errors**
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt
```

## 📜 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 and API access
- **LangChain** for the RAG framework
- **ChromaDB** for vector database functionality
- **ESPN** for fantasy football data (scraped respectfully)
- **DraftSharks** for injury and news RSS feeds

---
