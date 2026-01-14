import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Play, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function TaskCreate({ onNavigate, onTaskCreated }) {
  const [modules, setModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [owner, setOwner] = useState('test-user');
  const [inputs, setInputs] = useState('{}');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [jsonError, setJsonError] = useState(null);

  useEffect(() => {
    fetchModules();
  }, []);

  const fetchModules = async () => {
    try {
      const response = await axios.get(`${API_BASE}/modules`);
      setModules(response.data.modules || []);
    } catch (error) {
      console.error('Error fetching modules:', error);
      setError('Failed to load modules');
    }
  };

  const handleInputsChange = (value) => {
    setInputs(value);
    try {
      JSON.parse(value);
      setJsonError(null);
    } catch (e) {
      setJsonError('Invalid JSON format');
    }
  };

  const handleSubmit = async () => {
    if (!selectedModule) {
      setError('Please select a module');
      return;
    }

    if (jsonError) {
      setError('Please fix JSON errors before submitting');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const parsedInputs = JSON.parse(inputs);
      const response = await axios.post(`${API_BASE}/tasks`, {
        module_name: selectedModule.name,
        module_version: selectedModule.latest_version,
        owner: owner,
        inputs: parsedInputs
      });

      onTaskCreated(response.data);
    } catch (error) {
      console.error('Error creating task:', error);
      setError(error.response?.data?.detail || 'Failed to create task');
      setLoading(false);
    }
  };

  const setExampleInput = (moduleName) => {
    const examples = {
      browser_playwright: JSON.stringify({
        url: "https://example.com",
        action: "navigate",
        wait_for_selector: "body"
      }, null, 2),
      browser_auth: JSON.stringify({
        site: "google",
        username: "user@example.com",
        action: "login"
      }, null, 2),
      gcp_core: JSON.stringify({
        project_id: "my-project",
        action: "list_instances"
      }, null, 2),
      vertex_ai: JSON.stringify({
        prompt: "Explain quantum computing",
        model: "gemini-pro"
      }, null, 2),
      fb_business: JSON.stringify({
        account_id: "123456789",
        action: "get_campaigns"
      }, null, 2),
      mcp_provisioner: JSON.stringify({
        resource_type: "server",
        specifications: {}
      }, null, 2)
    };

    setInputs(examples[moduleName] || JSON.stringify({}, null, 2));
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-8 py-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => onNavigate('dashboard')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold">Create New Task</h1>
            <p className="text-sm text-gray-400">Configure and launch a new task</p>
          </div>
        </div>
      </header>

      <div className="p-8 max-w-6xl mx-auto">
        {error && (
          <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-red-400 mr-3 mt-0.5" />
            <div className="text-red-200">{error}</div>
          </div>
        )}

        {/* Owner Input */}
        <div className="mb-8 bg-gray-800 rounded-lg p-6">
          <label className="block text-sm font-semibold mb-2">Task Owner</label>
          <input
            type="text"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
            placeholder="Enter owner name"
          />
          <p className="text-xs text-gray-400 mt-2">Identifier for task tracking and permissions</p>
        </div>

        {/* Module Selection */}
        <div className="mb-8 bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Select Module</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {modules.map((module) => (
              <div
                key={module.name}
                onClick={() => {
                  setSelectedModule(module);
                  setExampleInput(module.name);
                }}
                className={`p-6 rounded-lg cursor-pointer transition-all ${
                  selectedModule?.name === module.name
                    ? 'bg-blue-600 ring-2 ring-blue-400'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-3xl">{getModuleIcon(module.name)}</span>
                  <span className="text-xs px-2 py-1 bg-gray-900 rounded font-mono">
                    v{module.latest_version}
                  </span>
                </div>
                <h3 className="font-bold mb-2 capitalize">
                  {module.name.replace(/_/g, ' ')}
                </h3>
                <div className="text-sm text-gray-300">
                  {module.sandbox_type}
                </div>
              </div>
            ))}
          </div>
          {!selectedModule && (
            <p className="text-sm text-gray-400 mt-4">Select a module to continue</p>
          )}
        </div>

        {/* Input Configuration */}
        {selectedModule && (
          <div className="mb-8 bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Task Inputs (JSON)</h2>
              <button
                onClick={() => setExampleInput(selectedModule.name)}
                className="text-sm px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
              >
                Reset to Example
              </button>
            </div>
            <textarea
              value={inputs}
              onChange={(e) => handleInputsChange(e.target.value)}
              className={`w-full h-64 px-4 py-3 bg-gray-900 border rounded-lg font-mono text-sm focus:outline-none ${
                jsonError ? 'border-red-500' : 'border-gray-600 focus:border-blue-500'
              }`}
              placeholder='{"key": "value"}'
            />
            {jsonError && (
              <p className="text-red-400 text-sm mt-2">{jsonError}</p>
            )}
            <p className="text-xs text-gray-400 mt-2">
              Enter the input parameters for the selected module as JSON
            </p>
          </div>
        )}

        {/* Submit Button */}
        {selectedModule && (
          <div className="flex items-center justify-end space-x-4">
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !!jsonError || !selectedModule}
              className={`flex items-center space-x-2 px-8 py-3 rounded-lg font-semibold transition-colors ${
                loading || jsonError || !selectedModule
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              <Play className="w-5 h-5" />
              <span>{loading ? 'Creating Task...' : 'Run Task'}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function getModuleIcon(name) {
  const icons = {
    gcp_core: '☁️',
    vertex_ai: '🤖',
    browser_playwright: '🌐',
    browser_auth: '🔐',
    fb_business: '📊',
    mcp_provisioner: '⚙️'
  };
  return icons[name] || '📦';
}

export default TaskCreate;
