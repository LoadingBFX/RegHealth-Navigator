import React, {useState, useRef, useEffect} from 'react';
import {useStore} from '../../store/store';
import {SendHorizontal, RefreshCw, Plus, X, Search, Filter, MessageSquare} from 'lucide-react';
import ChatMessage from './ChatMessage';
import config from '../../config';

const ChatPanel: React.FC = () => {
    const {
        messages,
        addMessage,
        clearMessages,
        selectedFiles,
        setSelectedFiles,
        files,
<<<<<<< HEAD
=======
        fetchFiles,
>>>>>>> dev
        showDocumentSelector,
        setShowDocumentSelector,
        searchTerm,
        setSearchTerm,
        yearFilter,
        setYearFilter,
        programFilter,
        setProgramFilter,
        typeFilter,
        setTypeFilter,
        showFilters,
        setShowFilters
    } = useStore();

    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const searchRef = useRef<HTMLDivElement>(null);
    const [isLoading, setIsLoading] = useState(false);

<<<<<<< HEAD
    const programs = ['MPFS', 'HOSPICE', 'SNF', 'QPP'];
=======
    const programs = ['MPFS', 'HOSPICE', 'SNF'];
>>>>>>> dev
    const types = ['final', 'proposed'];
    const years = ['2024', '2023', '2022', '2021'];

    const selectedFileNames = selectedFiles
        .map(id => files.find(file => file.id === id)?.name || '')
        .filter(Boolean);

    // Filter files based on search and filters
    const filteredFiles = files.filter(file => {
        const matchesSearch = file.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesYear = yearFilter === 'all' || file.name.includes(yearFilter);
        const matchesProgram = programFilter === 'all' || file.name.includes(programFilter);
        const matchesType = typeFilter === 'all' || file.name.includes(typeFilter);
        return matchesSearch && matchesYear && matchesProgram && matchesType;
    });

<<<<<<< HEAD
=======
    // Fetch documents on component mount
    useEffect(() => {
        fetchFiles();
    }, [fetchFiles]);

>>>>>>> dev
    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({behavior: 'smooth'});
        }
    }, [messages]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowDocumentSelector(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [setShowDocumentSelector]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (input.trim()) {
            const userMessage = {
                id: Date.now().toString(),
                role: 'user' as const,
                content: input
            };

            // Add user message to the chat
            addMessage(userMessage);

            // Clear input immediately for better UX
            const messageToSend = input;
            setInput('');
<<<<<<< HEAD

            try {
=======
            setIsLoading(true);

            try {
                // Prepare request body with selected documents
                const requestBody: any = { query: messageToSend };
                
                // Add selected documents if any are selected
                if (selectedFiles.length > 0) {
                    const selectedDocNames = selectedFiles
                        .map(id => files.find(file => file.id === id)?.name)
                        .filter(Boolean)
                        .map(name => `${name}.xml`); // Add .xml extension
                    requestBody.doc_names = selectedDocNames;
                }

>>>>>>> dev
                const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.chat}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
<<<<<<< HEAD
                    body: JSON.stringify({ query: messageToSend })
=======
                    body: JSON.stringify(requestBody)
>>>>>>> dev
                });

                // Check if the response is ok
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Server error: ${response.status} - ${errorText}`);
                }

                // Check if response is JSON
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned non-JSON response');
                }

                const data = await response.json();

                // Handle error responses from the server
                if (data.error) {
                    throw new Error(data.error);
                }

                // Create assistant message with the expected format
                const assistantMessage = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant' as const,
                    content: data.response || 'No response from server',
<<<<<<< HEAD
                    citations: data.citations || []
=======
                    citations: data.citations || [],
                    sources: data.sources || []
>>>>>>> dev
                };

                addMessage(assistantMessage);

            } catch (error) {
                console.error('API call failed:', error);

                // More specific error messages
                let errorMessage = 'Sorry, something went wrong. Please try again later.';

                if (error instanceof TypeError && error.message.includes('fetch')) {
                    errorMessage = `Unable to connect to the server. Please check if the backend is running at ${config.api.baseUrl}`;
                } else if (error instanceof Error) {
                    errorMessage = `Error: ${error.message}`;
                }

                addMessage({
                    id: (Date.now() + 2).toString(),
                    role: 'assistant' as const,
                    content: errorMessage,
                    citations: []
                });
<<<<<<< HEAD
=======
            } finally {
                setIsLoading(false);
>>>>>>> dev
            }
        }
    };

    const handleFileSelect = (fileId: string) => {
        if (selectedFiles.includes(fileId)) {
            setSelectedFiles(selectedFiles.filter(id => id !== fileId));
        } else {
            setSelectedFiles([...selectedFiles, fileId]);
        }
    };

    const removeSelectedFile = (fileId: string) => {
        setSelectedFiles(selectedFiles.filter(id => id !== fileId));
    };

    const clearAllFilters = () => {
        setSearchTerm('');
        setYearFilter('all');
        setProgramFilter('all');
        setTypeFilter('all');
    };

    const hasActiveFilters = searchTerm || yearFilter !== 'all' || programFilter !== 'all' || typeFilter !== 'all';

    return (
        <div className="flex-1 flex flex-col h-full">
<<<<<<< HEAD
=======
            {/* Demo Mode Banner */}
            <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="ml-3">
                            <p className="text-sm font-medium text-yellow-800">
                                Demo Mode - Sample Data
                            </p>
                            <p className="text-sm text-yellow-700">
                                This is a demonstration with sample data. Backend connection is not configured.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

>>>>>>> dev
            {/* Chat Header */}
            <div className="p-4 border-b border-neutral-200 bg-white">
                <div className="flex justify-between items-center">
                    <div>
                        <h2 className="text-lg font-medium text-neutral-800">Chat</h2>
                        {selectedFiles.length > 0 && (
                            <p className="text-sm text-neutral-500 mt-1">
                                Analyzing: {selectedFileNames.join(', ')}
                            </p>
                        )}
                    </div>
                    <button
                        onClick={() => clearMessages()}
                        className="p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
                        title="Clear conversation"
                    >
                        <RefreshCw className="h-4 w-4"/>
                    </button>
                </div>

                {/* Selected Files Tags */}
                {selectedFiles.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                        {selectedFiles.map(fileId => {
                            const file = files.find(f => f.id === fileId);
                            if (!file) return null;

                            return (
                                <div
                                    key={fileId}
                                    className="flex items-center gap-1 px-2 py-1 bg-primary-50 text-primary-700 rounded-full text-sm"
                                >
                                    <span>{file.name}</span>
                                    <button
                                        onClick={() => removeSelectedFile(fileId)}
                                        className="p-0.5 hover:bg-primary-100 rounded-full"
                                    >
                                        <X className="h-3 w-3"/>
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="bg-primary-50 p-4 rounded-full mb-4">
                            <MessageSquare className="h-8 w-8 text-primary-700" />
                        </div>
                        <h3 className="text-lg font-medium text-neutral-800 mb-2">Start a Conversation</h3>
                        <p className="text-neutral-500 mb-4 max-w-md">
                            You can select a document and ask me questions, or ask me directly. For more accurate answers, please specify the year, program, and type in your question.
                        </p>
                        <div className="text-sm text-neutral-600 max-w-md">
<<<<<<< HEAD
                            <p className="mb-2 font-medium">Example questions:</p>
=======
                            <p className="mb-2 font-medium">Example questions (demo data):</p>
>>>>>>> dev
                            <ul className="text-left space-y-1 text-xs">
                                <li>• When did the CY 2024 Medicare Physician Fee Schedule (MPFS) Final Rule become effective?</li>
                                <li>• What is the finalized conversion factor for CY 2024, and how does it compare to CY 2023?</li>
                                <li>• Why did CMS implement HCPCS code G2211 in 2024?</li>
                            </ul>
<<<<<<< HEAD
                        </div>
                    </div>
                ) : (
                    messages.map(message => (
                        <ChatMessage key={message.id} message={message}/>
                    ))
=======
                            <p className="mt-2 text-xs text-yellow-600 font-medium">
                                ⚠️ Note: These are sample responses for demonstration purposes only.
                            </p>
                        </div>
                    </div>
                ) : (
                    <>
                        {messages.map(message => (
                            <ChatMessage key={message.id} message={message}/>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="max-w-3/4 rounded-lg p-4 bg-neutral-100 text-neutral-800">
                                    <div className="flex items-center space-x-2">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                                            <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                                            <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                                        </div>
                                        <span className="text-sm text-neutral-500">Thinking...</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
>>>>>>> dev
                )}
                <div ref={messagesEndRef}/>
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-neutral-200 bg-white">
                <form onSubmit={handleSubmit} className="flex gap-2">
                    <div className="relative flex-1">
                        <button
                            type="button"
                            onClick={() => setShowDocumentSelector(!showDocumentSelector)}
                            className="absolute left-3 top-1/2 -translate-y-1/2 p-1 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
                        >
                            <Plus className="h-4 w-4"/>
                        </button>

                        {showDocumentSelector && (
                            <div
                                ref={searchRef}
                                className="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-lg shadow-lg border border-neutral-200 overflow-hidden"
                            >
                                <div className="p-3 border-b border-neutral-200">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400"/>
                                        <input
                                            type="text"
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            placeholder="Search documents..."
                                            className="w-full pl-9 pr-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                        />
                                    </div>

                                    <div className="flex items-center gap-2 mt-2">
                                        <button
                                            type="button"
                                            onClick={() => setShowFilters(!showFilters)}
                                            className="flex items-center gap-1 px-2 py-1 text-sm text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
                                        >
                                            <Filter className="h-4 w-4"/>
                                            Filters
                                            {hasActiveFilters && (
                                                <span className="ml-1 px-1.5 py-0.5 bg-primary-100 text-primary-700 rounded-full text-xs">
                                                    Active
                                                </span>
                                            )}
                                        </button>

                                        {hasActiveFilters && (
                                            <button
                                                type="button"
                                                onClick={clearAllFilters}
                                                className="text-sm text-primary-700 hover:text-primary-800"
                                            >
                                                Clear all
                                            </button>
                                        )}
                                    </div>

                                    {showFilters && (
                                        <div className="mt-2 space-y-2">
                                            <div>
                                                <label className="block text-xs font-medium text-neutral-700 mb-1">
                                                    Year
                                                </label>
                                                <select
                                                    value={yearFilter}
                                                    onChange={(e) => setYearFilter(e.target.value)}
                                                    className="w-full px-2 py-1 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                                >
                                                    <option value="all">All Years</option>
                                                    {years.map(year => (
                                                        <option key={year} value={year}>{year}</option>
                                                    ))}
                                                </select>
                                            </div>

                                            <div>
                                                <label className="block text-xs font-medium text-neutral-700 mb-1">
                                                    Program
                                                </label>
                                                <select
                                                    value={programFilter}
                                                    onChange={(e) => setProgramFilter(e.target.value)}
                                                    className="w-full px-2 py-1 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                                >
                                                    <option value="all">All Programs</option>
                                                    {programs.map(program => (
                                                        <option key={program} value={program}>{program}</option>
                                                    ))}
                                                </select>
                                            </div>

                                            <div>
                                                <label className="block text-xs font-medium text-neutral-700 mb-1">
                                                    Type
                                                </label>
                                                <select
                                                    value={typeFilter}
                                                    onChange={(e) => setTypeFilter(e.target.value)}
                                                    className="w-full px-2 py-1 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                                >
                                                    <option value="all">All Types</option>
                                                    {types.map(type => (
                                                        <option key={type} value={type}>{type}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="max-h-60 overflow-y-auto">
                                    {filteredFiles.length > 0 ? (
                                        <div className="divide-y divide-neutral-200">
                                            {filteredFiles.map(file => (
                                                <div
                                                    key={file.id}
                                                    className={`p-3 cursor-pointer transition-colors ${
                                                        selectedFiles.includes(file.id)
                                                            ? 'bg-primary-50 border border-primary-200'
                                                            : 'hover:bg-neutral-50'
                                                    }`}
                                                    onClick={() => handleFileSelect(file.id)}
                                                >
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium text-neutral-800 truncate">{file.name}</p>
                                                        <div className="flex text-xs text-neutral-500 mt-1">
                                                            <span className="mr-2">{file.size}</span>
                                                            <span>{file.date}</span>
                                                        </div>
                                                    </div>
                                                    {selectedFiles.includes(file.id) && (
                                                        <div
                                                            className="ml-2 w-2 h-2 bg-primary-600 rounded-full"></div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="p-4 text-center text-neutral-500 text-sm">
                                            No documents found
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask about the documents..."
                            className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={!input.trim()}
                        className={`p-3 rounded-lg transition-colors ${
                            input.trim()
                                ? 'bg-primary-700 hover:bg-primary-800 text-white'
                                : 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
                        }`}
                    >
                        <SendHorizontal className="h-5 w-5"/>
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatPanel;