"use client"

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ChatInterface } from '@/components/chat/chat-interface';
import { apiClient, MessageResponse } from '@/lib/api-client';
import { ShieldCheck } from 'lucide-react';

export default function ConversationPage() {
  const params = useParams();
  const conversationId = params.id as string;
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (conversationId) {
      loadMessages();
    }
  }, [conversationId]);

  const loadMessages = async () => {
    try {
      const msgs = await apiClient.getMessages(conversationId);
      setMessages(msgs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center gap-2 text-muted-foreground">
          <ShieldCheck className="animate-pulse size-5" />
          <span>Loading conversation...</span>
        </div>
      </div>
    );
  }

  return <ChatInterface conversationId={conversationId} initialMessages={messages} />;
}
