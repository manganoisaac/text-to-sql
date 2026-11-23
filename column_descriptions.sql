-- Business descriptions for every table and reporting-view column in schema retail.
-- Apply directly to an existing sample database or include with sample_ecommerce.sql.

COMMENT ON COLUMN retail.customers.customer_id IS 'Stable generated identifier for one customer.';
COMMENT ON COLUMN retail.customers.first_name IS 'Customer given name; sample values are synthetic.';
COMMENT ON COLUMN retail.customers.last_name IS 'Customer family name; sample values are synthetic.';
COMMENT ON COLUMN retail.customers.email IS 'Unique customer contact email address; sample values use reserved example domains.';
COMMENT ON COLUMN retail.customers.phone IS 'Optional customer contact telephone number; sample values are synthetic.';
COMMENT ON COLUMN retail.customers.segment IS 'Commercial grouping used for customer analysis: consumer, small_business, or enterprise.';
COMMENT ON COLUMN retail.customers.signup_date IS 'Calendar date when the customer account was created.';
COMMENT ON COLUMN retail.customers.marketing_opt_in IS 'Whether the customer has consented to receive marketing communications.';

COMMENT ON COLUMN retail.customer_addresses.address_id IS 'Stable generated identifier for one saved customer address.';
COMMENT ON COLUMN retail.customer_addresses.customer_id IS 'Customer who owns this address; references customers.customer_id.';
COMMENT ON COLUMN retail.customer_addresses.label IS 'Customer-assigned address label such as Home, Office, or Warehouse.';
COMMENT ON COLUMN retail.customer_addresses.line_1 IS 'Street address or delivery address line.';
COMMENT ON COLUMN retail.customer_addresses.city IS 'Suburb or city for delivery.';
COMMENT ON COLUMN retail.customer_addresses.state_region IS 'State, territory, or region for delivery.';
COMMENT ON COLUMN retail.customer_addresses.postal_code IS 'Postal or ZIP code for delivery.';
COMMENT ON COLUMN retail.customer_addresses.country_code IS 'Two-letter ISO 3166-1 country code.';
COMMENT ON COLUMN retail.customer_addresses.is_default IS 'Whether this is the customer default address; at most one per customer.';

COMMENT ON COLUMN retail.suppliers.supplier_id IS 'Stable generated identifier for one supplier.';
COMMENT ON COLUMN retail.suppliers.supplier_name IS 'Display name of the supplier company.';
COMMENT ON COLUMN retail.suppliers.country_code IS 'Two-letter ISO 3166-1 country code for the supplier.';
COMMENT ON COLUMN retail.suppliers.contact_email IS 'Supplier contact email address.';
COMMENT ON COLUMN retail.suppliers.lead_time_days IS 'Expected supplier replenishment lead time in calendar days.';
COMMENT ON COLUMN retail.suppliers.active IS 'Whether the supplier is currently available for purchasing.';

COMMENT ON COLUMN retail.categories.category_id IS 'Stable generated identifier for one product category.';
COMMENT ON COLUMN retail.categories.category_name IS 'Unique human-readable product category name.';
COMMENT ON COLUMN retail.categories.parent_category_id IS 'Optional parent category identifier for the category hierarchy.';

COMMENT ON COLUMN retail.products.product_id IS 'Stable generated identifier for one product.';
COMMENT ON COLUMN retail.products.sku IS 'Unique internal stock-keeping unit used to identify the product.';
COMMENT ON COLUMN retail.products.product_name IS 'Human-readable name of the product.';
COMMENT ON COLUMN retail.products.category_id IS 'Product category identifier; references categories.category_id.';
COMMENT ON COLUMN retail.products.list_price IS 'Current list price per unit in the product selling currency, AUD in this dataset.';
COMMENT ON COLUMN retail.products.unit_cost IS 'Current estimated acquisition cost per unit, in AUD.';
COMMENT ON COLUMN retail.products.weight_kg IS 'Shipping weight of one product unit in kilograms.';
COMMENT ON COLUMN retail.products.discontinued IS 'Whether the product is no longer offered for new sale.';

COMMENT ON COLUMN retail.product_suppliers.product_id IS 'Product identifier in this supplier-product association.';
COMMENT ON COLUMN retail.product_suppliers.supplier_id IS 'Supplier identifier in this supplier-product association.';
COMMENT ON COLUMN retail.product_suppliers.supplier_sku IS 'Supplier-specific stock-keeping unit for the product.';
COMMENT ON COLUMN retail.product_suppliers.supplier_cost IS 'Supplier quoted acquisition cost per unit, in AUD.';
COMMENT ON COLUMN retail.product_suppliers.is_preferred IS 'Whether this supplier is marked as the preferred source for the product.';

COMMENT ON COLUMN retail.warehouses.warehouse_id IS 'Stable generated identifier for one fulfillment warehouse.';
COMMENT ON COLUMN retail.warehouses.warehouse_name IS 'Unique display name of the warehouse or fulfillment center.';
COMMENT ON COLUMN retail.warehouses.city IS 'City where the warehouse is located.';
COMMENT ON COLUMN retail.warehouses.state_region IS 'State, territory, or region where the warehouse is located.';
COMMENT ON COLUMN retail.warehouses.country_code IS 'Two-letter ISO 3166-1 country code for the warehouse.';

COMMENT ON COLUMN retail.inventory.warehouse_id IS 'Warehouse holding this product stock; part of the inventory key.';
COMMENT ON COLUMN retail.inventory.product_id IS 'Product held at this warehouse; part of the inventory key.';
COMMENT ON COLUMN retail.inventory.on_hand IS 'Physical units currently recorded at the warehouse.';
COMMENT ON COLUMN retail.inventory.reserved IS 'Units allocated to orders and not available for new orders.';
COMMENT ON COLUMN retail.inventory.reorder_point IS 'Stock threshold at or below which replenishment should be considered.';
COMMENT ON COLUMN retail.inventory.last_counted_at IS 'Date when the warehouse last verified this stock quantity.';

COMMENT ON COLUMN retail.inventory_adjustments.adjustment_id IS 'Stable generated identifier for one inventory movement record.';
COMMENT ON COLUMN retail.inventory_adjustments.warehouse_id IS 'Warehouse where the stock movement occurred.';
COMMENT ON COLUMN retail.inventory_adjustments.product_id IS 'Product affected by the stock movement.';
COMMENT ON COLUMN retail.inventory_adjustments.quantity_change IS 'Signed unit change: positive adds stock and negative removes stock.';
COMMENT ON COLUMN retail.inventory_adjustments.reason IS 'Movement category: receipt, cycle_count, damage, transfer, or return.';
COMMENT ON COLUMN retail.inventory_adjustments.occurred_at IS 'Timestamp when the inventory movement was recorded.';
COMMENT ON COLUMN retail.inventory_adjustments.note IS 'Optional operational note describing the inventory movement.';

COMMENT ON COLUMN retail.promotions.promotion_id IS 'Stable generated identifier for one promotion.';
COMMENT ON COLUMN retail.promotions.promo_code IS 'Unique code customers or staff apply to an order.';
COMMENT ON COLUMN retail.promotions.description IS 'Human-readable explanation of the promotion.';
COMMENT ON COLUMN retail.promotions.discount_pct IS 'Discount fraction between zero and one; for example 0.10 means ten percent.';
COMMENT ON COLUMN retail.promotions.starts_on IS 'First calendar date on which the promotion is valid.';
COMMENT ON COLUMN retail.promotions.ends_on IS 'Last calendar date on which the promotion is valid.';

COMMENT ON COLUMN retail.orders.order_id IS 'Stable generated internal identifier for one order.';
COMMENT ON COLUMN retail.orders.order_number IS 'Unique customer-facing order reference.';
COMMENT ON COLUMN retail.orders.customer_id IS 'Customer who placed the order; references customers.customer_id.';
COMMENT ON COLUMN retail.orders.ship_to_address_id IS 'Saved delivery address selected for the order.';
COMMENT ON COLUMN retail.orders.ordered_at IS 'Timestamp when the order was placed.';
COMMENT ON COLUMN retail.orders.status IS 'Order lifecycle state: pending, processing, shipped, delivered, or cancelled.';
COMMENT ON COLUMN retail.orders.sales_channel IS 'Order origin: web, mobile_app, marketplace, or phone.';
COMMENT ON COLUMN retail.orders.currency IS 'Three-letter ISO 4217 currency code for order amounts.';

COMMENT ON COLUMN retail.order_items.order_id IS 'Order containing this line item.';
COMMENT ON COLUMN retail.order_items.line_number IS 'Line sequence within the order; combined with order_id forms the primary key.';
COMMENT ON COLUMN retail.order_items.product_id IS 'Product purchased on this line.';
COMMENT ON COLUMN retail.order_items.quantity IS 'Number of product units purchased on this line.';
COMMENT ON COLUMN retail.order_items.unit_price IS 'Per-unit selling price captured when the order was placed, before line discount and tax.';
COMMENT ON COLUMN retail.order_items.discount_pct IS 'Line-level discount fraction between zero and one; for example 0.05 means five percent.';
COMMENT ON COLUMN retail.order_items.tax_rate IS 'Tax fraction applied after line discount; sample orders use 0.10.';

COMMENT ON COLUMN retail.order_promotions.order_id IS 'Order to which the promotion code was applied.';
COMMENT ON COLUMN retail.order_promotions.promotion_id IS 'Promotion applied to the order.';

COMMENT ON COLUMN retail.payments.payment_id IS 'Stable generated identifier for one payment attempt or refund record.';
COMMENT ON COLUMN retail.payments.order_id IS 'Order associated with this payment or refund.';
COMMENT ON COLUMN retail.payments.paid_at IS 'Timestamp when the payment provider recorded this attempt or refund.';
COMMENT ON COLUMN retail.payments.method IS 'Payment instrument used: card, paypal, bank_transfer, or gift_card.';
COMMENT ON COLUMN retail.payments.amount IS 'Positive monetary amount of this payment attempt or refund, in the order currency.';
COMMENT ON COLUMN retail.payments.status IS 'Payment outcome: authorized, captured, failed, or refunded.';
COMMENT ON COLUMN retail.payments.provider_reference IS 'Unique transaction reference returned by the payment provider.';

COMMENT ON COLUMN retail.shipments.shipment_id IS 'Stable generated identifier for one shipment.';
COMMENT ON COLUMN retail.shipments.order_id IS 'Order fulfilled by this shipment; only one shipment per order in this dataset.';
COMMENT ON COLUMN retail.shipments.warehouse_id IS 'Warehouse from which this shipment was dispatched.';
COMMENT ON COLUMN retail.shipments.carrier IS 'Delivery carrier responsible for transporting the shipment.';
COMMENT ON COLUMN retail.shipments.tracking_number IS 'Unique carrier tracking reference for the shipment.';
COMMENT ON COLUMN retail.shipments.shipped_at IS 'Timestamp when the shipment left the warehouse.';
COMMENT ON COLUMN retail.shipments.delivered_at IS 'Delivery timestamp; null until delivery is confirmed.';
COMMENT ON COLUMN retail.shipments.status IS 'Shipment state: in_transit, delivered, or exception.';

COMMENT ON COLUMN retail.shipment_items.shipment_id IS 'Shipment containing the shipped order line.';
COMMENT ON COLUMN retail.shipment_items.order_id IS 'Order associated with both the shipment and the order line.';
COMMENT ON COLUMN retail.shipment_items.line_number IS 'Order line included in the shipment.';
COMMENT ON COLUMN retail.shipment_items.quantity IS 'Number of units from the order line included in this shipment.';

COMMENT ON COLUMN retail.return_requests.return_id IS 'Stable generated identifier for one return request.';
COMMENT ON COLUMN retail.return_requests.order_id IS 'Order for which the return was requested.';
COMMENT ON COLUMN retail.return_requests.requested_at IS 'Timestamp when the customer requested the return.';
COMMENT ON COLUMN retail.return_requests.status IS 'Return workflow state: requested, approved, received, rejected, or refunded.';
COMMENT ON COLUMN retail.return_requests.reason IS 'Customer return reason: damaged, wrong_item, not_as_described, changed_mind, or other.';
COMMENT ON COLUMN retail.return_requests.resolution IS 'Optional free-text outcome or resolution note.';

COMMENT ON COLUMN retail.return_items.return_id IS 'Return request containing the returned order line.';
COMMENT ON COLUMN retail.return_items.order_id IS 'Order containing the returned line; also validates return ownership.';
COMMENT ON COLUMN retail.return_items.line_number IS 'Order line whose product is being returned.';
COMMENT ON COLUMN retail.return_items.quantity IS 'Number of units from the order line being returned.';
COMMENT ON COLUMN retail.return_items.refund_amount IS 'Refund amount for this returned quantity, in the order currency.';

COMMENT ON COLUMN retail.product_reviews.review_id IS 'Stable generated identifier for one product review.';
COMMENT ON COLUMN retail.product_reviews.customer_id IS 'Customer who submitted the review.';
COMMENT ON COLUMN retail.product_reviews.product_id IS 'Product being reviewed.';
COMMENT ON COLUMN retail.product_reviews.order_id IS 'Optional associated order; null when the review is not linked to a specific order.';
COMMENT ON COLUMN retail.product_reviews.rating IS 'Customer score from one to five, with five as the highest rating.';
COMMENT ON COLUMN retail.product_reviews.review_title IS 'Short customer-written review heading.';
COMMENT ON COLUMN retail.product_reviews.review_body IS 'Full customer-written review text.';
COMMENT ON COLUMN retail.product_reviews.reviewed_at IS 'Calendar date when the review was submitted.';
COMMENT ON COLUMN retail.product_reviews.verified_purchase IS 'Whether the review is marked as associated with a verified purchase.';

COMMENT ON COLUMN retail.order_totals.order_id IS 'Internal identifier of the order summarized by this view.';
COMMENT ON COLUMN retail.order_totals.order_number IS 'Customer-facing order reference.';
COMMENT ON COLUMN retail.order_totals.customer_id IS 'Customer who placed the order.';
COMMENT ON COLUMN retail.order_totals.ordered_at IS 'Timestamp when the order was placed.';
COMMENT ON COLUMN retail.order_totals.status IS 'Current order lifecycle state.';
COMMENT ON COLUMN retail.order_totals.subtotal IS 'Sum of line quantity times captured unit price before discounts and tax.';
COMMENT ON COLUMN retail.order_totals.line_discounts IS 'Total line-item discount amount before tax; promotion mappings are not additionally deducted.';
COMMENT ON COLUMN retail.order_totals.tax IS 'Tax summed across order lines after each line-level discount.';
COMMENT ON COLUMN retail.order_totals.total IS 'Order line total after line discounts and tax; excludes shipping charges.';

COMMENT ON COLUMN retail.monthly_sales.sales_month IS 'First calendar day of the sales month.';
COMMENT ON COLUMN retail.monthly_sales.category_id IS 'Product category identifier used to group sales.';
COMMENT ON COLUMN retail.monthly_sales.category_name IS 'Human-readable product category used to group sales.';
COMMENT ON COLUMN retail.monthly_sales.order_count IS 'Distinct shipped or delivered orders containing this category in the month.';
COMMENT ON COLUMN retail.monthly_sales.units_sold IS 'Units sold in shipped or delivered orders for the category and month.';
COMMENT ON COLUMN retail.monthly_sales.net_sales_before_tax IS 'Line sales after line discounts and before tax for shipped or delivered orders.';

COMMENT ON COLUMN retail.customer_summary.customer_id IS 'Internal identifier of the summarized customer.';
COMMENT ON COLUMN retail.customer_summary.first_name IS 'Customer given name.';
COMMENT ON COLUMN retail.customer_summary.last_name IS 'Customer family name.';
COMMENT ON COLUMN retail.customer_summary.segment IS 'Commercial customer grouping.';
COMMENT ON COLUMN retail.customer_summary.completed_or_open_orders IS 'Count of the customer orders whose status is not cancelled.';
COMMENT ON COLUMN retail.customer_summary.fulfilled_order_value IS 'Sum of line totals including tax for shipped or delivered orders; excludes cancelled and open orders.';
COMMENT ON COLUMN retail.customer_summary.most_recent_order_at IS 'Timestamp of the latest order of any status for the customer.';
