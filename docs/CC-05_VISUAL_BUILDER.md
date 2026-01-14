# CC-05: Visual Workflow Builder
## Claude Code Task Specification

**Module:** React Flow Visual Builder
**Priority:** P0 (MVP Critical)
**Estimated Time:** 4-5 days
**Dependencies:** CC-03 (Workflow Engine v2)

---

## Objective

Build a drag-and-drop visual workflow builder using React Flow that outputs JSON compatible with Workflow Engine v2.

---

## Technical Stack

```bash
npm install reactflow @reactflow/node-resizer @reactflow/background
npm install zustand          # State management
npm install @dnd-kit/core    # Drag and drop
```

---

## Directory Structure
```
frontend/src/
├── pages/
│   └── WorkflowBuilder/
│       ├── index.tsx
│       ├── WorkflowCanvas.tsx
│       ├── NodePalette.tsx
│       ├── PropertiesPanel.tsx
│       └── WorkflowToolbar.tsx
├── components/
│   └── workflow/
│       ├── nodes/
│       │   ├── TriggerNode.tsx
│       │   ├── ActionNode.tsx
│       │   ├── ConditionNode.tsx
│       │   ├── WaitNode.tsx
│       │   ├── ABSplitNode.tsx
│       │   └── GoalNode.tsx
│       ├── edges/
│       │   └── CustomEdge.tsx
│       └── panels/
│           ├── TriggerConfig.tsx
│           ├── SMSConfig.tsx
│           ├── EmailConfig.tsx
│           ├── CallConfig.tsx
│           ├── WaitConfig.tsx
│           └── ConditionConfig.tsx
├── stores/
│   └── workflowStore.ts
└── utils/
    └── workflowConverter.ts  # Canvas <-> JSON
```

---

## Node Types

| Type | Icon | Description |
|------|------|-------------|
| trigger | ⚡ | Start of workflow |
| send_sms | 💬 | Send SMS message |
| send_email | ✉️ | Send email |
| make_call | 📞 | Initiate call |
| wait | ⏰ | Delay execution |
| condition | ❓ | If/else branch |
| ab_split | 🔀 | A/B test split |
| update_contact | 👤 | Update fields/tags |
| webhook | 🌐 | HTTP request |
| goal | 🎯 | Conversion goal |
| exit | 🚪 | End workflow |

---

## React Flow Implementation

```tsx
// WorkflowCanvas.tsx
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';

const nodeTypes = {
  trigger: TriggerNode,
  send_sms: ActionNode,
  send_email: ActionNode,
  make_call: ActionNode,
  wait: WaitNode,
  condition: ConditionNode,
  ab_split: ABSplitNode,
  goal: GoalNode,
};

export function WorkflowCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      fitView
    >
      <Background />
      <Controls />
      <MiniMap />
    </ReactFlow>
  );
}
```

---

## JSON ↔ Visual Conversion

```typescript
// workflowConverter.ts

interface VisualWorkflow {
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
}

interface WorkflowDefinition {
  name: string;
  trigger: TriggerConfig;
  steps: Step[];
}

// Visual → JSON (for saving)
export function visualToJson(visual: VisualWorkflow): WorkflowDefinition {
  // Convert React Flow nodes/edges to workflow engine format
  const trigger = visual.nodes.find(n => n.type === 'trigger');
  const steps = visual.nodes
    .filter(n => n.type !== 'trigger')
    .map(node => ({
      id: node.id,
      type: node.type,
      config: node.data.config,
      next: findNextStep(node.id, visual.edges),
    }));
  
  return { name: '', trigger: trigger.data.config, steps };
}

// JSON → Visual (for loading)
export function jsonToVisual(def: WorkflowDefinition): VisualWorkflow {
  // Auto-layout steps into canvas positions
  // Use dagre or elkjs for automatic layout
}
```

---

## Properties Panel

```tsx
// PropertiesPanel.tsx
export function PropertiesPanel({ selectedNode, onUpdate }) {
  if (!selectedNode) {
    return <EmptyState>Select a node to configure</EmptyState>;
  }
  
  const ConfigPanel = {
    trigger: TriggerConfig,
    send_sms: SMSConfig,
    send_email: EmailConfig,
    make_call: CallConfig,
    wait: WaitConfig,
    condition: ConditionConfig,
    ab_split: ABSplitConfig,
  }[selectedNode.type];
  
  return (
    <div className="w-80 border-l bg-white p-4">
      <h3>{selectedNode.data.label}</h3>
      <ConfigPanel 
        config={selectedNode.data.config}
        onChange={(config) => onUpdate(selectedNode.id, config)}
      />
    </div>
  );
}
```

---

## Acceptance Criteria

1. ✅ Drag nodes from palette to canvas
2. ✅ Connect nodes with edges
3. ✅ Configure each node type
4. ✅ Validate workflow (no orphans, has trigger)
5. ✅ Save workflow to API
6. ✅ Load workflow from API
7. ✅ Import YAML → Visual
8. ✅ Export Visual → YAML
9. ✅ Undo/redo support
10. ✅ Copy/paste nodes
11. ✅ Auto-layout option
12. ✅ Zoom and pan controls
13. ✅ Minimap navigation
14. ✅ Mobile-responsive (view only)

---

## API Integration

```typescript
// Save workflow
const saveWorkflow = async (workflow: VisualWorkflow) => {
  const definition = visualToJson(workflow);
  await api.post('/api/workflows', {
    name: workflowName,
    definition,
    visual_data: workflow, // Store visual layout too
  });
};

// Load workflow
const loadWorkflow = async (id: string) => {
  const { data } = await api.get(`/api/workflows/${id}`);
  if (data.visual_data) {
    return data.visual_data; // Use saved layout
  }
  return jsonToVisual(data.definition); // Auto-generate layout
};
```
