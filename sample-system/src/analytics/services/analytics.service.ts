// Analytics service — processes domain events for reporting
import { AnalyticsEvent } from "../models/analytics.model";

export class AnalyticsService {
  private events: AnalyticsEvent[] = [];

  async recordEvent(eventType: string, payload: Record<string, any>): Promise<void> {
    this.events.push({
      id: crypto.randomUUID(),
      eventType,
      payload,
      timestamp: new Date(),
    });
  }

  async getEventCount(eventType: string): Promise<number> {
    return this.events.filter((e) => e.eventType === eventType).length;
  }

  async getRecentEvents(limit: number = 100): Promise<AnalyticsEvent[]> {
    return this.events.slice(-limit);
  }
}
