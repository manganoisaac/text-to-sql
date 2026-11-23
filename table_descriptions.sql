-- Business descriptions for every table and reporting view in schema retail.

COMMENT ON TABLE retail.customers IS 'Customer accounts with contact, signup, segment, and marketing-consent information.';
COMMENT ON TABLE retail.customer_addresses IS 'Saved customer delivery addresses used by orders.';
COMMENT ON TABLE retail.suppliers IS 'Supplier directory with contact details, country, lead time, and active status.';
COMMENT ON TABLE retail.categories IS 'Hierarchical product categories; a null parent identifies a top-level category.';
COMMENT ON TABLE retail.products IS 'Product catalog with SKU, category, current pricing, cost, weight, and lifecycle status.';
COMMENT ON TABLE retail.product_suppliers IS 'Many-to-many product sourcing relationships, including supplier cost and preferred source.';
COMMENT ON TABLE retail.warehouses IS 'Physical warehouses and fulfillment centers that hold and dispatch inventory.';
COMMENT ON TABLE retail.inventory IS 'Current on-hand, reserved, and reorder-threshold quantities by warehouse and product.';
COMMENT ON TABLE retail.inventory_adjustments IS 'Timestamped stock movements and corrections by warehouse, product, quantity, and reason.';
COMMENT ON TABLE retail.promotions IS 'Promotion codes with percentage discounts and validity date ranges.';
COMMENT ON TABLE retail.orders IS 'Customer orders with placement time, delivery address, channel, currency, and fulfillment status.';
COMMENT ON TABLE retail.order_items IS 'Products and captured unit pricing for each order line, including quantity, discount, and tax rate.';
COMMENT ON TABLE retail.order_promotions IS 'Associative records linking orders to the promotion codes applied to them.';
COMMENT ON TABLE retail.payments IS 'Payment attempts and refunds recorded for orders, including amount, method, outcome, and provider reference.';
COMMENT ON TABLE retail.shipments IS 'Order shipment tracking, carrier, dispatch warehouse, timestamps, and delivery state.';
COMMENT ON TABLE retail.shipment_items IS 'Order lines and quantities packed into each shipment.';
COMMENT ON TABLE retail.return_requests IS 'Customer return workflow records with request time, status, reason, and resolution.';
COMMENT ON TABLE retail.return_items IS 'Specific order lines and quantities included in a return, with their refund amounts.';
COMMENT ON TABLE retail.product_reviews IS 'Customer product ratings and review text, optionally linked to an order.';

COMMENT ON VIEW retail.order_totals IS 'Per-order monetary summary derived from order lines, including subtotal, line discounts, tax, and total.';
COMMENT ON VIEW retail.monthly_sales IS 'Monthly shipped and delivered sales summarized by product category, including orders, units, and net sales before tax.';
COMMENT ON VIEW retail.customer_summary IS 'Per-customer order counts, fulfilled order value, segment, and most recent order timestamp.';
