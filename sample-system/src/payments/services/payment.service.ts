// Payment service — business logic for payment processing
import { Payment, PaymentMethod, PaymentStatus } from "../models/payment.model";
import { PaymentRepository } from "../repositories/payment.repository";

export class PaymentService {
  constructor(private readonly paymentRepo: PaymentRepository) {}

  async processPayment(
    orderId: string,
    amount: number,
    currency: string,
    method: PaymentMethod
  ): Promise<Payment> {
    const payment: Payment = {
      id: crypto.randomUUID(),
      orderId,
      amount,
      currency,
      method,
      status: PaymentStatus.PROCESSING,
    };

    await this.paymentRepo.save(payment);

    // Simulate payment gateway call
    const success = await this.callPaymentGateway(payment);

    if (success) {
      payment.status = PaymentStatus.COMPLETED;
      payment.processedAt = new Date();
    } else {
      payment.status = PaymentStatus.FAILED;
    }

    await this.paymentRepo.save(payment);
    return payment;
  }

  async refundPayment(paymentId: string): Promise<void> {
    await this.paymentRepo.updateStatus(paymentId, PaymentStatus.REFUNDED);
  }

  private async callPaymentGateway(payment: Payment): Promise<boolean> {
    // Simulated gateway call
    return true;
  }
}
