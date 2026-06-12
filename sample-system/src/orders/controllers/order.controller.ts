// Order controller — HTTP layer
import { OrderService } from "../services/order.service";

export class OrderController {
  constructor(private readonly orderService: OrderService) {}

  async createOrder(req: any, res: any) {
    try {
      const { customerId, items } = req.body;
      const order = await this.orderService.createOrder(customerId, items);
      res.status(201).json(order);
    } catch (error) {
      res.status(500).json({ error: "Failed to create order" });
    }
  }

  async getOrder(req: any, res: any) {
    const order = await this.orderService.getOrder(req.params.id);
    if (!order) {
      return res.status(404).json({ error: "Order not found" });
    }
    res.json(order);
  }

  async getCustomerOrders(req: any, res: any) {
    const orders = await this.orderService.getCustomerOrders(req.params.customerId);
    res.json(orders);
  }

  async cancelOrder(req: any, res: any) {
    await this.orderService.cancelOrder(req.params.id);
    res.status(204).send();
  }
}
