// Event bus — domain event publishing
export interface DomainEvent {
  type: string;
  payload: Record<string, any>;
  timestamp: Date;
}

export class EventBus {
  private subscribers: Map<string, Array<(event: DomainEvent) => Promise<void>>> = new Map();

  async publish(type: string, payload: Record<string, any>): Promise<void> {
    const event: DomainEvent = { type, payload, timestamp: new Date() };
    const handlers = this.subscribers.get(type) || [];
    await Promise.all(handlers.map((h) => h(event)));
  }

  subscribe(type: string, handler: (event: DomainEvent) => Promise<void>): void {
    const handlers = this.subscribers.get(type) || [];
    handlers.push(handler);
    this.subscribers.set(type, handlers);
  }
}
