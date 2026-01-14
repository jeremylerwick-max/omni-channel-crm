import React, { useState } from 'react';
import { ArrowLeft, Download, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

function Results({ task, onNavigate }) {
  const [activeTab, setActiveTab] = useState('outputs');

  const duration = task.completed_at 
    ? ((new Date(task.completed_at) - new Date(task.created_at)) / 1000).toFixed(1) + 's'
    : 'N/A';

  const isSuccess = task.status === 'completed';

  const handleDownload = (data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRerun = () => {
    onNavigate('create');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => onNavigate('dashboard')}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold">Task Results</h1>
              <p className="text-sm text-gray-400 font-mono">{task.task_id}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRerun}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Run Again</span>
            </button>
            <button
              onClick={() => handleDownload(task, `task_${task.task_id}_results.json`)}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          </div>
        </div>
      </header>

      <div className="p-8 max-w-6xl mx-auto">
        {/* Status Summary */}
        <div className={`rounded-lg p-6 mb-8 ${
          isSuccess ? 'bg-green-900 border border-green-700' : 'bg-red-900 border border-red-700'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {isSuccess ? (
                <CheckCircle className="w-12 h-12 text-green-400" />
              ) : (
                <XCircle className="w-12 h-12 text-red-400" />
              )}
              <div>
                <div className={`text-3xl font-bold ${
                  isSuccess ? 'text-green-400' : 'text-red-400'
                }`}>
                  {isSuccess ? 'Task Completed Successfully' : 'Task Failed'}
                </div>
                <div className="text-gray-300 mt-1">
                  Execution finished at {new Date(task.completed_at || task.updated_at).toLocaleString()}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-300">Total Duration</div>
              <div className="text-3xl font-bold">{duration}</div>
            </div>
          </div>
        </div>

        {/* Task Information */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">Task Information</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <div className="text-sm text-gray-400 mb-1">Module</div>
              <div className="font-semibold">{task.module_name}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Version</div>
              <div className="font-semibold">v{task.module_version}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Owner</div>
              <div className="font-semibold">{task.owner}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Status</div>
              <div className={`font-semibold ${
                isSuccess ? 'text-green-400' : 'text-red-400'
              }`}>
                {task.status.toUpperCase()}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-gray-800 rounded-lg overflow-hidden mb-8">
          <div className="flex border-b border-gray-700">
            <button
              onClick={() => setActiveTab('outputs')}
              className={`px-6 py-3 font-semibold transition-colors ${
                activeTab === 'outputs'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              Outputs
            </button>
            <button
              onClick={() => setActiveTab('inputs')}
              className={`px-6 py-3 font-semibold transition-colors ${
                activeTab === 'inputs'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              Inputs
            </button>
            <button
              onClick={() => setActiveTab('metadata')}
              className={`px-6 py-3 font-semibold transition-colors ${
                activeTab === 'metadata'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              Metadata
            </button>
          </div>

          <div className="p-6">
            {activeTab === 'outputs' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Task Outputs</h3>
                  {task.outputs && (
                    <button
                      onClick={() => handleDownload(task.outputs, `task_${task.task_id}_outputs.json`)}
                      className="text-sm px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                    >
                      Download Outputs
                    </button>
                  )}
                </div>
                {task.outputs ? (
                  <pre className="bg-gray-900 p-4 rounded overflow-x-auto text-sm max-h-96">
                    {JSON.stringify(task.outputs, null, 2)}
                  </pre>
                ) : (
                  <div className="text-gray-400 text-center py-8">
                    No outputs available
                  </div>
                )}
              </div>
            )}

            {activeTab === 'inputs' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Task Inputs</h3>
                <pre className="bg-gray-900 p-4 rounded overflow-x-auto text-sm">
                  {JSON.stringify(task.inputs, null, 2)}
                </pre>
              </div>
            )}

            {activeTab === 'metadata' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Task Metadata</h3>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-gray-400">Task ID</div>
                      <div className="font-mono text-sm bg-gray-900 p-2 rounded mt-1">
                        {task.task_id}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400">Created At</div>
                      <div className="font-mono text-sm bg-gray-900 p-2 rounded mt-1">
                        {new Date(task.created_at).toLocaleString()}
                      </div>
                    </div>
                    {task.completed_at && (
                      <div>
                        <div className="text-sm text-gray-400">Completed At</div>
                        <div className="font-mono text-sm bg-gray-900 p-2 rounded mt-1">
                          {new Date(task.completed_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                    {task.updated_at && (
                      <div>
                        <div className="text-sm text-gray-400">Updated At</div>
                        <div className="font-mono text-sm bg-gray-900 p-2 rounded mt-1">
                          {new Date(task.updated_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Error Details (if failed) */}
        {!isSuccess && task.error && (
          <div className="bg-red-900 border border-red-700 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-red-400">Error Details</h2>
            <pre className="bg-gray-900 p-4 rounded overflow-x-auto text-sm text-red-300">
              {typeof task.error === 'string' ? task.error : JSON.stringify(task.error, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default Results;
