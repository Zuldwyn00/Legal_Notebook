# AI Knowledge Assistant UI

A modern CustomTkinter-based user interface for the AI Knowledge Assistant, designed to mimic NotebookLM's functionality with a sleek orange and black color scheme.

## Author

**Zuldwyn00** - Creator and Developer of AI Framework

*This project represents a comprehensive AI knowledge management system built with modern Python technologies and a sleek user interface.*

## Contact

- **GitHub**: [Zuldwyn00]
- **Email**: [zuldwyn@gmail.com]
- **LinkedIn**: [https://www.linkedin.com/in/justin-pinter-9473b4366]

---

## Features

🎨 **Modern UI Design**
- Clean orange and black dark theme
- Responsive layout with proper component separation
- Intuitive search interface with example queries

🔍 **Smart Search**
- Vector-based knowledge base search
- Real-time relevance scoring
- Source document and page range tracking

🤖 **AI-Powered Responses**
- Context-aware AI responses using found documents
- Threaded processing to prevent UI freezing
- Clear error handling and user feedback

## Project Structure

```
ui/
├── __init__.py                 # Package initialization
├── app.py                      # Main application launcher
├── main_window.py              # Primary application window
├── theme.py                    # Orange/black color theme
├── components/                 # UI components
│   ├── __init__.py
│   ├── query_input.py          # Search input component
│   ├── results_display.py      # Search results display
│   └── ai_response.py          # AI response display
├── services/                   # Backend services
│   ├── __init__.py
│   └── chat_service.py         # Chat and search logic
└── README.md                   # This file
```

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure your knowledge base is set up:**
   - Make sure your vector database (Qdrant) is running
   - Verify that documents have been ingested using the main.py embedding pipeline
   - Check that Azure OpenAI credentials are configured in your .env file

## Usage

### Running the Application

```bash
# From the project root directory
python ui/app.py
```

### Using the Interface

1. **Ask Questions**: Enter your question in the text area
2. **Use Examples**: Click on example questions for quick starts
3. **Search**: Press Ctrl+Enter or click the "Search" button
4. **Review Results**: Check the found documents and relevance scores
5. **Read AI Response**: Get contextual answers based on your knowledge base

### Keyboard Shortcuts

- `Ctrl + Enter`: Execute search from anywhere in the application
- Standard text editing shortcuts work in all input areas

## Color Scheme

The interface uses a custom orange and black theme:

- **Primary Colors**: Black (#000000) for main backgrounds
- **Accent Colors**: Orange (#FF6B35) for highlights and interactive elements
- **Text Colors**: White for primary text, gray tones for secondary information
- **UI Elements**: Subtle borders and hover effects in complementary shades

## Architecture

### Component Separation

Each UI component is kept under 500 lines and has a single responsibility:

- **QueryInputFrame**: Handles user input and example queries
- **ResultsDisplayFrame**: Shows search results with metadata
- **AIResponseFrame**: Displays AI-generated responses
- **ChatService**: Manages backend AI and search operations

### Threading

Search operations run in background threads to maintain UI responsiveness, with proper error handling and user feedback.

### Theme System

The custom theme is centralized in `theme.py` and applied consistently across all components.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed via `pip install -r requirements.txt`
2. **No Search Results**: Verify your Qdrant database is running and contains indexed documents
3. **AI Response Failures**: Check your Azure OpenAI configuration and API keys
4. **UI Not Loading**: Make sure you're running from the project root directory

### Debug Mode

To enable debug logging, modify the logging configuration in your `config.yaml` file.

## Development

### Adding New Components

1. Create new component files in `ui/components/`
2. Import and apply the `OrangeBlackTheme` for consistent styling
3. Keep components focused and under 500 lines
4. Follow the existing patterns for grid layout and styling

### Modifying the Theme

Edit `ui/theme.py` to adjust colors and styling. The theme is applied automatically when the application starts.

## Dependencies

- `customtkinter>=5.2.0`: Modern UI framework
- `langchain`: AI and LLM integration
- `qdrant-client`: Vector database client
- `azure-ai-inference`: Azure OpenAI integration
- Additional dependencies as specified in `requirements.txt`
