/**
 * GmailConnect Component
 * Handles Gmail OAuth connection flow
 */
import { useState, useEffect } from 'react';
import { getGoogleAuthUrl } from '../services/api';

interface GmailConnectProps {
  onConnectionSuccess?: () => void;
}

const GmailConnect: React.FC<GmailConnectProps> = ({ onConnectionSuccess }) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [message, setMessage] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Check URL params for connection status
    const params = new URLSearchParams(window.location.search);
    const gmailConnected = params.get('gmail_connected');
    const gmailError = params.get('gmail_error');

    if (gmailConnected === 'true') {
      setIsConnected(true);
      setMessage('✅ Gmail connected successfully! Email sync will begin shortly.');
      if (onConnectionSuccess) {
        onConnectionSuccess();
      }

      // Clean up URL params
      window.history.replaceState({}, '', window.location.pathname);
    } else if (gmailError) {
      setMessage(`❌ Error connecting Gmail: ${gmailError}`);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [onConnectionSuccess]);

  const handleConnect = async () => {
    try {
      setIsConnecting(true);
      setMessage('Initiating Google OAuth...');

      // Get OAuth URL from backend
      const authUrl = await getGoogleAuthUrl();

      // Redirect to Google OAuth page
      window.location.href = authUrl;
    } catch (error: any) {
      setIsConnecting(false);
      setMessage(`❌ Failed to initiate OAuth: ${error.message}`);
    }
  };

  return (
    <div className="gmail-connect-container bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
      <div className="text-center mb-6">
        <svg
          className="mx-auto h-16 w-16 mb-4"
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M24 4C12.95 4 4 12.95 4 24C4 35.05 12.95 44 24 44C35.05 44 44 35.05 44 24C44 12.95 35.05 4 24 4ZM34 30L24 24L14 30V14L24 20L34 14V30Z"
            fill="#EA4335"
          />
        </svg>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Connect Gmail</h2>
        <p className="text-gray-600">
          Connect your Gmail account to automatically import and analyze your emails
        </p>
      </div>

      {!isConnected ? (
        <button
          onClick={handleConnect}
          disabled={isConnecting}
          className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-all duration-200 ${
            isConnecting
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
          }`}
        >
          {isConnecting ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Connecting...
            </span>
          ) : (
            '🔗 Connect Gmail Account'
          )}
        </button>
      ) : (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div className="text-green-800 font-semibold mb-2">✅ Gmail Connected!</div>
          <p className="text-green-600 text-sm">
            Your emails are being synced and analyzed in the background.
          </p>
        </div>
      )}

      {message && !isConnected && (
        <div
          className={`mt-4 p-4 rounded-lg text-sm ${
            message.startsWith('❌')
              ? 'bg-red-50 border border-red-200 text-red-800'
              : 'bg-blue-50 border border-blue-200 text-blue-800'
          }`}
        >
          {message}
        </div>
      )}

      <div className="mt-6 text-xs text-gray-500 text-center">
        <p className="mb-2">By connecting, you allow msg2act to:</p>
        <ul className="list-disc list-inside text-left space-y-1">
          <li>Read your Gmail messages</li>
          <li>Extract entities (people, companies, amounts)</li>
          <li>Store data securely with encryption</li>
        </ul>
        <p className="mt-3">
          <a href="#" className="text-blue-600 hover:text-blue-800 underline">
            Learn more about privacy
          </a>
        </p>
      </div>
    </div>
  );
};

export default GmailConnect;
