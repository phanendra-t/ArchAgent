// Notification service — sends notifications based on domain events
import {
  Notification,
  NotificationChannel,
  NotificationStatus,
} from "../models/notification.model";

export class NotificationService {
  async sendOrderConfirmation(recipientId: string, orderId: string): Promise<void> {
    const notification: Notification = {
      id: crypto.randomUUID(),
      recipientId,
      channel: NotificationChannel.EMAIL,
      subject: "Order Confirmed",
      body: `Your order ${orderId} has been confirmed.`,
      status: NotificationStatus.QUEUED,
    };

    await this.send(notification);
  }

  async sendPaymentReceipt(recipientId: string, amount: number): Promise<void> {
    const notification: Notification = {
      id: crypto.randomUUID(),
      recipientId,
      channel: NotificationChannel.EMAIL,
      subject: "Payment Received",
      body: `Payment of ${amount} received successfully.`,
      status: NotificationStatus.QUEUED,
    };

    await this.send(notification);
  }

  private async send(notification: Notification): Promise<void> {
    // Simulated send
    notification.status = NotificationStatus.SENT;
    notification.sentAt = new Date();
  }
}
