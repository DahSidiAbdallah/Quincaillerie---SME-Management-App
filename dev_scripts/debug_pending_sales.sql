-- Find all client debts with remaining amount > 0
SELECT * FROM client_debts WHERE remaining_amount > 0;

-- Find all credit sales with no matching client_debts row
SELECT * FROM sales s WHERE s.is_credit = 1 AND NOT EXISTS (
    SELECT 1 FROM client_debts cd WHERE cd.sale_id = s.id
);
