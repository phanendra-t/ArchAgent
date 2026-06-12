// Notification event handlers — subscribes to domain events
import { NotificationService } from "../services/notification.service";

export class NotificationEventHandler {
  constructor(private readonly notificationService: NotificationService) {}

  async handleOrderCreated(event: { orderId: string; customerId: string }): Promise<void> {
    await this.notificationService.sendOrderConfirmation(
      event.customerId,
      event.orderId
    );
  }

  async handleOrderConfirmed(event: { orderId: string; customerId: string }): Promise<void> {
    await this.notificationService.sendOrderConfirmation(
      event.customerId,
      event.orderId
    );
  }
}
