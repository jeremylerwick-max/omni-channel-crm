import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, RefreshCw, CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function TaskView({ task, onNavigate }) {
  const [taskData, setTaskData] = useState(task);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (taskData.status === 'pending' || taskData.status === 'running') {
      const interval = setInterval(fetchTaskStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [taskData.status]);

  const fetchTaskStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/tasks/${taskData.task_id}`);
      setTaskData(response.data);
      
      // Simulate log updates (in production, this would come from WebSocket)
      if (response.data.status === 'running') {
        addLog('info', 'Task is executing...');
      } else if (response.data.status === 'completed') {
        addLog('success', 'Task completed successfully!');
      } else if (response.data.status === 'failed') {
        addLog('error', 'Task failed');
      }
    } catch (error) {
      console.error('Error fetching task status:', error);
    }
  };

  const addLog = (type, message) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { type, message, timestamp }]);
  };

  const getStatusInfo = (status) => {
    const configs = {
      pending: {
        icon: <Clock className="w-6 h-6 text-yellow-500" />,
        text: 'Pending',
        color: 'text-yellow-500',
        bg: 'bg-yellow-900'
      },
      running: {
        icon: <RefreshCw className="w-6 h-6 text-blue-500 animate-spin" />,
        text: 'Running',
        color: 'text-blue-500',
        bg: 'bg-blue-900'
      },
      completed: {
        icon: <CheckCircle className="w-6 h-6 text-green-500" />,
        text: 'Completed',
        color: 'text-green-500',
        bg: 'bg-green-900'
      },
      failed: {
        icon: <XCircle className="w-6 h-6 text-red-500" />,
        text: 'Failed',
        color: 'text-red-500',
        bg: 'bg-red-900'
      }
    };
    return configs[status] || configs.pending;
  };

  const statusInfo = getStatusInfo(taskData.status);
  const duration = taskData.completed_at 
    ? ((new Date(taskData.completed_at) - new Date(taskData.created_at)) / 1000).toFixed(1) + 's'
    : 'Running...';

  const steps = [
    { name: 'Task Created', completed: true },
    { name: 'Planning', completed: taskData.status !== 'pending' },
    { name: 'Module Loaded', completed: taskData.status === 'running' || taskData.status === 'completed' || taskData.status === 'failed' },
    { name: 'Executing', completed: taskData.status === 'running' || taskData.status === 'completed' || taskData.status === 'failed', current: taskData.status === 'running' },
    { name: 'Results Collection', completed: taskData.status === 'completed' || taskData.status === 'failed' },
    { name: 'Finished', completed: taskData.status === 'completed' || taskData.status === 'failed' }
  ];

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
              <h1 className="text-2xl font-bold">Task Execution</h1>
              <p className="text-sm text-gray-400 font-mono">{taskData.task_id}</p>
            </div>
          </div>
          {(taskData.status === 'completed' || taskData.status === 'failed') && (
            <button
              onClick={() => onNavigate('results', taskData)}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
            >
              View Results
            </button>
          )}
        </div>
      </header>

      <div className="p-8 max-w-6xl mx-auto">
        {/* Status Card */}
        <div className={`${statusInfo.bg} border border-gray-700 rounded-lg p-6 mb-8`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {statusInfo.icon}
              <div>
                <div className={`text-2xl font-bold ${statusInfo.color}`}>
                  {statusInfo.text}
                </div>
                <div className="text-gray-300">
                  Module: {taskData.module_name} v{taskData.module_version}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400">Duration</div>
              <div className="text-2xl font-bold">{duration}</div>
            </div>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-6">Execution Steps</h2>
          <div className="space-y-3">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-4 ${
                  step.completed
                    ? 'bg-green-600'
                    : step.current
                    ? 'bg-blue-600 animate-pulse'
                    : 'bg-gray-700'
                }`}>
                  {step.completed ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : step.current ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : (
                    <span>{index + 1}</span>
                  )}
                </div>
                <div className={`flex-1 py-3 px-4 rounded ${
                  step.current ? 'bg-blue-900' : 'bg-gray-700'
                }`}>
                  <div className="font-semibold">{step.name}</div>
                  {step.current && (
                    <div className="text-sm text-gray-300 mt-1">In progress...</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Task Details */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">Task Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-400">Owner</div>
              <div className="font-semibold">{taskData.owner}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Created At</div>
              <div className="font-semibold">{new Date(taskData.created_at).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Module</div>
              <div className="font-semibold">{taskData.module_name}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Version</div>
              <div className="font-semibold">v{taskData.module_version}</div>
            </div>
          </div>
        </div>

        {/* Inputs */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">Task Inputs</h2>
          <pre className="bg-gray-900 p-4 rounded overflow-x-auto text-sm">
            {JSON.stringify(taskData.inputs, null, 2)}
          </pre>
        </div>

        {/* Live Logs */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Live Logs</h2>
            <button
              onClick={fetchTaskStatus}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="bg-gray-900 rounded p-4 h-64 overflow-y-auto font-mono text-sm">
            {logs.length === 0 ? (
              <div className="text-gray-500">No logs yet...</div>
            ) : (
              logs.map((log, index) => (
                <div key={index} className={`mb-2 ${
                  log.type === 'error' ? 'text-red-400' :
                  log.type === 'success' ? 'text-green-400' :
                  'text-gray-300'
                }`}>
                  <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TaskView;
