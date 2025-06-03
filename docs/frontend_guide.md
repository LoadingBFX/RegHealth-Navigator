# Frontend Development Guide

## Project Structure

```
front/
├── src/
│   ├── components/         # React components
│   │   ├── chat/          # Chat-related components
│   │   ├── layout/        # Layout components (Header, Sidebar, etc.)
│   │   └── results/       # Results panel components
│   ├── store/             # State management (Zustand store)
│   ├── types/             # TypeScript type definitions
│   ├── utils/             # Utility functions
│   ├── App.tsx           # Main application component
│   └── main.tsx          # Application entry point
├── public/               # Static assets
└── index.html           # HTML template
```

## Key Components

### Layout Components
- `Header.tsx`: Top navigation bar with active file display
- `Sidebar.tsx`: Left sidebar with file selection and history
- `Layout.tsx`: Main layout wrapper component

### Feature Components
- `ChatPanel.tsx`: Chat interface for Q&A
- `ResultsPanel.tsx`: Right panel for displaying summaries and comparisons
- `SummaryTab.tsx`: Summary generation interface
- `FAQTab.tsx`: FAQ generation interface
- `ComparisonTab.tsx`: Document comparison interface

## State Management

The application uses Zustand for state management. The main store is defined in `store/store.ts`:

```typescript
interface Store {
  // File Management
  files: File[];
  selectedFiles: string[];
  
  // UI State
  activeTab: 'summary' | 'faq' | 'comparison';
  activeSidebarTab: 'files' | 'history';
  isProcessing: boolean;
  processingProgress: number;
  
  // Chat
  messages: Message[];
  
  // Actions
  setSelectedFiles: (files: string[]) => void;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  // ... other actions
}
```

## Backend Integration

### API Endpoints

The frontend interacts with the FastAPI backend through the following endpoints:

1. **File Management**
   ```typescript
   // Upload XML file
   POST /api/files/upload
   Content-Type: multipart/form-data
   Body: { file: File }
   Response: { id: string, name: string, size: string, date: string }

   // Get file list
   GET /api/files
   Response: File[]

   // Get file content
   GET /api/files/{file_id}
   Response: { content: string }
   ```

2. **Analysis Endpoints**
   ```typescript
   // Generate summary
   POST /api/analyze/summary
   Body: { file_ids: string[] }
   Response: { sections: Section[] }

   // Generate FAQ
   POST /api/analyze/faq
   Body: { file_ids: string[] }
   Response: { questions: Question[] }

   // Compare documents
   POST /api/analyze/compare
   Body: { file_ids: string[], aspect: string }
   Response: { changes: Change[] }
   ```

3. **Chat Endpoints**
   ```typescript
   // Send chat message
   POST /api/chat/message
   Body: { message: string, file_ids: string[] }
   Response: { 
     content: string,
     citations: string[]
   }
   ```

### API Integration Example

```typescript
// Example of API integration in a component
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(`${API_BASE_URL}/files/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const generateSummary = async (fileIds: string[]) => {
  const response = await axios.post(`${API_BASE_URL}/analyze/summary`, {
    file_ids: fileIds,
  });
  
  return response.data;
};
```

### Chat Example

Here's a simple example of how the chat interface interacts with the backend:

1. **Frontend (ChatPanel.tsx)**:
```typescript
// State for input text
const [input, setInput] = useState('');

// Handle form submission
const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
        // Send POST request to backend
        const response = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                section_id: "demo_section",
                query: input 
            }),
        });

        // Handle response
        const data = await response.json();
        // Display response in chat
        addMessage({
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.response
        });
    }
};

// Input field in JSX
<input
    type="text"
    value={input}
    onChange={(e) => setInput(e.target.value)}
    placeholder="Ask about the XML documents..."
    className="flex-1 p-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
/>
```

2. **Backend (main.py)**:
```python
@app.post("/api/chat")
async def chat(request: SectionRequest):
    """Chat with a specific section"""
    try:
        # Hardcoded response for demonstration
        response = f"Hello! You asked about section {request.section_id}. Your query was: {request.query}"
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

3. **Data Flow**:
   - User types in the input field
   - Clicks send button or presses enter
   - Frontend sends POST request to `/api/chat`
   - Backend processes request and returns response
   - Frontend displays response in chat interface

4. **Testing**:
   1. Start backend server:
   ```bash
   cd app
   uvicorn main:app --reload
   ```
   
   2. Start frontend development server:
   ```bash
   cd front
   npm run dev
   ```
   
   3. Open frontend in browser
   4. Type message in input field
   5. Click send button
   6. View response in chat interface

## Error Handling

Implement error handling for API calls:

```typescript
try {
  const response = await apiCall();
  // Handle success
} catch (error) {
  if (axios.isAxiosError(error)) {
    // Handle API errors
    console.error('API Error:', error.response?.data);
    // Show user-friendly error message
  } else {
    // Handle other errors
    console.error('Error:', error);
  }
}
```

## Development Guidelines

1. **Component Structure**
   - Keep components small and focused
   - Use TypeScript interfaces for props
   - Implement proper error boundaries
   - Use React hooks for state management

2. **API Integration**
   - Use axios for HTTP requests
   - Implement proper error handling
   - Use environment variables for API URLs
   - Implement request/response interceptors for common operations

3. **State Management**
   - Use Zustand for global state
   - Keep component state local when possible
   - Implement proper loading states
   - Handle API errors in the store

4. **Styling**
   - Use Tailwind CSS for styling
   - Follow the existing design system
   - Maintain responsive design
   - Use consistent spacing and colors

## Environment Setup

1. Create a `.env` file:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## Testing

1. Write unit tests for components
2. Test API integration
3. Test error handling
4. Test responsive design

## Deployment

1. Build the application:
   ```bash
   npm run build
   ```

2. Serve the built files from your FastAPI backend:
   ```python
   from fastapi.staticfiles import StaticFiles
   
   app.mount("/", StaticFiles(directory="front/dist", html=True), name="static")
   ```

## Common Issues and Solutions

1. **CORS Issues**
   - Ensure FastAPI CORS middleware is configured correctly
   - Check API URL configuration

2. **File Upload Issues**
   - Check file size limits
   - Verify multipart/form-data handling
   - Check file type validation

3. **State Management Issues**
   - Verify store updates
   - Check component re-renders
   - Validate state shape

## Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation
4. Create pull requests with clear descriptions 