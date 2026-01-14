import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { nlApi } from '../api/client';
import { Terminal, Send, CheckCircle, XCircle } from 'lucide-react';

const LOCATION_ID = '00000000-0000-0000-0000-000000000001';

interface CommandResult {
  success: boolean;
  intent: string;
  confidence: number;
  result: Record<string, any>;
}

export function CommandPage() {
  const [command, setCommand] = useState('');
  const [history, setHistory] = useState<Array<{ command: string; result: CommandResult }>>([]);

  const executeMutation = useMutation({
    mutationFn: (text: string) => nlApi.command(text, LOCATION_ID),
    onSuccess: (response, text) => {
      setHistory((prev) => [...prev, { command: text, result: response.data }]);
      setCommand('');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (command.trim()) {
      executeMutation.mutate(command);
    }
  };

  const examples = [
    'Show me leads from today',
    'Find contacts tagged hot lead',
    'How many contacts do I have?',
    'Schedule a call with John tomorrow at 2pm',
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Terminal size={28} />
          Natural Language Control
        </h1>
        <p className="text-gray-500 mt-1">
          Control your CRM with plain English commands
        </p>
      </div>

      {/* Examples */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-500 mb-2">Try these:</h3>
        <div className="flex flex-wrap gap-2">
          {examples.map((ex) => (
            <button
              key={ex}
              onClick={() => setCommand(ex)}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Command Input */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type a command..."
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            className="flex-1 px-4 py-3 border rounded-lg text-lg"
          />
          <button
            type="submit"
            disabled={executeMutation.isPending || !command.trim()}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2"
          >
            <Send size={20} />
            Run
          </button>
        </div>
      </form>

      {/* Results History */}
      <div className="space-y-4">
        {history.slice().reverse().map((item, idx) => (
          <div key={idx} className="bg-white rounded-lg border p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <code className="text-blue-600 font-mono">{item.command}</code>
                <div className="text-sm text-gray-500 mt-1">
                  Intent: {item.result.intent} (confidence: {(item.result.confidence * 100).toFixed(0)}%)
                </div>
              </div>
              {item.result.success ? (
                <CheckCircle className="text-green-500" size={24} />
              ) : (
                <XCircle className="text-red-500" size={24} />
              )}
            </div>
            <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto">
              {JSON.stringify(item.result.result, null, 2)}
            </pre>
          </div>
        ))}
      </div>

      {history.length === 0 && (
        <div className="text-center text-gray-400 py-8">
          Run a command to see results here
        </div>
      )}
    </div>
  );
}
