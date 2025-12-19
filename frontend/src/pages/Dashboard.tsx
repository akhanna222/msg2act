/**
 * Dashboard Page
 * Main dashboard showing connection status, entities, and messages
 */
import { useState, useEffect } from 'react';
import GmailConnect from '../components/GmailConnect';
import {
  getEntities,
  getMessages,
  getMessageStats,
  Entity,
  Message,
} from '../services/api';

const Dashboard: React.FC = () => {
  const [isGmailConnected, setIsGmailConnected] = useState(false);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [stats, setStats] = useState({
    total_messages: 0,
    processed_messages: 0,
    pending_processing: 0,
    last_30_days: 0,
  });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'people' | 'companies' | 'amounts' | 'messages'>(
    'people'
  );

  useEffect(() => {
    // Check if Gmail is connected by looking for data
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load entities and messages in parallel
      const [entitiesRes, messagesRes, statsRes] = await Promise.all([
        getEntities({ limit: 50 }).catch(() => ({ entities: [], total: 0 })),
        getMessages({ limit: 10 }).catch(() => ({ messages: [], total: 0 })),
        getMessageStats().catch(() => ({
          total_messages: 0,
          processed_messages: 0,
          pending_processing: 0,
          last_30_days: 0,
        })),
      ]);

      setEntities(entitiesRes.entities);
      setMessages(messagesRes.messages);
      setStats(statsRes);

      // If we have messages, Gmail is connected
      if (messagesRes.total > 0) {
        setIsGmailConnected(true);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectionSuccess = () => {
    setIsGmailConnected(true);
    // Reload data after connection
    setTimeout(() => loadDashboardData(), 2000);
  };

  const filterEntitiesByType = (type: string) => {
    return entities.filter((e) => e.type === type);
  };

  if (!isGmailConnected && messages.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Welcome to msg2act
            </h1>
            <p className="text-xl text-gray-600">
              Your personal knowledge graph platform
            </p>
          </div>

          <GmailConnect onConnectionSuccess={handleConnectionSuccess} />

          <div className="mt-12 bg-white rounded-lg shadow-lg p-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              What happens after you connect?
            </h3>
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-semibold">1</span>
                </div>
                <div className="ml-4">
                  <h4 className="font-semibold text-gray-900">Email Import</h4>
                  <p className="text-gray-600">
                    We'll import your recent emails (configurable: 30/90/365 days)
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-semibold">2</span>
                </div>
                <div className="ml-4">
                  <h4 className="font-semibold text-gray-900">Entity Extraction</h4>
                  <p className="text-gray-600">
                    AI extracts people, companies, amounts, and dates from your emails
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-semibold">3</span>
                </div>
                <div className="ml-4">
                  <h4 className="font-semibold text-gray-900">Knowledge Graph</h4>
                  <p className="text-gray-600">
                    Discover relationships and insights across your communications
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">msg2act Dashboard</h1>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                <span className="w-2 h-2 bg-green-600 rounded-full mr-2"></span>
                Gmail Connected
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Total Messages</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_messages}</div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Processed</div>
            <div className="text-3xl font-bold text-green-600">{stats.processed_messages}</div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Pending</div>
            <div className="text-3xl font-bold text-yellow-600">{stats.pending_processing}</div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Entities Found</div>
            <div className="text-3xl font-bold text-blue-600">{entities.length}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {[
                { id: 'people', label: 'People', count: filterEntitiesByType('PERSON').length },
                { id: 'companies', label: 'Companies', count: filterEntitiesByType('COMPANY').length },
                { id: 'amounts', label: 'Amounts', count: filterEntitiesByType('AMOUNT').length },
                { id: 'messages', label: 'Recent Messages', count: messages.length },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">Loading...</p>
              </div>
            ) : (
              <>
                {/* People Tab */}
                {activeTab === 'people' && (
                  <div className="space-y-4">
                    {filterEntitiesByType('PERSON').map((entity) => (
                      <div
                        key={entity.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-gray-900">{entity.name}</h3>
                            {entity.attributes?.email && (
                              <p className="text-sm text-gray-600 mt-1">{entity.attributes.email}</p>
                            )}
                            <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                              <span>Mentions: {entity.mentions}</span>
                              <span>Confidence: {(entity.confidence * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    {filterEntitiesByType('PERSON').length === 0 && (
                      <p className="text-center text-gray-500 py-8">
                        No people found yet. They'll appear as emails are processed.
                      </p>
                    )}
                  </div>
                )}

                {/* Companies Tab */}
                {activeTab === 'companies' && (
                  <div className="space-y-4">
                    {filterEntitiesByType('COMPANY').map((entity) => (
                      <div
                        key={entity.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-gray-900">{entity.name}</h3>
                            {entity.attributes?.domain && (
                              <p className="text-sm text-gray-600 mt-1">{entity.attributes.domain}</p>
                            )}
                            <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                              <span>Mentions: {entity.mentions}</span>
                              <span>Confidence: {(entity.confidence * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    {filterEntitiesByType('COMPANY').length === 0 && (
                      <p className="text-center text-gray-500 py-8">
                        No companies found yet. They'll appear as emails are processed.
                      </p>
                    )}
                  </div>
                )}

                {/* Amounts Tab */}
                {activeTab === 'amounts' && (
                  <div className="space-y-4">
                    {filterEntitiesByType('AMOUNT').map((entity) => (
                      <div
                        key={entity.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-gray-900 text-lg">{entity.name}</h3>
                            {entity.attributes?.currency && (
                              <p className="text-sm text-gray-600 mt-1">
                                {entity.attributes.currency} {entity.attributes.value}
                              </p>
                            )}
                            <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                              <span>Mentions: {entity.mentions}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    {filterEntitiesByType('AMOUNT').length === 0 && (
                      <p className="text-center text-gray-500 py-8">
                        No amounts found yet. They'll appear as emails are processed.
                      </p>
                    )}
                  </div>
                )}

                {/* Messages Tab */}
                {activeTab === 'messages' && (
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-gray-900">{message.subject || '(No subject)'}</h3>
                          <span
                            className={`text-xs px-2 py-1 rounded-full ${
                              message.is_processed
                                ? 'bg-green-100 text-green-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {message.is_processed ? 'Processed' : 'Processing'}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600">
                          From: {message.from_name || message.from_email}
                        </div>
                        <div className="mt-2 text-xs text-gray-500">
                          {new Date(message.received_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                    {messages.length === 0 && (
                      <p className="text-center text-gray-500 py-8">
                        No messages yet. Sync is in progress.
                      </p>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
