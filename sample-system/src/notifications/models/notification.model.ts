// Notification model
export interface Notification {
  id: string;
  recipientId: string;
  channel: NotificationChannel;
  subject: string;
  body: string;
  sentAt?: Date;
  status: NotificationStatus;
}

export enum NotificationChannel {
  EMAIL = "email",
  SMS = "sms",
  PUSH = "push",
}

export enum NotificationStatus {
  QUEUED = "queued",
  SENT = "sent",
  FAILED = "failed",
}
