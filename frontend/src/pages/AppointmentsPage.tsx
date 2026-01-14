import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { appointmentsApi, Appointment } from '../api/client';
import { Plus, Calendar, Clock } from 'lucide-react';

const LOCATION_ID = '00000000-0000-0000-0000-000000000001';

export function AppointmentsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: appointments, isLoading } = useQuery({
    queryKey: ['appointments'],
    queryFn: () => appointmentsApi.list(LOCATION_ID),
    select: (res) => res.data,
  });

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Appointments</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          <Plus size={20} />
          New Appointment
        </button>
      </div>

      {isLoading ? (
        <div className="text-center text-gray-500 py-8">Loading...</div>
      ) : appointments?.length === 0 ? (
        <div className="text-center text-gray-500 py-8">No appointments scheduled</div>
      ) : (
        <div className="grid gap-4">
          {appointments?.map((apt) => (
            <AppointmentCard key={apt.id} appointment={apt} />
          ))}
        </div>
      )}

      {showCreateModal && (
        <CreateAppointmentModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            queryClient.invalidateQueries({ queryKey: ['appointments'] });
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
}

function AppointmentCard({ appointment }: { appointment: Appointment }) {
  const startDate = new Date(appointment.start_time);
  const endDate = new Date(appointment.end_time);

  return (
    <div className="bg-white p-4 rounded-lg border hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-medium">{appointment.title}</h3>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar size={14} />
              {startDate.toLocaleDateString()}
            </span>
            <span className="flex items-center gap-1">
              <Clock size={14} />
              {startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -
              {endDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs rounded ${
          appointment.status === 'confirmed' ? 'bg-green-100 text-green-700' :
          appointment.status === 'cancelled' ? 'bg-red-100 text-red-700' :
          'bg-yellow-100 text-yellow-700'
        }`}>
          {appointment.status}
        </span>
      </div>
    </div>
  );
}

function CreateAppointmentModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [formData, setFormData] = useState({
    title: '',
    contact_id: '',
    start_time: '',
    end_time: '',
    location_id: LOCATION_ID,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => appointmentsApi.create(data),
    onSuccess: onCreated,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-96">
        <h3 className="text-lg font-bold mb-4">New Appointment</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="w-full px-3 py-2 border rounded"
            required
          />
          <input
            type="text"
            placeholder="Contact ID"
            value={formData.contact_id}
            onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
            className="w-full px-3 py-2 border rounded"
            required
          />
          <input
            type="datetime-local"
            value={formData.start_time}
            onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
            className="w-full px-3 py-2 border rounded"
            required
          />
          <input
            type="datetime-local"
            value={formData.end_time}
            onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
            className="w-full px-3 py-2 border rounded"
            required
          />
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
