'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Award } from 'lucide-react';

import { API_BASE_URL } from '@/lib/api';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

const AWS_CERTIFICATIONS = [
    'Generative AI Developer - Professional',
    'ML Engineer - Associate',
    'Solutions Architect - Associate',
    'AI Practitioner',
];

export default function Twin() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string>('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = async () => {
        if (isLoading) return;
        const messageText = input.trim();
        if (!messageText) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: messageText,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: messageText,
                    session_id: sessionId || undefined,
                }),
            });

            if (!response.ok) throw new Error('Failed to send message');

            const payload = await response.json();
            if (payload.session_id) {
                setSessionId(payload.session_id);
            }

            setMessages(prev => [
                ...prev,
                {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: payload.response ?? 'I ran into a temporary issue while generating a response. Please try again.',
                    timestamp: new Date(),
                },
            ]);
        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [
                ...prev,
                {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: 'I ran into a temporary issue while generating a response. Please try again.',
                    timestamp: new Date(),
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 rounded-lg shadow-lg">
            {/* Header */}
            <div className="rounded-t-lg bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 p-4 text-white sm:p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <h2 className="flex items-center gap-2 text-lg font-semibold sm:text-xl">
                            <Bot className="h-5 w-5 sm:h-6 sm:w-6" />
                            Welcome Message from Tumelo
                        </h2>
                        <p className="mt-1 text-sm text-slate-300">
                            A conversational way to explore my background, projects, and engineering approach.
                        </p>
                    </div>
                    <div className="rounded-full border border-emerald-300/30 bg-emerald-300/10 px-3 py-1 text-xs font-medium text-emerald-200">
                        Portfolio Experience | Live
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 space-y-4 overflow-y-auto bg-gradient-to-b from-white to-slate-50/90 p-4">
                {messages.length === 0 && (
                    <div className="mx-auto mt-8 max-w-3xl rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
                        <div className="mb-5 flex items-center gap-3">
                            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-white">
                                <Bot className="h-6 w-6" />
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-slate-900">Recruiter Snapshot</p>
                                <p className="text-sm text-slate-600">A quick, scannable overview before you chat.</p>
                            </div>
                        </div>

                        <div className="space-y-3 text-sm text-slate-700">
                            <section className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Who I Am</p>
                                <p className="mt-2 leading-6">
                                    Data Scientist and AI/ML Engineer with 6+ years building production-ready systems.
                                    I combine mathematical rigor with practical software engineering.
                                </p>
                            </section>

                            <section className="rounded-xl border border-slate-200 bg-white p-4">
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">What I Build</p>
                                <ul className="mt-2 list-disc space-y-1 pl-4 leading-6">
                                    <li>Production-grade RAG and agentic AI systems</li>
                                    <li>Modular API platforms with clean backend architecture</li>
                                    <li>End-to-end ML pipelines from training to deployment</li>
                                </ul>
                            </section>

                            <section className="rounded-xl border border-slate-200 bg-white p-4">
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Cloud &amp; Infrastructure</p>
                                <ul className="mt-2 list-disc space-y-1 pl-4 leading-6">
                                    <li>AWS-native AI deployment and infrastructure-as-code</li>
                                    <li>Terraform, Docker, and CI/CD-driven workflows</li>
                                    <li>Scalable, cost-aware system design for real usage</li>
                                </ul>
                            </section>

                            <section className="rounded-xl border border-amber-200 bg-amber-50/60 p-4">
                                <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-amber-800">
                                    <Award className="h-3.5 w-3.5" />
                                    Certifications
                                </p>
                                <p className="mt-2 leading-6 text-slate-700">AWS certified across GenAI, ML engineering, architecture, and AI fundamentals.</p>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {AWS_CERTIFICATIONS.map((certification) => (
                                        <span
                                            key={certification}
                                            className="rounded-full border border-amber-300/50 bg-white px-2.5 py-1 text-[11px] font-medium text-amber-900"
                                        >
                                            {certification}
                                        </span>
                                    ))}
                                </div>
                            </section>

                            <section className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Outside Work</p>
                                <p className="mt-2 leading-6">
                                    I stay sharp through hiking, fitness, football, and building side AI projects.
                                </p>
                            </section>
                        </div>
                    </div>
                )}

                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex gap-3 ${
                            message.role === 'user' ? 'justify-end' : 'justify-start'
                        }`}
                    >
                        {message.role === 'assistant' && (
                            <div className="flex-shrink-0">
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800">
                                    <Bot className="h-5 w-5 text-white" />
                                </div>
                            </div>
                        )}

                        <div
                            className={`max-w-[70%] rounded-lg p-3 ${
                                message.role === 'user'
                                    ? 'bg-slate-900 text-white shadow-sm'
                                    : 'border border-gray-200 bg-white text-gray-800 shadow-sm'
                            }`}
                        >
                            <p className="whitespace-pre-wrap">{message.content}</p>
                            <p
                                className={`text-xs mt-1 ${
                                    message.role === 'user' ? 'text-slate-300' : 'text-gray-500'
                                }`}
                            >
                                {message.timestamp.toLocaleTimeString()}
                            </p>
                        </div>

                        {message.role === 'user' && (
                            <div className="flex-shrink-0">
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-700">
                                    <User className="h-5 w-5 text-white" />
                                </div>
                            </div>
                        )}
                    </div>
                ))}

                {isLoading && messages[messages.length - 1]?.role !== 'assistant' && (
                    <div className="flex gap-3 justify-start">
                        <div className="flex-shrink-0">
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800">
                                <Bot className="h-5 w-5 text-white" />
                            </div>
                        </div>
                        <div className="bg-white border border-gray-200 rounded-lg p-3">
                            <div className="flex space-x-2">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="rounded-b-lg border-t border-gray-200 bg-white p-4">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder="Ask about my projects, strengths, deployment experience, or role fit..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-600 focus:border-transparent text-gray-800"
                        disabled={isLoading}
                    />
                    <button
                        onClick={() => sendMessage()}
                        disabled={!input.trim() || isLoading}
                        aria-label="Send message"
                        className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
