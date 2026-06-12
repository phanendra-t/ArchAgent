// Payment controller
import { PaymentService } from "../services/payment.service";
import { PaymentMethod } from "../models/payment.model";

export class PaymentController {
  constructor(private readonly paymentService: PaymentService) {}

  async processPayment(req: any, res: any) {
    try {
      const { orderId, amount, currency, method } = req.body;
      const payment = await this.paymentService.processPayment(
        orderId,
        amount,
        currency,
        method as PaymentMethod
      );
      res.status(201).json(payment);
    } catch (error) {
      res.status(500).json({ error: "Payment processing failed" });
    }
  }

  async refundPayment(req: any, res: any) {
    await this.paymentService.refundPayment(req.params.id);
    res.status(204).send();
  }
}
