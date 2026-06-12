// Payment model
export interface Payment {
  id: string;
  orderId: string;
  amount: number;
  currency: string;
  method: PaymentMethod;
  status: PaymentStatus;
  processedAt?: Date;
}

export enum PaymentMethod {
  CREDIT_CARD = "credit_card",
  DEBIT_CARD = "debit_card",
  UPI = "upi",
  NET_BANKING = "net_banking",
}

export enum PaymentStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
  REFUNDED = "refunded",
}
