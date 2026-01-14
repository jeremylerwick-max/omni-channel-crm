# CC-05: Visual Workflow Builder

## Overview
React Flow-based drag-and-drop workflow builder with bi-directional sync to code definitions.

## Repository
`/Users/mac/Desktop/omni-channel-crm`

## Priority
**P0 - Table Stakes** - Users expect visual workflow building.

## Tech Stack
- React 18
- React Flow (npm install reactflow)
- TypeScript
- TailwindCSS
- Zustand (state management)

## Files to Create

```
frontend/src/
├── components/workflow-builder/
│   ├── WorkflowCanvas.tsx       # Main React Flow canvas
│   ├── NodePalette.tsx          # Draggable action nodes
│   ├── nodes/
│   │   ├── index.ts
│   │   ├── TriggerNode.tsx      # Workflow trigger
│   │   ├── SendSMSNode.tsx      # SMS action
│   │   ├── SendEmailNode.tsx    # Email action
│   │   ├── DelayNode.tsx        # Wait/delay
│   │   ├── ConditionNode.tsx    # If/then branch
│   │   ├── AddTagNode.tsx       # Tag action
│   │   ├── WebhookNode.tsx      # HTTP request
│   │   └── EndNode.tsx          # Workflow end
│   ├── edges/
│   │   └── ConditionalEdge.tsx  # Yes/No branches
│   ├── panels/
│   │   ├── NodeConfigPanel.tsx  # Edit selected node
│   │   └── WorkflowSettings.tsx # Global settings
│   └── hooks/
│       ├── useWorkflowStore.ts  # Zustand store
│       └── useAutoLayout.ts     # Auto-arrange nodes
├── pages/
│   └── WorkflowBuilderPage.tsx
└── lib/
    └── workflow-converter.ts    # Canvas ↔ JSON conversion
```

## React Flow Setup

```tsx
// frontend/src/components/workflow-builder/WorkflowCanvas.tsx

import { useCallback, useRef } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { TriggerNode } from './nodes/TriggerNode';
import { SendSMSNode } from './nodes/SendSMSNode';
import { SendEmailNode } from './nodes/SendEmailNode';
import { DelayNode } from './nodes/DelayNode';
import { ConditionNode } from './nodes/ConditionNode';
import { AddTagNode } from './nodes/AddTagNode';
import { EndNode } from './nodes/EndNode';
import { NodePalette } from './NodePalette';
import { NodeConfigPanel } from './panels/NodeConfigPanel';
import { useWorkflowStore } from './hooks/useWorkflowStore';

const nodeTypes = {
  trigger: TriggerNode,
  send_sms: SendSMSNode,
  send_email: SendEmailNode,
  delay: DelayNode,
  condition: ConditionNode,
  add_tag: AddTagNode,
  end: EndNode,
};

interface WorkflowCanvasProps {
  workflowId?: string;
  initialDefinition?: object;
  onSave: (definition: object) => void;
}

export function WorkflowCanvas({ 
  workflowId, 
  initialDefinition, 
  onSave 
}: WorkflowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const { selectedNode, setSelectedNode } = useWorkflowStore();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      
      const type = event.dataTransfer.getData('application/reactflow');
      if (!type || !reactFlowWrapper.current) return;

      const bounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = {
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      };

      const newNode: Node = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: { label: type, config: {} },
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, [setSelectedNode]);

  return (
    <div className="flex h-screen">
      {/* Left: Node Palette */}
      <NodePalette />
      
      {/* Center: Canvas */}
      <div className="flex-1" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <Background />
          <MiniMap />
        </ReactFlow>
      </div>
      
      {/* Right: Config Panel */}
      {selectedNode && (
        <NodeConfigPanel 
          node={selectedNode} 
          onUpdate={(data) => {
            setNodes((nds) =>
              nds.map((n) =>
                n.id === selectedNode.id ? { ...n, data } : n
              )
            );
          }}
        />
      )}
    </div>
  );
}

export default function WorkflowBuilder(props: WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <WorkflowCanvas {...props} />
    </ReactFlowProvider>
  );
}
```

## Node Components

```tsx
// frontend/src/components/workflow-builder/nodes/SendSMSNode.tsx

import { Handle, Position, NodeProps } from 'reactflow';
import { MessageSquare } from 'lucide-react';

interface SendSMSData {
  label: string;
  config: {
    body?: string;
    template_id?: string;
  };
}

export function SendSMSNode({ data, selected }: NodeProps<SendSMSData>) {
  return (
    <div className={`
      px-4 py-3 rounded-lg shadow-md bg-white border-2
      ${selected ? 'border-blue-500' : 'border-gray-200'}
    `}>
      <Handle type="target" position={Position.Top} />
      
      <div className="flex items-center gap-2">
        <div className="p-2 bg-green-100 rounded">
          <MessageSquare className="w-4 h-4 text-green-600" />
        </div>
        <div>
          <div className="text-sm font-medium">Send SMS</div>
          <div className="text-xs text-gray-500">
            {data.config?.body?.substring(0, 30) || 'Configure message...'}
          </div>
        </div>
      </div>
      
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
```

```tsx
// frontend/src/components/workflow-builder/nodes/ConditionNode.tsx

import { Handle, Position, NodeProps } from 'reactflow';
import { GitBranch } from 'lucide-react';

export function ConditionNode({ data, selected }: NodeProps) {
  return (
    <div className={`
      px-4 py-3 rounded-lg shadow-md bg-white border-2
      ${selected ? 'border-blue-500' : 'border-gray-200'}
    `}>
      <Handle type="target" position={Position.Top} />
      
      <div className="flex items-center gap-2">
        <div className="p-2 bg-yellow-100 rounded">
          <GitBranch className="w-4 h-4 text-yellow-600" />
        </div>
        <div>
          <div className="text-sm font-medium">Condition</div>
          <div className="text-xs text-gray-500">
            {data.config?.field || 'Set condition...'}
          </div>
        </div>
      </div>
      
      {/* Two output handles for Yes/No branches */}
      <Handle 
        type="source" 
        position={Position.Bottom} 
        id="yes"
        style={{ left: '30%' }}
      />
      <Handle 
        type="source" 
        position={Position.Bottom} 
        id="no"
        style={{ left: '70%' }}
      />
      
      <div className="flex justify-between mt-2 text-xs text-gray-400">
        <span>Yes</span>
        <span>No</span>
      </div>
    </div>
  );
}
```

## Node Palette

```tsx
// frontend/src/components/workflow-builder/NodePalette.tsx

import { 
  MessageSquare, Mail, Clock, GitBranch, 
  Tag, Webhook, Play, Square 
} from 'lucide-react';

const nodeTypes = [
  { type: 'trigger', label: 'Trigger', icon: Play, color: 'purple' },
  { type: 'send_sms', label: 'Send SMS', icon: MessageSquare, color: 'green' },
  { type: 'send_email', label: 'Send Email', icon: Mail, color: 'blue' },
  { type: 'delay', label: 'Delay', icon: Clock, color: 'orange' },
  { type: 'condition', label: 'Condition', icon: GitBranch, color: 'yellow' },
  { type: 'add_tag', label: 'Add Tag', icon: Tag, color: 'pink' },
  { type: 'webhook', label: 'Webhook', icon: Webhook, color: 'gray' },
  { type: 'end', label: 'End', icon: Square, color: 'red' },
];

export function NodePalette() {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-64 bg-gray-50 border-r p-4">
      <h3 className="font-semibold mb-4">Actions</h3>
      <div className="space-y-2">
        {nodeTypes.map(({ type, label, icon: Icon, color }) => (
          <div
            key={type}
            draggable
            onDragStart={(e) => onDragStart(e, type)}
            className={`
              flex items-center gap-2 p-3 bg-white rounded-lg 
              border border-gray-200 cursor-grab hover:border-gray-400
              transition-colors
            `}
          >
            <Icon className={`w-4 h-4 text-${color}-600`} />
            <span className="text-sm">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Canvas ↔ JSON Conversion

```typescript
// frontend/src/lib/workflow-converter.ts

import { Node, Edge } from 'reactflow';

interface WorkflowDefinition {
  name: string;
  version: number;
  trigger: {
    type: string;
    config: object;
  };
  steps: Array<{
    id: string;
    type: string;
    config: object;
    next?: string;
    branches?: { [key: string]: string };
  }>;
}

/**
 * Convert React Flow nodes/edges to workflow JSON definition.
 */
export function canvasToDefinition(
  nodes: Node[],
  edges: Edge[],
  name: string
): WorkflowDefinition {
  // Find trigger node
  const triggerNode = nodes.find(n => n.type === 'trigger');
  
  // Build adjacency map from edges
  const adjacency: Record<string, string[]> = {};
  edges.forEach(edge => {
    if (!adjacency[edge.source]) {
      adjacency[edge.source] = [];
    }
    adjacency[edge.source].push(edge.target);
  });
  
  // Convert nodes to steps
  const steps = nodes
    .filter(n => n.type !== 'trigger')
    .map(node => {
      const step: any = {
        id: node.id,
        type: node.type,
        config: node.data.config || {},
      };
      
      // Handle branching for condition nodes
      if (node.type === 'condition') {
        const outEdges = edges.filter(e => e.source === node.id);
        step.branches = {};
        outEdges.forEach(e => {
          if (e.sourceHandle === 'yes') {
            step.branches.true = e.target;
          } else if (e.sourceHandle === 'no') {
            step.branches.false = e.target;
          }
        });
      } else {
        // Simple next pointer
        const nextNodes = adjacency[node.id] || [];
        if (nextNodes.length > 0) {
          step.next = nextNodes[0];
        }
      }
      
      return step;
    });
  
  return {
    name,
    version: 1,
    trigger: {
      type: triggerNode?.data.config?.type || 'manual',
      config: triggerNode?.data.config || {},
    },
    steps,
  };
}

/**
 * Convert workflow JSON definition to React Flow nodes/edges.
 */
export function definitionToCanvas(
  definition: WorkflowDefinition
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  
  // Create trigger node
  nodes.push({
    id: 'trigger',
    type: 'trigger',
    position: { x: 250, y: 0 },
    data: { 
      label: 'Trigger', 
      config: definition.trigger 
    },
  });
  
  // Create step nodes
  let yPos = 100;
  definition.steps.forEach((step, index) => {
    nodes.push({
      id: step.id,
      type: step.type,
      position: { x: 250, y: yPos },
      data: { 
        label: step.type, 
        config: step.config 
      },
    });
    yPos += 120;
  });
  
  // Create edges
  // Connect trigger to first step
  if (definition.steps.length > 0) {
    edges.push({
      id: 'trigger-to-first',
      source: 'trigger',
      target: definition.steps[0].id,
    });
  }
  
  // Connect steps based on next/branches
  definition.steps.forEach(step => {
    if (step.branches) {
      if (step.branches.true) {
        edges.push({
          id: `${step.id}-yes`,
          source: step.id,
          sourceHandle: 'yes',
          target: step.branches.true,
        });
      }
      if (step.branches.false) {
        edges.push({
          id: `${step.id}-no`,
          source: step.id,
          sourceHandle: 'no',
          target: step.branches.false,
        });
      }
    } else if (step.next) {
      edges.push({
        id: `${step.id}-next`,
        source: step.id,
        target: step.next,
      });
    }
  });
  
  return { nodes, edges };
}
```

## Config Panel

```tsx
// frontend/src/components/workflow-builder/panels/NodeConfigPanel.tsx

import { Node } from 'reactflow';

interface NodeConfigPanelProps {
  node: Node;
  onUpdate: (data: any) => void;
}

export function NodeConfigPanel({ node, onUpdate }: NodeConfigPanelProps) {
  const config = node.data.config || {};
  
  const renderConfig = () => {
    switch (node.type) {
      case 'send_sms':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Message Body
              </label>
              <textarea
                className="w-full border rounded p-2"
                rows={4}
                value={config.body || ''}
                onChange={(e) => onUpdate({
                  ...node.data,
                  config: { ...config, body: e.target.value }
                })}
                placeholder="Hi {{first_name}}, ..."
              />
            </div>
            <p className="text-xs text-gray-500">
              Available tokens: {'{{first_name}}'}, {'{{last_name}}'}, {'{{phone}}'}
            </p>
          </div>
        );
      
      case 'delay':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Duration
              </label>
              <input
                type="number"
                className="w-full border rounded p-2"
                value={config.duration || 1}
                onChange={(e) => onUpdate({
                  ...node.data,
                  config: { ...config, duration: parseInt(e.target.value) }
                })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Unit
              </label>
              <select
                className="w-full border rounded p-2"
                value={config.unit || 'days'}
                onChange={(e) => onUpdate({
                  ...node.data,
                  config: { ...config, unit: e.target.value }
                })}
              >
                <option value="minutes">Minutes</option>
                <option value="hours">Hours</option>
                <option value="days">Days</option>
              </select>
            </div>
          </div>
        );
      
      case 'condition':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Field
              </label>
              <input
                type="text"
                className="w-full border rounded p-2"
                value={config.field || ''}
                onChange={(e) => onUpdate({
                  ...node.data,
                  config: { ...config, field: e.target.value }
                })}
                placeholder="e.g., tags, status"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Operator
              </label>
              <select
                className="w-full border rounded p-2"
                value={config.operator || 'equals'}
                onChange={(e) => onUpdate({
                  ...node.data,
                  config: { ...config, operator: e.target.value }
                })}
              >
                <option value="equals">Equals</option>
                <option value="not_equals">Not Equals</option>
                <option value="contains">Contains</option>
                <option value="exists">Exists</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Value
              </label>
              <input
                type="text"
                className="w-full border rounded p-2"
                value={config.value || ''}
                onChange={(e) => onUpdate({
                  ...node.data,
                  config: { ...config, value: e.target.value }
                })}
              />
            </div>
          </div>
        );
      
      default:
        return <p className="text-gray-500">No configuration needed.</p>;
    }
  };

  return (
    <div className="w-80 bg-white border-l p-4">
      <h3 className="font-semibold mb-4">Configure: {node.type}</h3>
      {renderConfig()}
    </div>
  );
}
```

## Success Criteria

- [ ] React Flow canvas renders
- [ ] Node palette with all action types
- [ ] Drag & drop nodes to canvas
- [ ] Connect nodes with edges
- [ ] Condition node has Yes/No branches
- [ ] Config panel updates node data
- [ ] Canvas → JSON conversion
- [ ] JSON → Canvas conversion
- [ ] Save workflow to API
- [ ] Load workflow from API
- [ ] MiniMap navigation
- [ ] Zoom controls
- [ ] Undo/redo (stretch)
- [ ] Auto-layout (stretch)
