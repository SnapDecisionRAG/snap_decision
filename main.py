import os
import sys
from scraper_controller import main as run_scrapers
from chatbot import main as start_chatbot

def main():
    print('=' * 60)
    print('FANTASY FOOTBALL RAG APPLICATION')
    print('=' * 60)

    if not (os.getenv('OPENAI_API_KEY')):
        print('OPENAI_API_KEY environment variable not found')
        print('Please set your OpenAI API key:')
        print('export OPENAI_API_KEY="your-api-key-here"')
        print('Or create a .env file with: OPENAI_API_KEY=your-api-key-here')
        sys.exit(1)

    print('Environment check passed')
    print('\nRunning scraper controller...')

    try:
        run_scrapers()
        print('Data collection completed')
    except Exception as e:
        print(f'Scraper controller had issues: {e}')
        print('Continuing with available data...')

    print('Starting Fanatasy Football Expert...\n')

    try:
        start_chatbot()
    except Exception as e:
        print(f'Failed to start chatbot: {e}')
        print('Please check your setup and try again.')
        sys.exit(1)

if __name__ == '__main__': main()
