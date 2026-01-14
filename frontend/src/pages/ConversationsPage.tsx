import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { conversationsApi, messagesApi, Conversation, Message } from '../api/client';
import { Send, User } from 'lucide-react';

const LOCATION_ID = '00000000-0000-0000-0000-000000000001';

export function ConversationsPage() {
  const [selectedConvo, setSelectedConvo] = useState<Conversation | null>(null);

  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationsApi.list(LOCATION_ID),
    select: (res) => res.data,
  });

  return (
    <div className="flex h-full">
      {/* Conversation List */}
      <div className="w-80 border-r bg-white">
        <div className="p-4 border-b">
          <h2 className="font-bold">Conversations</h2>
        </div>
        <div className="overflow-auto h-[calc(100%-57px)]">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Loading...</div>
          ) : conversations?.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No conversations</div>
          ) : (
            conversations?.map((convo) => (
              <div
                key={convo.id}
                onClick={() => setSelectedConvo(convo)}
                className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                  selectedConvo?.id === convo.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">
                      Contact: {convo.contact_id.slice(0, 8)}...
                    </div>
                    <div className="text-sm text-gray-500 truncate">
                      {convo.last_message_body || 'No messages'}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`px-2 py-0.5 text-xs rounded ${
                      convo.status === 'open' ? 'bg-green-100 text-green-700' :
                      convo.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {convo.status}
                    </span>
                    {convo.unread_count > 0 && (
                      <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                        {convo.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Message Thread */}
      <div className="flex-1 flex flex-col">
        {selectedConvo ? (
          <MessageThread conversation={selectedConvo} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            Select a conversation
          </div>
        )}
      </div>
    </div>
  );
}

function MessageThread({ conversation }: { conversation: Conversation }) {
  const [newMessage, setNewMessage] = useState('');
  const queryClient = useQueryClient();

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', conversation.id],
    queryFn: () => conversationsApi.messages(conversation.id),
    select: (res) => res.data,
  });

  const sendMutation = useMutation({
    mutationFn: (body: string) =>
      messagesApi.send({
        to: conversation.contact_id, // Note: Need actual phone number
        body,
        location_id: '00000000-0000-0000-0000-000000000001',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', conversation.id] });
      setNewMessage('');
    },
  });

  const handleSend = () => {
    if (newMessage.trim()) {
      sendMutation.mutate(newMessage);
    }
  };

  return (
    <>
      {/* Header */}
      <div className="p-4 border-b bg-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
            <User size={20} className="text-gray-500" />
          </div>
          <div>
            <div className="font-medium">Contact {conversation.contact_id.slice(0, 8)}</div>
            <div className="text-sm text-gray-500">{conversation.channel}</div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {isLoading ? (
          <div className="text-center text-gray-500">Loading messages...</div>
        ) : (
          messages?.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] px-4 py-2 rounded-lg ${
                  msg.direction === 'outbound'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-900'
                }`}
              >
                <p>{msg.body}</p>
                <p className={`text-xs mt-1 ${
                  msg.direction === 'outbound' ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {new Date(msg.created_at).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type a message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          <button
            onClick={handleSend}
            disabled={sendMutation.isPending || !newMessage.trim()}
            className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </>
  );
}
