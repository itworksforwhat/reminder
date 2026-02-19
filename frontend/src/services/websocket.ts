import type { SyncMessage } from '../types';

type MessageHandler = (message: SyncMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectTimer: number | null = null;
  private companyId: string | null = null;
  private token: string | null = null;
  private retryCount = 0;
  private readonly maxRetries = 10;
  private readonly baseDelay = 1000;
  private readonly maxDelay = 30000;
  private intentionalClose = false;

  connect(companyId: string, token: string): void {
    this.companyId = companyId;
    this.token = token;
    this.retryCount = 0;
    this.intentionalClose = false;
    this.doConnect();
  }

  private doConnect(): void {
    if (!this.companyId || !this.token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_URL || `${protocol}//${window.location.host}`;
    const url = `${host}/ws/${this.companyId}?token=${this.token}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.retryCount = 0;
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const message: SyncMessage = JSON.parse(event.data);
        this.handlers.forEach((handler) => handler(message));
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    if (this.retryCount >= this.maxRetries) {
      console.warn(`WebSocket: max retries (${this.maxRetries}) reached, giving up`);
      return;
    }
    const delay = Math.min(this.baseDelay * Math.pow(2, this.retryCount), this.maxDelay);
    this.retryCount++;
    console.log(`WebSocket: reconnecting in ${delay}ms (attempt ${this.retryCount}/${this.maxRetries})`);
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.doConnect();
    }, delay);
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.companyId = null;
    this.token = null;
    this.retryCount = 0;
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  send(message: SyncMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}

export const wsService = new WebSocketService();
