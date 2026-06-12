// Order repository — data access layer
import { Order, OrderStatus } from "../models/order.model";

export class OrderRepository {
  private orders: Map<string, Order> = new Map();

  async findById(id: string): Promise<Order | null> {
    return this.orders.get(id) || null;
  }

  async findByCustomerId(customerId: string): Promise<Order[]> {
    return Array.from(this.orders.values()).filter(
      (o) => o.customerId === customerId
    );
  }

  async save(order: Order): Promise<Order> {
    this.orders.set(order.id, order);
    return order;
  }

  async updateStatus(id: string, status: OrderStatus): Promise<void> {
    const order = this.orders.get(id);
    if (order) {
      order.status = status;
      order.updatedAt = new Date();
    }
  }
}
