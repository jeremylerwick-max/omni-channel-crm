import React, { useState } from 'react';
import Dashboard from './Dashboard';
import TaskCreate from './TaskCreate';
import TaskView from './TaskView';
import Results from './Results';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedTask, setSelectedTask] = useState(null);

  const navigate = (view, task = null) => {
    setCurrentView(view);
    if (task) setSelectedTask(task);
  };

  return (
    <div className="App">
      {currentView === 'dashboard' && (
        <Dashboard 
          onNavigate={navigate}
          onSelectTask={(task) => navigate('task-view', task)}
        />
      )}
      {currentView === 'create' && (
        <TaskCreate 
          onNavigate={navigate}
          onTaskCreated={(task) => navigate('task-view', task)}
        />
      )}
      {currentView === 'task-view' && selectedTask && (
        <TaskView 
          task={selectedTask}
          onNavigate={navigate}
        />
      )}
      {currentView === 'results' && selectedTask && (
        <Results 
          task={selectedTask}
          onNavigate={navigate}
        />
      )}
    </div>
  );
}

export default App;
