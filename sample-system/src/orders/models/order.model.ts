// Order domain model — pure data structure, no dependencies
export interface Order {
  id: string;
  customerId: string;
  items: OrderItem[];
  status: OrderStatus;
  totalAmount: number;
  currency: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface OrderItem {
  productId: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
}

export enum OrderStatus {
  PENDING = "pending",
  CONFIRMED = "confirmed",
  PAID = "paid",
  SHIPPED = "shipped",
  DELIVERED = "delivered",
  CANCELLED = "cancelled",
}
