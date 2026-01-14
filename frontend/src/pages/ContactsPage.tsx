import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contactsApi, Contact } from '../api/client';
import { Search, Plus, Phone, Mail, Tag, Ban } from 'lucide-react';

const LOCATION_ID = '00000000-0000-0000-0000-000000000001'; // Default location

export function ContactsPage() {
  const [search, setSearch] = useState('');
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: contacts, isLoading } = useQuery({
    queryKey: ['contacts', search],
    queryFn: () => contactsApi.list(LOCATION_ID, { search: search || undefined }),
    select: (res) => res.data,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => contactsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setSelectedContact(null);
    },
  });

  return (
    <div className="flex h-full">
      {/* Contact List */}
      <div className="w-96 border-r bg-white">
        <div className="p-4 border-b">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Search contacts..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg"
              />
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              <Plus size={20} />
            </button>
          </div>
        </div>

        <div className="overflow-auto h-[calc(100%-73px)]">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Loading...</div>
          ) : contacts?.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No contacts found</div>
          ) : (
            contacts?.map((contact) => (
              <div
                key={contact.id}
                onClick={() => setSelectedContact(contact)}
                className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                  selectedContact?.id === contact.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">
                      {contact.first_name || contact.last_name
                        ? `${contact.first_name || ''} ${contact.last_name || ''}`.trim()
                        : contact.phone || contact.email || 'Unknown'}
                    </div>
                    <div className="text-sm text-gray-500">{contact.phone}</div>
                  </div>
                  {contact.dnd && (
                    <Ban size={16} className="text-red-500" title="Do Not Disturb" />
                  )}
                </div>
                {contact.tags.length > 0 && (
                  <div className="flex gap-1 mt-2">
                    {contact.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Contact Detail */}
      <div className="flex-1 p-6">
        {selectedContact ? (
          <ContactDetail
            contact={selectedContact}
            onDelete={() => deleteMutation.mutate(selectedContact.id)}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            Select a contact to view details
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateContactModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            queryClient.invalidateQueries({ queryKey: ['contacts'] });
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
}

function ContactDetail({ contact, onDelete }: { contact: Contact; onDelete: () => void }) {
  return (
    <div>
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold">
            {contact.first_name} {contact.last_name}
          </h2>
          <span className={`px-2 py-1 rounded text-sm ${
            contact.type === 'customer' ? 'bg-green-100 text-green-700' :
            contact.type === 'lead' ? 'bg-blue-100 text-blue-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {contact.type}
          </span>
        </div>
        <button
          onClick={onDelete}
          className="px-4 py-2 text-red-600 hover:bg-red-50 rounded"
        >
          Delete
        </button>
      </div>

      <div className="space-y-4">
        {contact.phone && (
          <div className="flex items-center gap-3">
            <Phone size={18} className="text-gray-400" />
            <span>{contact.phone}</span>
            {contact.dnd && (
              <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">DND</span>
            )}
          </div>
        )}
        {contact.email && (
          <div className="flex items-center gap-3">
            <Mail size={18} className="text-gray-400" />
            <span>{contact.email}</span>
          </div>
        )}
        {contact.tags.length > 0 && (
          <div className="flex items-center gap-3">
            <Tag size={18} className="text-gray-400" />
            <div className="flex gap-1 flex-wrap">
              {contact.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 pt-6 border-t">
        <div className="text-sm text-gray-500">
          Created: {new Date(contact.created_at).toLocaleDateString()}
        </div>
        <div className="text-sm text-gray-500">
          Updated: {new Date(contact.updated_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}

function CreateContactModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    location_id: '00000000-0000-0000-0000-000000000001',
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => contactsApi.create(data),
    onSuccess: onCreated,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-96">
        <h3 className="text-lg font-bold mb-4">Create Contact</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="First Name"
            value={formData.first_name}
            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            className="w-full px-3 py-2 border rounded"
          />
          <input
            type="text"
            placeholder="Last Name"
            value={formData.last_name}
            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            className="w-full px-3 py-2 border rounded"
          />
          <input
            type="tel"
            placeholder="Phone"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="w-full px-3 py-2 border rounded"
          />
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 border rounded"
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
