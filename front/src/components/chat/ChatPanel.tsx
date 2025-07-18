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
        fetchFiles,
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

    const programs = ['MPFS', 'HOSPICE', 'SNF'];
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

    // Fetch documents on component mount
    useEffect(() => {
        fetchFiles();
    }, [fetchFiles]);

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

                const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.chat}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
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
                    citations: data.citations || [],
                    sources: data.sources || []
                };

                addMessage(assistantMessage);

            } catch (error) {
                console.error('API call failed:', error);

                // More specific error messages
                let errorMessage = 'Daisy\'s cat seems to have caused some mischief! Seon, Sai, Sarvesh, Dhruv and Fanxing are working to fix it. Please try again later.';

                if (error instanceof TypeError && error.message.includes('fetch')) {
                    errorMessage = `Daisy's cat ran away, and Seon, Sai, Sarvesh, Dhruv and Fanxing are out looking for it. Please wait while they reconnect... Please check if the backend is running at ${config.api.baseUrl}`;
                } else if (error instanceof Error) {
                    errorMessage = `Error: ${error.message}`;
                }

                addMessage({
                    id: (Date.now() + 2).toString(),
                    role: 'assistant' as const,
                    content: errorMessage,
                    citations: []
                });
            } finally {
                setIsLoading(false);
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
            {/* Chat Header */}
            <div className="p-4 border-b border-neutral-200 bg-white">
                <div className="flex items-center justify-between">
                    <div className="flex items-center">
                        <div className="bg-teal-100 p-2 rounded-lg mr-3">
                            <MessageSquare className="h-5 w-5 text-teal-600" />
                        </div>
                        <h2 className="text-lg font-medium text-neutral-800">Chat</h2>
                    </div>
                    <button
                        onClick={() => clearMessages()}
                        className="p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
                        title="Clear conversation"
                    >
                        <RefreshCw className="h-4 w-4"/>
                    </button>
                </div>
                <p className="text-sm text-neutral-500 mt-1">
                    Ask questions about regulations or select specific documents as your knowledge base for inquiry.
                </p>
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
                    <div className="flex flex-col items-center justify-center min-h-[400px] text-center px-4">
                        <div className="bg-teal-100 p-4 sm:p-6 rounded-full mb-4 sm:mb-6 shadow-lg border-2 border-teal-200 flex items-center justify-center">
                            <MessageSquare className="h-8 w-8 sm:h-12 sm:w-12 text-teal-600" />
                        </div>
                        <h3 className="text-base sm:text-lg font-medium text-neutral-800 mb-2">Start a Conversation</h3>
                        <p className="text-neutral-500 mb-4 text-sm sm:text-base max-w-sm sm:max-w-md lg:max-w-lg">
                            You can select a document and ask me questions, or ask me directly. For more accurate answers, please specify the year, program, and type in your question.
                        </p>
                        <div className="w-full max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg">
                            <p className="mb-3 font-medium text-neutral-600 text-sm sm:text-base">Example questions:</p>
                            <div className="space-y-2">
                                {[
                                    "When did the CY 2024 Medicare Physician Fee Schedule (MPFS) Final Rule become effective?",
                                    "How are PE RVUs established for specific services?",
                                    "Why did CMS implement HCPCS code G2211 in 2024?",
                                    "What are the key changes in the 2024 MPFS payment methodology?"
                                ].map((suggestion, i) => (
                                    <button
                                        key={i}
                                        className="w-full text-left p-2 sm:p-3 border border-neutral-200 hover:bg-neutral-50 rounded-lg text-xs sm:text-sm text-neutral-700 transition-colors"
                                        onClick={() => setInput(suggestion)}
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                            <p className="mt-4 text-xs text-yellow-600 font-medium text-center">
                                RegHealth-Navigator can make mistakes. Please double-check responses.
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
                )}
                <div ref={messagesEndRef}/>
            </div>

            {/* Input Area */}
            <div className="p-6">
                <div className="max-w-2xl mx-auto">
                    <form onSubmit={handleSubmit} className="flex gap-3 bg-white rounded-2xl shadow-2xl p-2 border border-teal-200">
                        <div className="relative flex-1">
                            <button
                                type="button"
                                onClick={() => setShowDocumentSelector(!showDocumentSelector)}
                                className="absolute left-4 top-1/2 -translate-y-1/2 p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors z-10"
                            >
                                <Plus className="h-4 w-4"/>
                            </button>

                            {showDocumentSelector && (
                                <div
                                    ref={searchRef}
                                    className="absolute bottom-full left-0 right-0 mb-3 bg-white rounded-xl shadow-2xl border border-neutral-200 overflow-hidden"
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
                                placeholder="Ask about the documents... (Click + to select specific files)"
                                className="w-full pl-12 pr-4 py-4 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-200 bg-transparent text-lg"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={!input.trim()}
                            className={`p-4 rounded-xl transition-all duration-200 ${
                                input.trim()
                                    ? 'bg-gradient-to-r from-pink-400 to-pink-500 hover:from-pink-500 hover:to-pink-600 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
                                    : 'bg-pink-100 text-pink-300 cursor-not-allowed shadow-md'
                            }`}
                        >
                            <SendHorizontal className="h-6 w-6"/>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default ChatPanel;