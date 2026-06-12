// Order service — business logic layer
import { Order, OrderStatus, OrderItem } from "../models/order.model";
import { OrderRepository } from "../repositories/order.repository";
import { EventBus } from "../events/event-bus";

export class OrderService {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly eventBus: EventBus
  ) {}

  async createOrder(customerId: string, items: OrderItem[]): Promise<Order> {
    const order: Order = {
      id: crypto.randomUUID(),
      customerId,
      items,
      status: OrderStatus.PENDING,
      totalAmount: items.reduce((sum, item) => sum + item.subtotal, 0),
      currency: "USD",
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const saved = await this.orderRepo.save(order);

    // Emit event for other contexts (notifications, analytics)
    await this.eventBus.publish("order.created", {
      orderId: saved.id,
      customerId: saved.customerId,
      totalAmount: saved.totalAmount,
    });

    return saved;
  }

  async confirmOrder(orderId: string): Promise<void> {
    await this.orderRepo.updateStatus(orderId, OrderStatus.CONFIRMED);
    await this.eventBus.publish("order.confirmed", { orderId });
  }

  async cancelOrder(orderId: string): Promise<void> {
    await this.orderRepo.updateStatus(orderId, OrderStatus.CANCELLED);
    await this.eventBus.publish("order.cancelled", { orderId });
  }

  async getOrder(orderId: string): Promise<Order | null> {
    return this.orderRepo.findById(orderId);
  }

  async getCustomerOrders(customerId: string): Promise<Order[]> {
    return this.orderRepo.findByCustomerId(customerId);
  }
}
