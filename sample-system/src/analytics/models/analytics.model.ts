// Analytics model
export interface AnalyticsEvent {
  id: string;
  eventType: string;
  payload: Record<string, any>;
  timestamp: Date;
}

export interface MetricSnapshot {
  metricName: string;
  value: number;
  dimensions: Record<string, string>;
  timestamp: Date;
}
