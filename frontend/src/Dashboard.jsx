import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { RefreshCw, Play, CheckCircle, Clock, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function Dashboard({ onNavigate, onSelectTask }) {
  const [health, setHealth] = useState(null);
  const [modules, setModules] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [healthRes, modulesRes, tasksRes] = await Promise.all([
        axios.get(`${API_BASE}/health`),
        axios.get(`${API_BASE}/modules`),
        axios.get(`${API_BASE}/tasks?limit=10`).catch(() => ({ data: { tasks: [] } }))
      ]);
      
      setHealth(healthRes.data);
      setModules(modulesRes.data.modules || []);
      setTasks(tasksRes.data.tasks || []);
      setLoading(false);
      setError(null);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to connect to API. Make sure the server is running on port 8000.');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading orchestrator...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <div className="text-red-500 text-xl mb-4">Connection Error</div>
          <div className="text-gray-400 mb-6">{error}</div>
          <button 
            onClick={fetchData}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const queueCount = extractCount(health?.services?.scheduler);
  const sandboxCount = extractCount(health?.services?.sandboxes);
  const completedTasks = tasks.filter(t => t.status === 'completed').length;

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-3xl">🤖</div>
            <div>
              <h1 className="text-2xl font-bold">Agent Orchestrator</h1>
              <p className="text-sm text-gray-400">Intelligent Task Automation Platform</p>
            </div>
          </div>
          <button 
            onClick={fetchData}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </header>

      <div className="p-8">
        {/* System Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={<CheckCircle className="w-8 h-8 text-green-500" />}
            title="System Status"
            value={health?.status || 'Unknown'}
            color="green"
          />
          <StatCard
            icon={<span className="text-3xl">📦</span>}
            title="Modules Loaded"
            value={modules.length}
            color="blue"
          />
          <StatCard
            icon={<Clock className="w-8 h-8 text-yellow-500" />}
            title="Queue"
            value={queueCount}
            color="yellow"
          />
          <StatCard
            icon={<span className="text-3xl">🐳</span>}
            title="Sandboxes"
            value={sandboxCount}
            color="purple"
          />
        </div>

        {/* Services Status */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <span className="mr-2">🔧</span>
            Services Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {health?.services && Object.entries(health.services).map(([service, status]) => (
              <div key={service} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                <span className="capitalize">{service.replace(/_/g, ' ')}</span>
                <span className={`px-3 py-1 rounded text-sm font-semibold ${
                  String(status).toLowerCase().includes('ok') ? 'bg-green-600' : 'bg-red-600'
                }`}>
                  {String(status)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Tasks */}
        {tasks.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <span className="mr-2">📝</span>
              Recent Tasks
            </h2>
            <div className="space-y-2">
              {tasks.map((task) => (
                <div 
                  key={task.task_id}
                  onClick={() => onSelectTask(task)}
                  className="flex items-center justify-between p-4 bg-gray-700 rounded hover:bg-gray-600 cursor-pointer transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <StatusIcon status={task.status} />
                    <div>
                      <div className="font-mono text-sm">{task.task_id}</div>
                      <div className="text-xs text-gray-400">{task.module_name}</div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-400">
                    {new Date(task.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Available Modules */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold flex items-center">
              <span className="mr-2">📦</span>
              Available Modules
            </h2>
            <button 
              onClick={() => onNavigate('create')}
              className="flex items-center space-x-2 px-6 py-3 bg-green-600 rounded-lg hover:bg-green-700 font-semibold transition-colors"
            >
              <Play className="w-4 h-4" />
              <span>Create Task</span>
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {modules.map((module) => (
              <div 
                key={module.name} 
                className="p-6 bg-gray-700 rounded-lg hover:bg-gray-600 cursor-pointer transition-colors"
                onClick={() => onNavigate('create')}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold text-lg capitalize flex items-center">
                    {getModuleIcon(module.name)}
                    <span className="ml-2">{module.name.replace(/_/g, ' ')}</span>
                  </h3>
                  <span className="text-xs px-2 py-1 bg-blue-600 rounded font-mono">
                    v{module.latest_version}
                  </span>
                </div>
                <div className="text-sm text-gray-300 space-y-1">
                  <div>🏗️ Type: <span className="font-semibold">{module.sandbox_type}</span></div>
                  <div>📚 Versions: {module.versions.length}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Getting Started CTA */}
        <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">🚀 Ready to Get Started?</h2>
          <p className="text-gray-300 mb-6">
            Create your first task and watch the orchestrator execute it in real-time!
          </p>
          <button 
            onClick={() => onNavigate('create')}
            className="px-8 py-4 bg-white text-gray-900 rounded-lg hover:bg-gray-100 font-bold text-lg transition-colors"
          >
            Create Your First Task →
          </button>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, title, value, color }) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 hover:scale-105 transition-transform">
      <div className="mb-3">
        {icon}
      </div>
      <div className="text-sm text-gray-400 mb-1">{title}</div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  );
}

function StatusIcon({ status }) {
  const icons = {
    pending: <Clock className="w-5 h-5 text-yellow-500" />,
    running: <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />,
    completed: <CheckCircle className="w-5 h-5 text-green-500" />,
    failed: <AlertCircle className="w-5 h-5 text-red-500" />
  };
  return icons[status] || icons.pending;
}

function extractCount(status) {
  if (!status) return '0';
  const match = String(status).match(/\((\d+)/);
  return match ? match[1] : '0';
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

export default Dashboard;
