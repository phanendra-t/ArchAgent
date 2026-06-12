// Payment repository
import { Payment, PaymentStatus } from "../models/payment.model";

export class PaymentRepository {
  private payments: Map<string, Payment> = new Map();

  async findById(id: string): Promise<Payment | null> {
    return this.payments.get(id) || null;
  }

  async findByOrderId(orderId: string): Promise<Payment | null> {
    return Array.from(this.payments.values()).find(
      (p) => p.orderId === orderId
    ) || null;
  }

  async save(payment: Payment): Promise<Payment> {
    this.payments.set(payment.id, payment);
    return payment;
  }

  async updateStatus(id: string, status: PaymentStatus): Promise<void> {
    const payment = this.payments.get(id);
    if (payment) {
      payment.status = status;
    }
  }
}
